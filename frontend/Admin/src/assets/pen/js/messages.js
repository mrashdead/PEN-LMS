/*
 * Pen LMS — internal messaging UI (inbox + thread view + compose modal).
 * Server owns every rule (staff-only, membership, length limits); this file
 * only renders API results and posts what the user typed.
 */
(function () {
  'use strict';

  var API = '/api/messaging/';
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';
  var currentThread = null;
  var composeModal = window.bootstrap ? new window.bootstrap.Modal(document.getElementById('compose-modal')) : null;

  var $list = document.getElementById('msg-list');
  var $total = document.getElementById('msg-total');
  var $search = document.getElementById('msg-search');
  var $threadSubject = document.getElementById('thread-subject');
  var $threadParticipants = document.getElementById('thread-participants');
  var $threadEmpty = document.getElementById('thread-empty');
  var $threadBox = document.getElementById('thread-messages');
  var $replyForm = document.getElementById('reply-form');
  var $replyBody = document.getElementById('reply-body');
  var $hideBtn = document.getElementById('thread-hide');

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() {
    return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {});
  }
  function toast(m, k) { window.penToast && window.penToast(m, k); }

  // ── inbox ───────────────────────────────────────────────────────────

  function loadInbox() {
    $list.setAttribute('aria-busy', 'true');
    fetch(API, { credentials: 'same-origin', headers: headers() })
      .then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); }); })
      .then(function (rows) {
        renderInbox(rows.results || rows || []);
      })
      .catch(function (e) { $list.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>'; })
      .finally(function () { $list.removeAttribute('aria-busy'); });
  }

  function renderInbox(rows) {
    var q = ($search.value || '').trim();
    if (q) rows = rows.filter(function (r) { return (r.subject || '').indexOf(q) !== -1; });

    var unreadTotal = rows.reduce(function (s, r) { return s + (r.unread_count || 0); }, 0);
    updateBadge(unreadTotal);

    if (!rows.length) {
      $list.innerHTML = '<div class="pen-empty"><p class="mb-0">' + (q ? 'چیزی یافت نشد.' : 'صندوق خالی است.') + '</p></div>';
      return;
    }
    $list.innerHTML = rows.map(function (t) {
      var active = currentThread === t.thread_id ? ' active' : '';
      return '<a href="#" class="msg-item d-flex align-items-start gap-2 p-3 border-bottom text-decoration-none' + active + '" data-thread="' + esc(t.thread_id) + '" role="listitem">' +
        '<div class="flex-grow-1 overflow-hidden">' +
        '<div class="d-flex align-items-center gap-2">' +
        '<strong class="fs-14 text-truncate">' + esc(t.subject) + '</strong>' +
        (t.unread_count ? '<span class="badge bg-primary rounded-pill ms-auto">' + window.persianNumbers(t.unread_count) + '</span>' : '') +
        '</div>' +
        '<div class="fs-13 text-muted text-truncate">' + esc(t.created_by_name || '') + ' — ' + esc(t.updated_at || '') + '</div>' +
        '</div></a>';
    }).join('');

    $list.querySelectorAll('[data-thread]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        openThread(a.dataset.thread);
      });
    });
  }

  function updateBadge(count) {
    // sidebar/topbar badge (desktop + mobile menus)
    document.querySelectorAll('.msg-unread-badge').forEach(function (el) {
      if (count > 0) {
        el.hidden = false;
        el.textContent = window.persianNumbers(count > 99 ? '+99' : count);
      } else {
        el.hidden = true;
      }
    });
    if ($total) {
      $total.hidden = count === 0;
      $total.textContent = window.persianNumbers(count);
    }
  }

  // ── thread view ─────────────────────────────────────────────────────

  function openThread(id) {
    currentThread = id;
    fetch(API + 'threads/' + id + '/', { credentials: 'same-origin', headers: headers() })
      .then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || ('HTTP ' + r.status)); }); })
      .then(function (t) {
        $threadEmpty.hidden = true;
        $threadBox.hidden = false;
        $replyForm.hidden = false;
        $hideBtn.hidden = false;
        $threadSubject.textContent = t.subject;
        $threadParticipants.textContent = (t.participants || []).map(function (p) { return p.name || p.username; }).join('، ');

        $threadBox.innerHTML = (t.messages || []).map(function (m) {
          var mine = m.is_mine;
          return '<div class="d-flex ' + (mine ? 'justify-content-start' : 'justify-content-end') + '">' +
            '<div class="msg-bubble ' + (mine ? 'msg-mine' : 'msg-theirs') + '">' +
            '<div class="msg-head fs-13">' + esc(m.sender_name || m.sender_username) + ' — ' + esc(m.created_at || '') + '</div>' +
            '<div class="msg-body">' + esc(m.body).replace(/\n/g, '<br>') + '</div>' +
            '</div></div>';
        }).join('');
        $threadBox.scrollTop = $threadBox.scrollHeight;

        loadInbox(); // refresh badges (opening marks read server-side)
      })
      .catch(function (e) { toast(e.message, 'danger'); });
  }

  $replyForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var body = ($replyBody.value || '').trim();
    if (!body || !currentThread) return;
    fetch(API + 'threads/' + currentThread + '/reply/', {
      method: 'POST', credentials: 'same-origin', headers: headers(),
      body: JSON.stringify({ body: body }),
    })
      .then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
      .then(function (res) {
        if (!res.ok) { toast(res.b.error || 'خطا در ارسال', 'danger'); return; }
        $replyBody.value = '';
        openThread(currentThread);
      });
  });

  $hideBtn.addEventListener('click', function () {
    if (!currentThread) return;
    fetch(API + 'threads/' + currentThread + '/hide/', { method: 'POST', credentials: 'same-origin', headers: headers() })
      .then(function () {
        currentThread = null;
        $threadEmpty.hidden = false;
        $threadBox.hidden = true;
        $replyForm.hidden = true;
        $hideBtn.hidden = true;
        $threadSubject.textContent = 'یک گفتگو را انتخاب کنید';
        $threadParticipants.textContent = '';
        loadInbox();
      });
  });

  // ── compose ─────────────────────────────────────────────────────────

  function loadDirectory() {
    var sel = document.getElementById('compose-recipients');
    sel.innerHTML = '<option value="">در حال بارگذاری…</option>';
    fetch(API + 'directory/', { credentials: 'same-origin', headers: headers() })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('خطا در دریافت فهرست کارکنان')); })
      .then(function (users) {
        sel.innerHTML = users.map(function (u) {
          var label = u.name + (u.job_title ? ' (' + u.job_title + ')' : '');
          return '<option value="' + esc(u.id) + '">' + esc(label) + '</option>';
        }).join('');
      })
      .catch(function (e) { sel.innerHTML = '<option value="">' + esc(e.message) + '</option>'; });
  }

  document.getElementById('msg-compose').addEventListener('click', function () {
    document.getElementById('compose-errors').hidden = true;
    document.getElementById('compose-subject').value = '';
    document.getElementById('compose-body').value = '';
    loadDirectory();
    composeModal && composeModal.show();
  });

  document.getElementById('compose-send').addEventListener('click', function () {
    var sel = document.getElementById('compose-recipients');
    var payload = {
      recipients: Array.prototype.slice.call(sel.selectedOptions).map(function (o) { return o.value; }),
      subject: document.getElementById('compose-subject').value.trim(),
      body: document.getElementById('compose-body').value.trim(),
    };
    var errBox = document.getElementById('compose-errors');
    fetch(API + 'threads/', { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(payload) })
      .then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
      .then(function (res) {
        if (!res.ok) {
          var lines = res.b.error ? [res.b.error] :
            Object.keys(res.b).map(function (k) { return k + ': ' + res.b[k]; });
          errBox.querySelector('ul').innerHTML = lines.map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('');
          errBox.hidden = false;
          return;
        }
        composeModal && composeModal.hide();
        toast('پیام ارسال شد ✓', 'success');
        currentThread = res.b.id;
        loadInbox();
        openThread(res.b.id);
      });
  });

  // ── search debounce ─────────────────────────────────────────────────
  var timer = null;
  $search.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(loadInbox, 250);
  });

  // ── boot: open thread from ?thread= (bell deep-link) else just list ─
  loadInbox();
  var params = new URLSearchParams(window.location.search);
  var preselect = params.get('thread');
  if (preselect) openThread(preselect);
})();
