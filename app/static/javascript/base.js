const Prebooru = {};

Prebooru.postRequest = function(url, args) {
    let form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    for (let key in args) {
        let input = document.createElement('input');
        input.name = key;
        input.value = args[key];
        input.type = "hidden";
        form.appendChild(input);
    }
    document.body.appendChild(form);
    form.submit();
};

Prebooru.promptArgPost = function(obj, prompt_text, argname) {
    let arg = prompt(prompt_text);
    if (arg !== null) {
        Prebooru.postRequest(obj.href, {[argname]: arg});
    }
    return false;
};

Prebooru.linkPost = function(obj) {
    Prebooru.postRequest(obj.href, {});
    return false;
};

Prebooru.linkDelete = function(obj) {
    Prebooru.postRequest(obj.href, {_method: 'delete'});
    return false;
};

Prebooru.deleteConfirm = function(obj) {
    if (confirm("Delete this item?")) {
        Prebooru.linkDelete(obj);
    }
    return false;
};

Prebooru.createPool = function (obj, type) {
    let item_id = obj.dataset[type + 'Id'];
    let pool_id = prompt("Enter pool # to add to:");
    if (pool_id !== null) {
        Prebooru.postRequest(obj.href, {'pool_element[pool_id]': pool_id, [`pool_element[${type}_id]`]: item_id});
    }
    return false;
};

Prebooru.deletePool = function(obj) {
    if (confirm('Remove item from pool?')) {
        Prebooru.linkDelete(obj);
    }
    return false;
};

Prebooru.selectAll = function(classname) {
    [...document.getElementsByClassName(classname)].forEach((input)=>{
        input.checked = true;
    });
};

Prebooru.selectNone = function(classname) {
    [...document.getElementsByClassName(classname)].forEach((input)=>{
        input.checked = false;
    });
};

Prebooru.selectInvert = function(classname) {
    [...document.getElementsByClassName(classname)].forEach((input)=>{
        input.checked = !input.checked;
    });
};
