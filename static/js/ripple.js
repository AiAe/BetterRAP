$(document).ready(function() {
    $(document).keydown(function(e) {
        var activeElement = $(document.activeElement);
        var isInput = activeElement.is(":input,[contenteditable]");
        if ((e.which === 83 || e.which === 115) && !isInput) {
            $("#user-search-input").focus();
            e.preventDefault();
        }
        if (e.which === 27 && isInput) {
            activeElement.blur();
        }
    });
    new Konami(function() {
        var cflags = document.cookie.replace(/(?:(?:^|.*;\s*)cflags\s*\=\s*([^;]*).*$)|^.*$/, "$1");
        cflags = (+cflags) ^ 1;
        document.cookie = "cflags=" + cflags + ";path=/;max-age=31536000";
        window.location.reload();
    });
    $("#language-selector .item").click(function() {
        var lang = $(this).data("lang");
        document.cookie = "language=" + lang + ";path=/;max-age=31536000";
        window.location.reload();
    });
});