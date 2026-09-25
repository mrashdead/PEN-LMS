/*
 * Pen LMS — visual form-schema builder (no build step).
 *
 * Contract with the server:
 *   • Saving POSTs {slug,title,description,version,is_active,fields} to
 *     /api/forms/admin/schemas/ (FormSchemaAdminView) — the server runs
 *     validate_form_fields() and is the ONLY authority; this UI performs
 *     the same checks client-side purely for instant feedback.
 *   • Editing never mutates a published version: every save posts a NEW
 *     version (version field is editable pre-save).
 *   • The raw JSON textarea is the source of truth when edited ("apply").
 *
 * Reads context from #pen-builder-ctx (json_script in schema_builder.html).
 */
(function () {
  'use strict';

  var ctxEl = document.getElementById('pen-builder-ctx');
  if (!ctxEl) return;
  var CTX = JSON.parse(ctxEl.textContent);
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  var fields = Array.isArray(CTX.fields) ? CTX.fields.map(function (f) { return JSON.parse(JSON.stringify(f)); }) : [];
  var nextOrder = fields.reduce(function (m, f) { return Math.max(m, f.order || 0); }, 0) + 1;

  var $fields = document.getElementById('b-fields');
  var $empty = document.getElementById('b-empty');
  var $json = document.getElementById('b-json');

  var TYPES = [
    ['text', 'متن'], ['textarea', 'متن بلند'], ['rich_text', 'متن غنی'],
    ['number', 'عدد'], ['integer', 'عدد صحیح'], ['decimal', 'عدد اعشاری'],
    ['date', 'تاریخ'], ['datetime', 'تاریخ و ساعت'], ['time', 'ساعت'],
    ['select', 'انتخابی'], ['multi_select', 'چند انتخابی'], ['boolean', 'بله/خیر'],
    ['relation', 'ارجاع'], ['multi_relation', 'ارجاع چندگانه'],
    ['file', 'فایل'], ['table', 'جدول آزاد'],
    ['attendance_table', 'جدول حضور'], ['grade_table', 'جدول ارزشیابی'],
  ];
  var RELATION_KEYS = (CTX.relationRegistry || []);
  var OPERATORS = [['eq', 'مساوی'], ['neq', 'نامساوی'], ['in', 'مقدار در لیست'], ['not_in', 'مقدار بیرون لیست'], ['exists', 'پر باشد']];

  // ── helpers ─────────────────────────────────────────────────────────

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : String(s == null ? '' : s); }

  function relabel(key) {
    var hit = RELATION_KEYS.filter(function (r) { return r.key === key; })[0];
    return hit ? hit.key + (hit.available ? '' : ' (نصب‌نشده)') : key + ' (نامعتبر)';
  }

  function toast(msg, kind) { window.penToast && window.penToast(msg, kind); }

  function renumber() {
    // order = position × 10 keeps room for insertions
    fields.forEach(function (f, i) { f.order = (i + 1) * 10; });
    nextOrder = fields.length * 10 + 10;
  }

  function uniqueKey(base) {
    var taken = {};
    fields.forEach(function (f) { taken[f.key] = true; });
    if (!(base in taken)) return base;
    var i = 2;
    while (base + '_' + i in taken) i++;
    return base + '_' + i;
  }

  // ── field card ──────────────────────────────────────────────────────

  function cardHtml(f, idx) {
    var t = f.type || 'text';
    var html = '';
    html += '<div class="card builder-field" draggable="true" data-idx="' + idx + '">';
    html += '<div class="card-header d-flex align-items-center gap-2 py-2">';
    html += '<i data-lucide="grip-vertical" class="size-4 text-muted" title="کشیدن برای تغییر ترتیب"></i>';
    html += '<span class="badge bg-primary-subtle text-primary">' + esc(f.type) + '</span>';
    html += '<strong class="fs-14">' + esc(f.label || f.key || 'بی‌نام') + '</strong>';
    html += '<code class="fs-13 text-muted">' + esc(f.key || '') + '</code>';
    if (f.required) html += '<span class="badge bg-danger-subtle text-danger">الزامی</span>';
    if (f.conditional) html += '<span class="badge bg-info-subtle text-info">شرطی</span>';
    html += '<span class="ms-auto d-flex gap-1">';
    html += '<button class="btn btn-sm btn-light" data-act="up" title="بالا"><i data-lucide="chevron-up" class="size-4"></i></button>';
    html += '<button class="btn btn-sm btn-light" data-act="down" title="پایین"><i data-lucide="chevron-down" class="size-4"></i></button>';
    html += '<button class="btn btn-sm btn-outline-danger" data-act="del" title="حذف"><i data-lucide="trash-2" class="size-4"></i></button>';
    html += '</span></div>';
    html += '<div class="card-body py-3 d-none" data-body>';

    // key + label + type
    html += '<div class="row g-2 mb-2">';
    html += '<div class="col-12 col-md-4"><label class="form-label fs-14">کلید (key)</label><input class="form-control form-control-sm" dir="ltr" data-k="key" value="' + esc(f.key) + '"></div>';
    html += '<div class="col-12 col-md-4"><label class="form-label fs-14">برچسب</label><input class="form-control form-control-sm" data-k="label" value="' + esc(f.label || '') + '"></div>';
    html += '<div class="col-12 col-md-4"><label class="form-label fs-14">نوع</label><select class="form-select form-select-sm" data-k="type">';
    TYPES.forEach(function (p) { html += '<option value="' + p[0] + '"' + (t === p[0] ? ' selected' : '') + '>' + p[1] + ' (' + p[0] + ')</option>'; });
    html += '</select></div></div>';

    // flags
    html += '<div class="d-flex flex-wrap gap-3 mb-2 fs-14">';
    html += '<div class="form-check"><input class="form-check-input" type="checkbox" data-k="required" id="req_' + idx + '"' + (f.required ? ' checked' : '') + '><label class="form-check-label" for="req_' + idx + '">الزامی</label></div>';
    html += '<div class="form-check"><input class="form-check-input" type="checkbox" data-k="column_span" id="span_' + idx + '"' + (f.column_span === 2 ? ' checked' : '') + '><label class="form-check-label" for="span_' + idx + '">نیم‌عرض (کنار فیلد قبل)</label></div>';
    html += '<div class="form-check"><input class="form-check-input" type="checkbox" data-k="help_text_on" id="help_' + idx + '"' + (f.help_text ? ' checked' : '') + '><label class="form-check-label" for="help_' + idx + '">متن راهنما</label></div>';
    html += '</div>';

    html += '<div class="row g-2">';
    // placeholder / section
    html += '<div class="col-12 col-md-4"><label class="form-label fs-14">جای‌نگهدار</label><input class="form-control form-control-sm" data-k="placeholder" value="' + esc(f.placeholder || '') + '"></div>';
    html += '<div class="col-12 col-md-4"><label class="form-label fs-14">بخش (section)</label><input class="form-control form-control-sm" data-k="section" value="' + esc(f.section || '') + '"></div>';
    html += '<div class="col-12 col-md-4" data-help-wrap style="display:' + (f.help_text ? '' : 'none') + '"><label class="form-label fs-14">متن راهنما</label><input class="form-control form-control-sm" data-k="help_text" value="' + esc(f.help_text || '') + '"></div>';

    // text-ish constraints
    if (['text', 'textarea', 'rich_text'].indexOf(t) !== -1) {
      html += '<div class="col-6 col-md-3"><label class="form-label fs-14">حداقل طول</label><input type="number" class="form-control form-control-sm" dir="ltr" data-k="min_length" value="' + esc(f.min_length != null ? f.min_length : '') + '"></div>';
      html += '<div class="col-6 col-md-3"><label class="form-label fs-14">حداکثر طول</label><input type="number" class="form-control form-control-sm" dir="ltr" data-k="max_length" value="' + esc(f.max_length != null ? f.max_length : '') + '"></div>';
      html += '<div class="col-12 col-md-6"><label class="form-label fs-14">الگوی regex</label><input class="form-control form-control-sm" dir="ltr" data-k="pattern" value="' + esc(f.pattern || '') + '"></div>';
    }

    // numeric bounds
    if (['number', 'integer', 'decimal'].indexOf(t) !== -1) {
      html += '<div class="col-6 col-md-3"><label class="form-label fs-14">کمینه</label><input type="number" class="form-control form-control-sm" dir="ltr" data-k="min" value="' + esc(f.min != null ? f.min : '') + '"></div>';
      html += '<div class="col-6 col-md-3"><label class="form-label fs-14">بیشینه</label><input type="number" class="form-control form-control-sm" dir="ltr" data-k="max" value="' + esc(f.max != null ? f.max : '') + '"></div>';
    }

    // options editor
    if (['select', 'multi_select'].indexOf(t) !== -1) {
      html += '<div class="col-12"><label class="form-label fs-14">گزینه‌ها (value|label در هر خط)</label>';
      html += '<textarea class="form-control form-control-sm font-monospace" dir="ltr" rows="3" data-k="__options">';
      (f.options || []).forEach(function (o) { html += o.value + '|' + o.label + '\n'; });
      html += '</textarea></div>';
    }

    // relation picker
    if (['relation', 'multi_relation'].indexOf(t) !== -1) {
      html += '<div class="col-12 col-md-6"><label class="form-label fs-14">کلید رجیستری (سمت سرور ثابت است)</label><select class="form-select form-select-sm" data-k="__registry">';
      html += '<option value="">— انتخاب —</option>';
      RELATION_KEYS.forEach(function (r) {
        html += '<option value="' + esc(r.key) + '"' + (f.relation && f.relation.registry_key === r.key ? ' selected' : '') + '>' + esc(r.key + ' ← ' + r.model) + (r.available ? '' : ' [نصب‌نشده]') + '</option>';
      });
      html += '</select></div>';
      html += '<div class="col-6 col-md-3"><label class="form-label fs-14">فیلتر (JSON)</label><input class="form-control form-control-sm" dir="ltr" data-k="__filter" value=\'' + esc(f.relation && f.relation.filter ? JSON.stringify(f.relation.filter) : '') + '\'></div>';
      html += '<div class="col-6 col-md-3"><label class="form-label fs-14">ارجاع اختیاری؟</label><select class="form-select form-select-sm" data-k="__optional"><option value="0"' + (f.relation && f.relation.required === false ? '' : ' selected') + '>الزامی</option><option value="1"' + (f.relation && f.relation.required === false ? ' selected' : '') + '>اختیاری</option></select></div>';
    }

    // file constraints
    if (t === 'file') {
      html += '<div class="col-12 col-md-6"><label class="form-label fs-14">پسوندها (با نقطه، با کاما)</label><input class="form-control form-control-sm" dir="ltr" data-k="__accept" value="' + esc((f.accept || []).join(', ')) + '"></div>';
      html += '<div class="col-6 col-md-3"><label class="form-label fs-14">حداکثر حجم (مگابایت)</label><input type="number" step="0.1" min="0.1" class="form-control form-control-sm" dir="ltr" data-k="__max_mb" value="' + esc(f.max_file_size != null ? Math.round((f.max_file_size / 1048576) * 10) / 10 : '') + '"></div>';
    }

    // attendance/grade/table specifics
    if (t === 'attendance_table') {
      html += '<div class="col-12 col-md-6"><label class="form-label fs-14">وضعیت‌ها (کاما)</label><input class="form-control form-control-sm" dir="ltr" data-k="__statuses" value="' + esc((f.statuses || ['present', 'absent', 'late', 'excused']).join(', ')) + '"></div>';
    }
    if (t === 'grade_table') {
      html += '<div class="col-12 col-md-6"><label class="form-label fs-14">نتیجه‌ها (کاما)</label><input class="form-control form-control-sm" dir="ltr" data-k="__results" value="' + esc((f.results || ['passed', 'failed']).join(', ')) + '"></div>';
    }
    if (['attendance_table', 'grade_table', 'table'].indexOf(t) !== -1) {
      html += '<div class="col-6 col-md-3"><label class="form-label fs-14">حداکثر ردیف</label><input type="number" class="form-control form-control-sm" dir="ltr" data-k="max_rows" value="' + esc(f.max_rows != null ? f.max_rows : '') + '"></div>';
    }
    if (t === 'table') {
      html += '<div class="col-12"><label class="form-label fs-14">ستون‌ها (key|label در هر خط)</label>';
      html += '<textarea class="form-control form-control-sm font-monospace" dir="ltr" rows="2" data-k="__columns">';
      (f.columns || []).forEach(function (c) { html += c.key + '|' + (c.label || c.key) + '\n'; });
      html += '</textarea></div>';
    }

    // conditional
    html += '<div class="col-12"><div class="border rounded p-2 bg-light">';
    html += '<div class="form-check fs-14"><input class="form-check-input" type="checkbox" data-k="__cond_on" id="cond_' + idx + '"' + (f.conditional ? ' checked' : '') + '><label class="form-check-label" for="cond_' + idx + '">نمایش شرطی (فیلد تا شرط برقرار نشده مخفی می‌شود)</label></div>';
    html += '<div class="row g-2 mt-1" data-cond-wrap style="display:' + (f.conditional ? '' : 'none') + '">';
    html += '<div class="col-12 col-md-4"><input class="form-control form-control-sm" dir="ltr" placeholder="field" data-k="__cond_field" value="' + esc(f.conditional && f.conditional.field || '') + '"></div>';
    html += '<div class="col-6 col-md-3"><select class="form-select form-select-sm" data-k="__cond_op">';
    OPERATORS.forEach(function (p) { html += '<option value="' + p[0] + '"' + (f.conditional && f.conditional.operator === p[0] ? ' selected' : '') + '>' + p[1] + '</option>'; });
    html += '</select></div>';
    html += '<div class="col-6 col-md-5"><input class="form-control form-control-sm" dir="ltr" placeholder=\'value (JSON: "x" یا 1 یا ["a","b"])\' data-k="__cond_value" value=\'' + esc(f.conditional && 'value' in f.conditional ? JSON.stringify(f.conditional.value) : '') + '\'></div>';
    html += '</div></div></div>';

    html += '</div></div>'; // row + body
    html += '</div>';
    return html;
  }

  function render() {
    renumber();
    $fields.innerHTML = fields.map(cardHtml).join('');
    $empty.hidden = fields.length > 0;
    if (window.penRenderIcons) window.penRenderIcons();
    syncJson();
  }

  // ── JSON sync ───────────────────────────────────────────────────────

  function cleanField(f) {
    var out = {};
    var ORDER = ['key', 'type', 'order', 'label', 'required', 'column_span',
      'placeholder', 'section', 'help_text', 'min_length', 'max_length',
      'pattern', 'min', 'max', 'options', 'relation', 'accept',
      'max_file_size', 'mime_types', 'statuses', 'results', 'max_rows',
      'columns', 'conditional'];
    ORDER.forEach(function (k) {
      var v = f[k];
      if (v === undefined || v === null || v === '' || v === false) {
        // keep explicit false only for required
        if (k === 'required' && v === false) out[k] = false;
        return;
      }
      if (Array.isArray(v) && !v.length) return;
      if (typeof v === 'object' && !Array.isArray(v) && !Object.keys(v).length) return;
      out[k] = v;
    });
    return out;
  }

  function syncJson() {
    $json.value = JSON.stringify(fields.map(cleanField), null, 2);
  }

  function applyJson() {
    try {
      var parsed = JSON.parse($json.value);
      if (!Array.isArray(parsed)) throw new Error('آرایه فیلدها لازم است');
      fields = parsed.map(function (f) { return JSON.parse(JSON.stringify(f)); });
      render();
      toast('JSON روی بیلدر اعمال شد.', 'success');
    } catch (e) {
      toast('JSON نامعتبر: ' + e.message, 'danger');
    }
  }

  // ── card events (delegated) ─────────────────────────────────────────

  function bindCardEvents() {
    $fields.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-act]');
      var card = e.target.closest('.builder-field');
      if (!card) return;
      var idx = parseInt(card.dataset.idx, 10);

      if (btn) {
        e.preventDefault();
        var act = btn.dataset.act;
        if (act === 'del') { fields.splice(idx, 1); render(); }
        if (act === 'up' && idx > 0) { fields.splice(idx - 1, 0, fields.splice(idx, 1)[0]); render(); }
        if (act === 'down' && idx < fields.length - 1) { fields.splice(idx + 1, 0, fields.splice(idx, 1)[0]); render(); }
        return;
      }

      // header click toggles body
      if (e.target.closest('.card-header') && !e.target.closest('input,button,select')) {
        var body = card.querySelector('[data-body]');
        body.classList.toggle('d-none');
      }
    });

    // inputs → model
    $fields.addEventListener('input', function (e) {
      var el = e.target;
      var card = el.closest('.builder-field');
      if (!card) return;
      var idx = parseInt(card.dataset.idx, 10);
      var f = fields[idx];
      if (!f) return;
      var k = el.dataset.k;
      if (!k) return;

      switch (k) {
        case 'required': f.required = el.checked; break;
        case 'column_span': f.column_span = el.checked ? 2 : 1; break;
        case 'help_text_on':
          f.help_text = el.checked ? (f.help_text || '') : undefined;
          card.querySelector('[data-help-wrap]').style.display = el.checked ? '' : 'none';
          break;
        case '__options':
          f.options = el.value.split('\n').map(function (line) {
            var m = line.split('|');
            if (!m[0].trim()) return null;
            return { value: m[0].trim(), label: (m[1] || m[0]).trim() };
          }).filter(Boolean);
          break;
        case '__registry':
          f.relation = f.relation || {};
          if (el.value) { f.relation.registry_key = el.value; f.relation.lookup = 'id'; }
          else delete f.relation.registry_key;
          if (!f.relation.registry_key) delete f.relation;
          break;
        case '__optional':
          f.relation = f.relation || {};
          f.relation.required = el.value !== '1';
          break;
        case '__filter':
          f.relation = f.relation || {};
          try { f.relation.filter = el.value.trim() ? JSON.parse(el.value) : undefined; }
          catch (err) { /* leave as-is; server validate will catch */ }
          if (f.relation.filter === undefined) delete f.relation.filter;
          break;
        case '__accept':
          f.accept = el.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
          break;
        case '__statuses': f.statuses = el.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean); break;
        case '__results': f.results = el.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean); break;
        case '__columns':
          f.columns = el.value.split('\n').map(function (line) {
            var m = line.split('|');
            if (!m[0].trim()) return null;
            return { key: m[0].trim(), label: (m[1] || m[0]).trim(), type: 'text' };
          }).filter(Boolean);
          break;
        case '__cond_on':
          if (el.checked) f.conditional = f.conditional || { field: '', operator: 'eq', value: '' };
          else delete f.conditional;
          card.querySelector('[data-cond-wrap]').style.display = el.checked ? '' : 'none';
          break;
        case '__cond_field': f.conditional = f.conditional || {}; f.conditional.field = el.value.trim(); break;
        case '__cond_op': f.conditional = f.conditional || {}; f.conditional.operator = el.value; break;
        case '__cond_value':
          f.conditional = f.conditional || {};
          try { f.conditional.value = el.value.trim() ? JSON.parse(el.value) : ''; }
          catch (err) { f.conditional.value = el.value; }
          break;
        case '__max_mb':
          // UI is megabytes; the schema stores bytes. Guard against the
          // "0MB" bug: a blank/zero/negative value drops the cap entirely
          // (falls back to the server global limit), never writes 0 bytes.
          var mb = el.value === '' ? NaN : Number(el.value);
          if (mb > 0) f.max_file_size = Math.round(mb * 1048576);
          else delete f.max_file_size;
          break;
        default:
          if (el.type === 'number') {
            var n = el.value === '' ? undefined : Number(el.value);
            if (n === undefined) delete f[k]; else f[k] = n;
          } else if (el.type === 'checkbox') {
            f[k] = el.checked;
          } else {
            f[k] = el.value;
          }
      }
      syncJson();
      // live badge refresh (cheap: update header only)
      var header = card.querySelector('.card-header');
      header.querySelectorAll('.badge').forEach(function (b) { if (!b.dataset.keep) b.remove(); });
      var badgeZone = header.querySelector('span.ms-auto');
      var t = f.type || 'text';
      var badges = ['<span class="badge bg-primary-subtle text-primary">' + esc(t) + '</span>'];
      if (f.required) badges.push('<span class="badge bg-danger-subtle text-danger">الزامی</span>');
      if (f.conditional) badges.push('<span class="badge bg-info-subtle text-info">شرطی</span>');
      header.querySelectorAll('.badge').forEach(function (b) { b.remove(); });
      badgeZone.insertAdjacentHTML('beforebegin', badges.join(''));
      var strong = header.querySelector('strong');
      if (strong) strong.textContent = f.label || f.key || 'بی‌نام';
      var code = header.querySelector('code');
      if (code) code.textContent = f.key || '';
    });

    // drag & drop reorder
    var dragIdx = null;
    $fields.addEventListener('dragstart', function (e) {
      var card = e.target.closest('.builder-field');
      if (!card) return;
      dragIdx = parseInt(card.dataset.idx, 10);
      e.dataTransfer.effectAllowed = 'move';
    });
    $fields.addEventListener('dragover', function (e) {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
    });
    $fields.addEventListener('drop', function (e) {
      e.preventDefault();
      var card = e.target.closest('.builder-field');
      if (!card || dragIdx === null) return;
      var to = parseInt(card.dataset.idx, 10);
      if (to === dragIdx) return;
      var moved = fields.splice(dragIdx, 1)[0];
      fields.splice(to, 0, moved);
      dragIdx = null;
      render();
    });
  }

  // ── add field ───────────────────────────────────────────────────────

  document.getElementById('b-add-field').addEventListener('click', function () {
    fields.push({
      key: uniqueKey('field_' + (fields.length + 1)),
      type: 'text',
      order: nextOrder,
      label: 'فیلد تازه',
    });
    render();
    // open the new card's body
    var last = $fields.querySelector('.builder-field:last-child [data-body]');
    if (last) last.classList.remove('d-none');
  });

  // ── save / validate ─────────────────────────────────────────────────

  function payload() {
    renumber();
    return {
      slug: document.getElementById('b-slug').value.trim(),
      title: document.getElementById('b-title').value.trim(),
      description: document.getElementById('b-description').value.trim(),
      request_type_code: (document.getElementById('b-request-type') || {}).value || '',
      version: parseInt(document.getElementById('b-version').value, 10) || 1,
      is_active: true,
      fields: fields.map(cleanField),
    };
  }

  function clientCheck(p) {
    var errs = {};
    if (!/^[a-z][a-z0-9_]*$/.test(p.slug)) errs.slug = 'الگوی slug: ^[a-z][a-z0-9_]*$';
    if (!p.title) errs.title = 'عنوان لازم است';
    if (!p.fields.length) errs.fields = 'حداقل یک فیلد';
    var orders = {};
    var keys = {};
    p.fields.forEach(function (f, i) {
      if (!/^[a-z][a-z0-9_]*$/.test(f.key || '')) errs['فیلد ' + (i + 1)] = 'کلید نامعتبر';
      if (keys[f.key]) errs['فیلد ' + (i + 1)] = 'کلید تکراری: ' + f.key;
      keys[f.key] = true;
      if (f.order && f.order in orders) errs['فیلد ' + (i + 1)] = 'order تکراری';
      orders[f.order] = true;
    });
    return errs;
  }

  function post(validateOnly) {
    var p = payload();
    var errs = clientCheck(p);
    if (Object.keys(errs).length) {
      showResult(errs, true);
      return;
    }
    fetch(CTX.adminApiUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
      body: JSON.stringify(p),
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (body) {
        return { ok: r.ok, status: r.status, body: body };
      });
    }).then(function (res) {
      if (res.ok) {
        if (validateOnly) {
          toast('اعتبارسنجی سرور موفق بود ✓', 'success');
        } else {
          toast('فرم ذخیره شد (v' + res.body.version + ').', 'success');
          setTimeout(function () {
            window.location.href = '/forms/admin/schemas/' + res.body.slug + '/';
          }, 800);
        }
        return;
      }
      // server field errors → highlight
      showResult(res.body, false);
    }).catch(function (e) { toast('خطا: ' + e, 'danger'); });
  }

  function showResult(errs, isClient) {
    var lines = [];
    Object.keys(errs).forEach(function (k) {
      var v = errs[k];
      if (Array.isArray(v)) v.forEach(function (m) { lines.push(k + ': ' + m); });
      else lines.push(k + ': ' + String(v));
    });
    toast(lines.join(' — ') || (isClient ? 'خطای اعتبارسنجی' : 'خطای سرور'), 'danger');
  }

  document.getElementById('b-validate').addEventListener('click', function () { post(true); });
  document.getElementById('b-save').addEventListener('click', function () { post(false); });
  document.getElementById('b-json-apply').addEventListener('click', applyJson);
  document.getElementById('b-json-refresh').addEventListener('click', syncJson);

  // ── boot ────────────────────────────────────────────────────────────
  bindCardEvents();
  render();
})();
