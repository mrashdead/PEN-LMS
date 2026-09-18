/*
 * Pen LMS — learner portal (student / parent).
 *
 * Task spec §4: a student (or a parent logging in with guardian access) sees
 * ONLY that student's data — attendance stats (present/absent/late counts +
 * rate), the sessions table (jalali date, number, start/end, status, teacher
 * note) and the descriptive report card (قبول/مردود + the teacher's text).
 *
 * One API: GET /api/education/portal/?student=<id>
 *   student  → their own person (the param may be omitted);
 *   guardian → one of their ACTIVE wards; the `students` array in the
 *   response powers the child switcher. The server resolves scope — this
 *   script never builds URLs to arbitrary students.
 */
(function () {
  'use strict';

  var PORTAL = '/api/education/portal/';
  var STATUS_LABEL = { present: 'حاضر', absent: 'غایب', late: 'تأخیر', excused: 'موجه' };

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function pn(s) { return window.persianNumbers ? window.persianNumbers(s) : s; }
  function jal(iso) { return (window.penISOToJalali ? window.penISOToJalali(iso) : iso) || '—'; }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (r) {
        return r.json().then(function (b) {
          if (r.ok) return b;
          throw Object.assign(new Error(b.detail || b.error || ('HTTP ' + r.status)), { status: r.status, body: b });
        });
      });
  }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }
  function param(name) { return new URLSearchParams(location.search).get(name) || ''; }

  var $switchRow = document.getElementById('lp-switch-row');
  var $switch = document.getElementById('lp-switch');
  var $ring = document.getElementById('lp-ring');
  var $rate = document.getElementById('lp-rate');
  var $onTimeRate = document.getElementById('lp-on-time-rate');
  var $total = document.getElementById('lp-total');
  var $cards = document.getElementById('lp-cards');
  var $sessions = document.getElementById('lp-sessions');
  var $filter = document.getElementById('lp-filter');
  var $pdfLink = document.getElementById('lp-pdf-link');
  var $smsButton = document.getElementById('lp-sms-button');
  var $schedule = document.getElementById('lp-schedule');
  var $scheduleUpdated = document.getElementById('lp-schedule-updated');

  var current = [];   // sessions of the loaded student (for client-side filter)

  function renderSwitch(students, activeId) {
    if (!students || students.length < 2) { $switchRow.hidden = true; return; }
    $switchRow.hidden = false;
    $switch.innerHTML = students.map(function (s) {
      var on = s.id === activeId;
      return '<button type="button" class="btn btn-sm ' + (on ? 'btn-primary' : 'btn-outline-primary') + '"' +
        ' data-student="' + esc(s.id) + '">' + esc(s.name) +
        (s.relation === 'ward' ? '' : ' <span class="fs-13 opacity-75">(من)</span>') + '</button>';
    }).join('');
    $switch.querySelectorAll('[data-student]').forEach(function (b) {
      b.addEventListener('click', function () { load(b.dataset.student); });
    });
  }

  function renderAttendance(att) {
    var t = att.totals || {};
    ['present', 'absent', 'late', 'excused'].forEach(function (k) {
      var el = document.querySelector('[data-tot="' + k + '"]');
      if (el) el.textContent = pn(t[k] || 0);
    });
    var rate = att.rate || 0;
    var onTimeRate = att.on_time_rate || 0;
    $ring.style.setProperty('--pen-ring', rate);
    $rate.textContent = pn(rate) + '٪';
    if ($onTimeRate) $onTimeRate.textContent = pn(onTimeRate) + '٪';
    $total.textContent = 'از ' + pn(att.all || 0) + ' جلسه ثبت‌شده';

    current = att.sessions || [];
    renderSessions();
  }

  function renderSessions() {
    var want = $filter.value;
    var rows = current.filter(function (s) { return !want || s.status === want; });
    if (!rows.length) {
      $sessions.innerHTML = '<tr><td colspan="5"><div class="pen-empty">' +
        (current.length ? 'موردی با این فیلتر نیست.' : 'هنوز جلسه‌ای برای این دانش‌آموز ثبت نشده است.') +
        '</div></td></tr>';
      return;
    }
    $sessions.innerHTML = rows.map(function (s) {
      return '<tr>' +
        '<td class="fw-semibold" dir="ltr">' + esc(s.date_jalali || jal(s.date)) + '</td>' +
        '<td>' + (s.offering ? '<div class="fs-13 text-muted">' + esc(s.offering) + '</div>' : '') +
          'جلسه ' + pn(s.session_number) + '</td>' +
        '<td dir="ltr">' + pn(s.start) + '–' + pn(s.end) + '</td>' +
        '<td><span class="pen-status ' + esc(s.status) + '"><span class="dot"></span>' +
          esc(s.status_display || STATUS_LABEL[s.status] || s.status) + '</span></td>' +
        '<td class="fs-13 text-muted">' + esc(s.note || '—') + '</td>' +
        '</tr>';
    }).join('');
  }

  function renderCards(cards) {
    if (!cards || !cards.length) {
      $cards.innerHTML = '<div class="pen-empty py-5"><p class="mb-0 fs-14">کارنامه‌ای برای این دانش‌آموز صادر نشده است.</p></div>';
      return;
    }
    $cards.innerHTML = '<ul class="list-unstyled mb-0">' + cards.map(function (c) {
      return '<li class="border-bottom px-3 py-3">' +
        '<div class="d-flex align-items-center gap-2 flex-wrap">' +
          '<span class="fw-semibold flex-grow-1">' + esc(c.offering || '—') +
            (c.lesson ? ' <span class="fs-13 text-muted">· ' + esc(c.lesson) + '</span>' : '') + '</span>' +
          '<span class="pen-result ' + esc(c.result) + '">' +
            '<i data-lucide="' + (c.result === 'passed' ? 'check' : 'x') + '" class="size-4"></i>' +
            esc(c.result_display || c.result) + '</span>' +
          '<span class="fs-13 text-muted" dir="ltr">' + esc(jal(c.date)) + '</span>' +
        '</div>' +
        '<p class="fs-14 mt-2 mb-0" style="white-space:pre-wrap">' + esc(c.teacher_note || '') + '</p>' +
        '</li>';
    }).join('') + '</ul>';
    icons();
  }

  function renderSchedule(schedule) {
    var days = (schedule && schedule.days) || [];
    var rows = [];
    days.forEach(function (day) {
      (day.sessions || []).forEach(function (s) {
        rows.push({ day: day.date_jalali || jal(day.date), session: s });
      });
    });
    if (!rows.length) {
      $schedule.innerHTML = '<div class="pen-empty py-4">برای ۳۰ روز آینده جلسه‌ای در برنامه ثبت نشده است.</div>';
      $scheduleUpdated.textContent = '';
      return;
    }
    var changed = rows.some(function (r) { return Number(r.session.schedule_version || 1) > 1; });
    $scheduleUpdated.textContent = changed ? 'برنامهٔ به‌روزشده' : '';
    $schedule.innerHTML = '<div class="table-responsive"><table class="table table-hover align-middle mb-0"><thead class="table-light"><tr>' +
      '<th>تاریخ</th><th>موضوع درس</th><th>ساعت</th><th>محل</th><th>آخرین تغییر</th><th>ضمیمه</th></tr></thead><tbody>' +
      rows.map(function (r) {
        var s = r.session;
        var materials = (s.materials || []).map(function (m) {
          return '<a href="' + esc(m.url || '#') + '" target="_blank" rel="noopener" class="d-block fs-13">' + esc(m.title) + '</a>';
        }).join('') || '—';
        var changedLabel = 'بدون تغییر';
        if (Number(s.schedule_version || 1) > 1) {
          var stamp = s.schedule_updated_at ? new Date(s.schedule_updated_at).toLocaleString('fa-IR', { dateStyle: 'short', timeStyle: 'short' }) : '';
          changedLabel = 'نسخهٔ ' + pn(s.schedule_version) + (stamp ? ' · ' + stamp : '');
        }
        return '<tr><td class="fw-semibold" dir="ltr">' + esc(r.day) + '</td>' +
          '<td><div class="fw-semibold">' + esc(s.topic || s.title || 'موضوع جلسه ثبت نشده') + '</div>' +
          (Number(s.schedule_version || 1) > 1 ? '<span class="badge bg-warning-subtle text-warning mt-1">برنامه تغییر کرده</span>' : '') + '</td>' +
          '<td dir="ltr">' + pn(s.start || '') + '–' + pn(s.end || '') + '</td>' +
          '<td>' + esc(s.location || '—') + '</td><td class="fs-13 text-muted">' + esc(changedLabel) + '</td><td>' + materials + '</td></tr>';
      }).join('') + '</tbody></table></div>';
    icons();
  }

  function load(studentId) {
    var url = PORTAL + (studentId ? '?student=' + encodeURIComponent(studentId) : '');
    $cards.innerHTML = '<div class="pen-loading">در حال بارگذاری…</div>';
    $sessions.innerHTML = '<tr><td colspan="5"><div class="pen-loading">در حال بارگذاری…</div></td></tr>';
    get(url).then(function (d) {
      renderSwitch(d.students, d.student && d.student.id);
      renderAttendance(d.attendance || {});
      renderCards(d.report_cards || []);
      renderSchedule(d.schedule || {});
      var selected = d.student && d.student.id;
      if ($pdfLink) $pdfLink.href = '/api/education/portal/report-card/?format=pdf&student=' + encodeURIComponent(selected || '');
      if ($smsButton) $smsButton.dataset.student = selected || '';
    }).catch(function (e) {
      if (e.status === 403 && e.body && e.body.students) {
        renderSwitch(e.body.students, null);
        $cards.innerHTML = '<div class="pen-empty py-5"><p class="mb-0 fs-14">' + esc(e.message) + '</p></div>';
        $sessions.innerHTML = '<tr><td colspan="5"><div class="pen-empty">داده‌ای قابل نمایش نیست.</div></td></tr>';
      } else {
        toast(e.message, 'danger');
      }
    });
  }

  $filter.addEventListener('change', renderSessions);

  if ($smsButton) {
    $smsButton.addEventListener('click', function () {
      var studentId = $smsButton.dataset.student || '';
      $smsButton.disabled = true;
      fetch('/api/education/portal/report-card/', {
        method: 'POST', credentials: 'same-origin',
        headers: Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}),
        body: JSON.stringify({ student: studentId, channel: 'sms' })
      }).then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
        .then(function (res) { if (!res.ok) throw new Error(res.b.detail || 'ارسال پیامک انجام نشد.'); toast(res.b.message || 'پیامک ارسال شد.', 'success'); })
        .catch(function (e) { toast(e.message, 'danger'); })
        .finally(function () { $smsButton.disabled = false; });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    load(param('student') || '');
    icons();
  });
})();
