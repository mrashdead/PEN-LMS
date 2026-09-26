/*
 * Pen LMS — layout glue (runs after pen.bundle.js: Bootstrap + SimpleBar + Lucide).
 *
 * Implements the Domiex sidebar contract that the demo's main.js provided,
 * reduced to what our shell actually uses:
 *   • sidebar size toggle (large ⇄ small) with sessionStorage persistence
 *     (layout.js restores the attr before paint — no flicker)
 *   • responsive behavior: ≤991.98 slide-over + backdrop; 992–1199.98
 *     collapsed (body.sidebar-hidden); ≥1200 icon mode
 *   • small-mode flyout menus: position .nav-menu-sub next to its trigger,
 *     one open at a time, click-outside closes them
 *   • dark-mode button, toasts, shared helpers
 */
(function () {
  'use strict';

  var docEl = document.documentElement;
  var BREAKPOINT_TABLET = 991.98;
  var BREAKPOINT_DESKTOP = 1199.98;

  // ── Shared helpers (API-compatible with the old static/dashboard/js) ─
  var PEN_DIGITS = { 0: '۰', 1: '۱', 2: '۲', 3: '۳', 4: '۴', 5: '۵', 6: '۶', 7: '۷', 8: '۸', 9: '۹' };

  window.getCookie = function (name) {
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : '';
  };
  window.htmlEscape = function (s) {
    var d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
  };
  window.persianNumbers = function (s) {
    return String(s).replace(/[0-9]/g, function (c) { return PEN_DIGITS[c]; });
  };
  window.penCsrfHeader = function () {
    return { 'X-CSRFToken': window.getCookie('csrftoken') };
  };

  // One confirmation component for every module. It always posts JSON with
  // CSRF; delete URLs are never navigated to with GET.
  window.penOpenDeleteModal = function (options) {
    options = options || {};
    var el = document.getElementById('pen-delete-modal');
    var message = document.getElementById('pen-delete-message');
    var error = document.getElementById('pen-delete-error');
    var confirm = document.getElementById('pen-delete-confirm');
    if (!el || !confirm || !window.bootstrap) return;
    var name = options.name || 'این رکورد';
    var code = options.code ? ' با کد ' + options.code : '';
    message.textContent = 'آیا از حذف «' + name + '»' + code + ' اطمینان دارید؟ سوابق غیرفعال می‌شود.';
    error.hidden = true;
    error.textContent = '';
    confirm.disabled = false;
    var instance = window.bootstrap.Modal.getOrCreateInstance(el);
    var handler = function () {
      if (confirm.disabled) return;
      confirm.disabled = true;
      error.hidden = true;
      fetch(options.url, {
        method: 'POST', credentials: 'same-origin',
        headers: Object.assign({'Content-Type': 'application/json'}, window.penCsrfHeader ? window.penCsrfHeader() : {}),
        body: '{}',
      }).then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (body) {
          if (!response.ok) throw new Error(body.detail || body.error || 'عملیات حذف انجام نشد.');
          return body;
        });
      }).then(function () {
        instance.hide();
        if (window.penToast) window.penToast('رکورد با موفقیت غیرفعال شد ✓', 'success');
        if (typeof options.onSuccess === 'function') options.onSuccess();
        else if (options.redirect) window.location.assign(options.redirect);
      }).catch(function (e) {
        error.textContent = e.message || 'عملیات حذف انجام نشد.';
        error.hidden = false;
        confirm.disabled = false;
      });
    };
    confirm.replaceWith(confirm.cloneNode(true));
    confirm = document.getElementById('pen-delete-confirm');
    confirm.addEventListener('click', handler);
    if (window.penRenderIcons) window.penRenderIcons();
    instance.show();
  };

  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-delete-action]');
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    window.penOpenDeleteModal({
      url: button.dataset.deleteUrl,
      name: button.dataset.deleteName,
      code: button.dataset.deleteCode,
      redirect: button.dataset.deleteRedirect,
    });
  });

  window.penToast = function (message, kind) {
    var container = document.getElementById('pen-toast-root');
    if (!container) {
      container = document.createElement('div');
      container.id = 'pen-toast-root';
      container.className = 'toast-container position-fixed top-0 start-0 p-3';
      container.style.zIndex = '2000';
      document.body.appendChild(container);
    }
    var el = document.createElement('div');
    el.className = 'toast align-items-center text-bg-' + (kind || 'danger') + ' border-0';
    el.setAttribute('role', 'alert');
    el.innerHTML =
      '<div class="d-flex">' +
      '<div class="toast-body">' + window.htmlEscape(message || 'خطای نامشخص') + '</div>' +
      '<button type="button" class="btn-close btn-close-white me-auto m-auto" data-bs-dismiss="toast" aria-label="بستن"></button>' +
      '</div>';
    container.appendChild(el);
    if (window.bootstrap && window.bootstrap.Toast) {
      var t = new window.bootstrap.Toast(el, { delay: 6000 });
      el.addEventListener('hidden.bs.toast', function () { el.remove(); });
      t.show();
    } else {
      el.classList.add('show');
      setTimeout(function () { el.remove(); }, 6000);
    }
  };

  // ── Sidebar machinery ───────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('toggleSidebar');
    var sidebar = document.getElementById('main-sidebar');
    var backdrop = document.getElementById('sidebar-backdrop');
    var menuList = document.getElementById('navbar-menu-list');

    function persist(key, value) {
      try { sessionStorage.setItem(key, value); } catch (e) { /* private mode */ }
    }
    function viewport() {
      var w = window.innerWidth;
      if (w <= BREAKPOINT_TABLET) return 'mobile';
      if (w <= BREAKPOINT_DESKTOP) return 'tablet';
      return 'desktop';
    }
    function setSidebarAttr(value) {
      docEl.setAttribute('data-sidebar', value);
      persist('data-sidebar', value);
    }
    function closeFlyouts(exceptLi) {
      if (!menuList) return;
      menuList.querySelectorAll('#navbar-menu-list .nav-item').forEach(function (li) {
        if (exceptLi && li === exceptLi) return;
        li.querySelectorAll('.collapse.show').forEach(function (collapse) {
          collapse.classList.remove('show');
          var trigger = collapse.previousElementSibling;
          if (trigger) trigger.setAttribute('aria-expanded', 'false');
        });
      });
    }
    function hideMobileDrawer() {
      if (sidebar) sidebar.classList.remove('show');
      if (backdrop) backdrop.classList.remove('d-block');
    }

    // small-mode flyout: place .nav-menu-sub beside its trigger (RTL: left edge)
    function positionFlyout(trigger) {
      var sub = trigger.nextElementSibling && trigger.nextElementSibling.querySelector
        ? trigger.nextElementSibling.querySelector('.nav-menu-sub') : null;
      if (!sub) return;
      var rect = trigger.getBoundingClientRect();
      var menuRect = sub.getBoundingClientRect();
      var top = rect.top;
      if (top + menuRect.height > window.innerHeight) {
        top = Math.max(10, window.innerHeight - menuRect.height - 10);
      }
      sub.style.top = top + 'px';
      sub.style.right = (window.innerWidth - rect.left + 1) + 'px';
      sub.style.bottom = 'auto';
    }

    function toggleSidebar() {
      var mode = viewport();
      if (mode === 'mobile') {
        setSidebarAttr('large');
        document.body.classList.remove('sidebar-hidden');
        if (sidebar) sidebar.classList.toggle('show');
        if (backdrop) backdrop.classList.toggle('d-block');
        closeFlyouts();
      } else if (mode === 'tablet') {
        document.body.classList.toggle('sidebar-hidden');
        setSidebarAttr('small');
        hideMobileDrawer();
        closeFlyouts();
      } else {
        var next = (docEl.getAttribute('data-sidebar') || 'large') === 'large' ? 'small' : 'large';
        setSidebarAttr(next);
        document.body.classList.remove('sidebar-hidden');
        hideMobileDrawer();
        closeFlyouts();
      }
    }

    if (toggle) toggle.addEventListener('click', toggleSidebar);
    if (backdrop) backdrop.addEventListener('click', function () {
      hideMobileDrawer();
      closeFlyouts();
    });

    // Responsive sync on load/resize (theme behavior):
    //  mobile: drawer mode, attr=large
    //  tablet: small icons + body.sidebar-hidden until user opens
    //  desktop: restore persisted size, drop mobile classes
    function syncViewport() {
      var mode = viewport();
      if (mode === 'mobile') {
        docEl.setAttribute('data-sidebar', 'large');
        document.body.classList.remove('sidebar-hidden');
        if (sidebar) sidebar.classList.remove('show');
      } else if (mode === 'tablet') {
        setSidebarAttr('small');
      } else {
        document.body.classList.remove('sidebar-hidden');
        hideMobileDrawer();
        var saved = 'large';
        try { saved = sessionStorage.getItem('data-sidebar') || docEl.getAttribute('data-sidebar') || 'large'; } catch (e) {}
        docEl.setAttribute('data-sidebar', saved === 'small' ? 'small' : 'large');
      }
      closeFlyouts();
    }
    window.addEventListener('resize', syncViewport);
    syncViewport();

    // Flyout interactions (small mode): parent click closes siblings + positions.
    if (menuList) {
      menuList.addEventListener('click', function (e) {
        var trigger = e.target.closest('#navbar-menu-list .nav-item > a[data-bs-toggle="collapse"]');
        if (!trigger) return;
        if (docEl.getAttribute('data-sidebar') === 'small') {
          var li = trigger.closest('.nav-item');
          closeFlyouts(li);
          if (trigger.getAttribute('aria-expanded') !== 'true') {
            // let Bootstrap open it, then position after transition starts
            requestAnimationFrame(function () { positionFlyout(trigger); });
          }
        }
      });
      // Keep flyout anchored while open during resize/scroll.
      window.addEventListener('scroll', function () {
        if (docEl.getAttribute('data-sidebar') !== 'small') return;
        menuList.querySelectorAll('.nav-item').forEach(function (li) {
          var collapse = li.querySelector('.collapse.show');
          if (collapse) positionFlyout(collapse.previousElementSibling);
        });
      });
    }

    // Click-outside closes flyouts in small mode (theme contract).
    window.addEventListener('click', function (e) {
      if (docEl.getAttribute('data-sidebar') !== 'small') return;
      if (menuList && menuList.contains(e.target)) return;
      closeFlyouts();
    });
  });

  // ── Dark mode toggle ────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    var button = document.getElementById('darkModeButton');
    if (!button) return;
    var current = docEl.getAttribute('data-bs-theme') || 'light';
    button.setAttribute('aria-pressed', String(current === 'dark'));
    button.addEventListener('click', function () {
      var next = (docEl.getAttribute('data-bs-theme') || 'light') === 'light' ? 'dark' : 'light';
      docEl.setAttribute('data-bs-theme', next);
      button.setAttribute('aria-pressed', String(next === 'dark'));
      try { sessionStorage.setItem('data-bs-theme', next); } catch (e) { /* private mode */ }
      window.dispatchEvent(new CustomEvent('pen:theme-change', { detail: { theme: next } }));
    });
  });

  // ── Footer year ─────────────────────────────────────────────────────
  function setYear() {
    var el = document.getElementById('currentYearFooter');
    if (el) el.textContent = String(new Date().getFullYear());
  }
  document.addEventListener('DOMContentLoaded', setYear);
  setYear();

  // ── Global unread-messages badge (sidebar + topbar bell) ────────────
  // Polls /api/messaging/unread-count/ every 45s on every page. Non-staff
  // users get 403 → silently ignored (no badge shown).
  function applyUnreadBadge(count) {
    document.querySelectorAll('.msg-unread-badge').forEach(function (el) {
      if (count > 0) {
        el.hidden = false;
        el.textContent = window.persianNumbers(count > 99 ? '+99' : count);
      } else {
        el.hidden = true;
      }
    });
  }
  function fetchJson(url) {
    return fetch(url, {
      credentials: 'same-origin',
      headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
    }).then(function (r) { return r.ok ? r.json() : { count: 0, results: [] }; });
  }
  function refreshUnread() {
    fetchJson('/api/messaging/unread-count/')
      .then(function (d) { applyUnreadBadge(d.count || 0); })
      .catch(function () { /* non-staff / offline: ignore */ });
  }
  function renderNotifList() {
    var box = document.getElementById('notif-list');
    if (!box) return;
    box.innerHTML = '<div class="pen-loading">…</div>';
    fetchJson('/api/messaging/')
      .then(function (data) {
        var rows = (data.results || data || []).filter(function (t) { return (t.unread_count || 0) > 0; });
        if (!rows.length) {
          box.innerHTML = '<div class="pen-empty py-4"><p class="mb-0 fs-14">پیام خوانده‌نشده‌ای ندارید.</p></div>';
          return;
        }
        box.innerHTML = rows.slice(0, 8).map(function (t) {
          return '<a href="/workspace/messages/?thread=' + encodeURIComponent(t.thread_id) + '" class="d-block px-3 py-2 border-bottom text-decoration-none">' +
            '<div class="d-flex align-items-center gap-2">' +
            '<strong class="fs-14 text-truncate">' + window.htmlEscape(t.subject) + '</strong>' +
            '<span class="msg-badge ms-auto">' + window.persianNumbers(t.unread_count) + '</span>' +
            '</div>' +
            '<div class="fs-13 text-muted text-truncate">' + window.htmlEscape(t.created_by_name || '') + ' — ' + window.htmlEscape(t.updated_at || '') + '</div>' +
            '</a>';
        }).join('');
      })
      .catch(function () { box.innerHTML = '<div class="pen-empty py-4"><p class="mb-0 fs-14">خطا در دریافت.</p></div>'; });
  }
  document.addEventListener('DOMContentLoaded', function () {
    var bell = document.getElementById('notifBell');
    if (bell) {
      bell.addEventListener('show.bs.dropdown', renderNotifList);
      bell.addEventListener('click', renderNotifList); // first open fallback
    }
    refreshUnread();
    setInterval(refreshUnread, 45000);
  });
})();
