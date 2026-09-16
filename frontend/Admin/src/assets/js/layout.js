// Run as early as possible in <head> to prevent flicker
(function () {
    'use strict';

    // Avoid deferring critical variables
    const docEl = document.documentElement;

    // List of attributes to manage
    const settings = [
        "data-layout",
        "data-nav-type",
        "data-bs-theme",
        "data-sidebar",
        "data-sidebar-colors",
        "data-content-width",
        "data-profile-sidebar",
        "data-topbar-colors",
        "data-colors"
    ];

    // Fast function to apply stored settings without reflow-heavy logic
    function applyStoredValuesFast() {
        const isProfileSidebar = sessionStorage.getItem('data-profile-sidebar') === 'true';
        if (isProfileSidebar) {
            docEl.setAttribute('data-profile-sidebar', 'true');
        } else {
            docEl.removeAttribute('data-profile-sidebar');
        }

        settings.forEach(setting => {
            const savedValue = sessionStorage.getItem(setting) || docEl.getAttribute(setting);
            if (savedValue !== null) {
                docEl.setAttribute(setting, savedValue);
                // Only store back if missing in session (cache warming)
                if (!sessionStorage.getItem(setting)) {
                    sessionStorage.setItem(setting, savedValue);
                }
            }
        });
    }

    // Apply fast settings immediately
    applyStoredValuesFast();

    // Defer less critical tasks (like updating UI checkboxes/radio buttons)
    window.addEventListener('load', function () {
        settings.forEach(setting => {
            const savedValue = sessionStorage.getItem(setting);
            if (savedValue) {
                const radio = document.querySelector(`input[name="${setting}"][value="${savedValue}"]`);
                if (radio) radio.checked = true;
            }
        });
    });
})();