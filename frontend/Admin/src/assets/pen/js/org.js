/*
 * Pen LMS - organizational chart page (org tree + profile modal).
 * All data comes from /api/org/* (server-derived). The permissions,
 * responsibilities and delegation screens were dropped from the UI.
 */
(function () {
  'use strict';

  var BASE = '/api/org/';
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function get(url) { return fetch(url, { credentials: 'same-origin', headers: headers() }).then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); }); }); }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }

  // ── ORG CHART page ──────────────────────────────────────────────────
  function bootChart() {
    var $tree = document.getElementById('rightToLeftChart');
    var profileModalElement = document.getElementById('profile-modal');
    var profileModal = window.bootstrap && profileModalElement ? new window.bootstrap.Modal(profileModalElement) : null;
    var defaultAvatar = $tree.getAttribute('data-avatar-default') || '/static/assets/images/avatar/user-no.png';
    var $groups = document.getElementById('org-groups');
    var $activeCount = document.getElementById('org-active-count');
    var groupRecords = [];
    var selectedGroup = 'all';
    var chartNodes = null;
    var resizeTimer = null;

    function getColor(color) {
      var value = getComputedStyle(document.documentElement).getPropertyValue(color).trim();
      if (/^\d{1,3},\s*\d{1,3},\s*\d{1,3}$/.test(value)) return 'rgb(' + value + ')';
      return value || color;
    }

    // ApexTree receives actual CSS values in the purchased template's
    // initialization. Resolve the same --dx-* tokens for the Django page.
    function resolveTheme(value) {
      if (typeof value === 'string') return value.indexOf('--dx-') === 0 ? getColor(value) : value;
      if (Array.isArray(value)) return value.map(resolveTheme);
      if (value && typeof value === 'object') {
        var copy = {};
        Object.keys(value).forEach(function (key) { copy[key] = resolveTheme(value[key]); });
        return copy;
      }
      return value;
    }

    function nodeColor(depth) {
      var colors = ['--dx-primary-bg-subtle', '--dx-orange-bg-subtle', '--dx-success-bg-subtle', '--dx-warning-bg-subtle', '--dx-pink-bg-subtle'];
      return colors[Math.min(depth, colors.length - 1)];
    }

    function toTreeNode(node, depth) {
      return {
        id: String(node.id),
        data: {
          userId: String(node.id),
          name: node.name || node.username || 'کاربر سازمانی',
          jobTitle: node.job_title || '',
          department: node.department || '',
          imageURL: node.photo_url || defaultAvatar,
        },
        options: {
          nodeBGColor: nodeColor(depth),
          nodeBGColorHover: depth === 0 ? '--dx-primary-border-subtle' : '--dx-border-color',
        },
        children: (node.reports || []).map(function (child) { return toTreeNode(child, depth + 1); }),
      };
    }

    function formatCount(value) {
      return window.persianNumbers ? window.persianNumbers(value) : String(value);
    }

    function renderGroupFilters() {
      $groups.innerHTML = groupRecords.map(function (group) {
        var active = group.key === selectedGroup;
        return '<button type="button" class="btn btn-sm org-group-filter' + (active ? ' is-active' : '') + '"' +
          ' role="tab" aria-selected="' + (active ? 'true' : 'false') + '"' +
          ' aria-controls="rightToLeftChart" data-org-group="' + esc(group.key) + '"' +
          ' title="' + esc(group.description || group.label) + '">' +
          '<i data-lucide="' + esc(group.icon || 'users') + '" class="size-4" aria-hidden="true"></i>' +
          '<span>' + esc(group.label) + '</span>' +
          '<span class="org-group-count">' + formatCount(group.count || 0) + '</span>' +
          '</button>';
      }).join('');
      $groups.setAttribute('aria-busy', 'false');
      $groups.querySelectorAll('[data-org-group]').forEach(function (button) {
        button.addEventListener('click', function () { selectGroup(button.getAttribute('data-org-group')); });
      });
      icons();
    }

    function selectGroup(key) {
      var group = groupRecords.find(function (item) { return item.key === key; });
      if (!group) return;
      selectedGroup = group.key;
      chartNodes = group.chart || [];
      $activeCount.textContent = formatCount(group.count || 0) + ' نفر';
      renderGroupFilters();
      renderChart();
    }

    var chartOptions = {
      contentKey: 'data',
      width: '100%',
      height: 600,
      nodeWidth: 150,
      nodeHeight: 70,
      childrenSpacing: 70,
      siblingSpacing: 30,
      fontColor: '--dx-body-color',
      borderColor: '--dx-border-color',
      edgeColor: '--dx-border-color',
      edgeColorHover: '--dx-primary',
      tooltipBorderColor: '--dx-border-color',
      direction: 'right',
      nodeTemplate: function (content) {
        var name = esc(content.name || 'کاربر سازمانی');
        var title = esc(content.jobTitle || content.department || '');
        var image = esc(content.imageURL || defaultAvatar);
        return '<button type="button" class="org-apex-node" data-org-user="' + esc(content.userId) + '" aria-label="مشاهده پروفایل ' + name + '">' +
          '<div class="d-flex flex-row justify-content-center align-items-center h-100 px-3 gap-2">' +
          '<img class="rounded-circle size-10 flex-shrink-0" src="' + image + '" alt="' + name + '">' +
          '<div class="min-w-0 text-start">' +
          '<h6 class="mb-0 text-truncate">' + name + '</h6>' +
          (title ? '<span class="d-block fs-13 text-muted text-truncate">' + title + '</span>' : '') +
          '</div></div></button>';
      },
      canvasStyle: 'border: 1px solid var(--dx-border-color);background: var(--dx-secondary-bg);',
    };

    function renderChart() {
      if (!chartNodes) return;
      $tree.setAttribute('aria-busy', 'true');
      $tree.innerHTML = '';
      if (!chartNodes.length) {
        $tree.setAttribute('aria-busy', 'false');
        $tree.innerHTML = '<div class="pen-empty"><p class="mb-0">برای این گروه هنوز عضوی ثبت نشده است.</p></div>';
        return;
      }
      if (typeof window.ApexTree !== 'function') {
        $tree.setAttribute('aria-busy', 'false');
        $tree.innerHTML = '<div class="pen-empty">کتابخانهٔ نمودار سازمانی بارگذاری نشد.</div>';
        return;
      }
      var options = resolveTheme(chartOptions);
      // Functions are intentionally restored after token resolution because a
      // JSON-style clone would drop the node renderer.
      options.nodeTemplate = chartOptions.nodeTemplate;
      var data;
      if (chartNodes.length === 1) {
        data = resolveTheme(toTreeNode(chartNodes[0], 0));
      } else {
        data = resolveTheme({
          id: 'pen-org-root',
          data: { userId: 'pen-org-root', name: 'ساختار سازمانی', imageURL: defaultAvatar },
          options: { nodeBGColor: '--dx-secondary-bg', nodeBGColorHover: '--dx-tertiary-bg' },
          children: chartNodes.map(function (node) { return toTreeNode(node, 1); }),
        });
      }
      new window.ApexTree($tree, options).render(data);
      $tree.setAttribute('aria-busy', 'false');
    }

    $tree.addEventListener('click', function (event) {
      var target = event.target.closest ? event.target.closest('[data-org-user]') : null;
      if (target && target.getAttribute('data-org-user') !== 'pen-org-root') openProfile(target.getAttribute('data-org-user'));
    });

    get(BASE + 'chart/').then(function (d) {
      groupRecords = d.groups || [{ key: 'all', label: 'همه اعضا', count: (d.chart || []).length, chart: d.chart || [], icon: 'network' }];
      renderGroupFilters();
      selectGroup(selectedGroup);
    }).catch(function (e) {
      $groups.setAttribute('aria-busy', 'false');
      $groups.innerHTML = '';
      $activeCount.textContent = '—';
      $tree.setAttribute('aria-busy', 'false');
      $tree.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>';
    });

    function scheduleRender() {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(renderChart, 120);
    }

    window.addEventListener('resize', scheduleRender);
    document.getElementById('darkModeButton')?.addEventListener('click', scheduleRender);

    function openProfile(id) {
      document.getElementById('profile-body').innerHTML = '<div class="pen-loading">در حال بارگذاری…</div>';
      profileModal && profileModal.show();
      get(BASE + 'profile/' + id + '/').then(function (p) {
        function row(label, val) { return '<div class="row g-2 py-1 border-bottom"><div class="col-4 text-muted fs-14">' + esc(label) + '</div><div class="col-8 fs-14">' + val + '</div></div>'; }
        var roles = (p.roles || []).map(function (r) { return '<span class="badge bg-primary-subtle text-primary me-1">' + esc(r) + '</span>'; }).join('') || '—';
        var groups = (p.groups || []).map(function (g) { return '<span class="badge bg-light text-dark border me-1">' + esc(g) + '</span>'; }).join('') || '—';
        var del = (p.delegations || []).map(function (d) {
          return '<li class="fs-14">' + esc(d.delegate_name) + ' — ' + esc(d.department || d.workflow_code || 'کارتابل') + ' (' + esc(d.valid_from) + ' تا ' + esc(d.valid_to) + ')</li>';
        }).join('');
        document.getElementById('profile-body').innerHTML =
          '<h6 class="mb-3">' + esc(p.name) + ' <span class="fs-13 text-muted">@' + esc(p.username) + '</span></h6>' +
          row('واحد', esc(p.department || '—')) +
          row('سمت', esc(p.job_title || '—')) +
          row('کد پرسنلی', esc(p.employee_code || '—')) +
          row('مدیر مستقیم', p.manager ? '<a href="#" class="link-primary" data-user="' + esc(p.manager_id) + '">' + esc(p.manager) + '</a>' : '—') +
          row('نوع کاربری', esc(p.person_type_display || '—')) +
          row('نقش‌ها', roles) +
          row('گروه‌ها', groups) +
          row('کارهای باز', window.persianNumbers(p.pending_tasks)) +
          (del ? '<div class="mt-3"><div class="text-muted fs-14 mb-1">جانشینی‌های فعال</div><ul class="mb-0 ps-3">' + del + '</ul></div>' : '');
        // nested manager link
        var link = document.querySelector('#profile-body [data-user]');
        if (link) link.addEventListener('click', function (e) { e.preventDefault(); openProfile(link.dataset.user); });
        icons();
      }).catch(function (e) { document.getElementById('profile-body').innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>'; });
    }

  }

  // ── router: boot whichever page's root exists ───────────────────────
  if (document.getElementById('rightToLeftChart')) bootChart();
})();
