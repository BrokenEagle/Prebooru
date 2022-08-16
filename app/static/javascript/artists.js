// APP/STATIC/JAVASCRIPT/ARTISTS.JS

/* global Prebooru */

const Artists = {};

Artists.createArtistFromUrl = function(obj) {
    return Prebooru.promptArgPost(obj, "Enter the site artist URL to create from:", 'url');
};
