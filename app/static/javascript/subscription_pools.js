const SubscriptionPools = {};

SubscriptionPools.networkHandler = function(obj) {
    let has_preview = JSON.parse(obj.dataset.preview);
    let replace_selector = has_preview ? '.subscription-element' : '.subscription-element-info';
    let $element = Prebooru.closest(obj, replace_selector);
    fetch(obj.href, {method: 'POST'})
        .then((resp)=>resp.json())
        .then((data)=>{
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message("Updated element.");
            }
            if (data.html) {
                $element.outerHTML = data.html;
                if (has_preview) {
                    let $post = $element.querySelector('.post');
                    if ($post?.classList.contains('video-post')) {
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
    for (var curr = obj; curr.tagName !== 'DIV' && curr.parentElement !== null; curr = curr.parentElement);
    if (obj.checked) {
        curr.classList.add('checkbox-active');
    } else {
        curr.classList.remove('checkbox-active');
    }
};

SubscriptionPools.updateAllInputs = function() {
    document.querySelectorAll('form#form input[type=checkbox]').forEach(function (input) {
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
