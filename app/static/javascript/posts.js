const Posts = {};

Posts.createUpload = function(obj) {
    let url = prompt("Enter the URL of the post to upload from:");
    if (url !== null) {
        Prebooru.postRequest(obj.href, {'upload[request_url]': url});
    }
    return false;
};

Posts.regeneratePreviews = function(obj) {
    if (confirm("Regenerate sample and preview images?")) {
        Prebooru.postRequest(obj.href);
    }
    return false;
};

Posts.regenerateSimilarity = function(obj) {
    if (confirm("Regenerate similarity data and pools?")) {
        Prebooru.postRequest(obj.href);
    }
    return false;
};
