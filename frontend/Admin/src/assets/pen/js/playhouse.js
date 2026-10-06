/*
 * Pen LMS — playhouse (خانه بازی) operator dashboard.
 *
 * Drives: intake form, existing-member autocomplete, per-session live timers
 * (client-side tick from the entry timestamp; the server is authoritative for
 * state), start/stop/end/cancel transitions, and the invoice modal (cafe
 * items + totals + payment hand-off).
 */
(function () {
  'use strict';

  var API = window.__PLAYHOUSE_API__ || '/api/playhouse/';
  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }

  function post(url, body) {
    return fetch(url, { method: 'POST', credentials: 'same-origin', headers: headers(), body: body ? JSON.stringify(body) : undefined })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { if (!r.ok) throw new Error(apiError(b) || ('HTTP ' + r.status)); return b; }); });
  }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', headers: headers() })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { if (!r.ok) throw new Error(apiError(b) || ('HTTP ' + r.status)); return b; }); });
  }
  function apiError(body) {
    if (!body) return '';
    if (typeof body === 'string') return body;
    if (body.detail) return String(body.detail);
    if (body.error) return String(body.error);
    var values = [];
    Object.keys(body).forEach(function (key) {
      var value = body[key];
      if (Array.isArray(value)) values = values.concat(value.map(String));
      else if (value) values.push(String(value));
    });
    return values.join('؛ ');
  }
  function fmt(n) { n = Number(n) || 0; return window.persianNumbers(n.toLocaleString('en-US').replace(/,/g, '٬')); }
  function fmtDuration(totalSeconds) {
    totalSeconds = Math.max(0, Math.floor(Number(totalSeconds) || 0));
    var h = Math.floor(totalSeconds / 3600);
    var m = Math.floor((totalSeconds % 3600) / 60);
    var s = totalSeconds % 60;
    return window.persianNumbers(String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0'));
  }
  function fmtTime(totalMinutes) {
    return fmtDuration((Number(totalMinutes) || 0) * 60);
  }
  function fmtClock(value) {
    if (!value) return '—';
    var d = new Date(value);
    return isNaN(d.getTime()) ? '—' : d.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
  }
  function jalaliDate(value) {
    return value && window.penISOToJalali ? window.penISOToJalali(value) : (value || '—');
  }
  function jalaliDateTime(value) {
    if (!value) return '—';
    var d = new Date(value);
    if (isNaN(d.getTime())) return '—';
    var day = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    return jalaliDate(day) + ' ' + fmtClock(value);
  }
  function localTimestamp(dateValue, timeValue) {
    var day = window.penJalaliToISO ? window.penJalaliToISO(dateValue) : dateValue;
    if (!day || !timeValue) return null;
    var parsed = new Date(day + 'T' + timeValue);
    return isNaN(parsed.getTime()) ? null : parsed.toISOString();
  }
  function renderTimes(tr) {
    var cell = tr.querySelector('[data-role="times"]');
    if (!cell) return;
    var entry = tr.getAttribute('data-entry') || '';
    var exit = tr.getAttribute('data-exit') || '';
    cell.innerHTML = '<div>ورود: ' + jalaliDateTime(entry) + '</div><div class="text-muted">خروج: ' + jalaliDateTime(exit) + '</div>';
  }
  function syncJalaliDate() {
    var display = document.getElementById('ph-date-display');
    var hidden = document.getElementById('ph-date');
    if (!display || !hidden) return true;
    var iso = window.penJalaliToISO ? window.penJalaliToISO(display.value) : null;
    if (!iso) {
      display.classList.add('is-invalid');
      toast('تاریخ شمسی را به شکل ۱۴۰۵/۰۶/۳۰ وارد کنید.', 'danger');
      return false;
    }
    display.classList.remove('is-invalid');
    hidden.value = iso;
    return true;
  }

  // ── shared elements ─────────────────────────────────────────────────
  var $table = document.getElementById('ph-session-table');
  var $intake = document.getElementById('ph-intake-form');
  var $priceBadge = document.getElementById('ph-price-value');
  var $priceForm = document.getElementById('ph-price-form');

  // ── live timers (tick client-side every second) ─────────────────────
  var tickTimer = null;
  function timerMinutesForRow(tr, now) {
    var entry = tr.getAttribute('data-entry');
    if (!entry) return 0;
    var pausedAt = tr.getAttribute('data-paused-at');
    var pausedSeconds = Number(tr.getAttribute('data-paused-seconds')) || 0;
    var end = pausedAt ? new Date(pausedAt).getTime() : now;
    return Math.max(0, Math.floor((end - new Date(entry).getTime()) / 1000 - pausedSeconds));
  }
  function tickAll() {
    if (!$table) return;
    var now = Date.now();
    $table.querySelectorAll('tr[data-id][data-status="active"], tr[data-id][data-status="paused"]').forEach(function (tr) {
      var seconds = timerMinutesForRow(tr, now);
      var cell = tr.querySelector('[data-role="timer"]');
      if (cell) cell.textContent = fmtDuration(seconds);
    });
  }
  function startClock() { if (!tickTimer) { tickAll(); tickTimer = setInterval(tickAll, 1000); } }

  // render a session row from API data
  function renderRow(s) {
    if (!$table) return;
    var tbody = $table.querySelector('tbody');
    tbody.querySelectorAll('.ph-empty').forEach(function (e) { e.remove(); });
    var tr = document.createElement('tr');
    tr.setAttribute('data-id', s.id);
    tr.setAttribute('data-status', s.status);
    tr.setAttribute('data-entry', s.entry_at || '');
    tr.setAttribute('data-paused-at', s.paused_at || '');
    tr.setAttribute('data-paused-seconds', s.paused_seconds || 0);
    tr.setAttribute('data-billable', s.billable_minutes || 0);
    tr.setAttribute('data-session-date', s.session_date || '');
    tr.setAttribute('data-exit', s.exit_at || '');
    tr.innerHTML =
      '<td class="small" data-role="times"></td>' +
      '<td><div class="ph-child-name">' + esc(s.member_name) + '</div><div class="ph-child-age">' + (s.age != null ? esc(s.age) + ' ساله' : 'سن ثبت نشده') + '</div></td>' +
      '<td><div>' + esc(s.guardian_name || '—') + '</div><div dir="ltr" class="ph-phone-cell">' + esc(s.guardian_mobile || '—') + '</div><small class="text-muted">' + esc(s.member_notes || '') + '</small></td>' +
      '<td>' + esc(s.operator_name || '—') + '<small class="d-block text-muted">ثبت: ' + jalaliDateTime(s.created_at) + '</small></td>' +
      '<td class="fw-bold" data-role="timer">' + ((s.status === 'active' || s.status === 'paused') ? (s.elapsed_label || fmtDuration(s.elapsed_seconds)) : '—') + '</td>' +
      '<td data-role="status">' + statusMarkup(s) + '</td>' +
      '<td data-role="invoice">' + invoiceMarkup(s.invoice_detail) + '</td>' +
      '<td class="text-end"><div class="ph-row-actions" data-role="actions">' + actionsMarkup(s) + '</div></td>';
    tbody.prepend(tr);
    renderTimes(tr);
    icons();
  }
  function statusLabel(st) {
    return { waiting: 'در انتظار ورود', active: 'داخل خانه بازی', paused: 'متوقف شده', finished: 'پایان یافته', cancelled: 'لغو شده' }[st] || st;
  }
  function statusBadge(st) {
    return 'ph-status ph-status-' + st;
  }
  function invoiceStatusMarkup(isPaid) {
    return '<span class="ph-status ' + (isPaid ? 'ph-status-paid' : 'ph-status-invoiced') + '"><span></span>' + (isPaid ? 'پرداخت شده' : 'فاکتور صادر شد') + '</span>';
  }
  function statusMarkup(s) {
    return s.has_invoice ? invoiceStatusMarkup(!!s.invoice_is_paid) : '<span class="' + statusBadge(s.status) + '"><span></span>' + esc(statusLabel(s.status)) + '</span>';
  }
  function invoiceMarkup(inv) {
    if (!inv) return '<span class="text-muted">فاکتور صادر نشده</span>';
    var method = { pos: 'دستگاه پوز', card_transfer: 'کارت به کارت' }[inv.payment_method] || '—';
    var items = (inv.items || []).map(function (item) {
      return '<div class="small">' + esc(item.name) + ': ' + fmt(item.price) + ' تومان</div>';
    }).join('');
    return '<span class="ph-status ' + (inv.is_paid ? 'ph-status-paid' : 'ph-status-invoiced') + '"><span></span>' + (inv.is_paid ? 'پرداخت شده' : 'پرداخت نشده') + '</span>' +
      '<strong class="d-block">' + fmt(inv.total_amount) + ' تومان</strong><details><summary class="small">فاکتور ' + esc(inv.invoice_number) + '</summary>' +
      '<div class="small">مدت محاسبه‌شده: ' + fmtTime(inv.billed_minutes) + '</div><div class="small">هزینه زمان: ' + fmt(inv.time_amount) + ' تومان</div>' + items +
      '<div class="small">جمع کافه: ' + fmt(inv.cafe_total) + ' تومان</div><div class="small fw-bold">جمع کل: ' + fmt(inv.total_amount) + ' تومان</div>' +
      '<div class="small">روش پرداخت: ' + esc(method) + '</div>' +
      (inv.tracking_code ? '<div class="small">کد رهگیری: <span dir="ltr">' + esc(inv.tracking_code) + '</span></div>' : '') +
      (inv.paid_at ? '<div class="small">زمان پرداخت: ' + jalaliDateTime(inv.paid_at) + '</div>' : '') + '</details>';
  }
  function actionsMarkup(s) {
    if (!s.has_invoice) return actionButtons(s.status);
    return '<span class="ph-invoice-done" title="' + esc(s.invoice_number || '') + '">' + esc(s.invoice_number || 'ثبت شد') + '</span>';
  }
  function actionButtons(st) {
    if (st === 'waiting') {
      return '<button class="btn ph-row-btn ph-row-start" data-act="start" title="شروع تایمر"><i data-lucide="play" aria-hidden="true"></i></button>' +
        '<button class="btn ph-row-btn ph-row-cancel" data-act="cancel" title="لغو"><i data-lucide="x" aria-hidden="true"></i></button>' +
        '<details><summary class="small">ثبت زمان واقعی</summary><input class="form-control form-control-sm mt-1" type="text" data-entry-date data-jalali dir="ltr" placeholder="تاریخ شمسی ورود"><input class="form-control form-control-sm mt-1" type="time" data-entry-time aria-label="ساعت واقعی ورود"><button class="btn btn-sm btn-outline-primary mt-1" data-act="correct-start">ثبت زمان ورود</button></details>';
    }
    if (st === 'active') {
      return '<button class="btn ph-row-btn ph-row-pause" data-act="stop" title="توقف تایمر"><i data-lucide="pause" aria-hidden="true"></i></button>' +
        '<button class="btn ph-row-btn ph-row-end" data-act="end" title="پایان حضور"><i data-lucide="square" aria-hidden="true"></i></button>' +
        '<details><summary class="small">ثبت خروج واقعی</summary><input class="form-control form-control-sm mt-1" type="text" data-exit-date data-jalali dir="ltr" placeholder="تاریخ شمسی خروج"><input class="form-control form-control-sm mt-1" type="time" data-exit-time aria-label="ساعت واقعی خروج"><button class="btn btn-sm btn-outline-danger mt-1" data-act="correct-end">ثبت زمان خروج</button></details>';
    }
    if (st === 'paused') {
      return '<button class="btn ph-row-btn ph-row-start" data-act="start" title="ادامه تایمر"><i data-lucide="play" aria-hidden="true"></i></button>' +
        '<button class="btn ph-row-btn ph-row-end" data-act="end" title="پایان حضور"><i data-lucide="square" aria-hidden="true"></i></button>';
    }
    if (st === 'finished') {
      return '<button class="btn ph-row-btn ph-row-invoice" data-act="invoice" title="صدور فاکتور"><i data-lucide="receipt" aria-hidden="true"></i><span>فاکتور</span></button>';
    }
    return '';
  }

  // ── intake submission ───────────────────────────────────────────────
  if ($intake) {
    $intake.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!syncJalaliDate()) return;
      var fd = new FormData($intake);
      var payload = {
        first_name: fd.get('first_name'),
        last_name: fd.get('last_name'),
        age: fd.get('age') ? Number(fd.get('age')) : null,
        guardian_mobile: fd.get('guardian_mobile') || '',
        session_date: fd.get('session_date') || undefined,
        member_pk: fd.get('member_pk') || null,
        person_pk: fd.get('person_pk') || null,
        national_code: fd.get('national_code') || '',
        student_code: fd.get('student_code') || '',
      };
      if (!payload.member_pk && !payload.person_pk && (!payload.national_code || !payload.student_code)) {
        toast('برای فرد جدید، کد ملی و کد دانش‌آموزی/شناسه را وارد کنید؛ یا یک فرد قبلی را انتخاب کنید.', 'danger');
        return;
      }
      post(API + 'sessions/', payload).then(function (d) {
        toast('ورود ثبت شد.', 'success');
        var url = new URL(window.location.href);
        url.searchParams.set('day', payload.session_date);
        window.location.assign(url.toString());
      }).catch(function (err) { toast(err.message, 'danger'); });
    });
  }

  // ── existing-member search ──────────────────────────────────────────
  var $search = document.getElementById('ph-member-search');
  if ($search) {
    var $results = document.getElementById('ph-member-results');
    var $pk = document.getElementById('ph-member-pk');
    var $personPk = document.getElementById('ph-person-pk');
    var $selected = document.getElementById('ph-selected-member');
    var $selectedName = document.getElementById('ph-selected-name');
    var $selectedMeta = document.getElementById('ph-selected-meta');
    var $selectedRemove = document.getElementById('ph-selected-remove');
    var $memberClear = document.getElementById('ph-member-clear');
    var $searchStatus = document.getElementById('ph-search-status');
    var $first = document.getElementById('ph-first');
    var $last = document.getElementById('ph-last');
    var $age = document.getElementById('ph-age');
    var $mobile = document.getElementById('ph-mobile');
    var $nationalCode = document.getElementById('ph-national-code');
    var $studentCode = document.getElementById('ph-student-code');
    var sTimer = null;
    function clearMemberSelection(clearFields) {
      $pk.value = '';
      $personPk.value = '';
      $selected.hidden = true;
      $memberClear.hidden = true;
      $search.setAttribute('aria-expanded', 'false');
      $searchStatus.textContent = 'برای انتخاب سریع، نام یا شماره را جستجو کنید.';
      if (clearFields) {
        $first.value = '';
        $last.value = '';
        $age.value = '';
        $mobile.value = '';
        if ($nationalCode) $nationalCode.value = '';
        if ($studentCode) $studentCode.value = '';
      }
    }
    function chooseMember(member) {
      $pk.value = member.member_pk || '';
      $personPk.value = member.person_pk || '';
      $first.value = member.first_name || '';
      $last.value = member.last_name || '';
      $age.value = member.age == null ? '' : member.age;
      $mobile.value = member.guardian_mobile || '';
      if ($nationalCode) $nationalCode.value = '';
      if ($studentCode) $studentCode.value = '';
      $search.value = member.display_name || '';
      $selectedName.textContent = member.display_name || 'عضو انتخاب‌شده';
      $selectedMeta.textContent = (member.meta || (member.guardian_mobile ? ('شماره والدین: ' + member.guardian_mobile) : 'اطلاعات قبلی بارگذاری شد'));
      $selected.hidden = false;
      $memberClear.hidden = false;
      $results.classList.add('d-none');
      $search.setAttribute('aria-expanded', 'false');
      $searchStatus.textContent = 'اطلاعات قبلی در فرم بارگذاری شد؛ در صورت نیاز قابل ویرایش است.';
      icons();
      toast('اطلاعات عضو انتخاب و بارگذاری شد.', 'success');
    }
    $search.addEventListener('input', function () {
      clearTimeout(sTimer);
      var q = $search.value.trim();
      if (q.length < 1) { $results.classList.add('d-none'); $search.setAttribute('aria-expanded', 'false'); return; }
      sTimer = setTimeout(function () {
        get(API + 'members/search/?q=' + encodeURIComponent(q)).then(function (d) {
          var rows = d.results || [];
          $results.classList.remove('d-none');
          $search.setAttribute('aria-expanded', 'true');
          $results.innerHTML = '';
          if (!rows.length) {
            $results.innerHTML = '<div class="ph-member-empty">عضوی با این مشخصات پیدا نشد.</div>';
            return;
          }
          rows.forEach(function (m) {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'ph-member-option';
            b.setAttribute('role', 'option');
            b.innerHTML = '<span class="ph-member-option-avatar">' + esc((m.first_name || '؟').slice(0, 1)) + '</span><span class="flex-grow-1"><strong>' + esc(m.display_name) + '</strong><small>' + esc(m.guardian_mobile || 'شماره والدین ثبت نشده') + '</small></span><i data-lucide="arrow-left" aria-hidden="true"></i>';
            b.addEventListener('click', function () { chooseMember(m); });
            $results.appendChild(b);
          });
          icons();
        }).catch(function () { $results.classList.add('d-none'); });
      }, 250);
    });
    $memberClear.addEventListener('click', function () { clearMemberSelection(true); $search.value = ''; $search.focus(); });
    $selectedRemove.addEventListener('click', function () { clearMemberSelection(false); $search.value = ''; $search.focus(); });
    // clicking outside closes the list
    document.addEventListener('click', function (e) { if (!$results.contains(e.target) && e.target !== $search) $results.classList.add('d-none'); });
  }

  // ── member picker clears member_pk when user types fresh name ───────
  ['ph-first', 'ph-last'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', function () {
      var pk = document.getElementById('ph-member-pk');
      var personPk = document.getElementById('ph-person-pk');
      if ((pk && pk.value) || (personPk && personPk.value)) {
        pk.value = '';
        if (personPk) personPk.value = '';
        var selected = document.getElementById('ph-selected-member');
        if (selected) selected.hidden = true;
      }
    });
  });
  var $reset = document.getElementById('ph-reset');
  if ($reset && $intake) $reset.addEventListener('click', function () {
    $intake.reset();
    var pk = document.getElementById('ph-member-pk');
    if (pk) pk.value = '';
    var personPk = document.getElementById('ph-person-pk');
    if (personPk) personPk.value = '';
    if ($search) $search.value = '';
    var selected = document.getElementById('ph-selected-member');
    if (selected) selected.hidden = true;
    var clear = document.getElementById('ph-member-clear');
    if (clear) clear.hidden = true;
    var results = document.getElementById('ph-member-results');
    if (results) results.classList.add('d-none');
  });

  // ── row actions (event delegation) ──────────────────────────────────
  if ($table) {
    $table.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-act]');
      if (!btn) return;
      var tr = btn.closest('tr');
      var id = tr.getAttribute('data-id');
      var act = btn.getAttribute('data-act');
      if (act === 'invoice') { openInvoice(tr); return; }
      var apiAct = act === 'correct-start' ? 'start' : (act === 'correct-end' ? 'end' : act);
      var payload = {};
      if (act === 'correct-start') {
        payload.entry_at = localTimestamp(tr.querySelector('[data-entry-date]').value, tr.querySelector('[data-entry-time]').value);
        if (!payload.entry_at) { toast('تاریخ شمسی و ساعت واقعی ورود را وارد کنید.', 'danger'); return; }
      } else if (act === 'correct-end') {
        payload.exit_at = localTimestamp(tr.querySelector('[data-exit-date]').value, tr.querySelector('[data-exit-time]').value);
        if (!payload.exit_at) { toast('تاریخ شمسی و ساعت واقعی خروج را وارد کنید.', 'danger'); return; }
      }
      post(API + 'sessions/' + id + '/' + apiAct + '/', payload)
        .then(function (d) {
          toast(actLabel(act) + ' انجام شد.', 'success');
          updateRow(d);
        })
        .catch(function (err) { toast(err.message, 'danger'); });
    });
  }
  function actLabel(a) {
    return { start: 'شروع', 'correct-start': 'ثبت زمان ورود', stop: 'توقف', end: 'پایان', 'correct-end': 'ثبت زمان خروج', cancel: 'لغو' }[a] || a;
  }
  function updateRow(s) {
    if (!$table) return;
    var tr = $table.querySelector('tr[data-id="' + s.id + '"]');
    if (!tr) { renderRow(s); startClock(); return; }
    tr.setAttribute('data-status', s.status);
    tr.setAttribute('data-entry', s.entry_at || '');
    tr.setAttribute('data-exit', s.exit_at || '');
    tr.setAttribute('data-session-date', s.session_date || '');
    tr.setAttribute('data-paused-at', s.paused_at || '');
    tr.setAttribute('data-paused-seconds', s.paused_seconds || 0);
    tr.setAttribute('data-billable', s.billable_minutes || 0);
    var st = s.status;
    var statusCell = tr.querySelector('[data-role="status"]');
    if (statusCell) statusCell.innerHTML = statusMarkup(s);
    var actions = tr.querySelector('[data-role="actions"]');
    if (actions) actions.innerHTML = actionsMarkup(s);
    var timer = tr.querySelector('[data-role="timer"]');
    if (timer) timer.textContent = (st === 'active' || st === 'paused') ? (s.elapsed_label || fmtDuration(s.elapsed_seconds)) : '—';
    renderTimes(tr);
    var invoice = tr.querySelector('[data-role="invoice"]');
    if (invoice && s.invoice_detail) invoice.innerHTML = invoiceMarkup(s.invoice_detail);
    icons();
    updateCounters();
    if (st === 'active') startClock();
  }

  function updateCounters() {
    if (!$table) return;
    var rows = Array.prototype.slice.call($table.querySelectorAll('tbody tr[data-id]'));
    var active = rows.filter(function (tr) { return tr.getAttribute('data-status') === 'active'; }).length;
    var activeEl = document.getElementById('ph-active-count');
    var todayEl = document.getElementById('ph-today-count');
    if (activeEl) activeEl.textContent = window.persianNumbers ? window.persianNumbers(active) : active;
    if (todayEl) todayEl.textContent = window.persianNumbers ? window.persianNumbers(rows.length) : rows.length;
  }

  // ── invoice modal ───────────────────────────────────────────────────
  var $invModal = document.getElementById('ph-invoice-modal');
  var cafeRows = function () { return Array.prototype.slice.call(document.querySelectorAll('#ph-cafe-items .ph-cafe-row')); };
  function computeTotal() {
    var timeAmountEl = document.getElementById('ph-invoice-time-amount');
    var totalEl = document.getElementById('ph-invoice-total');
    var timeAmount = Number(timeAmountEl && timeAmountEl.dataset.amount) || 0;
    var cafe = cafeRows().reduce(function (sum, row) {
      var price = Number((row.querySelector('input[aria-label="قیمت"]').value || '').replace(/[^\d]/g, '')) || 0;
      return sum + price;
    }, 0);
    if (totalEl) totalEl.textContent = fmt(timeAmount + cafe);
  }
  var currentPrice = 0;
  function showInvoicePreview(tr) {
    var billable = Number(tr.getAttribute('data-billable')) || 0;
    var timeEl = document.getElementById('ph-invoice-time');
    var timeAmountEl = document.getElementById('ph-invoice-time-amount');
    var rateEl = document.getElementById('ph-invoice-rate');
    var blocksEl = document.getElementById('ph-invoice-blocks');
    var timeAmount = Math.round((billable / 15) * currentPrice);
    timeEl.textContent = fmtTime(billable);
    timeAmountEl.dataset.amount = String(timeAmount);
    timeAmountEl.textContent = fmt(timeAmount) + ' تومان';
    if (rateEl) rateEl.textContent = 'نرخ: ' + fmt(currentPrice) + ' تومان / ۱۵ دقیقه';
    if (blocksEl) blocksEl.textContent = fmt(billable / 15) + ' بازه ۱۵ دقیقه‌ای';
    computeTotal();
  }
  function openInvoice(tr) {
    if (!$invModal) return;
    var id = tr.getAttribute('data-id');
    document.getElementById('ph-invoice-session').value = id;
    if (currentPrice <= 0) {
      get(API + 'config/').then(function (d) {
        currentPrice = Number(d.price_per_15_minutes) || 0;
        showInvoicePreview(tr);
      }).catch(function () { showInvoicePreview(tr); });
    } else {
      showInvoicePreview(tr);
    }
    document.getElementById('ph-invoice-error').hidden = true;
    // reset payment selection + tracking code
    var checked = document.querySelector('input[name="ph-pay-method"]:checked');
    if (checked) checked.checked = false;
    var trackingInp = document.getElementById('ph-tracking');
    if (trackingInp) trackingInp.value = '';
    // ensure at least one empty cafe row
    if (!cafeRows().length) addCafeRow();
    // reset existing rows to blank (keep the first)
    cafeRows().forEach(function (row, i) {
      row.querySelector('input[aria-label="نام آیتم"]').value = '';
      row.querySelector('input[aria-label="قیمت"]').value = '';
      if (i > 0) row.remove();
    });
    computeTotal();
    const modal = window.bootstrap ? bootstrap.Modal.getOrCreateInstance($invModal) : null;
    if (modal) modal.show();
  }
  function addCafeRow() {
    var wrap = document.getElementById('ph-cafe-items');
    var row = document.createElement('div');
    row.className = 'row g-2 ph-cafe-row mt-0';
    row.innerHTML =
      '<div class="col-6"><input type="text" class="form-control" placeholder="نام آیتم" aria-label="نام آیتم"></div>' +
      '<div class="col-5"><input type="number" class="form-control" placeholder="قیمت" min="0" aria-label="قیمت"></div>' +
      '<div class="col-1 d-flex align-items-center"><button type="button" class="btn btn-sm btn-light ph-cafe-remove" title="حذف"><i data-lucide="x"></i></button></div>';
    wrap.appendChild(row);
    icons();
    bindCafeRow(row);
    computeTotal();
  }
  function bindCafeRow(row) {
    row.querySelectorAll('input').forEach(function (inp) { inp.addEventListener('input', computeTotal); });
  }
  if (document.getElementById('ph-cafe-items')) {
    cafeRows().forEach(bindCafeRow);
    // add-row button (first row has add; subsequent have remove)
    document.getElementById('ph-cafe-items').addEventListener('click', function (e) {
      var add = e.target.closest('.ph-cafe-add');
      if (add) { addCafeRow(); return; }
      var rm = e.target.closest('.ph-cafe-remove');
      if (rm) { cafeRows().forEach(function (r) { if (rm.closest('.ph-cafe-row') === r) { r.remove(); computeTotal(); icons(); } }); if (!cafeRows().length) addCafeRow(); }
    });
  }

  var $submit = document.getElementById('ph-invoice-submit');
  if ($submit) {
    $submit.addEventListener('click', function () {
      var sessionId = document.getElementById('ph-invoice-session').value;
      var errorEl = document.getElementById('ph-invoice-error');
      var cafe = cafeRows().map(function (row) {
        var name = row.querySelector('input[aria-label="نام آیتم"]').value.trim();
        var price = row.querySelector('input[aria-label="قیمت"]').value.trim();
        if (!name && !price) return null;
        return { name: name, price: Number(price.replace(/[^\d]/g, '')) || 0 };
      }).filter(Boolean);
      var methodEl = document.querySelector('input[name="ph-pay-method"]:checked');
      var method = methodEl ? methodEl.value : '';
      var tracking = document.getElementById('ph-tracking').value.trim();
      $submit.disabled = true;
      post(API + 'sessions/' + sessionId + '/invoice/', {
        cafe_items: cafe,
        payment_method: method,
        tracking_code: tracking,
      })
        .then(function (inv) {
          errorEl.hidden = true;
          toast(inv.is_paid ? 'فاکتور صادر و پرداخت ثبت شد: ' + fmt(inv.total_amount) + ' تومان' : 'فاکتور صادر شد: ' + fmt(inv.total_amount) + ' تومان', 'success');
          if (window.bootstrap) bootstrap.Modal.getInstance($invModal) && bootstrap.Modal.getInstance($invModal).hide();
          var row = $table && $table.querySelector('tr[data-id="' + sessionId + '"]');
          if (row) {
            row.setAttribute('data-has-invoice', '1');
            var statusCell = row.querySelector('[data-role="status"]');
            if (statusCell) statusCell.innerHTML = invoiceStatusMarkup(!!inv.is_paid);
            var invoiceCell = row.querySelector('[data-role="invoice"]');
            if (invoiceCell) invoiceCell.innerHTML = invoiceMarkup(inv);
            var actions = row.querySelector('[data-role="actions"]');
            if (actions) actions.innerHTML = '<span class="ph-invoice-done" title="' + esc(inv.invoice_number || '') + '">' + esc(inv.invoice_number || 'ثبت شد') + '</span>';
            icons();
          }
        })
        .catch(function (err) {
          errorEl.hidden = false;
          errorEl.textContent = err.message;
        })
        .finally(function () { $submit.disabled = false; });
    });
  }

  // ── refresh + clock ─────────────────────────────────────────────────
  var $refresh = document.getElementById('ph-refresh');
  if ($refresh) $refresh.addEventListener('click', function () { window.location.reload(); });

  if ($priceForm) $priceForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var input = document.getElementById('ph-price-input');
    var error = document.getElementById('ph-price-error');
    var save = document.getElementById('ph-price-save');
    var value = Number(input.value);
    if (!input.value || !Number.isInteger(value) || value < 0) {
      error.textContent = 'هزینه معتبر و غیرمنفی وارد کنید.';
      error.hidden = false;
      return;
    }
    save.disabled = true;
    error.hidden = true;
    fetch(API + 'config/', { method: 'PUT', credentials: 'same-origin', headers: headers(), body: JSON.stringify({ price_per_15_minutes: value }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { if (!r.ok) throw new Error(apiError(b) || ('HTTP ' + r.status)); return b; }); })
      .then(function (d) {
        currentPrice = Number(d.price_per_15_minutes) || 0;
        if ($priceBadge) $priceBadge.textContent = fmt(currentPrice);
        toast('هزینه هر ۱۵ دقیقه ذخیره شد.', 'success');
        if (window.bootstrap) bootstrap.Modal.getInstance(document.getElementById('ph-price-modal')).hide();
      })
      .catch(function (err) { error.textContent = err.message; error.hidden = false; })
      .finally(function () { save.disabled = false; });
  });

  function showLogDay() {
    var input = document.getElementById('ph-log-date');
    var iso = input && window.penJalaliToISO ? window.penJalaliToISO(input.value) : null;
    if (!iso) { toast('تاریخ شمسی را به شکل سال/ماه/روز وارد کنید.', 'danger'); return; }
    var url = new URL(window.location.href);
    url.searchParams.set('day', iso);
    window.location.assign(url.toString());
  }
  var $logDate = document.getElementById('ph-log-date');
  var $logSubmit = document.getElementById('ph-log-date-submit');
  if ($logSubmit) $logSubmit.addEventListener('click', showLogDay);
  if ($logDate) $logDate.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); showLogDay(); } });
  var $logToday = document.getElementById('ph-log-today');
  if ($logToday) $logToday.addEventListener('click', function () { window.location.assign(window.location.pathname); });

  if ($table) {
    $table.addEventListener('focusin', function (e) {
      var tr = e.target.closest('tr[data-id]');
      if (!tr) return;
      var entryDate = tr.querySelector('[data-entry-date]');
      var exitDate = tr.querySelector('[data-exit-date]');
      if (entryDate && !entryDate.value) entryDate.value = jalaliDate(tr.getAttribute('data-session-date'));
      if (exitDate && !exitDate.value) exitDate.value = jalaliDate(tr.getAttribute('data-session-date'));
      if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    startClock();
    updateCounters();
    if ($table) $table.querySelectorAll('tr[data-id]').forEach(function (tr) {
      renderTimes(tr);
      var entryDate = tr.querySelector('[data-entry-date]');
      var exitDate = tr.querySelector('[data-exit-date]');
      if (entryDate) entryDate.value = jalaliDate(tr.getAttribute('data-session-date'));
      if (exitDate) exitDate.value = jalaliDate(tr.getAttribute('data-session-date'));
      var paidAt = tr.querySelector('[data-paid-at]');
      if (paidAt) paidAt.textContent = jalaliDateTime(paidAt.getAttribute('data-paid-at'));
    });
    if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
    var dateDisplay = document.getElementById('ph-date-display');
    if (dateDisplay) {
      dateDisplay.addEventListener('input', syncJalaliDate);
      dateDisplay.addEventListener('change', syncJalaliDate);
    }
    // fetch current price (used for the invoice preview + badge)
    get('/api/playhouse/config/').then(function (d) {
      currentPrice = Number(d.price_per_15_minutes) || 0;
      if ($priceBadge) $priceBadge.textContent = fmt(currentPrice);
      var priceInput = document.getElementById('ph-price-input');
      if (priceInput) priceInput.value = currentPrice;
    }).catch(function () {});
  });
})();
