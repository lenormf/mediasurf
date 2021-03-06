#!/usr/bin/env python3

import os
import sys
import math
import enum
import urllib
import hashlib
import pathlib
import inspect
import logging
import argparse
import datetime
import itertools
import collections
import multiprocessing

# TODO: version dependencies statically
import bottle
import ffmpeg
import PIL
import PIL.Image
import PIL.ExifTags
import pyparsing as pp

from bottle import get, static_file, request
from bottle import mako_view
from bottle import HTTPError, HTTP_CODES


class HttpError(HTTPError):
    def __init__(self, status_code):
        super().__init__(status=status_code, body=HTTP_CODES[status_code])


class HttpBadRequest(HTTPError):
    def __init__(self):
        super().__init__(400)


class HttpUnauthorized(HTTPError):
    def __init__(self):
        super().__init__(401)


class HttpPermissionDenied(HTTPError):
    def __init__(self):
        super().__init__(403)


class HttpNotFound(HTTPError):
    def __init__(self):
        super().__init__(404)


class HttpInternalServerError(HTTPError):
    def __init__(self):
        super().__init__(500)


# NOTE: the template abstraction doesn't recognise the `.mako`
# extension for Mako templates, might be fixed upstream in the future
bottle.BaseTemplate.extensions.append("mako")

router_t = collections.namedtuple("router_t", "get_url current_route_name current_url")


def new_router():
    return router_t(
        get_url=bottle.app().get_url,
        current_route_name=request.route.name,
        current_url=request.path,
    )


