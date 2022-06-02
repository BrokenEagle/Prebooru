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

Prebooru.addTag = function (obj, type) {
    let item_id = obj.dataset[type + 'Id'];
    let tag_name = prompt("Enter tag name to add:");
    if (tag_name !== null) {
        Prebooru.postRequest(obj.href, {'tag[name]': tag_name, [`tag[${type}_id]`]: item_id});
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

Prebooru.copyFileLink = function(obj) {
    prompt('Copy file link:', obj.dataset.filePath);
    return false;
};

Prebooru.message = function(msg) {
    this.processNotice('notice-message', msg);
    this._notice_timeout_id = setTimeout(function () {
        Prebooru.closeNotice();
        Prebooru._notice_timeout_id = null;
    }, 6000);
};

Prebooru.error = function(msg) {
    this.processNotice('notice-error', msg);
};

Prebooru.processNotice = function(notice_class, msg) {
    let $notice = document.getElementById('script-notice');
    $notice.className = notice_class;
    $notice.children['script-notice-message'].innerHTML = msg;
    if (Number.isInteger(this._notice_timeout_id)) {
        clearTimeout(this._notice_timeout_id);
        this._notice_timeout_id = null;
    }
};

Prebooru.closeNotice = function() {
    document.getElementById('script-notice').className = "";
    return false;
};

Prebooru.keepElement = function(obj) {
    fetch(obj.href, {method: 'POST'})
        .then((resp)=>resp.json())
        .then((data)=>{
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message("Updated element.");
                Prebooru.replaceDiv(obj, data.html);
            }
        });
    return false;
};

Prebooru.replaceDiv = function(obj, html) {
    for (var curr = obj; curr.tagName !== 'DIV' && curr.parentElement !== null; curr = curr.parentElement);
    curr.outerHTML = html;
};