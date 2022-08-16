// APP/STATIC/JAVASCRIPT/TAGS.JS

/* global Prebooru */

const Tags = {};

Tags.createUserTagFromName = function(obj) {
    let arg = prompt("Enter the name of the tag to create:");
    if (arg !== null) {
        Prebooru.postRequest(obj.href, {'tag[name]': arg, 'tag[type]': 'user_tag'});
    }
    return false;
};
