new Konami(function() {
    var cflags = document.cookie.replace(/(?:(?:^|.*;\s*)cflags\s*\=\s*([^;]*).*$)|^.*$/, "$1");
    cflags = (+cflags) ^ 1;
    document.cookie = "cflags=" + cflags + ";path=/;max-age=31536000";
    window.location.reload();
});