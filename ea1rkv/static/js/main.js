/**
 * EA1RKV - Vigo Val Miñor Radioclub - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    initSmoothScroll();
    initLibraryFilterPosition();
    initFormValidation();
});

/**
 * Enable smooth scrolling for anchor links.
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (event) {
            var targetId = this.getAttribute('href');
            if (targetId === '#') return;

            var target = document.querySelector(targetId);
            if (target) {
                event.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/**
 * Bootstrap form validation.
 */
function initFormValidation() {
    var forms = document.querySelectorAll('.needs-validation');

    forms.forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}


/** Keep the media library in view when a server-side filter reloads the page. */
function initLibraryFilterPosition() {
    var key = 'ea1rkv-library-scroll';
    var library = document.getElementById('biblioteca');
    var controls = document.querySelectorAll('.library-filters, .library-tabs a');
    if (!library || !controls.length) return;

    controls.forEach(function (control) {
        control.addEventListener('submit', function () {
            sessionStorage.setItem(key, String(library.getBoundingClientRect().top + window.scrollY));
        });
        control.addEventListener('click', function () {
            sessionStorage.setItem(key, String(library.getBoundingClientRect().top + window.scrollY));
        });
    });

    var saved = sessionStorage.getItem(key);
    if (saved !== null) {
        sessionStorage.removeItem(key);
        var position = Number(saved);
        if (Number.isFinite(position)) {
            var restore = function () {
                window.scrollTo({ top: position, left: 0, behavior: 'auto' });
            };
            // pageshow runs after the browser's own history/fragment restoration.
            window.addEventListener('pageshow', function () { setTimeout(restore, 0); }, { once: true });
            setTimeout(restore, 0);
        }
    }
}
