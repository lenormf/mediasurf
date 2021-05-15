# MediaSurf - A shareable, extendable, minimalist media gallery

MediaSurf is a web-based utility that displays whatever local media you point it to in a visually appealing, responsive, filterable gallery. It's an ideal solution for users who want to quickly browse a collection of pictures, videos from the command line, or share select media over the net.

Features include:

- support for all common image/video formats
- the gallery is easily shareable with other users over the net
- the thumbnails are laid out in an optimal fashion in any modern browser, and scale dynamically to suit the resolution of the user's device or browser
- a query syntax can be used to filter out and sort the entries
- metadata such as name, file creation date, EXIF tags… are visible beneath their respective thumbnails
- videos are viewable in-place, from the thumbnail view
- the user interface is extendable, and adding additional, custom ones is easy

## Screenshots

![Screenshot of the desktop view, extra large viewport](/images/screenshot-desktop_xl.png)

![Screenshot of the desktop view, large viewport](/images/screenshot-desktop_lg.png)

![Screenshot of the sort widget](/images/screenshot-sort_widget.png)

![Screenshot of the tablet view](/images/screenshot-tablet.png)

![Screenshot of the mobile view](/images/screenshot-mobile.png)

## Docker

A Docker image can be built using the following commands:

```
$ cd docker
$ docker build -t mediasurf .
```

Once the command has successfully completed, use the newly created `mediasurf` image and mount the directory that contains the images to serve onto the `/media` volume:

```
$ docker run -P -v <directory_gallery>:/media mediasurf
```

The MediaSurf interface will be available at http://localhost:8080/

### Build options

The following build options (to pass to the `docker build` command as `--build-arg <option>=<value>` command line arguments) are available:

- `RELEASE`: can be `master` (default) or a custom tag that marks a prior release

## Query syntax

Queries allow filtering out entries from the gallery, and sorting them out. A query is a space separated combination of `command:argument` pairs, which can be written on and sent from the user interface (i.e. the gallery).

### `sort`

Sort entries according to a given field, which can optionally be cast as a special type prior to comparison.

	sort: field : type

- **field**: must be one of `name` , `date` or `tag:tagname` where `tagname` is the name of a file tag, as displayed in the details of the entry.

- **type (opt.)**: must be one of `s` (string), `n` (number) or `d` (date). Defaults to `s`.

#### Examples

	sort:name

	sort:tag:DateTime:d

### `order`

Set the sorting order of the results. Has to be used after the `sort` keyword.

	sort:… order: order

- **order**: must be one of `asc` (ascending) or `desc` (descending).

#### Examples

	sort:… order:asc

	sort:… order:desc

### search

Only display entries that match the given search predicate.

	field : value

- **field**: must be one of `name` , `date` or `tag:tagname` where `tagname` is the name of a file tag, as displayed in the details of the entry.

- **value**: word or whitespace separated list of words enclosed in quotes (simple or double)

#### Examples

	name:IMG_

	date:2010

	tag:Make:Canon

### `from`, `to`

Only display entries created after or before a given date. The `from` and `to` commands can be used together or individually.

	from: date to: date

- **date**: date in one of the following formats: `YYYY/MM/DD` , `YYYY/MM` or `YYYY`.

#### Examples

    from:2010/12/31 to:2020

### `type`

Only display entries of a given media type.

	type: type

- **type**: must be one of `image` or `video`.

#### Examples

    type:image

	type:video
