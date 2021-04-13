const SimilarityPosts = {};

SimilarityPosts.deleteElement = function(obj) {
    if (confirm('Remove element from similar posts?')) {
        Prebooru.linkDelete(obj);
    }
    return false;
};
