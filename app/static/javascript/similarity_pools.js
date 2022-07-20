const SimilarityPools = {};

SimilarityPools.deleteElement = function(obj) {
    fetch(obj.href, {method: 'DELETE'})
        .then((resp)=>resp.json())
        .then((data)=>{
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
    for (var curr = obj; curr.tagName !== 'ARTICLE' && curr.parentElement !== null; curr = curr.parentElement);
    curr.outerHTML = "";
};

SimilarityPools.toggleCheckbox = function(obj) {
    for (var curr = obj; curr.tagName !== 'DIV' && curr.parentElement !== null; curr = curr.parentElement);
    if (obj.checked) {
        curr.classList.add('checkbox-active');
    } else {
        curr.classList.remove('checkbox-active');
    }
};

SimilarityPools.updateAllInputs = function() {
    document.querySelectorAll('form#form input[type=checkbox]').forEach(function (input) {
        SimilarityPools.toggleCheckbox(input);
    });
};

