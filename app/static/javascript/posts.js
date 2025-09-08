// APP/STATIC/JAVASCRIPT/POSTS.JS

/* global Prebooru */

const Posts = {};

Posts.submitForm = function (type, url) {
    if (['pool', 'tag'].includes(type)) {
        let post_inputs = document.querySelectorAll('.post-select input[type=checkbox]');
        let post_ids = [...post_inputs].filter((input) => input.checked && input.value.match(/^\d+$/)).map((input) => input.value);
        if (post_ids.length > 0) {
            if (type === 'pool') {
                let pool_id = prompt("Enter pool # to add to:");
                if (pool_id?.match(/^\d+$/)) {
                    let data = new FormData();
                    data.append('pool_element[pool_id]', Number(pool_id));
                    post_ids.forEach((post_id) => {
                        data.append('pool_element[post_id][]', Number(post_id));
                    });
                    fetch(url, {method: 'POST', body: data})
                        .then((resp) => resp.json())
                        .then((data) => {
                            if (data.error) {
                                Prebooru.error(data.message);
                            } else {
                                Prebooru.message(`Added posts to pool #${pool_id}.`);
                            }
                        });
                }
            } else if (type === 'tag') {
                let tag_name = prompt("Enter tag name to add:");
                let data = new FormData();
                data.append('tag[name]', tag_name);
                post_ids.forEach((post_id) => {
                    data.append('tag[post_id][]', Number(post_id));
                });
                fetch(url, {method: 'POST', body: data})
                    .then((resp) => resp.json())
                    .then((data) => {
                        if (data.error) {
                            Prebooru.error(data.message);
                        } else {
                            Prebooru.message(`Added tag ${tag_name} to posts.`);
                        }
                    });
            }
        } else {
            Prebooru.message("No posts selected.");
        }
    }
    return false;
};

Posts.createDownload = function(obj) {
    let url = prompt("Enter the URL of the post to upload from:");
    if (url !== null) {
        Prebooru.postRequest(obj.href, {'download[request_url]': url});
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
