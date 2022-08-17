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
