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
  function remove(url) {
    return fetch(url, { method: 'DELETE', credentials: 'same-origin', headers: headers() })
      .then(function (r) { if (!r.ok) return r.json().catch(function () { return {}; }).then(function (b) { throw new Error(apiError(b) || ('HTTP ' + r.status)); }); });
  }
  function patchJson(url, body) {
    return fetch(url, { method: 'PATCH', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body) })
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
  function sessionTimerLabel(session) {
    if (session.status === 'active' || session.status === 'paused') {
      return session.elapsed_label || fmtDuration(session.elapsed_seconds);
    }
    if (session.status === 'finished') {
      return session.elapsed_label || fmtDuration(session.elapsed_seconds);
    }
    return '—';
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
    cell.innerHTML = '<span><i data-lucide="log-in" aria-hidden="true"></i><b>ورود</b> ' + fmtClock(entry) + '</span><span class="text-muted"><i data-lucide="log-out" aria-hidden="true"></i><b>خروج</b> ' + fmtClock(exit) + '</span>';
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
    tr.setAttribute('data-member-pk', s.member_pk || '');
    tr.setAttribute('data-member-first', s.member_first_name || '');
    tr.setAttribute('data-member-last', s.member_last_name || '');
    tr.setAttribute('data-member-age', s.age == null ? '' : s.age);
    tr.setAttribute('data-member-mobile', s.guardian_mobile || '');
    tr.setAttribute('data-member-guardian', s.guardian_name || '');
    tr.setAttribute('data-national-code', s.national_code || '');
    tr.setAttribute('data-temporary-id', s.temporary_id || '');
    tr.innerHTML =
      '<td class="small" data-role="times"></td>' +
      '<td><div class="ph-child-name">' + esc(s.member_name) + '</div><div class="ph-child-age">' + (s.age != null ? esc(s.age) + ' ساله' : 'سن ثبت نشده') + '</div><small class="ph-child-identity text-muted">' + esc(s.national_code ? ('کد ملی: ' + s.national_code) : ('موقت: ' + (s.temporary_id || 'شناسه ثبت نشده'))) + '</small></td>' +
      '<td><div>' + esc(s.guardian_name || '—') + '</div><div dir="ltr" class="ph-phone-cell">' + esc(s.guardian_mobile || '—') + '</div><small class="text-muted">' + esc(s.member_notes || '') + '</small></td>' +
      '<td class="fw-bold" data-role="timer">' + sessionTimerLabel(s) + '</td>' +
      '<td data-role="status">' + statusMarkup(s) + '</td>' +
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
  function statusMarkup(s) {
    var visit = '<span class="' + statusBadge(s.status) + '"><span></span>' + esc(statusLabel(s.status)) + '</span>';
    var readyCount = (s.cafe_orders || []).filter(function (order) { return order.status === 'ready'; }).length;
    return visit + (readyCount ? '<span class="ph-status ph-status-ready"><span></span>' + fmt(readyCount) + ' سفارش آماده</span>' : '');
  }
  function actionsMarkup(s) {
    var actions = s.has_invoice ? '' : actionButtons(s.status);
    return actions + '<button type="button" class="btn ph-row-btn ph-row-edit" data-member-edit title="ویرایش اطلاعات کودک" aria-label="ویرایش اطلاعات کودک"><i data-lucide="pencil" aria-hidden="true"></i></button>';
  }
  function actionButtons(st) {
    if (st === 'waiting') {
      return '<button class="btn ph-row-btn ph-row-start" data-act="start" title="شروع تایمر" aria-label="شروع تایمر"><i data-lucide="play" aria-hidden="true"></i></button>' +
        '<button class="btn ph-row-btn ph-row-cancel" data-act="cancel" title="لغو" aria-label="لغو مراجعه"><i data-lucide="x" aria-hidden="true"></i></button>' +
        '<details><summary class="small">ثبت زمان واقعی</summary><input class="form-control form-control-sm mt-1" type="text" data-entry-date data-jalali dir="ltr" placeholder="تاریخ شمسی ورود"><input class="form-control form-control-sm mt-1" type="time" data-entry-time aria-label="ساعت واقعی ورود"><button class="btn btn-sm btn-outline-primary mt-1" data-act="correct-start"><i data-lucide="clock-3" aria-hidden="true"></i>ثبت زمان ورود</button></details>';
    }
    if (st === 'active') {
      return '<button class="btn ph-row-btn btn-outline-success" data-act="cafe-order" title="ثبت سفارش کافه" aria-label="ثبت سفارش کافه"><i data-lucide="coffee" aria-hidden="true"></i></button>' +
        '<button class="btn ph-row-btn ph-row-pause" data-act="stop" title="توقف تایمر" aria-label="توقف تایمر"><i data-lucide="pause" aria-hidden="true"></i></button>' +
        '<button class="btn ph-row-btn ph-row-end" data-act="end" title="پایان حضور" aria-label="پایان حضور"><i data-lucide="square" aria-hidden="true"></i></button>' +
        '<details><summary class="small">ثبت خروج واقعی</summary><input class="form-control form-control-sm mt-1" type="text" data-exit-date data-jalali dir="ltr" placeholder="تاریخ شمسی خروج"><input class="form-control form-control-sm mt-1" type="time" data-exit-time aria-label="ساعت واقعی خروج"><button class="btn btn-sm btn-outline-danger mt-1" data-act="correct-end"><i data-lucide="clock-3" aria-hidden="true"></i>ثبت زمان خروج</button></details>';
    }
    if (st === 'paused') {
      return '<button class="btn ph-row-btn btn-outline-success" data-act="cafe-order" title="ثبت سفارش کافه" aria-label="ثبت سفارش کافه"><i data-lucide="coffee" aria-hidden="true"></i></button>' +
        '<button class="btn ph-row-btn ph-row-start" data-act="start" title="ادامه تایمر" aria-label="ادامه تایمر"><i data-lucide="play" aria-hidden="true"></i></button>' +
        '<button class="btn ph-row-btn ph-row-end" data-act="end" title="پایان حضور" aria-label="پایان حضور"><i data-lucide="square" aria-hidden="true"></i></button>';
    }
    if (st === 'finished') {
      return '<button class="btn ph-row-btn ph-row-invoice" data-act="invoice" title="صدور فاکتور" aria-label="صدور فاکتور"><i data-lucide="receipt" aria-hidden="true"></i></button>';
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
        national_code: (fd.get('national_code') || '').trim(),
      };
      post(API + 'sessions/', payload).then(function (d) {
        toast(d.temporary_id ? ('ورود ثبت شد؛ شناسه موقت: ' + d.temporary_id) : 'ورود ثبت شد.', 'success');
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
      }
    }
    function chooseMember(member) {
      $pk.value = member.member_pk || '';
      $personPk.value = member.person_pk || '';
      $first.value = member.first_name || '';
      $last.value = member.last_name || '';
      $age.value = member.age == null ? '' : member.age;
      $mobile.value = member.guardian_mobile || '';
      if ($nationalCode) $nationalCode.value = member.national_code || '';
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
            var details = [m.meta, m.guardian_mobile || 'شماره والدین ثبت نشده'].filter(Boolean).join(' · ');
            b.innerHTML = '<span class="ph-member-option-avatar">' + esc((m.first_name || '؟').slice(0, 1)) + '</span><span class="flex-grow-1"><strong>' + esc(m.display_name) + '</strong><small>' + esc(details) + '</small></span><i data-lucide="arrow-left" aria-hidden="true"></i>';
            b.addEventListener('click', function () { chooseMember(m); });
            $results.appendChild(b);
          });
          icons();
        }).catch(function () { $results.classList.add('d-none'); });
      }, 250);
    });
    $memberClear.addEventListener('click', function () { clearMemberSelection(true); $search.value = ''; $search.focus(); });
    $selectedRemove.addEventListener('click', function () { clearMemberSelection(false); if ($nationalCode) $nationalCode.value = ''; $search.value = ''; $search.focus(); });
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
        var nationalCode = document.getElementById('ph-national-code');
        if (nationalCode) nationalCode.value = '';
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
      var edit = e.target.closest('[data-member-edit]');
      if (edit) { openMemberEditor(edit.closest('tr')); return; }
      var btn = e.target.closest('[data-act]');
      if (!btn) return;
      var tr = btn.closest('tr');
      var id = tr.getAttribute('data-id');
      var act = btn.getAttribute('data-act');
      if (act === 'invoice') { openInvoice(tr); return; }
      if (act === 'cafe-order') { if (window.openPlayhouseCafeOrder) window.openPlayhouseCafeOrder(tr); return; }
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
  function openMemberEditor(tr) {
    var modal = document.getElementById('ph-member-modal');
    if (!modal || !window.bootstrap) return;
    document.getElementById('ph-edit-member-pk').value = tr.getAttribute('data-member-pk') || '';
    document.getElementById('ph-edit-first').value = tr.getAttribute('data-member-first') || '';
    document.getElementById('ph-edit-last').value = tr.getAttribute('data-member-last') || '';
    document.getElementById('ph-edit-national-code').value = tr.getAttribute('data-national-code') || '';
    document.getElementById('ph-edit-age').value = tr.getAttribute('data-member-age') || '';
    document.getElementById('ph-edit-mobile').value = tr.getAttribute('data-member-mobile') || '';
    document.getElementById('ph-edit-guardian').value = tr.getAttribute('data-member-guardian') || '';
    var temporaryId = tr.getAttribute('data-temporary-id') || '';
    document.getElementById('ph-edit-temporary-id').textContent = temporaryId ? ('شناسه موقت: ' + temporaryId) : 'شناسه موقت ثبت نشده';
    document.getElementById('ph-member-error').hidden = true;
    window.bootstrap.Modal.getOrCreateInstance(modal).show();
  }
  var memberForm = document.getElementById('ph-member-form');
  if (memberForm) memberForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var pk = document.getElementById('ph-edit-member-pk').value;
    var body = {
      first_name: document.getElementById('ph-edit-first').value.trim(),
      last_name: document.getElementById('ph-edit-last').value.trim(),
      national_code: document.getElementById('ph-edit-national-code').value.trim(),
      age: document.getElementById('ph-edit-age').value ? Number(document.getElementById('ph-edit-age').value) : null,
      guardian_mobile: document.getElementById('ph-edit-mobile').value.trim(),
      guardian_name: document.getElementById('ph-edit-guardian').value.trim()
    };
    patchJson(API + 'members/' + pk + '/', body).then(function (member) {
      document.querySelectorAll('#ph-session-table tr[data-member-pk="' + pk + '"]').forEach(function (tr) {
        tr.setAttribute('data-member-first', member.first_name || '');
        tr.setAttribute('data-member-last', member.last_name || '');
        tr.setAttribute('data-member-age', member.age == null ? '' : member.age);
        tr.setAttribute('data-member-mobile', member.guardian_mobile || '');
        tr.setAttribute('data-member-guardian', member.guardian_name || '');
        tr.setAttribute('data-national-code', body.national_code || '');
        tr.setAttribute('data-temporary-id', member.temporary_id || '');
        var name = tr.querySelector('.ph-child-name'); if (name) name.textContent = member.display_name;
        var age = tr.querySelector('.ph-child-age'); if (age) age.textContent = member.age == null ? 'سن ثبت نشده' : member.age + ' ساله';
        var phone = tr.querySelector('.ph-phone-cell'); if (phone) phone.textContent = member.guardian_mobile || '—';
        var identity = tr.querySelector('.ph-child-identity');
        if (identity) identity.textContent = body.national_code ? ('کد ملی: ' + body.national_code) : ('موقت: ' + (member.temporary_id || 'شناسه ثبت نشده'));
      });
      window.bootstrap.Modal.getOrCreateInstance(document.getElementById('ph-member-modal')).hide();
      toast('اطلاعات کودک ذخیره شد؛ تایمر بدون تغییر ادامه دارد.', 'success');
    }).catch(function (err) {
      var error = document.getElementById('ph-member-error'); error.textContent = err.message; error.hidden = false;
    });
  });
  function actLabel(a) {
    return { start: 'شروع', 'correct-start': 'ثبت زمان ورود', stop: 'توقف', end: 'پایان', 'correct-end': 'ثبت زمان خروج', cancel: 'لغو' }[a] || a;
  }
  function updateRow(s) {
    if (!$table) return;
    var tr = $table.querySelector('tr[data-id="' + s.id + '"]');
    if (!tr) { renderRow(s); startClock(); updateCounters(); return; }
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
    if (timer) timer.textContent = sessionTimerLabel(s);
    renderTimes(tr);
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
  function amountDigits(value) {
    return String(value || '').replace(/[۰-۹]/g, function (digit) { return String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)); })
      .replace(/[٠-٩]/g, function (digit) { return String('٠١٢٣٤٥٦٧٨٩'.indexOf(digit)); }).replace(/\D/g, '');
  }
  function parseAmount(value) { return Number(amountDigits(value)) || 0; }
  function formatAmountInput(input) {
    var caret = input.selectionStart || 0;
    var digitsBeforeCaret = amountDigits(input.value.slice(0, caret)).length;
    var digits = amountDigits(input.value);
    var formatted = digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    input.value = formatted;
    var nextCaret = 0;
    var seenDigits = 0;
    while (nextCaret < formatted.length && seenDigits < digitsBeforeCaret) {
      if (/\d/.test(formatted.charAt(nextCaret))) seenDigits++;
      nextCaret++;
    }
    input.setSelectionRange(nextCaret, nextCaret);
  }
  function computeTotal() {
    var timeAmountEl = document.getElementById('ph-invoice-time-amount');
    var totalEl = document.getElementById('ph-invoice-total');
    var timeAmount = Number(timeAmountEl && timeAmountEl.dataset.amount) || 0;
    var discountInput = document.getElementById('ph-invoice-discount');
    var discount = parseAmount(discountInput && discountInput.value);
    var cafe = cafeRows().reduce(function (sum, row) {
      var price = parseAmount(row.querySelector('input[aria-label="قیمت"]').value);
      return sum + price;
    }, 0);
    if (totalEl) totalEl.textContent = fmt(Math.max(0, timeAmount + cafe - discount));
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
    var discountInput = document.getElementById('ph-invoice-discount');
    var discountNote = document.getElementById('ph-invoice-discount-note');
    if (discountInput) discountInput.value = '0';
    if (discountNote) discountNote.value = '';
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
      '<div class="col-5"><input type="text" class="form-control" placeholder="قیمت" inputmode="numeric" autocomplete="off" dir="ltr" aria-label="قیمت"></div>' +
      '<div class="col-1 d-flex align-items-center"><button type="button" class="btn btn-sm btn-light ph-cafe-remove" title="حذف"><i data-lucide="x"></i></button></div>';
    wrap.appendChild(row);
    icons();
    bindCafeRow(row);
    computeTotal();
    return row;
  }
  function bindCafeRow(row) {
    row.querySelectorAll('input').forEach(function (inp) {
      inp.addEventListener('input', function () {
        if (inp.getAttribute('aria-label') === 'قیمت') formatAmountInput(inp);
        computeTotal();
      });
    });
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
  var discountInput = document.getElementById('ph-invoice-discount');
  if (discountInput) discountInput.addEventListener('input', function () { formatAmountInput(this); computeTotal(); });

  var cafePresets = [];
  var $cafePresetSelect = document.getElementById('ph-cafe-preset-select');
  var $cafePresetList = document.getElementById('ph-cafe-preset-list');
  function renderCafePresets() {
    if ($cafePresetSelect) {
      $cafePresetSelect.innerHTML = '<option value="">انتخاب از فهرست آماده</option>';
      cafePresets.forEach(function (preset) {
        var option = document.createElement('option');
        option.value = preset.id;
        option.textContent = preset.name + ' — ' + fmt(preset.price) + ' تومان';
        $cafePresetSelect.appendChild(option);
      });
    }
    if ($cafePresetList) {
      $cafePresetList.innerHTML = '';
      if (!cafePresets.length) {
        $cafePresetList.textContent = 'هنوز آیتمی در فهرست آماده ثبت نشده است.';
      } else {
        cafePresets.forEach(function (preset) {
          var item = document.createElement('div');
          item.className = 'row g-1 align-items-center border-top py-1 ph-cafe-preset-row';
          item.setAttribute('data-id', preset.id);
          var name = document.createElement('div');
          name.className = 'col-5';
          var nameInput = document.createElement('input');
          nameInput.type = 'text';
          nameInput.maxLength = 200;
          nameInput.className = 'form-control form-control-sm';
          nameInput.setAttribute('aria-label', 'نام آیتم آماده');
          nameInput.value = preset.name;
          name.appendChild(nameInput);
          var price = document.createElement('div');
          price.className = 'col-4';
          var priceInput = document.createElement('input');
          priceInput.type = 'text';
          priceInput.inputMode = 'numeric';
          priceInput.dir = 'ltr';
          priceInput.className = 'form-control form-control-sm';
          priceInput.setAttribute('aria-label', 'قیمت آیتم آماده');
          priceInput.value = String(preset.price);
          formatAmountInput(priceInput);
          priceInput.addEventListener('input', function () { formatAmountInput(priceInput); });
          price.appendChild(priceInput);
          var actions = document.createElement('div');
          actions.className = 'col-3 d-flex gap-1';
          var save = document.createElement('button');
          save.type = 'button';
          save.className = 'btn btn-sm btn-light ph-cafe-preset-save';
          save.textContent = 'ذخیره';
          var button = document.createElement('button');
          button.type = 'button';
          button.className = 'btn btn-sm btn-light text-danger ph-cafe-preset-delete';
          button.setAttribute('aria-label', 'حذف ' + preset.name + ' از فهرست آماده');
          button.textContent = 'حذف';
          actions.appendChild(save);
          actions.appendChild(button);
          item.appendChild(name);
          item.appendChild(price);
          item.appendChild(actions);
          $cafePresetList.appendChild(item);
        });
      }
    }
  }
  function loadCafePresets() {
    if (!$cafePresetSelect) return;
    get(API + 'cafe-presets/').then(function (items) {
      cafePresets = Array.isArray(items) ? items : [];
      renderCafePresets();
    }).catch(function () {
      var error = document.getElementById('ph-cafe-preset-error');
      if (error) { error.hidden = false; error.textContent = 'بارگذاری فهرست آیتم‌های آماده انجام نشد.'; }
    });
  }
  if ($cafePresetSelect) {
    loadCafePresets();
    document.getElementById('ph-cafe-preset-add').addEventListener('click', function () {
      var preset = cafePresets.filter(function (item) { return String(item.id) === $cafePresetSelect.value; })[0];
      if (!preset) return;
      var row = addCafeRow();
      row.querySelector('input[aria-label="نام آیتم"]').value = preset.name;
      var priceInput = row.querySelector('input[aria-label="قیمت"]');
      priceInput.value = String(preset.price);
      formatAmountInput(priceInput);
      computeTotal();
      $cafePresetSelect.value = '';
    });
    var $presetForm = document.getElementById('ph-cafe-preset-form');
    $presetForm.addEventListener('submit', function (event) {
      event.preventDefault();
      var nameInput = document.getElementById('ph-cafe-preset-name');
      var priceInput = document.getElementById('ph-cafe-preset-price');
      var error = document.getElementById('ph-cafe-preset-error');
      var name = nameInput.value.trim();
      var price = parseAmount(priceInput.value);
      if (!name || !price) {
        error.hidden = false;
        error.textContent = 'نام و قیمت آیتم را وارد کنید.';
        return;
      }
      error.hidden = true;
      post(API + 'cafe-presets/', { name: name, price: price }).then(function (preset) {
        cafePresets.push(preset);
        cafePresets.sort(function (a, b) { return a.name.localeCompare(b.name, 'fa'); });
        renderCafePresets();
        nameInput.value = '';
        priceInput.value = '';
      }).catch(function (err) {
        error.hidden = false;
        error.textContent = err.message;
      });
    });
    document.getElementById('ph-cafe-preset-price').addEventListener('input', function (event) { formatAmountInput(event.target); });
    $cafePresetList.addEventListener('click', function (event) {
      var error = document.getElementById('ph-cafe-preset-error');
      var row = event.target.closest('.ph-cafe-preset-row');
      if (!row) return;
      var id = row.getAttribute('data-id');
      var removeButton = event.target.closest('.ph-cafe-preset-delete');
      if (removeButton) {
        remove(API + 'cafe-presets/' + id + '/').then(function () {
          cafePresets = cafePresets.filter(function (item) { return String(item.id) !== id; });
          renderCafePresets();
        }).catch(function (err) { error.hidden = false; error.textContent = err.message; });
        return;
      }
      var saveButton = event.target.closest('.ph-cafe-preset-save');
      if (!saveButton) return;
      var name = row.querySelector('input[aria-label="نام آیتم آماده"]').value.trim();
      var price = parseAmount(row.querySelector('input[aria-label="قیمت آیتم آماده"]').value);
      patchJson(API + 'cafe-presets/' + id + '/', { name: name, price: price }).then(function (updated) {
        cafePresets = cafePresets.map(function (item) { return String(item.id) === id ? updated : item; });
        cafePresets.sort(function (a, b) { return a.name.localeCompare(b.name, 'fa'); });
        error.hidden = true;
        renderCafePresets();
      }).catch(function (err) { error.hidden = false; error.textContent = err.message; });
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
        return { name: name, price: parseAmount(price) };
      }).filter(Boolean);
      var methodEl = document.querySelector('input[name="ph-pay-method"]:checked');
      var method = methodEl ? methodEl.value : '';
      var tracking = document.getElementById('ph-tracking').value.trim();
      var discount = parseAmount((document.getElementById('ph-invoice-discount') || {}).value);
      var discountNote = (document.getElementById('ph-invoice-discount-note') || {}).value || '';
      $submit.disabled = true;
      post(API + 'sessions/' + sessionId + '/invoice/', {
        cafe_items: cafe,
        payment_method: method,
        tracking_code: tracking,
        discount_amount: discount,
        discount_note: discountNote,
      })
        .then(function (inv) {
          errorEl.hidden = true;
          toast(inv.is_paid ? 'فاکتور صادر و پرداخت ثبت شد: ' + fmt(inv.total_amount) + ' تومان' : 'فاکتور صادر شد: ' + fmt(inv.total_amount) + ' تومان', 'success');
          if (window.bootstrap) bootstrap.Modal.getInstance($invModal) && bootstrap.Modal.getInstance($invModal).hide();
          var row = $table && $table.querySelector('tr[data-id="' + sessionId + '"]');
          if (row) {
            row.setAttribute('data-has-invoice', '1');
            var statusCell = row.querySelector('[data-role="status"]');
            if (statusCell) statusCell.innerHTML = '<span class="' + statusBadge(row.getAttribute("data-status")) + '"><span></span>' + esc(statusLabel(row.getAttribute("data-status"))) + '</span>';
            var actions = row.querySelector('[data-role="actions"]');
            if (actions) actions.innerHTML = actionsMarkup({ has_invoice: true });
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

  // Keep order readiness visible at the counter while local timer labels tick.
  function refreshAttendance() {
    var day = new URL(window.location.href).searchParams.get('day') || window.__PLAYHOUSE_SELECTED_DAY__;
    if (!day || !$table) return;
    get(API + 'attendance/?date=' + encodeURIComponent(day)).then(function (rows) {
      rows.forEach(updateRow);
    }).catch(function () {});
  }
  if ($table) window.setInterval(refreshAttendance, 6000);
  window.addEventListener('ph-cafe-order-created', refreshAttendance);

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
