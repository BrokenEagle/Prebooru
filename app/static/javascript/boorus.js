// APP/STATIC/JAVASCRIPT/BOORUS.JS

/* global Prebooru */

const Boorus = {};

Boorus.createFromId = function (obj) {
    return Prebooru.promptArgPost(obj, "Enter the danbooru artist ID to create from:", 'danbooru_id');
};

Boorus.addArtist = function (obj) {
    let artist_id = prompt("Enter artist ID to add:");
    if (artist_id !== null) {
        Prebooru.postRequest(obj.href, {'artist_id': artist_id});
    }
    return false;
};
