// ==UserScript==
// @name         NTISAS-Prebooru
// @namespace    https://github.com/BrokenEagle/JavaScripts
// @version      1.2
// @description  Prebooru addon to NTISAS.
// @source       https://danbooru.donmai.us/users/23799
// @author       BrokenEagle
// @match        https://twitter.com/*
// @require      https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js
// @require      https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js
// @require      https://cdn.jsdelivr.net/npm/jquery-hotkeys@0.2.2/jquery-hotkeys.min.js
// @require      https://cdnjs.cloudflare.com/ajax/libs/validate.js/0.13.1/validate.min.js
// @require      https://cdnjs.cloudflare.com/ajax/libs/localforage/1.9.0/localforage.min.js
// @require      https://cdn.jsdelivr.net/npm/localforage-getitems@1.4.2/dist/localforage-getitems.min.js
// @require      https://cdn.jsdelivr.net/npm/localforage-setitems@1.4.0/dist/localforage-setitems.min.js
// @require      https://cdn.jsdelivr.net/npm/localforage-removeitems@1.4.0/dist/localforage-removeitems.min.js
// @require      https://cdn.jsdelivr.net/npm/xregexp@4.4.1/xregexp-all.min.js
// @require      https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/custom-20190305/custom/qtip_tisas.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/module.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/debug.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/load.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/notice.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/utility.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/statistics.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/storage.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/validate.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/concurrency.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/danbooru.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/saucenao.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/network.js
// @require      https://raw.githubusercontent.com/BrokenEagle/JavaScripts/20220515/lib/menu.js
// @resource     jquery_ui_css https://raw.githubusercontent.com/BrokenEagle/JavaScripts/custom-20190305/custom/jquery_ui_custom.css
// @resource     jquery_qtip_css https://raw.githubusercontent.com/BrokenEagle/JavaScripts/custom-20190305/custom/qtip_tisas.css
// @grant        GM_getResourceText
// @grant        GM.xmlHttpRequest
// @connect      donmai.us
// @connect      saucenao.com
// @connect      twimg.com
// @connect      api.twitter.com
// @connect      google.com
// @connect      googleusercontent.com
// @connect      127.0.0.1
// @run-at       document-body
// @noframes
// ==/UserScript==

// eslint-disable-next-line no-redeclare
/* global $ jQuery JSPLib validate localforage saveAs XRegExp GM_getResourceText GM */

/****Global variables****/

//Library constants

JSPLib.validate.timestamp_constraints = JSPLib.validate.id_constraints;

//Exterior script variables

const PREBOORU_SERVER_URL = 'http://127.0.0.1:5000';

//Variables for load.js
const PROGRAM_LOAD_REQUIRED_SELECTORS = ['[role=region]'];

//Program name constants
const PROGRAM_NAME = 'PREBOORU';
const PROGRAM_SHORTCUT = 'prebooru';
const PROGRAM_CLICK = 'click.prebooru';
const PROGRAM_KEYDOWN = 'keydown.prebooru';

//Variables for storage.js

JSPLib.storage.preboorustorage = localforage.createInstance({
    name: 'Prebooru storage',
    driver: [localforage.INDEXEDDB]
});

//Main program variable
const PREBOORU = {};

const PROGRAM_RESET_KEYS = {
    tweet_pos: [],
    tweet_faves: [],
    tweet_finish: {},
    page_stats: {},
    counted_artists: [],
    counted_tweets: [],
    displayed_errors: new Set(),
};
const PROGRAM_DEFAULT_VALUES = {
    artists: {},
    lists: {},
    update_profile: {},
    tweet_images: {},
    tweet_index: {},
    tweet_qtip: {},
    image_anchor: {},
    qtip_anchor: {},
    image_data: {},
    tweet_dialog: {},
    dialog_anchor: {},
    prebooru_dialog: {},
    prebooru_anchor: {},
    current_pool: false,
    prebooru_data: {},
    prebooru_pool_dialog: {},
    prebooru_pool_anchor: {},
    prebooru_misc_dialog: {},
    prebooru_misc_anchor: {},
    prebooru_similar_dialog: {},
    prebooru_similar_anchor: {},
    similar_results: {},
    no_url_results: [],
    merge_results: [],
    recorded_views: [],
    photo_index: null,
    photo_navigation: false,
    artist_iqdb_enabled: false,
    opened_menu: false,
    colors_checked: false,
    page_locked: false,
    import_is_running: false,
    update_user_timer: null,
    wait: true,
};

//CSS constants

const FONT_FAMILY = '\'Segoe UI\', Arial, sans-serif';
const BASE_PREVIEW_WIDTH = 160;
const POST_PREVIEW_DIMENSION = 150;

const PROGRAM_CSS = `
.prebooru-menu,
.prebooru-prebooru-stub {
    font-size: 16px;
    font-weight: bold;
    font-family: ${FONT_FAMILY};
}
.prebooru-menu {
    display: flex;
    border: 2px solid black;
    padding: 0.5em;
}
.ntisas-stream-tweet .ntisas-tweet-controls {
    margin-top: 0.5em;
    margin-left: -4em;
}
.ntisas-stream-tweet .prebooru-prebooru-header {
    font-size: 1.1em;
}
.ntisas-main-tweet .prebooru-prebooru-header {
    font-size: 1.5em;
}
.ntisas-stream-tweet .prebooru-prebooru-thumbs,
.ntisas-stream-tweet .prebooru-prebooru-similar {
    font-size: 0.8em;
}
.prebooru-link-section {
    padding-left: 0.5em;
}
.prebooru-link-section > div {
    padding: 0.25em;
}
.prebooru-prebooru-controls a {
    padding: 10px;
}
.prebooru-prebooru-controls .ntisas-help-info {
    padding: 8px;
}
.prebooru-prebooru-info {
    font-size: 0.8em;
}
.prebooru-prebooru-info > a:not(.ntisas-help-info) {
    display: inline-block;
    min-width: 70px;
    text-align: center;
}
.prebooru-all-prebooru-upload,
.prebooru-select-prebooru-upload,
.prebooru-prebooru-thumbs,
.prebooru-prebooru-similar {
    color: rgb(27, 149, 224);
}
.prebooru-prebooru-similar.ntisas-active {
    color: #CCC;
}
.ntisas-activated,
.ntisas-activated:hover {
    color: unset;
}
.prebooru-force-prebooru-upload {
    color: goldenrod;
}
.prebooru-force-prebooru-upload.ntisas-activated {
    color: red;
}
.prebooru-prebooru-upload {
    color: green;
}

#prebooru-side-menu {
    font-size: 14px;
    width: 270px;
    font-family: ${FONT_FAMILY};
}
#prebooru-side-border {
    border: solid lightgrey 1px;
}
#prebooru-menu-header {
    padding: 2px;
    font-size: 24px;
    font-weight: bold;
    text-decoration: underline;
    margin-bottom: 0.5em;
}
.prebooru-links a {
    cursor: pointer;
    text-decoration: none;
}
.prebooru-links a:hover {
    text-decoration: underline;
}


.prebooru-confirm-image > p {
    font-weight: 12px;
    padding: 6px;
}
.prebooru-confirm-image b {
    font-weight: bold;
}
.ntisas-similar-results .prebooru-select-controls {
    right: 0;
    top: -5px;
}
.ntisas-post-result .prebooru-select-controls {
    left: 0;
    top: 0;
}
.prebooru-confirm-image .prebooru-select-controls {
    left: 0;
    bottom: -2.5em;
}
.ui-dialog .prebooru-confirm-image.ui-dialog-content {
    overflow: visible;
}
.ntisas-preview-tooltip .prebooru-select-controls a, .ntisas-dialog .prebooru-select-controls a {
    color: dodgerblue;
    font-weight: bold;
    font-size: 14px;
}

.prebooru-post-preview {
    display: inline-block;
    width: ${BASE_PREVIEW_WIDTH}px;
    text-align: center;
    font-family: ${FONT_FAMILY};
}
.prebooru-post-preview img {
    max-width: ${POST_PREVIEW_DIMENSION}px;
    max-height: ${POST_PREVIEW_DIMENSION}px;
    overflow: hidden;
}

.prebooru-post-upload::before {
    content: "";
    display: inline-block;
    background-image: url(data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22iso-8859-1%22%3F%3E%0D%0A%3Csvg%20version%3D%221.1%22%20id%3D%22Capa_1%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20xmlns%3Axlink%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxlink%22%20x%3D%220px%22%20y%3D%220px%22%0D%0A%09%20width%3D%2215%22%20height%3D%2215%22%20viewBox%3D%220%200%2053.867%2053.867%22%20style%3D%22enable-background%3Anew%200%200%2053.867%2053.867%3B%22%20xml%3Aspace%3D%22preserve%22%3E%0D%0A%3Cpolygon%20style%3D%22fill%3A%23EFCE4A%3B%22%20points%3D%2226.934%2C1.318%2035.256%2C18.182%2053.867%2C20.887%2040.4%2C34.013%2043.579%2C52.549%2026.934%2C43.798%20%0D%0A%0910.288%2C52.549%2013.467%2C34.013%200%2C20.887%2018.611%2C18.182%20%22%2F%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3Cg%3E%0D%0A%3C%2Fg%3E%0D%0A%3C%2Fsvg%3E);
    background-repeat: no-repeat;
    background-size: 1em;
    width: 1em;
    height: 1em;
    padding-right: 0.5em;
}
.prebooru-image-container {
    height: ${POST_PREVIEW_DIMENSION}px;
    width: ${POST_PREVIEW_DIMENSION}px;
    border: solid transparent 5px;
}
.prebooru-post-match .prebooru-image-container {
    border: solid green 5px;
}
.prebooru-post-select .prebooru-image-container {
    border: solid black 5px;
}
.prebooru-confirm-image .prebooru-post-select .prebooru-image-container {
    border: solid blue 5px;
}
.prebooru-desc {
    font-size:12px;
    margin-bottom: 2px;
    margin-top: 0;
}
.prebooru-desc-info {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.prebooru-desc-size {
    letter-spacing: -1px;
}
`;

//HTML constants

const HORIZONTAL_RULE = '<div class="ntisas-horizontal-rule"></div>';

const SETTINGS_MENU = `<div id="new-twitter-image-searches-and-stuff" title="${PROGRAM_NAME} Settings"></div>`;

const IMPORT_FILE_INPUT = '<div class="jsplib-menu-item"><h4>Import file</h4><input size="50" type="file" name="ntisas-import-file" id="ntisas-import-file"></div>';

const LIST_INFO_TABLE = '<div id="ntisas-list-info-table" style="display:none"></div>';

const IMPORT_ERROR_DISPLAY = '<div id="ntisas-import-data-errors" style="display:none"></div>';

const PREBOORU_MENU = `
<div class="prebooru-menu ntisas-links" style="display: none;">
    <div style="border-right: 1px solid grey; padding-right: 0.25em;">
        <div class="prebooru-prebooru-header">Prebooru</div>
        <div style="margin: 0.25em -0.4em;">〈&thinsp;<a class="prebooru-prebooru-thumbs ntisas-expanded-link">thumbs</a> | <a class="prebooru-prebooru-similar ntisas-expanded-link">similar</a>&thinsp;〉</div>
    </div>
    <div class="prebooru-link-section"></div>
</div>`;

const PREBOORU_LINK_MENU = `
<div style="min-height: 30px; border-bottom: 1px solid lightgrey;">
    <div class="prebooru-prebooru-controls" style="font-size: 0.9em;">
        Upload&thinsp;<span style="display: inline-block; margin-right: 0.25em; padding: 2.5px 5px; background: #EEE; border: 1px solid black; border-radius: 10px;">
            <a class="prebooru-all-prebooru-upload ntisas-expanded-link">All</a> |
            <a class="prebooru-select-prebooru-upload ntisas-expanded-link">Select</a> |
            <a class="prebooru-force-prebooru-upload ntisas-expanded-link">Force</a>
        </span>
        <span style="display: inline-block; margin-right: 0.25em; padding: 2.5px 5px; background: #EEE; border: 1px solid black; border-radius: 25px;"><a class="prebooru-pool-actions ntisas-expanded-link">Pool</a></span>
        <span style="display: inline-block; margin-right: 0.25em; padding: 2.5px 5px; background: #EEE; border: 1px solid black; border-radius: 25px;"><a class="prebooru-misc-actions ntisas-expanded-link">Misc</a></span>
        ( %CONTROL_HELPLINK% )
    </div>
    <div class="prebooru-prebooru-progress" style="width: 360px; height: 28px; display: none;"></div>
</div>
<div class="prebooru-prebooru-info">
    [
        %INFO_HTML% | %INFO_HELPLINK%
    ]
</div>`;

const SIDE_MENU = `
<div id="prebooru-side-menu" class="prebooru-links" style="position: fixed; top: 55vh; left: 5px; z-index: 1000;">
<div id="prebooru-side-border">
    <div id="prebooru-menu-header">Prebooru</div>
    <div id="prebooru-menu-prebooru" class="prebooru-links" style="padding-left: 5px;">
        <div style="font-size: 18px; font-weight: bold; margin-top: -8px;"><a class="prebooru-expanded-link" style="font-weight: bold; color: dodgerblue; text-decoration: underline;" id="prebooru-select-prior">Prior Pool</a>: <a class="prebooru-expanded-link" target="_blank" style="font-weight: bold; color: orange;" id="prebooru-prior-last">&raquo;</a></div>
        <div style="color: grey;">&emsp;<span id="prebooru-prior-name" style="font-weight: bold;"></span>&emsp;( <span id="prebooru-prior-count"></span> )</div>
        <div style="font-size: 18px; font-weight: bold; margin-top: -8px;"><a class="prebooru-expanded-link" style="font-weight: bold; color: dodgerblue; text-decoration: underline;" id="prebooru-select-pool">Current Pool</a>: <a class="prebooru-expanded-link" target="_blank" style="font-weight: bold; color: orange;" id="prebooru-pool-last">&raquo;</a></div>
        <div style="color: grey;">&emsp;<span id="prebooru-pool-name" style="font-weight: bold;"></span>&emsp;( <span id="prebooru-pool-count"></span> )</div>
        <div style="font-size: 18px; font-weight: bold;"><a class="prebooru-expanded-link" style="font-weight: bold; color: dodgerblue; text-decoration: underline;" id="prebooru-clear-pending">Pending</a>:</div>
        <div style="color: grey;">&emsp;<b>Uploads:</b>&emsp;<span id="prebooru-pending-uploads"></span>&emsp;<b>Pool adds:</b>&emsp;<span id="prebooru-pending-pool-adds"></span></div>
    </div>
    ${HORIZONTAL_RULE}
    <div>
        <span id="prebooru-menu-toggle">
            <a id="prebooru-enable-menu" class="ntisas-expanded-link">Show</a>
            <a id="prebooru-disable-menu" class="ntisas-expanded-link">Hide</a>
        </span>
    </div>
</div>
</div>`;

const SELECTION_CONTROLS = `
<div style="position: absolute" class="prebooru-select-controls ntisas-links">
    [
        <a class="ntisas-expanded-link" data-type="all">all</a> |
        <a class="ntisas-expanded-link" data-type="none">none</a> |
        <a class="ntisas-expanded-link" data-type="invert">invert</a>
    ]
</div>`;

const MINUS_SIGN = `
<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="-20 -40 240 240">
    <path d="M 0,75 L 0,125 L 200,125 L 200,75 L 0,75 z" fill="#F00" />
</svg>`;

const PLUS_SIGN = `
<svg xmlns="http://www.w3.org/2000/svg"  width="15" height="15" viewBox="-20 -40 240 240">
    <path d="M75,0 V75 H0 V125 H75 V200 H125 V125 H200 V75 H125 V0 H75 z" fill="#080" />
</svg>`;

const HIGHLIGHT_HTML = `
<span id="ntisas-artist-toggle">
    <a id="ntisas-enable-highlights" class="ntisas-expanded-link">Enable</a>
    <a id="ntisas-disable-highlights" class="ntisas-expanded-link">Disable</a>
    <span id="ntisas-unavailable-highlights">Unavailable</span>
</span>`;

const FADE_HIGHLIGHT_HTML = `
<a id="ntisas-decrease-fade-level" class="ntisas-expanded-link">${MINUS_SIGN}</a>
<span id="ntisas-current-fade-level">%s</span>
<a id="ntisas-increase-fade-level" class="ntisas-expanded-link">${PLUS_SIGN}</a>`;

