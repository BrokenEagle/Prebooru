// APP/STATIC/JAVASCRIPT/SIMILARITY_MATCHES.JS

/* global Prebooru */

const SimilarityMatches = {};

SimilarityMatches.deleteElement = function(obj) {
    fetch(obj.href, {method: 'DELETE'})
        .then((resp) => resp.json())
        .then((data) => {
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message("Deleted element.");
                SimilarityMatches.removeArticle(obj);
                document.getElementById('image-select-counter').innerText = document.querySelectorAll('.similarity-element .checkbox-active').length;
            }
        });
    return false;
};

SimilarityMatches.removeArticle = function(obj) {
    let $article = Prebooru.closest(obj, 'article');
    $article.outerHTML = "";
};

SimilarityMatches.toggleCheckbox = function(obj) {
    let $div = Prebooru.closest(obj, 'div');
    if (obj.checked) {
        $div.classList.add('checkbox-active');
    } else {
        $div.classList.remove('checkbox-active');
    }
};

SimilarityMatches.updateAllInputs = function() {
    document.querySelectorAll('form#form input[type=checkbox]').forEach((input) => {
        SimilarityMatches.toggleCheckbox(input);
    });
};

SimilarityMatches.submitForm = function (event, type) {
    event.preventDefault();
    let msg = (type === 'pool' ? "Remove all similarity matches?" : "Remove all selected similarity matches?");
    if (confirm(msg)) {
        document.getElementById('form').submit();
    }
    return false;
};

SimilarityMatches.initializeEventCallbacks = function() {
    document.addEventListener('prebooru:update-inputs', SimilarityMatches.updateAllInputs);
};
