/*
 * Pen LMS — teacher attendance sheet (پنل مدرس › حضور و غیاب).
 *
 * Flow (task spec §2): pick one of MY classes → the roster auto-loads
 * (GET /offerings/{id}/sheet/) → fill session metadata (Jalali date, number,
 * start/end) → mark each student present/absent/late/excused + note →
 * ONE atomic POST /offerings/{id}/record-session/ (session + all rows in a
 * single server-side transaction; duplicate number/date is refused there).
 *
 * Editing: the session dropdown lists the class's saved sessions; picking one
 * prefills metadata + statuses (the sheet endpoint merges saved records).
 * Deep links: ?class=<offering>&session=<sid> (dashboard cards) or
 * ?session=<sid> (teacher calendar) — resolved via the session detail API.
 */
(function () {
  'use strict';

  var CLASSES_URL = '/api/education/teacher/classes/';
  var SHEET = function (oid) { return '/api/education/offerings/' + oid + '/sheet/'; };
  var RECORD = function (oid) { return '/api/education/offerings/' + oid + '/record-session/'; };
  var SESSION = function (sid) { return '/api/education/sessions/' + sid + '/'; };

  var STATUSES = [
    ['present', 'حاضر', 'success'],
    ['absent', 'غایب', 'danger'],
    ['late', 'تأخیر', 'warning'],
    ['excused', 'موجه', 'info'],
  ];

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function pn(s) { return window.persianNumbers ? window.persianNumbers(s) : s; }
  function toLatin(s) {
    return String(s == null ? '' : s).replace(/[۰-۹]/g, function (c) { return String('۰۱۲۳۴۵۶۷۸۹'.indexOf(c)); })
      .replace(/[٠-٩]/g, function (c) { return String('٠١٢٣٤٥٦٧٨٩'.indexOf(c)); });
  }
  function isoToJalali(iso) { return window.penISOToJalali ? window.penISOToJalali(iso) : (iso || ''); }
  function todayJalali() { return isoToJalali(new Date().toISOString().slice(0, 10)); }
  function headers() {
    return Object.assign({ 'Content-Type': 'application/json' },
      window.penCsrfHeader ? window.penCsrfHeader() : {});
  }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (r) {
        return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); });
      });
  }
  function post(url, body) {
    return fetch(url, { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body) })
      .then(function (r) {
        return r.json().then(function (b) {
          if (r.ok) return b;
          var msg = b.error || b.detail;
          if (!msg && typeof b === 'object') {
            msg = Object.keys(b).map(function (k) {
              var v = b[k]; return (k === 'detail' || k === 'error') ? v : k + ': ' + (Array.isArray(v) ? v.join(' / ') : v);
            }).join(' — ');
          }
          throw new Error(msg || ('HTTP ' + r.status));
        });
      });
  }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }
  function param(name) { return new URLSearchParams(location.search).get(name) || ''; }

  var $cls = document.getElementById('att-class');
  var $ses = document.getElementById('att-session');
  var $sesHint = document.getElementById('att-session-hint');
  var $new = document.getElementById('att-new');
  var $date = document.getElementById('att-date');
  var $num = document.getElementById('att-number');
  var $start = document.getElementById('att-start');
  var $end = document.getElementById('att-end');
  var $title = document.getElementById('att-title');
  var $rows = document.getElementById('att-rows');
  var $count = document.getElementById('att-count');
  var $summary = document.getElementById('att-summary');
  var $replace = document.getElementById('att-replace');
  var $save = document.getElementById('att-save');
  var $allPresent = document.getElementById('att-all-present');
  var $clear = document.getElementById('att-clear');

  var classes = [];
  var sheet = null;        // { offering_id, session_id|null, rows:[{id,status,note,inactive}] }

  // ── enable/disable ──────────────────────────────────────────────────
  function setEnabled(on) {
    [$date, $num, $start, $end, $title, $save, $new, $allPresent, $clear].forEach(function (el) {
      el.disabled = !on;
    });
  }

  // ── class picker ────────────────────────────────────────────────────
  function renderSessions() {
    var c = classes.filter(function (x) { return x.id === $cls.value; })[0];
    if (!c) {
      $ses.innerHTML = '<option value="">— ابتدا کلاس را انتخاب کنید —</option>';
      $ses.disabled = true; $sesHint.textContent = '';
      return;
    }
    $ses.disabled = false;
    $ses.innerHTML = '<option value="">⟵ جلسه جدید (امروز)</option>' +
      (c.sessions || []).slice().reverse().map(function (s) {
        var label = 'جلسه ' + pn(s.number) + ' — ' + esc(isoToJalali(s.date)) + ' · ' + pn(s.start) +
          (s.recorded ? ' (' + pn(s.recorded) + ' ثبت‌شده)' : ' (بدون حضور)');
        return '<option value="' + esc(s.id) + '">' + label + '</option>';
      }).join('');
    var pend = (c.stats && c.stats.not_recorded) || 0;
    $sesHint.textContent = pend
      ? pn(pend) + ' جلسه از این کلاس هنوز حضور ندارد.'
      : 'همه جلسات این کلاس حضور ثبت‌شده دارند.';
  }

  function loadClasses() {
    return get(CLASSES_URL).then(function (d) {
      classes = d.results || [];
      $cls.innerHTML = '<option value="">— انتخاب کلاس —</option>' + classes.map(function (c) {
        return '<option value="' + esc(c.id) + '">' + esc(c.title || c.course) +
          ' (' + pn(c.roster_size || 0) + ' دانش‌آموز)</option>';
      }).join('');
      return classes;
    });
  }

  // ── sheet render ────────────────────────────────────────────────────
  function statusButton(row, st) {
    var active = row.status === st[0];
    return '<button type="button" class="pen-status ' + (active ? st[0] : 'unset') + '"' +
      ' data-status="' + st[0] + '" aria-pressed="' + (active ? 'true' : 'false') + '">' +
      '<span class="dot"></span>' + st[1] + '</button>';
  }

  function renderRows() {
    if (!sheet) {
      $rows.innerHTML = '<tr><td colspan="4"><div class="pen-empty">برای بارگذاری خودکار فهرست دانش‌آموزان، ابتدا کلاس را انتخاب کنید.</div></td></tr>';
      $count.textContent = ''; updateSummary(); return;
    }
    var rows = sheet.rows;
    if (!rows.length) {
      $rows.innerHTML = '<tr><td colspan="4"><div class="pen-empty">این کلاس هنوز دانش‌آموز فعالی ندارد (ثبت‌نام معتبری یافت نشد).</div></td></tr>';
      $count.textContent = ''; updateSummary(); return;
    }
    $count.textContent = '— ' + pn(rows.length) + ' دانش‌آموز';
    $rows.innerHTML = rows.map(function (r, i) {
      return '<tr class="att-row' + (r.status ? ' marked' : '') + '" data-id="' + esc(r.id) + '">' +
        '<td class="text-muted">' + pn(i + 1) + '</td>' +
        '<td><div class="fw-semibold">' + esc(r.name) + '</div>' +
          '<div class="fs-13 text-muted" dir="ltr">' + esc(r.student_code || '') +
          (r.inactive ? ' <span class="badge text-bg-secondary">غیرفعال</span>' : '') + '</div></td>' +
        '<td><div class="pen-seg">' + STATUSES.map(function (st) { return statusButton(r, st); }).join('') + '</div></td>' +
        '<td class="row-note"><input type="text" class="form-control form-control-sm note-input" maxlength="500" ' +
          'value="' + esc(r.note || '') + '" placeholder="توضیح وضعیت…" aria-label="یادداشت ' + esc(r.name) + '"></td>' +
        '</tr>';
    }).join('');

    $rows.querySelectorAll('tr').forEach(function ($tr) {
      var id = $tr.dataset.id;
      function row() { return sheet.rows.filter(function (x) { return x.id === id; })[0]; }
      $tr.querySelectorAll('[data-status]').forEach(function ($btn) {
        $btn.addEventListener('click', function () {
          var r = row(); if (!r) return;
          var next = (r.status === $btn.dataset.status) ? '' : $btn.dataset.status;
          r.status = next;
          $tr.classList.toggle('marked', !!next);
          $tr.querySelectorAll('[data-status]').forEach(function (b) {
            var on = b.dataset.status === next;
            b.className = 'pen-status ' + (on ? b.dataset.status : 'unset');
            b.setAttribute('aria-pressed', on ? 'true' : 'false');
          });
          updateSummary();
        });
      });
      var $note = $tr.querySelector('.note-input');
      if ($note) $note.addEventListener('input', function () { var r = row(); if (r) r.note = $note.value; });
    });
    updateSummary();
    icons();
  }

  function updateSummary() {
    if (!sheet) { $summary.textContent = 'وضعیت هیچ دانش‌آموزی انتخاب نشده است.'; return; }
    var t = { present: 0, absent: 0, late: 0, excused: 0, unset: 0 };
    sheet.rows.forEach(function (r) { if (r.status) t[r.status]++; else t.unset++; });
    $summary.innerHTML = 'حاضر ' + pn(t.present) + ' · غایب ' + pn(t.absent) +
      ' · تأخیر ' + pn(t.late) + ' · موجه ' + pn(t.excused) +
      (t.unset ? ' · <span class="text-danger">بدون وضعیت: ' + pn(t.unset) + '</span>' : '');
  }

  function fillMeta(s) {
    $date.value = isoToJalali(s.date);
    $num.value = s.number;
    $start.value = s.start;
    $end.value = s.end;
    $title.value = s.title || '';
  }

  function openSheet(offeringId, sessionId) {
    var url = SHEET(offeringId) + (sessionId ? '?session=' + encodeURIComponent(sessionId) : '');
    return get(url).then(function (d) {
      sheet = { offering_id: offeringId, session_id: (d.session && d.session.id) || null, rows: d.rows || [] };
      if (sheet.session_id) {
        // editing a saved session — prefill its metadata; the sheet's own
        // session list is authoritative (the class picker may be capped),
        // dates come back ISO in both.
        var s = (d.sessions || []).filter(function (x) { return x.id === sheet.session_id; })[0];
        if (s) fillMeta(s);
        if (d.session && d.session.title) $title.value = d.session.title;
        $num.disabled = false;
      } else {
        // new session — sensible defaults from the class schedule
        var cc = classes.filter(function (x) { return x.id === offeringId; })[0];
        $date.value = todayJalali();
        var maxNo = ((cc && cc.sessions) || []).reduce(function (m, x) { return Math.max(m, x.number || 0); }, 0);
        $num.value = maxNo + 1;
        if (cc && cc.schedule && cc.schedule.start) { $start.value = cc.schedule.start; $end.value = cc.schedule.end || ''; }
        $title.value = '';
      }
      $ses.value = sheet.session_id || '';
      renderRows();
      setEnabled(true);
      if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
      icons();
    });
  }

  // ── events ──────────────────────────────────────────────────────────
  $cls.addEventListener('change', function () {
    sheet = null;
    renderSessions();
    if (!$cls.value) { setEnabled(false); renderRows(); return; }
    openSheet($cls.value, null);
  });
  $ses.addEventListener('change', function () {
    if (!$cls.value) return;
    openSheet($cls.value, $ses.value || null);
  });
  $new.addEventListener('click', function () {
    if (!$cls.value) return;
    $ses.value = '';
    openSheet($cls.value, null);
  });
  $allPresent.addEventListener('click', function () {
    if (!sheet) return;
    sheet.rows.forEach(function (r) { if (!r.inactive) r.status = r.status || 'present'; });
    renderRows();
  });
  $clear.addEventListener('click', function () {
    if (!sheet) return;
    sheet.rows.forEach(function (r) { r.status = ''; });
    renderRows();
  });

  $save.addEventListener('click', function () {
    if (!sheet) return;
    var date = toLatin($date.value).trim().replace(/\./g, '/');
    var start = toLatin($start.value).trim();
    var end = toLatin($end.value).trim();
    if (!date) { toast('تاریخ جلسه را وارد کنید.', 'warning'); return; }
    if (!start || !end) { toast('ساعت شروع و پایان الزامی است.', 'warning'); return; }
    if (!/^\d{1,2}:\d{2}$/.test(start) || !/^\d{1,2}:\d{2}$/.test(end)) {
      toast('قالب ساعت باید HH:MM باشد.', 'warning'); return;
    }
    if (end <= start) { toast('ساعت پایان باید بعد از شروع باشد.', 'warning'); return; }
    if (!sheet.rows.length) { toast('فهرست دانش‌آموزان خالی است.', 'warning'); return; }
    var unset = sheet.rows.filter(function (r) { return !r.status && !r.inactive; });
    if (unset.length && !window.confirm(pn(unset.length) + ' دانش‌آموز بدون وضعیت باقی است. ثبت شود؟')) return;

    var payload = {
      session_date: date,
      start_time: start,
      end_time: end,
      session_number: parseInt(toLatin($num.value), 10) || null,
      title: $title.value.trim(),
      session_id: sheet.session_id || undefined,
      replace: $replace.checked,
      rows: sheet.rows.map(function (r) {
        return { student: r.id, status: r.status || 'present', note: r.note || '' };
      }),
    };
    $save.disabled = true;
    post(RECORD(sheet.offering_id), payload)
      .then(function (res) {
        toast('جلسه ثبت شد — ' + pn(res.total || 0) + ' ردیف (' + pn(res.created || 0) + ' جدید، ' + pn(res.updated || 0) + ' اصلاحی).', 'success');
        // refresh the class list (session counters) + reopen this session
        return loadClasses().then(function () {
          renderSessions();
          return openSheet(sheet.offering_id, res.session_id);
        });
      })
      .catch(function (e) { toast(e.message, 'danger'); })
      .finally(function () { $save.disabled = false; });
  });

  // ── boot (+ deep links) ─────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    loadClasses().then(function () {
      var qClass = param('class'), qSession = param('session');
      if (qClass && classes.some(function (c) { return c.id === qClass; })) {
        $cls.value = qClass;
        renderSessions();
        return openSheet(qClass, qSession || null);
      }
      if (qSession) {
        // calendar deep link: resolve the offering behind the session id
        return get(SESSION(qSession)).then(function (s) {
          var oid = s.offering;
          if (oid && classes.some(function (c) { return c.id === oid; })) {
            $cls.value = oid;
            renderSessions();
            return openSheet(oid, qSession);
          }
          toast('جلسه در کلاس‌های شما یافت نشد.', 'warning');
        });
      }
    }).catch(function (e) { toast(e.message, 'danger'); });
  });
})();