const HIDE_HIGHLIGHT_HTML = `
<a id="ntisas-decrease-hide-level" class="ntisas-expanded-link">${MINUS_SIGN}</a>
<span id="ntisas-current-hide-level">%s</span>
<a id="ntisas-increase-hide-level" class="ntisas-expanded-link">${PLUS_SIGN}</a>`;

const VIEWS_HTML = `
<span id="ntisas-views-toggle">
    <a id="ntisas-enable-views" class="ntisas-expanded-link">Show</a>
    <a id="ntisas-disable-views" class="ntisas-expanded-link">Hide</a>
</span>`;

const PROFILE_TIMELINE_HTML = `
<div class="ntisas-profile-section">
    <div class="ntisas-profile-user-id"></div>
    <div class="ntisas-profile-user-view"></div>
    <div class="ntisas-profile-stream-view"></div>
</div>`;

const AUTO_IQDB_HTML = `
<span id="ntisas-iqdb-toggle">
    <a id="ntisas-enable-autoiqdb" class="ntisas-expanded-link">Enable</a>
    <a id="ntisas-disable-autoiqdb" class="ntisas-expanded-link">Disable</a>
    <span id="ntisas-active-autoiqdb">Active</span>
    <span id="ntisas-unavailable-autoiqdb">Unavailable</span>
</span>`;

const LOCKPAGE_HTML = `
<span id="ntisas-lockpage-toggle">
    <a id="ntisas-enable-lockpage" class="ntisas-expanded-link">Lock</a>
    <a id="ntisas-disable-lockpage" class="ntisas-expanded-link" style="display:none">Unlock</a>
</span>`;

const INDICATOR_HTML = `
<span id="ntisas-indicator-toggle">
    <a id="ntisas-enable-indicators" class="ntisas-expanded-link">Show</a>
    <a id="ntisas-disable-indicators" class="ntisas-expanded-link">Hide</a>
</span>`;

const DOWNLOAD_HTML = `
<span id="download-menu-toggle">
    <a id="ntisas-enable-download" class="ntisas-expanded-link">Show</a>
    <a id="ntisas-disable-download" class="ntisas-expanded-link">Hide</a>
</span>`;

const PREBOORU_HTML = `
<span id="prebooru-menu-toggle">
    <a id="ntisas-enable-prebooru" class="ntisas-expanded-link">Show</a>
    <a id="ntisas-disable-prebooru" class="ntisas-expanded-link">Hide</a>
</span>`;

const MEDIA_LINKS_HTML = `
<div class="ntisas-main-links">
    <a class="ntisas-media-link" href="/%SCREENNAME%/media">Media</a>
    <a class="ntisas-media-link" href="/%SCREENNAME%/likes">Likes</a>
</div>`;

const STATUS_MARKER = '<span class="ntisas-status-marker"><span class="ntisas-user-id"></span><span class="ntisas-retweet-id"></span><span class="ntisas-indicators"></span><span class="ntisas-view-info"></span><span class="ntisas-sensitive-info"></span></span>';
const MAIN_COUNTER = '<span id="ntisas-indicator-counter">( <span class="ntisas-count-artist">0</span> , <span class="ntisas-count-tweet">0</span> )</span>';
const TWEET_INDICATORS = '<span class="ntisas-mark-artist">Ⓐ</span><span class="ntisas-mark-tweet">Ⓣ</span><span class="ntisas-count-artist">ⓐ</span><span class="ntisas-count-tweet">ⓣ</span>';
const LOAD_COUNTER = '<span id="ntisas-load-message">Loading ( <span id="ntisas-counter">...</span> )</span>';

const PROFILE_USER_ID = '<b>User ID&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - %s</b>';
const PROFILE_USER_VIEW = 'Viewed user&nbsp;&nbsp; - %s';
const PROFILE_STREAM_VIEW = 'Viewed stream - %s';

//Message constants

const SAVE_HELP = "L-Click to save current settings. (Shortcut: Alt+S)";
const RESET_HELP = "L-Click to reset settings to default. (Shortcut: Alt+R)";
const SETTINGS_HELP = "L-Click to open settings menu. (Shortcut: Alt+M)";
const CLOSE_HELP = "L-Click to close. (Shortcut: Alt+C)";

const NO_MATCH_HELP = "no sources: L-click, manual add posts";
const NO_RESULTS_HELP = "no results: L-click, reset IQDB/Sauce results";
const CHECK_URL_HELP = "URL: L-click, query Danbooru for URL match";
const CHECK_IQDB_HELP = "IQDB: L-click, query Danbooru for image match";
const CHECK_SAUCE_HELP = "Sauce: L-click, query SauceNAO for image match";
const CONFIRM_DELETE_HELP = "postlink: L-click, add/delete info; R-click, open postlink";
const CONFIRM_IQDB_HELP = "postlink: L-click, confirm results; R-click open postlink";
const MERGE_RESULTS_HELP = "Merge: L-click, perform another query and merge with current results";
const IQDB_SELECT_HELP = "Select posts that aren't valid IQDB matches.\nClick the colored postlink when finished to confirm.";
const POST_SELECT_HELP = "Select posts for deletion by clicking the thumbnail.\nLeaving the Delete all checkbox on will select all posts.\nUnsetting that checkbox allows adding posts to the current set.\nClick the colored postlink when finished to delete/add posts.";

const PREBOORU_MENU_HELP = "All: L-click, submit post for upload\nSelect: L-click, choose images to submit for upload\nForce: L-click, toggle forcing upload even if one already exists\n    (yellow = default, red = force)";
const PREBOORU_INFO_HELP = "thumbs: L-click, display post thumbnails (if exist)\nuploadlink: L-click, show/query upload(s) JSON\npostlink: L-click, show/query post(s) JSON\n";

const INSTALL_DATABASE_HELP = "L-Click to install database.";
const UPGRADE_DATABASE_HELP = "L-Click to upgrade database.";
const DATABASE_VERSION_HELP = "L-Click to set record position to latest on Danbooru.\nR-Click to open page to Danbooru records.";
const UPDATE_RECORDS_HELP = "L-Click to update records to current.";
const MUST_INSTALL_HELP = "The database must be installed before the script is fully functional.";
const REFRESH_RECORDS_HELP = "L-Click to refresh record count.";
const AVAILABLE_SAUCE_HELP = "Shows the number of API requests remaining.\nOnly shown after use of the Sauce link.\nResults are kept for only 1 hour.";
const HIGHLIGHTS_HELP = "L-Click to toggle Tweet hiding/fading. (Shortcut: Alt+H)";
const VIEWS_HELP = "L-Click to toggle borders on viewed Tweets. (Shortcut: Alt+V)";
const FADE_HIGHLIGHT_HELP = "L-Click '-' to decrease fade level. (Shortcut: Alt+-)\nL-Click '+' to increase fade level. (Shortcut: Alt+=)";
const HIDE_HIGHLIGHT_HELP = "L-Click '-' to decrease hide level. (Shortcut: Alt+[)\nL-Click '+' to increase hide level. (Shortcut: Alt+])";
const AUTO_IQDB_HELP = "L-Click to toggle auto-IQDB click. (Shortcut: Alt+Q)";
const INDICATOR_HELP = "L-Click to toggle display of Tweet mark/count controls. (Shortcut: Alt+I)";
const DOWNLOAD_HELP = "L-Click to toggle display of Download menu. (Shortcut: Alt+D)";
const PREBOORU_HELP = "L-Click to toggle display of Prebooru menu. (Shortcut: Alt+B)";
const LOCKPAGE_HELP = "L-Click to prevent navigating away from the page (does not prevent Twitter navigation).";
const ERROR_MESSAGES_HELP = "L-Click to see full error messages.";
const STATISTICS_HELP = 'L-Click any category heading to narrow down results.\nL-Click &quot;Total&quot; category to reset results.';

const INSTALL_MENU_TEXT = "Must install DB!";

const SERVER_ERROR = "Failed to connect to remote server to get latest %s!";

const INSTALL_CONFIRM = JSPLib.utility.trim`
This will install the database (%s, %s).
This can take a couple of minutes.

Click OK when ready.`;

const UPGRADE_CONFIRM = JSPLib.utility.trim`
This will upgrade the database to (%s, %s).
Old database is at (%s, %s).
This can take a couple of minutes.

Click OK when ready.`;

const CURRENT_RECORDS_CONFIRM = JSPLib.utility.trim`
This will keep querying Danbooru until the records are current.
Depending on the current position, this could take several minutes.
Moving focus away from the page will halt the process.

Continue?`;

const CURRENT_POSTVER_CONFIRM = JSPLib.utility.trim`
This will query Danbooru for the latest record position to use.
This may potentially cause change records to be missed.

Continue?`;

const MANUAL_ADD_PROMPT = "Enter the post IDs of matches. (separated by commas)";
const CONFIRM_SAVE_PROMPT = "Save the following post IDs? (separate by comma, empty to reset link)";
const CONFIRM_DELETE_PROMPT = JSPLib.utility.trim`
The following posts will be deleted: %s

Save the following post IDs? (separate by comma, empty to delete)`;

//Database constants

const SERVER_DATABASE_URL = 'https://drive.google.com/uc?export=download&id=16YapNscZ0W-tZaRelYF2kDtR31idUd_p';
const SERVER_PURGELIST_URL = 'https://drive.google.com/uc?export=download&id=1uFixlRryOGUzhfvU6nbrkNRAQC4VvO10';
const DATABASE_INFO_URL = 'https://drive.google.com/uc?export=download&id=1evAJM-K6QpHg52997PbXf-bptImLgHDs';

//Time constants

const STORAGE_DELAY = 1; //Don't save lists synchronously since large lists delay UI response
const JQUERY_DELAY = 1; //For jQuery updates that should not be done synchronously
const TWITTER_DELAY = 100; //Give twitter handler some time to change the page
const TIMER_POLL_INTERVAL = 100;
const QUEUE_POLL_INTERVAL = 500;
const PROGRAM_RECHECK_INTERVAL = JSPLib.utility.one_second;
const VIEWCOUNT_RECENT_DURATION = JSPLib.utility.one_minute * 5;
const POST_VERSIONS_CALLBACK = JSPLib.utility.one_second * 5;
const PAGE_REFRESH_TIMEOUT = JSPLib.utility.one_second * 5;
const SAUCE_EXPIRES = JSPLib.utility.one_hour;
const MIN_POST_EXPIRES = JSPLib.utility.one_day;
const MAX_POST_EXPIRES = JSPLib.utility.one_month;
const USER_EXPIRES = JSPLib.utility.one_month;
const VIEW_EXPIRES = JSPLib.utility.one_month * 2;
const SIMILAR_EXPIRES = JSPLib.utility.one_day;
const VIDEO_EXPIRES = JSPLib.utility.one_week;
const LENGTH_RECHECK_EXPIRES = JSPLib.utility.one_hour;
const USER_PROFILE_RECHECK_EXPIRES = JSPLib.utility.one_month;
const DATABASE_RECHECK_EXPIRES = JSPLib.utility.one_day;
const BADVER_RECHECK_EXPIRES = JSPLib.utility.one_day;
const PRUNE_RECHECK_EXPIRES = JSPLib.utility.one_hour * 6;
const CLEANUP_TASK_DELAY = JSPLib.utility.one_minute;
const PROFILE_VIEWS_CALLBACK = JSPLib.utility.one_second * 10;

//Regex constants

var TWITTER_ACCOUNT = String.raw`[\w-]+`;
var TWITTER_ID = String.raw`\d+`;
var QUERY_END = String.raw`(?:\?|$)`;

const TWEET_REGEX = XRegExp.tag('g')`^https://twitter\.com/[\w-]+/status/(\d+)$`;
const TWEET_URL_REGEX = XRegExp.tag('g')`^https://twitter\.com/[\w-]+/status/\d+`;
const TWEET_ID_REGEX = XRegExp.tag()`^https://twitter\.com/[\w-]+/status/(\d+)(?:\?|$)`;
const SOURCE_TWITTER_REGEX = XRegExp.tag('g')`^source:https://twitter\.com/[\w-]+/status/(\d+)$`;

const IMAGE_REGEX = XRegExp.tag()`(https://pbs\.twimg\.com/media/[\w-]+\?format=(?:jpg|png|gif)&name=)(.+)`;
const BANNER_REGEX = XRegExp.tag()`https://pbs\.twimg\.com/profile_banners/(\d+)/\d+/`;

const HANDLED_IMAGES = [{
    regex: XRegExp.tag()`^https://pbs\.twimg\.com/(media|tweet_video_thumb)/([^.?]+)`,
    format: 'https://pbs.twimg.com/%s/%s.%s',
    arguments: (match,extension)=>[match[1], match[2], extension[0]],
},{
    regex: XRegExp.tag()`^https://pbs\.twimg\.com/ext_tw_video_thumb/(\d+)/(\w+)/img/([^.?]+)`,
    format: 'https://pbs.twimg.com/ext_tw_video_thumb/%s/%s/img/%s.jpg',
    arguments: (match)=>[match[1], match[2], match[3]],
},{
    regex: XRegExp.tag()`^https://pbs\.twimg\.com/amplify_video_thumb/(\d+)/img/([^.?]+)`,
    format: 'https://pbs.twimg.com/amplify_video_thumb/%s/img/%s.jpg',
    arguments: (match)=>[match[1], match[2]],
}];
const UNHANDLED_IMAGES = [
    XRegExp.tag()`^https://pbs\.twimg\.com/profile_images/`,
    XRegExp.tag()`^https://[^.]+\.twimg\.com/emoji/`,
    XRegExp.tag()`^https://pbs.twimg.com/ad_img/`,
    XRegExp.tag()`^https://abs.twimg.com/hashflags/`,
    XRegExp.tag()`^https://pbs.twimg.com/card_img/`,
];

var ALL_PAGE_REGEXES = {
    main: {
        format: ' {{no_match}} ({{main_account}}) {{end}} ',
        subs: {
            main_account: TWITTER_ACCOUNT,
            no_match: '(?!search|home)',
            end: QUERY_END,
        }
    },
    media: {
        format: ' ( {{media_account}} ) {{media}} {{end}} ',
        subs: {
            media_account: TWITTER_ACCOUNT,
            media: '/media',
            end: QUERY_END,
        }
    },
    search: {
        format: ' {{search}} ( {{search_query}} ) ',
        subs: {
            search: String.raw`search\?`,
            search_query: String.raw`.*?\bq=.+`,
        }
    },
    tweet: {
        format: ' ( {{tweet_account}} ) {{status}} ( {{tweet_id}} ) {{end}} ',
        subs: {
            tweet_account: TWITTER_ACCOUNT,
            tweet_id: TWITTER_ID,
            status: '/status/',
            end: QUERY_END,
        }
    },
    web_tweet: {
        format: ' {{status}} ( {{web_tweet_id}} ) {{end}} ',
        subs: {
            web: TWITTER_ACCOUNT,
            web_tweet_id: TWITTER_ID,
            status: 'i/web/status/',
            end: QUERY_END,
        }
    },
    hashtag: {
        format: ' {{hashtag}} ( {{hashtag_hash}} ) {{end}} ',
        subs: {
            hashtag: 'hashtag/',
            hashtag_hash: '.+?',
            end: QUERY_END,
        }
    },
    list: {
        format: ' ( {{list_account}} ) {{list}} ( {{list_id}} ) {{end}} ',
        subs: {
            list_account: TWITTER_ACCOUNT,
            list_id: String.raw`[\w-]+`,
            list: '/lists/',
            end: QUERY_END,
        }
    },
    home: {
        format: ' {{home}} {{end}} ',
        subs: {
            home: 'home',
            end: QUERY_END,
        }
    },
    likes: {
        format: ' ( {{likes_account}} ) {{likes}} {{end}} ',
        subs: {
            likes_account: TWITTER_ACCOUNT,
            likes: '/likes',
            end: QUERY_END,
        }
    },
    replies: {
        format: ' ( {{replies_account}} ) {{replies}} {{end}} ',
        subs: {
            replies_account: TWITTER_ACCOUNT,
            replies: '/with_replies',
            end: QUERY_END,
        }
    },
    photo: {
        format: ' ( {{photo_account}} ) {{status}} ( {{photo_id}} ) {{type}} ( {{photo_index}} ) {{end}} ',
        subs: {
            photo_account: TWITTER_ACCOUNT,
            photo_id: TWITTER_ID,
            photo_index: String.raw`\d`,
            type: '/(?:photo|video)/',
            status: '/status/',
            end: QUERY_END,
        }
    },
    moments: {
        format: ' {{moments}} ( {{moment_id}} ) {{end}} ',
        subs: {
            moment_account: TWITTER_ACCOUNT,
            moment_id: TWITTER_ID,
            moments: 'i/moments/',
            end: QUERY_END,
        }
    },
    display: {
        format: ' {{display}} {{end}} ',
        subs: {
            display: 'i/display',
            end: QUERY_END,
        }
    },
};

