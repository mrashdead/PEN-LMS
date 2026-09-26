/* Display Django admin date widgets in Jalali; submit ISO values to Django. */
(function () {
  'use strict';

  function prepare() {
    document.querySelectorAll('input.vDateField, input[type="date"]').forEach(function (input) {
      if (input.dataset.adminJalali) return;
      var value = input.value.trim();
      if (input.type === 'date') input.type = 'text';
      input.dataset.adminJalali = '1';
      input.setAttribute('data-jalali', '');
      input.setAttribute('autocomplete', 'off');
      input.setAttribute('dir', 'ltr');
      if (!input.placeholder) input.placeholder = 'سال/ماه/روز';
      if (/^\d{4}[-/]\d{1,2}[-/]\d{1,2}$/.test(value) && +value.slice(0, 4) >= 1700) {
        input.value = window.penISOToJalali(value) || value;
      }
    });
    window.penAttachJalaliPickers();
  }

  document.addEventListener('DOMContentLoaded', function () {
    prepare();
    var pending = false;
    new MutationObserver(function () {
      if (pending) return;
      pending = true;
      queueMicrotask(function () { pending = false; prepare(); });
    }).observe(document.body, { childList: true, subtree: true });

    document.addEventListener('input', function (event) {
      if (event.target.matches('input[data-admin-jalali]')) event.target.setCustomValidity('');
    });
    document.addEventListener('submit', function (event) {
      var fields = event.target.querySelectorAll('input[data-admin-jalali]');
      for (var i = 0; i < fields.length; i += 1) {
        var input = fields[i];
        var raw = input.value.trim();
        if (!raw) continue;
        if (/^\d{4}-\d{2}-\d{2}$/.test(raw) && +raw.slice(0, 4) >= 1700) continue;
        var iso = window.penJalaliToISO(raw);
        if (!iso) {
          event.preventDefault();
          input.setCustomValidity('تاریخ شمسی معتبر وارد کنید.');
          input.reportValidity();
          return;
        }
        input.value = iso;
      }
    }, true);
  });
})();
