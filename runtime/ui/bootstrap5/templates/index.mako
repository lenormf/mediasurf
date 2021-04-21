<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        ## TODO: store all vendor libraries statically once Bootstrap5 is released
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-eOJMYsd53ii+scO/bJGFsiCZc+5NDVN2yr8+0RDqr0Ql0h+rP48ckxlpbzKgwra6" crossorigin="anonymous">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.4.1/font/bootstrap-icons.css">

        ## TODO: favicon

        <title>ImageServ</title>

        <style>
            .shadow-xs {
                box-shadow: 0 .0625rem .125rem rgba(0,0,0,.075) !important;
            }

            .rotate-0 {
                transform: rotate(0deg);
            }
            .rotate-90 {
                transform: rotate(90deg);
            }
            .rotate-180 {
                transform: rotate(180deg);
            }
            .rotate-270 {
                transform: rotate(270deg);
            }
            .rotate-360 {
                transform: rotate(360deg);
            }
        </style>
    </head>

    <body class="bg-light">
        <nav class="navbar sticky-top navbar-expand-lg navbar-dark bg-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">
                    <i class="bi bi-camera2 d-inline-block align-text-top"></i>
                    ImageServ
                </a>

                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
                    <i class="bi bi-list"></i>
                </button>

                <div class="collapse navbar-collapse justify-content-between" id="navbarSupportedContent">
                    <form class="mb-2 mb-lg-0" method="GET" action="${router.current_url}" id="searchForm">
                        <div class="input-group input-group-sm">
                            <button class="btn btn-light" type="button" id="searchFormReset">
                                <i class="bi bi-x"></i>
                            </button>

                            <input class="form-control" type="text" name="search" value="${page.search_query or ""}" placeholder="tag, date, name…">

                            <button class="btn btn-primary">
                                <i class="bi bi-search"></i>
                                search
                            </button>
                        </div>
                    </form>

                    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