//Network constants

const QUERY_LIMIT = 100;
const QUERY_BATCH_NUM = 5;
const QUERY_BATCH_SIZE = QUERY_LIMIT * QUERY_BATCH_NUM;

const POST_FIELDS = 'id,uploader_id,score,fav_count,rating,tag_string,created_at,preview_file_url,source,file_ext,file_size,image_width,image_height,uploader[name]';
const POSTVER_FIELDS = 'id,updated_at,post_id,version,source,source_changed,added_tags,removed_tags';
const PROFILE_FIELDS = 'id,level';

//DOM constants

const HIGHLIGHT_CONTROLS = ['enable', 'disable', 'unavailable'];
const VIEW_CONTROLS = ['enable', 'disable'];
const IQDB_CONTROLS = ['enable', 'disable', 'active', 'unavailable'];
const INDICATOR_CONTROLS = ['enable', 'disable'];
const PREBOORU_CONTROLS = ['enable', 'disable'];
const DOWNLOAD_CONTROLS = ['enable', 'disable'];

const ALL_INDICATOR_TYPES = ['mark-artist', 'mark-tweet', 'count-artist', 'count-tweet'];

const BASE_DIALOG_WIDTH = 60;
const BASE_QTIP_WIDTH = 10;

//Queue constants

const QUEUED_STORAGE_REQUESTS = [];
const SAVED_STORAGE_REQUESTS = [];
const CACHED_STORAGE_REQUESTS = {};
const CACHE_STORAGE_TYPES = ['get','check'];
const STORAGE_DATABASES = {
    danbooru: JSPLib.storage.danboorustorage,
    twitter: JSPLib.storage.twitterstorage,
    prebooru: JSPLib.storage.preboorustorage,
};

const QUEUED_NETWORK_REQUESTS = [];
const SAVED_NETWORK_REQUESTS = [];
const NETWORK_REQUEST_DICT = {
    posts: {
        data_key: "id",
        params (post_ids) {
            return {
                tags: 'status:any id:' + post_ids.join(','),
                only: POST_FIELDS,
                limit: 200,
            };
        },
    },
    users: {
        data_key: "id",
        params (user_ids) {
            return {
                search: {
                    id: user_ids.join(','),
                },
                only: 'id,name',
                limit: 1000,
            };
        },
    },
};

//Other constants

const STREAMING_PAGES = ['home', 'main', 'likes', 'replies', 'media', 'list', 'search', 'hashtag', 'moment'];
const MEDIA_TYPES = ['images', 'media', 'videos'];

const ALL_LISTS = {
    highlight: 'no-highlight-list',
    iqdb: 'auto-iqdb-list',
    artist: 'artist-list',
    tweet: 'tweet-list'
};

const GOLD_LEVEL = 30;

//UI constants

const PREVIEW_QTIP_SETTINGS = {
    style: {
        classes: 'qtiptisas-twitter ntisas-preview-tooltip',
    },
    position: {
        my: 'top center',
        at: 'bottom center',
        viewport: true,
    },
    show: {
        delay: 500,
        solo: true,
    },
    hide: {
        delay: 250,
        fixed: true,
        leave: false, // Prevent hiding when cursor hovers a browser tooltip
    }
};

const IMAGE_QTIP_SETTINGS = {
    style: {
        classes: 'qtiptisas-twitter ntisas-image-tooltip',
    },
    position: {
        my: 'center',
        at: 'center',
        viewport: false,
    },
    show: {
        delay: 1000,
        solo: true,
    },
    hide: {
        delay: 100,
        fixed: true,
    }
};

const MENU_QTIP_SETTINGS = {
    style: {
        classes: 'qtiptisas-twitter ntisas-menu-tooltip',
    },
    position: {
        my: 'center',
        at: 'center',
        viewport: true,
    },
    show: {
        delay: 100,
        solo: true,
    },
    hide: {
        delay: 100,
        fixed: true,
    }
};

const CONFIRM_DIALOG_SETTINGS = {
    title: "Image select",
    modal: true,
    resizable:false,
    autoOpen: false,
    classes: {
        'ui-dialog': 'ntisas-dialog',
        'ui-dialog-titlebar-close': 'ntisas-dialog-close'
    },
    open: function () {
        this.promiseConfirm = new Promise((resolve)=>{this.resolveConfirm = resolve;});
    },
    close: function () {
        this.resolveConfirm && this.resolveConfirm(false);
    },
    buttons: {
        'Submit': function () {
            this.resolveConfirm && this.resolveConfirm(true);
            $(this).dialog('close');
        },
        'Cancel': function () {
            this.resolveConfirm && this.resolveConfirm(false);
            $(this).dialog('close');
        }
    }
};

const PREBOORU_DIALOG_SETTINGS = {
    title: "Prebooru thumbnails",
    modal: true,
    resizable:false,
    autoOpen: false,
    classes: {
        'ui-dialog': 'ntisas-dialog',
        'ui-dialog-titlebar-close': 'ntisas-dialog-close'
    },
    open: function () {
        this.promiseData = null;
        this.promiseConfirm = new Promise((resolve)=>{this.resolveConfirm = resolve;});
    },
    close: function () {
        this.resolveConfirm && this.resolveConfirm(this.promiseData);
    },
    buttons: {
        'Close': function () {
            $(this).dialog('close');
        },
    }
};

const MENU_DIALOG_BUTTONS = {
    'Save': {
        id: 'ntisas-commit',
        title: SAVE_HELP
    },
    'Factory reset': {
        id: 'ntisas-resetall',
        title: RESET_HELP
    },
    'Close': {
        id: null,
        title: CLOSE_HELP
    }
};

//Validation constants

const POST_CONSTRAINTS = {
    entry: JSPLib.validate.hashentry_constraints,
    value: {
        id: JSPLib.validate.id_constraints,
        uploaderid: JSPLib.validate.id_constraints,
        uploadername: JSPLib.validate.stringonly_constraints,
        score: JSPLib.validate.integer_constraints,
        favcount: JSPLib.validate.counting_constraints,
        rating: JSPLib.validate.inclusion_constraints(['s', 'q', 'e']),
        tags: JSPLib.validate.stringonly_constraints,
        created: JSPLib.validate.counting_constraints,
        thumbnail: JSPLib.validate.stringonly_constraints,
        source: JSPLib.validate.stringonly_constraints,
        ext: JSPLib.validate.inclusion_constraints(['jpg', 'png', 'gif', 'mp4', 'webm']),
        size: JSPLib.validate.counting_constraints,
        width: JSPLib.validate.counting_constraints,
        height: JSPLib.validate.counting_constraints
    }
};

const USER_CONSTRAINTS = {
    entry: JSPLib.validate.hashentry_constraints,
    value: {
        id: JSPLib.validate.id_constraints,
        name: JSPLib.validate.stringonly_constraints,
    }
};

const VIEW_CONSTRAINTS = {
    entry: JSPLib.validate.hashentry_constraints,
    value: {
        count: JSPLib.validate.counting_constraints,
        viewed: JSPLib.validate.counting_constraints,
    },
};

const SIMILAR_CONSTRAINTS = {
    expires: JSPLib.validate.expires_constraints,
    value: JSPLib.validate.boolean_constraints
};

const VIDEO_CONSTRAINTS = {
    expires: JSPLib.validate.expires_constraints,
    value: JSPLib.validate.stringnull_constraints
};

const TWUSER_CONSTRAINTS = {
    expires: JSPLib.validate.expires_constraints,
    value: JSPLib.validate.stringonly_constraints,
};

const SAUCE_CONSTRAINTS = {
    expires: JSPLib.validate.expires_constraints,
    value: JSPLib.validate.integer_constraints
};

const COLOR_CONSTRAINTS = {
    base_color: JSPLib.validate.array_constraints({is: 3}),
    text_color: JSPLib.validate.array_constraints({is: 3}),
    background_color: JSPLib.validate.array_constraints({is: 3})
};

const PROFILE_CONSTRAINTS = {
    id: JSPLib.validate.id_constraints,
    level: JSPLib.validate.id_constraints,
};

const DATABASE_CONSTRAINTS = {
    post_version: JSPLib.validate.id_constraints,
    timestamp: JSPLib.validate.timestamp_constraints,
};

/****Functions****/

//Library functions

//// None

//Helper functions

////Make setting all of these into a library function
function GetLocalData(key,default_val) {
    return JSPLib.storage.getStorageData(key, localStorage, default_val);
}

function SetLocalData(key,data) {
    JSPLib.storage.setStorageData(key, data, localStorage);
}

function InvalidateLocalData(key) {
    JSPLib.storage.invalidateStorageData(key, localStorage);
}

function GetSessionTwitterData(tweet_id) {
    return JSPLib.storage.getIndexedSessionData('tweet-' + tweet_id, [], STORAGE_DATABASES.twitter);
}

function GetDomDataIds($obj, key) {
    let data = $obj.data(key);
    if (Number.isInteger(data)) {
        return [data];
    }
    if (Array.isArray(data)) {
        return data;
    }
    if (!data) {
        return [];
    }
    try {
        return data.split(',').map(Number);
    } catch (e) {
        JSPLib.notice.debugError("Error: GetDomDataIds");
        JSPLib.debug.debugerror("Bad data", data, e);
        return [];
    }
}

function LocalPrebooruData(tweet_id, type) {
    let plural = type + 's';
    if (!(tweet_id in PREBOORU.prebooru_data)) {
        PREBOORU.prebooru_data[tweet_id] = {};
    }
    if (!(plural in PREBOORU.prebooru_data[tweet_id])) {
        PREBOORU.prebooru_data[tweet_id][plural] = JSPLib.storage.getIndexedSessionData(plural + '-' + tweet_id, [], STORAGE_DATABASES.prebooru);
    }
    return PREBOORU.prebooru_data[tweet_id][plural] || [];
}

function SetPrebooruData(tweet_id, plural, ids, override=true) {
    if (!(tweet_id in PREBOORU.prebooru_data)) {
        PREBOORU.prebooru_data[tweet_id] = {};
    }
    if (override || !(plural in PREBOORU.prebooru_data[tweet_id])) {
        PREBOORU.prebooru_data[tweet_id][plural] = ids;
    } else {
        PREBOORU.prebooru_data[tweet_id][plural] = JSPLib.utility.arrayUnion(PREBOORU.prebooru_data[tweet_id][plural], ids);
    }
}

