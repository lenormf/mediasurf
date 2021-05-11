<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <link rel="stylesheet" href="/static/vendor/bootstrap/v5.0.0/css/bootstrap.min.css">
        <link rel="stylesheet" href="/static/vendor/bootstrap-icons/v1.4.1/bootstrap-icons.min.css">

        <link rel="icon" href="/static/image/tsunami.svg" sizes="any" type="image/svg+xml">

        <title>
            MediaSurf - ${page.all_entries_count} entries
        </title>

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
                    <i class="bi bi-tsunami d-inline-block align-text-top"></i>
                    MediaSurf
                </a>

                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
                    <i class="bi bi-list"></i>
                </button>

                <div class="collapse navbar-collapse justify-content-between" id="navbarSupportedContent">
                    <ul class="navbar-nav mb-2 mb-lg-0">
                        <li class="nav-item mb-2 mb-lg-0 me-lg-2">
                            <form method="GET" action="${router.current_url}" id="searchForm">
                                <div class="input-group input-group-sm">
                                    <button class="btn btn-outline-light" type="button" id="searchFormReset">
                                        <i class="bi bi-x"></i>
                                    </button>

                                    <input class="form-control" type="text" name="search" value="${page.search_query or ""}" placeholder="e.g. sort:date:d order:desc">

                                    <button class="btn btn-primary">
                                        <i class="bi bi-search"></i>
                                        search
                                    </button>
                                </div>
                            </form>
                        </li>

                        <li class="nav-item dropdown mb-2 mb-lg-0 me-lg-2">
                            <a class="btn btn-sm btn-outline-secondary dropdown-toggle" href="#" id="navbarDropdownSort" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="bi bi-arrow-down-up"></i>
                                sort
                            </a>

                            ## NOTE: the minimum width accomodates the grouped input form
                            <ul class="dropdown-menu dropdown-menu-dark shadow-sm" aria-labelledby="navbarDropdownSort" style="min-width: 22rem">
                                <li>
                                    <h6 class="dropdown-header">
                                        by name
                                    </h6>
                                </li>

                                <li>
                                    <a class="dropdown-item" href="javascript:appendSearch('sort:name order:asc')">
                                        <i class="bi bi-sort-alpha-down"></i>
                                        ascending
                                    </a>
                                </li>

                                <li>
                                    <a class="dropdown-item" href="javascript:appendSearch('sort:name order:desc')">
                                        <i class="bi bi-sort-alpha-down-alt"></i>
                                        descending
                                    </a>
                                </li>

                                <li>
                                    <h6 class="dropdown-header">
                                        by date
                                    </h6>
                                </li>

                                <li>
                                    <a class="dropdown-item" href="javascript:appendSearch('sort:date order:asc')">
                                        <i class="bi bi-sort-numeric-down"></i>
                                        ascending
                                    </a>
                                </li>

                                <li>
                                    <a class="dropdown-item" href="javascript:appendSearch('sort:date order:desc')">
                                        <i class="bi bi-sort-numeric-down-alt"></i>
                                        descending
                                    </a>
                                </li>

                                <li>
                                    <h6 class="dropdown-header">
                                        by tag
                                    </h6>
                                </li>

                                <li class="px-3 py-1">
                                    <form id="sortTagsForm">
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

                                            <button class="btn btn-secondary">
                                                apply
                                            </button>
                                        </div>
                                    </form>
                                </li>
                            </ul>
                        </li>

                        <li class="nav-item dropdown">
                            <a class="btn btn-sm btn-outline-secondary dropdown-toggle" href="#" id="navbarDropdownFilter" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="bi bi-filter"></i>
                                filter
                            </a>

                            ## NOTE: the minimum width accomodates the grouped input form
                            <ul class="dropdown-menu dropdown-menu-dark shadow-sm" aria-labelledby="navbarDropdownFilter" style="min-width: 22rem">
                                <li>
                                    <h6 class="dropdown-header">
                                        by name
                                    </h6>
                                </li>

                                <li class="px-3 py-1">
                                    <form id="filterNameForm">
                                        <div class="input-group input-group-sm">
                                            <input type="text" class="form-control" id="filterNameInput" placeholder="e.g. IMG_" required>

                                            <button class="btn btn-secondary">
                                                apply
                                            </button>
                                        </div>
                                    </form>
                                </li>

                                <li>
                                    <h6 class="dropdown-header">
                                        by date
                                    </h6>
                                </li>

                                <li class="px-3 py-1">
                                    <form id="filterDateForm">
                                        <div class="input-group input-group-sm">
                                            <input type="text" class="form-control" id="filterDateInput" placeholder="e.g. 2010/12/31" required>

                                            <button class="btn btn-secondary">
                                                apply
                                            </button>
                                        </div>
                                    </form>
                                </li>

                                <li>
                                    <h6 class="dropdown-header">
                                        by date range
                                    </h6>
                                </li>

                                <li class="px-3 py-1">
                                    <form id="filterDateRangeForm">
                                        <div class="input-group input-group-sm">
                                            <input type="text" class="form-control" id="filterDateFromInput" placeholder="e.g. 2010/12/31">
                                            <input type="text" class="form-control" id="filterDateToInput" placeholder="e.g. 2010/12/31">

                                            <button class="btn btn-secondary">
                                                apply
                                            </button>
                                        </div>
                                    </form>
                                </li>

                                <li>
                                    <h6 class="dropdown-header">
                                        by tag
                                    </h6>
                                </li>

                                <li class="px-3 py-1">
                                    <form id="filterTagsForm">
                                        <div class="input-group input-group-sm">
                                            <select class="form-select" id="filterTagsName" required>
                                                <option value="" selected>Pick a tag</option>

                                                % for tag_name in page.tag_sort_keys:

                                                <option value="${tag_name}">${tag_name}</option>

                                                % endfor
                                            </select>

                                            <input type="text" class="form-control" id="filterTagsValueInput" placeholder="e.g. Nokia" required>

                                            <button class="btn btn-secondary">
                                                apply
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

                                % for i in [10, 25, 50, 100, 500]:

                                <li>
                                    <a class="dropdown-item ${"active" if page.limit == i else ""}" href="${page.url_limit(i)}">
                                        ${i}
                                    </a>
                                </li>

                                % endfor
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

                            ${page.page_offset * page.limit + (1 if page.all_entries_count > 0 else 0)} — ${page.page_offset * page.limit + page.entries_count} of ${page.all_entries_count}

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

                <div class="col-12 col-md-6 col-lg-4 col-xl-3 col-xxl-2">

                % else:

                <div class="col-12 col-md-12 col-lg-6 col-xl-4 col-xxl-3">

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
                                        <a class="text-decoration-none link-light" href="${router.get_url("media_uuid", uuid_media=media.hash)}" target="_blank">
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

        <script src="/static/vendor/bootstrap/v5.0.0/js/bootstrap.bundle.min.js"></script>
        <script>
            const searchFormInput = document.querySelector('#searchForm input[name="search"]'),
                  searchFormReset = document.getElementById("searchFormReset"),
                  filterTagsForm = document.getElementById("filterTagsForm"),
                  filterNameForm = document.getElementById("filterNameForm"),
                  filterDateForm = document.getElementById("filterDateForm"),
                  sortTagsForm = document.getElementById("sortTagsForm");

            searchFormReset.onclick = function () {
                searchFormInput.value = "";
            }

            window.appendSearch = function (query) {
                searchFormInput.value += " " + query;
            }

            filterTagsForm.onsubmit = function () {
                const filterTagsName = document.getElementById("filterTagsName"),
                      filterTagsValueInput = document.getElementById("filterTagsValueInput");
                if (filterTagsValueInput.value) {
                    const filter_has_space = filterTagsValueInput.value.indexOf(" ") > -1;
                    appendSearch("tag:" + filterTagsName.value \
                                 + ":"
                                 + (filter_has_space ? '"' + filterTagsValueInput.value + '"' : filterTagsValueInput.value));
                    filterTagsForm.reset();
                }
                return false;
            }

            filterNameForm.onsubmit = function () {
                const filterNameInput = document.getElementById("filterNameInput");
                if (filterNameInput.value) {
                    const filter_has_space = filterNameInput.value.indexOf(" ") > -1;
                    appendSearch("name:" \
                                 + (filter_has_space ? '"' + filterNameInput.value + '"' : filterNameInput.value));
                    filterNameForm.reset();
                }
                return false;
            }

            filterDateForm.onsubmit = function () {
                const filterDateInput = document.getElementById("filterDateInput");
                if (filterDateInput.value) {
                    const filter_has_space = filterDateInput.value.indexOf(" ") > -1;
                    appendSearch("date:" \
                                 + (filter_has_space ? '"' + filterDateInput.value + '"' : filterDateInput.value));
                    filterDateForm.reset();
                }
                return false;
            }

            filterDateRangeForm.onsubmit = function () {
                const filterDateFromInput = document.getElementById("filterDateFromInput");
                if (filterDateFromInput.value) {
                    const filter_has_space = filterDateFromInput.value.indexOf(" ") > -1;
                    appendSearch("from:" \
                                 + (filter_has_space ? '"' + filterDateFromInput.value + '"' : filterDateFromInput.value));
                }

                const filterDateToInput = document.getElementById("filterDateToInput");
                if (filterDateToInput.value) {
                    const filter_has_space = filterDateToInput.value.indexOf(" ") > -1;
                    appendSearch("to:" \
                                 + (filter_has_space ? '"' + filterDateToInput.value + '"' : filterDateToInput.value));
                }

                if (filterDateFromInput.value || filterDateToInput.value) {
                    filterDateRangeForm.reset();
                }

                return false;
            }

            sortTagsForm.onsubmit = function () {
                const sortTagsName = document.getElementById("sortTagsName"),
                      sortTagsCast = document.getElementById("sortTagsCast"),
                      sortTagsAsc = document.getElementById("sortTagsAsc");
                if (sortTagsName.value) {
                    appendSearch("sort:tag:" + sortTagsName.value \
                                 + ":" + (sortTagsCast.value ? sortTagsCast.value : "s") \
                                 + " order:" + (sortTagsAsc.checked ? "asc" : "desc"));
                    sortTagsForm.reset();
                }
                return false;
            }
        </script>
    </body>
</html>
