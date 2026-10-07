(function () {
  'use strict';
  var API = window.__PLAYHOUSE_FINANCE_API__ || '/api/playhouse/finance/report/';
  var TODAY = window.__PLAYHOUSE_FINANCE_TODAY__ || '';
  var fromInput = document.getElementById('ph-fin-from');
  var toInput = document.getElementById('ph-fin-to');
  var rows = document.getElementById('ph-fin-rows');
  var cafeRows = document.getElementById('ph-fin-cafe-rows');
  var errorBox = document.getElementById('ph-fin-error');
  var detailBody = document.getElementById('ph-fin-invoice-detail');
  var invoiceModal = document.getElementById('ph-fin-invoice-modal');
  var currentInvoices = [];

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : String(s == null ? '' : s); }
  function fmt(n) { n = Number(n) || 0; return window.persianNumbers(n.toLocaleString('en-US').replace(/,/g, '٬')); }
  function toISO(jalali) { return window.penJalaliToISO ? window.penJalaliToISO(jalali || '') : null; }
  function toJalali(iso) { return window.penISOToJalali ? window.penISOToJalali(iso || '') : (iso || '—'); }
  function shiftISO(iso, days) {
    var parts = (iso || '').split('-').map(Number);
    var date = new Date(parts[0], parts[1] - 1, parts[2], 12);
    date.setDate(date.getDate() + days);
    return date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0') + '-' + String(date.getDate()).padStart(2, '0');
  }
  function jalaliMonthStart(iso) {
    var parts = toJalali(iso).split('/').map(Number);
    return toISO(parts[0] + '/' + String(parts[1]).padStart(2, '0') + '/01');
  }
  function previousJalaliMonthStart(iso) {
    var parts = toJalali(iso).split('/').map(Number);
    var year = parts[0], month = parts[1] - 1;
    if (month < 1) { month = 12; year -= 1; }
    return toISO(year + '/' + String(month).padStart(2, '0') + '/01');
  }
  function displayRange(from, to) {
    document.getElementById('ph-fin-period').textContent = 'از ' + toJalali(from) + ' تا ' + toJalali(to);
  }
  function paidAt(value) {
    if (!value) return '—';
    var d = new Date(value);
    if (isNaN(d.getTime())) return '—';
    var day = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    return toJalali(day) + ' ' + d.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
  }
  function get(url) {
    return fetch(url, { credentials: 'same-origin' }).then(function (r) {
      return r.json().then(function (body) {
        if (!r.ok) throw new Error(body.detail || 'خطا در دریافت گزارش');
        return body;
      });
    });
  }
  function methodLabel(method) { return { pos: 'دستگاه پوز', card_transfer: 'کارت به کارت' }[method] || method || '—'; }
  function renderInvoiceDetail(invoice) {
    var items = invoice.items || [];
    var itemList = items.length ? items.map(function (item) {
      return '<li class="d-flex justify-content-between gap-3 py-1"><span>' + esc(item.name) + '</span><span class="text-nowrap">' + fmt(item.price) + ' تومان</span></li>';
    }).join('') : '<li class="text-muted py-1">برای این فاکتور آیتم کافه ثبت نشده است.</li>';
    detailBody.innerHTML =
      '<div class="row g-2 mb-3"><div class="col-6"><div class="text-muted small">نام کودک</div><strong>' + esc(invoice.member) + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">سن</div><strong>' + (invoice.member_age == null ? '—' : fmt(invoice.member_age) + ' سال') + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">نام والد</div><strong>' + esc(invoice.guardian_name || '—') + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">شماره تماس</div><strong dir="ltr">' + esc(invoice.guardian_mobile || '—') + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">شماره فاکتور</div><strong dir="ltr">' + esc(invoice.number) + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">روش پرداخت</div><strong>' + esc(methodLabel(invoice.method)) + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">تاریخ پرداخت</div><strong>' + esc(paidAt(invoice.paid_at)) + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">ثبت‌کننده</div><strong>' + esc(invoice.operator || '—') + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">ورود</div><strong>' + esc(paidAt(invoice.entry_at)) + '</strong></div>' +
      '<div class="col-6"><div class="text-muted small">خروج</div><strong>' + esc(paidAt(invoice.exit_at)) + '</strong></div>' +
      '<div class="col-12"><div class="text-muted small">کد رهگیری</div><strong dir="ltr">' + esc(invoice.tracking || '—') + '</strong></div></div>' +
      '<div class="border-top pt-3"><div class="fw-semibold mb-2">آیتم‌های سفارش‌داده‌شده</div><ul class="list-unstyled mb-0">' + itemList + '</ul></div>' +
      '<div class="border-top mt-3 pt-3 small"><div class="d-flex justify-content-between"><span>هزینه زمان بازی</span><span>' + fmt(invoice.time_amount) + ' تومان</span></div>' +
      '<div class="d-flex justify-content-between mt-1"><span>جمع کافه</span><span>' + fmt(invoice.cafe_total) + ' تومان</span></div>' +
      '<div class="d-flex justify-content-between fw-bold mt-2"><span>جمع کل</span><span>' + fmt(invoice.total) + ' تومان</span></div></div>';
  }
  function load(from, to) {
    errorBox.hidden = true;
    rows.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">در حال بارگذاری…</td></tr>';
    cafeRows.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-4">در حال بارگذاری…</td></tr>';
    displayRange(from, to);
    get(API + '?from=' + encodeURIComponent(from) + '&to=' + encodeURIComponent(to)).then(function (data) {
      var summary = data.summary || {};
      document.getElementById('ph-fin-invoices').textContent = fmt(summary.invoices);
      document.getElementById('ph-fin-time').textContent = fmt(summary.time_total);
      document.getElementById('ph-fin-cafe').textContent = fmt(summary.items_total);
      document.getElementById('ph-fin-total').textContent = fmt(summary.grand_total);
      var cafeSales = data.cafe_item_sales || [];
      cafeRows.innerHTML = cafeSales.length ? cafeSales.map(function (item) {
        return '<tr><td class="fw-semibold">' + esc(item.name) + '</td><td class="ph-fin-number">' + fmt(item.quantity) + '</td>' +
          '<td class="ph-fin-number">' + fmt(item.total) + '</td></tr>';
      }).join('') : '<tr><td colspan="3" class="text-center text-muted py-4">برای این بازه فروش آیتم کافه ثبت نشده است.</td></tr>';
      var invoices = data.invoices || [];
      currentInvoices = invoices;
      rows.innerHTML = invoices.length ? invoices.map(function (invoice) {
        return '<tr><td class="fw-semibold" dir="ltr">' + esc(invoice.number) + '</td>' +
          '<td>' + esc(invoice.member) + '</td><td>' + esc(methodLabel(invoice.method)) + '</td>' +
          '<td dir="ltr">' + esc(invoice.tracking || '—') + '</td><td class="ph-fin-number">' + fmt(invoice.time_amount) + '</td>' +
          '<td class="ph-fin-number">' + fmt(invoice.cafe_total) + '</td><td class="fw-bold ph-fin-number">' + fmt(invoice.total) + '</td>' +
          '<td>' + esc(paidAt(invoice.paid_at)) + '</td><td><button type="button" class="btn btn-sm btn-outline-primary ph-fin-details" data-invoice-id="' + esc(invoice.id) + '">اطلاعات بیشتر</button></td></tr>';
      }).join('') : '<tr><td colspan="9" class="text-center text-muted py-4">برای این بازه پرداختی ثبت نشده است.</td></tr>';
    }).catch(function (err) {
      rows.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">گزارش بارگذاری نشد.</td></tr>';
      cafeRows.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-4">گزارش بارگذاری نشد.</td></tr>';
      errorBox.textContent = err.message;
      errorBox.hidden = false;
    });
  }
  function applyRange() {
    var from = toISO(fromInput.value.trim());
    var to = toISO(toInput.value.trim());
    if (!from || !to) { errorBox.textContent = 'هر دو تاریخ را با تقویم شمسی وارد کنید.'; errorBox.hidden = false; return; }
    if (from > to) { errorBox.textContent = 'تاریخ شروع بازه نمی‌تواند بعد از تاریخ پایان باشد.'; errorBox.hidden = false; return; }
    document.querySelectorAll('[data-preset]').forEach(function (button) { button.classList.remove('active'); });
    load(from, to);
  }
  function presetRange(preset) {
    var from = TODAY, to = TODAY;
    if (preset === 'week') from = shiftISO(TODAY, -6);
    if (preset === 'month') from = jalaliMonthStart(TODAY);
    if (preset === 'previous-month') {
      to = shiftISO(jalaliMonthStart(TODAY), -1);
      from = previousJalaliMonthStart(TODAY);
    }
    fromInput.value = toJalali(from);
    toInput.value = toJalali(to);
    document.querySelectorAll('[data-preset]').forEach(function (button) {
      button.classList.toggle('active', button.getAttribute('data-preset') === preset);
    });
    load(from, to);
  }

  document.querySelectorAll('[data-preset]').forEach(function (button) {
    button.addEventListener('click', function () { presetRange(button.getAttribute('data-preset')); });
  });
  document.getElementById('ph-fin-apply').addEventListener('click', applyRange);
  rows.addEventListener('click', function (event) {
    var button = event.target.closest('.ph-fin-details');
    if (!button) return;
    var invoice = currentInvoices.filter(function (item) { return item.id === button.getAttribute('data-invoice-id'); })[0];
    if (!invoice) return;
    renderInvoiceDetail(invoice);
    if (window.bootstrap && invoiceModal) window.bootstrap.Modal.getOrCreateInstance(invoiceModal).show();
  });
  [fromInput, toInput].forEach(function (input) {
    input.addEventListener('keydown', function (event) { if (event.key === 'Enter') { event.preventDefault(); applyRange(); } });
  });
  if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  presetRange('today');
})();
