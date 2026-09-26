/*
 * Pen LMS — organizational intelligence screens (one script, four pages).
 * Each page has a distinct root; this file detects which is present and
 * boots only that view. All data comes from /api/org/* (server-derived);
 * nothing here computes access — the simulator just renders the verdict.
 */
(function () {
  'use strict';

  var BASE = '/api/org/';
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function get(url) { return fetch(url, { credentials: 'same-origin', headers: headers() }).then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); }); }); }
  function post(url, body) { return fetch(url, { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body || {}) }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { return { ok: r.ok, b: b }; }); }); }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }

  // flatten chart tree → [{id,name,department}] for user pickers
  function flatten(nodes, out) {
    out = out || [];
    (nodes || []).forEach(function (n) {
      out.push({ id: n.id, name: n.name, department: n.department });
      if (n.reports) flatten(n.reports, out);
    });
    return out;
  }

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

  // ── PERMISSIONS page (matrix + simulator) ───────────────────────────
  function bootPermissions() {
    var VERB_LABEL = { view: 'مشاهده', add: 'ایجاد', change: 'ویرایش', delete: 'حذف' };
    var $matrix = document.getElementById('matrix-wrap');
    var $simUser = document.getElementById('sim-user');
    var $simRes = document.getElementById('sim-resource');

    get(BASE + 'permissions/matrix/').then(function (d) {
      var resources = d.resources || [];
      var rows = d.rows || [];
      // matrix table
      var head = '<tr><th>گروه</th>' + resources.map(function (r) {
        return '<th class="text-center">' + esc(r.label) + '</th>';
      }).join('') + '</tr>';
      var body = rows.map(function (row) {
        var cells = resources.map(function (r) {
          var v = row.resources[r.key] || {};
          var marks = ['view', 'add', 'change', 'delete'].map(function (verb) {
            var on = v[verb];
            return '<span class="mx-1 ' + (on ? 'text-success' : 'text-muted') + '" title="' + VERB_LABEL[verb] + '">' +
              (on ? '<i data-lucide="check" class="size-3"></i>' : '<i data-lucide="minus" class="size-3"></i>') + '</span>';
          }).join('');
          return '<td class="text-center">' + marks + '</td>';
        }).join('');
        return '<tr><td class="fw-semibold">' + esc(row.group) + '</td>' + cells + '</tr>';
      }).join('');
      $matrix.innerHTML = '<table class="table table-sm align-middle mb-0"><thead class="table-light">' + head + '</thead><tbody>' + body + '</tbody></table>';
      // resource picker for simulator
      $simRes.innerHTML = resources.map(function (r) { return '<option value="' + esc(r.key) + '">' + esc(r.label) + '</option>'; }).join('');
      icons();
    }).catch(function (e) { $matrix.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>'; });

    // user picker from chart
    get(BASE + 'chart/').then(function (d) {
      var users = flatten(d.chart);
      $simUser.innerHTML = '<option value="">— انتخاب کاربر —</option>' + users.map(function (u) {
        return '<option value="' + esc(u.id) + '">' + esc(u.name) + (u.department ? ' (' + esc(u.department) + ')' : '') + '</option>';
      }).join('');
    });

    document.getElementById('sim-run').addEventListener('click', function () {
      var user = $simUser.value, resource = $simRes.value, verb = document.getElementById('sim-verb').value;
      var $out = document.getElementById('sim-result');
      if (!user) { toast('یک کاربر انتخاب کنید.', 'warning'); return; }
      $out.hidden = false; $out.innerHTML = '<div class="pen-loading">…</div>';
      post(BASE + 'permissions/simulate/', { user: user, resource: resource, verb: verb }).then(function (res) {
        if (!res.ok) { $out.innerHTML = '<div class="alert alert-danger mb-0">' + esc(res.b.error || 'خطا') + '</div>'; return; }
        var allowed = res.b.allowed;
        var reasons = (res.b.reasons || []).map(function (r) { return '<li>' + esc(r) + '</li>'; }).join('');
        $out.innerHTML =
          '<div class="alert alert-' + (allowed ? 'success' : 'danger') + ' mb-0">' +
          '<div class="d-flex align-items-center gap-2 mb-1"><i data-lucide="' + (allowed ? 'shield-check' : 'shield-x') + '" class="size-5"></i>' +
          '<strong>' + (allowed ? 'مجاز است' : 'مجاز نیست') + '</strong></div>' +
          '<ul class="mb-0 ps-4 fs-14">' + reasons + '</ul></div>';
        icons();
      }).catch(function (e) { $out.innerHTML = '<div class="alert alert-danger mb-0">' + esc(e.message) + '</div>'; });
    });
  }

  // ── RESPONSIBILITIES page (perf + who-approves) ─────────────────────
  function bootResponsibilities() {
    var $perf = document.getElementById('perf-list');
    var $resp = document.getElementById('resp-wrap');
    var HEALTH = { green: ['success', 'در محدوده'], amber: ['warning', 'نیاز به توجه'], red: ['danger', 'تأخیرکرده'] };

    get(BASE + 'performance/units/').then(function (d) {
      var rows = d.results || [];
      $perf.innerHTML = rows.length ? rows.map(function (r) {
        var h = HEALTH[r.health] || HEALTH.amber;
        return '<div class="card bg-body-tertiary"><div class="card-body py-3">' +
          '<div class="d-flex align-items-center gap-2 mb-2"><strong>' + esc(r.department) + '</strong>' +
          '<span class="badge bg-' + h[0] + '-subtle text-' + h[0] + ' ms-auto">' + h[1] + '</span></div>' +
          '<div class="progress mb-2" style="height:8px"><div class="progress-bar bg-' + h[0] + '" style="width:' + r.rate + '%"></div></div>' +
          '<div class="d-flex flex-wrap gap-3 fs-13 text-muted">' +
          '<span>تکمیل: <b class="text-body">' + window.persianNumbers(r.done) + '</b>/' + window.persianNumbers(r.total) + '</span>' +
          '<span>باز: <b class="text-body">' + window.persianNumbers(r.pending) + '</b></span>' +
          '<span>تأخیر: <b class="text-' + (r.overdue ? 'danger' : 'body') + '">' + window.persianNumbers(r.overdue) + '</b></span>' +
          '<span>نرخ: <b class="text-body">' + window.persianNumbers(r.rate) + '٪</b></span>' +
          '</div></div></div>';
      }).join('') : '<div class="pen-empty"><p class="mb-0">داده‌ای برای عملکرد واحدها نیست.</p></div>';
      icons();
    }).catch(function (e) { $perf.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>'; });

    get(BASE + 'responsibilities/').then(function (d) {
      var rows = d.results || [];
      if (!rows.length) { $resp.innerHTML = '<div class="pen-empty"><p class="mb-0">فرآیندی با نقش مشخص تعریف نشده است.</p></div>'; return; }
      $resp.innerHTML = '<table class="table table-sm align-middle mb-0"><thead class="table-light"><tr><th>فرآیند</th><th>اقدام</th><th>نقش‌های مجاز</th></tr></thead><tbody>' +
        rows.map(function (r) {
          var roles = (r.roles || []).map(function (x) { return '<span class="badge bg-primary-subtle text-primary me-1">' + esc(x) + '</span>'; }).join('');
          return '<tr><td>' + esc(r.workflow) + '</td><td>' + esc(r.action) + (r.requires_comment ? ' <i data-lucide="message-square" class="size-3 text-muted" title="نیازمند توضیح"></i>' : '') + '</td><td>' + roles + '</td></tr>';
        }).join('') + '</tbody></table>';
      icons();
    }).catch(function (e) { $resp.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>'; });
  }

  // ── DELEGATIONS page ────────────────────────────────────────────────
  function bootDelegations() {
    var $wrap = document.getElementById('del-wrap');
    var modal = window.bootstrap ? new window.bootstrap.Modal(document.getElementById('del-modal')) : null;
    var users = [];

    function load() {
      $wrap.setAttribute('aria-busy', 'true');
      get(BASE + 'delegations/').then(function (d) {
        var rows = d.results || [];
        if (!rows.length) { $wrap.innerHTML = '<div class="pen-empty"><p class="mb-0">جانشینی ثبت نشده است.</p></div>'; return; }
        $wrap.innerHTML = '<table class="table table-hover align-middle mb-0"><thead class="table-light"><tr><th>صاحب کار</th><th>جانشین</th><th>دامنه</th><th>بازه</th><th>وضعیت</th><th></th></tr></thead><tbody>' +
          rows.map(function (r) {
            var scope = r.department || (r.workflow_code ? 'فرآیند: ' + r.workflow_code : 'کارتابل کامل');
            var badge = r.is_live ? '<span class="badge bg-success-subtle text-success">جاری</span>'
              : (r.is_active ? '<span class="badge bg-secondary-subtle text-secondary">آینده/گذشته</span>' : '<span class="badge bg-light text-muted border">لغوشده</span>');
            var revoke = (r.is_active)
              ? '<button class="btn btn-sm btn-outline-danger" data-revoke="' + esc(r.id) + '"><i data-lucide="x" class="size-4"></i></button>' : '';
            return '<tr><td>' + esc(r.principal) + '</td><td>' + esc(r.delegate) + '</td><td>' + esc(scope) + (r.reason ? ' <span class="fs-13 text-muted">· ' + esc(r.reason) + '</span>' : '') + '</td>' +
              '<td class="fs-13">' + esc(r.valid_from) + ' → ' + esc(r.valid_to) + '</td><td>' + badge + '</td><td>' + revoke + '</td></tr>';
          }).join('') + '</tbody></table>';
        $wrap.querySelectorAll('[data-revoke]').forEach(function (b) {
          b.addEventListener('click', function () {
            post(BASE + 'delegations/' + b.dataset.revoke + '/revoke/', {}).then(function (res) {
              if (res.ok) { toast('جانشینی لغو شد.', 'success'); load(); } else toast(res.b.detail || 'خطا', 'danger');
            });
          });
        });
        icons();
      }).catch(function (e) { $wrap.innerHTML = '<div class="pen-empty">' + esc(e.message) + '</div>'; })
        .finally(function () { $wrap.removeAttribute('aria-busy'); });
    }

    // populate user pickers from chart
    get(BASE + 'chart/').then(function (d) {
      users = flatten(d.chart);
      var opts = '<option value="">— انتخاب —</option>' + users.map(function (u) {
        return '<option value="' + esc(u.id) + '">' + esc(u.name) + (u.department ? ' (' + esc(u.department) + ')' : '') + '</option>';
      }).join('');
      document.getElementById('del-principal').innerHTML = opts;
      document.getElementById('del-delegate').innerHTML = opts;
    });

    document.getElementById('del-create').addEventListener('click', function () {
      ['del-principal', 'del-delegate', 'del-department', 'del-workflow', 'del-from', 'del-to', 'del-reason'].forEach(function (id) {
        var el = document.getElementById(id); if (el) el.value = '';
      });
      document.getElementById('del-error').hidden = true;
      modal && modal.show();
      if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
    });

    document.getElementById('del-save').addEventListener('click', function () {
      var from = window.penJalaliToISO(document.getElementById('del-from').value);
      var to = window.penJalaliToISO(document.getElementById('del-to').value);
      var $err = document.getElementById('del-error');
      function fail(msg) { $err.querySelector('ul').innerHTML = '<li>' + esc(msg) + '</li>'; $err.hidden = false; }
      if (!from || !to) { fail('تاریخ‌ها را با پیکر جلالی انتخاب کنید.'); return; }
      post(BASE + 'delegations/', {
        principal: document.getElementById('del-principal').value,
        delegate: document.getElementById('del-delegate').value,
        department: document.getElementById('del-department').value.trim(),
        workflow_code: document.getElementById('del-workflow').value.trim(),
        reason: document.getElementById('del-reason').value.trim(),
        valid_from: from + 'T00:00:00',
        valid_to: to + 'T23:59:59',
      }).then(function (res) {
        if (!res.ok) { fail(typeof res.b.error === 'string' ? res.b.error : JSON.stringify(res.b)); return; }
        modal && modal.hide(); toast('جانشینی ثبت شد ✓', 'success'); load();
      }).catch(function (e) { fail(e.message); });
    });

    load();
  }

  // ── router: boot whichever page's root exists ───────────────────────
  if (document.getElementById('rightToLeftChart')) bootChart();
  else if (document.getElementById('matrix-wrap')) bootPermissions();
  else if (document.getElementById('perf-list')) bootResponsibilities();
  else if (document.getElementById('del-wrap')) bootDelegations();
})();
