/*
 * Pen LMS — generic resource engine (list + filters + create/detail modal).
 *
 * One script drives every configured page (/workspace/persons|lessons|…).
 * The server owns all authorization/validation: this JS only calls the
 * existing DRF endpoints and renders what they return. Field visibility
 * rules ("when") are UX conveniences — the API re-validates everything.
 *
 * Context: #pen-resource-ctx (json_script), window.__PEN_RES_WRITE__.
 */
(function () {
  'use strict';

  var ctxEl = document.getElementById('pen-resource-ctx');
  if (!ctxEl) return;
  var CFG = JSON.parse(ctxEl.textContent);
  var CAN_WRITE = window.__PEN_RES_WRITE__ === true;
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  var state = { page: 1, filters: {}, search: '' };
  // Group expansion survives API reloads during this page session without browser storage.
  var groupExpansion = {};

  var $thead = document.getElementById('res-thead-row');
  var $tbody = document.getElementById('res-tbody');
  var $count = document.getElementById('res-count');
  var $pager = document.getElementById('res-pager');
  var $search = document.getElementById('res-search');
  var $filters = document.getElementById('res-filters');
  var $add = document.getElementById('res-add');
  var $modalEl = document.getElementById('res-modal');
  var modal = window.bootstrap ? new window.bootstrap.Modal($modalEl) : null;

  // ── helpers ─────────────────────────────────────────────────────────

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }

  // 1234567 → "۱٬۲۳۴٬۵۶۷" (display only; stored value stays an integer).
  function money(n) {
    if (n == null || n === '') return '—';
    var num = Number(String(n).replace(/[^\d-]/g, ''));
    if (isNaN(num)) return esc(n);
    return window.persianNumbers(num.toLocaleString('en-US').replace(/,/g, '٬'));
  }

  function cellHtml(col, row) {
    var v = row[col.field];
    if (col.type === 'bool') {
      return v ? '<span class="badge bg-success-subtle text-success">بله</span>'
               : '<span class="badge bg-light text-muted border">خیر</span>';
    }
    if (col.type === 'badge') {
      return '<span class="badge bg-primary-subtle text-primary">' + esc(v == null || v === '' ? '—' : v) + '</span>';
    }
    if (col.type === 'money') {
      return '<span class="text-nowrap">' + money(v) + (col.suffix ? ' ' + esc(col.suffix) : '') + '</span>';
    }
    if (col.type === 'list') {
      var arr = Array.isArray(v) ? v : (v == null ? [] : [v]);
      return arr.length ? arr.map(function (x) { return esc(typeof x === 'object' ? (x.title || x.name || '') : x); }).join('، ') : '—';
    }
    if (col.type === 'jalali-time') {
      return '<span dir="ltr">' + esc(v == null || v === '' ? '—' : window.persianNumbers(v)) + '</span>';
    }
    return esc(v == null || v === '' ? '—' : v);
  }

  function errorLines(body) {
    var lines = [];
    Object.keys(body || {}).forEach(function (k) {
      var v = body[k];
      if (k === 'non_field_errors' || k === 'detail' || k === 'error') {
        (Array.isArray(v) ? v : [v]).forEach(function (m) { lines.push(String(m)); });
      } else {
        (Array.isArray(v) ? v : [v]).forEach(function (m) { lines.push(k + ': ' + m); });
      }
    });
    return lines.length ? lines : ['خطای نامشخص'];
  }

  // ── filters ─────────────────────────────────────────────────────────

  function renderFilters() {
    if (!CFG.filters) return;
    $filters.innerHTML = CFG.filters.map(function (f) {
      if (f.type === 'text') {
        return '<input type="search" class="form-control form-control-sm" data-filter="' + esc(f.param) + '" aria-label="' + esc(f.label) + '" placeholder="' + esc(f.placeholder || f.label) + '"' + (f.dir ? ' dir="' + esc(f.dir) + '"' : '') + ' style="min-width:150px">';
      }
      var opts = (f.options || []).map(function (o) {
        var selected = (state.filters[f.param] || '') === o.value ? ' selected' : '';
        return '<option value="' + esc(o.value) + '"' + selected + '>' + esc(o.label) + '</option>';
      }).join('');
      return '<select class="form-select form-select-sm" data-filter="' + esc(f.param) + '" aria-label="' + esc(f.label) + '" style="min-width:130px">' + opts + '</select>';
    }).join('');
    $filters.querySelectorAll('[data-filter]').forEach(function (control) {
      var eventName = control.tagName === 'INPUT' ? 'input' : 'change';
      var timer = null;
      control.addEventListener(eventName, function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
          var p = control.dataset.filter;
          if (control.value.trim()) state.filters[p] = control.value.trim();
          else delete state.filters[p];
          state.page = 1;
          load();
        }, eventName === 'input' ? 300 : 0);
      });
    });
  }

  // ── list ────────────────────────────────────────────────────────────

  function qs() {
    var params = new URLSearchParams();
    Object.keys(state.filters).forEach(function (k) { params.set(k, state.filters[k]); });
    if (state.search) params.set(CFG.searchParam || 'search', state.search);
    params.set('page', state.page);
    return params.toString();
  }

  function load() {
    $tbody.innerHTML = '<tr><td colspan="' + (CFG.columns.length + 1) + '"><div class="pen-loading">در حال بارگذاری…</div></td></tr>';
    $modalEl.setAttribute('aria-busy', 'true');
    fetch(CFG.api + '?' + qs(), {
      credentials: 'same-origin',
      headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
    })
      .then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(errorLines(b).join(' — ')); }); })
      .then(function (data) { renderRows(data); })
      .catch(function (e) {
        $tbody.innerHTML = '<tr><td colspan="' + (CFG.columns.length + 1) + '"><div class="pen-empty">' + esc(e.message) + '</div></td></tr>';
      })
      .finally(function () { $modalEl.removeAttribute('aria-busy'); });
  }

  function renderRows(data) {
    // header
    $thead.innerHTML = CFG.columns.map(function (c) {
      return '<th scope="col">' + esc(c.label) + '</th>';
    }).join('') + '<th scope="col" class="text-end">عملیات</th>';

    var results = data.results || [];
    if (!results.length) {
      $tbody.innerHTML = '<tr><td colspan="' + (CFG.columns.length + 1) + '"><div class="pen-empty"><p class="mb-0">موردی یافت نشد.</p></div></td></tr>';
    } else {
      var rowsHtml = [];
      var previousGroup = null;
      var groupIndex = 0;
      results.forEach(function (row, i) {
        var groupValue = CFG.groupBy ? (row[CFG.groupBy] || 'بدون گروه') : null;
        var groupKey = String(groupValue);
        if (CFG.groupBy && groupValue !== previousGroup) {
          var isExpanded = groupExpansion[groupKey] !== false;
          var groupId = 'res-group-' + groupIndex++;
          rowsHtml.push('<tr class="table-light pen-group-row" data-group-key="' + esc(groupKey) + '">' +
            '<th colspan="' + (CFG.columns.length + 1) + '" class="py-2 fw-semibold">' +
            '<button type="button" class="btn btn-sm btn-link p-0 me-2 align-middle" data-group-toggle="' + esc(groupKey) + '"' +
            ' aria-expanded="' + (isExpanded ? 'true' : 'false') + '" aria-controls="' + groupId + '" aria-label="نمایش یا مخفی کردن گروه ' + esc(groupValue) + '">' +
            '<i data-lucide="chevron-' + (isExpanded ? 'down' : 'left') + '" class="size-4"></i></button>' +
            '<span class="text-muted me-2">گروه کلاس</span><code dir="ltr">' + esc(groupValue) + '</code></th></tr>');
          previousGroup = groupValue;
        }
        var hidden = CFG.groupBy && groupExpansion[groupKey] === false;
        var tds = CFG.columns.map(function (c) { return '<td>' + cellHtml(c, row) + '</td>'; }).join('');
        var actions = row.actions || {view: true, edit: false, delete: false};
        var label = row.title || row.name || row.code || row.id;
        var menu = '<div class="dropdown pen-actions-dropdown text-end">' +
          '<button class="btn btn-sm btn-light" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="عملیات ' + esc(label) + '">' +
          '<i data-lucide="more-horizontal" class="size-4"></i></button>' +
          '<ul class="dropdown-menu dropdown-menu-end">' +
          (actions.view ? '<li><button type="button" class="dropdown-item" data-open><i data-lucide="eye" class="size-4"></i> مشاهده</button></li>' : '') +
          (actions.edit ? '<li><button type="button" class="dropdown-item" data-edit><i data-lucide="pencil" class="size-4"></i> ویرایش</button></li>' : '') +
          (actions.delete ? '<li><hr class="dropdown-divider"></li><li><button type="button" class="dropdown-item text-danger" data-delete-action data-delete-url="' + esc(CFG.api + row.id + '/delete/') + '" data-delete-name="' + esc(label) + '" data-delete-code="' + esc(row.code || row.id) + '"><i data-lucide="trash-2" class="size-4"></i> حذف نرم</button></li>' : '') +
          '</ul></div>';
        rowsHtml.push('<tr data-id="' + esc(row.id) + '" data-idx="' + i + '" data-group-row="' + esc(groupKey) + '" role="button" tabindex="0"' +
          (hidden ? ' hidden' : '') + '>' + tds +
               '<td class="text-nowrap text-end">' + menu + '</td></tr>');
      });
      $tbody.innerHTML = rowsHtml.join('');
    }

    // count text
    $count.textContent = data.count != null
      ? ('نمایش صفحهٔ ' + window.persianNumbers(state.page) + ' از مجموع ' + window.persianNumbers(data.count) + ' مورد')
      : '';

    // pager (prev/next driven by API links)
    $pager.innerHTML = '';
    if (data.previous || data.next) {
      var liPrev = document.createElement('li');
      liPrev.className = 'page-item' + (data.previous ? '' : ' disabled');
      liPrev.innerHTML = '<a class="page-link" href="#">قبلی</a>';
      if (data.previous) liPrev.querySelector('a').addEventListener('click', function (e) { e.preventDefault(); state.page--; load(); });
      $pager.appendChild(liPrev);

      var liNext = document.createElement('li');
      liNext.className = 'page-item' + (data.next ? '' : ' disabled');
      liNext.innerHTML = '<a class="page-link" href="#">بعدی</a>';
      if (data.next) liNext.querySelector('a').addEventListener('click', function (e) { e.preventDefault(); state.page++; load(); });
      $pager.appendChild(liNext);
    }

    // Group headers toggle all rows in that class without another API request.
    $tbody.querySelectorAll('[data-group-toggle]').forEach(function (toggle) {
      toggle.addEventListener('click', function () {
        var key = toggle.dataset.groupToggle;
        var expanded = toggle.getAttribute('aria-expanded') !== 'true';
        groupExpansion[key] = expanded;
        toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        var icon = toggle.querySelector('[data-lucide]');
        if (icon) icon.setAttribute('data-lucide', 'chevron-' + (expanded ? 'down' : 'left'));
        $tbody.querySelectorAll('tr[data-group-row]').forEach(function (row) {
          if (row.dataset.groupRow === key) row.hidden = !expanded;
        });
        if (window.penRenderIcons) window.penRenderIcons();
      });
    });

    // row → detail (fetch full object: list serializers carry fewer fields)
    $tbody.querySelectorAll('tr[data-id]').forEach(function (tr) {
      var idx = parseInt(tr.dataset.idx, 10);
      var row = results[idx];
      function open() {
        if (CFG.detail) {
          // has a detail contract → hydrate from the object endpoint
          fetch(CFG.api + row.id + '/?include_history=1', { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
            .then(function (r) { return r.ok ? r.json() : row; })
            .catch(function () { return row; })
            .then(function (full) { openDetail(full || row); });
        } else {
          openDetail(row);
        }
      }
      tr.addEventListener('click', function (event) {
        if (event.target.closest('button, a, [data-bs-toggle]')) return;
        open();
      });
      tr.addEventListener('keydown', function (e) { if (e.key === 'Enter') open(); });
      var edit = tr.querySelector('[data-edit]');
      if (edit) edit.addEventListener('click', function () {
        fetch(CFG.api + row.id + '/', {credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {}})
          .then(function (r) { return r.ok ? r.json() : row; }).catch(function () { return row; })
          .then(function (full) { openForm(row, full || row); });
      });
    });

    if (window.penRenderIcons) window.penRenderIcons();
  }

  // ── detail modal ────────────────────────────────────────────────────

  function dl(label, valueHtml) {
    return '<div class="row g-2 mb-1"><div class="col-5 col-md-4 text-muted fs-14">' + esc(label) +
           '</div><div class="col-7 col-md-8">' + valueHtml + '</div></div>';
  }

  function openDetail(row) {
    document.getElementById('res-modal-label').textContent = CFG.title + ' — جزئیات';
    var body = (CFG.detail || []).map(function (d) {
      var v = row[d.field];
      var html;
      if (d.type === 'registration-link') {
        var kind = d.kind === 'course' ? 'course' : 'offering';
        html = '<a class="btn btn-sm btn-outline-primary" href="/workspace/enrollments/' + kind + '/' + encodeURIComponent(row.id) + '/">مشاهده ثبت‌نام‌ها</a>';
      }
      else if (d.type === 'bool') html = v ? 'بله' : 'خیر';
      else if (d.type === 'money') html = '<span class="text-nowrap">' + money(v) + (d.suffix ? ' ' + esc(d.suffix) : '') + '</span>';
      else if (d.type === 'list') {
        var arr = Array.isArray(v) ? v : (v == null ? [] : [v]);
        html = arr.length ? arr.map(function (x) { return esc(typeof x === 'object' ? (x.title || x.name || '') : x); }).join('، ') : '—';
      }
      else if (d.type === 'classes') {
        var cls = Array.isArray(v) ? v : [];
        html = cls.length
          ? '<div class="table-responsive"><table class="table table-sm mb-0"><thead><tr>' +
            '<th>کد کلاس</th><th>درس</th><th>جلسات</th><th>بازه</th></tr></thead><tbody>' +
            cls.map(function (c) {
              return '<tr><td dir="ltr">' + esc(c.class_code) + '</td><td>' + esc(c.lesson_title || '—') + '</td>' +
                     '<td>' + window.persianNumbers(c.sessions) + ' جلسه</td>' +
                     '<td dir="ltr" class="fs-13">' + esc(c.first_date) + ' → ' + esc(c.last_date) + '</td></tr>';
            }).join('') + '</tbody></table></div>'
          : '<span class="text-muted">هنوز کلاسی تشکیل نشده — با دکمهٔ «تشکیل کلاس» اقدام کنید.</span>';
      }
      else if (typeof v === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v)) {
        html = '<span class="text-muted">(' + v.slice(0, 8) + '…)</span>';
      } else html = esc(v == null || v === '' ? '—' : v);
      return dl(d.label, html);
    }).join('');
    var meta = '<div class="pen-detail-meta">' +
      '<div><small>وضعیت</small><strong>' + esc(row.status || (row.is_active === false ? 'غیرفعال' : 'فعال')) + '</strong></div>' +
      '<div><small>ایجاد</small><strong dir="ltr">' + esc(row.created_at || '—') + '</strong></div>' +
      '<div><small>آخرین تغییر</small><strong dir="ltr">' + esc(row.updated_at || '—') + '</strong></div>' +
      '</div>';
    var history = Array.isArray(row.audit_trail) && row.audit_trail.length
      ? '<div class="mt-4 pt-3 border-top"><h6 class="fw-semibold mb-2">سوابق تغییرات</h6><ol class="pen-timeline mb-0">' +
        row.audit_trail.map(function (event) { return '<li class="pen-timeline-item"><div class="fw-semibold fs-14">' + esc(event.summary || event.kind) + '</div><div class="fs-13 text-muted">' + esc(event.actor || 'سامانه') + ' · ' + esc(event.created_at || '—') + '</div></li>'; }).join('') +
        '</ol></div>' : '';
    document.getElementById('res-modal-body').innerHTML = meta + '<div class="vstack gap-1">' + body + '</div>' + history;

    var footer = document.getElementById('res-modal-footer');
    footer.innerHTML = '';
    // edit action — rehydrate from the detail payload (openForm patches it)
    if (row.actions && row.actions.edit && row.id) {
      var bEdit = document.createElement('button');
      bEdit.className = 'btn btn-outline-primary';
      bEdit.innerHTML = '<i data-lucide="pencil" class="size-4 me-1"></i> ویرایش';
      bEdit.addEventListener('click', function () { openForm(row, row); });
      footer.appendChild(bEdit);
    }
    if (row.actions && row.actions.delete && row.id) {
      var bDelete = document.createElement('button');
      bDelete.className = 'btn btn-outline-danger';
      bDelete.innerHTML = '<i data-lucide="trash-2" class="size-4 me-1"></i> حذف نرم';
      bDelete.addEventListener('click', function () {
        window.penOpenDeleteModal({
          url: CFG.api + row.id + '/delete/',
          name: row.title || row.name || row.code || CFG.title,
          code: row.code || row.id,
          onSuccess: function () { modal.hide(); load(); },
        });
      });
      footer.appendChild(bDelete);
    }
    if (CFG.hasActions && row.id) {
      if (CAN_WRITE && !row.has_user) {
        var bUser = document.createElement('button');
        bUser.className = 'btn btn-outline-primary';
        bUser.innerHTML = '<i data-lucide="user-plus" class="size-4 me-1"></i> ساخت کاربر';
        bUser.addEventListener('click', function () {
          bUser.disabled = true;
          fetch(CFG.api + row.id + '/create-user/', {
            method: 'POST', credentials: 'same-origin',
            headers: Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}),
            body: '{}',
          }).then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
            .then(function (res) {
              if (res.ok) { toast('کاربر ساخته شد ✓', 'success'); modal.hide(); load(); }
              else toast(errorLines(res.b).join(' — '), 'danger');
            })
            .finally(function () { bUser.disabled = false; });
        });
        footer.appendChild(bUser);
      }
    }
    // «تشکیل کلاس» from an offering's detail (offerings page). Wait for the
    // detail modal to finish hiding before opening the wizard (two modals
    // racing leaves a stuck backdrop).
    if (CFG.formationAction && CAN_WRITE && row.id) {
      var bForm = document.createElement('button');
      bForm.className = 'btn btn-success';
      bForm.innerHTML = '<i data-lucide="graduation-cap" class="size-4 me-1"></i> تشکیل کلاس';
      bForm.addEventListener('click', function () {
        if (window.penOpenClassFormation) {
          var target = row.id;
          $modalEl.addEventListener('hidden.bs.modal', function onHidden() {
            $modalEl.removeEventListener('hidden.bs.modal', onHidden);
            window.penOpenClassFormation(target);
          });
          modal.hide();
        }
      });
      footer.appendChild(bForm);
    }
    // generate-sessions action (offerings): materialize weekly schedule
    if (CFG.generateAction && CAN_WRITE && row.id) {
      var ga = CFG.generateAction;
      var bGen = document.createElement('button');
      bGen.className = 'btn btn-outline-success';
      bGen.innerHTML = '<i data-lucide="calendar-plus" class="size-4 me-1"></i> ' + esc(ga.label);
      bGen.addEventListener('click', function () {
        if (!window.confirm(ga.confirm || 'مطمئنید؟')) return;
        bGen.disabled = true;
        fetch(CFG.api + row.id + '/' + ga.endpoint, {
          method: 'POST', credentials: 'same-origin',
          headers: Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}),
          body: '{}',
        }).then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
          .then(function (res) {
            bGen.disabled = false;
            if (!res.ok) { toast(errorLines(res.b).join(' — '), 'danger'); return; }
            var msg = window.persianNumbers(res.b.created || 0) + ' جلسه ساخته شد';
            if (res.b.skipped && res.b.skipped.length) msg += ' — ' + window.persianNumbers(res.b.skipped.length) + ' تداخل رد شد';
            toast(msg + ' ✓', 'success');
          })
          .catch(function (e) { bGen.disabled = false; toast('خطا: ' + e, 'danger'); });
      });
      footer.appendChild(bGen);
    }
    var bClose = document.createElement('button');
    bClose.className = 'btn btn-light';
    bClose.setAttribute('data-bs-dismiss', 'modal');
    bClose.textContent = 'بستن';
    footer.appendChild(bClose);

    modal.show();
    if (window.penRenderIcons) window.penRenderIcons();
  }

  // ── create modal ────────────────────────────────────────────────────

  // lookup select: options fetched from a list endpoint on first open
  var lookupCache = {};
  function labelFor(f, item) {
    if (f.labelTemplate) {
      return f.labelTemplate.replace(/\{(\w+)\}/g, function (_, key) {
        return item[key] == null ? '' : item[key];
      });
    }
    return item[f.labelField || 'title'] || item.name || item.id;
  }

  function populateLookup(sel, f) {
    var url = f.endpoint;
    if (lookupCache[url]) { fillOptions(sel, f, lookupCache[url]); return; }
    sel.innerHTML = '<option value="">در حال بارگذاری…</option>';
    fetch(url + (url.indexOf('?') !== -1 ? '&' : '?') + 'page_size=100', {
      credentials: 'same-origin',
      headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
    })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('خطا در دریافت گزینه‌ها')); })
      .then(function (data) {
        var items = data.results || data || [];
        lookupCache[url] = items;
        fillOptions(sel, f, items);
      })
      .catch(function (e) {
        sel.innerHTML = '<option value="">' + esc(e.message) + '</option>';
      });
  }

  function fillOptions(sel, f, items) {
    var multi = sel.multiple;
    sel.innerHTML = (multi ? '' : '<option value="">— انتخاب کنید —</option>') + items.map(function (item) {
      return '<option value="' + esc(item.id) + '">' + esc(labelFor(f, item)) + '</option>';
    }).join('');
    // edit-mode prefill may have arrived before the options did — apply now.
    if (sel._wanted != null) { applySelectWanted(sel, sel._wanted); }
  }

  // Select value(s) on a (possibly not-yet-populated) lookup. Kept on
  // sel._wanted so a later re-populate re-applies it too.
  function applySelectWanted(sel, wanted) {
    var list = (Array.isArray(wanted) ? wanted : [wanted]).map(String);
    if (sel.multiple) {
      Array.prototype.forEach.call(sel.options, function (o) {
        o.selected = list.indexOf(o.value) !== -1;
      });
    } else {
      var has = Array.prototype.some.call(sel.options, function (o) { return o.value === list[0]; });
      if (has) sel.value = list[0];
    }
    // mirrors (readonly-money / readonly-list) update on "change" — replay it
    // now that the pre-filled value actually resolved.
    if (sel.value) sel.dispatchEvent(new Event('change', { bubbles: true }));
  }

  // ── check-lookup: searchable checkbox list with clear selected state ──
  function initCheckLookups(form) {
    form.querySelectorAll('[data-check-lookup]').forEach(function (box) {
      var endpoint = box.dataset.endpoint;
      var labelField = box.dataset.labelField || 'title';
      var $list = box.querySelector('.cl-list');
      var $search = box.querySelector('.cl-search');
      var $summary = box.querySelector('.cl-summary');
      var items = lookupCache[endpoint];

      function renderList(filter) {
        var q = (filter || '').trim().toLowerCase();
        var shown = (items || []).filter(function (it) {
          if (!q) return true;
          var label = (it[labelField] || it.name || it.id || '').toLowerCase();
          var code = (it.code || '').toLowerCase();
          return label.indexOf(q) !== -1 || code.indexOf(q) !== -1;
        });
        if (!shown.length) { $list.innerHTML = '<div class="p-2 text-muted fs-14">' + (items ? 'موردی نیست.' : 'بارگذاری نشد.') + '</div>'; return; }
        $list.innerHTML = shown.map(function (it) {
          var checked = it.__checked ? ' checked' : '';
          return '<label class="cl-item d-flex align-items-center gap-2 px-2 py-1 border-bottom mb-0">' +
            '<input class="form-check-input" type="checkbox" data-cl-id="' + esc(it.id) + '"' + checked + '>' +
            '<span class="fs-14">' + esc(it[labelField] || it.name || it.id) + '</span>' +
            (it.code ? '<code class="fs-13 text-muted ms-auto">' + esc(it.code) + '</code>' : '') +
            '</label>';
        }).join('');
        $list.querySelectorAll('input[data-cl-id]').forEach(function (cb) {
          cb.addEventListener('change', function () {
            var it = items.filter(function (x) { return String(x.id) === cb.dataset.clId; })[0];
            if (it) it.__checked = cb.checked;
            updateSummary();
          });
        });
      }
      function updateSummary() {
        var n = (items || []).filter(function (x) { return x.__checked; }).length;
        $summary.textContent = window.persianNumbers(n) + ' مورد انتخاب شده';
      }
      function boot(list) {
        items = list;
        // fresh create form: clear any prior selection carried in the cache
        (items || []).forEach(function (x) { x.__checked = false; });
        // edit prefill: re-check the wanted ids (dataset set by openForm)
        var wanted = [];
        try { wanted = JSON.parse(box.dataset.wanted || '[]'); } catch (e) { wanted = []; }
        wanted = wanted.map(String);
        if (wanted.length) {
          (items || []).forEach(function (x) {
            if (wanted.indexOf(String(x.id)) !== -1) x.__checked = true;
          });
        }
        renderList('');
        updateSummary();
      }
      if (items) { boot(items); }
      else {
        fetch(endpoint + (endpoint.indexOf('?') !== -1 ? '&' : '?') + 'page_size=100', {
          credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
        }).then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('خطا')); })
          .then(function (d) { var arr = d.results || d || []; lookupCache[endpoint] = arr; boot(arr); })
          .catch(function () { $list.innerHTML = '<div class="p-2 text-danger fs-14">خطا در دریافت گزینه‌ها.</div>'; });
      }
      $search.addEventListener('input', function () { renderList($search.value); });
    });
  }

  // ── readonly-money: mirror a related object's amount (offering ← course) ──
  function initReadonlyMoney(form) {
    form.querySelectorAll('[data-readonly-money]').forEach(function (inp) {
      var sourceName = inp.dataset.source;
      var endpoint = inp.dataset.endpoint;
      var valueField = inp.dataset.valueField || 'tuition';
      var srcSel = form.querySelector('select[name="' + sourceName + '"]');
      if (!srcSel) return;
      function refresh() {
        var id = srcSel.value;
        if (!id) { inp.value = '—'; return; }
        var items = lookupCache[endpoint] || [];
        var it = items.filter(function (x) { return String(x.id) === id; })[0];
        if (it && it[valueField] != null) { inp.value = money(it[valueField]); return; }
        // not in cache (list may omit the field) → fetch the object once
        fetch(endpoint.replace(/\/$/, '') + '/' + id + '/', {
          credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
        }).then(function (r) { return r.ok ? r.json() : null; })
          .then(function (full) { inp.value = full && full[valueField] != null ? money(full[valueField]) : '—'; })
          .catch(function () { inp.value = '—'; });
      }
      srcSel.addEventListener('change', refresh);
      refresh();
    });
  }

  // ── readonly-list: mirror a related object's list (offering ← its course
  // lessons). The offering form shows the curriculum read-only, exactly as
  // the brief asks ("با انتخاب دوره، لیست دروس واکشی و نمایش داده شود").
  function initReadonlyLists(form) {
    form.querySelectorAll('[data-readonly-list]').forEach(function (box) {
      var sourceName = box.dataset.source;
      var endpoint = box.dataset.endpoint;
      var valueField = box.dataset.valueField || 'lesson_titles';
      var srcSel = form.querySelector('select[name="' + sourceName + '"]');
      if (!srcSel) return;
      function render(items) {
        var arr = (items || []).map(function (x) {
          return typeof x === 'object' ? (x.title || x.name || '') : String(x);
        }).filter(Boolean);
        box.innerHTML = arr.length
          ? arr.map(function (t) {
              return '<span class="badge bg-light text-dark border me-1 mb-1">' + esc(t) + '</span>';
            }).join('')
          : '<span class="text-muted">— درسی برای این دوره تعریف نشده —</span>';
      }
      function refresh() {
        var id = srcSel.value;
        if (!id) { render([]); return; }
        var cached = (lookupCache[endpoint] || []).filter(function (x) { return String(x.id) === id; })[0];
        if (cached && cached[valueField]) { render(cached[valueField]); return; }
        fetch(endpoint.replace(/\/$/, '') + '/' + id + '/', {
          credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
        }).then(function (r) { return r.ok ? r.json() : null; })
          .then(function (full) { render(full && full[valueField]); })
          .catch(function () { render([]); });
      }
      srcSel.addEventListener('change', refresh);
      refresh();
    });
  }

  function formField(f, value) {
    var req = f.required ? ' <span class="text-danger">*</span>' : '';
    var dir = f.dir ? ' dir="' + f.dir + '"' : '';
    var hint = f.hint ? '<div class="form-text">' + esc(f.hint) + '</div>' : '';
    var id = 'f_' + f.name;
    var inner;
    if (f.type === 'select') {
      inner = '<select class="form-select" id="' + id + '" name="' + f.name + '"' + (f.required ? ' required' : '') + dir + '>' +
        '<option value="">— انتخاب کنید —</option>' +
        f.options.map(function (o) {
          return '<option value="' + esc(o.value) + '"' + (value === o.value ? ' selected' : '') + '>' + esc(o.label) + '</option>';
        }).join('') + '</select>';
    } else if (f.type === 'lookup') {
      inner = '<select class="form-select" id="' + id + '" name="' + f.name + '"' + (f.required ? ' required' : '') + '>' +
        '<option value="">— انتخاب کنید —</option></select>';
    } else if (f.type === 'jalali-date') {
      inner = '<input class="form-control" id="' + id + '" name="' + f.name + '" type="text" dir="ltr"' +
        ' data-jalali placeholder="۱۴۰۴/۰۷/۰۱" inputmode="numeric" value="' + esc(value || '') + '"' +
        (f.required ? ' required' : '') + '>';
    } else if (f.type === 'jalali-time') {
      // API sends "HH:MM:SS" — the field contract is HH:MM.
      inner = '<input class="form-control" id="' + id + '" name="' + f.name + '" type="text" dir="ltr"' +
        ' data-jalali-time placeholder="۱۴:۳۰" inputmode="numeric" value="' + esc(String(value || '').slice(0, 5)) + '"' +
        (f.required ? ' required' : '') + '>';
    } else if (f.type === 'money') {
      // thousands-separated display; submitForm strips separators to an int
      var mval = (value === '' || value == null) ? '' : money(value).replace(/—/g, '');
      inner = '<div class="input-group">' +
        '<input class="form-control" id="' + id + '" name="' + f.name + '" type="text" dir="ltr"' +
        ' data-money inputmode="numeric" placeholder="۰" value="' + esc(mval) + '"' +
        (f.required ? ' required' : '') + '>' +
        '<span class="input-group-text fs-13">' + esc(f.unit || 'تومان') + '</span></div>';
    } else if (f.type === 'readonly-list') {
      // display-only mirror of a related object's list (offering ← lessons);
      // initReadonlyLists fills it from the source lookup.
      inner = '<div class="form-control bg-body-tertiary text-wrap" id="' + id + '" data-readonly-list' +
        ' data-source="' + esc(f.source || '') + '" data-endpoint="' + esc(f.endpoint || '') + '"' +
        ' data-value-field="' + esc(f.valueField || 'lesson_titles') + '"' +
        (f.itemsFrom ? ' data-items-from="' + esc(f.itemsFrom) + '"' : '') + '>' +
        '<span class="text-muted">— ابتدا منبع را انتخاب کنید —</span></div>';
    } else if (f.type === 'readonly-money') {
      // display-only mirror of a related object's amount (e.g. offering ← course
      // tuition). Never submitted; the source lookup fills it on change.
      inner = '<div class="input-group">' +
        '<input class="form-control bg-body-tertiary" id="' + id + '" type="text" dir="ltr" readonly' +
        ' data-readonly-money data-source="' + esc(f.source || '') + '" data-endpoint="' + esc(f.endpoint || '') + '"' +
        ' data-value-field="' + esc(f.valueField || 'tuition') + '" value="—">' +
        '<span class="input-group-text fs-13">تومان</span></div>';
    } else if (f.type === 'multi-lookup') {
      inner = '<select class="form-select" id="' + id + '" name="' + f.name + '" multiple size="6"' +
        (f.required ? ' required' : '') + '></select>' +
        '<div class="form-text">برای انتخاب چندتایی Ctrl را نگه دارید.</div>';
    } else if (f.type === 'check-lookup') {
      // searchable checkbox list — clear selected/unselected state
      inner = '<div class="check-lookup border rounded" data-check-lookup="' + f.name + '" data-endpoint="' + esc(f.endpoint) + '" data-label-field="' + esc(f.labelField || 'title') + '">' +
        '<div class="p-2 border-bottom"><input type="search" class="form-control form-control-sm cl-search" placeholder="جستجو…" aria-label="جستجو در گزینه‌ها"></div>' +
        '<div class="cl-list" style="max-height:220px;overflow-y:auto"><div class="p-2 text-muted fs-14">در حال بارگذاری…</div></div>' +
        '<div class="cl-summary px-2 py-1 border-top fs-13 text-muted">۰ مورد انتخاب شده</div></div>';
    } else if (f.type === 'schedule') {
      // days-of-week checkboxes + start/end time → stored as {days:[],start,end}
      var days = [['sat', 'شنبه'], ['sun', 'یکشنبه'], ['mon', 'دوشنبه'], ['tue', 'سه‌شنبه'],
        ['wed', 'چهارشنبه'], ['thu', 'پنجشنبه'], ['fri', 'جمعه']];
      inner = '<div class="border rounded p-2 w-100" data-schedule="' + f.name + '">' +
        '<div class="d-flex flex-wrap gap-2 mb-2">' +
        days.map(function (d) {
          return '<div class="form-check"><input class="form-check-input" type="checkbox" data-sched-day value="' + d[0] + '" id="sch_' + f.name + '_' + d[0] + '"><label class="form-check-label fs-14" for="sch_' + f.name + '_' + d[0] + '">' + d[1] + '</label></div>';
        }).join('') + '</div>' +
        '<div class="d-flex gap-2 align-items-center">' +
        '<input class="form-control form-control-sm" data-sched-start type="text" dir="ltr" data-jalali-time placeholder="۱۸:۰۰" aria-label="ساعت شروع">' +
        '<span class="text-muted">تا</span>' +
        '<input class="form-control form-control-sm" data-sched-end type="text" dir="ltr" data-jalali-time placeholder="۲۰:۰۰" aria-label="ساعت پایان">' +
        '</div></div>';
    } else if (f.type === 'textarea') {
      inner = '<textarea class="form-control" id="' + id + '" name="' + f.name + '" rows="2"' + dir + '>' + esc(value || '') + '</textarea>';
    } else if (f.type === 'checkbox') {
      return '<div class="form-check py-1"><input class="form-check-input" type="checkbox" id="' + id + '" name="' + f.name + '" value="true"><label class="form-check-label" for="' + id + '">' + esc(f.label) + '</label></div>';
    } else {
      inner = '<input class="form-control" id="' + id + '" name="' + f.name + '" type="' + (f.type || 'text') + '"' + dir + ' value="' + esc(value || '') + '"' + (f.required ? ' required' : '') + '>';
    }
    var wide = (f.type === 'check-lookup' || f.type === 'schedule' || f.type === 'textarea' || f.type === 'readonly-list');
    return '<div class="' + (wide ? 'col-12' : 'col-12 col-md-6') + '" data-when=\'' + esc(f.when ? JSON.stringify(f.when) : '') + '\'>' +
           '<label class="form-label" for="' + id + '">' + esc(f.label) + req + '</label>' + inner + hint + '</div>';
  }

  function openCreate() { openForm(null); }

  // ── generic create/edit modal ─────────────────────────────────────────
  // row == null → create (POST); otherwise edit (PATCH against the detail
  // endpoint). Prefill values come from the object response; every field
  // type knows how to seed itself. The API still re-validates everything.
  function openForm(row, full) {
    var editing = !!(row && row.id && row.actions && row.actions.edit);
    var src = full || row || {};
    document.getElementById('res-modal-label').textContent =
      CFG.title + (editing ? ' — ویرایش' : ' — افزودن');
    var fields = (CFG.form || []).map(function (f) {
      return formField(f, editing ? src[f.name] : '');
    }).join('');
    document.getElementById('res-modal-body').innerHTML =
      '<form id="res-form" novalidate><div class="row g-3">' + fields + '</div>' +
      '<div id="res-form-errors" class="pen-error-summary mt-3" role="alert" hidden><ul class="mb-0"></ul></div></form>';
    var footer = document.getElementById('res-modal-footer');
    footer.innerHTML = '';
    var bCancel = document.createElement('button');
    bCancel.className = 'btn btn-light';
    bCancel.setAttribute('data-bs-dismiss', 'modal');
    bCancel.textContent = 'انصراف';
    var bSave = document.createElement('button');
    bSave.className = 'btn btn-primary';
    bSave.innerHTML = '<i data-lucide="save" class="size-4 me-1"></i> ذخیره';
    bSave.addEventListener('click', function (e) { e.preventDefault(); submitForm(editing ? row.id : null); });
    footer.appendChild(bCancel);
    footer.appendChild(bSave);

    // conditional "when" fields
    var form = document.getElementById('res-form');
    // populate lookup + multi-lookup selects from their endpoints
    form.querySelectorAll('select[name]').forEach(function (sel) {
      var f = (CFG.form || []).filter(function (x) {
        return x.name === sel.name && (x.type === 'lookup' || x.type === 'multi-lookup');
      })[0];
      if (!f) return;
      // seed prefill BEFORE populate — fillOptions re-applies once loaded.
      var want = src[f.name];
      if (want != null && want !== '') { sel._wanted = Array.isArray(want) ? want : [String(want)]; }
      populateLookup(sel, f);
    });
    // live thousands formatting for money inputs
    form.querySelectorAll('[data-money]').forEach(function (inp) {
      inp.addEventListener('input', function () {
        var digits = inp.value.replace(/[^\d]/g, '');
        inp.value = digits ? Number(digits).toLocaleString('en-US').replace(/,/g, '٬') : '';
      });
    });
    // searchable checkbox lists (prerequisites, course lessons) — with prefill
    form.querySelectorAll('[data-check-lookup]').forEach(function (box) {
      var want = src[box.dataset.checkLookup];
      if (Array.isArray(want) && want.length) box.dataset.wanted = JSON.stringify(want.map(String));
    });
    initCheckLookups(form);
    // readonly money mirrors (offering tuition ← selected course)
    initReadonlyMoney(form);
    // readonly lists (offering lessons ← selected course)
    initReadonlyLists(form);
    // checkbox prefill
    form.querySelectorAll('[type="checkbox"][name]').forEach(function (cb) {
      var f = (CFG.form || []).filter(function (x) { return x.name === cb.name && x.type === 'checkbox'; })[0];
      if (f) cb.checked = src[f.name] === true;
    });
    // schedule prefill: {days:[…], start:"HH:MM", end:"HH:MM"}
    form.querySelectorAll('[data-schedule]').forEach(function (box) {
      var f = (CFG.form || []).filter(function (x) { return x.name === box.dataset.schedule && x.type === 'schedule'; })[0];
      var v = f ? src[f.name] : null;
      if (!v || typeof v !== 'object') return;
      (v.days || []).forEach(function (d) {
        var cb = box.querySelector('[data-sched-day][value="' + d + '"]');
        if (cb) cb.checked = true;
      });
      if (v.start) { var s = box.querySelector('[data-sched-start]'); if (s) s.value = v.start; }
      if (v.end) { var e2 = box.querySelector('[data-sched-end]'); if (e2) e2.value = v.end; }
    });
    function applyWhen() {
      form.querySelectorAll('[data-when]').forEach(function (wrap) {
        var raw = wrap.dataset.when;
        if (!raw || raw === '""') return;
        var when = JSON.parse(raw);
        var key = Object.keys(when)[0];
        var allowed = when[key] || [];
        var ctrl = form.elements[key];
        var show = !key || allowed.indexOf(ctrl ? ctrl.value : '') !== -1;
        wrap.style.display = show ? '' : 'none';
        wrap.querySelectorAll('input,select,textarea').forEach(function (el) { el.disabled = !show; });
      });
    }
    form.addEventListener('change', applyWhen);
    form.addEventListener('input', applyWhen);
    applyWhen();

    modal.show();
    if (window.penRenderIcons) window.penRenderIcons();
    if (window.penAttachJalaliPickers) window.penAttachJalaliPickers({ format: 'jalali' });
  }

  function submitForm(editId) {
    var form = document.getElementById('res-form');
    var payload = {};
    (CFG.form || []).forEach(function (f) {
      if (f.type === 'readonly-list') return;   // display-only mirror
      var el = form.elements[f.name];
      if (f.type === 'schedule') {
        var box = form.querySelector('[data-schedule="' + f.name + '"]');
        if (!box) return;
        var days = Array.prototype.slice.call(box.querySelectorAll('[data-sched-day]:checked')).map(function (c) { return c.value; });
        var s = box.querySelector('[data-sched-start]').value.trim();
        var e = box.querySelector('[data-sched-end]').value.trim();
        if (days.length || s || e) payload[f.name] = { days: days, start: s, end: e };
        return;
      }
      if (f.type === 'multi-lookup') {
        if (!el) return;
        var vals = Array.prototype.slice.call(el.selectedOptions).map(function (o) { return o.value; });
        if (vals.length) payload[f.name] = vals;
        return;
      }
      if (f.type === 'check-lookup') {
        var box = form.querySelector('[data-check-lookup="' + f.name + '"]');
        if (!box) return;
        var ids = Array.prototype.slice.call(box.querySelectorAll('input[data-cl-id]:checked')).map(function (c) { return c.dataset.clId; });
        payload[f.name] = ids; // always send (may be []) so clearing works on update
        return;
      }
      if (!el) return;
      var v = el.value;
      if (v === '' || v == null) {
        // clearing an optional field on edit must reach the server, but only
        // in a form the serializer accepts: '' for free text/dates, null for
        // optional FK lookups (UUIDField refuses '').
        if (editId && !f.required && (f.type === 'text' || f.type === 'jalali-date')) {
          payload[f.name] = '';
        } else if (editId && f.type === 'lookup' && !f.required) {
          payload[f.name] = null;
        }
        return;
      }
      if (f.type === 'money') {
        var n = Number(String(v).replace(/[^\d]/g, ''));
        payload[f.name] = isNaN(n) ? 0 : n;
        return;
      }
      if (el.type === 'checkbox') { payload[f.name] = el.checked; return; }
      payload[f.name] = v === 'true' ? true : v;
    });
    var box = document.getElementById('res-form-errors');
    fetch(CFG.api + (editId ? editId + '/' : ''), {
      method: editId ? 'PATCH' : 'POST', credentials: 'same-origin',
      headers: Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}),
      body: JSON.stringify(payload),
    }).then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
      .then(function (res) {
        if (res.ok) { toast('ثبت شد ✓', 'success'); modal.hide(); load(); return; }
        var lines = errorLines(res.b);
        box.querySelector('ul').innerHTML = lines.map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('');
        box.hidden = false;
      })
      .catch(function (e) { toast('خطا: ' + e, 'danger'); });
  }

  function toast(msg, kind) { window.penToast && window.penToast(msg, kind); }

  // ── boot ────────────────────────────────────────────────────────────

  if ($thead) {
    // debounce search
    var t = null;
    $search.addEventListener('input', function () {
      clearTimeout(t);
      t = setTimeout(function () { state.search = $search.value.trim(); state.page = 1; load(); }, 300);
    });
    if ($add && CAN_WRITE) $add.addEventListener('click', openCreate);
    // «تشکیل کلاس» button (sessions page) → formation wizard
    var $form = document.getElementById('res-formation');
    if ($form && CAN_WRITE && window.penOpenClassFormation) {
      $form.addEventListener('click', function () { window.penOpenClassFormation(); });
    }
    renderFilters();
    load();
  }

  // formation.js reloads the list after generating sessions
  window.__PEN_RES_RELOAD__ = load;
})();
