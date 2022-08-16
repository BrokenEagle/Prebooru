// APP/STATIC/JAVASCRIPT/ILLUSTS.JS

/* global Prebooru */

const Illusts = {};

Illusts.createFromUrl = function (obj) {
    return Prebooru.promptArgPost(obj, "Enter the site illust URL to create from:", 'url');
};
