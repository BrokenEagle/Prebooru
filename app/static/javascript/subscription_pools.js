// APP/STATIC/JAVASCRIPT/SUBSCRIPTION_POOLS.JS

/* global Prebooru */

const SubscriptionPools = {};

SubscriptionPools.networkHandler = function(obj) {
    let $element = Prebooru.closest(obj, '.subscription-element');
    fetch(obj.href, {method: 'POST'})
        .then((resp) => resp.json())
        .then((data) => {
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message("Updated element.");
            }
            if (data.html) {
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

SubscriptionPools.toggleCheckbox = function(obj) {
    let $div = Prebooru.closest(obj, 'div');
    if (obj.checked) {
        $div.classList.add('checkbox-active');
    } else {
        $div.classList.remove('checkbox-active');
    }
};

SubscriptionPools.updateAllInputs = function() {
    document.querySelectorAll('form#form input[type=checkbox]').forEach((input) => {
        SubscriptionPools.toggleCheckbox(input);
    });
};

SubscriptionPools.delaySubscriptionElements = function(obj) {
    return Prebooru.promptArgPost(obj, "Enter the number of days to delay active elements (0 removes expiration):", 'days');
};

SubscriptionPools.dragKeepClick = function(obj) {
    obj.click();
    return false;
};

SubscriptionPools.initializeReloadInterval = function (pool_status) {
    if (pool_status !== 'manual' && pool_status !== 'automatic') return;
    const page_timer = setInterval(() => {
        if (document.hidden) return;
        window.location.reload();
        clearInterval(page_timer);
    }, 15000);
};

SubscriptionPools.initializeJobQueryInterval = function (job_status, query_url) {
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
                    document.getElementById('subscription-pool-job-stage').innerHTML = data.item.stage || '<em>none</em>';
                    document.getElementById('subscription-pool-job-range').innerHTML = data.item.range || '<em>none</em>';
                    document.getElementById('subscription-pool-job-records').innerText = data.item.records;
                    document.getElementById('subscription-pool-job-elements').innerText = data.item.elements;
                    document.getElementById('subscription-pool-job-illusts').innerText = data.item.illusts;
                    document.getElementById('subscription-pool-job-downloads').innerText = data.item.downloads;
                    if (data.item.stage === 'done') {
                        clearInterval(job_interval);
                    }
                }
            });
    }, 2000);
};

SubscriptionPools.submitForm = function (value) {
    document.getElementById('subscription-pool-element-keep').value = value;
    document.getElementById('form').submit();
    return false;
};

SubscriptionPools.initializeEventCallbacks = function () {
    document.addEventListener('prebooru:update-inputs', SubscriptionPools.updateAllInputs);
};

SubscriptionPools.setAllInputsTimeout = function () {
    setTimeout(() => {
        document.querySelectorAll('.subscription-element input[type=checkbox]').forEach((input) => {
            if (!input.checked) return;
            let curr = Prebooru.closest('div.input');
            if (curr !== null) {
                curr.classList.add('checkbox-active');
            }
        });
    }, 500);
};
