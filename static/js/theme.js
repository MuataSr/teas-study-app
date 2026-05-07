(function () {
    var STORAGE_KEY = 'teas-theme';
    var html = document.documentElement;

    function getPreferredTheme() {
        var stored = localStorage.getItem(STORAGE_KEY);
        if (stored === 'dark' || stored === 'light') {
            return stored;
        }
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    function applyTheme(theme) {
        html.setAttribute('data-theme', theme);
        var btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.textContent = theme === 'dark' ? 'Light' : 'Dark';
        }
    }

    var theme = getPreferredTheme();
    applyTheme(theme);

    document.addEventListener('DOMContentLoaded', function () {
        applyTheme(getPreferredTheme());

        var btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.addEventListener('click', function () {
                var current = html.getAttribute('data-theme') || 'light';
                var next = current === 'dark' ? 'light' : 'dark';
                localStorage.setItem(STORAGE_KEY, next);
                applyTheme(next);
            });
        }
    });
})();
