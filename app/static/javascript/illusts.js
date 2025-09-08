// APP/STATIC/JAVASCRIPT/ILLUSTS.JS

/* global Prebooru */

const Illusts = {};

Illusts.createFromUrl = function (obj) {
    return Prebooru.promptArgPost(obj, "Enter the site illust URL to create from:", 'url');
};
Illusts.changeSite = function () {
    let site_id = document.getElementById("illust-site-id").value;
    document.getElementById('form').className = Illusts.SITE_MAP[site_id];
};
Illusts.submitForm = function (url) {
    let illust_inputs = document.querySelectorAll('.illust-display input[type=checkbox]');
    let illust_ids = [...illust_inputs].filter((input) => input.checked && input.value.match(/^\d+$/)).map((input) => input.value);
    if (illust_ids.length > 0) {
        let pool_id = prompt("Enter pool # to add to:");
        if (pool_id?.match(/^\d+$/)) {
            let data = new FormData();
            data.append('pool_element[pool_id]', Number(pool_id));
            illust_ids.forEach((illust_id) => {
                data.append('pool_element[illust_id][]', Number(illust_id));
            });
            fetch(url, {method: 'POST', body: data})
                .then((resp) => resp.json())
                .then((data) => {
                    if (data.error) {
                        Prebooru.error(data.message);
                    } else {
                        Prebooru.message(`Added illusts to pool #${pool_id}.`);
                    }
                });
        }
    } else {
        Prebooru.message("No posts selected.");
    }
    return false;
};
