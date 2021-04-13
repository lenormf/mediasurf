#!/usr/bin/env python3

import os
import sys
import math
import urllib
import hashlib
import pathlib
import inspect
import logging
import argparse
import datetime
import itertools
import collections

# TODO: version dependencies statically
# TODO: remove PIL to only use FFmpeg?
import magic
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


@get("/media/<uuid_media>", name="media_uuid")
def get_media_uuid(mdb, uuid_media):
    assert bottle.app().resources.path

    if uuid_media not in mdb.db:
        raise HttpNotFound()

    path_media = mdb.db[uuid_media].path

    return static_file(path_media.name, root=path_media.parent)


@get("/media/<uuid_media>/thumbnail/<breakpoint>", name="media_uuid_thumbnail")
def get_media_uuid_thumbnail(mdb, uuid_media, breakpoint):
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
    page = mdb.Page(list(mdb.db.values()), request)

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
        self.hash = None
        self.resolution = None
        self.filetime = None
        self.tags = {}
        self.format = None

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

        st = self.path.stat()
        self.filetime = datetime.datetime.fromtimestamp(st.st_ctime)

        try:
            probe = ffmpeg.probe(self.path)
        except ffmpeg.Error as e:
            raise MediaError("unable to open video: %s" % e.stderr)

        # TODO: extract tags if any
        meta_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
        if meta_stream is None:
            raise MediaError("no video stream in the file")

        self.resolution = [meta_stream["width"], meta_stream["height"]]
        self.format = probe["format"]["format_name"]

        # TODO: factorise hashing into the parent class
        h = hashlib.sha1()
        h_data = "%s-%d-%d.%d-%s" % (self.name, str2int(probe["format"]["size"]), self.resolution[0], self.resolution[1], self.format)
        h.update(h_data.encode())
        self.hash = h.hexdigest()

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

        try:
            st = self.path.stat()
            self.filetime = datetime.datetime.fromtimestamp(st.st_ctime)

            with PIL.Image.open(self.path) as im:
                self.resolution = im.size
                self.format = im.format

                for k, v in im.getexif().items():
                    if k in PIL.ExifTags.TAGS:
                        self.tags[PIL.ExifTags.TAGS[k]] = v
                    else:
                        logging.warning("unknown tag index: %s", k)

                h = hashlib.sha1()
                h_data = "%s-%d-%d.%d-%s" % (self.name, st.st_size, im.width, im.height, im.format)
                h.update(h_data.encode())
                self.hash = h.hexdigest()
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


class Date(pp.ParserElement):
    DATE_FORMAT = "%a %b %d %H:%M:%S %Y"
    MAX_DELIM = 5

    def __init__(self, format=DATE_FORMAT, max_delim=MAX_DELIM):
        super().__init__()

        self.format = format or Date.DATE_FORMAT
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

        max_delim = max(self.format.count(" "), self.max_delim)
        previous_delim = loc - 1
        for i in range(max_delim):
            previous_delim = instring.find(" ", previous_delim + 1)
            if previous_delim < 0:
                raise pp.ParseException(instring, loc, self.errmsg, self)

            if self._match_datetime(instring[loc:previous_delim], self.format):
                return previous_delim, instring[loc:previous_delim]

        raise pp.ParseException(instring, loc, self.errmsg, self)


class QueryError(Exception): pass