% if False:
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdownSort" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="bi bi-arrow-down-up"></i>
                                sort
                            </a>

                            ## NOTE: the minimum width accomodates the grouped input form
                            <ul class="dropdown-menu shadow-sm" aria-labelledby="navbarDropdownSort" style="min-width: 22rem">
                                <li>
                                    <h6 class="dropdown-header">
                                        by date
                                    </h6>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.sort_method == "date_asc" else ""}" href="${page.url_sort_date_asc}">
                                        <i class="bi bi-sort-numeric-down"></i>
                                        ascending
                                    </a>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.sort_method == "date_desc" else ""}" href="${page.url_sort_date_desc}">
                                        <i class="bi bi-sort-numeric-down-alt"></i>
                                        descending
                                    </a>
                                </li>

                                <li>
                                    <h6 class="dropdown-header">
                                        by name
                                    </h6>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.sort_method == "name_asc" else ""}" href="${page.url_sort_name_asc}">
                                        <i class="bi bi-sort-alpha-down"></i>
                                        ascending
                                    </a>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.sort_method == "name_desc" else ""}" href="${page.url_sort_name_desc}">
                                        <i class="bi bi-sort-alpha-down-alt"></i>
                                        descending
                                    </a>
                                </li>

                                <li>
                                    <h6 class="dropdown-header">
                                        by tag
                                    </h6>
                                </li>

                                <li class="px-3 py-1">
                                    <form method="GET" action="${router.current_url}" id="sortTagsForm">
                                        <div class="input-group input-group-sm">
                                            <select class="form-select" id="sortTagsName" required>
                                                <option value="" selected>Pick a tag</option>

                                                % for tag_name in page.tag_sort_keys:

                                                <option value="${tag_name}">${tag_name}</option>

                                                % endfor
                                            </select>

                                            <select class="form-select" id="sortTagsCast">
                                                <option value="" selected>Pick a type</option>
                                                <option value="s">string</option>
                                                <option value="n">integer</option>
                                                <option value="d">date</option>
                                            </select>

                                            <div class="input-group-text">
                                                <input class="form-check-input me-1" type="checkbox" id="sortTagsAsc">
                                                <label class="form-check-label" for="sortTagsAsc">
                                                    asc.
                                                </label>
                                            </div>

                                            <input type="hidden" name="sort" id="sortTagsSort">

                                            <button class="btn btn-primary">
                                                sort
                                            </button>
                                        </div>
                                    </form>
                                </li>
                            </ul>
                        </li>
                    </ul>

                    <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdownSort" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="bi bi-list-ol"></i>
                                pagination
                            </a>

                            <ul class="dropdown-menu dropdown-menu-dark shadow-sm" aria-labelledby="navbarDropdownSort">
                                <li>
                                    <h6 class="dropdown-header">
                                        number of items per page
                                    </h6>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.limit == 10 else ""}" href="${page.url_limit(10)}">
                                        10
                                    </a>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.limit == 25 else ""}" href="${page.url_limit(25)}">
                                        25
                                    </a>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.limit == 50 else ""}" href="${page.url_limit(50)}">
                                        50
                                    </a>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.limit == 100 else ""}" href="${page.url_limit(100)}">
                                        100
                                    </a>
                                </li>

                                <li>
                                    <a class="dropdown-item ${"active" if page.limit == 500 else ""}" href="${page.url_limit(500)}">
                                        500
                                    </a>
                                </li>
                            </ul>
                        </li>

                        <li class="nav-item text-light">
                            % if page.has_previous_page:

                            <a class="nav-link d-inline-block" href="${page.url_first_page}" title="Jump to the first page">
                                <i class="bi bi-chevron-bar-left"></i>
                            </a>

                            <a class="nav-link d-inline-block" href="${page.url_previous_page}" title="Jump to the previous page">
                                <i class="bi bi-chevron-compact-left"></i>
                            </a>

                            % else:

                            <a class="nav-link d-inline-block disabled" href="#" title="Jump to the first page">
                                <i class="bi bi-chevron-bar-left"></i>
                            </a>

                            <a class="nav-link d-inline-block disabled" href="#" title="Jump to the previous page">
                                <i class="bi bi-chevron-compact-left"></i>
                            </a>

                            % endif

                            ${page.page_offset * page.limit + 1} — ${page.page_offset * page.limit + page.entries_count} of ${page.all_entries_count}

                            % if page.has_next_page:

                            <a class="nav-link d-inline-block" href="${page.url_next_page}" title="Jump to the next page">
                                <i class="bi bi-chevron-compact-right"></i>
                            </a>

                            <a class="nav-link d-inline-block" href="${page.url_last_page}" title="Jump to the last page">
                                <i class="bi bi-chevron-bar-right"></i>
                            </a>

                            % else:

                            <a class="nav-link d-inline-block disabled" href="#" title="Jump to the next page">
                                <i class="bi bi-chevron-compact-right"></i>
                            </a>

                            <a class="nav-link d-inline-block disabled" href="#" title="Jump to the last page">
                                <i class="bi bi-chevron-bar-right"></i>
                            </a>

                            % endif
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <div class="container-fluid my-2">
            % if page.all_entries_count > 0:

            <div class="row g-1">
                % for i, media in enumerate(page.entries):

                % if media.resolution[0] < media.resolution[1]:

                <div class="col col-md-6 col-lg-4 col-xl-3 col-xxl-2">

                % else:

                <div class="col col-md-12 col-lg-6 col-xl-4 col-xxl-3">

                % endif

                    <div class="card rounded-0 p-1 shadow-xs">
                        <a href="${router.get_url("media_uuid", uuid_media=media.hash)}">
                            % if media.type == "image":

                            <picture class="mw-100">
                                % if media.format.lower() == "gif":

                                <img class="card-img-top rounded-0 border" src="${router.get_url("media_uuid", uuid_media=media.hash)}" loading="lazy">

                                % else:

                                <source srcset="${router.get_url("media_uuid_thumbnail", uuid_media=media.hash, breakpoint="xxl")}" media="(min-width: 1400px)">
                                <source srcset="${router.get_url("media_uuid_thumbnail", uuid_media=media.hash, breakpoint="lg")}" media="(min-width: 992px)">
                                <source srcset="${router.get_url("media_uuid_thumbnail", uuid_media=media.hash, breakpoint="md")}" media="(min-width: 768px)">
                                <img class="card-img-top rounded-0 border" src="${router.get_url("media_uuid_thumbnail", uuid_media=media.hash, breakpoint="sm")}" loading="lazy">

                                % endif
                            </picture>

                            % elif media.type == "video":

                            ## FIXME: find a way to load a breakpoint-specific poster with media-queries
                            <video class="mw-100" controls muted preload="none" poster="${router.get_url("media_uuid_thumbnail", uuid_media=media.hash, breakpoint="xxl")}">
                                <source src="${router.get_url("media_uuid", uuid_media=media.hash)}">
                            </video>

                            % endif
                        </a>

                        <div class="card-img-overlay" style="bottom: inherit">
                            <div class="d-flex justify-content-between">
                                <ul class="list-inline">
                                    % if media.type == "image":

                                    <li class="list-inline-item">
                                        <i class="bi bi-file-image text-light"></i>
                                    </li>

                                    % elif media.type == "video":

                                    <li class="list-inline-item">
                                        <i class="bi bi-file-play-fill text-light"></i>
                                    </li>

                                    % endif

                                    <li class="list-inline-item">
                                        <a class="text-decoration-none link-light" href="${router.get_url("media_uuid", uuid_media=media.hash)}" download="${media.path.name}">
                                            <i class="bi bi-save"></i>
                                        </a>
                                    </li>

                                    <li class="list-inline-item">
                                        <a class="text-decoration-none link-light" href="${router.get_url("media_uuid", uuid_media=media.hash)}">
                                            <i class="bi bi-box-arrow-up-right"></i>
                                        </a>
                                    </li>
                                </ul>

                                ## TODO: implement
                                <ul class="list-inline">
                                    <li class="list-inline-item">
                                        <a class="text-decoration-none link-light" href="#">
                                            <i class="bi bi-arrow-clockwise"></i>
                                        </a>
                                    </li>

                                    <li class="list-inline-item">
                                        <a class="text-decoration-none link-light" href="#">
                                            <i class="bi bi-arrow-counterclockwise"></i>
                                        </a>
                                    </li>
                                </ul>
                            </div>
                        </div>

                        <table class="table table-striped table-sm table-responsive mb-0 mt-1">
                            <tbody>
                                <tr>
                                    <th scope="row" class="h6 lh-base">
                                        name
                                    </th>

                                    <td>
                                        ${media.name}
                                    </td>
                                </tr>

                                <tr>
                                    <th scope="row" class="h6 lh-base">
                                        date
                                    </th>

                                    <td>
                                        ${media.filetime.strftime("%c")}
                                    </td>
                                </tr>
                            </tbody>
                        </table>

                        <div class="accordion accordion-flush" id="accordionTags${i}">
                            <div class="accordion-item">
                                <div class="accordion-header" id="accordionTagsHeading${i}">
                                    <button class="accordion-button collapsed p-1 text-muted" type="button" data-bs-toggle="collapse" data-bs-target="#accordionTagsCollapse${i}" aria-expanded="false" aria-controls="accordionTagsCollapse${i}">
                                        <small>details</small>
                                    </button>
                                </div>

                                <div id="accordionTagsCollapse${i}" class="accordion-collapse collapse" aria-labelledby="accordionTagsHeading${i}" data-bs-parent="#accordionTags${i}">
                                    <div class="accordion-body p-0">
                                        <table class="table table-striped table-sm table-responsive mb-0 mt-1">
                                            <tbody>
                                                <tr>
                                                    <th scope="row" class="h6 lh-base">
                                                        format
                                                    </th>

                                                    <td>
                                                        <span class="badge bg-secondary">
                                                            ${media.format}
                                                        </span>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>

                                        % if media.tags:

                                        <table class="table table-striped table-sm table-responsive mb-0 mt-1">
                                            <thead>
                                                <tr>
                                                    <th scope="col">
                                                        tag
                                                    </th>

                                                    <th scope="col">
                                                        value
                                                    </th>
                                                </tr>
                                            </thead>

                                            <tbody>
                                                % for k, v in media.tags.items():

                                                <tr>
                                                    <th scope="row" class="h6 lh-base">
                                                        ${k}
                                                    </th>

                                                    <td>
                                                        ${v}
                                                    </td>
                                                </tr>

                                                % endfor

                                            </tbody>
                                        </table>

                                        % endif
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                % endfor
            </div>

            % else:

            <div class="row justify-content-center">
                <div class="col col-md-6 col-lg-4">
                    ## FIXME: make it look more appealing, give links
                    <div class="alert alert-light alert-dismissible fade show border" role="alert">
                        No entries! Try tweaking the search query.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                </div>
            </div>

            % endif
        </div>

        ## TODO: footer

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/js/bootstrap.min.js"></script>
        <script>
/*
            const sortTagsForm = document.getElementById("sortTagsForm");
            sortTagsForm.onsubmit = function () {
                const sortTagsName = document.getElementById("sortTagsName"),
                      sortTagsCast = document.getElementById("sortTagsCast"),
                      sortTagsAsc = document.getElementById("sortTagsAsc"),
                      sortTagsSort = document.getElementById("sortTagsSort");
                if (sortTagsName.value) {
                    sortTagsSort.value = "tag:" + sortTagsName.value;
                    sortTagsSort.value += ":" + (sortTagsAsc.checked ? "asc" : "desc");
                    sortTagsSort.value += ":" + (sortTagsCast.value ? sortTagsCast.value : "s");
                }
                return true;
            }
*/

            const searchFormReset = document.getElementById("searchFormReset");
            searchFormReset.onclick = function () {
                const searchFormInput = document.querySelector('#searchForm input[name="search"]');

                searchFormInput.value = "";
            }
        </script>
    </body>
</html>
