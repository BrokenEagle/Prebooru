// APP/STATIC/JAVASCRIPT/DOWNLOADS.JS

const Downloads = {};

Downloads.initializeReloadInterval = function (download_status) {
    if (download_status !== "pending" && download_status !== "processing") return;
    const page_timer = setInterval(() => {
        if (document.hidden) {
            document.onvisibilitychange = function () {
                window.location.reload();
            };
        } else {
            window.location.reload();
        }
        clearInterval(page_timer);
    }, 5000);
};
