$(document).ready(function() {

    if ($('#flash-modal').length > 0) {
        var flashModal = new bootstrap.Modal(document.getElementById('flash-modal'), {});
        flashModal.show();
    }

    $('#flash-modal .btn-close').on('click', function () {
        flashModal.hide();
    });

    $('#home-button').on('click', function () {
        window.location.href = '/';
    });
});