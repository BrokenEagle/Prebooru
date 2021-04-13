const Posts = {};

Posts.createUpload = function(obj) {
    let url = prompt("Enter the URL of the post to upload from:");
    if (url !== null) {
        Prebooru.postRequest(obj.href, {'upload[request_url]': url});
    }
    return false;
};

Posts.regenerateSimilarity = function(obj) {
    if (confirm("Regenerate similarity data and pools?")) {
        Prebooru.postRequest(obj.href);
    }
    return false;
};

Posts.copyFileLink = function(obj) {
    console.log(obj);
    prompt('Copy file link:', obj.dataset.filePath);
    return false;
};