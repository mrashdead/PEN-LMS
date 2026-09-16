/*
 * Pen LMS — درخواست‌ها (list + rich detail).
 *
 * The detail view is the heart of the task-oriented UX:
 *   • status in plain Persian + "whose turn is it?" (assignees of pending tasks)
 *   • workflow history as a Timeline (ActionLog)
 *   • action buttons rendered ONLY from /available-transitions/ — if the
 *     server doesn't authorize approve, no approve button exists
 *   • all executions go through the workflow engine endpoints
 * Server is the source of truth; this file renders what it returns.
 */
(function () {
  'use strict';

  var API = '/api/workflow/instances/';
  var TASKS = '/api/tasks/';
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  var STATUS_LABELS = {
    running: 'در جریان', completed: 'تکمیل‌شده',
    rejected: 'ردشده', cancelled: 'لغوشده',
  };
  var STATUS_BADGE = {
    running: 'pen-badge-submitted', completed: 'pen-badge-approved',
    rejected: 'pen-badge-rejected', cancelled: 'pen-badge-archived',
  };
  // friendly action naming (kind/name based; engine still authorizes)
  var ACTION_META = {
    approve: { label: 'تأیید', btn: 'btn-success', icon: 'check', comment: 'optional' },
    reject: { label: 'رد', btn: 'btn-danger', icon: 'x', comment: 'required' },
    return: { label: 'برگشت برای اصلاح', btn: 'btn-warning', icon: 'undo-2', comment: 'required' },
    complete: { label: 'اتمام', btn: 'btn-primary', icon: 'flag', comment: 'optional' },
    submit: { label: 'ارسال', btn: 'btn-primary', icon: 'send', comment: 'optional' },
  };

  var params = new URLSearchParams(window.location.search);
  var selectedId = params.get('id');
  var state = { status: '', search: '', page: 1 };
  var $listView = document.getElementById('req-list-view');
  var $detailView = document.getElementById('req-detail-view');

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function fetchJson(url) {
    return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); }); });
  }

  // ── list ────────────────────────────────────────────────────────────

  function loadList() {
    var $list = document.getElementById('req-list');
    $list.setAttribute('aria-busy', 'true');
    $list.innerHTML = '<div class="pen-loading">در حال بارگذاری…</div>';
    var p = new URLSearchParams();
    if (state.status) p.set('status', state.status);
    if (state.search) p.set('search', state.search);
    p.set('page', state.page);
    fetchJson(API + '?' + p.toString()).then(function (d) {
      var rows = d.results || [];
      if (!rows.length) {
        $list.innerHTML = '<div class="card"><div class="pen-empty"><i data-lucide="inbox" class="size-8 opacity-50"></i><p class="mb-0 mt-2">درخواستی یافت نشد.</p></div></div>';
        return;
      }
      $list.innerHTML = rows.map(function (r) {
        var badge = STATUS_BADGE[r.status] || 'pen-badge-draft';
        var actions = r.actions || {};
        var menu = '<div class="dropdown pen-actions-dropdown ms-auto"><button class="btn btn-sm btn-light" type="button" data-bs-toggle="dropdown" aria-label="عملیات درخواست"><i data-lucide="more-horizontal" class="size-4"></i></button><ul class="dropdown-menu dropdown-menu-end">' +
          '<li><a class="dropdown-item" href="/workspace/requests/?id=' + encodeURIComponent(r.id) + '"><i data-lucide="eye" class="size-4"></i> مشاهده</a></li>' +
          (actions.delete ? '<li><hr class="dropdown-divider"></li><li><button type="button" class="dropdown-item text-danger" data-delete-action data-delete-url="' + esc(API + r.id + '/delete/') + '" data-delete-name="' + esc(r.title || 'درخواست') + '" data-delete-code="' + esc(r.tracking_number || r.id) + '"><i data-lucide="trash-2" class="size-4"></i> حذف نرم</button></li>' : '') +
          '</ul></div>';
        return '<div class="card wq-card" data-request-card="' + esc(r.id) + '">' +
          '<div class="card-body d-flex flex-wrap align-items-center gap-3 py-3">' +
          '<div class="flex-grow-1 overflow-hidden">' +
          '<a class="fw-semibold text-truncate d-block text-decoration-none" href="/workspace/requests/?id=' + encodeURIComponent(r.id) + '">' + esc(r.title) + '</a>' +
          '<div class="fs-13 text-muted">درخواست‌دهنده: ' + esc(r.requester_username) + ' · ' + esc(r.created_at) + '</div>' +
          '</div>' +
          '<span class="pen-badge ' + badge + '">' + esc(STATUS_LABELS[r.status] || r.status) + '</span>' +
          menu +
          '<a href="/workspace/requests/?id=' + encodeURIComponent(r.id) + '" aria-label="مشاهده جزئیات"><i data-lucide="chevron-left" class="size-4 text-muted"></i></a>' +
          '</div></div>';
      }).join('');
      // pager
      var $pager = document.getElementById('req-pager');
      $pager.innerHTML = '';
      [['قبلی', d.previous, -1], ['بعدی', d.next, 1]].forEach(function (pair) {
        var li = document.createElement('li');
        li.className = 'page-item' + (pair[1] ? '' : ' disabled');
        li.innerHTML = '<a class="page-link" href="#">' + pair[0] + '</a>';
        if (pair[1]) li.querySelector('a').addEventListener('click', function (e) {
          e.preventDefault(); state.page += pair[2]; loadList();
        });
        $pager.appendChild(li);
      });
    }).catch(function (e) {
      $list.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>';
    }).finally(function () {
      $list.removeAttribute('aria-busy');
      if (window.penRenderIcons) window.penRenderIcons();
    });
  }

  // ── detail ──────────────────────────────────────────────────────────

  function actionMeta(t) {
    var name = (t.name || '').toLowerCase();
    var kind = (t.kind || '').toLowerCase();
    if (ACTION_META[kind]) return ACTION_META[kind];
    for (var key in ACTION_META) { if (name.indexOf(key) !== -1) return ACTION_META[key]; }
    return { label: t.name || 'اقدام', btn: 'btn-outline-primary', icon: 'arrow-left-right', comment: t.requires_comment ? 'required' : 'optional' };
  }

  function renderActions(instanceId, transitions) {
    var $box = document.getElementById('rd-actions');
    $box.innerHTML = '';
    if (!transitions.length) {
      $box.innerHTML = '<p class="text-muted mb-0 fs-14">اقدامی برای شما مجاز نیست.</p>';
      return;
    }
    transitions.forEach(function (t) {
      var meta = actionMeta(t);
      var btn = document.createElement('button');
      btn.className = 'btn ' + meta.btn + ' w-100';
      btn.innerHTML = '<i data-lucide="' + meta.icon + '" class="size-4 me-1"></i> ' + esc(meta.label);
      btn.addEventListener('click', function () { openActionModal(instanceId, t, meta); });
      $box.appendChild(btn);
    });
    if (window.penRenderIcons) window.penRenderIcons();
  }

  var actionModal = null;
  function openActionModal(instanceId, t, meta) {
    document.getElementById('action-label').textContent = meta.label;
    document.getElementById('action-hint').textContent =
      'اقدام «' + meta.label + '» روی درخواست ثبت می‌شود. ' +
      (meta.comment === 'required' ? 'نوشتن توضیح الزامی است.' : 'توضیح اختیاری است.');
    document.getElementById('action-comment').value = '';
    document.getElementById('action-error').hidden = true;
    var confirmBtn = document.getElementById('action-confirm');
    var fresh = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(fresh, confirmBtn);
    fresh.addEventListener('click', function () {
      var comment = document.getElementById('action-comment').value.trim();
      if (meta.comment === 'required' && !comment) {
        var eb = document.getElementById('action-error');
        eb.querySelector('ul').innerHTML = '<li>توضیح برای این اقدام الزامی است.</li>';
        eb.hidden = false;
        return;
      }
      fresh.disabled = true;
      fetch(API + instanceId + '/execute-transition/', {
        method: 'POST', credentials: 'same-origin', headers: headers(),
        body: JSON.stringify({
          transition_id: t.id, comment: comment,
          idempotency_key: (crypto.randomUUID ? crypto.randomUUID() : String(Date.now())),
        }),
      }).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (b) { return { ok: r.ok, b: b }; });
      }).then(function (res) {
        fresh.disabled = false;
        if (!res.ok) {
          var eb = document.getElementById('action-error');
          var msg = res.b.error || res.b.detail || Object.keys(res.b).map(function (k) { return k + ': ' + res.b[k]; }).join('؛ ') || ('HTTP error');
          eb.querySelector('ul').innerHTML = '<li>' + esc(msg) + '</li>';
          eb.hidden = false;
          return;
        }
        actionModal && actionModal.hide();
        window.penToast('اقدام «' + meta.label + '» ثبت شد ✓', 'success');
        openDetail(instanceId); // refresh
      }).catch(function (e) { fresh.disabled = false; window.penToast('خطا: ' + e, 'danger'); });
    });
    actionModal = actionModal || (window.bootstrap ? new window.bootstrap.Modal(document.getElementById('action-modal')) : null);
    actionModal && actionModal.show();
  }

  function openDetail(id) {
    $listView.hidden = true;
    $detailView.hidden = false;

    fetchJson(API + id + '/').then(function (inst) {
      document.getElementById('rd-title').textContent = inst.title || 'درخواست';
      var badge = document.getElementById('rd-status');
      badge.className = 'pen-badge ' + (STATUS_BADGE[inst.status] || 'pen-badge-draft');
      badge.textContent = STATUS_LABELS[inst.status] || inst.status;
      document.getElementById('rd-meta').textContent =
        'درخواست‌دهنده: ' + (inst.requester_username || '—') +
        ' · ثبت: ' + (inst.created_at || '—') +
        ' · فرآیند: ' + (inst.workflow_definition && inst.workflow_definition.name || '—');
      var deleteButton = document.getElementById('rd-delete');
      if (deleteButton) {
        deleteButton.hidden = !(inst.actions && inst.actions.delete);
        deleteButton.dataset.deleteUrl = API + id + '/delete/';
        deleteButton.dataset.deleteName = inst.title || 'درخواست';
        deleteButton.dataset.deleteCode = inst.tracking_number || id;
        deleteButton.dataset.deleteRedirect = '/workspace/requests/';
      }

      // whose turn is it? (pending tasks of this instance — my tasks API is
      // assignee-scoped; for "others' turns" we show task_count summary)
      var tc = inst.task_count || {};
      document.getElementById('rd-whonow-text').innerHTML =
        'مرحلهٔ فعلی: <strong>' + esc(inst.current_state_code || '—') + '</strong>' +
        ' — <strong>' + window.persianNumbers(tc.pending || 0) + '</strong> کار در انتظار اقدام';

      // info
      var infoHtml =
        '<div class="vstack gap-1">' +
        '<div class="fs-14"><span class="text-muted">توضیحات:</span> ' + esc(inst.description || '—') + '</div>' +
        '</div>';
      if (inst.submission) {
        var sub = inst.submission;
        var rows = Object.keys(sub.data || {}).map(function (k) {
          var v = sub.data[k];
          if (v == null || v === '') return '';
          var shown = Array.isArray(v) ? v.join('، ') : String(v);
          return '<tr><th scope="row" class="fw-normal text-muted">' + esc(k) + '</th><td>' + esc(shown) + '</td></tr>';
        }).filter(Boolean).join('');
        infoHtml +=
          '<div class="card bg-body-tertiary mt-3"><div class="card-body py-3">' +
          '<div class="d-flex align-items-center gap-2 mb-2">' +
          '<span class="badge bg-primary-subtle text-primary">' + esc(sub.schema_title) + '</span>' +
          '<code class="fs-13">' + esc(sub.submission_number || 'پیش‌نویس') + '</code>' +
          '<a href="' + esc(sub.detail_url) + '" class="btn btn-sm btn-outline-primary ms-auto">پیوست‌ها و نظرات</a>' +
          '</div>' +
          (rows ? '<table class="table table-sm mb-0"><tbody>' + rows + '</tbody></table>' : '<p class="text-muted mb-0 fs-14">داده‌ای ثبت نشده است.</p>') +
          '</div></div>';
      }
      document.getElementById('rd-info').innerHTML = infoHtml;

      // timeline (ActionLog, newest first → reverse for chronology)
      return fetchJson(API + id + '/logs/').then(function (logs) {
        var rows = (logs.results || logs || []).slice().reverse();
        var $tl = document.getElementById('rd-timeline');
        if (!rows.length) {
          $tl.innerHTML = '<li class="text-muted fs-14">هنوز گردشی ثبت نشده است.</li>';
          return;
        }
        $tl.innerHTML = rows.map(function (l) {
          return '<li class="pen-timeline-item">' +
            '<div class="fw-semibold fs-14">' + esc(l.action) + (l.to_state_code ? ' <span class="text-muted">→ ' + esc(l.to_state_code) + '</span>' : '') + '</div>' +
            '<div class="fs-13 text-muted">' + esc(l.actor_username) + ' · ' + esc(l.created_at) + '</div>' +
            (l.comment ? '<div class="fs-14 mt-1 p-2 rounded bg-body-tertiary">' + esc(l.comment) + '</div>' : '') +
            '</li>';
        }).join('');
      });
    }).then(function () {
      // available transitions (server-authoritative action buttons)
      return fetchJson(API + id + '/available-transitions/').then(function (ts) {
        renderActions(id, ts.results || ts || []);
      });
    }).catch(function (e) {
      window.penToast(e.message, 'danger');
    }).finally(function () {
      if (window.penRenderIcons) window.penRenderIcons();
    });
  }

  // ── boot ────────────────────────────────────────────────────────────
  var timer = null;
  document.getElementById('req-search').addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { state.search = document.getElementById('req-search').value.trim(); state.page = 1; loadList(); }, 250);
  });
  document.getElementById('req-status').addEventListener('change', function () {
    state.status = this.value; state.page = 1; loadList();
  });

  if (selectedId) openDetail(selectedId);
  else loadList();
})();