function DtextNotice(str) {
    let position = 0;
    let output = "";
    do {
        let substr = str.slice(position);
        var match = substr.match(/\b(booru|artist|illust|post|upload|pool|notation) #(\d+)\b/);
        let endpos = (match ? match.index + position : undefined);
        output += str.slice(position, endpos);
        if (match) {
            output += `<a href="${PREBOORU_SERVER_URL}/${match[1]}s/${match[2]}">${match[1]} #${match[2]}</a>`
            position += match.index + match[0].length;
        }
    } while (match);
    return output;
}

function JSONNotice(data) {
    JSPLib.notice.notice('<pre>' + JSON.stringify(data, null, 2) + '</pre>', false, true);
}

function GetNumericTimestamp(timestamp) {
    return GetDateString(timestamp) + GetTimeString(timestamp);
}

function GetDateString(timestamp) {
    let time_obj = new Date(timestamp);
    return `${time_obj.getFullYear()}${JSPLib.utility.padNumber(time_obj.getMonth() + 1, 2)}${JSPLib.utility.padNumber(time_obj.getDate() ,2)}`;
}

function GetTimeString(timestamp) {
    let time_obj = new Date(timestamp);
    return `${JSPLib.utility.padNumber(time_obj.getHours(), 2)}${JSPLib.utility.padNumber(time_obj.getMinutes(), 2)}`;
}

function ParseQueries(str) {
    return str.split(' ').reduce(function (params, param) {
        var paramSplit = param.split(':');
        params[paramSplit[0]] = paramSplit[1];
        return params;
    }, {});
}

//This needs its own separate validation because it should not be exported
function GetRemoteDatabase() {
    let data = GetLocalData('ntisas-remote-database');
    return (JSPLib.validate.validateHashEntries('ntisas-remote-database', data, DATABASE_CONSTRAINTS) ? data : null);
}

function IsTISASInstalled() {
    return GetRemoteDatabase() !== null;
}

function MapPostData(posts) {
    return posts.map(MapPost);
}

function MapPost(post) {
    return {
        id: post.id,
        uploaderid: post.uploader_id,
        uploadername: ('uploader' in post ? post.uploader.name : null),
        score: post.score,
        favcount: post.fav_count,
        rating: post.rating,
        tags: post.tag_string,
        created: new Date(post.created_at).getTime(),
        thumbnail: post.preview_file_url,
        source: post.source,
        ext: post.file_ext,
        size: post.file_size,
        width: post.image_width,
        height: post.image_height
    };
}

function MapSimilar(post,score) {
    return {
        score: score,
        post: post
    };
}

function GetLinkTitle(post) {
    let tags = JSPLib.utility.HTMLEscape(post.tags);
    let age = JSPLib.utility.HTMLEscape(`age:"${JSPLib.utility.timeAgo(post.created)}"`);
    return `user:${post.uploadername} score:${post.score} favcount:${post.favcount} rating:${post.rating} ${age} ${tags}`;
}

function GetMultiLinkTitle(posts) {
    let title = [];
    posts.forEach((post)=>{
        let age = JSPLib.utility.HTMLEscape(`age:"${JSPLib.utility.timeAgo(post.created)}"`);
        title.push(`post #${post.id} - user:${post.uploadername} score:${post.score} favcount:${post.favcount} rating:${post.rating} ${age}`);
    });
    return title.join('\n');
}

async function GetTotalRecords(manual=false) {
    if (manual || JSPLib.concurrency.checkTimeout('ntisas-length-recheck', LENGTH_RECHECK_EXPIRES)) {
        let database_length = await STORAGE_DATABASES.twitter.length();
        SetLocalData('ntisas-database-length', database_length);
        JSPLib.concurrency.setRecheckTimeout('ntisas-length-recheck', LENGTH_RECHECK_EXPIRES);
    }
    return GetLocalData('ntisas-database-length', 0);
}

function ReadableBytes(bytes) {
    var i = Math.floor(Math.log(bytes) / Math.log(1024)),
    sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    return JSPLib.utility.setPrecision((bytes / Math.pow(1024, i)), 2) + ' ' + sizes[i];
}

function GetFileExtension(url,splitter=' ') {
    let parser = new URL(url);
    let pathname = parser.pathname.split(splitter)[0];
    let extpos = pathname.lastIndexOf('.');
    return pathname.slice(extpos + 1);
}

function GetThumbUrl(url,splitter,ext,size) {
    let parser = new URL(url);
    let pathname = parser.pathname.split(splitter)[0];
    let extpos = pathname.lastIndexOf('.');
    return parser.origin + pathname.slice(0, extpos) + `?format=${ext}&name=${size}`;
}

function GetFileURLNameExt(file_url) {
    let path_index = file_url.lastIndexOf('/');
    let file_ident = file_url.slice(path_index + 1);
    let [file_name,extension] = file_ident.split('.');
    extension = extension.split(/\W+/)[0];
    return [file_name, extension];
}

function GetNormalImageURL(image_url) {
    let extension = JSPLib.utility.arrayIntersection(image_url.split(/\W+/), ['jpg', 'png', 'gif']);
    for (let i = 0; i < HANDLED_IMAGES.length; i++) {
        let match = image_url.match(HANDLED_IMAGES[i].regex);
        if (match && extension.length !== 0) {
            return JSPLib.utility.sprintf(HANDLED_IMAGES[i].format, ...HANDLED_IMAGES[i].arguments(match, extension));
        }
    }
    for (let i = 0; i < UNHANDLED_IMAGES.length; i++) {
        let match = image_url.match(UNHANDLED_IMAGES[i]);
        if (match) {
            return null;
        }
    }
    return false;
}

function GetNomatchHelp(no_url_results,no_iqdb_results,no_sauce_results) {
    let help_info = [NO_MATCH_HELP];
    if (no_iqdb_results || no_sauce_results) {
        help_info.push(NO_RESULTS_HELP);
    }
    if (!no_url_results) {
        help_info.push(CHECK_URL_HELP);
    }
    if (!no_iqdb_results) {
        help_info.push(CHECK_IQDB_HELP);
    }
    if (!no_sauce_results) {
        help_info.push(CHECK_SAUCE_HELP);
    }
    return help_info.join('\n');
}

function RemoveDuplicates(obj_array,attribute){
    const attribute_index = JSPLib.utility.getObjectAttributes(obj_array, attribute);
    return obj_array.filter((obj,index) => (attribute_index.indexOf(obj[attribute]) === index));
}

function LogarithmicExpiration(count, max_count, time_divisor, multiplier) {
    let time_exponent = Math.pow(10, (1 / time_divisor));
    return Math.round(Math.log10(time_exponent + (10 - time_exponent) * (count / max_count)) * multiplier);
}

//Auxiliary functions

function UploadsQuery(screen_name, tweet_id) {
    let request_url = `https://twitter.com/*/status/${tweet_id}`;
    return {request_url_like: request_url};
}

function PostsQuery(tweet_id) {
    return {illust_urls:{illust: {site_illust_id: tweet_id, site_id: 3}}};
}

function IllustsQuery(tweet_id) {
    return {site_illust_id: tweet_id, site_id: 3};
}

function ArtistsQuery(account) {
    return {current_site_account: account, site_id: 3};
}

function DisplayControl(control,all_controls,type) {
    let all_selectors = JSPLib.utility.joinList(all_controls, '#prebooru-', '-' + type, ',');
    $(all_selectors).hide();
    console.log('DisplayControl', control, all_controls, type, all_selectors, `#ntisas-${control}-${type}`);
    setTimeout(()=>{$(`#prebooru-${control}-${type}`).show();}, JQUERY_DELAY);
}

function GetImageLinks(tweet) {
    let $obj = $('[ntisas-media-type=image] [data-image-url], [ntisas-media-type=video] [data-image-url]', tweet).sort((entrya,entryb)=>($(entrya).data('image-num') - $(entryb).data('image-num')));
    return JSPLib.utility.getDOMAttributes($obj, 'image-url');
}

function GetTweetStat(tweet,types) {
    for (let i = 0; i < types.length; i++) {
        let label = $(`[data-testid=${types[i]}]`, tweet).attr('aria-label');
        let match = label && label.match(/\d+/);
        if (match) {
            return parseInt(match[0]);
        }
    }
    return 0;
}

function SetThumbnailWait(container,all_posts) {
    all_posts.forEach(async (post)=>{
        let blob = await JSPLib.network.getData(post.thumbnail);
        let image_blob = blob.slice(0, blob.size, 'image/jpeg');
        let blob_url = window.URL.createObjectURL(image_blob);
        $(`[data-id=${post.id}] img`, container).attr('src', blob_url);
    });
}

//Checks and removes a value from a hash key if it exists
function RemoveHashKeyValue(hash,key,value) {
    if ((key in hash) && hash[key].includes(value)) {
        hash[key] = JSPLib.utility.arrayDifference(hash[key], [value]);
        if (hash[key].length === 0) {
            delete hash[key];
        }
        return true;
    }
    return false;
}

function UpdatePrebooruMenu() {
    if($('#prebooru-side-menu').length === 0) {
        $('header[role=banner]').after(SIDE_MENU);
        Promise.all([
            JSPLib.storage.retrieveData('prebooru-prebooru-pool', false, STORAGE_DATABASES.prebooru),
            JSPLib.storage.retrieveData('ntisas-prior-pool', false, STORAGE_DATABASES.prebooru)
            ]).then(([current_pool, prior_pool])=>{
            PREBOORU.current_pool = current_pool;
            PREBOORU.prior_pool = prior_pool;
            UpdatePoolDisplay();
        });
        GetUploadRecords();
        PREBOORU.failed_pool_adds = GetLocalData('ntisas-failed-pool-adds', []);
        $('#prebooru-select-pool').on(PROGRAM_CLICK, ChooseCurrentPool);
        $('#prebooru-select-prior').on(PROGRAM_CLICK, ChoosePriorPool);
        $('#prebooru-clear-pending').on(PROGRAM_CLICK, (event)=>{
            if (confirm("Empty all upload data?")) {
                PREBOORU.upload_records = [];
                SetUploadRecords();
            }
            event.preventDefault();
        });
        $('#prebooru-menu-toggle a').on(PROGRAM_CLICK, ToggleLinkMenu);
    }
}

function UpdatePrebooruItems(tweet_id, item_ids, type, all_idents=null, message=true) {
    let plural = type + 's';
    if (Array.isArray(all_idents) && all_idents.length) {
        let screen_name = all_idents.find((ident) => !Number.isInteger(Number(ident)));
        var $tweet = $(`.ntisas-tweet[data-screen-name=${screen_name}]`);
    } else {
        $tweet = $(`.ntisas-tweet[data-tweet-id=${tweet_id}]`);
    }
    if (item_ids.length === 1) {
        var item_label = "1 " + type;
    } else {
        item_label = item_ids.length + ' ' + plural;
    }
    let href = PREBOORU_SERVER_URL + '/' + plural;
    if (item_ids.length === 1) {
        href += '/' + item_ids[0];
    } else {
        href += '?search[id]=' + item_ids.join(',');
    }
    let link_html = `<a style="color: green;" class="prebooru-prebooru-${plural} ntisas-expanded-link" href="${href}">${item_label}</a>`;
    let $plural = $tweet.find('.prebooru-prebooru-' + plural);
    let $info = $tweet.find('.prebooru-menu');
    $plural.html(link_html);
    $info.data(type + '-ids', item_ids);
    if (message) {
        PREBOORU.channel.postMessage({type: 'preboorulink', subtype: type, tweet_id, item_ids, all_idents});
    }
}

function UpdatePoolDisplay(other_pool=null) {
    if ( PREBOORU.current_pool) {
        $('#prebooru-pool-name').html(JSPLib.utility.maxLengthString( PREBOORU.current_pool.name), 30);
        $('#prebooru-pool-count').text( PREBOORU.current_pool.element_count);
        if (PREBOORU.pool_selection_dialog) {
            $(`.ntisas-pool[data-id=${PREBOORU.current_pool.id}] .ntisas-pool-count`).text(PREBOORU.current_pool.element_count);
        }
        $('#prebooru-select-pool').attr('href', `${PREBOORU_SERVER_URL}/pools/${PREBOORU.current_pool.id}`);
        $('#prebooru-pool-last').attr('href', `${PREBOORU_SERVER_URL}/pools/${PREBOORU.current_pool.id}/last`).show();
    } else {
        $('#prebooru-pool-name').html('<i>NONE</i>');
        $('#prebooru-pool-count').text('N/A');
        $('#prebooru-select-pool').attr('href', `${PREBOORU_SERVER_URL}/posts`);
        $('#prebooru-pool-last').attr('href', "").hide();
    }
    if (PREBOORU.prior_pool) {
        $('#prebooru-prior-name').html(JSPLib.utility.maxLengthString(PREBOORU.prior_pool.name), 30);
        $('#prebooru-prior-count').text(PREBOORU.prior_pool.element_count);
        if (PREBOORU.pool_selection_dialog) {
            $(`.ntisas-pool[data-id=${PREBOORU.prior_pool.id}] .ntisas-pool-count`).text(PREBOORU.prior_pool.element_count);
        }
        $('#prebooru-select-prior').attr('href', `${PREBOORU_SERVER_URL}/pools/${PREBOORU.prior_pool.id}`);
        $('#prebooru-prior-last').attr('href', `${PREBOORU_SERVER_URL}/pools/${PREBOORU.prior_pool.id}/last`).show();
    } else {
        $('#prebooru-prior-name').html('<i>NONE</i>');
        $('#prebooru-prior-count').text('N/A');
        $('#prebooru-select-prior').attr('href', `${PREBOORU_SERVER_URL}/posts`);
        $('#prebooru-prior-last').attr('href', "").hide();
    }
    if (other_pool !== null) {
        $(`.ntisas-pool[data-id=${other_pool.id}] .ntisas-pool-count`).text(other_pool.element_count);
    }
}

function UpdateUploadRecords(message=true) {
    if (message && PREBOORU.upload_records) {
        SetLocalData('ntisas-pending-uploads', PREBOORU.upload_records);
        PREBOORU.channel.postMessage({type: 'pendinguploads', upload_records: PREBOORU.upload_records});
    } else if (!PREBOORU.upload_records) {
        PREBOORU.upload_records = GetLocalData('ntisas-pending-uploads', []);
    }
    $('#prebooru-pending-uploads').text(PREBOORU.upload_records.length);
}

function UpdateUploadCounters() {
    $('#prebooru-pending-uploads').text(PREBOORU.upload_records.filter((record) => record.status === 'pending').length);
    $('#prebooru-pending-pool-adds').text(PREBOORU.upload_records.filter((record) => record.status === 'complete').length);
}

function SetUploadRecords() {
    SetLocalData('ntisas-pending-uploads', PREBOORU.upload_records);
    PREBOORU.upload_records_uid = JSPLib.utility.getUniqueID();
    localStorage.setItem('ntisas-uploads-uid', PREBOORU.upload_records_uid);
    UpdateUploadCounters();
}

function GetUploadRecords() {
    PREBOORU.upload_records_uid = localStorage.getItem('ntisas-uploads-uid');
    PREBOORU.upload_records = GetLocalData('ntisas-pending-uploads', []);
    UpdateUploadCounters();
}

function RefreshUploadRecords() {
    let temp_uid = localStorage.getItem('ntisas-uploads-uid');
    if (PREBOORU.upload_records_uid != temp_uid) {
        InvalidateLocalData('ntisas-pending-uploads');
        GetUploadRecords();
    }
}

function ShowProgressBar($tweet) {
    $tweet.find('.prebooru-prebooru-controls').hide();
    $tweet.find('.prebooru-prebooru-progress').progressbar({value: false}).show();
}

function HideProgressBar($tweet) {
    $tweet.find('.prebooru-prebooru-progress').progressbar('destroy').hide();
    $tweet.find('.prebooru-prebooru-controls').show();
}

function ProcessPrebooruUpload(post_data,tweet_id,$tweet,type,screen_name,user_id) {
    InitializeUIStyle();
    ShowProgressBar($tweet);
    let backup_cancel = setTimeout(($tweet)=>{HideProgressBar($tweet);}, 10000);
    $.post(PREBOORU_SERVER_URL + '/uploads.json', post_data, null, 'json').then((resp)=>{
        if (resp.error) {
            JSPLib.notice.error(resp.message);
            if (resp.message.match('Upload already exists')) {
                let upload_query_data = UploadsQuery(screen_name, tweet_id);
                let upload_promise = QueryPrebooruData(tweet_id, 'upload', upload_query_data);
                let post_query_data = PostsQuery(tweet_id);
                let post_promise = QueryPrebooruData(tweet_id, 'post', post_query_data);
                let illust_query_data = IllustsQuery(tweet_id);
                let illust_promise = QueryPrebooruData(tweet_id, 'illust', illust_query_data);
                let artist_query_data = ArtistsQuery(screen_name);
                let all_idents = [screen_name];
                if (user_id) {
                    all_idents.push(user_id);
                }
                let artist_promise = QueryPrebooruData(tweet_id, 'artist', artist_query_data, all_idents);
            }
        } else {
            let data = resp.item;
            let data_key = 'uploads-' + tweet_id;
            GetData(data_key, 'prebooru').then((upload_ids)=>{
                upload_ids = upload_ids || [];
                upload_ids.push(data.id);
                upload_ids = JSPLib.utility.arrayUnique(upload_ids);
                SaveData(data_key, upload_ids, 'prebooru');
                UpdatePrebooruItems(tweet_id, upload_ids, 'upload');
            });
            let upload_record = {
                id: data.id,
                status: 'pending',
                tweet_id: tweet_id,
                account: screen_name,
                user_id: user_id,
                illusts: [],
                posts: [],
                pool_id: PREBOORU.current_pool?.id || null,
            }
            console.log("Upload record:\n", JSON.stringify(upload_record, null, 2));
            PREBOORU.upload_records.push(upload_record);
            SetUploadRecords();
        }
        setTimeout(()=>{
            HideProgressBar($tweet);
            clearTimeout(backup_cancel);
        }, 1000);
    }).catch(()=>{
        JSPLib.notice.error("Network error: Check the client and server settings.");
    });
}

function IllustsCallback(upload_record) {
    let query_data = IllustsQuery(upload_record.tweet_id);
    QueryPrebooruData(upload_record.tweet_id, 'illust', query_data);
}

function ArtistsCallback(upload_record) {
    let query_data = ArtistsQuery(upload_record.account);
    let all_idents = [upload_record.account, upload_record.user_id].filter((ident) => ident);
    QueryPrebooruData(upload_record.tweet_id, 'artist', query_data, all_idents);
}

function RetrievePrebooruData(tweet_id, item_ids, type, query_data, all_idents=null, open_notice=true) {
    let plural = type + 's';
    if (item_ids.length > 0) {
        GetPrebooruData(plural, item_ids).then((data)=>{
            JSONNotice(data);
        });
    } else {
        QueryPrebooruData(tweet_id, type, query_data, all_idents).then((data)=>{
            if (data.length === 0) {
                JSPLib.notice.notice(`No ${plural} found!`);
            } else if (open_notice) {
                JSONNotice(data);
            }
        });
    }
}

function GetPrebooruData(plural, item_ids) {
    if (item_ids.length === 0) {
        return Promise.resolve([]);
    }
    return $.getJSON(PREBOORU_SERVER_URL + `/${plural}.json`, {search: {id: item_ids.join(',')}});
}

function QueryPrebooruData(tweet_id, type, query_data, all_idents=null) {
    let plural = type + 's';
    return $.getJSON(PREBOORU_SERVER_URL + `/${plural}.json`, {search: query_data}).then((data)=>{
        let item_ids = data.map(item => item.id);
        if (all_idents !== null) {
            all_idents.forEach((ident)=>{
                SaveData(plural + '-' + ident, item_ids, 'prebooru');
            });
        } else {
            SaveData(plural + '-' + tweet_id, item_ids, 'prebooru');
        }
        UpdatePrebooruItems(tweet_id, item_ids, type, all_idents);
        console.log('QueryPrebooruData-1', tweet_id, plural, item_ids, PREBOORU.prebooru_data[tweet_id]);
        SetPrebooruData(tweet_id, plural, item_ids);
        RefreshUploadRecords();
        let upload_record = PREBOORU.upload_records.find((record) => record.tweet_id === tweet_id);
        if (upload_record) {
            upload_record[plural] = item_ids;
            SetUploadRecords();
        }
        return data;
    });
}

function GetTweetInfo($tweet) {
    let tweet_id = String($tweet.data('tweet-id'));
    let user_id = String($tweet.data('user-id') || "");
    let screen_name = String($tweet.data('screen-name'));
    let user_ident = user_id || screen_name;
    let all_idents = JSPLib.utility.arrayUnique([user_ident, screen_name]);
    return [tweet_id, user_id, screen_name, user_ident, all_idents];
}

function GetEventPreload(event,classname) {
    let $link = $(event.target);
    let $tweet = $link.closest('.ntisas-tweet');
    let [tweet_id,user_id,screen_name,user_ident,all_idents] = GetTweetInfo($tweet);
    let $replace = $(`[data-tweet-id=${tweet_id}] .${classname}`).parent();
    return [$link, $tweet, tweet_id, user_id, screen_name, user_ident, all_idents, $replace];
}

//File functions

function ReadFileAsync(fileselector,is_json) {
    const context = this;
    return new Promise((resolve,reject)=>{
        let files = $(fileselector).prop('files');
        if (!files.length) {
            alert('Please select a file!');
            reject();
            return;
        }
        var file = files[0];
        var reader = new FileReader();
        reader.onloadend = function(event) {
            if (event.target.readyState == FileReader.DONE) {
                context.debug('log', "File loaded:", file.size);
                let data = event.target.result;
                if (is_json) {
                    try {
                        data = JSON.parse(data);
                    } catch (e) {
                        JSPLib.notice.error("Error: File is not JSON!");
                        reject();
                    }
                }
                resolve(data);
            }
        };
        var blob = file.slice(0, file.size);
        reader.readAsBinaryString(blob);
    });
}

function DownloadObject(export_obj, export_name, is_json) {
    var export_data = export_obj;
    var encoding = {type: 'text/plain;charset=utf-8'};
    if (is_json) {
        export_data = JSON.stringify(export_obj);
        encoding = {type: 'text/json;charset=utf-8'};
    }
    var blob = new Blob([export_data], encoding);
    saveAs(blob, export_name);
}

//Render functions

function RenderPoolSelection(pool_data) {
    let html = `<li style="height: 1.5em;" data-id="0"><b>XX. <a style="color: red;" href="${PREBOORU_SERVER_URL}/posts"class="ntisas-expaned-link ntisas-pool-selection">NONE</a></b></li>`;
    pool_data.forEach((pool,i)=>{
        let index_str = JSPLib.utility.padNumber(i + 1, 2);
        html += `<li class="ntisas-pool" style="height: 1.5em;" data-id="${pool.id}"><b>${index_str}. <a style="color: dodgerblue;" class="ntisas-expaned-link ntisas-pool-selection" href="${PREBOORU_SERVER_URL}/pools/${pool.id}">${pool.name}</a>: <a style="color: orange;" class="ntisas-expaned-link" href="${PREBOORU_SERVER_URL}/pools/${pool.id}/last">&raquo;</a></b> <span class="ntisas-pool-count">${pool.element_count}</span></li>`;
    });
    return `<ul style="margin-left: 1em;" class="ntisas-links">${html}</ul>`;
}

function RenderAllSimilarPrebooru(all_similar_results) {
    var image_results = [];
    var max_results = 0;
    all_similar_results.forEach((similar_result,i)=>{
        max_results = Math.max(max_results, similar_result.post_results.length, 5);
        let html = RenderPrebooruSimilarContainer("Image " + (i + 1), similar_result, i);
        image_results.push(html);
    });
    let render_width = Math.min(((max_results + 1) * BASE_PREVIEW_WIDTH) + BASE_QTIP_WIDTH + 20, 850);
    return `
<div class="ntisas-similar-results ntisas-qtip-container" data-type="prebooru" style="width:${render_width}px; max-height: 75vh;">
    ${image_results.join(HORIZONTAL_RULE)}
</div>`;
}

function RenderPrebooruSimilarContainer(header,similar_result,index) {
    var html = RenderTwimgPreview(similar_result.image_url, index);
    html += `<div class="ntisas-vr"></div>`;
    if (similar_result.post_results.length) {
        let sorted_results = similar_result.post_results.sort((a, b) => (b.score - a.score)).slice(0, PREBOORU.results_returned);
        sorted_results.forEach((post_result)=>{
            let site_ids = JSPLib.utility.arrayUnique(post_result.post.illust_urls.map((illust_url) => illust_url.site_id));
            let addons = RenderPreviewAddons(site_ids.join(' ,'), null, post_result.score, post_result.post.file_ext, post_result.post.size, post_result.post.width, post_result.post.height, false);
            html += RenderPostPreview(post_result.post, PREBOORU_SERVER_URL, addons, false);
        });
    } else {
        html += '<div style="font-style: italic; display: inline-block; height: 200px; width: 160px; position: relative;"><span style="position: absolute; top: 2em; left: 2em;">Nothing found.</span></div>';
    }
    return `
<div class="ntisas-similar-result">
    <h4>${header} (${RenderHelp(IQDB_SELECT_HELP)})</h4>
    ${html}
</div>`;
}

function RenderPrebooruContainer(posts) {
    let html = "";
    posts.forEach((post)=>{
        let addons = RenderPreviewAddons('https://twitter.com', post.id, null, post.file_ext, post.size, post.width, post.height);
        html += RenderPostPreview(post, PREBOORU_SERVER_URL, addons, false);
    });
    let width_addon = (posts.length > 10 ? 'style="width:850px"' : "");
    return `
<div class="prebooru-prebooru-thumbs-container" ${width_addon}>
    ${html}
</div>`;
}

//Expects a mapped post as input
function RenderPostPreview(post,server_url,append_html="",populate_title=true) {
    let [width,height] = JSPLib.utility.getPreviewDimensions(post.width, post.height, POST_PREVIEW_DIMENSION);
    let padding_height = POST_PREVIEW_DIMENSION - height;
    let title = (populate_title ? GetLinkTitle(post) : "");
    return `
<article class="prebooru-post-preview prebooru-post-selectable" data-id="${post.id}" data-size="${post.size}">
    <div class="prebooru-image-container">
        <a target="_blank" href="${server_url}/posts/${post.id}">
            <img width="${width}" height="${height}" style="padding-top:${padding_height}px" title="${title}">
        </a>
    </div>
    ${append_html}
</article>`;
}

function RenderTwimgPreview(image_url,index,selectable) {
    let file_type = GetFileExtension(image_url, ':');
    let thumb_url = GetThumbUrl(image_url, ':', 'jpg', '360x360');
    let image_html = `<img width="${POST_PREVIEW_DIMENSION}" height="${POST_PREVIEW_DIMENSION}" src="${thumb_url}">`;
    let selected_class = "";
    if (selectable) {
        image_html = `<a>${image_html}</a>`;
        selected_class = 'prebooru-post-select prebooru-post-selectable';
    }
    let append_html = RenderPreviewAddons('https://twitter.com', null, null, file_type);
    return `
<article class="prebooru-post-preview prebooru-tweet-preview ${selected_class}" data-id="${index}">
    <div class="prebooru-image-container">
        ${image_html}
    </div>
    ${append_html}
</article>`;
}

function RenderPreviewAddons(source,id,score,file_ext,file_size,width,height,is_user_upload=false) {
    let title_text = "Original image";
    if (JSPLib.validate.validateID(id)) {
        title_text = "post #" + id;
    } else if (JSPLib.validate.isNumber(score)) {
        title_text = `Similarity: ${JSPLib.utility.setPrecision(score, 2)}`;
    }
    let uploader_addon = (is_user_upload ? 'class="prebooru-post-upload"' : "");
    let domain = (source.match(/^https?:\/\//) ? JSPLib.utility.getDomainName(source, 2) : "NON-WEB");
    let size_text = (Number.isInteger(file_size) && Number.isInteger(width) && Number.isInteger(height) ? `${ReadableBytes(file_size)} (${width}x${height})` : "");
    return `
<p class="prebooru-desc prebooru-desc-title"><span ${uploader_addon}>${title_text}</span></p>
<p class="prebooru-desc prebooru-desc-info">${file_ext.toUpperCase()} @ <span title="${domain}">${domain}</span></p>
<p class="prebooru-desc prebooru-desc-size">${size_text}</p>`;
}

function RenderHelp(help_text) {
    return `<a class="ntisas-help-info ntisas-expanded-link" title="${help_text}">&nbsp;?&nbsp;</a>`;
}

//Initialize functions

function InitializeUIStyle() {
    if (!JSPLib.utility.hasStyle('jquery')) {
        const jquery_ui_css = GM_getResourceText('jquery_ui_css');
        JSPLib.utility.setCSSStyle(jquery_ui_css, 'jquery');
    }
}

function InitializeStatusBar(tweet_status,is_main_tweet) {
    var $container;
    var direction = 'append';
    if (tweet_status.childElementCount > 0) {
        if (tweet_status.children[0] && tweet_status.children[0].children[0] && tweet_status.children[0].children[0].children[0]) {
            $container = $('> div > div > div > div:last-of-type', tweet_status);
            $("> div:last-of-type", $container[0]).css('flex-grow', 'unset').css('flex-basis', 'unset');
            $("[role=link] > span > span", $container[0]).addClass('ntisas-retweet-marker');
        } else if (!is_main_tweet) {
            direction = 'prepend';
        }
    }
    if (!$container) {
        $container = $(tweet_status);
    }
    $container[direction](STATUS_MARKER);
}

function InitializePoolSelection(pool_data) {
    let $dialog = $(RenderPoolSelection(pool_data));
    const dialog_settings = Object.assign({}, PREBOORU_DIALOG_SETTINGS, {
        width: 500,
        height: 800,
    });
    $dialog.find('.ntisas-pool-selection').on(PROGRAM_CLICK,(event)=>{
        let pool_id = $(event.currentTarget).closest('li').data('id');
        let pool = pool_data.find((pool) => (pool.id === pool_id)) || null;
        if (pool) {
            if ((PREBOORU.current_pool === null) || (PREBOORU.current_pool.id !== pool.id)) {
                PREBOORU.prior_pool = PREBOORU.current_pool;
                if (PREBOORU.prior_pool) {
                    JSPLib.storage.saveData('ntisas-prior-pool', PREBOORU.prior_pool, STORAGE_DATABASES.prebooru);
                } else {
                    JSPLib.storage.removeData('ntisas-prior-pool', true, STORAGE_DATABASES.prebooru);
                }
            }
            PREBOORU.current_pool = pool;
            JSPLib.storage.saveData('prebooru-prebooru-pool', PREBOORU.current_pool, STORAGE_DATABASES.prebooru);
        } else {
            if (PREBOORU.current_pool !== null) {
                PREBOORU.prior_pool = PREBOORU.current_pool;
                JSPLib.storage.saveData('ntisas-prior-pool', PREBOORU.prior_pool, STORAGE_DATABASES.prebooru);
            }
            PREBOORU.current_pool = null;
            JSPLib.storage.removeData('prebooru-prebooru-pool', true, STORAGE_DATABASES.prebooru);
        }
        UpdatePoolDisplay();
        PREBOORU.channel.postMessage({type: 'pool'});
        event.preventDefault();
    });
    InitializeUIStyle();
    $dialog.dialog(dialog_settings);
    return $dialog;
}

function RenderMiscActionsDialog(tweet_id) {
    return `
<div class="prebooru-misc-actions-container ntisas-links" data-tweet-id="${tweet_id}">
    <ul style="font-weight: bold; margin: 0; padding: 0.5em;">
        <li><a class="prebooru-query-data ntisas-expanded-link">Query All Data</a></li>
        <li><a class="prebooru-add-tweet-notation ntisas-expanded-link">Add tweet notation</a></li>
        <li><a class="prebooru-add-tweet-tag ntisas-expanded-link">Add tweet tag</a></li>
    </ul>
</div>
`;
}

function RenderItemActionsDialog(tweet_id, item_type) {
    return `
<div class="prebooru-item-actions-container ntisas-links" data-tweet-id="${tweet_id}" data-action="">
    <ul style="font-weight: bold; margin: 0; padding: 0.5em;">
        <li><a class="ntisas-set-link-data ntisas-expanded-link" data-action="query">Query Data</a></li>
        <li><a class="ntisas-set-link-data ntisas-expanded-link" data-action="create">Create ${item_type}</a></li>
    </ul>
</div>`;
}

function InitializeMiscActions(tweet_id) {
    let $dialog = $(RenderMiscActionsDialog(tweet_id));
    const dialog_settings = Object.assign({}, PREBOORU_DIALOG_SETTINGS, {
        width: 200
    });
    InitializeUIStyle();
    $dialog.dialog(dialog_settings);
    return $dialog;
}

function InitializeItemActions(tweet_id, item_type) {
    let $dialog = $(RenderItemActionsDialog(tweet_id, item_type));
    $dialog.find('.ntisas-set-link-data').on(PROGRAM_CLICK, (event)=>{
        let selected_action = $(event.currentTarget).data('action');
        $dialog.data('action', selected_action);
        $dialog.prop('promiseData', selected_action);
        $dialog.dialog('close');
    });
    const dialog_settings = Object.assign({}, PREBOORU_DIALOG_SETTINGS, {
        width: 200,
    });
    InitializeUIStyle();
    $dialog.dialog(dialog_settings);
    return $dialog;
}

function RenderPoolActionsDialog(tweet_id) {
    return `
<div class="prebooru-pool-actions-container ntisas-links" data-tweet-id="${tweet_id}">
    <ul style="font-weight: bold; margin: 0; padding: 0.5em;">
        <li><a class="prebooru-add-pool-tweet ntisas-expanded-link" style="color: cornflowerblue;">Add pool</a></li>
        <li><a class="prebooru-query-tweet-pools ntisas-expanded-link" style="color: cornflowerblue;">Query pool</a></li>
    </ul>
</div>
`;
}

function InitializePoolActions(tweet_id) {
    let $dialog = $(RenderPoolActionsDialog(tweet_id));
    const dialog_settings = Object.assign({}, PREBOORU_DIALOG_SETTINGS, {
        width: 200
    });
    InitializeUIStyle();
    $dialog.dialog(dialog_settings);
    return $dialog;
}

function InitializePrebooruContainer(prebooru_posts) {
    let $dialog = $(RenderPrebooruContainer(prebooru_posts));
    prebooru_posts.forEach((post)=>{post.thumbnail = post.preview_url;});
    SetThumbnailWait($dialog[0], prebooru_posts);
    const dialog_settings = Object.assign({}, PREBOORU_DIALOG_SETTINGS, {
        width: BASE_DIALOG_WIDTH + BASE_PREVIEW_WIDTH * prebooru_posts.length
    });
    InitializeUIStyle();
    $dialog.dialog(dialog_settings);
    return $dialog;
}

function InitializePrebooruSimilarContainer(similar_results) {
    let $dialog = $(RenderAllSimilarPrebooru(similar_results));
    let posts = [];
    let image_urls = [];
    let max_image_results = 1;
    similar_results.forEach((similar_result)=>{
        similar_result.post_results.forEach((post_result)=>{
            posts.push(post_result.post);
        });
        image_urls.push(similar_result.image_url);
        max_image_results = Math.min(Math.max(max_image_results, similar_result.post_results.length), 5);
    })
    let unique_posts = RemoveDuplicates(posts, 'id');
    unique_posts.forEach((post)=>{post.thumbnail = post.preview_url;});
    console.log({unique_posts});
    SetThumbnailWait($dialog[0], unique_posts);
    $('article.prebooru-tweet-preview', $dialog[0]).each((i,article)=>{
        InitializeTwitterImage(article, image_urls).then(({size})=>{
            $(article).closest('.ntisas-similar-result').find(`[data-size=${size}]`).addClass('prebooru-post-match');
        });
    });
    const dialog_settings = Object.assign({}, PREBOORU_DIALOG_SETTINGS, {
        width: BASE_DIALOG_WIDTH + BASE_PREVIEW_WIDTH * max_image_results + 180,
        maxHeight: 800,
    });
    InitializeUIStyle();
    $dialog.dialog(dialog_settings);
    return $dialog;
}

function GetImageAttributes(image_url) {
    const self = this;
    let base_url = image_url.split(':orig')[0];
    PREBOORU.image_data = PREBOORU.image_data || {};
    return new Promise((resolve)=>{
        if (image_url in PREBOORU.image_data) {
            resolve(PREBOORU.image_data[image_url]);
        }
        let size_promise = JSPLib.network.getDataSize(image_url);
        let dimensions_promise;
        if (base_url in PREBOORU.tweet_images) {
            self.debug('log', "Found image API data:", base_url, PREBOORU.tweet_images[base_url]);
            dimensions_promise = Promise.resolve(PREBOORU.tweet_images[base_url].original_info);
        } else {
            self.debug('warn', "Missing image API data:", base_url);
            dimensions_promise = JSPLib.utility.getImageDimensions(image_url);
            console.warn('blah');
        }
        Promise.allSettled([size_promise, dimensions_promise]).then(([size_result, dimensions_result])=>{
            let size = (size_result.status === 'fulfilled' ? size_result.value : null);
            if (size_result.status === 'rejected') {
                self.debug('error', `Error getting image size - HTTP ${size_result.reason.status}:`, image_url);
            }
            let dimensions = (dimensions_result.status === 'fulfilled' ? dimensions_result.value : {width: null, height: null})
            if (dimensions_result.status === 'rejected') {
                self.debug('error', 'Error getting image dimensions:', image_url);
            }
            PREBOORU.image_data[image_url] = Object.assign(dimensions, {size: size});
            resolve(PREBOORU.image_data[image_url]);
        });
    });
}

function InitializeTwitterImage(article,image_urls) {
    let index = Number($(article).data('id'));
    let image_url = image_urls[index] + ':orig';
    let image = $('img', article)[0];
    console.warn({article, image_url, image_urls, index});
    let image_promise = GetImageAttributes(image_url);
    image_promise.then(({size,width,height})=>{
            let [use_width, use_height] = (width && height ? [width, height] : [image.naturalWidth, image.naturalHeight]);
            let [preview_width,preview_height] = JSPLib.utility.getPreviewDimensions(use_width, use_height, POST_PREVIEW_DIMENSION);
            image.width = preview_width;
            image.height = preview_height;
        image.style.paddingTop = `${POST_PREVIEW_DIMENSION - preview_height}px`;
        let size_text = (Number.isInteger(size) && size > 0 ? ReadableBytes(size) : 'Unavailable');
        $('p:nth-child(4)', article).html(`${size_text} (${width}x${height})`);
    });
    return image_promise;
}

function RenderPrebooruMenu(posts,uploads,illusts,artists) {
    const types = ['upload', 'post', 'illust', 'artist'];
    let itemdict = {uploads, posts, illusts, artists};
    let info_html = types.map((type)=>{
        let plural = type + 's';
        let items = itemdict[plural] || [];
        let label = (items.length === 1 ? type : plural);
        let num = (items.length === 0 ? "no" : String(items.length));
        let style = (items.length === 0 ? 'color: grey;' : 'color: green;');
        let href = "#";
        if (items.length) {
            href = PREBOORU_SERVER_URL + '/' + plural;
            if (items.length === 1) {
                href += '/' + items[0];
            } else {
                href += '?search[id]=' + items.join(',');
            }
        }
        return `<a style="${style}" class="prebooru-prebooru-${plural} ntisas-expanded-link" href="${href}">${num} ${label}</a>`;
    }).join(' | ');
    let control_helplink = RenderHelp(PREBOORU_MENU_HELP);
    let info_helplink = RenderHelp(PREBOORU_INFO_HELP);
    return JSPLib.utility.regexReplace(PREBOORU_LINK_MENU, {
        CONTROL_HELPLINK: control_helplink,
        INFO_HTML: info_html,
        INFO_HELPLINK: info_helplink,
    });
}

function InitializePrebooruMenu(tweet) {
    let [tweet_id, user_id, screen_name, user_ident, all_idents] = GetTweetInfo($(tweet));
    console.log('InitializePrebooruMenu-0', {tweet_id, user_id, screen_name, user_ident, all_idents});
    if (tweet_id === undefined) {
        return;
    }
    let $prebooru_menu = $(PREBOORU_MENU);
    let $prebooru_section = $prebooru_menu.find('.prebooru-link-section');
    let $prebooru_stub = $('<span class="prebooru-prebooru-stub">Loading...</span>');
    $prebooru_section.append($prebooru_stub);
    let promise_array = [];
    promise_array.push(GetData('uploads-' + tweet_id, 'prebooru'));
    promise_array.push(GetData('posts-' + tweet_id, 'prebooru'));
    promise_array.push(GetData('illusts-' + tweet_id, 'prebooru'));
    promise_array.push(GetData('artists-' + user_ident, 'prebooru'));
    Promise.all(promise_array).then(([uploads,posts,illusts,artists])=>{
        console.log('InitializePrebooruMenu-2', uploads, posts, illusts, artists);
        const types = ['upload', 'post', 'illust', 'artist'];
        let itemdict = {uploads, posts, illusts, artists};
        let $prebooru_entry = $('.prebooru-menu', tweet);
        types.forEach((type)=>{
            let plural = type + 's';
            let items = itemdict[plural] || [];
            let id_string = items.join(',');
            $prebooru_entry.attr(`data-${type}-ids`, id_string);
        });
        let $prebooru_links = $(RenderPrebooruMenu(posts,uploads,illusts,artists));
        let temp_hash = {uploads, posts, illusts, artists};
        if (tweet_id in PREBOORU.prebooru_data) {
            for (let key in temp_hash) {
                PREBOORU.prebooru_data[tweet_id][key] = PREBOORU.prebooru_data[tweet_id][key] || temp_hash[key];
            }
        } else {
            PREBOORU.prebooru_data[tweet_id] = temp_hash;
        }
        $prebooru_stub.replaceWith($prebooru_links);
        let artist_ids = artists || [];
        let missing_artist_ids = JSPLib.utility.arrayDifference(artist_ids, Object.keys(PREBOORU.artists));
        GetPrebooruData('artists', missing_artist_ids).then((data) => {
            data.forEach((artist) => {
                PREBOORU.artists[artist.id] = artist;
            });
            artist_ids.forEach((id) => {
                let artist = PREBOORU.artists[id];
                if (!artist.primary) {
                    $prebooru_links.find('.prebooru-prebooru-artists').css('color', 'darkviolet');
                }
            });
        });
    });
    console.log('InitializePrebooruMenu-1', $prebooru_menu, $prebooru_section, $prebooru_stub, $('.ntisas-tweet-image-menu', tweet));
    $('.ntisas-tweet-image-menu', tweet).after($prebooru_menu);
}

//Queue functions

function QueueStorageRequest(type,key,value,database) {
    let queue_key = type + '-' + key + '-' + database;
    if (!CACHE_STORAGE_TYPES.includes(type) || !(queue_key in CACHED_STORAGE_REQUESTS)) {
        const request = {
            type,
            key,
            value,
            database,
            promise: $.Deferred(),
            error: (JSPLib.debug.debug_console ? new Error() : null),
        };
        if (CACHE_STORAGE_TYPES.includes(type)) {
            JSPLib.debug.recordTime(key, 'Storage-queue');
        }
        QUEUED_STORAGE_REQUESTS.push(request);
        CACHED_STORAGE_REQUESTS[queue_key] = request.promise;
        JSPLib.debug.debugExecute(()=>{
            SAVED_STORAGE_REQUESTS.push(request);
        });
    }
    return CACHED_STORAGE_REQUESTS[queue_key];
}

function InvalidateCache(key,database) {
    CACHE_STORAGE_TYPES.forEach((type)=>{
        let queue_key = type + '-' + key + '-' + database;
        delete CACHED_STORAGE_REQUESTS[queue_key];
    });
}

function FulfillStorageRequests(keylist,data_items,requests) {
    keylist.forEach((key)=>{
        let data = (key in data_items ? data_items[key] : null);
        let request = requests.find((request) => (request.key === key));
        request.promise.resolve(data);
        request.data = data;
        JSPLib.debug.recordTimeEnd(key, 'Storage-queue');
    });
}

function IntervalStorageHandler() {
    if (QUEUED_STORAGE_REQUESTS.length === 0) {
        return;
    }
    this.debug('logLevel', ()=>["Queued requests:",JSPLib.utility.dataCopy(QUEUED_STORAGE_REQUESTS)], JSPLib.debug.VERBOSE);
    for (let database in STORAGE_DATABASES) {
        let requests = QUEUED_STORAGE_REQUESTS.filter((request) => (request.database === database));
        let save_requests = requests.filter((request) => (request.type === 'save'));
        if (save_requests.length) {
             this.debug('logLevel', "Save requests:", save_requests, JSPLib.debug.DEBUG);
            let save_data = Object.assign(...save_requests.map((request) => ({[request.key]: request.value})));
            JSPLib.storage.batchSaveData(save_data, STORAGE_DATABASES[database]).then(()=>{
                save_requests.forEach((request)=>{
                    request.promise.resolve(null);
                    request.endtime = performance.now();
                });
            });
        }
        let remove_requests = requests.filter((request) => (request.type === 'remove'));
        if (remove_requests.length) {
            this.debug('logLevel', "Remove requests:", remove_requests, JSPLib.debug.DEBUG);
            let remove_keys = remove_requests.map((request) => request.key);
            JSPLib.storage.batchRemoveData(remove_keys, STORAGE_DATABASES[database]).then(()=>{
                remove_requests.forEach((request)=>{
                    request.promise.resolve(null);
                    request.endtime = performance.now();
                });
            });
        }
        let check_requests = requests.filter((request) => (request.type === 'check'));
        if (check_requests.length) {
            this.debug('logLevel', "Check requests:", check_requests, JSPLib.debug.DEBUG);
            let check_keys = check_requests.map((request) => request.key);
            JSPLib.storage.batchCheckLocalDB(check_keys, () => true, () => true, STORAGE_DATABASES[database]).then((check_data)=>{
                FulfillStorageRequests(check_keys,check_data,check_requests);
            });
        }
        let noncheck_requests = requests.filter((request) => (request.type === 'get'));
        if (noncheck_requests.length) {
            this.debug('logLevel', "Noncheck requests:", noncheck_requests, JSPLib.debug.DEBUG);
            let noncheck_keys = noncheck_requests.map((request) => request.key);
            JSPLib.storage.batchRetrieveData(noncheck_keys, STORAGE_DATABASES[database]).then((noncheck_data)=>{
                FulfillStorageRequests(noncheck_keys,noncheck_data,noncheck_requests);
            });
        }
    }
    QUEUED_STORAGE_REQUESTS.length = 0;
}

//Database functions

function GetData(key, database) {
    let type = (database === 'danbooru' ? 'check' : 'get');
    return QueueStorageRequest(type, key, null, database);
}

function SaveData(key, value, database, invalidate = true) {
    if (invalidate) {
        InvalidateCache(key, database);
    }
    return QueueStorageRequest('save', key, value, database);
}

function RemoveData(key, database) {
    InvalidateCache(key, database);
    return QueueStorageRequest('remove', key, null, database);
}

//Event handlers

function TogglePrebooruMenu() {
    let controls = GetLocalData('prebooru-menu', true);
    SetLocalData('prebooru-menu', !controls);
    UpdateLinkControls();
    UpdatePrebooruMenu();
    PREBOORU.channel.postMessage({type: 'prebooru_ui'});
}

function ChooseCurrentPool(event) {
    if (!PREBOORU.pool_selection_dialog) {
        $.getJSON(PREBOORU_SERVER_URL + '/pools.json', {limit: 50, search: {order: 'updated'}}).then((data)=>{
            PREBOORU.pool_selection_dialog = InitializePoolSelection(data);
            PREBOORU.pool_selection_dialog.dialog('open');
        });
    } else {
        PREBOORU.pool_selection_dialog.dialog('open');
    }
    event.preventDefault();
}

function ChoosePriorPool(event) {
    let temp = PREBOORU.current_pool;
    PREBOORU.current_pool = PREBOORU.prior_pool;
    PREBOORU.prior_pool = temp;
    if (PREBOORU.current_pool) {
        JSPLib.storage.saveData('prebooru-prebooru-pool', PREBOORU.current_pool, STORAGE_DATABASES.prebooru);
    } else {
        JSPLib.storage.removeData('prebooru-prebooru-pool', true, STORAGE_DATABASES.prebooru);
    }
    if (PREBOORU.prior_pool) {
        JSPLib.storage.saveData('ntisas-prior-pool', PREBOORU.prior_pool, STORAGE_DATABASES.prebooru);
    } else {
        JSPLib.storage.removeData('ntisas-prior-pool', true, STORAGE_DATABASES.prebooru);
    }
    UpdatePoolDisplay();
    event.preventDefault();
}

async function TogglePrebooruForceUpload(event) {
    $(event.currentTarget).toggleClass('ntisas-activated');
}

function PrebooruAllUpload(event) {
    let [$link,$tweet,tweet_id,user_id,screen_name,,all_idents,] = GetEventPreload(event, 'prebooru-all-prebooru-upload');
    let request_url = `https://twitter.com/${screen_name}/status/${tweet_id}`;
    let force_download = $tweet.find('.prebooru-force-prebooru-upload').hasClass('ntisas-activated');
    let post_data = {
        upload: {
            request_url: request_url,
        },
        force: force_download,
    };
    ProcessPrebooruUpload(post_data, tweet_id, $tweet, 'All', screen_name, user_id);
}

function RenderConfirmContainer(image_urls) {
    let html = "";
    image_urls.forEach((image,i)=>{
        html += RenderTwimgPreview(image, i, true);
    });
    let controls = (image_urls.length > 1 ? `<div style="position: relative; display: block; width: 10em;">${SELECTION_CONTROLS}</div>` : "");
    return `
<div class="prebooru-confirm-image prebooru-selectable-results">
    <div style="font-size:12px">Selected images will be used for the query. Press <b>Submit</b> to execute query, or <b>Cancel</b> to go back.</div>
    ${html}
    ${controls}
</div>`;
}

function InitializeConfirmContainer(image_urls) {
    let $dialog = $(RenderConfirmContainer(image_urls));
    const dialog_settings = Object.assign({}, CONFIRM_DIALOG_SETTINGS, {
        width: BASE_DIALOG_WIDTH + BASE_PREVIEW_WIDTH * image_urls.length
    });
    $('article', $dialog[0]).each((i,article)=>{
        InitializeTwitterImage(article, image_urls);
    });
    InitializeUIStyle();
    $dialog.dialog(dialog_settings);
    return $dialog;
}

function GetSelectPostIDs(tweet_id,type) {
    if (!PREBOORU[type][tweet_id]) {
        return [];
    }
    let $select_previews = $('.prebooru-post-select', PREBOORU[type][tweet_id][0]);
    return JSPLib.utility.getDOMAttributes($select_previews, 'id', Number);
}

function SelectPreview(event) {
    $(event.currentTarget).closest('.prebooru-post-preview').toggleClass('prebooru-post-select');
    event.preventDefault();
}

function SelectControls(event) {
    let $container = $(event.target).closest('.prebooru-selectable-results');
    let type = $(event.target).data('type');
    let $post_previews = $container.find('.prebooru-post-preview.prebooru-post-selectable');
    switch (type) {
        case 'all':
            $post_previews.addClass('prebooru-post-select');
            break;
        case 'none':
            $post_previews.removeClass('prebooru-post-select');
            break;
        case 'invert':
            $post_previews.toggleClass('prebooru-post-select');
            // falls through
        default:
            // do nothing
    }
}

async function PickImage(event,type,pick_func,load_msg=true,setting=true,always=false) {
    let similar_class = 'ntisas-check-' + type;
    let [$link,$tweet,tweet_id,,,,all_idents,$replace] = GetEventPreload(event, similar_class);
    let all_image_urls = GetImageLinks($tweet[0]);
    if (all_image_urls.length === 0) {
        this.debug('log', "Images not loaded yet...");
        return false;
    }
    this.debug('log', "All:", all_image_urls);
    if (always || ((all_image_urls.length > 1) && (!setting) && (typeof pick_func !== 'function' || pick_func()))) {
        if (!PREBOORU.tweet_dialog[tweet_id]) {
            PREBOORU.tweet_dialog[tweet_id] = InitializeConfirmContainer(all_image_urls);
            PREBOORU.dialog_anchor[tweet_id] = $link;
        }
        PREBOORU.tweet_dialog[tweet_id].dialog('open');
        let status = await PREBOORU.tweet_dialog[tweet_id].prop('promiseConfirm');
        if (!status) {
            this.debug('log', "Exiting...");
            return false;
        }
        let selected_indexes = GetSelectPostIDs(tweet_id, 'tweet_dialog');
        var selected_image_urls = all_image_urls.filter((image,index) => selected_indexes.includes(index));
    } else {
        selected_image_urls = all_image_urls;
    }
    this.debug('log', "Selected:", selected_image_urls);
    if (load_msg) {
        $link.removeClass(similar_class).html("loading…");
    }
    return [$link,$tweet,tweet_id,$replace,selected_image_urls,all_idents];
}

async function PrebooruSelectUpload(event) {
    let pick = await PickImage(event, 'prebooru', null, false, false, true);
    if (!pick) {
        return;
    }
    let [$link,$tweet,tweet_id,$replace,selected_image_urls,all_idents] = pick;
    let screen_name = $tweet.data('screen-name');
    let user_id = $tweet.data('user-id');
    let request_url = `https://twitter.com/${screen_name}/status/${tweet_id}`;
    let force_download = $tweet.find('.prebooru-force-prebooru-upload').hasClass('ntisas-activated');
    let post_data = {
        upload: {
            request_url: request_url,
            image_urls: selected_image_urls,
        },
        force: force_download,
    };
    ProcessPrebooruUpload(post_data, tweet_id, $tweet, 'Select', screen_name, user_id);
}

function PrebooruThumbs(event) {
    let [$link,$tweet,tweet_id,,,,,] = GetEventPreload(event, 'prebooru-prebooru-thumbs');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    if (post_ids.length > 0) {
        $.getJSON(PREBOORU_SERVER_URL + '/posts.json', {search: {id: post_ids.join(',')}}).then((data)=>{
            if (!PREBOORU.prebooru_dialog[tweet_id]) {
                PREBOORU.prebooru_dialog[tweet_id] = InitializePrebooruContainer(data);
                PREBOORU.prebooru_anchor[tweet_id] = $link;
            }
            PREBOORU.prebooru_dialog[tweet_id].dialog('open');
        });
    }
}

async function PrebooruSimilar(event) {
    let [$link, $tweet, tweet_id, user_id, screen_name, user_ident, all_idents, $replace] = GetEventPreload(event, 'prebooru-prebooru-similar');
    if (!PREBOORU.prebooru_similar_dialog[tweet_id]) {
        let pick = await PickImage(event, 'similar', null, false, false);
        if (!pick) {
            return;
        }
        let [$link,$tweet,tweet_id,$replace,selected_image_urls,all_idents] = pick;
        $link.addClass('ntisas-active');
        try {
            var data = await $.getJSON(PREBOORU_SERVER_URL + '/image_hashes/check.json', {urls: selected_image_urls});
        } catch (e) {
            JSPLib.notice.error("Error contacting Prebooru.");
            return;
        }
        $link.removeClass('ntisas-active');
        if (data.error === false) {
            PREBOORU.prebooru_similar_dialog[tweet_id] = InitializePrebooruSimilarContainer(data.similar_results);
            PREBOORU.prebooru_similar_anchor[tweet_id] = $link;
        } else {
            JSONNotice(data);
        }
    }
    PREBOORU.prebooru_similar_dialog[tweet_id].dialog('open');
}

function PrebooruUploads(event) {
    let [,$tweet,tweet_id,,screen_name,,,$replace] = GetEventPreload(event, 'prebooru-prebooru-info');
    let $info = $tweet.find('.prebooru-menu');
    let upload_ids = GetDomDataIds($info, 'upload-ids');
    let query_data = UploadsQuery(screen_name, tweet_id);
    RetrievePrebooruData(tweet_id, upload_ids, 'upload', query_data);
    event.preventDefault();
}

function PrebooruPosts(event) {
    let [,$tweet,tweet_id,,,,,$replace] = GetEventPreload(event, 'prebooru-prebooru-info');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    let query_data = PostsQuery(tweet_id);
    RetrievePrebooruData(tweet_id, post_ids, 'post', query_data);
    event.preventDefault();
}

async function PrebooruIllusts(event) {
    let [$link, $tweet, tweet_id, user_id, screen_name, user_ident, all_idents, $replace] = GetEventPreload(event, 'prebooru-prebooru-info');
    event.preventDefault();
    PREBOORU.prebooru_action_dialog ||= {};
    PREBOORU.prebooru_action_anchor ||= {};
    PREBOORU.prebooru_action_dialog[tweet_id] ||= {};
    PREBOORU.prebooru_action_anchor[tweet_id] ||= {};
    if (!PREBOORU.prebooru_action_dialog[tweet_id].illust) {
        PREBOORU.prebooru_action_dialog[tweet_id].illust = InitializeItemActions(tweet_id, 'illust');
        PREBOORU.prebooru_action_anchor[tweet_id].illust = $link;
    }
    PREBOORU.prebooru_action_dialog[tweet_id].illust.dialog('open');
    let action = await PREBOORU.prebooru_action_dialog[tweet_id].illust.prop('promiseConfirm');
    let action_type = PREBOORU.prebooru_action_dialog[tweet_id].illust.data('action');
    console.log('PrebooruIllusts', {action, action_type});
    if (action === 'query') {
        let $info = $tweet.find('.prebooru-menu');
        let illust_ids = GetDomDataIds($info, 'illust-ids');
        let query_data = IllustsQuery(tweet_id);
        RetrievePrebooruData(tweet_id, illust_ids, 'illust', query_data);
    } else {
        PrebooruCreateIllust([$tweet,tweet_id,user_id,screen_name,user_ident,all_idents]);
    }
}

function PrebooruArtists(event) {
    let [,$tweet,tweet_id,,screen_name,,all_idents,$replace] = GetEventPreload(event, 'prebooru-prebooru-info');
    let $info = $tweet.find('.prebooru-menu');
    let artist_ids = GetDomDataIds($info, 'artist-ids');
    let query_data = ArtistsQuery(screen_name);
    RetrievePrebooruData(tweet_id, artist_ids, 'artist', query_data, all_idents);
    event.preventDefault();
}

function GetPrebooruDialogPreload(event, container_class) {
    let $container = $(event.currentTarget).closest(container_class);
    let tweet_id = $container.data('tweet-id');
    let $tweet = $(`.ntisas-tweet[data-tweet-id="${tweet_id}"]`);
    return JSPLib.utility.concat([$tweet], GetTweetInfo($tweet));
}

function PrebooruQueryData(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-misc-actions-container');
    let upload_query_data = UploadsQuery(screen_name, tweet_id);
    let upload_promise = QueryPrebooruData(tweet_id, 'upload', upload_query_data);
    let post_query_data = PostsQuery(tweet_id);
    let post_promise = QueryPrebooruData(tweet_id, 'post', post_query_data);
    let illust_query_data = IllustsQuery(tweet_id);
    let illust_promise = QueryPrebooruData(tweet_id, 'illust', illust_query_data);
    let artist_query_data = ArtistsQuery(screen_name);
    let artist_promise = QueryPrebooruData(tweet_id, 'artist', artist_query_data, all_idents);
    Promise.all([upload_promise, post_promise, illust_promise, artist_promise]).then((query_data)=>{
        JSPLib.notice.notice("Prebooru data updated.");
    });
    event.preventDefault();
}

var IMAGE2_RG = XRegExp.tag('xi')`
^https?://pbs\.twimg\.com               # Hostname
/(media|tweet_video_thumb)
/([\w-]+)                               # Image key
\?format=(jpg|png|gif)                  # Extension
(?:&name=(\w+))?$                       # Size
`;

var SITE_IDS = {
    'pbs.twimg.com': 4,
    'video.twimg.com': 5
};

function FixupCRLF(text) {
    return text.replace(/(?<!\r)\n/g, '\r\n');
}

async function PrebooruCreateIllust(event) {
    if (Array.isArray(event)) {
        var [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = event;
    } else {
        [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-misc-actions-container');
    }
    let tweet_data = PREBOORU.NTISAS.GetAPIData('tweets', tweet_id);
    console.log('PrebooruCreateIllust-1', {tweet_data, $tweet,tweet_id,user_id,screen_name,user_ident,all_idents});
    if (tweet_data === null) {
        JSPLib.notice.error("Tweet data not found!");
        return;
    }
    let $info = $tweet.find('.prebooru-menu');
    let artist_ids = GetDomDataIds($info, 'artist-ids');
    if (artist_ids.length === 0) {
        JSPLib.notice.error("Prebooru artist not found!");
        return;
    }
    let tags = JSPLib.utility.getObjectAttributes(tweet_data.entities.hashtags, 'text');
    let illust_urls = tweet_data.entities.media.map((entry, i)=>{
        let parse = new URL(entry.media_url_https);
        let [width, height] = [entry.original_info.width, entry.original_info.height];
        let match = IMAGE2_RG.exec(entry.media_url_https);
        let query_addon = (match ? '?format=%s' % match[3] : "");
        let site_id = SITE_IDS[parse.hostname];
        let url = parse.pathname + query_addon;
        return {
            site_id,
            url,
            width,
            height,
            order: i + 1,
            active: true,
        };
    });
    let commentary = tweet_data.full_text;
    tweet_data.entities.urls.reverse().forEach((url_data)=>{
        commentary = commentary.slice(0, url_data.indices[0]) + tweet_data.expanded_url + commentary.slice(url_data.indices[1]);
    });
    commentary = commentary.replace(/https?:\/\/t\.co\/\w+/g, "").trim();
    let send_data = {
        illust: {
            site_id: 3,
            site_illust_id: tweet_id,
            site_created: new Date(tweet_data.created_at).toISOString(),
            pages: tweet_data.extended_entities.media.length,
            score: tweet_data.favorite_count,
            retweets: tweet_data.retweet_count,
            replies: tweet_data.reply_count,
            quotes: tweet_data.quote_count,
            requery: null,
            tags,
            commentary,
            illust_urls,
            active: true,
            site_artist_id: user_id,
            artist_id: artist_ids[0],
        },
    };
    console.log('PrebooruCreateIllust-2', tweet_id, Number(tweet_id), parseInt(tweet_id), send_data);
    JSPLib.network.post(PREBOORU_SERVER_URL + '/illusts.json', {data: send_data}).then((data)=>{
        if (data.error) {
            JSPLib.notice.error(data.message);
        } else {
            JSPLib.notice.notice("Illust created.");
            let item_ids = [data.item.id];
            SaveData('illusts-' + tweet_id, item_ids, 'prebooru');
            UpdatePrebooruItems(tweet_id, item_ids, 'illust', []);
            SetPrebooruData(tweet_id, 'illusts', item_ids);
        }
        console.warn('PrebooruCreateIllust-3', data);
    });
}

function PrebooruAddTweetNotation(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-misc-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    let illust_ids = GetDomDataIds($info, 'illust-ids');
    if (post_ids.length == 1) {
        PrebooruAddPostNotation(event);
    } else if (illust_ids.length == 1) {
        PrebooruAddIllustNotation(event);
    } else {
        JSPLib.notice.error("No posts or illusts to notate!");
    }
}

function PrebooruAddIllustNotation(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-misc-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let illust_ids = GetDomDataIds($info, 'illust-ids');
    if (illust_ids.length == 1) {
        let illust_id = illust_ids[0];
        let prompt_string = prompt(`Enter notation for illust #${illust_id}.`);
        if (prompt_string !== null && prompt_string.trim().length > 0) {
            let post_data = {
                notation: {
                    body: prompt_string,
                    illust_id,
                }
            };
            $.post(PREBOORU_SERVER_URL + `/notations.json`, post_data, null, 'json').done((data)=>{
                if (data.error) {
                    JSPLib.notice.error(data.message);
                } else {
                    JSPLib.notice.notice("Notation added.");
                }
            }).fail((data)=>{
                console.warn("Network error:", data);
                JSPLib.notice.error("Network error: illust notation.");
            });
        }
    } else if (illust_ids.length == 0) {
        JSPLib.notice.error("No illusts to notate!");
    } else {
        JSPLib.notice.notice("Multiple illustrations not handled yet.");
    }
}

function PrebooruAddPostNotation(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-misc-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    if (post_ids.length == 1) {
        let post_id = post_ids[0];
        let prompt_string = prompt(`Enter notation for post #${post_id}.`);
        if (prompt_string !== null && prompt_string.trim().length > 0) {
            let post_data = {
                notation: {
                    body: prompt_string,
                    post_id,
                }
            };
            $.post(PREBOORU_SERVER_URL + `/notations.json`, post_data, null, 'json').done((data)=>{
                if (data.error) {
                    JSPLib.notice.error(data.message);
                } else {
                    JSPLib.notice.notice("Notation added.");
                }
            }).fail((data)=>{
                console.warn("Network data:", data);
                JSPLib.notice.error("Network error: post notation.");
            });
        }
    } else if (post_ids.length == 0) {
        JSPLib.notice.error("No posts to notate!");
    } else {
        JSPLib.notice.notice("Multiple posts not handled yet.");
    }
}

function PrebooruAddTweetTag(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-misc-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    let illust_ids = GetDomDataIds($info, 'illust-ids');
    console.log('PrebooruAddTweetTag', post_ids);
    if (post_ids.length !== 0) {
        let prompt_string = prompt(`Enter tag for posts: ${post_ids.join(', ')}.`);
        if (prompt_string !== null && prompt_string.trim().length > 0) {
            let promise_array = [];
            post_ids.forEach((post_id)=>{
                let tags = prompt_string.split(' ');
                tags.forEach((tag)=>{
                    let post_data = {
                        tag: {
                            name: tag,
                            post_id,
                        },
                    };
                    let p = JSPLib.network.post(PREBOORU_SERVER_URL + `/tags/append.json`, {data: post_data, type: 'json'}).done((data)=>{
                        if (data.error) {
                            console.warn("Prebooru error:", data);
                            JSPLib.notice.error(data.message);
                            return Object.assign({post_id}, data);
                        } else {
                            return {error: false};
                        }

                    }).fail((data)=>{
                        console.warn("Network data:", data);
                        return {error: true, message: "Network error. See console for details.", post_id};
                    });
                    promise_array.push(p);
                });
            });
            Promise.all(promise_array).then((results)=>{
                let errors = results.filter((result)=>result.error);
                if (errors.length) {
                    let unique_errors = {};
                    errors.forEach((error)=>{
                        unique_errors[error.message] ||= [];
                        unique_errors[error.message].push(error.post_id);
                    });
                    let error_string = Object.entries(unique_errors).map((message, post_ids)=>{
                        return '<strong>' + message + '</strong> -> ' + JSPLib.utility.joinList(post_ids, 'post #', "", ', ');
                    });
                } else {
                    JSPLib.notice.notice('Tags added.');
                }
            });
        }
    } else {
        JSPLib.notice.error("No posts or illusts to notate!");
    }
}

function PrebooruAddPoolTweet(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-pool-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    let illust_ids = GetDomDataIds($info, 'illust-ids');
    if (post_ids.length == 1) {
        PrebooruAddPoolPost(event);
    } else if (illust_ids.length == 1) {
        PrebooruAddPoolIllust(event);
    } else {
        JSPLib.notice.error("No posts or illusts to add to pool!");
    }
}

function PrebooruAddPoolIllust(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-pool-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let illust_ids = GetDomDataIds($info, 'illust-ids');
    if (illust_ids.length == 1) {
        let illust_id = illust_ids[0];
        if (confirm("Add illust to current pool?")) {
            let post_data = {
                pool_element: {
                    pool_id: PREBOORU.current_pool.id,
                    illust_id: illust_id,
                },
            };
            $.post(PREBOORU_SERVER_URL + `/pool_elements.json`, post_data, null, 'json').done((data)=>{
                if (data.error) {
                    JSPLib.notice.error(data.message);
                } else {
                    JSPLib.notice.notice("Illust added to pool.");
                    PREBOORU.current_pool = data.pool;
                    JSPLib.storage.saveData('prebooru-prebooru-pool', PREBOORU.current_pool, STORAGE_DATABASES.prebooru);
                    UpdatePoolDisplay();
                }
            }).fail((data)=>{
                console.warn("Network error:", data);
                JSPLib.notice.error("Network error: pool illust.");
            });
        }
    } else if (illust_ids.length == 0) {
        JSPLib.notice.error("No illusts to add!");
    } else {
        JSPLib.notice.notice("Multiple illusts not handled yet.");
    }
}

function PrebooruAddPoolPost(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-pool-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    if (post_ids.length == 1) {
        let post_id = post_ids[0];
        if (confirm("Add post to current pool?")) {
            let post_data = {
                pool_element: {
                    pool_id: PREBOORU.current_pool.id,
                    post_id: post_id,
                },
            };
            $.post(PREBOORU_SERVER_URL + `/pool_elements.json`, post_data, null, 'json').done((data)=>{
                if (data.error) {
                    JSPLib.notice.error(data.message);
                } else {
                    JSPLib.notice.notice("Post added to pool.");
                    PREBOORU.current_pool = data.pool;
                    JSPLib.storage.saveData('prebooru-prebooru-pool', PREBOORU.current_pool, STORAGE_DATABASES.prebooru);
                    UpdatePoolDisplay();
                }
            }).fail((data)=>{
                console.warn("Network error:", data);
                JSPLib.notice.error("Network error: pool post.");
            });
        }
    } else if (post_ids.length == 0) {
        JSPLib.notice.error("No posts to add!");
    } else {
        JSPLib.notice.notice("Multiple posts not handled yet.");
    }
}

function PrebooruQueryTweetPools(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-pool-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    let illust_ids = GetDomDataIds($info, 'illust-ids');
    if (post_ids.length == 1) {
        PrebooruQueryPostPools(event);
    } else if (illust_ids.length == 1) {
        PrebooruQueryIllustPools(event);
    } else {
        JSPLib.notice.error("No posts or illusts to query pool!");
    }
}

function PrebooruQueryIllustPools(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-pool-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let illust_ids = GetDomDataIds($info, 'illust-ids');
    if (illust_ids.length == 1) {
        let get_data = {
            search: {
                illust_id: illust_ids[0],
            },
        };
        $.getJSON(PREBOORU_SERVER_URL + '/pools.json', get_data).done((data)=>{
            JSONNotice(data);
        }).fail((data)=>{
            console.warn("Network error:", data);
            JSPLib.notice.error("Network error: PrebooruQueryIllustPools.");
        });
    } else if (illust_ids.length == 0) {
        JSPLib.notice.error("No illusts to query!");
    } else {
        JSPLib.notice.notice("Multiple illusts not handled yet.");
    }
}

function PrebooruQueryPostPools(event) {
    let [$tweet,tweet_id,user_id,screen_name,user_ident,all_idents] = GetPrebooruDialogPreload(event, '.prebooru-pool-actions-container');
    let $info = $tweet.find('.prebooru-menu');
    let post_ids = GetDomDataIds($info, 'post-ids');
    if (post_ids.length == 1) {
        let get_data = {
            search: {
                post_id: post_ids[0]
            },
        };
        $.getJSON(PREBOORU_SERVER_URL + '/pools.json', get_data).done((data)=>{
            JSONNotice(data);
        }).fail((data)=>{
            console.warn("Network error:", data);
            JSPLib.notice.error("Network error: PrebooruQueryPostPools.");
        });
    } else if (post_ids.length == 0) {
        JSPLib.notice.error("No posts to query!");
    } else {
        JSPLib.notice.notice("Multiple posts not handled yet.");
    }
}

function PrebooruMiscActions(event) {
    let [$link,$tweet,tweet_id,,screen_name,,all_idents,] = GetEventPreload(event, 'prebooru-prebooru-info');
    if (!PREBOORU.prebooru_misc_dialog[tweet_id]) {
        PREBOORU.prebooru_misc_dialog[tweet_id] = InitializeMiscActions(tweet_id);
        PREBOORU.prebooru_misc_anchor[tweet_id] = $link;
    }
    PREBOORU.prebooru_misc_dialog[tweet_id].dialog('open');
}

function PrebooruPoolActions(event) {
    let [$link,$tweet,tweet_id,,screen_name,,all_idents,] = GetEventPreload(event, 'prebooru-prebooru-info');
    if (!PREBOORU.prebooru_pool_dialog[tweet_id]) {
        PREBOORU.prebooru_pool_dialog[tweet_id] = InitializePoolActions(tweet_id);
        PREBOORU.prebooru_pool_anchor[tweet_id] = $link;
    }
    PREBOORU.prebooru_pool_dialog[tweet_id].dialog('open');
}

//To move

function ToggleLinkMenu(event) {
    let menu_shown = GetLocalData('prebooru-link-menu', true);
    SetLocalData('prebooru-link-menu', !menu_shown);
    UpdateLinkMenu();
    UpdateLinkControls();
    PREBOORU.channel.postMessage({type: 'linkmenu_ui'});
}

function UpdateLinkMenu() {
    let menu_shown = GetLocalData('prebooru-link-menu', true);
    console.log('UpdateLinkMenu', menu_shown);
    if (menu_shown) {
        $('.prebooru-menu').show();
    } else {
        $('.prebooru-menu').hide();
    }
}

function UpdateLinkControls() {
    let indicators_enabled = GetLocalData('prebooru-link-menu', true);
    console.log('UpdateLinkControls', indicators_enabled);
    if (indicators_enabled) {
        DisplayControl('disable', PREBOORU_CONTROLS, 'menu');
    } else {
        DisplayControl('enable', PREBOORU_CONTROLS, 'menu');
    }
}

//Main execution functions

function RegularCheck() {
    let new_tweets = false;
    $('.ntisas-tweet:not(.prebooru-tweet)').each((i, tweet) => {
        let $tweet = $(tweet);
        $tweet.addClass('prebooru-tweet');
        InitializePrebooruMenu(tweet);
        new_tweets = true;
    });
    if (new_tweets) {
        UpdateLinkMenu();
    }
    if (PREBOORU.page != PREBOORU.NTISAS.page) {
        UpdatePrebooruMenu();
        UpdateLinkControls();
        PREBOORU.page = PREBOORU.NTISAS.page;
    }
}

async function PrebooruUploadRecheck() {
    if (document.hidden) {
        return;
    }
    RefreshUploadRecords();
    if (PREBOORU.upload_records.length == 0) {
        return;
    }
    let pending_records = PREBOORU.upload_records.filter((record) => record.status === 'pending' || record.status === 'processing');
    if (pending_records.length === 0) {
        return;
    }
    let id_string = pending_records.map((record) => record.id).join(',');
    let uploads = await $.getJSON(`${PREBOORU_SERVER_URL}/uploads.json`, {search: {id: id_string}});
    JSPLib.debug.debuglog("Prebooru uploads:", uploads);
    let dirty = false;
    for (let i = 0; i < uploads.length; i++) {
        let upload = uploads[i];
        let upload_record = pending_records.find((record) => record.id == upload.id);
        if (upload.status === 'complete') {
            let tweet_id = upload_record.tweet_id;
            if (upload.post_ids.length > 0) {
                let prebooru_key = 'posts-' + tweet_id;
                GetData(prebooru_key, 'prebooru').then((post_ids)=>{
                    post_ids = post_ids || [];
                    post_ids = JSPLib.utility.arrayDifference(JSPLib.utility.arrayUnion(post_ids, upload.post_ids), upload.duplicate_post_ids);
                    SaveData(prebooru_key, post_ids, 'prebooru');
                    UpdatePrebooruItems(tweet_id, post_ids, 'post');
                    SetPrebooruData(tweet_id, 'posts', post_ids);
                    upload_record.posts = post_ids;
                    if (upload_record.posts.length === 0) {
                        PREBOORU.upload_records = PREBOORU.upload_records.filter((record) => record.id !== upload_record.id);
                    }
                    SetUploadRecords();
                });
                let illusts = LocalPrebooruData(tweet_id, 'illust');
                if (illusts.length === 0) {
                    IllustsCallback(upload_record);
                } else {
                    upload_record.illusts = illusts;
                    SetUploadRecords();
                }
                if (LocalPrebooruData(tweet_id, 'artist').length === 0) {
                    ArtistsCallback(upload_record);
                }
            }
            if (upload.duplicate_post_ids.length > 0) {
                let post_shortlink_string = JSPLib.utility.joinList(upload.duplicate_post_ids, 'post #', null, ', ');
                JSPLib.notice.notice(DtextNotice(`Upload #${upload.id} has duplicates(${upload.duplicate_post_ids.length}):<br>&emsp;=> ${post_shortlink_string}`));
            }
            upload_record.status = 'complete';
            SetUploadRecords();
        }
        if (upload.status === 'error' || upload.errors.length) {
            let display_errors = upload.errors.filter(error => !PREBOORU.displayed_errors.has(error.id));
            if (display_errors.length) {
                let error_string = display_errors.map(error => `${error.module}: ${error.message}`).join(' ;') || "Unknown error occurred. Check the server logs.";
                JSPLib.notice.error(DtextNotice(`Error with upload #${upload.id}<br>&emsp;=> ${error_string}`));
                display_errors.forEach((error) => PREBOORU.displayed_errors.add(error.id));
            }
        }
    }
    if (dirty) {
        SetUploadRecords();
    }
}

async function AddPrebooruUploadsToPool() {
    if (document.hidden || PREBOORU.current_pool === false) {
        return;
    }
    RefreshUploadRecords();
    if (PREBOORU.upload_records.length == 0) {
        return;
    }
    let complete_uploads = PREBOORU.upload_records.filter((record) => record.status === 'complete');
    if (complete_uploads.length === 0) {
        return;
    }
    if (complete_uploads.some((record) => record.pool_id === null)) {
        complete_uploads = complete_uploads.filter((record) => record.pool_id !== null);
        PREBOORU.upload_records = PREBOORU.upload_records.filter((record) => (record.pool_id !== null || record.status !== 'complete'));
        SetUploadRecords();
    }
    let dirty = false;
    for (let i = 0; i < complete_uploads.length; i++) {
        let upload_record = complete_uploads[i];
        let tweet_id = upload_record.tweet_id;
        //console.log("#UR", upload_record);
        if (!Array.isArray(upload_record.posts) || !Array.isArray(upload_record.illusts)) {
            //Need to add validation for upload records to prevent this from happening
            //Had one upload record missing posts for some reason...???
            continue;
        }
        if (upload_record.posts.length && upload_record.illusts.length) {
            let post_data = {
                pool_element: {
                    pool_id: upload_record.pool_id,
                },
            };
            if (upload_record.posts.length > 1) {
                post_data.pool_element.illust_id = upload_record.illusts[0];
            } else {
                post_data.pool_element.post_id = upload_record.posts[0];
            }
            $.post(PREBOORU_SERVER_URL + `/pool_elements.json`, post_data, null, 'json').done((data)=>{
                if (data.error) {
                    JSPLib.notice.error(data.message);
                    PREBOORU.failed_pool_adds.push(tweet_id);
                    SetLocalData('ntisas-failed-pool-adds', PREBOORU.failed_pool_adds);
                } else {
                    var other_pool = null;
                    if (PREBOORU.current_pool?.id === data.pool.id) {
                        PREBOORU.current_pool = data.pool;
                        JSPLib.storage.saveData('prebooru-prebooru-pool', PREBOORU.current_pool, STORAGE_DATABASES.prebooru);
                    } else if (PREBOORU.prior_pool?.id === data.pool.id) {
                        PREBOORU.prior_pool = data.pool;
                        JSPLib.storage.saveData('ntisas-prior-pool', PREBOORU.prior_pool, STORAGE_DATABASES.prebooru);
                    } else {
                        other_pool = data;
                    }
                    UpdatePoolDisplay(other_pool);
                }
            }).fail((error)=>{
                JSPLib.notice.error("Network error: pool add.");
                let error_key = '[POST] ' + PREBOORU_SERVER_URL + '/pool_elements.json\nData:\n' + JSON.stringify(post_data, null, 2);
                JSPLib.network.logError(error_key, error);
                console.error("Network error:", error_key, error);
                PREBOORU.failed_pool_adds.push(tweet_id);
                SetLocalData('ntisas-failed-pool-adds', PREBOORU.failed_pool_adds);
            });
            upload_record.status = 'finished';
            dirty = true;
        } else if (!JSPLib.utility.validateExpires(upload_record.expires, JSPLib.utility.one_second * 15)) {
            if (upload_record.tweet_id in PREBOORU.prebooru_data) {
                let tweet_data = PREBOORU.prebooru_data[upload_record.tweet_id];
                upload_record.illusts = tweet_data.illusts;
                upload_record.posts = tweet_data.posts;
            } else if (upload_record.illusts.length === 0) {
                IllustsCallback(upload_record);
            }
        }
    }
    if (dirty) {
        PREBOORU.upload_records = PREBOORU.upload_records.filter((record) => record.id !== 'finished');
        SetUploadRecords();
    }
}

//Settings functions

function BroadcastPREBOORU(ev) {
    this.debug('log', `(${ev.data.type}):`, ev.data);
    switch (ev.data.type) {
        case 'pendinguploads':
            PREBOORU.upload_records = ev.data.upload_records;
            UpdateUploadRecords(false);
            break;
        case 'preboorulink':
            UpdatePrebooruItems(ev.data.tweet_id, ev.data.item_ids, ev.data.subtype, ev.data.all_idents, false);
            PREBOORU.prebooru_data[ev.data.tweet_id] = PREBOORU.prebooru_data[ev.data.tweet_id] || {};
            PREBOORU.prebooru_data[ev.data.tweet_id][ev.data.subtype + 's'] = ev.data.item_ids;
            break;
        case 'prebooru_ui':
            UpdateLinkControls();
            UpdateLinkMenu();
            break;
        case 'pool':
            JSPLib.storage.removeIndexedSessionData('prebooru-prebooru-pool', STORAGE_DATABASES.prebooru);
            JSPLib.storage.removeIndexedSessionData('ntisas-prior-pool', STORAGE_DATABASES.prebooru);
            break;
            // falls through
        default:
            //do nothing
    }
}


//Main function

async function Main() {
    Object.assign(PREBOORU, {
        channel: JSPLib.utility.createBroadcastChannel(PROGRAM_NAME, BroadcastPREBOORU),
    }, PROGRAM_DEFAULT_VALUES, PROGRAM_RESET_KEYS);
    JSPLib.network.jQuerySetup();
    JSPLib.notice.installBanner(PROGRAM_SHORTCUT);
    JSPLib.load.setProgramGetter(PREBOORU, 'NTISAS', 'NTISAS');
    $(document).on(PROGRAM_CLICK, '.prebooru-post-preview a', SelectPreview);
    $(document).on(PROGRAM_CLICK, '.prebooru-select-controls a', SelectControls);
    $(document).on(PROGRAM_CLICK, '.prebooru-force-prebooru-upload', TogglePrebooruForceUpload);
    $(document).on(PROGRAM_CLICK, '.prebooru-all-prebooru-upload', PrebooruAllUpload);
    $(document).on(PROGRAM_CLICK, '.prebooru-select-prebooru-upload', PrebooruSelectUpload);
    $(document).on(PROGRAM_CLICK, '.prebooru-prebooru-uploads', PrebooruUploads);
    $(document).on(PROGRAM_CLICK, '.prebooru-prebooru-posts', PrebooruPosts);
    $(document).on(PROGRAM_CLICK, '.prebooru-prebooru-illusts', PrebooruIllusts);
    $(document).on(PROGRAM_CLICK, '.prebooru-prebooru-artists', PrebooruArtists);
    $(document).on(PROGRAM_CLICK, '.prebooru-prebooru-thumbs', PrebooruThumbs);
    $(document).on(PROGRAM_CLICK, '.prebooru-prebooru-similar', PrebooruSimilar);
    $(document).on(PROGRAM_CLICK, '.prebooru-pool-actions', PrebooruPoolActions);
    $(document).on(PROGRAM_CLICK, '.prebooru-misc-actions', PrebooruMiscActions);
    $(document).on(PROGRAM_CLICK, '.prebooru-query-data', PrebooruQueryData);
    $(document).on(PROGRAM_CLICK, '.prebooru-create-illust', PrebooruCreateIllust);
    $(document).on(PROGRAM_CLICK, '.prebooru-add-tweet-tag', PrebooruAddTweetTag);
    $(document).on(PROGRAM_CLICK, '.prebooru-add-tweet-notation', PrebooruAddTweetNotation);
    $(document).on(PROGRAM_CLICK, '.prebooru-add-illust-notation', PrebooruAddIllustNotation);
    $(document).on(PROGRAM_CLICK, '.prebooru-add-post-notation', PrebooruAddPostNotation);
    $(document).on(PROGRAM_CLICK, '.prebooru-add-pool-tweet', PrebooruAddPoolTweet);
    $(document).on(PROGRAM_CLICK, '.prebooru-add-pool-illust', PrebooruAddPoolIllust);
    $(document).on(PROGRAM_CLICK, '.prebooru-add-pool-post', PrebooruAddPoolPost);
    $(document).on(PROGRAM_CLICK, '.prebooru-query-tweet-pools', PrebooruQueryTweetPools);
    $(document).on(PROGRAM_CLICK, '.prebooru-query-illust-pools', PrebooruQueryIllustPools);
    $(document).on(PROGRAM_CLICK, '.prebooru-query-post-pools', PrebooruQueryPostPools);
    JSPLib.utility.initializeInterval(RegularCheck, PROGRAM_RECHECK_INTERVAL);
    setInterval(IntervalStorageHandler, QUEUE_POLL_INTERVAL);
    setInterval(PrebooruUploadRecheck, JSPLib.utility.one_second * 2.5);
    setInterval(AddPrebooruUploadsToPool, JSPLib.utility.one_second * 2.5);
    JSPLib.utility.setCSSStyle(PROGRAM_CSS, 'program');
}
/****Function decoration****/

[
    BroadcastPREBOORU, PickImage, GetImageAttributes,
    IntervalStorageHandler, PrebooruSelectUpload, PrebooruAllUpload,
] = JSPLib.debug.addFunctionLogs([
    BroadcastPREBOORU, PickImage, GetImageAttributes,
    IntervalStorageHandler, PrebooruSelectUpload, PrebooruAllUpload,
]);

/****Initialization****/

//Variables for debug.js
JSPLib.debug.debug_console = true;
JSPLib.debug.level = JSPLib.debug.INFO;
JSPLib.debug.program_shortcut = PROGRAM_SHORTCUT;

//Variables for load.js
JSPLib.load.load_when_hidden = false;

//Export JSPLib
JSPLib.load.exportData(PROGRAM_NAME, PREBOORU);

/****Execution start****/

JSPLib.load.programInitialize(Main, {program_name: PROGRAM_NAME, required_selectors: PROGRAM_LOAD_REQUIRED_SELECTORS, max_retries: 100});
