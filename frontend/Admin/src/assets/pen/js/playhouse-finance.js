(function () {
  'use strict';
  var API = window.__PLAYHOUSE_FINANCE_API__ || '/api/playhouse/finance/report/';
  var period = 'daily';
  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : String(s == null ? '' : s); }
  function fmt(n) { n = Number(n) || 0; return window.persianNumbers(n.toLocaleString('en-US').replace(/,/g, '٬')); }
  function get(url) { return fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.json().then(function (b) { if (!r.ok) throw new Error(b.detail || 'خطا در دریافت گزارش'); return b; }); }); }
  function methodLabel(m) { return { pos: 'دستگاه پوز', card_transfer: 'کارت به کارت' }[m] || m || '—'; }
  function load() {
    var rows = document.getElementById('ph-fin-rows');
    rows.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">در حال بارگذاری…</td></tr>';
    get(API + '?period=' + encodeURIComponent(period)).then(function (data) {
      var s = data.summary || {};
      document.getElementById('ph-fin-invoices').textContent = fmt(s.invoices);
      document.getElementById('ph-fin-time').textContent = fmt(s.time_total);
      document.getElementById('ph-fin-cafe').textContent = fmt(s.items_total);
      document.getElementById('ph-fin-total').textContent = fmt(s.grand_total);
      document.getElementById('ph-fin-period').textContent = 'از ' + esc(data.period.from) + ' تا ' + esc(data.period.to);
      var invoices = data.invoices || [];
      rows.innerHTML = invoices.length ? invoices.map(function (i) {
        return '<tr><td class="fw-semibold" dir="ltr">' + esc(i.number) + '</td>' +
          '<td>' + esc(i.member) + '</td><td>' + esc(methodLabel(i.method)) + '</td>' +
          '<td dir="ltr">' + esc(i.tracking || '—') + '</td><td>' + fmt(i.time_amount) + '</td>' +
          '<td>' + fmt(i.cafe_total) + '</td><td class="fw-bold">' + fmt(i.total) + '</td>' +
          '<td dir="ltr">' + esc(i.paid_at ? new Date(i.paid_at).toLocaleString('fa-IR') : '—') + '</td></tr>';
      }).join('') : '<tr><td colspan="8" class="text-center text-muted py-4">برای این بازه پرداختی ثبت نشده است.</td></tr>';
    }).catch(function (err) {
      rows.innerHTML = '<tr><td colspan="8" class="text-center text-danger py-4">' + esc(err.message) + '</td></tr>';
    });
  }
  document.querySelectorAll('[data-period]').forEach(function (button) {
    button.addEventListener('click', function () {
      period = button.getAttribute('data-period');
      document.querySelectorAll('[data-period]').forEach(function (b) { b.classList.toggle('active', b === button); });
      load();
    });
  });
  document.getElementById('ph-fin-refresh').addEventListener('click', load);
  load();
})();
