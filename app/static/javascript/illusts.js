// APP/STATIC/JAVASCRIPT/ILLUSTS.JS

/* global Prebooru */

const Illusts = {};

(function () {
    const SITE_MAP = {
        "": "",
        "1": 'pixiv-data',
        "3": 'twitter-data',
    };
    Illusts.createFromUrl = function (obj) {
        return Prebooru.promptArgPost(obj, "Enter the site illust URL to create from:", 'url');
    };
    Illusts.changeSite = function () {
        let site_id = document.getElementById("illust-site-id").value;
        document.getElementById('form').className = SITE_MAP[site_id];
    };
    Illusts.updateArtist = function(obj) {
        return Prebooru.promptArgPost(obj, "Enter the artist ID:", 'artist_id');
    };

})();

