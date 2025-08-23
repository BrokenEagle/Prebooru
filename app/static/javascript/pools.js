// APP/STATIC/JAVASCRIPT/POOLS.JS

/* global Prebooru */

const Pools = {};

Pools.deleteElement = function(obj) {
    let $section = document.querySelector('.pool-section');
    fetch(obj.href, {method: 'DELETE'})
        .then((resp) => resp.json())
        .then((data) => {
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message(`Removed ${data.type} #${data.item.id} from pool.`);
                $section.outerHTML = data.html;
            }
        });
    return false;
};

Pools.createElement = function (obj, type) {
    let $section = document.querySelector('.pool-section');
    let item_id = obj.dataset[type + 'Id'];
    let pool_id = prompt("Enter pool # to add to:");
    if (pool_id !== null) {
        let data = new FormData();
        data.append('pool_element[pool_id]', pool_id);
        data.append(`pool_element[${type}_id]`, item_id);
        fetch(obj.href, {method: 'POST', body: data})
            .then((resp) => resp.json())
            .then((data) => {
                if (data.error) {
                    Prebooru.error(data.message);
                } else {
                    Prebooru.message(`Added ${type} #${item_id} to pool.`);
                    $section.outerHTML = data.html;
                }
            });
    }
    return false;
};

Pools.deleteElements = function () {
    if (document.querySelectorAll('div.input.checkbox-active').length) {
        if(confirm("Remove these items from pool?")) {
            let form = document.querySelector('#form');
            form.submit();
        }
    } else {
        Prebooru.message("No elements selected.");
    }
    return false;
};
