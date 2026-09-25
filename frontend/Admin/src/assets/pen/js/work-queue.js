/*
 * Pen LMS — unified work queue.
 *
 * The inbox is backed by the same Request aggregate used by the request
 * page. Assigned WorkflowTask rows are only the operational projection that
 * tells us whose turn it is; drafts and completed requests stay in the same
 * response so the UI has one contract and one vocabulary.
 */
(function () {
  'use strict';

  var API = '/api/forms/my-work/';
  var tab = 'pending';
  var query = '';
  var snapshot = { requests: [], tasks: [] };
  var $list = document.getElementById('wq-list');
  var $search = document.getElementById('wq-search');

  var STATUS_LABELS = {
    draft: 'پیش‌نویس', submitted: 'ارسال‌شده', in_review: 'در بررسی',
    awaiting_action: 'منتظر اقدام', changes_requested: 'نیازمند اصلاح',
    approved: 'تأییدشده', rejected: 'ردشده', cancelled: 'لغوشده',
    completed: 'تکمیل‌شده', archived: 'بایگانی‌شده',
  };
  var STATUS_BADGES = {
    draft: 'pen-badge-draft', submitted: 'pen-badge-submitted',
    in_review: 'pen-badge-processing', awaiting_action: 'pen-badge-processing',
    changes_requested: 'pen-badge-processing', approved: 'pen-badge-approved',
    rejected: 'pen-badge-rejected', cancelled: 'pen-badge-archived',
    completed: 'pen-badge-approved', archived: 'pen-badge-archived',
  };

  function esc(value) {
    return window.htmlEscape ? window.htmlEscape(value) : String(value == null ? '' : value)
      .replace(/[&<>"']/g, function (ch) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[ch];
      });
  }

  function headers() { return window.penCsrfHeader ? window.penCsrfHeader() : {}; }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }
  function statusLabel(value) { return STATUS_LABELS[value] || value || '—'; }
  function statusBadge(value) { return STATUS_BADGES[value] || 'pen-badge-draft'; }

  function fetchJson(url) {
    return fetch(url, { credentials: 'same-origin', headers: headers() }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (body) {
        if (!response.ok) throw new Error(body.error || body.detail || ('خطا (' + response.status + ')'));
        return body;
      });
    });
  }

  function setLoading() {
    $list.setAttribute('aria-busy', 'true');
    $list.innerHTML = '<div class="pen-loading">در حال بارگذاری کارهای شما…</div>';
  }

  function setEmpty(message) {
    $list.innerHTML = '<div class="card"><div class="pen-empty"><i data-lucide="check-circle-2" class="size-8 opacity-50"></i><p class="mb-0 mt-2">' + esc(message) + '</p></div></div>';
    icons();
  }

  function searchable(value) {
    return String(value || '').toLowerCase().indexOf(query.toLowerCase()) !== -1;
  }

  function requestTitle(request) {
    return request.request_type_title || request.request_type_code || 'درخواست';
  }

  function requestHref(requestId) {
    return requestId ? '/workspace/requests/?id=' + encodeURIComponent(requestId) : '/workspace/requests/';
  }

  function cardForTask(task) {
    var due = task.due_date ? 'سررسید: ' + task.due_date : 'بدون سررسید';
    var tone = task.is_overdue ? 'text-danger' : 'text-muted';
    return '<a class="card text-decoration-none wq-card" href="' + requestHref(task.request_id) + '">' +
      '<div class="card-body d-flex flex-wrap align-items-center gap-3 py-3">' +
      '<div class="avatar size-10 rounded bg-warning-subtle text-warning flex-shrink-0"><i data-lucide="clipboard-check" class="size-5"></i></div>' +
      '<div class="flex-grow-1 overflow-hidden"><div class="fw-semibold text-truncate">' + esc(task.instance_title || 'کار گردش‌کار') + '</div>' +
      '<div class="fs-13 text-muted">مرحله: ' + esc(task.state_code || '—') + ' · فرآیند: ' + esc(task.workflow_definition_code || '—') + '</div>' +
      '<div class="fs-13 ' + tone + '">' + esc(due) + '</div></div>' +
      '<span class="pen-badge ' + (task.is_overdue ? 'pen-badge-rejected' : 'pen-badge-processing') + '">' + (task.is_overdue ? 'تأخیرکرده' : 'منتظر اقدام') + '</span>' +
      '<i data-lucide="chevron-left" class="size-4 text-muted"></i></div></a>';
  }

  function cardForRequest(request) {
    return '<a class="card text-decoration-none wq-card" href="' + requestHref(request.id) + '">' +
      '<div class="card-body d-flex flex-wrap align-items-center gap-3 py-3">' +
      '<div class="avatar size-10 rounded bg-primary-subtle text-primary flex-shrink-0"><i data-lucide="file-clock" class="size-5"></i></div>' +
      '<div class="flex-grow-1 overflow-hidden"><div class="fw-semibold text-truncate">' + esc(requestTitle(request)) + '</div>' +
      '<div class="fs-13 text-muted">' + esc(request.tracking_number || request.request_number || request.id) + ' · ' + esc(request.current_state_title || request.current_state_code || 'پیش‌نویس') + '</div>' +
      '<div class="fs-13 text-muted">' + esc(request.created_at || '—') + '</div></div>' +
      '<span class="pen-badge ' + statusBadge(request.status) + '">' + esc(statusLabel(request.status)) + '</span>' +
      '<i data-lucide="chevron-left" class="size-4 text-muted"></i></div></a>';
  }

  function matchesTask(task) {
    return !query || searchable(task.instance_title) || searchable(task.state_code) || searchable(task.workflow_definition_code);
  }

  function matchesRequest(request) {
    return !query || searchable(requestTitle(request)) || searchable(request.request_number) || searchable(request.current_state_code);
  }

  function dueWithin48Hours(task) {
    if (!task.due_date || task.is_overdue) return false;
    var due = new Date(String(task.due_date).replace(' ', 'T'));
    return !isNaN(due.getTime()) && (due.getTime() - Date.now()) / 3600000 <= 48;
  }

  function render() {
    setLoading();
    var rows = [];
    if (tab === 'pending') rows = snapshot.tasks.filter(matchesTask);
    if (tab === 'soon') rows = snapshot.tasks.filter(function (task) { return dueWithin48Hours(task) && matchesTask(task); });
    if (tab === 'overdue') rows = snapshot.tasks.filter(function (task) { return task.is_overdue && matchesTask(task); });
    if (tab === 'drafts') rows = snapshot.requests.filter(function (request) { return request.status === 'draft' && matchesRequest(request); });
    if (tab === 'done') rows = snapshot.requests.filter(function (request) {
      return ['completed', 'approved', 'rejected', 'cancelled', 'archived'].indexOf(request.status) !== -1 && matchesRequest(request);
    });
    if (!rows.length) {
      setEmpty(tab === 'done' ? 'هنوز درخواست تکمیل‌شده‌ای در فهرست شما نیست.' : 'کاری منتظر شما نیست — عالی!');
      return;
    }
    $list.innerHTML = rows.map(function (row) {
      return tab === 'drafts' || tab === 'done' ? cardForRequest(row) : cardForTask(row);
    }).join('');
    $list.removeAttribute('aria-busy');
    icons();
  }

  function setKpi(id, value) {
    var element = document.getElementById(id);
    if (element) element.textContent = window.persianNumbers ? window.persianNumbers(value) : value;
  }

  function load() {
    setLoading();
    fetchJson(API).then(function (data) {
      snapshot.requests = data.requests || [];
      snapshot.tasks = data.tasks || [];
      var soon = snapshot.tasks.filter(dueWithin48Hours).length;
      var overdue = snapshot.tasks.filter(function (task) { return task.is_overdue; }).length;
      setKpi('kpi-open', snapshot.tasks.length);
      setKpi('kpi-soon', soon);
      setKpi('kpi-overdue', overdue);
      setKpi('kpi-drafts', snapshot.requests.filter(function (request) { return request.status === 'draft'; }).length);
      render();
    }).catch(function (error) {
      $list.innerHTML = '<div class="alert alert-danger" role="alert">' + esc(error.message) + '</div>';
      $list.removeAttribute('aria-busy');
    }).finally(icons);
  }

  document.querySelectorAll('[data-tab]').forEach(function (button) {
    button.addEventListener('click', function () {
      document.querySelectorAll('[data-tab]').forEach(function (item) {
        item.classList.remove('active');
        item.setAttribute('aria-selected', 'false');
      });
      button.classList.add('active');
      button.setAttribute('aria-selected', 'true');
      tab = button.dataset.tab;
      render();
    });
  });

  if ($search) {
    var timer = null;
    $search.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        query = $search.value.trim();
        render();
      }, 250);
    });
  }

  if ($list) load();
})();
