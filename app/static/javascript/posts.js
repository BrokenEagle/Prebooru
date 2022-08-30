// APP/STATIC/JAVASCRIPT/POSTS.JS

/* global Prebooru */

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

Posts.loadOriginal = function (obj) {
    let video = document.querySelector('#media-container video');
    video.src = video.dataset.original;
    obj.style.setProperty('display', 'none');
    return false;
};

Posts.initializePlay = function () {
    let container = document.querySelector('#media-container');
    let icon = container.querySelector('.play-icon');
    let video = container.querySelector('video');
    let post_width = parseInt(video.attributes.width.value);
    let post_height = parseInt(video.attributes.height.value);
    const norm_width = Math.min(125, Math.floor(post_width / 4));
    const norm_height = Math.min(125, Math.floor(post_height / 4));
    const expand_width = Math.min(150, Math.floor(post_width * 1.25 / 4));
    const expand_height = Math.min(150, Math.floor(post_height * 1.25 / 4));
    icon.width = norm_width;
    icon.height = norm_height;
    icon.onmouseenter = function () {
        icon.width = expand_width;
        icon.height = expand_height;
    };
    icon.onmouseleave = function () {
        icon.width = norm_width;
        icon.height = norm_height;
    };
    icon.onclick = function () {
        container.classList.replace('loading', 'playing');
        video.src = video.dataset.src;
    };
};
