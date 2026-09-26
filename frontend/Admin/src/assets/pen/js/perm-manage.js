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
  var saving = false;
  var userRequest = 0;

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
  get(PERM_BASE + 'options/').then(function (d) {
    window._permOptions = d;
    if (current) { renderRoles(); renderGroups(); updateSaveStatus(); }
  }).catch(function () { toast('گزینه‌های نقش و گروه بارگذاری نشد.', 'danger'); });

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
          return '<button type="button" class="pm-user' + active + '" data-id="' + esc(u.id) + '" aria-pressed="' + !!active + '">' +
            '<span class="pm-user-name">' + esc(u.name) + '</span>' +
            '<span class="pm-user-meta">' + esc(u.username) + (u.department ? ' · ' + esc(u.department) : '') + '</span></button>';
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
    var menuUserSave = document.getElementById('sidebar-user-save');
    var menuPending = menuUserSave && !menuUserSave.disabled;
    if (saving || (current && current.id !== id && (hasPendingChanges() || menuPending) && !window.confirm('تغییرات ذخیره‌نشده دارید. فرد دیگری را انتخاب می‌کنید؟'))) return;
    var request = ++userRequest;
    get(ACL_BASE + 'user/' + id + '/').then(function (data) {
      if (request !== userRequest) return;
      dirtyEntries = {};
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
      document.getElementById('pm-superuser-note').hidden = !data.is_superuser;
      document.getElementById('pm-acl-details').open = false;
      renderRoles();
      renderGroups();
      renderAclGrid();
      updateSaveStatus();
      loadSidebarUserSettings(id);
      $users.querySelectorAll('.pm-user').forEach(function (b) {
        var active = b.dataset.id === id;
        b.classList.toggle('active', active);
        b.setAttribute('aria-pressed', String(active));
      });
    }).catch(function (e) { if (request === userRequest) toast(e.message, 'danger'); });
  }

  // ── Roles ───────────────────────────────────────────────────────────
  function renderRoles() {
    var box = document.getElementById('pm-roles');
    var opts = window._permOptions || { roles: [] };
    var have = {};
    (current.roles || []).forEach(function (r) { have[r] = true; });
    box.innerHTML = (opts.roles || []).map(function (r) {
      return '<label class="pm-option"><input class="form-check-input" type="checkbox" data-role="' + esc(r.code) + '"' + (have[r.code] ? ' checked' : '') + (current.is_superuser ? ' disabled' : '') + '>' +
        '<span>' + esc(r.name) + '</span></label>';
    }).join('') || '<span class="text-muted fs-14">در حال بارگذاری نقش‌ها…</span>';
  }

  // ── Groups ─────────────────────────────────────────────────────────
  function renderGroups() {
    var box = document.getElementById('pm-groups');
    var opts = window._permOptions || { groups: [] };
    var have = {};
    (current.groups || []).forEach(function (g) { have[g] = true; });
    box.innerHTML = (opts.groups || []).map(function (g) {
      return '<label class="pm-option"><input class="form-check-input" type="checkbox" data-group="' + esc(g.name) + '"' + (have[g.name] ? ' checked' : '') + (current.is_superuser ? ' disabled' : '') + '>' +
        '<span>' + esc(g.name) + '</span></label>';
    }).join('') || '<span class="text-muted fs-14">' + (window._permOptions ? 'گروهی تعریف نشده است.' : 'در حال بارگذاری گروه‌ها…') + '</span>';
  }

  // ── One visible save action for the selected person's access ───────
  function checkedValues(selector, key) {
    return Array.prototype.slice.call(document.querySelectorAll(selector + ' input:checked')).map(function (c) { return c.dataset[key]; }).sort();
  }
  function sameValues(a, b) { return JSON.stringify((a || []).slice().sort()) === JSON.stringify((b || []).slice().sort()); }
  function rolesChanged() { return current && window._permOptions && !sameValues(checkedValues('#pm-roles', 'role'), current.roles); }
  function groupsChanged() { return current && window._permOptions && !sameValues(checkedValues('#pm-groups', 'group'), current.groups); }
  function hasPendingChanges() { return !!(rolesChanged() || groupsChanged() || Object.keys(dirtyEntries).length); }
  function updateSaveStatus(message) {
    var count = (rolesChanged() ? 1 : 0) + (groupsChanged() ? 1 : 0) + Object.keys(dirtyEntries).length;
    document.getElementById('pm-save-status').textContent = message || (count ? count + ' تغییر در انتظار ذخیره' : 'بدون تغییر');
    document.getElementById('pm-save').disabled = saving || !count || !!(current && current.is_superuser);
  }
  document.getElementById('pm-roles').addEventListener('change', function () { updateSaveStatus(); });
  document.getElementById('pm-groups').addEventListener('change', function () { updateSaveStatus(); });
  document.getElementById('pm-save').addEventListener('click', async function () {
    if (!current || saving || !hasPendingChanges()) return;
    saving = true;
    updateSaveStatus('در حال ذخیره…');
    var errors = [];
    var id = current.id;
    if (rolesChanged()) {
      try {
        var roles = checkedValues('#pm-roles', 'role');
        var roleRes = await post(PERM_BASE + 'user/' + id + '/roles/', { roles: roles });
        if (!roleRes.ok) throw new Error(roleRes.b.error || roleRes.b.detail || 'ذخیره نشد');
        current.roles = roleRes.b.roles || roles;
        loadUsers($search.value.trim());
      } catch (e) { errors.push('نقش‌ها: ' + e.message); }
    }
    if (groupsChanged()) {
      try {
        var groups = checkedValues('#pm-groups', 'group');
        var groupRes = await post(PERM_BASE + 'user/' + id + '/groups/', { groups: groups });
        if (!groupRes.ok) throw new Error(groupRes.b.error || groupRes.b.detail || 'ذخیره نشد');
        current.groups = groupRes.b.groups || groups;
      } catch (e) { errors.push('گروه‌ها: ' + e.message); }
    }
    if (Object.keys(dirtyEntries).length) {
      try {
        var entries = Object.keys(dirtyEntries).map(function (key) {
          var parts = key.split('|');
          return { resource_type: parts[0], resource_key: parts[1], verbs: dirtyEntries[key] };
        });
        var aclRes = await post(ACL_BASE + 'user/' + id + '/bulk/', { entries: entries });
        if (!aclRes.ok || (aclRes.b.errors && aclRes.b.errors.length)) {
          throw new Error((aclRes.b.errors || []).map(function (e) { return e.error; }).join('، ') || aclRes.b.error || 'ذخیره نشد');
        }
        var fresh = await get(ACL_BASE + 'user/' + id + '/');
        syncEntries(fresh.entries || []);
        dirtyEntries = {};
        renderAclGrid();
      } catch (e) { errors.push('دسترسی‌های موردی: ' + e.message); }
    }
    saving = false;
    updateSaveStatus(errors.length ? 'بخشی ذخیره نشد؛ تغییرات باقی‌مانده را دوباره ذخیره کنید.' : undefined);
    toast(errors.length ? errors.join('؛ ') : 'تغییرات ذخیره شد.', errors.length ? 'danger' : 'success');
  });

  // ══════════════════════════════════════════════════════════════════
  // ACL Grid
  // ══════════════════════════════════════════════════════════════════

  var _entriesMap = {}; // (type, key) → verbs[] | null
  var $aclSearch = document.getElementById('acl-search');
  var $aclType = document.getElementById('acl-type');
  var $aclGrid = document.getElementById('acl-grid');
  var $aclEmpty = document.getElementById('acl-empty');
  var $aclFilterClear = document.getElementById('acl-filter-clear');

  function currentVerbs(type, key) {
    var v = _entriesMap[entryKey(type, key)];
    return Object.prototype.hasOwnProperty.call(dirtyEntries, entryKey(type, key)) ? dirtyEntries[entryKey(type, key)] : (v !== undefined ? v : null);
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
    if (!rows.length) { $aclGrid.innerHTML = ''; updateSaveStatus(); return; }

    var allVerbs = catalog.verbs ? Object.keys(catalog.verbs) : ['view', 'add', 'change', 'delete'];

    var h = '<table class="table table-sm table-hover align-middle mb-0">';
    h += '<thead class="table-light"><tr>';
    h += '<th style="width:80px">وضعیت</th>';
    h += '<th>منبع</th>';
    h += '<th style="width:90px">نوع</th>';
    allVerbs.forEach(function (v) { h += '<th class="text-center" style="width:58px">' + verbLabel(v) + '</th>'; });
    h += '</tr></thead><tbody>';

    rows.forEach(function (r) {
      var hasExplicit = currentVerbs(r.category, r.key) !== null;
      var isSuper = current.is_superuser;
      var checkboxCols = allVerbs.map(function (v) {
        if (r.verbs.indexOf(v) === -1) return '<td class="text-center text-muted">—</td>';
        var cv = currentVerbs(r.category, r.key);
        var checked = isSuper || (cv !== null && (cv || []).indexOf(v) !== -1);
        var rowClass = hasExplicit ? 'acl-row-explicit' : '';
        return '<td class="text-center ' + rowClass + '">' +
          '<input type="checkbox" class="acl-verb" aria-label="' + esc(verbLabel(v) + '، ' + r.title) + '"' +
          ' data-type="' + esc(r.category) + '" data-key="' + esc(r.key) + '" data-verb="' + esc(v) + '"' +
          (checked ? ' checked' : '') + (isSuper ? ' disabled' : '') + '></td>';
      }).join('');

      h += '<tr class="' + (hasExplicit ? 'acl-row-explicit' : '') + '">' +
        '<td><span class="pm-acl-state">' + (hasExplicit ? 'موردی' : 'پیش‌فرض') + '</span></td>' +
        '<td><span class="fw-medium">' + esc(r.title) + '</span></td>' +
        '<td><span class="badge bg-light text-dark border"><i data-lucide="' + (CAT_ICON[r.category] || 'circle') + '" class="size-3 me-1"></i>' + (CAT_LABEL[r.category] || r.category) + '</span></td>' +
        checkboxCols + '</tr>';
    });

    h += '</tbody></table>';
    $aclGrid.innerHTML = h;
    icons();

    $aclGrid.querySelectorAll('.acl-verb').forEach(function (cb) {
      cb.addEventListener('change', onVerbChange);
    });

    document.getElementById('pm-acl-count').textContent = current.entries.length ? current.entries.length + ' مورد تنظیم‌شده' : 'برای موارد استثنا';
    updateSaveStatus();
  }

  function onVerbChange(e) {
    var cb = e.target;
    var type = cb.dataset.type;
    var key = cb.dataset.key;
    var verb = cb.dataset.verb;
    var ekey = entryKey(type, key);

    var original = _entriesMap[ekey] || null;
    var previous = currentVerbs(type, key);
    var verbs = previous ? previous.slice() : [];

    if (cb.checked) {
      if (verbs.indexOf(verb) === -1) verbs.push(verb);
    } else {
      verbs = verbs.filter(function (v) { return v !== verb; });
    }
    if (sameValues(verbs, original || [])) delete dirtyEntries[ekey];
    else dirtyEntries[ekey] = verbs;

    // Visual highlight
    var row = cb.closest('tr');
    row.classList.toggle('acl-row-explicit', !!currentVerbs(type, key));
    row.querySelector('.pm-acl-state').textContent = currentVerbs(type, key) ? 'موردی' : 'پیش‌فرض';
    updateSaveStatus();
  }

  // Filter controls
  if ($aclSearch) $aclSearch.addEventListener('input', renderAclGrid);
  if ($aclType) $aclType.addEventListener('change', renderAclGrid);
  if ($aclFilterClear) $aclFilterClear.addEventListener('click', function () {
    if ($aclSearch) $aclSearch.value = '';
    if ($aclType) $aclType.value = 'all';
    renderAclGrid();
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
  var loadedRoleCode = '';

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
      return '<section class="pm-menu-group">' +
        '<h3>' + esc(group.name) + '</h3>' +
        '<div class="pm-menu-items">' + group.items.map(function (item) {
          return '<label class="pm-menu-item">' +
            '<input class="form-check-input mt-1 flex-shrink-0 sidebar-role-item" type="checkbox" data-key="' + esc(item.key) + '"' + (item.visible ? ' checked' : '') + '>' +
            '<span>' + esc(item.title) + '</span>' +
            '</label>';
        }).join('') + '</div></section>';
    }).join('');
    if ($sidebarRoleSave) $sidebarRoleSave.disabled = true;
    if ($sidebarRoleReset) $sidebarRoleReset.disabled = false;
    if ($sidebarRoleStatus) $sidebarRoleStatus.textContent = 'وضعیت نمایش برای نقش انتخاب‌شده.';
  }

  function loadRoleSidebarSettings(roleCode) {
    if (!roleCode || !$sidebarRoleGrid) return;
    loadedRoleCode = roleCode;
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
      return '<section class="pm-menu-group">' +
        '<h3>' + esc(group.name) + '</h3>' +
        '<div class="pm-menu-items">' + group.items.map(function (item) {
          var override = item.override === null ? 'inherit' : (item.override ? 'show' : 'hide');
          var effective = item.effective_visible ? 'در سایدبار نمایش داده می‌شود' : 'در سایدبار پنهان است';
          return '<label class="pm-menu-item">' +
            '<span class="flex-grow-1">' + esc(item.title) + '<small class="d-block text-muted sidebar-user-effective">' + effective + '</small></span>' +
            '<select class="form-select form-select-sm sidebar-user-item" data-key="' + esc(item.key) + '" style="width:auto;min-width:10rem">' +
            '<option value="inherit"' + (override === 'inherit' ? ' selected' : '') + '>پیروی از نقش‌ها</option>' +
            '<option value="show"' + (override === 'show' ? ' selected' : '') + '>نمایش</option>' +
            '<option value="hide"' + (override === 'hide' ? ' selected' : '') + '>پنهان</option>' +
            '</select></label>';
        }).join('') + '</div></section>';
    }).join('');
    if ($sidebarUserSave) $sidebarUserSave.disabled = true;
    if ($sidebarUserReset) $sidebarUserReset.disabled = false;
    if ($sidebarUserStatus) $sidebarUserStatus.textContent = 'تنظیم‌های این فرد؛ «پیروی از نقش‌ها» مقدار جداگانه را حذف می‌کند.';
  }

  function loadSidebarUserSettings(userId) {
    if (!$sidebarUserAdmin || !userId) return;
    document.getElementById('sidebar-user-prompt').textContent = 'نمایش منو برای «' + current.name + '»؛ هر بخش می‌تواند از نقش‌ها پیروی کند یا جداگانه تنظیم شود.';
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
        if ($sidebarRoleSave && !$sidebarRoleSave.disabled && !window.confirm('تغییر نمایش این نقش ذخیره نشده است. نقش دیگری را انتخاب می‌کنید؟')) {
          $sidebarRoleSelect.value = loadedRoleCode;
          return;
        }
        loadRoleSidebarSettings($sidebarRoleSelect.value);
      });
      $sidebarRoleGrid.addEventListener('change', function (e) {
        if (e.target.matches('.sidebar-role-item')) {
          $sidebarRoleStatus.textContent = 'تغییر در انتظار ذخیره';
          $sidebarRoleSave.disabled = false;
        }
      });
      $sidebarRoleSave.addEventListener('click', function () { saveRoleSidebarSettings(false); });
      $sidebarRoleReset.addEventListener('click', function () { saveRoleSidebarSettings(true); });
    }
    if ($sidebarUserAdmin) {
      $sidebarUserGrid.addEventListener('change', function (e) {
        if (e.target.matches('.sidebar-user-item')) {
          $sidebarUserStatus.textContent = 'تغییر در انتظار ذخیره';
          $sidebarUserSave.disabled = false;
        }
      });
      $sidebarUserSave.addEventListener('click', function () { saveUserSidebarSettings(false); });
      $sidebarUserReset.addEventListener('click', function () { saveUserSidebarSettings(true); });
    }
  }

  // ── Init ───────────────────────────────────────────────────────────
  function switchTabs(first, second, firstPanel, secondPanel) {
    function activate(active, inactive, shown, hidden) {
      active.classList.add('is-active');
      inactive.classList.remove('is-active');
      active.setAttribute('aria-selected', 'true');
      inactive.setAttribute('aria-selected', 'false');
      shown.hidden = false;
      hidden.hidden = true;
    }
    first.addEventListener('click', function () { activate(first, second, firstPanel, secondPanel); });
    second.addEventListener('click', function () { activate(second, first, secondPanel, firstPanel); });
    [first, second].forEach(function (tab, index) {
      tab.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
        e.preventDefault();
        var next = index ? first : second;
        next.click();
        next.focus();
      });
    });
  }
  if (document.getElementById('pm-menu-tab')) {
    switchTabs(document.getElementById('pm-access-tab'), document.getElementById('pm-menu-tab'),
      document.getElementById('pm-access-view'), document.getElementById('pm-menu-view'));
    switchTabs(document.getElementById('pm-menu-role-tab'), document.getElementById('pm-menu-user-tab'),
      document.getElementById('sidebar-role-admin'), document.getElementById('sidebar-user-admin'));
  }
  initSidebarVisibility();
  loadUsers('');

})();
