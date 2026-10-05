(function () {
  'use strict';
  var api = window.__PLAYHOUSE_API__ || '/api/playhouse/';
  var dateInput = document.getElementById('ph-attendance-date');
  var rows = document.getElementById('ph-attendance-rows');
  var summary = document.getElementById('ph-attendance-summary');
  var esc = window.htmlEscape || function (v) { return String(v || '').replace(/[&<>"']/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]; }); };
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function fa(value) { return window.persianNumbers ? window.persianNumbers(value) : value; }
  function money(value) { return fa(Number(value || 0).toLocaleString('en-US').replace(/,/g, '٬')) + ' تومان'; }
  function jalali(iso) { return window.penISOToJalali ? window.penISOToJalali(iso) : (iso || '—'); }
  function jalaliDateTime(value) {
    if (!value) return '—';
    var d = new Date(value);
    if (isNaN(d.getTime())) return '—';
    var iso = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    return jalali(iso) + ' ' + clock(value);
  }
  function selectedISO() { return window.penJalaliToISO ? window.penJalaliToISO(dateInput.value) : dateInput.value; }
  function localTimestamp(dateValue, timeValue) {
    var isoDate = window.penJalaliToISO ? window.penJalaliToISO(dateValue) : dateValue;
    if (!isoDate || !timeValue) return null;
    var parsed = new Date(isoDate + 'T' + timeValue);
    return isNaN(parsed.getTime()) ? null : parsed.toISOString();
  }
  function clock(value) { return value ? new Date(value).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' }) : '—'; }
  function statusText(s) { return { waiting: 'در انتظار شروع', active: 'داخل خانه بازی', paused: 'متوقف', finished: 'پایان یافته', cancelled: 'لغو شده' }[s] || s; }
  function invoiceMarkup(inv) {
    if (!inv) return '<span class="text-muted">فاکتور صادر نشده</span>';
    var method = { pos: 'دستگاه پوز', card_transfer: 'کارت به کارت' }[inv.payment_method] || '—';
    var items = (inv.items || []).map(function (item) {
      return '<li class="d-flex justify-content-between gap-2"><span>' + esc(item.name) + '</span><span>' + money(item.price) + '</span></li>';
    }).join('');
    return '<div><span class="badge ' + (inv.is_paid ? 'text-bg-success' : 'text-bg-warning') + '">' + (inv.is_paid ? 'پرداخت شده' : 'پرداخت نشده') + '</span>' +
      '<strong class="d-block mt-1">' + money(inv.total_amount) + '</strong>' +
      '<details class="mt-1"><summary class="small">فاکتور ' + esc(inv.invoice_number) + '</summary><div class="small mt-2">' +
      '<div class="d-flex justify-content-between"><span>هزینه زمان</span><span>' + money(inv.time_amount) + '</span></div>' +
      (items ? '<ul class="list-unstyled border-top border-bottom py-1 my-1">' + items + '</ul>' : '') +
      '<div class="d-flex justify-content-between"><span>جمع کافه</span><span>' + money(inv.cafe_total) + '</span></div>' +
      '<div class="d-flex justify-content-between fw-bold"><span>جمع کل</span><span>' + money(inv.total_amount) + '</span></div>' +
      '<div class="mt-1">روش پرداخت: ' + esc(method) + '</div>' +
      (inv.tracking_code ? '<div>کد رهگیری: <span dir="ltr">' + esc(inv.tracking_code) + '</span></div>' : '') +
      (inv.paid_at ? '<div>زمان پرداخت: ' + jalaliDateTime(inv.paid_at) + '</div>' : '') +
      '</div></details></div>';
  }
  function load() {
    var day = selectedISO();
    if (!day) { window.penToast && window.penToast('تاریخ شمسی را به شکل سال/ماه/روز وارد کنید.', 'danger'); return; }
    rows.innerHTML = '<tr><td colspan="8" class="text-center py-4">در حال بارگذاری…</td></tr>';
    fetch(api + 'attendance/?date=' + encodeURIComponent(day), { credentials: 'same-origin', headers: headers() })
      .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.detail || 'دریافت سوابق ناموفق بود.'); return d.results || d; }); })
      .then(function (items) {
        summary.textContent = fa(items.length) + ' ثبت در این روز';
        if (!items.length) { rows.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-5">برای این روز سابقه‌ای ثبت نشده است.</td></tr>'; return; }
        rows.innerHTML = items.map(function (s) {
          var details = (s.age ? fa(s.age) + ' سال' : 'سن نامشخص') + (s.member_notes ? ' · ' + esc(s.member_notes) : '');
          var guardian = (s.guardian_name ? esc(s.guardian_name) + '<br>' : '') + (s.guardian_mobile ? '<span dir="ltr">' + esc(s.guardian_mobile) + '</span>' : '—');
          var correction = '';
          if (s.status === 'waiting') correction = '<div class="d-flex flex-wrap gap-1"><input class="form-control form-control-sm" type="text" data-entry-date data-jalali dir="ltr" placeholder="تاریخ ورود"><input class="form-control form-control-sm" type="time" data-entry-time aria-label="ساعت واقعی ورود"><button class="btn btn-sm btn-outline-primary" data-fix="start">ثبت زمان ورود</button></div>';
          else if (s.status === 'active') correction = '<div class="d-flex flex-wrap gap-1"><input class="form-control form-control-sm" type="text" data-exit-date data-jalali dir="ltr" placeholder="تاریخ خروج"><input class="form-control form-control-sm" type="time" data-exit-time aria-label="ساعت واقعی خروج"><button class="btn btn-sm btn-outline-danger" data-fix="end">ثبت خروج</button></div>';
          else if (s.status === 'paused') correction = '<button class="btn btn-sm btn-outline-danger" data-fix="end">پایان در همین لحظه</button>';
          return '<tr data-id="' + esc(s.id) + '" data-session-date="' + esc(s.session_date || '') + '"><td>ورود: ' + jalaliDateTime(s.entry_at) + '<br>خروج: ' + jalaliDateTime(s.exit_at) + '</td>' +
            '<td><strong>' + esc(s.member_name) + '</strong><small class="d-block text-muted">' + details + '</small></td><td>' + guardian + '</td><td>' + esc(s.operator_name || '—') + '<small class="d-block text-muted">ثبت: ' + jalaliDateTime(s.created_at) + '</small></td>' +
            '<td>' + (s.status === 'finished' ? esc(s.billable_label || '—') : esc(s.elapsed_label || s.duration_label || '—')) + '</td><td><span class="badge text-bg-light">' + esc(statusText(s.status)) + '</span></td><td>' + invoiceMarkup(s.invoice_detail) + '</td><td>' + (correction || '—') + '</td></tr>';
        }).join('');
      }).catch(function (e) { rows.innerHTML = '<tr><td colspan="8" class="text-center text-danger py-4">' + esc(e.message) + '</td></tr>'; });
  }
  function act(button) {
    var tr = button.closest('tr'), action = button.getAttribute('data-fix'), body = {};
    if (action === 'start') {
      var entry = localTimestamp(tr.querySelector('[data-entry-date]').value, tr.querySelector('[data-entry-time]').value);
      if (!entry) { window.penToast && window.penToast('تاریخ شمسی و ساعت واقعی ورود را وارد کنید.', 'danger'); return; }
      body.entry_at = entry;
    }
    if (action === 'end') {
      var exit = tr.querySelector('[data-exit-time]');
      if (exit && exit.value) {
        var exitAt = localTimestamp(tr.querySelector('[data-exit-date]').value, exit.value);
        if (!exitAt) { window.penToast && window.penToast('تاریخ شمسی و ساعت واقعی خروج را وارد کنید.', 'danger'); return; }
        body.exit_at = exitAt;
      }
    }
    button.disabled = true;
    fetch(api + 'sessions/' + tr.getAttribute('data-id') + '/' + action + '/', { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.detail || 'ثبت اصلاح انجام نشد.'); return d; }); })
      .then(function () { window.penToast && window.penToast('سوابق حضور به‌روزرسانی شد.', 'success'); load(); })
      .catch(function (e) { window.penToast && window.penToast(e.message, 'danger'); button.disabled = false; });
  }
  document.getElementById('ph-attendance-load').addEventListener('click', load);
  dateInput.addEventListener('change', load);
  rows.addEventListener('click', function (e) { var b = e.target.closest('[data-fix]'); if (b) act(b); });
  rows.addEventListener('focusin', function (e) {
    var tr = e.target.closest('tr[data-session-date]');
    if (!tr) return;
    var entryDate = tr.querySelector('[data-entry-date]');
    var exitDate = tr.querySelector('[data-exit-date]');
    if (entryDate && !entryDate.value) entryDate.value = jalali(tr.getAttribute('data-session-date'));
    if (exitDate && !exitDate.value) exitDate.value = jalali(dateInput.value ? selectedISO() : tr.getAttribute('data-session-date'));
    if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  });
  load();
})();
