/*
 * Pen LMS — teacher portal dashboard.
 *
 * Reads two scoped APIs:
 *   GET /api/education/teacher/classes/   → offerings where instructor == me
 *   GET /api/education/calendar/me/       → my own week (teacher perspective)
 * No management data is ever fetched here — the class cards and the agenda
 * are the whole surface (task spec §1.1).
 */
(function () {
  'use strict';

  var CLASSES = '/api/education/teacher/classes/';
  var AGENDA = '/api/education/calendar/me/';
  var contentSessionId = '';
  var contentModal = null;

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function pn(s) { return window.persianNumbers ? window.persianNumbers(s) : s; }
  function jal(iso) { return (window.penISOToJalali ? window.penISOToJalali(iso) : iso) || '—'; }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (r) {
        return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); });
      });
  }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }

  var DAY_NAMES = { sat: 'شنبه', sun: 'یکشنبه', mon: 'دوشنبه', tue: 'سه‌شنبه', wed: 'چهارشنبه', thu: 'پنجشنبه', fri: 'جمعه' };

  // ── class cards ─────────────────────────────────────────────────────
  function renderClasses(classes) {
    var $box = document.getElementById('td-classes');
    if (!$box) return;
    if (!classes.length) {
      $box.innerHTML = '<div class="col-12"><div class="pen-empty">' +
        '<i data-lucide="school" class="d-block mb-2" style="width:2rem;height:2rem;margin-inline:auto"></i>' +
        '<p class="mb-0">هنوز کلاسی به شما تخصیص داده نشده است.</p></div></div>';
      icons();
      return;
    }
    $box.innerHTML = classes.map(function (c) {
      var sched = (c.schedule && c.schedule.days) ? c.schedule.days : [];
      var time = (c.schedule && c.schedule.start) ? pn(c.schedule.start) + ' تا ' + pn(c.schedule.end || '—') : '';
      var next = c.stats && c.stats.next ? jal(c.stats.next) : '';
      var upcoming = (c.sessions || []).filter(function (s) { return !s.past; });
      var past = (c.sessions || []).filter(function (s) { return s.past; });
      var pend = (c.stats && c.stats.not_recorded) || 0;
      return '' +
        '<div class="col-12 col-lg-6">' +
        '  <div class="pen-class-card p-3 h-100">' +
        '    <div class="d-flex align-items-start gap-2">' +
        '      <div class="flex-grow-1 overflow-hidden">' +
        '        <h6 class="mb-1 text-truncate">' + esc(c.title || c.course) + '</h6>' +
        '        <p class="mb-2 fs-13 text-muted text-truncate">' + esc(c.course) +
                     (c.location ? ' · <i data-lucide="map-pin" class="size-3 d-inline-block align-middle"></i> ' + esc(c.location) : '') + '</p>' +
        '      </div>' +
        (pend ? '<span class="badge text-bg-warning flex-shrink-0">' + pn(pend) + ' جلسه بی‌حضور</span>'
              : '<span class="badge text-bg-success-subtle text-success-emphasis flex-shrink-0">روشن</span>') +
        '    </div>' +
        (sched.length || time
          ? '<div class="pen-week-strip mb-2">' +
              sched.map(function (d) { return '<span class="pen-week-chip">' + esc(DAY_NAMES[d] || d) + '</span>'; }).join('') +
              (time ? '<span class="pen-week-chip">' + esc(time) + '</span>' : '') +
            '</div>'
          : '') +
        '    <div class="d-flex fs-13 text-muted gap-3 mb-2 flex-wrap">' +
        '      <span><i data-lucide="users" class="size-4 d-inline-block align-middle ms-1"></i>' + pn(c.roster_size || 0) + ' دانش‌آموز</span>' +
        '      <span><i data-lucide="calendar-check" class="size-4 d-inline-block align-middle ms-1"></i>' + pn((c.stats && c.stats.held) || 0) + ' جلسه برگزارشده</span>' +
        (next ? '<span><i data-lucide="calendar-clock" class="size-4 d-inline-block align-middle ms-1"></i>بعدی: ' + esc(next) + '</span>' : '') +
        '    </div>' +
        (upcoming.length || past.length
          ? '<div class="list-group list-group-flush border-top" style="max-height:150px;overflow-y:auto">' +
              upcoming.slice(0, 3).map(function (s) {
                return '<div class="list-group-item d-flex align-items-center gap-2 px-0 py-2">' +
                  '<span class="badge text-bg-primary-subtle text-primary-emphasis flex-shrink-0">جلسه ' + pn(s.number) + '</span>' +
                  '<span class="fs-13 flex-grow-1">' + esc(jal(s.date)) + ' · ' + pn(s.start) + '–' + pn(s.end) + '</span>' +
                  '<a href="/workspace/teacher/attendance/?class=' + encodeURIComponent(c.id) + '&session=' + encodeURIComponent(s.id) + '" class="btn btn-sm btn-outline-primary flex-shrink-0" title="حضور و غیاب"><i data-lucide="user-check" class="size-4"></i></a>' +
                  '<button type="button" class="btn btn-sm btn-outline-secondary flex-shrink-0 td-content-btn" data-content-session="' + esc(s.id) + '" title="موضوع و ضمیمه"><i data-lucide="book-open-edit" class="size-4"></i></button>' +
                  '</div>';
              }).join('') +
              (past.length
                ? '<a href="/workspace/teacher/attendance/?class=' + encodeURIComponent(c.id) + '&session=' + encodeURIComponent(past[past.length - 1].id) + '"' +
                  ' class="list-group-item list-group-item-action d-flex align-items-center gap-2 px-0 py-2 text-muted">' +
                  '<span class="badge text-bg-secondary-subtle text-secondary-emphasis flex-shrink-0">ویرایش</span>' +
                  '<span class="fs-13 flex-grow-1">آخرین جلسه گذشته: ' + esc(jal(past[past.length - 1].date)) + ' (جلسه ' + pn(past[past.length - 1].number) + ')</span>' +
                  '<i data-lucide="pencil" class="size-4"></i></a>'
                : '') +
            '</div>'
          : '<p class="fs-13 text-muted mb-0">جلسه‌ای برای این کلاس ساخته نشده است.</p>') +
        '  </div>' +
        '</div>';
    }).join('');
    icons();
    bindContentButtons();
  }

  function showContentStatus(message, kind) {
    var box = document.getElementById('td-content-status');
    if (!box) return;
    box.className = 'alert alert-' + (kind || 'info');
    box.textContent = message;
    box.classList.remove('d-none');
  }

  function renderMaterials(rows) {
    var box = document.getElementById('td-material-list');
    if (!box) return;
    box.innerHTML = rows.length ? rows.map(function (m) {
      return '<div class="d-flex align-items-center gap-2 border rounded p-2"><i data-lucide="paperclip" class="size-4 text-muted"></i><a href="' + esc(m.public_url || m.url || '#') + '" target="_blank" rel="noopener" class="flex-grow-1">' + esc(m.title) + '</a></div>';
    }).join('') : '<div class="text-muted fs-13">هنوز ضمیمه‌ای برای این جلسه ثبت نشده است.</div>';
    icons();
  }

  function openContent(sessionId) {
    contentSessionId = sessionId;
    var topic = document.getElementById('td-content-topic');
    var status = document.getElementById('td-content-status');
    if (status) status.classList.add('d-none');
    if (topic) topic.value = '';
    if (!contentModal) contentModal = new bootstrap.Modal(document.getElementById('td-content-modal'));
    contentModal.show();
    get('/api/education/sessions/' + encodeURIComponent(sessionId) + '/materials/')
      .then(function (d) { if (topic) topic.value = d.topic || ''; renderMaterials(d.materials || []); })
      .catch(function (e) { showContentStatus(e.message, 'danger'); });
  }

  function bindContentButtons() {
    document.querySelectorAll('[data-content-session]').forEach(function (button) {
      button.addEventListener('click', function () { openContent(button.dataset.contentSession); });
    });
  }

  function saveContent() {
    var topic = (document.getElementById('td-content-topic').value || '').trim();
    var title = (document.getElementById('td-material-title').value || '').trim();
    var url = (document.getElementById('td-material-url').value || '').trim();
    fetch('/api/education/sessions/' + encodeURIComponent(contentSessionId) + '/materials/', {
      method: 'PATCH', credentials: 'same-origin',
      headers: Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}),
      body: JSON.stringify({ topic: topic })
    }).then(function (r) { return r.json().then(function (b) { if (!r.ok) throw new Error(b.detail || b.error || 'ذخیره انجام نشد.'); return b; }); })
      .then(function () {
        if (!title && !url) return null;
        return fetch('/api/education/sessions/' + encodeURIComponent(contentSessionId) + '/materials/', {
          method: 'POST', credentials: 'same-origin',
          headers: Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}),
          body: JSON.stringify({ title: title, url: url, kind: 'link' })
        }).then(function (r) { return r.json().then(function (b) { if (!r.ok) throw new Error(b.detail || b.error || 'افزودن ضمیمه انجام نشد.'); return b; }); });
      })
      .then(function () {
        document.getElementById('td-material-title').value = '';
        document.getElementById('td-material-url').value = '';
        showContentStatus('موضوع جلسه ذخیره شد.', 'success');
        return get('/api/education/sessions/' + encodeURIComponent(contentSessionId) + '/materials/');
      })
      .then(function (d) { renderMaterials(d.materials || []); })
      .catch(function (e) { showContentStatus(e.message, 'danger'); });
  }

  // ── KPI strip ───────────────────────────────────────────────────────
  function renderStats(classes) {
    var total = classes.length;
    var upcoming = 0, pending = 0, students = 0;
    classes.forEach(function (c) {
      upcoming += (c.stats && c.stats.upcoming) || 0;
      pending += (c.stats && c.stats.not_recorded) || 0;
      students += c.roster_size || 0;
    });
    var map = { classes: total, upcoming: upcoming, pending: pending, students: students };
    Object.keys(map).forEach(function (k) {
      var el = document.querySelector('[data-td-stat="' + k + '"]');
      if (el) el.textContent = pn(map[k]);
    });
  }

  // ── agenda (next 7 days, teacher perspective) ───────────────────────
  function renderAgenda(data) {
    var $box = document.getElementById('td-agenda');
    if (!$box) return;
    var sessions = (data && data.teacher && data.teacher.sessions) || [];
    if (!sessions.length) {
      $box.innerHTML = '<div class="pen-empty"><p class="mb-0 fs-14">در هفت روز آینده جلسه‌ای ندارید.</p></div>';
      return;
    }
    var byDate = {};
    sessions.forEach(function (s) { (byDate[s.date] = byDate[s.date] || []).push(s); });
    var days = Object.keys(byDate).sort();
    $box.innerHTML = '<ul class="list-unstyled mb-0">' + days.map(function (d) {
      return '<li class="border-bottom px-3 py-2">' +
        '<div class="fs-13 fw-semibold text-primary mb-1">' + esc(jal(d)) + '</div>' +
        byDate[d].map(function (s) {
          return '<div class="d-flex align-items-center gap-2 py-1">' +
            '<span class="badge text-bg-light flex-shrink-0">' + pn(s.start) + '–' + pn(s.end) + '</span>' +
            '<span class="fs-13 flex-grow-1 text-truncate">' + esc(s.title || '') +
              (s.location ? ' <span class="text-muted">· ' + esc(s.location) + '</span>' : '') + '</span>' +
            '<span class="fs-13 text-muted flex-shrink-0">جلسه ' + pn(s.number) + '</span>' +
            '<a href="' + esc(s.attendance_url || ('/workspace/teacher/attendance/?session=' + s.id)) + '"' +
              ' class="btn btn-sm btn-outline-primary flex-shrink-0" title="حضور این جلسه">' +
              '<i data-lucide="user-check" class="size-4"></i></a>' +
            '</div>';
        }).join('') +
        '</li>';
    }).join('') + '</ul>';
    icons();
  }

  // ── boot ────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('td-content-save').addEventListener('click', saveContent);
    var today = new Date();
    var from = today.toISOString().slice(0, 10);
    var toD = new Date(today.getTime() + 7 * 86400000);
    var to = toD.toISOString().slice(0, 10);

    get(CLASSES)
      .then(function (d) {
        var classes = d.results || [];
        renderClasses(classes);
        renderStats(classes);
      })
      .catch(function (e) {
        var $box = document.getElementById('td-classes');
        if ($box) $box.innerHTML = '<div class="col-12"><div class="pen-empty text-danger">' + esc(e.message) + '</div></div>';
      });

    get(AGENDA + '?from=' + from + '&to=' + to)
      .then(renderAgenda)
      .catch(function () {
        var $box = document.getElementById('td-agenda');
        if ($box) $box.innerHTML = '<div class="pen-empty fs-13">تقویم در دسترس نیست.</div>';
      });
  });
})();
