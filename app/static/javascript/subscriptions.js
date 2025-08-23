// APP/STATIC/JAVASCRIPT/SUBSCRIPTIONS.JS

/* global Prebooru */

const Subscriptions = {};

Subscriptions.networkHandler = function(obj) {
    let $element = Prebooru.closest(obj, '.subscription-element');
    fetch(obj.href, {method: 'POST'})
        .then((resp) => resp.json())
        .then((data) => {
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message("Updated element.");
            }
            if (data.html && $element.parentElement) {
                $element.outerHTML = data.html;
                let $post = $element.querySelector('.post');
                if ($post) {
                    if ($post.classList.contains('video-post')) {
                        Prebooru.initializeVideoPreviews('#' + $post.id);
                    }
                    document.getElementById('image-select-counter').innerText = document.querySelectorAll('.subscription-element .checkbox-active').length;
                    Prebooru.dispatchEvent('prebooru:preview-reloaded', {target: $element, data});
                }
            }
        });
    return false;
};

Subscriptions.delaySubscriptionElements = function(obj) {
    return Prebooru.promptArgPost(obj, "Enter the number of days to delay active elements (0 removes expiration):", 'days');
};

Subscriptions.dragKeepClick = function(obj) {
    obj.click();
    return false;
};

Subscriptions.initializeReloadInterval = function (subscription_status) {
    if (subscription_status !== 'manual' && subscription_status !== 'automatic') return;
    const page_timer = setInterval(() => {
        if (document.hidden) {
            document.onvisibilitychange = function () {
                window.location.reload();
            };
        } else {
            window.location.reload();
        }
        clearInterval(page_timer);
    }, 15000);
};

Subscriptions.initializeJobQueryInterval = function (job_status, query_url) {
    if (job_status === 'done') return;
    const job_interval = setInterval(() => {
        if (document.hidden) return;
        fetch(query_url)
            .then((resp) => resp.json())
            .then((data) => {
                console.log("Job interval:", JSON.stringify(data, null, 4));
                if (data.error) {
                    Prebooru.error(data.message);
                    clearInterval(job_interval);
                } else {
                    document.getElementById('subscription-job-stage').innerHTML = data.item.stage || '<em>none</em>';
                    document.getElementById('subscription-job-range').innerHTML = data.item.range || '<em>none</em>';
                    document.getElementById('subscription-job-records').innerText = data.item.records;
                    document.getElementById('subscription-job-elements').innerText = data.item.elements;
                    document.getElementById('subscription-job-illusts').innerText = data.item.illusts;
                    document.getElementById('subscription-job-downloads').innerText = data.item.downloads;
                    if (data.item.stage === 'done') {
                        clearInterval(job_interval);
                    }
                }
            });
    }, 2000);
};

Subscriptions.submitForm = function (value) {
    document.getElementById('subscription-element-keep').value = value;
    document.getElementById('form').submit();
    return false;
};

Subscriptions.changeProcess = function () {
    let type = [...document.getElementById("process-type").getElementsByTagName('input')].filter((input) => input.checked)[0].value;
    document.getElementById('form').className = type + '-timeline';
};
