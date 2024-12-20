// APP/STATIC/JAVASCRIPT/BASE.JS

const Prebooru = {};

Prebooru.updateInputsEvent = new CustomEvent('prebooru:update-inputs');

Prebooru.dispatchEvent = function (name, data) {
    let event = new CustomEvent(name, {detail: data});
    document.dispatchEvent(event);
};

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

Prebooru.linkPut = function(obj) {
    Prebooru.postRequest(obj.href, {_method: 'put'});
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
    let $section = document.querySelector('#tag-list');
    let item_id = obj.dataset[type + 'Id'];
    let tag_name = prompt("Enter tag name to add:");
    if (tag_name !== null) {
        let data = new FormData();
        data.append('tag[name]', tag_name);
        data.append(`tag[${type}_id]`, item_id);
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

Prebooru.removeTag = function (obj, type) {
    let $section = document.querySelector('#tag-list');
    let item_id = obj.dataset[type + 'Id'];
    let data = new FormData();
    data.append(`tag[${type}_id]`, item_id);
    fetch(obj.href, {method: 'DELETE', body: data})
        .then((resp) => resp.json())
        .then((data) => {
            if (data.error) {
                Prebooru.error(data.message);
            } else {
                Prebooru.message(`Removed tag #${item_id} from ${type} #${item_id}.`);
                $section.outerHTML = data.html;
            }
        });
    return false;
};

Prebooru.selectAll = function(classname) {
    let counter = 0;
    [...document.getElementsByClassName(classname)].forEach((input) => {
        input.checked = true;
        counter++;
    });
    document.getElementById('image-select-counter').innerText = counter;
    document.dispatchEvent(Prebooru.updateInputsEvent);
    return false;
};

Prebooru.selectNone = function(classname) {
    [...document.getElementsByClassName(classname)].forEach((input) => {
        input.checked = false;
    });
    document.getElementById('image-select-counter').innerText = 0;
    document.dispatchEvent(Prebooru.updateInputsEvent);
    return false;
};

Prebooru.selectInvert = function(classname) {
    let counter = 0;
    [...document.getElementsByClassName(classname)].forEach((input) => {
        input.checked = !input.checked;
        counter += (input.checked ? 1 : 0);
    });
    document.getElementById('image-select-counter').innerText = counter;
    document.dispatchEvent(Prebooru.updateInputsEvent);
    return false;
};

Prebooru.selectClick = function(obj) {
    let counter = Number(document.getElementById('image-select-counter').innerText);
    document.getElementById('image-select-counter').innerText = counter + (obj.checked ? 1 : -1);
};

Prebooru.copyFileLink = function(obj) {
    Prebooru.copyToClipboard(obj.dataset.filePath);
    return false;
};

Prebooru.message = function(msg) {
    this.processNotice('notice-message', msg);
    this._notice_timeout_id = setTimeout(() => {
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

Prebooru.copyToClipboard = async function(text) {
    try {
        await navigator.clipboard.writeText(text);
        Prebooru.message("Copied!");
    } catch (error) {
        Prebooru.error("Couldn't copy to clipboard");
    }
};

Prebooru.resizeImage = function (obj) {
    obj.classList.toggle('fullsize');
    return false;
};

Prebooru.onImageError = function (obj) {
    let retries = Number(obj.dataset.loadRetries) || 0;
    if (retries < 3) {
        // eslint-disable-next-line no-self-assign
        setTimeout(() => (obj.src = obj.src), 1000);
    } else {
        obj.src = '/static/image_error.jpg';
    }
    obj.dataset.loadRetries = ++retries;
    console.log("Error:", obj, obj.src, retries);
};

Prebooru.onVideoError = function (obj) {
    console.warn("Error loading video preview", obj.postName);
    obj.onMouseEnter = null;
    obj.onMouseLeave = null;
    obj.videoToImage?.(obj);
    obj.videoPreviewTimeout = false;
};

Prebooru.closest = function(obj, selector) {
    var curr = null;
    for (curr = obj; curr && !curr.matches(selector); curr = curr.parentElement);
    return curr;
};

Prebooru.initializeLazyLoad = function (container_selector) {
    let obs = new IntersectionObserver(((entries, observer) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.querySelectorAll('img[data-src]').forEach((image) => {
                    image.src = image.dataset.src;
                });
                observer.unobserve(entry.target);
            }
        });
    }), {
        rootMargin: '150px',
    });
    document.querySelectorAll(container_selector).forEach((preview) => {
        if (preview.querySelectorAll('img[data-src]').length > 0) {
            obs.observe(preview);
        }
    });
};

Prebooru.coordinateInBox = function(coord, box) {
    return coord.x > box.left && coord.x < box.right && coord.y > box.top && coord.y < box.bottom;
};

Prebooru.initializeVideoPreviews = function (container_selector) {
    function setCoordinate(event) {
        document.body.mousePageX = event.pageX;
        document.body.mousePageY = event.pageY;
    }
    function getWindowBox() {
        return {
            top: window.pageYOffset,
            bottom: window.pageYOffset + window.innerHeight,
            left: window.pageXOffset,
            right: window.pageXOffset + window.innerWidth
        };
    }
    function getImageBox(image) {
        return {
            top: image.offsetTop + image.container.offsetTop,
            bottom: image.offsetTop + image.offsetHeight + image.container.offsetTop,
            left: image.offsetLeft + image.container.offsetLeft,
            right: image.offsetLeft + image.offsetWidth + image.container.offsetLeft,
        };
    }
    function imageToVideo(image) {
        console.log("Changing from image to video on", image.postName);
        image.oldOnerror = image.onerror;
        image.src = image.dataset.video;
        document.body.addEventListener('mousemove', setCoordinate, false);
        image.videoCheckInterval = setTimeout(() => {
            let coord = {x: document.body.mousePageX, y: document.body.mousePageY};
            let box = getImageBox(image);
            if (!Prebooru.coordinateInBox(coord, box)) {
                console.log("Mouse outside", image.postName);
                videoToImage(image);
            }
        }, 500);
    }
    function videoToImage(image) {
        console.log("Changing from video to image on", image.postName);
        image.onerror = image.oldOnerror;
        image.src = image.dataset.src;
        document.body.removeEventListener('mousemove', setCoordinate, false);
        if (image.videoCheckInterval !== null) {
            clearInterval(image.videoCheckInterval);
            image.videoCheckInterval = null;
        }
    }
    function onMouseEnter(event) {
        let image = event.target;
        if (image.enteredPopup || Number.isInteger(image.videoPreviewTimeout)) return;
        image.videoPreviewTimeout = setTimeout(() => {
            imageToVideo(image);
            image.videoPreviewTimeout = true;
            setCoordinate(event);
        }, 500);
    }
    function onMouseLeave(event) {
        let image = event.target;
        let coord = {x: event.pageX, y: event.pageY};
        if (!Prebooru.coordinateInBox(coord, getWindowBox())) {
            console.log("Outside screen on", image.postName);
        } else if (Prebooru.coordinateInBox(coord, getImageBox(image))) {
            console.log("Encountered popup on", image.postName);
            image.enteredPopup = true;
            return;
        }
        image.enteredPopup = false;
        if (Number.isInteger(image.videoPreviewTimeout)) {
            clearTimeout(image.videoPreviewTimeout);
            image.videoPreviewTimeout = null;
        } else if (image.videoPreviewTimeout === true) {
            console.log("Mouse leave", image.postName);
            videoToImage(image);
        }
    }
    document.querySelectorAll(container_selector).forEach((preview) => {
        let image = preview.querySelector('img.preview');
        image.onmouseenter = onMouseEnter;
        image.onmouseleave = onMouseLeave;
        image.postName = preview.id;
        image.imageToVideo = imageToVideo;
        image.videoToImage = videoToImage;
        image.container = preview;
    });
};
