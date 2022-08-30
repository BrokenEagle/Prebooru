// APP/STATIC/JAVASCRIPT/SIMILARITY.JS

const Similarity = {};

Similarity.showForm = function (obj) {
    document.getElementById('form').classList.remove('hidden');
    obj.parentElement.style.display = 'none';
    return false;
};
