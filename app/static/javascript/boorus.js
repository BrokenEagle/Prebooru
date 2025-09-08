// APP/STATIC/JAVASCRIPT/BOORUS.JS

/* global Prebooru */

const Boorus = {};

Boorus.createFromId = function (obj) {
    return Prebooru.promptArgPost(obj, "Enter the danbooru artist ID to create from:", 'danbooru_id');
};
