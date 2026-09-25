/*
 * Pen LMS — unified business requests.
 *
 * This page speaks only to /api/forms/requests/. FormSubmission remains the
 * storage projection behind a request, but the browser renders the business
 * contract: request type, lifecycle, current stage, assigned work and the
 * server-authorized transitions.
 */
(function () {
  'use strict';

  var API = '/api/forms/requests/';
  var params = new URLSearchParams(window.location.search);
  var selectedId = params.get('id');
  var state = { status: '', search: '', page: 1 };
  var actionState = null;

  var STATUS_LABELS = {
    draft: 'پیش‌نویس', submitted: 'ارسال‌شده', in_review: 'در بررسی',
    awaiting_action: 'منتظر اقدام', changes_requested: 'نیازمند اصلاح',
    approved: 'تأییدشده', rejected: 'ردشده', cancelled: 'لغوشده',
    completed: 'تکمیل‌شده', blocked_assignment: 'بدون مسئول', archived: 'بایگانی‌شده',
  };
  var STATUS_BADGE = {
    draft: 'pen-badge-draft', submitted: 'pen-badge-submitted',
    in_review: 'pen-badge-processing', awaiting_action: 'pen-badge-processing',
    changes_requested: 'pen-badge-processing', approved: 'pen-badge-approved',
    rejected: 'pen-badge-rejected', cancelled: 'pen-badge-archived',
    completed: 'pen-badge-approved', blocked_assignment: 'pen-badge-rejected',
    archived: 'pen-badge-archived',
  };
  var ACTION_META = {
    approve: { label: 'تأیید', btn: 'btn-success', icon: 'check', comment: 'optional' },
    reject: { label: 'رد', btn: 'btn-danger', icon: 'x', comment: 'required' },
    return: { label: 'برگشت برای اصلاح', btn: 'btn-warning', icon: 'undo-2', comment: 'required' },
    request_changes: { label: 'درخواست اصلاح', btn: 'btn-warning', icon: 'undo-2', comment: 'required' },
    complete: { label: 'اتمام', btn: 'btn-primary', icon: 'flag', comment: 'optional' },
    submit: { label: 'ارسال', btn: 'btn-primary', icon: 'send', comment: 'optional' },
    cancel: { label: 'لغو درخواست', btn: 'btn-outline-danger', icon: 'ban', comment: 'required' },
  };
  var WORKFLOW_STATUS_LABELS = {
    running: 'در حال اجرا', completed: 'تکمیل‌شده', rejected: 'ردشده',
    cancelled: 'لغوشده', '': 'شروع نشده',
  };

  var $listView = document.getElementById('req-list-view');
  var $detailView = document.getElementById('req-detail-view');

  function esc(value) {
    return window.htmlEscape ? window.htmlEscape(value) : String(value == null ? '' : value)
      .replace(/[&<>"']/g, function (ch) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[ch];
      });
  }

  function headers(json) {
    return Object.assign(
      json ? { 'Content-Type': 'application/json' } : {},
      window.penCsrfHeader ? window.penCsrfHeader() : {}
    );
  }

  function notify(message, kind) {
    if (window.penToast) window.penToast(message, kind || 'info');
    else window.alert(message);
  }

  function icons() {
    if (window.penRenderIcons) window.penRenderIcons();
  }

  function fetchJson(url, options) {
    var config = Object.assign({ credentials: 'same-origin' }, options || {});
    config.headers = Object.assign({}, headers(!!config.body), config.headers || {});
    return fetch(url, config).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (body) {
        if (!response.ok) {
          var error = body.error || body.detail || body.message || ('خطا (' + response.status + ')');
          throw new Error(Array.isArray(error) ? error.join('؛ ') : String(error));
        }
        return body;
      });
    });
  }

  function postJson(url, body) {
    var key = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + '-' + Math.random();
    return fetchJson(url, {
      method: 'POST',
      headers: { 'Idempotency-Key': key },
      body: JSON.stringify(body || {}),
    });
  }

  function statusLabel(status) { return STATUS_LABELS[status] || status || '—'; }
  function statusBadge(status) { return STATUS_BADGE[status] || 'pen-badge-draft'; }

  function actionMeta(transition) {
    var name = String(transition.name || '').toLowerCase();
    var kind = String(transition.kind || '').toLowerCase();
    if (ACTION_META[kind]) return ACTION_META[kind];
    for (var key in ACTION_META) {
      if (name.indexOf(key) !== -1) return ACTION_META[key];
    }
    return {
      label: transition.name || 'اقدام',
      btn: 'btn-outline-primary',
      icon: 'arrow-left-right',
      comment: transition.requires_comment ? 'required' : 'optional',
    };
  }

  function displayValue(value) {
    if (value == null || value === '') return '—';
    if (Array.isArray(value)) return value.map(displayValue).join('، ');
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  }

  function schemaFieldMap(schema) {
    var map = {};
    (schema && schema.fields || []).forEach(function (field) {
      if (field && field.key) map[field.key] = field.label || field.key;
    });
    return map;
  }

  function renderRequestData(request) {
    var data = request.data || {};
    var labels = schemaFieldMap(request.form_schema);
    var keys = Object.keys(data);
    var html = '';
    if (request.form_schema) {
      html += '<div class="d-flex flex-wrap align-items-center gap-2 mb-3">' +
        '<span class="badge bg-primary-subtle text-primary">' + esc(request.form_schema.title) + '</span>' +
        '<span class="text-muted fs-13">نسخه ' + esc(request.form_schema.version) + '</span>' +
        (request.submission_id ? '<a class="btn btn-sm btn-outline-secondary ms-auto" href="/forms/submissions/' + esc(request.submission_id) + '/">جزئیات فرم و پیوست‌ها</a>' : '') +
        '</div>';
    }
    if (keys.length) {
      html += '<div class="table-responsive"><table class="table table-sm table-hover align-middle mb-0"><tbody>';
      keys.forEach(function (key) {
        html += '<tr><th scope="row" class="fw-normal text-muted" style="width:34%">' +
          esc(labels[key] || key) + '</th><td><span class="text-break">' + esc(displayValue(data[key])) + '</span></td></tr>';
      });
      html += '</tbody></table></div>';
    } else {
      html += '<div class="pen-empty py-4"><i data-lucide="file-question" class="size-7 opacity-50"></i><p class="mb-0 mt-2">اطلاعاتی در فرم ثبت نشده است.</p></div>';
    }
    if (request.notes) {
      html += '<div class="alert alert-light border mt-3 mb-0"><strong>یادداشت:</strong> ' + esc(request.notes) + '</div>';
    }
    return html;
  }

  function renderHistory(history) {
    if (!history || !history.length) {
      return '<li class="text-muted fs-14">هنوز اقدامی در گردش‌کار ثبت نشده است.</li>';
    }
    return history.map(function (item) {
      var state = item.to_state_title || item.to_state_code || '';
      return '<li class="pen-timeline-item">' +
        '<div class="fw-semibold fs-14">' + esc(item.action) +
        (state ? ' <span class="text-muted">→ ' + esc(state) + '</span>' : '') + '</div>' +
        '<div class="fs-13 text-muted">' + esc(item.actor_username || 'سامانه') +
        ' · ' + esc(item.created_at || '—') + '</div>' +
        (item.comment ? '<div class="fs-14 mt-1 p-2 rounded bg-body-tertiary">' + esc(item.comment) + '</div>' : '') +
        '</li>';
    }).join('');
  }

  function renderPeople(request) {
    var people = ['<li><span class="text-muted fs-13">درخواست‌دهنده</span><br><strong>' +
      esc(request.requester_username || '—') + '</strong></li>'];
    (request.pending_tasks || []).forEach(function (task) {
      people.push('<li><span class="text-muted fs-13">مسئول مرحلهٔ ' + esc(task.state_title || task.state_code) +
        '</span><br><strong>' + esc(task.assignee_username || '—') + '</strong></li>');
    });
    return people.join('');
  }

  function actionButton(action, meta, transition) {
    return '<button type="button" class="btn ' + meta.btn + ' w-100" data-request-action="' + esc(action) + '"' +
      (transition ? ' data-transition-id="' + esc(transition.id) + '" data-requires-comment="' + (!!transition.requires_comment) + '"' : '') + '>' +
      '<i data-lucide="' + esc(meta.icon) + '" class="size-4 me-1"></i>' + esc(meta.label) + '</button>';
  }

  function renderActions(request) {
    var $box = document.getElementById('rd-actions');
    $box.innerHTML = '';
    var actions = request.actions || {};
    if (actions.edit && request.submission_id) {
      $box.insertAdjacentHTML('beforeend',
        '<a class="btn btn-outline-primary w-100" href="/forms/submissions/' + esc(request.submission_id) + '/edit/">' +
        '<i data-lucide="pencil" class="size-4 me-1"></i> ویرایش و اصلاح فرم</a>');
    }
    if (actions.submit) $box.insertAdjacentHTML('beforeend', actionButton('submit', ACTION_META.submit, null));
    (request.available_transitions || []).forEach(function (transition) {
      $box.insertAdjacentHTML('beforeend', actionButton('transition', actionMeta(transition), transition));
    });
    if (!$box.children.length) {
      $box.innerHTML = '<p class="text-muted mb-0 fs-14">اقدامی برای شما مجاز نیست.</p>';
    }
    $box.querySelectorAll('[data-request-action]').forEach(function (button) {
      button.addEventListener('click', function () {
        openAction(button.dataset.requestAction, button.dataset.transitionId || null, button.dataset.requiresComment === 'true');
      });
    });
  }

  function openAction(action, transitionId, requiresComment) {
    actionState = { action: action, transitionId: transitionId, requiresComment: requiresComment };
    var meta = action === 'submit' ? ACTION_META.submit : (action === 'cancel' ? ACTION_META.cancel : { label: 'اقدام گردش‌کار' });
    var transition = (window.__PEN_REQUEST_TRANSITIONS__ || []).filter(function (item) { return item.id === transitionId; })[0];
    if (transition) meta = actionMeta(transition);
    document.getElementById('action-label').textContent = meta.label;
    document.getElementById('action-hint').textContent = requiresComment ? 'برای این اقدام توضیح الزامی است.' : 'در صورت نیاز توضیح خود را ثبت کنید.';
    document.getElementById('action-comment').value = '';
    document.getElementById('action-error').hidden = true;
    bootstrap.Modal.getOrCreateInstance(document.getElementById('action-modal')).show();
  }

  function failure(message) {
    var $error = document.getElementById('action-error');
    $error.querySelector('ul').innerHTML = '<li>' + esc(message) + '</li>';
    $error.hidden = false;
  }

  function executeAction() {
    if (!actionState || !selectedId) return;
    var comment = document.getElementById('action-comment').value.trim();
    if (actionState.requiresComment && !comment) {
      failure('ثبت توضیح برای این اقدام الزامی است.');
      return;
    }
    var $button = document.getElementById('action-confirm');
    $button.disabled = true;
    var url = API + selectedId + '/';
    var payload = {};
    if (actionState.action === 'submit') url += 'submit/';
    else if (actionState.action === 'cancel') {
      url += 'cancel/';
      payload.reason = comment;
    } else {
      url += 'transition/';
      payload.transition_id = actionState.transitionId;
      payload.comment = comment;
    }
    postJson(url, payload).then(function () {
      bootstrap.Modal.getOrCreateInstance(document.getElementById('action-modal')).hide();
      openDetail(selectedId);
      notify('اقدام با موفقیت ثبت شد.', 'success');
    }).catch(function (error) {
      failure(error.message);
    }).finally(function () {
      $button.disabled = false;
    });
  }

  function renderListPage(data) {
    var $list = document.getElementById('req-list');
    var rows = data.results || [];
    if (!rows.length) {
      $list.innerHTML = '<div class="card"><div class="pen-empty"><i data-lucide="inbox" class="size-8 opacity-50"></i><p class="mb-0 mt-2">درخواستی با این مشخصات یافت نشد.</p></div></div>';
      return;
    }
    $list.innerHTML = rows.map(function (request) {
      var title = request.request_type_title || request.request_type_code || 'درخواست';
      var stage = request.current_state_title || request.current_state_code ?
        'مرحله: ' + (request.current_state_title || request.current_state_code) : 'هنوز وارد گردش‌کار نشده است';
      var number = request.tracking_number || request.request_number || request.id;
      return '<a class="card text-decoration-none wq-card" href="/workspace/requests/?id=' + encodeURIComponent(request.id) + '">' +
        '<div class="card-body d-flex flex-wrap align-items-center gap-3 py-3">' +
        '<div class="avatar size-10 rounded bg-primary-subtle text-primary flex-shrink-0"><i data-lucide="file-clock" class="size-5"></i></div>' +
        '<div class="flex-grow-1 overflow-hidden"><div class="fw-semibold text-truncate">' + esc(title) + '</div>' +
        '<div class="fs-13 text-muted text-truncate">' + esc(number) + ' · ' + esc(stage) + '</div>' +
        '<div class="fs-13 text-muted">درخواست‌دهنده: ' + esc(request.requester_username || '—') + ' · ' + esc(request.created_at || '—') + '</div></div>' +
        '<span class="pen-badge ' + statusBadge(request.status) + '">' + esc(statusLabel(request.status)) + '</span>' +
        '<i data-lucide="chevron-left" class="size-4 text-muted"></i></div></a>';
    }).join('');

    var $pager = document.getElementById('req-pager');
    $pager.innerHTML = '';
    [['قبلی', data.previous, -1], ['بعدی', data.next, 1]].forEach(function (item) {
      var li = document.createElement('li');
      li.className = 'page-item' + (item[1] ? '' : ' disabled');
      li.innerHTML = '<a class="page-link" href="#">' + item[0] + '</a>';
      if (item[1]) li.querySelector('a').addEventListener('click', function (event) {
        event.preventDefault();
        state.page = Math.max(1, state.page + item[2]);
        loadList();
      });
      $pager.appendChild(li);
    });
  }

  function loadList() {
    var $list = document.getElementById('req-list');
    $list.setAttribute('aria-busy', 'true');
    $list.innerHTML = '<div class="pen-loading">در حال بارگذاری درخواست‌ها…</div>';
    var query = new URLSearchParams({ page: state.page });
    if (state.status) query.set('status', state.status);
    if (state.search) query.set('search', state.search);
    fetchJson(API + '?' + query.toString()).then(renderListPage).catch(function (error) {
      $list.innerHTML = '<div class="alert alert-danger" role="alert">' + esc(error.message) + '</div>';
    }).finally(function () {
      $list.removeAttribute('aria-busy');
      icons();
    });
  }

  function openDetail(id) {
    selectedId = id;
    if ($listView) $listView.hidden = true;
    if ($detailView) $detailView.hidden = false;
    document.getElementById('rd-title').textContent = 'در حال بارگذاری…';
    fetchJson(API + id + '/').then(function (request) {
      var title = request.request_type_title || request.request_type_code || 'درخواست';
      document.getElementById('rd-title').textContent = title;
      var badge = document.getElementById('rd-status');
      badge.className = 'pen-badge ' + statusBadge(request.status);
      badge.textContent = statusLabel(request.status);
      document.getElementById('rd-meta').textContent =
        (request.tracking_number || request.request_number || '—') + ' · درخواست‌دهنده: ' +
        (request.requester_username || '—') + ' · ثبت: ' + (request.created_at || '—');
      document.getElementById('rd-whonow-text').innerHTML =
        'مرحلهٔ فعلی: <strong>' + esc(request.current_state_title || request.current_state_code || 'پیش‌نویس') + '</strong>' +
        ' · وضعیت گردش‌کار: <strong>' + esc(WORKFLOW_STATUS_LABELS[request.workflow_status] || request.workflow_status || 'شروع نشده') + '</strong>';
      document.getElementById('rd-info').innerHTML = renderRequestData(request);
      document.getElementById('rd-timeline').innerHTML = renderHistory(request.history);
      document.getElementById('rd-people').innerHTML = renderPeople(request);
      var cancelButton = document.getElementById('rd-cancel');
      cancelButton.hidden = !(request.actions && request.actions.cancel);
      cancelButton.onclick = function () { openAction('cancel', null, true); };
      window.__PEN_REQUEST_TRANSITIONS__ = request.available_transitions || [];
      renderActions(request);
      icons();
    }).catch(function (error) {
      notify(error.message, 'danger');
    });
  }

  var $confirm = document.getElementById('action-confirm');
  if ($confirm) $confirm.addEventListener('click', executeAction);
  var $search = document.getElementById('req-search');
  if ($search) {
    var timer = null;
    $search.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        state.search = $search.value.trim();
        state.page = 1;
        loadList();
      }, 250);
    });
  }
  var $status = document.getElementById('req-status');
  if ($status) $status.addEventListener('change', function () {
    state.status = this.value;
    state.page = 1;
    loadList();
  });

  if (selectedId) openDetail(selectedId);
  else if ($listView) loadList();
})();
