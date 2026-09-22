/*
 * Pen LMS — dynamic form builder (no build step; plain IIFE).
 * Server is the single source of truth: every value is re-validated by
 * /api/forms/ — conditionals here are only a display convenience.
 *
 * Reads context from window.__PEN_FORM_CTX__ (submission_form.html).
 */
(function () {
  'use strict';

  var ctx = window.__PEN_FORM_CTX__ || {};
  var form = document.getElementById('dynamic-form');
  if (!form) return;

  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';
  var draftId = ctx.submissionId || null; // filled in after first save
  var editing = function () { return !!draftId; };  // ── helpers ─────────────────────────────────────────────────────────
  var dirty = false;
  var saving = false;
  var saveStatus = document.getElementById('draft-save-status');

  function escapeHtml(s) {
    return window.htmlEscape ? window.htmlEscape(s) : String(s == null ? '' : s);
  }

  function fieldWrap(key) {
    return document.getElementById('field-' + key);
  }

  function showFieldErrors(errors) {
    // errors: {fieldKey: [msgs]} or {non_field_errors: [...], error: "..."}
    form.querySelectorAll('.pen-field-errors, .pen-errors').forEach(function (el) { el.remove(); });
    form.querySelectorAll('.pen-field.is-invalid').forEach(function (el) {
      el.classList.remove('is-invalid');
    });

    var summary = document.getElementById('pen-error-box');
    var list = document.getElementById('pen-error-list');
    var generic = [];
    var fieldMsgs = [];

    Object.keys(errors || {}).forEach(function (key) {
      var msgs = errors[key];
      if (!Array.isArray(msgs)) msgs = [String(msgs)];
      if (key === 'non_field_errors' || key === '__all__' || key === 'error' || key === 'detail') {
        msgs.forEach(function (m) { generic.push(escapeHtml(m)); });
        return;
      }
      var wrap = fieldWrap(key);
      var ul = document.createElement('div');
      ul.className = 'invalid-feedback pen-field-errors';
      ul.id = 'error_' + key;
      ul.setAttribute('role', 'alert');
      msgs.forEach(function (m) {
        var item = document.createElement('div');
        item.textContent = m;
        ul.appendChild(item);
      });
      fieldMsgs.push(key + ': ' + msgs.join('؛ '));
      if (wrap) {
        wrap.classList.add('is-invalid');
        var help = wrap.querySelector('.form-text');
        if (help && help.parentNode) help.parentNode.insertBefore(ul, help.nextSibling);
        else wrap.appendChild(ul);
      } else {
        generic.push(escapeHtml(key + ': ' + msgs.join('؛ ')));
      }
    });

    if (list) {
      list.innerHTML = '';
      generic.concat(fieldMsgs).forEach(function (m) {
        var li = document.createElement('li');
        li.textContent = m;
        list.appendChild(li);
      });
    }
    if (summary) {
      var hasAny = generic.length > 0 || fieldMsgs.length > 0;
      summary.hidden = !hasAny;
      if (hasAny) summary.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function extractErrors(payload, fallback) {
    if (payload && typeof payload === 'object') return payload;
    return { error: fallback || 'خطای نامشخص' };
  }

  // ── conditional visibility (display only) ───────────────────────────

  function conditionValueOf(definition) {
    var key = definition.field;
    // boolean inputs use data-bool-key (no name attr)
    var boolEl = form.querySelector('[data-bool-key="' + key + '"]');
    if (boolEl) return boolEl.checked;
    var els = form.elements[key];
    if (!els) return undefined;
    if (els.length && els[0].type === 'checkbox') {
      var vals = [];
      Array.prototype.forEach.call(els, function (el) {
        if (el.checked) vals.push(el.value);
      });
      return vals;
    }
    return els.value;
  }

  function evaluateCondition(conditional) {
    // Mirrors apps/forms/schema_validation.evaluate_condition.
    var actual = conditionValueOf(conditional);
    var expected = conditional.value;
    switch (conditional.operator) {
      case 'exists': return actual != null && actual !== '' && (!Array.isArray(actual) || actual.length > 0);
      case 'eq': return actual == expected; // coerce: DOM values are strings
      case 'neq': return !(actual == expected);
      case 'in': return Array.isArray(expected) && Array.prototype.indexOf.call(expected, String(actual)) !== -1;
      case 'not_in': return Array.isArray(expected) && Array.prototype.indexOf.call(expected, String(actual)) === -1;
      default: return false;
    }
  }

  function applyConditionals() {
    form.querySelectorAll('[data-conditional]').forEach(function (wrap) {
      var parsed;
      try { parsed = JSON.parse(wrap.dataset.conditional); } catch (e) { parsed = null; }
      if (!parsed) { wrap.hidden = false; return; }
      var visible = evaluateCondition(parsed);
      wrap.hidden = !visible;
    });
  }

  // ── payload builder ─────────────────────────────────────────────────

  function collect() {
    var data = {};
    var tableRows = {}; // key -> array of row objects

    // 1) scalar inputs/selects/textarea
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name) return;
      var name = el.name;
      if (name === 'csrfmiddlewaretoken') return;

      if (name.indexOf('.') !== -1) {
        // table cell: key.<idx>.<col>
        var parts = name.split('.');
        var key = parts[0], idx = parseInt(parts[1], 10), col = parts.slice(2).join('.');
        tableRows[key] = tableRows[key] || [];
        tableRows[key][idx] = tableRows[key][idx] || {};
        if (el.type === 'select-multiple') {
          var mv = [];
          Array.prototype.forEach.call(el.options, function (o) { if (o.selected) mv.push(o.value); });
          tableRows[key][idx][col] = mv;
        } else {
          tableRows[key][idx][col] = el.value;
        }
        return;
      }

      if (el.type === 'checkbox' && !el.dataset.boolKey) {
        // multi-value checkbox group
        if (el.checked) {
          if (!(name in data)) data[name] = [];
          data[name].push(el.value);
        } else if (!(name in data)) {
          data[name] = [];
        }
        return;
      }

      if (el.type === 'select-multiple') {
        var vals = [];
        Array.prototype.forEach.call(el.options, function (o) { if (o.selected) vals.push(o.value); });
        data[name] = vals;
        return;
      }

      data[name] = el.value;
    });

    // 2) booleans (data-bool-key): real true/false — validator requires bool
    form.querySelectorAll('[data-bool-key]').forEach(function (el) {
      data[el.dataset.boolKey] = el.checked;
    });

    // 3) file fields → attachment id arrays (two-phase flow)
    form.querySelectorAll('[data-attachment-list]').forEach(function (ul) {
      var key = ul.dataset.attachmentList;
      var ids = [];
      ul.querySelectorAll('[data-attachment-id]').forEach(function (li) {
        ids.push(li.dataset.attachmentId);
      });
      data[key] = ids;
    });

    // 4) tables: compact sparse arrays, drop fully-empty rows
    Object.keys(tableRows).forEach(function (key) {
      var rows = tableRows[key].map(function (row) {
        if (!row) return null;
        var hasAny = Object.keys(row).some(function (c) {
          var v = row[c];
          return !(v == null || v === '' || (Array.isArray(v) && !v.length));
        });
        return hasAny ? row : null;
      }).filter(Boolean);
      data[key] = rows;
    });

    // 5) jalali → gregorian: the UI shows the Persian picker (data-jalali),
    //    but the dynamic-form validator expects ISO gregorian — convert
    //    date (YYYY/MM/DD→YYYY-MM-DD) and datetime (+HH:MM) at the boundary.
    form.querySelectorAll('[data-jalali]').forEach(function (el) {
      var key = el.name;
      var raw = (el.value || '').trim();
      if (!raw || !window.penJalaliToISO) return;
      var isDt = el.hasAttribute('data-jalali-dt');
      var parts = raw.split(/\s+/);
      var iso = window.penJalaliToISO(parts[0]);
      if (!iso) return; // leave as-is; server validation surfaces the error
      data[key] = isDt ? (iso + ' ' + (parts[1] || '00:00')) : iso;
    });

    return data;
  }

  // ── dynamic tables ──────────────────────────────────────────────────

  // Cell inputs carry their column key in data-col; renumberTable() rebuilds
  // the authoritative name (`<fieldKey>.<rowIndex>.<col>`) from it, so rows
  // added client-side and rows rendered server-side both reindex correctly.
  function makeCell(kind, colKey, colLabel, statuses, value) {
    var td = document.createElement('td');
    var el;
    if (kind === 'attendance_table' && colKey === 'status') {
      el = document.createElement('select');
      (statuses || []).forEach(function (st) {
        var o = document.createElement('option');
        o.value = st; o.textContent = st;
        if (value === st) o.selected = true;
        el.appendChild(o);
      });
      el.setAttribute('aria-label', 'وضعیت حضور');
    } else if (kind === 'grade_table' && colKey === 'result') {
      el = document.createElement('select');
      [['passed', 'قبول'], ['failed', 'مردود']].forEach(function (pair) {
        var o = document.createElement('option');
        o.value = pair[0]; o.textContent = pair[1];
        if (value === pair[0]) o.selected = true;
        el.appendChild(o);
      });
      el.setAttribute('aria-label', 'نتیجه ارزشیابی');
    } else {
      el = document.createElement('input');
      el.className = 'form-control form-control-sm';
      el.value = value == null ? '' : value;
      el.setAttribute('aria-label', colLabel);
    }
    el.className = (el.className || '') + (el.tagName === 'SELECT' ? ' form-select form-select-sm' : '');
    el.dataset.col = colKey;
    td.appendChild(el);
    return td;
  }

  function renumberTable(container) {
    var tbody = container.querySelector('tbody');
    var key = container.dataset.tableField;
    Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function (tr, i) {
      tr.querySelectorAll('input, select').forEach(function (el) {
        var col = el.dataset.col;
        if (col == null) {
          // Derive colKey from an existing `<key>.<idx>.<col>` server name.
          var re = new RegExp('^' + key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\.\\d+\\.(.+)$');
          var m = re.exec(el.name || '');
          col = m ? m[1] : null;
          if (col != null) el.dataset.col = col;
        }
        if (col != null) el.name = key + '.' + i + '.' + col;
      });
      var idxCell = tr.querySelector('td');
      if (idxCell) idxCell.textContent = String(i + 1);
    });
  }

  function addTableRow(container, value) {
    var kind = container.dataset.tableKind;
    var statuses = [], results = [], columns = [];
    try { statuses = JSON.parse(container.dataset.statuses || '[]'); } catch (e) {}
    try { results = JSON.parse(container.dataset.results || '[]'); } catch (e) {}
    try { columns = JSON.parse(container.dataset.columns || '[]'); } catch (e) {}

    var tbody = container.querySelector('tbody');
    var tr = document.createElement('tr');

    var idxTd = document.createElement('td');
    idxTd.textContent = '•';
    tr.appendChild(idxTd);

    if (kind === 'attendance_table') {
      tr.appendChild(makeCell(kind, 'student_id', 'شناسه دانش‌آموز', [], value && value.student_id));
      tr.appendChild(makeCell(kind, 'status', 'وضعیت', statuses, value && value.status));
      tr.appendChild(makeCell(kind, 'note', 'یادداشت', [], value && value.note));
    } else if (kind === 'grade_table') {
      tr.appendChild(makeCell(kind, 'student_id', 'شناسه دانش‌آموز', [], value && value.student_id));
      tr.appendChild(makeCell(kind, 'result', 'نمره نهایی (قبول/مردود)', results, value && value.result));
      tr.appendChild(makeCell(kind, 'teacher_note', 'چرایی (توسط استاد)', [], value && value.teacher_note));
    } else {
      (columns || []).forEach(function (col) {
        var v = value ? value[col.key] : '';
        tr.appendChild(makeCell(kind, col.key, col.label || col.key, [], v));
      });
    }

    var actionsTd = document.createElement('td');
    var del = document.createElement('button');
    del.type = 'button';
    del.className = 'btn btn-sm btn-outline-danger';
    del.setAttribute('aria-label', 'حذف ردیف');
    del.innerHTML = '<i data-lucide="trash-2" class="size-4"></i>';
    del.addEventListener('click', function () {
      tr.remove();
      renumberTable(container);
      if (window.penRenderIcons) window.penRenderIcons();
    });
    actionsTd.appendChild(del);
    tr.appendChild(actionsTd);

    tbody.appendChild(tr);
    renumberTable(container);
    if (window.penRenderIcons) window.penRenderIcons();
  }

  form.querySelectorAll('[data-table-field]').forEach(function (container) {
    var addBtn = container.querySelector('[data-add-row]');
    if (addBtn) {
      addBtn.addEventListener('click', function () { addTableRow(container, null); });
    }
    container.addEventListener('click', function (e) {
      var del = e.target.closest('[data-remove-row]');
      if (del) {
        del.closest('tr').remove();
        renumberTable(container);
        if (window.penRenderIcons) window.penRenderIcons();
      }
    });
    // server-rendered rows get proper numbering
    renumberTable(container);
  });

  // ── file dropzones (two-phase upload) ───────────────────────────────

  // ── lightweight rich-text editors (no external library) ─────────────
  form.querySelectorAll('[data-rich-for]').forEach(function (editor) {
    var key = editor.dataset.richFor;
    var source = document.getElementById('id_' + key);
    if (!source) return;
    // Seed the editor from the (old-value) textarea; server output is already
    // sanitized HTML, so innerHTML here is safe.
    if (source.value) editor.innerHTML = source.value;
    var sync = function () { source.value = editor.innerHTML; };
    editor.addEventListener('input', sync);
    editor.addEventListener('blur', sync);
    // Toolbar buttons act on the editor without stealing focus.
    var toolbar = form.querySelector('[data-rich-toolbar-for="' + key + '"]');
    if (toolbar) {
      toolbar.querySelectorAll('[data-rich-cmd]').forEach(function (btn) {
        btn.addEventListener('mousedown', function (e) { e.preventDefault(); });
        btn.addEventListener('click', function () {
          editor.focus();
          document.execCommand(btn.dataset.richCmd, false, null);
          sync();
        });
      });
    }
  });

  var GLOBAL_MAX_BYTES = 10 * 1024 * 1024; // FORMS_MAX_UPLOAD_SIZE default

  function fileFieldDef(key) {
    var zone = form.querySelector('[data-dropzone-for="' + key + '"]');
    if (!zone) return null;
    var def = { key: key, accept: [], maxBytes: GLOBAL_MAX_BYTES };
    if (zone.dataset.accept) {
      def.accept = zone.dataset.accept.split(',').map(function (s) {
        return s.trim().replace(/^\./, '').toLowerCase();
      }).filter(Boolean);
    }
    var max = parseInt(zone.dataset.maxSize, 10);
    // Cap must be a sane positive number of BYTES; anything else (0, empty,
    // garbage — e.g. someone typed megabytes) falls back to the global limit
    // so we can never produce "حداکثر 0MB".
    if (!isNaN(max) && max >= 1024) def.maxBytes = Math.min(def.maxBytes, max);
    return def;
  }

  function preCheckUpload(def, file) {
    if (def && def.accept && def.accept.length) {
      var m = /\.([a-z0-9]+)$/i.exec(file.name);
      if (m && def.accept.indexOf(m[1].toLowerCase()) === -1) {
        return 'پسوند فایل مجاز نیست (مجاز: ' + def.accept.join('، ') + ')';
      }
    }
    if (file.size > def.maxBytes) {
      var mb = def.maxBytes / 1048576;
      var mbText = mb >= 1 ? Math.round(mb) : Math.round(mb * 10) / 10;
      return 'حجم فایل بیش از حد مجاز است (حداکثر ' + mbText + 'MB)';
    }
    return null;
  }

  function renderAttachmentItem(list, att, pending) {
    var li = document.createElement('li');
    li.className = 'pen-attachment-item';
    if (att && att.id) li.dataset.attachmentId = att.id;
    li.innerHTML =
      '<i data-lucide="' + (pending ? 'loader' : 'paperclip') + '" class="size-4 flex-shrink-0 text-muted"></i>' +
      '<div class="flex-grow-1 overflow-hidden">' +
      '<span class="d-block text-truncate">' + escapeHtml(att && (att.original_filename || att.name) || 'در حال بارگذاری…') + '</span>' +
      '</div>';
    if (att && att.id) {
      var del = document.createElement('button');
      del.type = 'button';
      del.className = 'btn btn-sm btn-outline-danger flex-shrink-0';
      del.setAttribute('aria-label', 'حذف پیوست');
      del.innerHTML = '<i data-lucide="x" class="size-4"></i>';
      del.addEventListener('click', function () { li.remove(); if (window.penRenderIcons) window.penRenderIcons(); });
      li.appendChild(del);
    }
    list.appendChild(li);
    if (window.penRenderIcons) window.penRenderIcons();
    return li;
  }

  function ensureDraftSaved() {
    // Files attach to an existing submission; silently create the draft on
    // first upload so the drop-zone "just works" on the create page.
    if (draftId) {
      ctx.attachmentsEndpoint = '/api/forms/submissions/' + draftId + '/attachments/';
      return Promise.resolve(draftId);
    }
    var payload = { schema_slug: ctx.schemaSlug, data: collect() };
    return postJson('/api/forms/submissions/', payload, 'POST').then(function (res) {
      if (!res.ok) {
        showFieldErrors(extractErrors(res.body));
        throw new Error('ذخیره خودکار پیش‌نویس ناموفق بود');
      }
      draftId = res.body.id;
      ctx.submissionId = draftId;
      ctx.attachmentsEndpoint = '/api/forms/submissions/' + draftId + '/attachments/';
      // Point the draft button at PATCH so a later click doesn't duplicate.
      return draftId;
    });
  }

  function uploadAttachment(file, fieldKey, list) {
    var def = fileFieldDef(fieldKey) || { maxMB: 10, accept: [] };
    var preErr = preCheckUpload(def, file);
    if (preErr) { window.penToast(preErr, 'danger'); return; }

    var placeholder = renderAttachmentItem(list, { original_filename: file.name }, true);

    ensureDraftSaved()
      .then(function () {
        var fd = new FormData();
        fd.append('field_key', fieldKey);
        fd.append('file', file, file.name);
        return fetch(ctx.attachmentsEndpoint, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'X-CSRFToken': CSRF },
          body: fd,
        });
      })
      .then(function (resp) {
        if (!resp) return null;
        return resp.json().catch(function () { return {}; }).then(function (body) {
          return { ok: resp.ok, status: resp.status, body: body };
        });
      })
      .then(function (res) {
        if (!res) return;
        if (!res.ok) {
          placeholder.remove();
          var msg = (res.body && (res.body.file || res.body.error || res.body.detail)) ||
            ('بارگذاری ناموفق (' + res.status + ')');
          window.penToast(Array.isArray(msg) ? msg.join('؛ ') : String(msg), 'danger');
          return;
        }
        // swap placeholder → confirmed attachment row
        placeholder.remove();
        renderAttachmentItem(list, res.body, false);
      })
      .catch(function (err) {
        placeholder.remove();
        window.penToast('خطا در بارگذاری فایل: ' + err, 'danger');
      });
  }

  form.querySelectorAll('[data-dropzone-for]').forEach(function (zone) {
    var key = zone.dataset.dropzoneFor;
    var picker = zone.querySelector('[data-file-picker]');
    var list = form.querySelector('[data-attachment-list="' + key + '"]');

    zone.addEventListener('click', function () { picker && picker.click(); });
    zone.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); picker && picker.click(); }
    });
    picker && picker.addEventListener('change', function () {
      Array.prototype.forEach.call(picker.files, function (f) { uploadAttachment(f, key, list); });
      picker.value = '';
    });
    ['dragenter', 'dragover'].forEach(function (ev) {
      zone.addEventListener(ev, function (e) {
        e.preventDefault();
        zone.classList.add('is-dragover');
      });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
      zone.addEventListener(ev, function (e) {
        e.preventDefault();
        zone.classList.remove('is-dragover');
      });
    });
    zone.addEventListener('drop', function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files) Array.prototype.forEach.call(files, function (f) { uploadAttachment(f, key, list); });
    });
  });

  // ── section steps (progress bar; sections are NOT hidden — avoid
  //    confusing drafts — the bar just tracks scroll position) ─────────

  var progress = document.getElementById('pen-progress');
  var sections = form.querySelectorAll('fieldset.pen-section');
  if (progress && sections.length > 1) {
    progress.hidden = false;
    sections.forEach(function (section, i) {
      var bar = document.createElement('span');
      bar.title = section.dataset.stepTitle || ('مرحله ' + (i + 1));
      if (i === 0) bar.classList.add('done');
      progress.appendChild(bar);
    });
    window.addEventListener('scroll', function () {
      var reached = 0;
      sections.forEach(function (section, i) {
        if (section.getBoundingClientRect().top < window.innerHeight * 0.5) reached = i;
      });
      progress.querySelectorAll('span').forEach(function (bar, i) {
        bar.classList.toggle('done', i <= reached);
      });
    });
  }

  // ── submit / draft ──────────────────────────────────────────────────

  function postJson(url, body, method) {
    return fetch(url, {
      method: method || 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF,
        'Idempotency-Key': (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + '-' + Math.random()),
      },
      body: JSON.stringify(body || {}),
    }).then(function (resp) {
      return resp.json().catch(function () { return {}; }).then(function (payload) {
        return { ok: resp.ok, status: resp.status, body: payload };
      });
    });
  }

  function setBusy(button, busy) {
    if (!button) return;
    button.disabled = busy;
    button.setAttribute('aria-busy', busy ? 'true' : 'false');
  }

  function afterSave(submission) {
    window.location.href = '/forms/submissions/' + submission.id + '/';
  }

  function setSaveStatus(text, tone) {
    if (!saveStatus) return;
    saveStatus.textContent = text;
    saveStatus.className = 'fs-13 ' + (tone === 'danger' ? 'text-danger' : 'text-muted');
  }

  function saveDraftSilently() {
    if (!dirty || saving) return Promise.resolve();
    saving = true;
    setSaveStatus('در حال ذخیرهٔ پیش‌نویس…');
    var payload = editing()
      ? { data: collect() }
      : { schema_slug: ctx.schemaSlug, data: collect() };
    var url = editing() ? '/api/forms/submissions/' + draftId + '/' : '/api/forms/submissions/';
    return postJson(url, payload, editing() ? 'PATCH' : 'POST')
      .then(function (res) {
        if (!res.ok) { setSaveStatus('ذخیره نشد؛ بعداً دوباره تلاش می‌کنیم.', 'danger'); return; }
        if (!draftId) draftId = res.body.id;
        dirty = false;
        setSaveStatus('پیش‌نویس ذخیره شد.');
      })
      .catch(function () { setSaveStatus('ذخیره نشد؛ اتصال را بررسی کنید.', 'danger'); })
      .finally(function () { saving = false; });
  }

  var draftBtn = document.getElementById('save-draft');
  var submitBtn = document.getElementById('submit-form');

  if (draftBtn) {
    draftBtn.addEventListener('click', function () {
      setBusy(draftBtn, true);
      var payload = editing()
        ? { data: collect() }
        : { schema_slug: ctx.schemaSlug, data: collect() };
      var url = editing() ? '/api/forms/submissions/' + draftId + '/' : '/api/forms/submissions/';
      postJson(url, payload, editing() ? 'PATCH' : 'POST')
        .then(function (res) {
          if (res.status === 409) {
            window.penToast('این فرم دیگر قابل ویرایش نیست (وضعیت تغییر کرده است).', 'danger');
            return;
          }
          if (!res.ok) { showFieldErrors(extractErrors(res.body)); return; }
          if (!draftId) draftId = res.body.id;
          dirty = false;
          setSaveStatus('پیش‌نویس ذخیره شد.');
          afterSave(res.body);
        })
        .catch(function (err) { window.penToast('خطا: ' + err, 'danger'); })
        .finally(function () { setBusy(draftBtn, false); });
    });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    setBusy(submitBtn, true);
    var data = collect();

    var firstPass = editing()
      ? postJson('/api/forms/submissions/' + draftId + '/', { data: data }, 'PATCH')
      : postJson('/api/forms/submissions/', { schema_slug: ctx.schemaSlug, data: data }, 'POST');

    firstPass
      .then(function (res) {
        if (!res.ok) { showFieldErrors(extractErrors(res.body)); return null; }
        if (!draftId) draftId = res.body.id; // subsequent submit-time PATCHes reuse it
        return res;
      })
      .then(function (saved) {
        if (!saved) return;
        return postJson('/api/forms/submissions/' + draftId + '/submit/', {})
          .then(function (res) {
            if (res.status === 409) {
              window.penToast('این فرم قبلاً ارسال شده است.', 'danger');
              return;
            }
            if (!res.ok) {
              // submit-time errors are field-keyed; show them on the saved draft.
              showFieldErrors(extractErrors(res.body));
              return;
            }
            afterSave(res.body);
          });
      })
      .catch(function (err) { window.penToast('خطا: ' + err, 'danger'); })
      .finally(function () { setBusy(submitBtn, false); });
  });

  form.addEventListener('input', applyConditionals);
  form.addEventListener('change', applyConditionals);
  form.addEventListener('input', function () { dirty = true; setSaveStatus('تغییرات ذخیره‌نشده است.'); });
  form.addEventListener('change', function () { dirty = true; setSaveStatus('تغییرات ذخیره‌نشده است.'); });
  window.setInterval(saveDraftSilently, 20000);
  window.addEventListener('beforeunload', function (event) {
    if (!dirty || saving) return;
    event.preventDefault();
    event.returnValue = '';
  });
  applyConditionals();

  // Jalali pickers: hydrate server-rendered ISO values to Jalali text,
  // then arm the theme's picker. collect() converts back on submit.
  (function hydrateJalali() {
    if (window.penISOToJalali) {
      form.querySelectorAll('[data-jalali]').forEach(function (el) {
        var v = (el.value || '').trim();
        if (!/^\d{4}-\d{2}-\d{2}/.test(v)) return; // already jalali or empty
        var time = el.hasAttribute('data-jalali-dt') ? (v.split(/[T ]/)[1] || '').slice(0, 5) : '';
        var j = window.penISOToJalali(v.slice(0, 10));
        if (j) el.value = time ? (j + ' ' + time) : j;
      });
    }
    if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  })();
})();
