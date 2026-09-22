/*
 * Pen LMS — کارهای من (work queue / cartable).
 *
 * Task-oriented UI over the existing tasks API: the user sees "work waiting
 * for me", never WorkflowTask/Instance vocabulary. Tabs:
 *   pending → در حال انجام      (status=pending)
 *   soon    → نزدیک سررسید      (pending, due within 48h)
 *   overdue → تأخیرکرده         (overdue=true)
 *   drafts  → پیش‌نویس‌ها        (my draft form submissions)
 *   done    → انجام‌شده          (status=completed)
 * Each card links to the request detail (/workspace/requests/?id=…).
 * SLA coloring: server is_overdue + due window → badge text + color + icon.
 */
(function () {
  'use strict';

  var TASKS = '/api/tasks/';
  var FORMS = '/api/forms/submissions/?status=draft&ordering=-created_at';
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  var tab = 'pending';
  var q = '';
  var $list = document.getElementById('wq-list');
  var $search = document.getElementById('wq-search');

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() { return window.penCsrfHeader ? window.penCsrfHeader() : {}; }

  function slaInfo(t) {
    // returns {cls, icon, text} — color is never the only signal
    if (t.is_overdue) return { cls: 'bg-danger-subtle text-danger', icon: 'alarm-minus', text: 'تأخیرکرده' };
    if (!t.due_date) return { cls: 'bg-secondary-subtle text-secondary', icon: 'infinity', text: 'بدون سررسید' };
    var due = new Date(String(t.due_date).replace(' ', 'T'));
    if (isNaN(due.getTime())) return { cls: 'bg-secondary-subtle text-secondary', icon: 'clock', text: '' };
    var hrs = (due.getTime() - Date.now()) / 3600000;
    if (hrs <= 48) return { cls: 'bg-warning-subtle text-warning', icon: 'clock-3', text: 'نزدیک سررسید' };
    return { cls: 'bg-success-subtle text-success', icon: 'check-circle', text: 'در محدوده' };
  }

  function cardForTask(t) {
    var sla = slaInfo(t);
    var stateLabel = ({ pending: 'در انتظار اقدام', completed: 'انجام شد', skipped: 'رد شد' })[t.status] || t.status;
    return '<a class="card wq-card text-decoration-none" href="/workspace/requests/?id=' + encodeURIComponent(t.instance_id) + '">' +
      '<div class="card-body d-flex flex-wrap align-items-center gap-3 py-3">' +
      '<div class="avatar size-11 rounded bg-primary-subtle text-primary flex-shrink-0"><i data-lucide="clipboard-list" class="size-5"></i></div>' +
      '<div class="flex-grow-1 overflow-hidden">' +
      '<div class="fw-semibold text-truncate">' + esc(t.instance_title || 'بدون عنوان') + '</div>' +
      '<div class="fs-13 text-muted">' + esc(stateLabel) + ' · مرحله: ' + esc(t.state_code || '—') + '</div>' +
      '</div>' +
      '<div class="text-start">' +
      (sla.text ? '<span class="badge ' + sla.cls + ' mb-1"><i data-lucide="' + sla.icon + '" class="size-3 me-1"></i>' + sla.text + '</span>' : '') +
      '<div class="fs-13 text-muted">سررسید: ' + esc(t.due_date || '—') + '</div>' +
      '</div>' +
      '<i data-lucide="chevron-left" class="size-4 text-muted"></i>' +
      '</div></a>';
  }

  function cardForDraft(s) {
    return '<a class="card wq-card text-decoration-none" href="/forms/submissions/' + encodeURIComponent(s.id) + '/edit/">' +
      '<div class="card-body d-flex flex-wrap align-items-center gap-3 py-3">' +
      '<div class="avatar size-11 rounded bg-secondary-subtle text-secondary flex-shrink-0"><i data-lucide="file-pen" class="size-5"></i></div>' +
      '<div class="flex-grow-1 overflow-hidden">' +
      '<div class="fw-semibold text-truncate">' + esc(s.form_schema_title || s.form_schema || 'فرم') + '</div>' +
      '<div class="fs-13 text-muted">پیش‌نویس · ' + esc(s.created_at || '') + '</div>' +
      '</div>' +
      '<span class="pen-badge pen-badge-draft">پیش‌نویس</span>' +
      '<i data-lucide="chevron-left" class="size-4 text-muted"></i>' +
      '</div></a>';
  }

  function setLoading() {
    $list.innerHTML = '<div class="pen-loading">در حال بارگذاری…</div>';
  }
  function setEmpty(msg) {
    $list.innerHTML = '<div class="card"><div class="pen-empty"><i data-lucide="check-circle-2" class="size-8 opacity-50"></i><p class="mb-0 mt-2">' + esc(msg) + '</p></div></div>';
    if (window.penRenderIcons) window.penRenderIcons();
  }

  function qs(params) {
    return new URLSearchParams(params).toString();
  }

  function matches(t) {
    if (!q) return true;
    var hay = ((t.instance_title || '') + ' ' + (t.state_code || '') + ' ' + (t.workflow_definition_code || '')).toLowerCase();
    return hay.indexOf(q.toLowerCase()) !== -1;
  }

  function loadTasks(params) {
    return fetch(TASKS + '?' + qs(params), { credentials: 'same-origin', headers: headers() })
      .then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || ('HTTP ' + r.status)); }); });
  }

  function loadDrafts() {
    return fetch(FORMS, { credentials: 'same-origin', headers: headers() })
      .then(function (r) { return r.ok ? r.json() : { results: [] }; });
  }

  function render() {
    setLoading();
    var p;
    if (tab === 'pending') p = { status: 'pending', ordering: 'due_date' };
    else if (tab === 'soon') p = { status: 'pending', ordering: 'due_date' };
    else if (tab === 'overdue') p = { status: 'pending', overdue: 'true', ordering: 'due_date' };
    else if (tab === 'done') p = { status: 'completed', ordering: '-created_at' };
    else p = null;

    if (tab === 'drafts') {
      loadDrafts().then(function (d) {
        var rows = (d.results || []).filter(function (s) {
          return !q || ((s.form_schema_title || s.form_schema || '')).toLowerCase().indexOf(q.toLowerCase()) !== -1;
        });
        if (!rows.length) return setEmpty('پیش‌نویسی ندارید.');
        $list.innerHTML = rows.map(cardForDraft).join('');
      }).catch(function (e) { $list.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>'; })
        .finally(function () { if (window.penRenderIcons) window.penRenderIcons(); });
      return;
    }

    loadTasks(p || {}).then(function (d) {
      var rows = (d.results || []).filter(matches);
      if (tab === 'soon') {
        // keep only items due within 48h (server has no window filter)
        rows = rows.filter(function (t) {
          if (!t.due_date || t.is_overdue) return false;
          var due = new Date(String(t.due_date).replace(' ', 'T'));
          return !isNaN(due.getTime()) && (due.getTime() - Date.now()) / 3600000 <= 48;
        });
      }
      if (tab === 'overdue') rows = rows.filter(function (t) { return t.is_overdue; });
      if (!rows.length) return setEmpty(tab === 'done' ? 'کاری انجام‌نشده دارید؟ همه انجام شده!' : 'کاری منتظر شما نیست — عالی!');
      $list.innerHTML = rows.map(cardForTask).join('');
    }).catch(function (e) {
      $list.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>';
    }).finally(function () { if (window.penRenderIcons) window.penRenderIcons(); });
  }

  function loadKpis() {
    // one call each; failures leave dash placeholders
    var set = function (id, v) { var el = document.getElementById(id); if (el) el.textContent = window.persianNumbers(v); };
    loadTasks({ status: 'pending' }).then(function (d) {
      var rows = d.results || [];
      set('kpi-open', d.count != null ? d.count : rows.length);
      var soon = 0, overdue = 0;
      rows.forEach(function (t) {
        if (t.is_overdue) overdue++;
        else if (t.due_date) {
          var due = new Date(String(t.due_date).replace(' ', 'T'));
          if (!isNaN(due.getTime()) && (due.getTime() - Date.now()) / 3600000 <= 48) soon++;
        }
      });
      set('kpi-soon', soon);
      set('kpi-overdue', overdue);
    }).catch(function () { });
    loadDrafts().then(function (d) { set('kpi-drafts', d.count != null ? d.count : (d.results || []).length); }).catch(function () { });
  }

  // tabs
  document.querySelectorAll('[data-tab]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('[data-tab]').forEach(function (b) { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      tab = btn.dataset.tab;
      render();
    });
  });

  var timer = null;
  $search.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { q = $search.value.trim(); render(); }, 250);
  });

  if ($list) { render(); loadKpis(); }
})();