class QueryParser(collections.OrderedDict):
    TAG_TOKEN = (
        pp.Keyword("tag") + pp.Suppress(":") + pp.MatchFirst(map(pp.CaselessKeyword, PIL.ExifTags.TAGS.values()))
    )

    SORT_TOKEN = (
        pp.Keyword("sort") + pp.Suppress(":")
        + (pp.Keyword("name") | pp.Keyword("date") | TAG_TOKEN)
        + pp.Optional(
            pp.Suppress(":") + pp.oneOf("s n d"),
            default="s",
        )
    )

    ORDER_TOKEN = (
        pp.Keyword("order") + pp.Suppress(":") + (pp.Keyword("asc") | pp.Keyword("desc"))
    )

    SEARCH_TOKEN = (
        (
            (pp.Keyword("name") | pp.Keyword("date"))
            + pp.Suppress(":")
            + (pp.Word(pp.printables)
               | pp.dblQuotedString().setParseAction(pp.removeQuotes)
               | pp.sglQuotedString().setParseAction(pp.removeQuotes))
        ) | TAG_TOKEN
    )

    # TODO: date, from, to should be able to grab dates in EXIF tags

    # TODO: support quoted %c datetimes
    # TODO: support quoted datetimes with hour/minute/second individually
    DATETIME = Date("%Y/%m/%d") | Date("%Y/%m") | Date("%Y")
    FROM_TOKEN = (
        pp.Keyword("from") + pp.Suppress(":") + DATETIME
    )
    TO_TOKEN = (
        pp.Keyword("to") + pp.Suppress(":") + DATETIME
    )

    # TODO: order should only be used right after sort
    QUERY_TOKEN = pp.Group(SORT_TOKEN | ORDER_TOKEN | SEARCH_TOKEN | FROM_TOKEN | TO_TOKEN)

    GRAMMAR = pp.Dict(pp.OneOrMore(QUERY_TOKEN))

    def __init__(self, s, grammar=GRAMMAR):
        try:
            r = grammar.setDebug(logging.getLogger().isEnabledFor(logging.DEBUG)).parseString(s, parseAll=True)

            logging.debug("search query parse results: %s", r)

            self.update(collections.OrderedDict(r))
        except (Exception, pp.ParseException, pp.RecursiveGrammarException, pp.ParseFatalException, pp.ParseSyntaxException) as e:
            raise QueryError("unable to parse query: %s" % e)


