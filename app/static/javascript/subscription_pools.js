const SubscriptionPools = {};

SubscriptionPools.keepElement = function(obj) {
    fetch(obj.href, {method: 'POST'})
        .then((resp)=>resp.json())
        .then((data)=>{
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message("Updated element.");
                SubscriptionPools.replaceArticle(obj, data.html);
                document.getElementById('image-select-counter').innerText = document.querySelectorAll('.subscription-element .checkbox-active').length;
            }
        });
    return false;
};

SubscriptionPools.replaceArticle = function(obj, html) {
    for (var curr = obj; curr.tagName !== 'ARTICLE' && curr.parentElement !== null; curr = curr.parentElement);
    curr.outerHTML = html;
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
