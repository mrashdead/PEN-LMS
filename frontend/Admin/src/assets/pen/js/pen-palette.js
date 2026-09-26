(function () {
  'use strict';
  var root = document.documentElement;
  var allowed = ['balanced', 'sky', 'rose'];
  function updateChoices() {
    document.querySelectorAll('[data-palette-choice]').forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.dataset.paletteChoice === root.dataset.penPalette));
    });
  }
  document.addEventListener('DOMContentLoaded', function () {
    updateChoices();
    document.querySelectorAll('[data-palette-choice]').forEach(function (button) {
      button.addEventListener('click', function () {
        var value = button.dataset.paletteChoice;
        if (!allowed.includes(value)) return;
        root.dataset.penPalette = value;
        try { sessionStorage.setItem('pen-palette', value); } catch (e) { /* storage unavailable */ }
        updateChoices();
      });
    });
  });
})();