class ImagesDatabase:
    class Page:
        def __init__(self, all_entries, request):
            logging.debug("Request form filters: %r", [(k, v) for k, v in request.query.items()])

            def cast_integer(s):
                try:
                    return int(s)
                except ValueError:
                    logging.warning("unable to cast string as integer: %s", s)
                return s

            def cast_date(s):
                for D in QueryParser.DATETIME().streamline().exprs:
                    try:
                        d = D()
                        d.parseString(s, parseAll=True)
                        return datetime.datetime.strptime(s, d.format)
                    except pp.ParseException:
                        pass
                logging.warning("unable to cast string as date: %s", s)
                return s

            def cast_exif_date(s):
                try:
                    return datetime.datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    logging.warning("unable to cast string as date: %s", s)
                return s

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

                    last_sort_key = None
                    for name_filter, predicate in q.items():
                        logging.debug("filter: %s", name_filter)
                        logging.debug("predicate: %s", predicate)

                        if name_filter == "tag":
                            logging.debug("filtering by: %s", name_filter)

                            self.all_entries = filter(lambda x: predicate.lower() in [t.lower() for t in x.tags.keys()],
                                                      self.all_entries)
                        elif name_filter == "sort":
                            logging.debug("filtering by: %s", name_filter)

                            key_sort = predicate[0][0]

                            if key_sort == "tag":
                                cast = predicate[0][2]
                            else:
                                cast = predicate[1]

                            f_cast = {
                                "s": str,
                                "n": cast_integer,
                                "d": cast_date,
                            }[cast]

                            if key_sort == "tag":
                                if cast == "d":
                                    # NOTE: the datetimes in EXIF tags have a standard format
                                    f_cast = cast_exif_date
                                last_sort_key = lambda x: f_cast(x.tags.get(predicate[0][1], ""))
                                self.all_entries = sorted(self.all_entries,
                                                          key=last_sort_key)
                            elif key_sort == "name":
                                last_sort_key = lambda x: lambda x: f_cast(x.name)
                                self.all_entries = sorted(self.all_entries,
                                                          key=last_sort_key)
                            elif key_sort == "date":
                                last_sort_key = lambda x: f_cast(x.filetime)
                                self.all_entries = sorted(self.all_entries,
                                                          key=last_sort_key)
                        elif name_filter == "order":
                            logging.debug("filtering by: %s", name_filter)

                            if last_sort_key:
                                self.all_entries = sorted(self.all_entries, key=last_sort_key, reverse=predicate == "desc")
                        elif name_filter == "name":
                            logging.debug("filtering by: %s", name_filter)

                            self.all_entries = filter(lambda x: predicate.lower() in x.name.lower(),
                                                      self.all_entries)
                        elif name_filter == "date":
                            logging.debug("filtering by: %s", name_filter)

                            date_predicate = cast_date(predicate)
                            logging.debug("date predicate: %s", date_predicate)
                            self.all_entries = filter(lambda x: date_predicate == x.filetime,
                                                      self.all_entries)
                        elif name_filter == "from":
                            logging.debug("filtering by: %s", name_filter)

                            date_predicate = cast_date(predicate)
                            logging.debug("date predicate: %s", date_predicate)
                            self.all_entries = filter(lambda x: x.filetime >= date_predicate,
                                                      self.all_entries)
                        elif name_filter == "to":
                            logging.debug("filtering by: %s", name_filter)

                            # FIXME: to:2021 will set the predicate to Jan 1st 2021 which causes lots of false negatives
                            date_predicate = cast_date(predicate)
                            logging.debug("date predicate: %s", date_predicate)
                            self.all_entries = filter(lambda x: x.filetime <= date_predicate,
                                                      self.all_entries)
                        else:
                            logging.error("unsupported filter: %s", name_filter)
                except QueryError as e:
                    logging.error("couldn't parse query: %s", e)
                    # TODO: signal to the UI that the query is incorrect

            # NOTE: filter() returns a view, and we need a subscriptable list
            self.all_entries = list(self.all_entries)

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

    def __init__(self, paths, path_thumbnails):
        self.db = {}
        self.path_thumbnails = path_thumbnails

        def append_media(path_file):
            logging.info("identifying media: %s", path_file)

            mimetype = magic.from_file(str(path_file), mime=True)
            if mimetype.startswith("image/"):
                logging.debug("media type identified: image")
                ctor = Image
            elif mimetype.startswith("video/"):
                logging.debug("media type identified: video")
                ctor = Video
            else:
                logging.error("unable to identify media type")
                return

            try:
                logging.info("loading media: %s", path_file)

                media = ctor(path_file)
                # NOTE: we use a hash generated by the object itself to be able to lookup thumbnails easily
                uuid_media = media.hash
                self.db[uuid_media] = media
            except MediaError as e:
                logging.error("unable to assign the media to the database: %s", e)

        def append_directory(path_directory):
            logging.info("loading directory: %s", path_directory)

            def on_error(e):
                logging.error("unable to list directory: %s", e)

            for path in path_directory.iterdir():
                if path.is_file():
                    append_media(path)
                elif path.is_dir():
                    append_directory(path)

        for path in paths:
            path = pathlib.Path(path).resolve()
            if path.is_file():
                append_media(path)
            elif path.is_dir():
                append_directory(path)


class MediaDatabasePlugin(object):
    name = "media_database"
    api = 2

    def __init__(self, images_paths, path_thumbnails, keyword="mdb"):
        self.keyword = keyword
        self.mdb = ImagesDatabase(images_paths, path_thumbnails)

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
    # TODO: rebrand as MediaSurf
    PROGRAM_NAME = "imageserv"
    PROGRAM_DESCRIPTION = "ImageServ image gallery"

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

    # FIXME: error when the directory doesn't exist already
    path_cache = pathlib.Path(cli_options.ephemerals)
    if not path_cache.is_dir():
        path_cache = pathlib.Path(Defaults.DIR_SYS_CACHE) / Defaults.PROGRAM_NAME
        if not path_cache.is_dir():
            logging.critical("No cache directory detected")
            return 1

    bottle.TEMPLATE_PATH = [path_ui / "templates"]
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
