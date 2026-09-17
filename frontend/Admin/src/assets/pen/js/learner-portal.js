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

  function load(studentId) {
    var url = PORTAL + (studentId ? '?student=' + encodeURIComponent(studentId) : '');
    $cards.innerHTML = '<div class="pen-loading">در حال بارگذاری…</div>';
    $sessions.innerHTML = '<tr><td colspan="5"><div class="pen-loading">در حال بارگذاری…</div></td></tr>';
    get(url).then(function (d) {
      renderSwitch(d.students, d.student && d.student.id);
      renderAttendance(d.attendance || {});
      renderCards(d.report_cards || []);
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

  document.addEventListener('DOMContentLoaded', function () {
    load(param('student') || '');
    icons();
  });
})();
