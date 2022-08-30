// APP/STATIC/JAVASCRIPT/UPLOADS.JS

const Uploads = {};

Uploads.initializeReloadInterval = function (upload_status) {
    if (upload_status !== "pending" && upload_status !== "processing") return;
    const page_timer = setInterval(() => {
        if (document.hidden) return;
        window.location.reload();
        clearInterval(page_timer);
    }, 5000);
};
