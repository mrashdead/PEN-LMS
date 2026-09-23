/*
 * Pen LMS — playhouse settings page (تنظیمات خانه بازی).
 *
 * Loads the singleton config on boot and PUTs changes via the playhouse API.
 * Only finance/manager roles reach the page; the API re-checks authorisation.
 */
(function () {
  'use strict';

  var API = window.__PLAYHOUSE_API__ || '/api/playhouse/';
  var $price = document.getElementById('ph-set-price');
  var $open = document.getElementById('ph-set-open');
  var $openTime = document.getElementById('ph-set-open-time');
  var $closeTime = document.getElementById('ph-set-close-time');
  var $error = document.getElementById('ph-set-error');
  var $submit = document.getElementById('ph-set-submit');
  var $reset = document.getElementById('ph-set-reset');
  var $form = document.getElementById('ph-settings-form');

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function fmt(n) { n = Number(n) || 0; return window.persianNumbers(n.toLocaleString('en-US').replace(/,/g, '٬')); }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }

  function load() {
    fetch(API + 'config/', { credentials: 'same-origin', headers: headers() })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { if (!r.ok) throw new Error(b.detail || ('HTTP ' + r.status)); return b; }); })
      .then(function (d) {
        if ($price) $price.value = d.price_per_15_minutes || 0;
        if ($open) $open.checked = d.is_open_now !== false;
        if ($openTime) $openTime.value = (d.open_time || '').slice(0, 5);
        if ($closeTime) $closeTime.value = (d.close_time || '').slice(0, 5);
      })
      .catch(function (err) {
        if ($error) { $error.hidden = false; $error.textContent = 'بارگذاری تنظیمات ناموفق: ' + esc(err.message); }
      });
  }

  function save(e) {
    e.preventDefault();
    if (!$price || !$price.value || Number($price.value) < 0) {
      if ($error) { $error.hidden = false; $error.textContent = 'قیمت هر ۱۵ دقیقه را وارد کنید.'; }
      return;
    }
    var payload = {
      price_per_15_minutes: Number($price.value),
      is_open_now: !!($open && $open.checked),
      open_time: $openTime && $openTime.value ? $openTime.value + ':00' : null,
      close_time: $closeTime && $closeTime.value ? $closeTime.value + ':00' : null,
    };
    $submit.disabled = true;
    if ($error) $error.hidden = true;
    fetch(API + 'config/', {
      method: 'PUT',
      credentials: 'same-origin',
      headers: headers(),
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { if (!r.ok) throw new Error(b.detail || ('HTTP ' + r.status)); return b; }); })
      .then(function () {
        toast('تنظیمات ذخیره شد.', 'success');
        // the dashboard price badge is stale until reload
        setTimeout(function () { window.location.reload(); }, 600);
      })
      .catch(function (err) {
        if ($error) { $error.hidden = false; $error.textContent = esc(err.message); }
      })
      .finally(function () { $submit.disabled = false; });
  }

  if ($form) $form.addEventListener('submit', save);
  if ($reset) $reset.addEventListener('click', function () { window.location.reload(); });
  document.addEventListener('DOMContentLoaded', load);
})();