def str2int(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


@get("/static/<path:path>")
def get_static_path(path):
    assert bottle.app().resources.path
    return static_file(path, root=bottle.app().resources.path[0])


# NOTE: the extension is not used here
@get("/media/<uuid_media>.<extension>", name="media_uuid")
def get_media_uuid(mdb, uuid_media, extension):
    assert bottle.app().resources.path

    if uuid_media not in mdb.db:
        raise HttpNotFound()

    path_media = mdb.db[uuid_media].path

    return static_file(path_media.name, root=path_media.parent)


# TODO: create a route without the extension to display an HTML page with details
# NOTE: the extension is not used here, the file format is hardcoded
@get("/media/<uuid_media>/thumbnail/<breakpoint>.<extension>", name="media_uuid_thumbnail")
def get_media_uuid_thumbnail(mdb, uuid_media, breakpoint, extension):
    assert bottle.app().resources.path

    if uuid_media not in mdb.db:
        raise HttpNotFound()
    elif breakpoint not in ["sm", "md", "lg", "xl", "xxl"]:
        raise HttpBadRequest()

    media = mdb.db[uuid_media]
    name_thumbnail = "%s-%s" % (media.hash, breakpoint)
    path_thumbnail = mdb.path_thumbnails / name_thumbnail

    logging.debug("path to thumbnail: %s", path_thumbnail)

    if not path_thumbnail.exists():
        if not media.CreateThumbnail(breakpoint, path_thumbnail):
            raise HttpInternalServerError()

    return static_file(name_thumbnail, root=mdb.path_thumbnails)


@get("/", name="index")
@mako_view("index")
def get_index(mdb):
    # NOTE: dict values are a view, not a list, which aren't subscriptable
    page = Page(list(mdb.db.values()), request)

    return {
        "router": new_router(),
        "page": page,
    }


class MediaError(Exception): pass


class Media:
    FORMAT_THUMBNAIL = "webp"

    def __init__(self, path):
        self.path = path
        self.name = self.path.stem
        self.extension = self.path.suffix[1:]
        self.hash = None
        self.resolution = None
        self.filetime = None
        self.tags = {}
        self.format = None

        # NOTE: This field is used by the view templates to avoid type introspection
        self.type = None

    def _hash(self, filename, filesize, width, height, format):
        h = hashlib.sha1()
        h_data = "%s-%d-%d.%d-%s" % (filename, filesize, width, height, format)
        h.update(h_data.encode())

        return h.hexdigest()

    def ThumbnailResolution(self, breakpoint):
        def scale_resolution(target_width, resolution):
            if resolution[0] < target_width:
                return resolution

            q = resolution[0] / target_width

            return (resolution[0] / q, resolution[1] / q)

        resolution = self.resolution

        assert resolution is not None and breakpoint in ["sm", "md", "lg", "xl", "xxl"]

        if breakpoint == "sm":
            # NOTE: under this breakpoint, all pictures are shown on their own column
            resolution = scale_resolution(766, resolution)
        elif breakpoint == "md":
            if resolution[0] < resolution[1]:
                resolution = scale_resolution(990 / 2, resolution)
            else:
                resolution = scale_resolution(990, resolution)
        elif breakpoint == "lg":
            if resolution[0] < resolution[1]:
                resolution = scale_resolution(1398 / 3, resolution)
            else:
                resolution = scale_resolution(1398 / 2, resolution)
        elif breakpoint == "xl":
            if resolution[0] < resolution[1]:
                resolution = scale_resolution(1920 / 4, resolution)
            else:
                resolution = scale_resolution(1920 / 3, resolution)
        elif breakpoint == "xxl":
            if resolution[0] < resolution[1]:
                resolution = scale_resolution(2560 / 6, resolution)
            else:
                resolution = scale_resolution(2560 / 4, resolution)

        return resolution

    def CreateThumbnail(self, breakpoint, path_thumbnail, format_thumbnail=FORMAT_THUMBNAIL):
        pass


class Video(Media):
    def __init__(self, path):
        super().__init__(path)

        self.type = "video"

        st = self.path.stat()
        self.filetime = DatetimeWrapper(dt=datetime.datetime.fromtimestamp(st.st_ctime))

        try:
            probe = ffmpeg.probe(self.path)
        except ffmpeg.Error as e:
            raise MediaError("unable to open video: %s" % e.stderr)

        meta_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
        if meta_stream is None:
            raise MediaError("no video stream in the file")

        self.resolution = [meta_stream["width"], meta_stream["height"]]
        self.format = probe["format"]["format_name"]

        for stream in sorted(probe["streams"], key=lambda x: x["index"], reverse=True):
            self.tags.update(stream.get("tags", {}))
        self.tags.update(probe["format"].get("tags", {}))

        self.hash = self._hash(self.name, str2int(probe["format"]["size"]), self.resolution[0], self.resolution[1], self.format)

    def CreateThumbnail(self, breakpoint, path_thumbnail, format_thumbnail=Media.FORMAT_THUMBNAIL):
        logging.debug("generating thumbnail for breakpoint %s: %s", breakpoint, path_thumbnail)

        resolution = self.ThumbnailResolution(breakpoint)

        logging.debug("target thumbnail resolution: %d / %d", *resolution)

        try:
            ffmpeg.input(self.path).filter("scale", resolution[0], -1) \
                  .output(filename=path_thumbnail, format=format_thumbnail, vframes=1).overwrite_output() \
                  .run(capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            logging.error("unable to generate thumbnail: %s", e.stderr)
            return False

        return True


class Image(Media):
    def __init__(self, path):
        super().__init__(path)

        self.type = "image"

        try:
            st = self.path.stat()
            self.filetime = DatetimeWrapper(dt=datetime.datetime.fromtimestamp(st.st_ctime))

            with PIL.Image.open(self.path) as im:
                self.resolution = im.size
                self.format = im.format

                for k, v in im.getexif().items():
                    if k in PIL.ExifTags.TAGS:
                        self.tags[PIL.ExifTags.TAGS[k]] = v
                    else:
                        logging.warning("unknown tag index: %s", k)

                self.hash = self._hash(self.name, st.st_size, im.width, im.height, im.format)
        except (FileNotFoundError, ValueError, TypeError, OSError, PIL.UnidentifiedImageError) as e:
            raise MediaError("unable to open image: %s" % e)

    def CreateThumbnail(self, breakpoint, path_thumbnail, format_thumbnail=Media.FORMAT_THUMBNAIL):
        logging.debug("generating thumbnail for breakpoint %s: %s", breakpoint, path_thumbnail)

        resolution = self.ThumbnailResolution(breakpoint)

        logging.debug("target thumbnail resolution: %d / %d", *resolution)

        try:
            with PIL.Image.open(self.path) as im:
                im.thumbnail(size=resolution, resample=PIL.Image.LANCZOS)

                im.save(path_thumbnail, format=format_thumbnail)
        except (ValueError, OSError) as e:
            logging.error("unable to generate thumbnail: %s", e)
            return False

        return True


class DateHints(enum.Flag):
    YEAR = enum.auto()
    MONTH = enum.auto()
    DAY = enum.auto()
    HOUR = enum.auto()
    MINUTE = enum.auto()
    SECOND = enum.auto()
    MICROSECOND = enum.auto()


class DatetimeWrapper(datetime.datetime):
    def __new__(cls, dt, hints=DateHints.YEAR | DateHints.MONTH | DateHints.DAY | DateHints.HOUR | DateHints.MINUTE | DateHints.SECOND | DateHints.MICROSECOND):
        # NOTE: at some point the instance is re-constructed with a byte array
        if isinstance(dt, (bytes, str)):
            result = super().__new__(cls, dt)
        elif isinstance(dt, datetime.datetime):
            result = super().__new__(cls, dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, dt.tzinfo, fold=dt.fold)
        result.hints = hints
        return result

    def __str__(self):
        return "%s, %s" % (super().__str__(), self.hints)

    def __eq__(self, other):
        values = []
        for i in [i for i in list(DateHints) if i in self.hints]:
            values.append((getattr(self, i.name.lower()), getattr(other, i.name.lower())))

        logging.debug("equal date values: %s", values)

        return next((True for a, b in values if a != b), None) is None

    # NOTE: the following operators follow the date formats implemented in QueryParser
    def __le__(self, other):
        is_year = DateHints.YEAR in self.hints \
                  and DateHints.YEAR in other.hints
        is_year_month = is_year \
                        and DateHints.MONTH in self.hints \
                        and DateHints.MONTH in other.hints
        is_date = is_year_month \
                  and DateHints.DAY in self.hints \
                  and DateHints.DAY in other.hints

        if is_date:
            return self.date() <= other.date()
        elif is_year_month:
            return self.year < other.year \
                   or (self.year == other.year and self.month <= other.month)
        elif is_year:
            return self.year <= other.year
        else:
            logging.warning("unsupported combination of hints: %s/%s", self.hints, other.hints)

    # FIXME: factorise the operators
    def __ge__(self, other):
        is_year = DateHints.YEAR in self.hints \
                  and DateHints.YEAR in other.hints
        is_year_month = is_year \
                        and DateHints.MONTH in self.hints \
                        and DateHints.MONTH in other.hints
        is_date = is_year_month \
                  and DateHints.DAY in self.hints \
                  and DateHints.DAY in other.hints

        if is_date:
            return self.date() >= other.date()
        elif is_year_month:
            return self.year > other.year \
                   or (self.year == other.year and self.month >= other.month)
        elif is_year:
            return self.year >= other.year
        else:
            logging.warning("unsupported combination of hints: %s/%s", self.hints, other.hints)


class Date(pp.ParserElement):
    DATE_FORMAT = "%a %b %d %H:%M:%S %Y"
    DATE_FORMAT_HINTS = (
        DateHints.YEAR
        | DateHints.MONTH
        | DateHints.DAY
        | DateHints.HOUR
        | DateHints.MINUTE
        | DateHints.SECOND
    )
    STR_DELIM = " "
    MAX_DELIM = 5

    def __init__(self, format=DATE_FORMAT, format_hints=DATE_FORMAT_HINTS, delim=STR_DELIM, max_delim=MAX_DELIM):
        super().__init__()

        self.format = format or Date.DATE_FORMAT
        self.format_hints = format_hints or Date.DATE_FORMAT_HINTS
        self.delim = delim or Date.STR_DELIM
        self.max_delim = max_delim

        self.name = "Date"
        self.errmsg = "Expected %s" % self.name

    def _match_datetime(self, s, format):
        try:
            datetime.datetime.strptime(s, format)
            return True
        except ValueError:
            return False

    def parseImpl(self, instring, loc, doActions=True):
        if self._match_datetime(instring[loc:], self.format):
            return len(instring), instring[loc:]

        max_delim = max(self.format.count(self.delim), self.max_delim)
        previous_delim = loc - 1
        for i in range(max_delim):
            previous_delim = instring.find(self.delim, previous_delim + 1)
            if previous_delim < 0:
                raise pp.ParseException(instring, loc, self.errmsg, self)

            if self._match_datetime(instring[loc:previous_delim], self.format):
                return previous_delim, instring[loc:previous_delim]

        raise pp.ParseException(instring, loc, self.errmsg, self)


class QueryError(Exception): pass


class QueryParser(collections.OrderedDict):
    TAG_TOKEN = (
        pp.Keyword("tag") + pp.Suppress(":") + pp.Word(pp.alphas, pp.alphanums + "_")
    )

    SORT_TOKEN = (
        pp.Keyword("sort") + pp.Suppress(":")
        + (pp.Keyword("name") | pp.Keyword("date") | TAG_TOKEN)
        + pp.Optional(
            pp.Suppress(":") + pp.oneOf("s n d"),
            default="s",
        )
        + pp.Optional(
            pp.Suppress(pp.Keyword("order")) + pp.Suppress(":") + (pp.Keyword("asc") | pp.Keyword("desc")),
            default="desc",
        )
    )

    SEARCH_TOKEN = (
        (
            (pp.Keyword("name") | pp.Keyword("date"))
            + pp.Suppress(":")
            + (pp.Word(pp.printables)
               | pp.dblQuotedString().setParseAction(pp.removeQuotes)
               | pp.sglQuotedString().setParseAction(pp.removeQuotes))
        ) | (
            TAG_TOKEN
            + pp.Optional(
                pp.Suppress(":")
                + (pp.Word(pp.printables)
                   | pp.dblQuotedString().setParseAction(pp.removeQuotes)
                   | pp.sglQuotedString().setParseAction(pp.removeQuotes))
            )
        )
    )

    # TODO: date, from, to should be able to grab dates in EXIF tags

    # TODO: support quoted %c datetimes
    # TODO: support quoted datetimes with hour/minute/second individually
    DATETIME = (
        Date("%Y/%m/%d", DateHints.YEAR | DateHints.MONTH | DateHints.DAY)
        | Date("%Y/%m", DateHints.YEAR | DateHints.MONTH)
        | Date("%Y", DateHints.YEAR)
    )
    FROM_TOKEN = (
        pp.Keyword("from") + pp.Suppress(":") + DATETIME
    )
    TO_TOKEN = (
        pp.Keyword("to") + pp.Suppress(":") + DATETIME
    )

    TYPE_TOKEN = (
        pp.Keyword("type") + pp.Suppress(":")
        + (pp.Keyword("image") | pp.Keyword("video"))
    )

    QUERY_TOKEN = pp.Group(SORT_TOKEN | SEARCH_TOKEN | FROM_TOKEN | TO_TOKEN | TYPE_TOKEN)

    GRAMMAR = pp.Dict(pp.OneOrMore(QUERY_TOKEN))

    def __init__(self, s, grammar=GRAMMAR):
        try:
            r = grammar.setDebug(logging.getLogger().isEnabledFor(logging.DEBUG)).parseString(s, parseAll=True)

            logging.debug("search query parse results: %s", r)

            self.update(collections.OrderedDict(r))
        except (Exception, pp.ParseException, pp.RecursiveGrammarException, pp.ParseFatalException, pp.ParseSyntaxException) as e:
            raise QueryError("unable to parse query: %s" % e)


class Page:
    def __init__(self, all_entries, request):
        logging.debug("Request form filters: %r", [(k, v) for k, v in request.query.items()])

        def cast_integer(s):
            try:
                return int(s)
            except ValueError:
                logging.warning("unable to cast string as integer: %s", s)
            return 0

        def cast_date(s):
            for D in QueryParser.DATETIME().streamline().exprs:
                try:
                    d = D()
                    d.parseString(s, parseAll=True)
                    return DatetimeWrapper(dt=datetime.datetime.strptime(s, d.format), hints=d.format_hints)
                except pp.ParseException:
                    pass
            logging.warning("unable to cast string as date: %s", s)
            return datetime.datetime.fromtimestamp(0)

        def cast_exif_date(s):
            try:
                return datetime.datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                logging.warning("unable to cast string as date: %s", s)
            return datetime.datetime.fromtimestamp(0)

        self.page = str2int(request.query.get("page"))
        if self.page is None or self.page < 1:
            self.page = 1

        self.page_offset = self.page - 1

        self.limit = str2int(request.query.get("limit"))
        if self.limit is None:
            self.limit = 25
        elif self.limit < 10:
            self.limit = 10

        self.all_entries = all_entries
        self.tag_sort_keys = sorted(set(itertools.chain(*[p.tags.keys() for p in all_entries])), key=lambda x: x.lower())

        # TODO: fuzzy matching
        self.search_query = request.query.get("search")
        if self.search_query:
            try:
                q = QueryParser(self.search_query)

                logging.info("search query: %s", q)

                value_casts = {
                    "s": str,
                    "n": cast_integer,
                    "d": cast_date,
                }

                for name_filter, predicate in q.items():
                    logging.debug("filter: %s", name_filter)
                    logging.debug("predicate: %s", predicate)

                    if name_filter == "tag":
                        if isinstance(predicate, str):
                            logging.debug("filtering by tag: %s", predicate)

                            self.all_entries = list(filter(lambda x: predicate in x.tags, self.all_entries))
                        else:
                            logging.debug("filtering by tag and value: %s", predicate)

                            self.all_entries = list(filter(lambda x: str(x.tags.get(predicate[0], "")) == predicate[1], self.all_entries))
                    elif name_filter == "sort":
                        key = predicate[0]

                        if key == "tag":
                            cast = predicate[2]
                            order = predicate[3]
                        else:
                            cast = predicate[1]
                            order = predicate[2]

                        logging.debug("sorting by: %s (%s, %s)", key, cast, order)

                        f_cast = value_casts[cast]

                        if key == "tag":
                            if cast == "d":
                                # NOTE: the datetimes in EXIF tags have a standard format
                                f_cast = cast_exif_date
                            self.all_entries = sorted(self.all_entries,
                                                      key=lambda x: f_cast(x.tags.get(predicate[1], "")),
                                                      reverse=order == "desc")
                        elif key == "name":
                            self.all_entries = sorted(self.all_entries,
                                                      key=lambda x: f_cast(x.name),
                                                      reverse=order == "desc")
                        elif key == "date":
                            # NOTE: we don't cast here because there's no use serialising a datetime object
                            self.all_entries = sorted(self.all_entries,
                                                      key=lambda x: x.filetime,
                                                      reverse=order == "desc")
                        else:
                            logging.error("sorting predicate unsupported: %s", name_filter)
                    elif name_filter == "name":
                        logging.debug("filtering by name: %s", predicate)

                        self.all_entries = list(filter(lambda x: predicate.lower() in x.name.lower(),
                                                  self.all_entries))
                    elif name_filter == "date":
                        logging.debug("filtering by date: %s", predicate)

                        date_predicate = cast_date(predicate)
                        logging.debug("date predicate: %s", date_predicate)
                        self.all_entries = list(filter(lambda x: date_predicate == x.filetime,
                                                  self.all_entries))
                    elif name_filter == "from":
                        logging.debug("filtering by date, from: %s", predicate)

                        date_predicate = cast_date(predicate)
                        logging.debug("date predicate: %s", date_predicate)
                        self.all_entries = list(filter(lambda x: x.filetime >= date_predicate,
                                                  self.all_entries))
                    elif name_filter == "to":
                        logging.debug("filtering by date, to: %s", predicate)

                        date_predicate = cast_date(predicate)
                        logging.debug("date predicate: %s", date_predicate)
                        self.all_entries = list(filter(lambda x: x.filetime <= date_predicate,
                                                  self.all_entries))
                    elif name_filter == "type":
                        logging.debug("filtering by filetype: %s", predicate)
                        class_filter = Image if predicate == "image" else Video
                        self.all_entries = list(filter(lambda x: isinstance(x, class_filter),
                                                  self.all_entries))
                    else:
                        logging.error("unsupported filter: %s", name_filter)
            except QueryError as e:
                logging.error("couldn't parse query: %s", e)
                # TODO: signal to the UI that the query is incorrect

        self.all_entries_count = len(self.all_entries)

        self.entries = self.all_entries[self.page_offset * self.limit:(self.page_offset + 1) * self.limit]
        self.entries_count = len(self.entries)

        self.pages_count = math.ceil(self.all_entries_count / self.limit)

        self.has_previous_page = self.page_offset > 0
        self.has_next_page = self.page < self.pages_count

        self.url_previous_page = ""
        self.url_next_page = ""

        def edit_url_qs(url, **kwargs):
            qs = urllib.parse.parse_qs(url[4])
            qs.update(**kwargs)

            return urllib.parse.urlunparse(url._replace(query=urllib.parse.urlencode(qs, doseq=True)))

        url = urllib.parse.urlparse(request.url)

        self.url_first_page = edit_url_qs(url, page=1)
        self.url_last_page = edit_url_qs(url, page=self.pages_count)

        if self.has_previous_page:
            self.url_previous_page = edit_url_qs(url, page=self.page - 1)

        if self.has_next_page:
            self.url_next_page = edit_url_qs(url, page=self.page + 1)

        self.url_limit = lambda x: edit_url_qs(url, limit=x, page=1)


class MediaDatabaseError(Exception): pass


class MediaDatabase:
    EXTENSIONS_IMAGE = [
        "blp",
        "bmp",
        "cur",
        "dcx",
        "dds",
        "dib",
        "eps",
        "flc",
        "fli",
        "fpx",
        "ftex",
        "gbr",
        "gd",
        "gif",
        "icns",
        "ico",
        "im",
        "imt",
        "iptc",
        "jpeg",
        "jpg",
        "mcidas",
        "mic",
        "mpo",
        "msp",
        "naa",
        "pcd",
        "pcx",
        "pixar",
        "png",
        "ppm",
        "psd",
        "sgi",
        "spider",
        "tga",
        "tiff",
        "wal",
        "webp",
        "wmf",
        "xbm",
        "xpm",
    ]

    EXTENSIONS_VIDEO = [
        "avchd",
        "avi",
        "flv",
        "m4p",
        "m4v",
        "mkv",
        "mov",
        "mp2",
        "mp4",
        "mpe",
        "mpeg",
        "mpg",
        "mpv",
        "ogg",
        "qt",
        "swf",
        "webm",
        "wmv",
    ]

    def _append_media_done(self, media):
        if media is not None:
            # NOTE: we use a hash generated by the object itself to be able to lookup thumbnails easily
            self.db[media.hash] = media

    # NOTE: The function cannot be a member function because of multi-processing
    @staticmethod
    def _append_media(path_file):
        logging.info("identifying media: %s", path_file)

        if not path_file.suffix:
            logging.warning("no extension, skipping")
            return

        path_extension = path_file.suffix[1:].lower()
        if path_extension in MediaDatabase.EXTENSIONS_IMAGE:
            logging.debug("media type identified: image")
            ctor = Image
        elif path_extension in MediaDatabase.EXTENSIONS_VIDEO:
            logging.debug("media type identified: video")
            ctor = Video
        else:
            logging.error("unable to identify media type")
            return

        try:
            logging.info("loading media: %s", path_file)

            return ctor(path_file)
        except MediaError as e:
            logging.error("unable to assign the media to the database: %s", e)

    def _append_directory(self, pool, path_directory):
        logging.info("loading directory: %s", path_directory)

        results = []
        for path in path_directory.iterdir():
            results.extend(self._resolve_path(pool, path))

        return results

    def _resolve_path(self, pool, path):
        logging.debug("resolving path: %s", path)

        def error_callback(e):
            raise MediaDatabaseError(e)

        if path.is_file():
            result = pool.apply_async(MediaDatabase._append_media, (path,),
                                      callback=self._append_media_done,
                                      error_callback=error_callback)
            return [result]
        elif path.is_dir():
            return self._append_directory(pool, path)

        return []

    def __init__(self, paths, path_thumbnails):
        self.db = {}
        self.path_thumbnails = path_thumbnails

        self.paths = set((pathlib.Path(path).resolve() for path in paths))

        with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
            async_results = []
            for path in self.paths:
                for result in self._resolve_path(pool, path):
                    if not result.ready():
                        async_results.append(result)

            for result in async_results:
                result.wait()


class MediaDatabasePlugin(object):
    name = "media_database"
    api = 2

    def __init__(self, images_paths, path_thumbnails, keyword="mdb"):
        self.keyword = keyword

        try:
            self.mdb = MediaDatabase(images_paths, path_thumbnails)
        except MediaDatabaseError as e:
            raise bottle.PluginError("Unable to load media database: %s" % e)

    def setup(self, app):
        for other in app.plugins:
            if not isinstance(other, MediaDatabasePlugin):
                continue

            if other.keyword == self.keyword:
                raise bottle.PluginError("Found another '%s' plugin with conflicting settings (non-unique keyword)." % self.name)

    def apply(self, callback, context):
        conf = context.config.get(MediaDatabasePlugin.name) or {}
        keyword = conf.get("keyword", self.keyword)

        if self.keyword not in inspect.signature(callback).parameters:
            return callback

        def wrapper(*args, **kwargs):
            kwargs[keyword] = self.mdb
            return callback(*args, **kwargs)

        return wrapper


class Defaults:
    PROGRAM_NAME = "mediasurf"
    PROGRAM_DESCRIPTION = "MediaSurf media gallery"

    XDG_DATA_HOME = os.getenv("XDG_DATA_HOME") or os.path.join(os.getenv("HOME"), ".local", "share")
    XDG_CACHE_HOME = os.getenv("XDG_CACHE_HOME") or os.path.join(os.getenv("HOME"), ".cache")

    DIR_SYS_DATA = "/usr/local/share"
    DIR_SYS_CACHE = "/var/cache"

    DIR_DATA = os.path.join(XDG_DATA_HOME, PROGRAM_NAME)
    DIR_EPHEMERALS = os.path.join(XDG_CACHE_HOME, PROGRAM_NAME)

    HOST_BIND = "localhost"
    PORT_BIND = 8080

    USER_INTERFACE = "bootstrap5"


class CliOptions(argparse.Namespace):
    def __init__(self, args):
        parser = argparse.ArgumentParser(description=Defaults.PROGRAM_DESCRIPTION)
        parser.add_argument("-d", "--debug", action="store_true", help="Display debug messages")
        parser.add_argument("-v", "--verbose", action="store_true", help="Display informational messages")
        parser.add_argument("-H", "--host", default=Defaults.HOST_BIND, help="Hostname to bind to")
        parser.add_argument("-P", "--port", type=int, default=Defaults.PORT_BIND, help="Port to listen on")
        parser.add_argument("-U", "--user-interface", default=Defaults.USER_INTERFACE, help="Name of the user interface to use")
        # TODO: embed in script, remove option
        parser.add_argument("-D", "--data-dir", default=Defaults.DIR_DATA, help="Path to the directory that holds the data files (e.g. user interfaces)")
        parser.add_argument("-E", "--ephemerals", default=Defaults.DIR_EPHEMERALS, help="Path to the directory that holds ephemeral files (e.g. thumbnails)")
        parser.add_argument("paths", metavar="path", nargs="+", help="Path to the pictures or directories to share")

        parser.parse_args(args, self)


def main(av):
    cli_options = CliOptions(av[1:])

    logging_level = logging.WARN
    if cli_options.debug:
        logging_level = logging.DEBUG
    elif cli_options.verbose:
        logging_level = logging.INFO
    logging.basicConfig(level=logging_level,
                        format="[%(asctime)s][%(levelname)s]: %(message)s")

    logging.debug("Debug messages enabled")

    path_data = pathlib.Path(cli_options.data_dir)
    if not path_data.is_dir():
        path_data = pathlib.Path(Defaults.DIR_SYS_DATA) / Defaults.PROGRAM_NAME
        if not path_data.is_dir():
            logging.critical("No data directory detected")
            return 1

    path_ui = path_data / "ui" / cli_options.user_interface
    if not path_ui.is_dir():
        logging.critical("No such user interface detected: %s", cli_options.user_interface)
        return 1

    path_cache = pathlib.Path(cli_options.ephemerals)
    if not path_cache.is_dir():
        try:
            path_cache.mkdir(parents=True)
        except Exception as e:
            logging.warning("couldn't create the cache directory: %s", e)
            path_cache = pathlib.Path(Defaults.DIR_SYS_CACHE) / Defaults.PROGRAM_NAME
            if not path_cache.is_dir():
                logging.critical("No cache directory detected")
                return 1

    bottle.TEMPLATE_PATH = [path_ui / "templates"]
    # FIXME: the resources will be unpacked in the cache, but they are generated from the ui directory first
    bottle.app().resources = bottle.ResourceManager(str(path_ui / "static") + os.sep)
    bottle.app().resources.add_path(".")

    path_thumbnails = path_cache / "thumbnails"
    try:
        logging.debug("thumbnail directory: %s", path_thumbnails)
        path_thumbnails.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.critical("couldn't create the thumbnail directory: %s", e)
        return 1

    bottle.install(MediaDatabasePlugin(cli_options.paths, path_thumbnails))

    bottle.run(host=cli_options.host, port=cli_options.port,
               debug=cli_options.debug, reloader=cli_options.debug)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
