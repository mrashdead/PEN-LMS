/*
 * Pen LMS — permission management page.
 *
 * Search a person → view/edit their roles + Django groups + explicit ACL.
 * ACL section: grid of pages / forms / models with per-verb checkboxes.
 * All writes go through /api/org/acl/* which enforce the hierarchy
 * server-side; this UI reflects what the server returns.
 */
(function () {
  'use strict';

  var ACL_BASE = '/api/org/acl/';
  var PERM_BASE = '/api/org/perm/';
  var SIDEBAR_BASE = '/api/org/sidebar-visibility/';

  var $search = document.getElementById('pm-search');
  var $users = document.getElementById('pm-users');
  var $empty = document.getElementById('pm-empty');
  var $editor = document.getElementById('pm-editor');
  if (!$search) return;

  // ── State ───────────────────────────────────────────────────────────
  var catalog = { pages: [], forms: [], models: [], verbs: {} };
  var current = null; // {id, name, username, department, is_superuser, roles[], groups[], entries[]}
  var dirtyEntries = {}; // entryKey(type,key) → verbs[] | null (null=removed)

  // ── Helpers ─────────────────────────────────────────────────────────
  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); }); });
  }
  function post(url, body) {
    return fetch(url, { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body || {}) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { return { ok: r.ok, b: b }; }); });
  }
  function put(url, body) {
    return fetch(url, { method: 'PUT', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body || {}) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { return { ok: r.ok, b: b }; }); });
  }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }
  function entryKey(type, key) { return type + '|' + key; }

  var VERB_LABEL = {
    view: 'مشاهده', add: 'ایجاد', change: 'ویرایش', delete: 'حذف',
    submit: 'ارسال', approve: 'تأیید', reject: 'رد',
  };
  var CAT_ICON = { page: 'layout-dashboard', form: 'file-text', model: 'database' };
  var CAT_LABEL = { page: 'صفحه', form: 'فرم', model: 'ماژول' };

  // ── Load catalog ───────────────────────────────────────────────────
  get(ACL_BASE + 'catalog/').then(function (d) {
    catalog = d;
    if (current) renderAclGrid();
  }).catch(function (e) { toast('خطا در بارگذاری کاتالوگ: ' + e.message, 'danger'); });

  // ── Load perm options (roles + groups) ────────────────────────────
  get(PERM_BASE + 'options/').then(function (d) { window._permOptions = d; }).catch(function () {});

  // ── User directory ─────────────────────────────────────────────────
  var dirTimer = null;
  function loadUsers(q) {
    $users.setAttribute('aria-busy', 'true');
    get(PERM_BASE + 'directory/?search=' + encodeURIComponent(q || ''))
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
    clearTimeout(dirTimer);
    dirTimer = setTimeout(function () { loadUsers($search.value.trim()); }, 250);
  });

  // ── Open a user's full permissions (roles + groups + ACL) ─────────
  function openUser(id) {
    dirtyEntries = {};
    get(ACL_BASE + 'user/' + id + '/').then(function (data) {
      current = {
        id: id,
        name: data.name,
        username: data.username,
        department: data.department || '',
        is_superuser: data.is_superuser,
        roles: data.roles || [],
        groups: data.groups || [],
        entries: data.entries || [],
      };
      _entriesMap = {};
      (data.entries || []).forEach(function (e) {
        _entriesMap[entryKey(e.resource_type, e.resource_key)] = e.verbs || [];
      });

      $empty.hidden = true;
      $editor.hidden = false;
      document.getElementById('pm-name').textContent = data.name;
      document.getElementById('pm-sub').textContent = '@' + data.username + (data.department ? ' · ' + data.department : '');
      document.getElementById('pm-superuser').hidden = !data.is_superuser;
      renderRoles();
      renderGroups();
      renderPerms();
      renderAclGrid();
      loadSidebarUserSettings(id);
      $users.querySelectorAll('.pm-user').forEach(function (b) { b.classList.toggle('active', b.dataset.id === id); });
    }).catch(function (e) { toast(e.message, 'danger'); });
  }

  // ── Roles ───────────────────────────────────────────────────────────
  function renderRoles() {
    var box = document.getElementById('pm-roles');
    var opts = window._permOptions || { roles: [] };
    var have = {};
    (current.roles || []).forEach(function (r) { have[r] = true; });
    box.innerHTML = (opts.roles || []).map(function (r) {
      return '<div class="form-check"><input class="form-check-input" type="checkbox" data-role="' + esc(r.code) + '" id="role_' + esc(r.code) + '"' + (have[r.code] ? ' checked' : '') + (current.is_superuser ? ' disabled' : '') + '>' +
        '<label class="form-check-label fs-14" for="role_' + esc(r.code) + '">' + esc(r.name) + ' <code class="fs-12 text-muted">' + esc(r.code) + '</code></label></div>';
    }).join('');
  }

  // ── Groups ─────────────────────────────────────────────────────────
  function renderGroups() {
    var box = document.getElementById('pm-groups');
    var opts = window._permOptions || { groups: [] };
    var have = {};
    (current.groups || []).forEach(function (g) { have[g] = true; });
    box.innerHTML = (opts.groups || []).map(function (g) {
      return '<div class="form-check"><input class="form-check-input" type="checkbox" data-group="' + esc(g.name) + '" id="grp_' + esc(g.name) + '"' + (have[g.name] ? ' checked' : '') + (current.is_superuser ? ' disabled' : '') + '>' +
        '<label class="form-check-label fs-14" for="grp_' + esc(g.name) + '">' + esc(g.name) + '</label></div>';
    }).join('') || '<span class="text-muted fs-14">گروهی تعریف نشده.</span>';
  }

  // ── Effective model permissions table ──────────────────────────────
  function renderPerms() {
    var box = document.getElementById('pm-perms');
    // We derive effective perms from roles/groups (no separate API for this in ACL version)
    box.innerHTML = '<div class="pen-empty py-3"><p class="mb-0 fs-14">این جدول از گروه‌ها و نقش‌ها محاسبه می‌شود.</p></div>';
  }

  // ── Save roles / groups ─────────────────────────────────────────────
  document.getElementById('pm-save-roles').addEventListener('click', function () {
    if (!current) return;
    var roles = Array.prototype.slice.call(document.querySelectorAll('#pm-roles input[data-role]:checked')).map(function (c) { return c.dataset.role; });
    post(PERM_BASE + 'user/' + current.id + '/roles/', { roles: roles }).then(function (res) {
      if (!res.ok) { toast(res.b.error || res.b.detail || 'خطا', 'danger'); return; }
      toast('نقش‌ها ذخیره شد ✓', 'success');
      current.roles = res.b.roles || roles;
      renderRoles();
      loadUsers($search.value.trim());
    });
  });

  document.getElementById('pm-save-groups').addEventListener('click', function () {
    if (!current) return;
    var groups = Array.prototype.slice.call(document.querySelectorAll('#pm-groups input[data-group]:checked')).map(function (c) { return c.dataset.group; });
    post(PERM_BASE + 'user/' + current.id + '/groups/', { groups: groups }).then(function (res) {
      if (!res.ok) { toast(res.b.error || res.b.detail || 'خطا', 'danger'); return; }
      toast('گروه‌ها ذخیره شد ✓', 'success');
      current.groups = res.b.groups || groups;
      renderGroups();
    });
  });

  // ══════════════════════════════════════════════════════════════════
  // ACL Grid
  // ══════════════════════════════════════════════════════════════════

  var _entriesMap = {}; // (type, key) → verbs[] | null
  var $aclSearch = document.getElementById('acl-search');
  var $aclType = document.getElementById('acl-type');
  var $aclGrid = document.getElementById('acl-grid');
  var $aclEmpty = document.getElementById('acl-empty');
  var $aclStatus = document.getElementById('acl-status');
  var $aclSaveAll = document.getElementById('acl-save-all');
  var $aclFilterClear = document.getElementById('acl-filter-clear');

  function currentVerbs(type, key) {
    var v = _entriesMap[entryKey(type, key)];
    return v !== undefined ? v : null; // null = no explicit ACL entry
  }

  function buildGridRows() {
    var typeFilter = $aclType ? $aclType.value : 'all';
    var search = ($aclSearch ? $aclSearch.value : '').toLowerCase().trim();
    var all = [].concat(
      (catalog.pages || []).map(function (r) { return { key: r.key, title: r.title, category: 'page', verbs: r.verbs || [] }; }),
      (catalog.forms || []).map(function (r) { return { key: r.key, title: r.title, category: 'form', verbs: r.verbs || [] }; }),
      (catalog.models || []).map(function (r) { return { key: r.key, title: r.title, category: 'model', verbs: r.verbs || [] }; })
    );
    if (typeFilter !== 'all') all = all.filter(function (r) { return r.category === typeFilter; });
    if (search) all = all.filter(function (r) { return r.title.toLowerCase().includes(search) || r.key.toLowerCase().includes(search); });
    return all;
  }

  function verbLabel(v) {
    return (catalog.verbs && catalog.verbs[v]) || VERB_LABEL[v] || v;
  }

  function renderAclGrid() {
    if (!current || !$aclGrid) return;
    var rows = buildGridRows();
    $aclEmpty.hidden = rows.length > 0;
    if (!rows.length) { $aclGrid.innerHTML = ''; updateAclStatus(); return; }

    var allVerbs = catalog.verbs ? Object.keys(catalog.verbs) : ['view', 'add', 'change', 'delete'];

    var h = '<table class="table table-sm table-hover align-middle mb-0">';
    h += '<thead class="table-light"><tr>';
    h += '<th style="width:36px"><i data-lucide="lock" class="size-4"></i></th>';
    h += '<th>منبع</th>';
    h += '<th style="width:90px">نوع</th>';
    allVerbs.forEach(function (v) { h += '<th class="text-center" style="width:58px">' + verbLabel(v) + '</th>'; });
    h += '</tr></thead><tbody>';

    rows.forEach(function (r) {
      var hasExplicit = currentVerbs(r.category, r.key) !== null;
      var isSuper = current.is_superuser;
      var ekey = entryKey(r.category, r.key);
      var checkboxCols = allVerbs.map(function (v) {
        if (r.verbs.indexOf(v) === -1) return '<td class="text-center text-muted">—</td>';
        var cv = currentVerbs(r.category, r.key);
        var checked = isSuper || (cv !== null && (cv || []).indexOf(v) !== -1);
        var explicitAttr = hasExplicit ? ' data-explicit="1"' : '';
        var rowClass = hasExplicit ? 'acl-row-explicit' : '';
        return '<td class="text-center ' + rowClass + '">' +
          '<input type="checkbox" class="acl-verb"' + explicitAttr +
          ' data-type="' + esc(r.category) + '" data-key="' + esc(r.key) + '" data-verb="' + esc(v) + '"' +
          (checked ? ' checked' : '') + (isSuper ? ' disabled' : '') + '></td>';
      }).join('');

      h += '<tr class="' + (hasExplicit ? 'acl-row-explicit' : '') + '">' +
        '<td class="text-center"><span class="badge ' + (hasExplicit ? 'bg-warning text-dark' : 'bg-light text-muted') + '">' +
        (hasExplicit ? '<i data-lucide="lock" class="size-3"></i>' : '<i data-lucide="unlock" class="size-3"></i>') +
        '</span></td>' +
        '<td><span class="fw-medium">' + esc(r.title) + '</span><br><code class="fs-11 text-muted">' + esc(r.key) + '</code></td>' +
        '<td><span class="badge bg-light text-dark border"><i data-lucide="' + (CAT_ICON[r.category] || 'circle') + '" class="size-3 me-1"></i>' + (CAT_LABEL[r.category] || r.category) + '</span></td>' +
        checkboxCols + '</tr>';
    });

    h += '</tbody></table>';
    $aclGrid.innerHTML = h;
    icons();

    $aclGrid.querySelectorAll('.acl-verb').forEach(function (cb) {
      cb.addEventListener('change', onVerbChange);
    });

    updateAclStatus();
  }

  function onVerbChange(e) {
    var cb = e.target;
    var type = cb.dataset.type;
    var key = cb.dataset.key;
    var verb = cb.dataset.verb;
    var ekey = entryKey(type, key);

    // Track dirty state
    if (dirtyEntries[ekey] === undefined) {
      // Save original state as baseline
      dirtyEntries[ekey] = currentVerbs(type, key);
    }

    var verbs = dirtyEntries[ekey];
    if (verbs === null) verbs = []; // was absent → start from empty
    if (verbs === undefined) verbs = [];

    if (cb.checked) {
      if (verbs.indexOf(verb) === -1) verbs.push(verb);
    } else {
      verbs = verbs.filter(function (v) { return v !== verb; });
    }
    dirtyEntries[ekey] = verbs;

    // Visual highlight
    var row = cb.closest('tr');
    row.classList.add('acl-row-explicit');
    var badge = row.querySelector('.badge');
    if (badge) { badge.className = 'badge bg-warning text-dark'; badge.innerHTML = '<i data-lucide="lock" class="size-3"></i>'; }
    icons();
    updateAclStatus();
  }

  function updateAclStatus() {
    if (!$aclStatus) return;
    var count = Object.keys(dirtyEntries).length;
    if (!count) {
      $aclStatus.textContent = 'بدون تغییر';
      if ($aclSaveAll) $aclSaveAll.disabled = true;
    } else {
      $aclStatus.textContent = count + ' منبع تغییر کرده — در انتظار ذخیره';
      if ($aclSaveAll) $aclSaveAll.disabled = false;
    }
  }

  // Filter controls
  if ($aclSearch) $aclSearch.addEventListener('input', renderAclGrid);
  if ($aclType) $aclType.addEventListener('change', renderAclGrid);
  if ($aclFilterClear) $aclFilterClear.addEventListener('click', function () {
    if ($aclSearch) $aclSearch.value = '';
    if ($aclType) $aclType.value = 'all';
    renderAclGrid();
  });

  // ── Save all ACL ───────────────────────────────────────────────────
  if ($aclSaveAll) $aclSaveAll.addEventListener('click', function () {
    if (!current) return;
    var entries = Object.keys(dirtyEntries).map(function (ekey) {
      var parts = ekey.split('|');
      return { resource_type: parts[0], resource_key: parts[1], verbs: dirtyEntries[ekey] || [] };
    }).filter(function (e) { return e.verbs.length > 0; }); // empty = revoke

    if (!entries.length) {
      // All dirty → revoke
      Promise.all(Object.keys(dirtyEntries).map(function (ekey) {
        var parts = ekey.split('|');
        return post(ACL_BASE + 'user/' + current.id + '/revoke/', { resource_type: parts[0], resource_key: parts[1] });
      })).then(function () {
        dirtyEntries = {};
        updateAclStatus();
        return get(ACL_BASE + 'user/' + current.id + '/');
      }).then(function (data) {
        if (!data) return;
        syncEntries(data.entries || []);
        toast('ACL ذخیره شد ✓', 'success');
      });
      return;
    }

    $aclSaveAll.disabled = true;
    post(ACL_BASE + 'user/' + current.id + '/bulk/', { entries: entries }).then(function (res) {
      if (!res.ok && !res.b.ok) {
        toast(res.b.error || res.b.detail || 'خطا در ذخیره ACL', 'danger');
        $aclSaveAll.disabled = false;
        return;
      }
      toast('ACL ذخیره شد ✓', 'success');
      dirtyEntries = {};
      updateAclStatus();
      return get(ACL_BASE + 'user/' + current.id + '/');
    }).then(function (data) {
      if (!data) return;
      syncEntries(data.entries || []);
      renderAclGrid();
    }).catch(function (e) { toast('خطا: ' + e.message, 'danger'); $aclSaveAll.disabled = false; });
  });

  function syncEntries(entries) {
    current.entries = entries;
    _entriesMap = {};
    (entries || []).forEach(function (e) {
      _entriesMap[entryKey(e.resource_type, e.resource_key)] = e.verbs || [];
    });
  }

  // ══════════════════════════════════════════════════════════════════
  // Sidebar visibility (site-superuser controls only)
  // ══════════════════════════════════════════════════════════════════

  var $sidebarRoleAdmin = document.getElementById('sidebar-role-admin');
  var $sidebarRoleSelect = document.getElementById('sidebar-role-select');
  var $sidebarRoleGrid = document.getElementById('sidebar-role-grid');
  var $sidebarRoleStatus = document.getElementById('sidebar-role-status');
  var $sidebarRoleSave = document.getElementById('sidebar-role-save');
  var $sidebarRoleReset = document.getElementById('sidebar-role-reset');
  var $sidebarUserAdmin = document.getElementById('sidebar-user-admin');
  var $sidebarUserGrid = document.getElementById('sidebar-user-grid');
  var $sidebarUserStatus = document.getElementById('sidebar-user-status');
  var $sidebarUserSave = document.getElementById('sidebar-user-save');
  var $sidebarUserReset = document.getElementById('sidebar-user-reset');

  function groupSidebarItems(items) {
    var groups = [];
    (items || []).forEach(function (item) {
      var group = groups.filter(function (g) { return g.name === item.section; })[0];
      if (!group) {
        group = { name: item.section, items: [] };
        groups.push(group);
      }
      group.items.push(item);
    });
    return groups;
  }

  function renderRoleSidebarItems(items) {
    if (!$sidebarRoleGrid) return;
    $sidebarRoleGrid.innerHTML = groupSidebarItems(items).map(function (group) {
      return '<section class="border rounded p-3">' +
        '<h6 class="fw-semibold fs-14 mb-2">' + esc(group.name) + '</h6>' +
        '<div class="row g-2">' + group.items.map(function (item) {
          var defaultLabel = item.default_visible ? 'پیش‌فرض: نمایش' : 'پیش‌فرض: پنهان';
          return '<div class="col-12 col-md-6 col-xl-4">' +
            '<label class="d-flex align-items-start gap-2 border rounded p-2 h-100">' +
            '<input class="form-check-input mt-1 flex-shrink-0 sidebar-role-item" type="checkbox" data-key="' + esc(item.key) + '"' + (item.visible ? ' checked' : '') + '>' +
            '<span class="fs-13 flex-grow-1">' + esc(item.title) + '<small class="d-block text-muted">' + defaultLabel + '</small></span>' +
            '</label></div>';
        }).join('') + '</div></section>';
    }).join('');
    if ($sidebarRoleSave) $sidebarRoleSave.disabled = false;
    if ($sidebarRoleReset) $sidebarRoleReset.disabled = false;
    if ($sidebarRoleStatus) $sidebarRoleStatus.textContent = 'وضعیت نمایش برای نقش انتخاب‌شده.';
  }

  function loadRoleSidebarSettings(roleCode) {
    if (!roleCode || !$sidebarRoleGrid) return;
    $sidebarRoleGrid.innerHTML = '<div class="pen-loading">در حال بارگذاری تنظیمات نقش…</div>';
    if ($sidebarRoleSave) $sidebarRoleSave.disabled = true;
    if ($sidebarRoleReset) $sidebarRoleReset.disabled = true;
    get(SIDEBAR_BASE + 'role/' + encodeURIComponent(roleCode) + '/').then(function (data) {
      renderRoleSidebarItems(data.items || []);
    }).catch(function (e) {
      $sidebarRoleGrid.innerHTML = '<div class="text-danger fs-14">' + esc(e.message) + '</div>';
    });
  }

  function saveRoleSidebarSettings(reset) {
    if (!$sidebarRoleSelect || !$sidebarRoleSelect.value) return;
    var rules = {};
    $sidebarRoleGrid.querySelectorAll('.sidebar-role-item').forEach(function (cb) {
      rules[cb.dataset.key] = reset ? null : cb.checked;
    });
    if ($sidebarRoleSave) $sidebarRoleSave.disabled = true;
    if ($sidebarRoleReset) $sidebarRoleReset.disabled = true;
    put(SIDEBAR_BASE + 'role/' + encodeURIComponent($sidebarRoleSelect.value) + '/', { rules: rules }).then(function (res) {
      if (!res.ok) throw new Error(res.b.error || res.b.detail || 'ذخیرهٔ تنظیمات نقش انجام نشد.');
      toast(reset ? 'نمایش پیش‌فرض نقش بازیابی شد.' : 'نمایش سایدبار برای نقش ذخیره شد.', 'success');
      renderRoleSidebarItems(res.b.items || []);
    }).catch(function (e) {
      toast(e.message, 'danger');
      if ($sidebarRoleSave) $sidebarRoleSave.disabled = false;
      if ($sidebarRoleReset) $sidebarRoleReset.disabled = false;
    });
  }

  function renderUserSidebarItems(data) {
    if (!$sidebarUserGrid) return;
    $sidebarUserGrid.innerHTML = groupSidebarItems(data.items || []).map(function (group) {
      return '<section class="border rounded p-3">' +
        '<h6 class="fw-semibold fs-14 mb-2">' + esc(group.name) + '</h6>' +
        '<div class="vstack gap-2">' + group.items.map(function (item) {
          var override = item.override === null ? 'inherit' : (item.override ? 'show' : 'hide');
          var effective = item.effective_visible ? 'در سایدبار نمایش داده می‌شود' : 'در سایدبار پنهان است';
          return '<label class="d-flex flex-wrap align-items-center gap-2 border rounded p-2">' +
            '<span class="flex-grow-1 fs-13">' + esc(item.title) + '<small class="d-block text-muted sidebar-user-effective">' + effective + '</small></span>' +
            '<select class="form-select form-select-sm sidebar-user-item" data-key="' + esc(item.key) + '" style="width:auto;min-width:10rem">' +
            '<option value="inherit"' + (override === 'inherit' ? ' selected' : '') + '>پیروی از نقش‌ها</option>' +
            '<option value="show"' + (override === 'show' ? ' selected' : '') + '>نمایش</option>' +
            '<option value="hide"' + (override === 'hide' ? ' selected' : '') + '>پنهان</option>' +
            '</select></label>';
        }).join('') + '</div></section>';
    }).join('');
    if ($sidebarUserSave) $sidebarUserSave.disabled = false;
    if ($sidebarUserReset) $sidebarUserReset.disabled = false;
    if ($sidebarUserStatus) $sidebarUserStatus.textContent = 'تنظیم‌های این فرد؛ «پیروی از نقش‌ها» مقدار جداگانه را حذف می‌کند.';
  }

  function loadSidebarUserSettings(userId) {
    if (!$sidebarUserAdmin || !userId) return;
    $sidebarUserGrid.innerHTML = '<div class="pen-loading">در حال بارگذاری نمایش سایدبار…</div>';
    if ($sidebarUserSave) $sidebarUserSave.disabled = true;
    if ($sidebarUserReset) $sidebarUserReset.disabled = true;
    get(SIDEBAR_BASE + 'user/' + encodeURIComponent(userId) + '/').then(function (data) {
      renderUserSidebarItems(data);
    }).catch(function (e) {
      $sidebarUserGrid.innerHTML = '<div class="text-danger fs-14">' + esc(e.message) + '</div>';
    });
  }

  function saveUserSidebarSettings(reset) {
    if (!current || !$sidebarUserAdmin) return;
    var rules = {};
    $sidebarUserGrid.querySelectorAll('.sidebar-user-item').forEach(function (select) {
      rules[select.dataset.key] = reset || select.value === 'inherit' ? null : select.value === 'show';
    });
    if ($sidebarUserSave) $sidebarUserSave.disabled = true;
    if ($sidebarUserReset) $sidebarUserReset.disabled = true;
    put(SIDEBAR_BASE + 'user/' + encodeURIComponent(current.id) + '/', { rules: rules }).then(function (res) {
      if (!res.ok) throw new Error(res.b.error || res.b.detail || 'ذخیرهٔ نمایش کاربر انجام نشد.');
      toast(reset ? 'تنظیم نمایش این فرد از نقش‌ها پیروی می‌کند.' : 'نمایش سایدبار برای کاربر ذخیره شد.', 'success');
      renderUserSidebarItems(res.b);
    }).catch(function (e) {
      toast(e.message, 'danger');
      if ($sidebarUserSave) $sidebarUserSave.disabled = false;
      if ($sidebarUserReset) $sidebarUserReset.disabled = false;
    });
  }

  function initSidebarVisibility() {
    if ($sidebarRoleAdmin && $sidebarRoleSelect) {
      get(SIDEBAR_BASE + 'catalog/').then(function (data) {
        var roles = data.roles || [];
        if (!roles.length) {
          $sidebarRoleGrid.innerHTML = '<div class="pen-empty py-3">نقش فعالی برای تنظیم وجود ندارد.</div>';
          return;
        }
        $sidebarRoleSelect.innerHTML = roles.map(function (role) {
          return '<option value="' + esc(role.code) + '">' + esc(role.name) + ' (' + esc(role.code) + ')</option>';
        }).join('');
        $sidebarRoleSelect.disabled = false;
        loadRoleSidebarSettings($sidebarRoleSelect.value);
      }).catch(function (e) {
        $sidebarRoleGrid.innerHTML = '<div class="text-danger fs-14">' + esc(e.message) + '</div>';
      });
      $sidebarRoleSelect.addEventListener('change', function () {
        loadRoleSidebarSettings($sidebarRoleSelect.value);
      });
      $sidebarRoleGrid.addEventListener('change', function (e) {
        if (e.target.matches('.sidebar-role-item')) $sidebarRoleStatus.textContent = 'تغییر ذخیره‌نشده است.';
      });
      $sidebarRoleSave.addEventListener('click', function () { saveRoleSidebarSettings(false); });
      $sidebarRoleReset.addEventListener('click', function () { saveRoleSidebarSettings(true); });
    }
    if ($sidebarUserAdmin) {
      $sidebarUserSave.addEventListener('click', function () { saveUserSidebarSettings(false); });
      $sidebarUserReset.addEventListener('click', function () { saveUserSidebarSettings(true); });
    }
  }

  // ── Init ───────────────────────────────────────────────────────────
  initSidebarVisibility();
  loadUsers('');

})();
