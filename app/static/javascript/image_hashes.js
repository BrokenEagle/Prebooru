// APP/STATIC/JAVASCRIPT/IMAGE_HASHES.JS

const ImageHashes = {};

ImageHashes.showForm = function (obj) {
    document.getElementById('form').classList.remove('hidden');
    obj.parentElement.style.display = 'none';
    return false;
};
