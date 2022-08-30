// APP/STATIC/JAVASCRIPT/SIMILARITY_POOLS.JS

/* global Prebooru */

const SimilarityPools = {};

SimilarityPools.deleteElement = function(obj) {
    fetch(obj.href, {method: 'DELETE'})
        .then((resp) => resp.json())
        .then((data) => {
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message("Deleted element.");
                SimilarityPools.removeArticle(obj);
                document.getElementById('image-select-counter').innerText = document.querySelectorAll('.similarity-element .checkbox-active').length;
            }
        });
    return false;
};

SimilarityPools.removeArticle = function(obj) {
    let $article = Prebooru.closest(obj, 'article');
    $article.outerHTML = "";
};

SimilarityPools.toggleCheckbox = function(obj) {
    let $div = Prebooru.closest(obj, 'div');
    if (obj.checked) {
        $div.classList.add('checkbox-active');
    } else {
        $div.classList.remove('checkbox-active');
    }
};

SimilarityPools.updateAllInputs = function() {
    document.querySelectorAll('form#form input[type=checkbox]').forEach((input) => {
        SimilarityPools.toggleCheckbox(input);
    });
};

SimilarityPools.submitForm = function (event, type) {
    event.preventDefault();
    let msg = (type === 'pool' ? "Remove posts from similarity pool?" : "Remove all selected similarity elements?");
    if (confirm(msg)) {
        document.getElementById('form').submit();
    }
    return false;
};

SimilarityPools.initializeEventCallbacks = function() {
    document.addEventListener('prebooru:update-inputs', SimilarityPools.updateAllInputs);
};
