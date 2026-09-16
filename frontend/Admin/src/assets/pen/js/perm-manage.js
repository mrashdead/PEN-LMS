/*
 * Pen LMS — permission management page.
 *
 * Search a person → view/edit their roles + Django groups, and see the
 * effective model-permissions grid. All writes go through /api/org/perm/*
 * which enforce the hierarchy server-side; this UI just reflects what the
 * server returns (a manager can't grant workflow_admin — the API refuses and
 * we surface the error).
 */
(function () {
  'use strict';

  var BASE = '/api/org/perm/';
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  var $search = document.getElementById('pm-search');
  var $users = document.getElementById('pm-users');
  var $empty = document.getElementById('pm-empty');
  var $editor = document.getElementById('pm-editor');
  if (!$search) return;

  var options = { roles: [], groups: [] };
  var current = null; // {id, name, roles[], groups[]}

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function get(url) { return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} }).then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); }); }); }
  function post(url, body) { return fetch(url, { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body || {}) }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { return { ok: r.ok, b: b }; }); }); }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }

  var VERB_LABEL = { view: 'مشاهده', add: 'ایجاد', change: 'ویرایش', delete: 'حذف' };
  var RES_LABEL = {
    'persons.person': 'اشخاص', 'persons.studentparent': 'والد-فرزند',
    'forms.formsubmission': 'فرم‌ها', 'forms.formschema': 'تعریف فرم',
    'forms.formattachment': 'پیوست‌ها', 'forms.formcomment': 'نظرات',
    'workflow.instance': 'درخواست‌ها', 'workflow.workflowdefinition': 'تعریف فرآیند',
    'workflow.actionlog': 'تاریخچه', 'academics.academicterm': 'ترم‌ها',
    'academics.classgroup': 'کلاس‌ها', 'academics.classenrollment': 'ثبت‌نام',
    'education.lesson': 'درس‌ها', 'education.course': 'دوره‌ها',
    'education.courseoffering': 'برگزاری‌ها', 'education.classsession': 'جلسات',
    'education.location': 'محل‌ها', 'education.department': 'دپارتمان‌ها',
    'education.attendance': 'حضور', 'education.graderecord': 'کارنامه',
    'education.offeringenrollment': 'ثبت‌نام مالی', 'tasks.workflowtask': 'وظایف',
  };

  // ── options (roles + groups) ────────────────────────────────────────
  get(BASE + 'options/').then(function (d) {
    options = d;
  }).catch(function () { /* options load lazily too */ });

  // ── user directory ──────────────────────────────────────────────────
  var timer = null;
  function loadUsers(q) {
    $users.setAttribute('aria-busy', 'true');
    get(BASE + 'directory/?search=' + encodeURIComponent(q || ''))
      .then(function (d) {
        var rows = d.results || [];
        if (!rows.length) { $users.innerHTML = '<div class="text-muted fs-14">موردی نیست.</div>'; return; }
        $users.innerHTML = rows.map(function (u) {
          var active = current && current.id === u.id ? ' active' : '';
          return '<button type="button" class="card pm-user text-start' + active + '" data-id="' + esc(u.id) + '">' +
            '<div class="card-body py-2">' +
            '<div class="fw-semibold fs-14">' + esc(u.name) + '</div>' +
            '<div class="fs-13 text-muted">' + esc(u.username) + (u.department ? ' · ' + esc(u.department) : '') + '</div>' +
            '<div class="mt-1">' + (u.roles || []).map(function (r) { return '<span class="badge bg-light text-dark border me-1">' + esc(r) + '</span>'; }).join('') + '</div>' +
            '</div></button>';
        }).join('');
        $users.querySelectorAll('[data-id]').forEach(function (b) {
          b.addEventListener('click', function () { openUser(b.dataset.id); });
        });
      })
      .catch(function (e) { $users.innerHTML = '<div class="text-danger fs-14">' + esc(e.message) + '</div>'; })
      .finally(function () { $users.removeAttribute('aria-busy'); });
  }
  $search.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { loadUsers($search.value.trim()); }, 250);
  });

  // ── open a user's permissions ───────────────────────────────────────
  function openUser(id) {
    get(BASE + 'user/' + id + '/').then(function (u) {
      current = u;
      $empty.hidden = true;
      $editor.hidden = false;
      document.getElementById('pm-name').textContent = u.name;
      document.getElementById('pm-sub').textContent = '@' + u.username + (u.department ? ' · ' + u.department : '');
      document.getElementById('pm-superuser').hidden = !u.is_superuser;
      renderRoles(u);
      renderGroups(u);
      renderPerms(u);
      // highlight selected in list
      $users.querySelectorAll('.pm-user').forEach(function (b) { b.classList.toggle('active', b.dataset.id === id); });
    }).catch(function (e) { toast(e.message, 'danger'); });
  }

  function renderRoles(u) {
    var box = document.getElementById('pm-roles');
    var have = {};
    (u.roles || []).forEach(function (r) { have[r] = true; });
    box.innerHTML = options.roles.map(function (r) {
      return '<div class="form-check"><input class="form-check-input" type="checkbox" data-role="' + esc(r.code) + '" id="role_' + esc(r.code) + '"' + (have[r.code] ? ' checked' : '') + (u.is_superuser ? ' disabled' : '') + '>' +
        '<label class="form-check-label fs-14" for="role_' + esc(r.code) + '">' + esc(r.name) + ' <code class="fs-12 text-muted">' + esc(r.code) + '</code></label></div>';
    }).join('');
  }

  function renderGroups(u) {
    var box = document.getElementById('pm-groups');
    var have = {};
    (u.groups || []).forEach(function (g) { have[g] = true; });
    box.innerHTML = options.groups.map(function (g) {
      return '<div class="form-check"><input class="form-check-input" type="checkbox" data-group="' + esc(g.name) + '" id="grp_' + esc(g.name) + '"' + (have[g.name] ? ' checked' : '') + (u.is_superuser ? ' disabled' : '') + '>' +
        '<label class="form-check-label fs-14" for="grp_' + esc(g.name) + '">' + esc(g.name) + '</label></div>';
    }).join('') || '<span class="text-muted fs-14">گروهی تعریف نشده (seed_groups را اجرا کنید).</span>';
  }

  function renderPerms(u) {
    var box = document.getElementById('pm-perms');
    var rows = u.permissions || [];
    if (!rows.length) { box.innerHTML = '<div class="pen-empty py-3"><p class="mb-0 fs-14">مجوز مدل مشخصی ندارد.</p></div>'; return; }
    box.innerHTML = '<table class="table table-sm align-middle mb-0"><thead class="table-light"><tr><th>منبع</th>' +
      ['view', 'add', 'change', 'delete'].map(function (v) { return '<th class="text-center">' + VERB_LABEL[v] + '</th>'; }).join('') +
      '</tr></thead><tbody>' +
      rows.map(function (r) {
        return '<tr><td>' + esc(RES_LABEL[r.resource] || r.resource) + '</td>' +
          ['view', 'add', 'change', 'delete'].map(function (v) {
            return '<td class="text-center">' + (r.verbs[v] ? '<i data-lucide="check" class="size-4 text-success"></i>' : '<i data-lucide="minus" class="size-4 text-muted"></i>') + '</td>';
          }).join('') + '</tr>';
      }).join('') + '</tbody></table>';
    icons();
  }

  // ── save ────────────────────────────────────────────────────────────
  document.getElementById('pm-save-roles').addEventListener('click', function () {
    if (!current) return;
    var roles = Array.prototype.slice.call(document.querySelectorAll('#pm-roles input[data-role]:checked')).map(function (c) { return c.dataset.role; });
    post(BASE + 'user/' + current.id + '/roles/', { roles: roles }).then(function (res) {
      if (!res.ok) { toast(res.b.error || res.b.detail || 'خطا', 'danger'); return; }
      toast('نقش‌ها ذخیره شد ✓', 'success');
      current.roles = res.b.roles || roles;
      renderRoles(current);
      loadUsers($search.value.trim()); // refresh list badges
    });
  });
  document.getElementById('pm-save-groups').addEventListener('click', function () {
    if (!current) return;
    var groups = Array.prototype.slice.call(document.querySelectorAll('#pm-groups input[data-group]:checked')).map(function (c) { return c.dataset.group; });
    post(BASE + 'user/' + current.id + '/groups/', { groups: groups }).then(function (res) {
      if (!res.ok) { toast(res.b.error || res.b.detail || 'خطا', 'danger'); return; }
      toast('گروه‌ها ذخیره شد ✓', 'success');
      current.groups = res.b.groups || groups;
      renderGroups(current);
      // effective perms changed → reload the user view
      openUser(current.id);
    });
  });

  loadUsers('');
})();
