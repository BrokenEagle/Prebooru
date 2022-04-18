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
            }
        });
    return false;
};

SubscriptionPools.replaceArticle = function(obj, html) {
    for (var curr = obj; curr.tagName !== 'ARTICLE' && curr.parentElement !== null; curr = curr.parentElement);
    curr.outerHTML = html;
};
