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

function redirectIRS() {
    // Get the current search query from the URL
    const searchParams = new URLSearchParams(window.location.search);
    const searchQuery = searchParams.get('search');

    // Construct the new URL
    const newUrl = `http://127.0.0.1:5000/result/irs?search=${encodeURIComponent(searchQuery)}`;

    // Redirect to the new URL
    window.location.href = newUrl;
}

function redirectSQL() {
    // Get the current search query from the URL
    const searchParams = new URLSearchParams(window.location.search);
    const searchQuery = searchParams.get('search');

    // Construct the new URL
    const newUrl = `http://127.0.0.1:5000/result/sql?search=${encodeURIComponent(searchQuery)}`;

    // Redirect to the new URL
    window.location.href = newUrl;
}

document.getElementById('articleYearInput').max = new Date().getFullYear();