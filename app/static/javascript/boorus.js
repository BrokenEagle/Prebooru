const Booru = {}

Booru.createFromId = function (obj) {
    return Prebooru.promptArgPost(obj, "Enter the danbooru artist ID to create from:", 'danbooru_id');
};
