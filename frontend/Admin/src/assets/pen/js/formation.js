/*
 * Pen LMS — «تشکیل کلاس» wizard (form 2 of the offering/class pipeline).
 *
 * Flow: pick a CourseOffering → the offering's PROPOSED place / days+hours /
 * instructor / lessons / start-date auto-fill via GET
 * /api/education/offerings/{id}/formation/ → clerk edits anything (Override)
 * → live dry-run preview via POST /api/education/class-formation/preview/
 * → submit POST /api/education/class-formation/.
 *
 * Everything is re-validated server-side; the atomic generator writes exactly
 * N ClassSession rows. This file only orchestrates the three endpoints and
 * renders what they return — it never computes the schedule itself (the
 * preview is the server's own walk).
 *
 * Launched from resource.js via window.penOpenClassFormation(offeringId?).
 */
(function () {
  'use strict';

  var F_API = '/api/education/offerings/';
  var FORM_API = '/api/education/class-formation/';
  var TEACHERS_API = '/api/persons/?person_type=teacher&is_active=true&page_size=100';
  var LOCATIONS_API = '/api/education/locations/?page_size=100';

  var DAYS = [['sat', 'شنبه'], ['sun', 'یکشنبه'], ['mon', 'دوشنبه'], ['tue', 'سه‌شنبه'],
    ['wed', 'چهارشنبه'], ['thu', 'پنجشنبه'], ['fri', 'جمعه']];

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function pn(n) { return window.persianNumbers ? window.persianNumbers(n) : String(n == null ? '' : n); }
  function csrf() { return window.penCsrfHeader ? window.penCsrfHeader() : {}; }
  function toast(msg, kind) { window.penToast && window.penToast(msg, kind); }

  var modal = null, el = {};
  var state = { offering: null, prefill: null, teacher: null, location: null, previewT: null };

  // ── bootstrap the DOM once ──────────────────────────────────────────
  function ensureDom() {
    if (modal) return true;
    if (!window.bootstrap) { toast('فریمورک UI در دسترس نیست.', 'danger'); return false; }
    var host = document.createElement('div');
    host.innerHTML =
      '<div class="modal fade" id="pen-formation-modal" tabindex="-1" aria-labelledby="pf-title" aria-hidden="true">' +
      '<div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">' +
      '<div class="modal-content"><div class="modal-header">' +
      '<h6 class="modal-title mb-0" id="pf-title">تشکیل کلاس</h6>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="بستن"></button>' +
      '</div><div class="modal-body"><form id="pf-form" novalidate>' +
      '<div class="row g-3">' +
      // 1) offering (drives everything)
      '<div class="col-12 col-md-6"><label class="form-label" for="pf-offering">۱. برگزاری دوره <span class="text-danger">*</span></label>' +
      '<select class="form-select" id="pf-offering" required><option value="">— انتخاب برگزاری —</option></select>' +
      '<div class="form-text" id="pf-offering-meta"></div></div>' +
      // 2) class code
      '<div class="col-12 col-md-6"><label class="form-label" for="pf-code">کد کلاس <span class="text-danger">*</span></label>' +
      '<input class="form-control" id="pf-code" dir="ltr" placeholder="CLS-PY-01" required>' +
      '<div class="form-text">پیشنهاد خودکار پر می‌شود؛ قابل تغییر.</div></div>' +
      // 3) lesson (filtered to the offering's curriculum)
      '<div class="col-12 col-md-6"><label class="form-label" for="pf-lesson">درس <span class="text-danger">*</span></label>' +
      '<select class="form-select" id="pf-lesson" required><option value="">— ابتدا برگزاری را انتخاب کنید —</option></select>' +
      '<div class="form-text" id="pf-lesson-meta"></div></div>' +
      // 4) teacher
      '<div class="col-12 col-md-6"><label class="form-label" for="pf-teacher">استاد</label>' +
      '<select class="form-select" id="pf-teacher"><option value="">— از برگزاری برداشته می‌شود —</option></select></div>' +
      // 5) location
      '<div class="col-12 col-md-6"><label class="form-label" for="pf-location">محل برگزاری قطعی</label>' +
      '<select class="form-select" id="pf-location"><option value="">— از پیشنهاد برگزاری —</option></select></div>' +
      // 6) start date (jalali)
      '<div class="col-12 col-md-6"><label class="form-label" for="pf-date">تاریخ شروع قطعی (جلسهٔ اول)</label>' +
      '<input class="form-control" id="pf-date" type="text" dir="ltr" data-jalali placeholder="۱۴۰۴/۰۷/۰۱" autocomplete="off"></div>' +
      // 7) session count
      '<div class="col-12 col-md-6"><label class="form-label" for="pf-count">تعداد جلسات</label>' +
      '<div class="input-group"><input class="form-control" id="pf-count" type="number" min="1" max="200" dir="ltr">' +
      '<button class="btn btn-outline-secondary" type="button" id="pf-auto">محاسبه از مدت درس</button></div>' +
      '<div class="form-text" id="pf-count-hint">خالی = خودکار: مدت درس ÷ طول هر جلسه.</div></div>' +
      // schedule (days + hours) — wide
      '<div class="col-12"><label class="form-label">روزها و ساعات قطعی هر جلسه</label>' +
      '<div class="border rounded p-2" id="pf-sched">' +
      '<div class="d-flex flex-wrap gap-2 mb-2">' +
      DAYS.map(function (d) {
        return '<div class="form-check"><input class="form-check-input" type="checkbox" data-day value="' + d[0] + '" id="pf_d_' + d[0] + '">' +
          '<label class="form-check-label fs-14" for="pf_d_' + d[0] + '">' + d[1] + '</label></div>';
      }).join('') +
      '</div><div class="d-flex gap-2 align-items-center">' +
      '<input class="form-control form-control-sm" id="pf-start" type="text" dir="ltr" data-jalali-time placeholder="۱۶:۰۰" aria-label="ساعت شروع">' +
      '<span class="text-muted">تا</span>' +
      '<input class="form-control form-control-sm" id="pf-end" type="text" dir="ltr" data-jalali-time placeholder="۱۸:۰۰" aria-label="ساعت پایان">' +
      '<div class="form-check ms-auto"><input class="form-check-input" type="checkbox" id="pf-skip" checked>' +
      '<label class="form-check-label fs-14" for="pf-skip">پرش تعطیلات</label></div>' +
      '<div class="form-check"><input class="form-check-input" type="checkbox" id="pf-regen">' +
      '<label class="form-check-label fs-14" for="pf-regen">بازتولید جلسات</label></div>' +
      '</div></div></div>' +
      // preview
      '<div class="col-12"><div class="d-flex align-items-center gap-2 mb-1">' +
      '<h6 class="mb-0">پیش‌نمایش جلسات در تقویم</h6>' +
      '<span class="badge bg-light text-dark border" id="pf-prev-sum">—</span>' +
      '<button class="btn btn-sm btn-outline-primary ms-auto" type="button" id="pf-refresh">' +
      '<i data-lucide="refresh-cw" class="size-4 me-1"></i> پیش‌نمایش</button></div>' +
      '<div id="pf-preview" class="border rounded" style="max-height:260px;overflow:auto">' +
      '<div class="p-3 text-muted fs-14">پس از انتخاب برگزاری، پیش‌نمایش ساخته می‌شود.</div></div></div>' +
      '</div>' +
      '<div id="pf-errors" class="pen-error-summary mt-3" role="alert" hidden><ul class="mb-0"></ul></div>' +
      '</form></div>' +
      '<div class="modal-footer"><span id="pf-footnote" class="text-muted fs-13 me-auto"></span>' +
      '<button type="button" class="btn btn-light" data-bs-dismiss="modal">انصراف</button>' +
      '<button type="button" class="btn btn-success" id="pf-save"><i data-lucide="calendar-check" class="size-4 me-1"></i> تشکیل کلاس و تولید جلسات</button>' +
      '</div></div></div></div>';
    document.body.appendChild(host);
    el = {
      form: host.querySelector('#pf-form'),
      offering: host.querySelector('#pf-offering'),
      offeringMeta: host.querySelector('#pf-offering-meta'),
      code: host.querySelector('#pf-code'),
      lesson: host.querySelector('#pf-lesson'),
      lessonMeta: host.querySelector('#pf-lesson-meta'),
      teacher: host.querySelector('#pf-teacher'),
      location: host.querySelector('#pf-location'),
      date: host.querySelector('#pf-date'),
      count: host.querySelector('#pf-count'),
      countHint: host.querySelector('#pf-count-hint'),
      start: host.querySelector('#pf-start'),
      end: host.querySelector('#pf-end'),
      skip: host.querySelector('#pf-skip'),
      regen: host.querySelector('#pf-regen'),
      preview: host.querySelector('#pf-preview'),
      prevSum: host.querySelector('#pf-prev-sum'),
      errors: host.querySelector('#pf-errors'),
      save: host.querySelector('#pf-save'),
      footnote: host.querySelector('#pf-footnote'),
    };
    modal = new window.bootstrap.Modal(host.querySelector('#pen-formation-modal'));
    host.querySelector('#pf-refresh').addEventListener('click', function () { refreshPreview(true); });
    host.querySelector('#pf-auto').addEventListener('click', autoCount);
    el.save.addEventListener('click', submit);
    el.offering.addEventListener('change', onOfferingChange);
    [el.lesson, el.teacher, el.location, el.date, el.count, el.start, el.end].forEach(function (i) {
      i.addEventListener('change', function () { schedulePreview(); });
    });
    host.querySelectorAll('[data-day]').forEach(function (cb) {
      cb.addEventListener('change', function () { schedulePreview(); });
    });
    el.skip.addEventListener('change', function () { schedulePreview(); });
    return true;
  }

  // ── option loaders ──────────────────────────────────────────────────
  function fillSelect(sel, items, labelFn, valueFn) {
    var cur = sel.value;
    var head = sel.querySelector('option[value=""]');
    sel.innerHTML = '';
    if (head) sel.appendChild(head);
    (items || []).forEach(function (it) {
      var o = document.createElement('option');
      o.value = valueFn ? valueFn(it) : it.id;
      o.textContent = labelFn(it);
      sel.appendChild(o);
    });
    if (cur) sel.value = cur;
  }

  function loadPickers() {
    fetch(TEACHERS_API, { credentials: 'same-origin', headers: csrf() })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        state.teachers = (d && (d.results || d)) || [];
        fillSelect(el.teacher, state.teachers, function (p) {
          return ((p.first_name || '') + ' ' + (p.last_name || '')).trim() || p.display_name || p.id;
        });
      }).catch(function () {});
    fetch(LOCATIONS_API, { credentials: 'same-origin', headers: csrf() })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        state.locations = (d && (d.results || d)) || [];
        fillSelect(el.location, state.locations, function (l) {
          return l.name + (l.building ? ' — ' + l.building : '');
        });
      }).catch(function () {});
  }

  // offering dropdown: active, non-cancelled runs of every course.
  function loadOfferings(preselect) {
    fetch(F_API + '?page_size=100', { credentials: 'same-origin', headers: csrf() })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('خطا')); })
      .then(function (d) {
        var rows = (d.results || d || []).filter(function (o) { return o.status !== 'cancelled'; });
        state.offerings = rows;
        fillSelect(el.offering, rows, function (o) {
          var code = o.code ? o.code + ' — ' : '';
          return code + (o.course_title || '') + (o.title ? ' (' + o.title + ')' : '') +
            (o.start_date ? ' · ' + o.start_date : '');
        });
        if (preselect) {
          el.offering.value = String(preselect);
          onOfferingChange();
        }
      })
      .catch(function (e) { toast('بارگذاری برگزاری‌ها ناموفق: ' + e.message, 'danger'); });
  }

  // ── the auto-fill heart: offering → proposed values into editable fields ──
  function onOfferingChange() {
    var id = el.offering.value;
    clearErrors();
    if (!id) { state.prefill = null; renderPreview(null); return; }
    el.offeringMeta.textContent = 'در حال دریافت مقادیر پیشنهادی…';
    el.lesson.innerHTML = '<option value="">در حال بارگذاری…</option>';
    fetch(F_API + id + '/formation/', { credentials: 'same-origin', headers: csrf() })
      .then(function (r) {
        if (!r.ok) return r.json().then(function (b) { throw new Error(errText(b)); });
        return r.json();
      })
      .then(function (p) {
        state.offering = id;
        state.prefill = p;
        applyPrefill(p);
      })
      .catch(function (e) {
        el.offeringMeta.innerHTML = '<span class="text-danger">' + esc(e.message) + '</span>';
      });
  }

  function applyPrefill(p) {
    el.offeringMeta.textContent =
      'ظرفیت ' + pn(p.capacity || 'نامحدود') + ' · ثبت‌نام ' + pn(p.enrolled_count || 0) +
      ' · مجموع مدت ' + pn(p.total_hours || 0) + ' ساعت' +
      (p.classes && p.classes.length ? ' · ' + pn(p.classes.length) + ' کلاس تشکیل‌شده' : '');

    // lessons — filtered to the offering's curriculum (brief: فیلترشده)
    el.lesson.innerHTML = '<option value="">— انتخاب درس —</option>';
    (p.lessons || []).forEach(function (l) {
      var o = document.createElement('option');
      o.value = l.id;
      o.textContent = l.title + (l.hours ? ' (' + pn(l.hours) + ' ساعت)' : '');
      el.lesson.appendChild(o);
    });
    if ((p.lessons || []).length === 1) el.lesson.value = p.lessons[0].id;
    lessonMeta();

    el.code.value = p.suggested_class_code || '';
    // teacher/location: pre-select if the option exists, else keep proposal
    if (p.teacher) { ensureOption(el.teacher, p.teacher, p.teacher_name); el.teacher.value = p.teacher; }
    else el.teacher.value = '';
    if (p.location) { ensureOption(el.location, p.location, p.location_name); el.location.value = p.location; }
    else el.location.value = '';

    el.date.value = p.start_date || '';
    var sched = p.schedule || {};
    document.querySelectorAll('#pf-sched [data-day]').forEach(function (cb) {
      cb.checked = (sched.days || []).indexOf(cb.value) !== -1;
    });
    el.start.value = sched.start || '';
    el.end.value = sched.end || '';
    el.skip.checked = p.skip_holidays !== false;
    el.count.value = '';
    el.footnote.textContent = 'مقادیر از برگزاری پیش‌پر شده‌اند و قابل ویرایش‌اند.';
    refreshPreview(false);
  }

  function ensureOption(sel, value, label) {
    var has = Array.prototype.some.call(sel.options, function (o) { return o.value === String(value); });
    if (!has) {
      var o = document.createElement('option');
      o.value = String(value);
      o.textContent = label || String(value);
      sel.appendChild(o);
    }
  }

  function currentSchedule() {
    var days = Array.prototype.slice.call(document.querySelectorAll('#pf-sched [data-day]:checked'))
      .map(function (c) { return c.value; });
    return { days: days, start: el.start.value.trim(), end: el.end.value.trim() };
  }

  function selectedLesson() {
    var id = el.lesson.value;
    return (state.prefill && (state.prefill.lessons || []).filter(function (l) {
      return String(l.id) === String(id);
    })[0]) || null;
  }

  function lessonMeta() {
    var l = selectedLesson();
    el.lessonMeta.textContent = l
      ? 'کد ' + (l.code || '—') + (l.hours ? ' · ' + pn(l.hours) + ' ساعت' : '')
      : '';
    if (l) autoCount(true);
  }

  // تعداد جلسات = مدت درس ÷ طول جلسه (mirror of the server formula, for the
  // hint only — the authoritative count is recomputed by /preview and on POST).
  function autoCount(silent) {
    var l = selectedLesson();
    var s = currentSchedule();
    if (!l || !l.hours || !s.start || !s.end) { if (!silent) toast('مدت درس یا ساعت جلسه مشخص نیست.', 'warning'); return; }
    var mins = toMin(s.end) - toMin(s.start);
    if (mins <= 0) { if (!silent) toast('ساعت پایان باید بعد از شروع باشد.', 'danger'); return; }
    var n = Math.ceil((l.hours * 60) / mins);
    el.count.value = Math.min(200, Math.max(1, n));
    if (!silent) toast(pn(n) + ' جلسه محاسبه شد ✓', 'success');
    refreshPreview(false);
  }
  function toMin(hhmm) {
    var m = /^(\d{1,2}):(\d{2})$/.exec(hhmm || '');
    if (!m) return NaN;
    return (+m[1]) * 60 + (+m[2]);
  }

  // ── preview (server's own walk, throttled) ──────────────────────────
  function schedulePreview() {
    if (state.previewT) clearTimeout(state.previewT);
    state.previewT = setTimeout(function () { refreshPreview(false); }, 450);
    lessonMeta();
  }

  function previewPayload() {
    var s = currentSchedule();
    var body = {
      offering: state.offering || el.offering.value || '',
      lesson: el.lesson.value || '',
      schedule: s,
      skip_holidays: el.skip.checked,
    };
    if (el.code.value.trim()) body.class_code = el.code.value.trim();
    // JalaliDateField parses the jalali text (۱۴۰۵/۰۶/۲۸ or dashed) — send
    // exactly what the picker wrote, never pre-convert to gregorian ISO.
    if (el.date.value.trim()) body.start_date = el.date.value.trim();
    if (el.count.value) body.count = Number(el.count.value);
    if (el.teacher.value) body.teacher = el.teacher.value;
    if (el.location.value) body.location = el.location.value;
    return body;
  }

  function refreshPreview(manual) {
    if (!el.offering.value || !el.lesson.value) { renderPreview(null); return; }
    var s = currentSchedule();
    if (!s.days.length || !s.start || !s.end) { renderPreview(null, 'روزها و ساعت شروع/پایان را کامل کنید.'); return; }
    if (!manual) el.prevSum.textContent = '…';
    el.preview.innerHTML = '<div class="pen-loading p-3">در حال محاسبهٔ جلسات…</div>';
    fetch(FORM_API + 'preview/', {
      method: 'POST', credentials: 'same-origin',
      headers: Object.assign({ 'Content-Type': 'application/json' }, csrf()),
      body: JSON.stringify(previewPayload()),
    }).then(function (r) {
      return r.json().then(function (b) {
        if (!r.ok) throw new Error(errText(b));
        return b;
      });
    }).then(function (data) {
      renderPreview(data);
      if (manual) toast('پیش‌نمایش ' + pn(data.count) + ' جلسه آماده شد ✓', 'success');
    }).catch(function (e) { renderPreview(null, e.message); });
  }

  function renderPreview(data, msg) {
    if (!data) {
      el.prevSum.textContent = '—';
      el.preview.innerHTML = '<div class="p-3 text-muted fs-14">' + esc(msg || 'اطلاعات کافی نیست.') + '</div>';
      return;
    }
    var sum = pn(data.count) + ' جلسه · ' + pn(data.session_minutes) + ' دقیقه';
    if (data.holidays) sum += ' · ' + pn(data.holidays) + ' تعطی';
    if (data.conflicts) sum += ' · ' + pn(data.conflicts) + ' تداخل';
    el.prevSum.textContent = sum;
    var rows = (data.sessions || []).map(function (s) {
      var badge = s.conflict
        ? '<span class="badge bg-warning text-dark">تداخل → هفتهٔ بعد</span>'
        : '<span class="badge bg-success-subtle text-success">آزاد</span>';
      return '<tr><td>' + pn(s.number) + '</td>' +
        '<td class="text-nowrap">' + esc(DAY_LABEL(s.date)) + ' ' + esc(s.jalali) + '</td>' +
        '<td dir="ltr" class="text-nowrap">' + esc(pn(s.start)) + '–' + esc(pn(s.end)) + '</td>' +
        '<td>' + badge + '</td></tr>';
    }).join('');
    el.preview.innerHTML =
      '<table class="table table-sm mb-0 align-middle"><thead class="table-light"><tr>' +
      '<th>جلسه</th><th>تاریخ</th><th>ساعت</th><th>وضعیت فضا/مدرس</th></tr></thead>' +
      '<tbody>' + (rows || '<tr><td colspan="4" class="text-muted p-3">جلسه‌ای ساخته نمی‌شود.</td></tr>') +
      '</tbody></table>' +
      (data.complete === false
        ? '<div class="p-2 small text-danger">افق جست‌وجو کافی نبود؛ تعداد/روزها را تغییر دهید.</div>'
        : (data.conflicts
          ? '<div class="p-2 small text-muted">جلساتِ متداخل هنگام ذخیره به تکرار بعدیِ همان روز (هفتهٔ بعد) منتقل می‌شوند.</div>'
          : ''));
    if (window.penRenderIcons) window.penRenderIcons();
  }
  function DAY_LABEL(dateISO) {
    if (!dateISO) return '';
    var names = ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه'];
    var d = new Date(dateISO + 'T00:00:00');
    return isNaN(d) ? '' : names[d.getDay()];
  }

  // ── submit ──────────────────────────────────────────────────────────
  function submit() {
    var body = previewPayload();
    body.class_code = el.code.value.trim();
    body.regenerate = el.regen.checked;
    body.strict = false;
    if (!body.offering) { showErrors({ offering: 'برگزاری دوره را انتخاب کنید.' }); return; }
    if (!body.lesson) { showErrors({ lesson: 'درس را انتخاب کنید.' }); return; }
    if (!body.class_code) { showErrors({ class_code: 'کد کلاس را وارد کنید.' }); return; }
    clearErrors();
    el.save.disabled = true;
    fetch(FORM_API, {
      method: 'POST', credentials: 'same-origin',
      headers: Object.assign({ 'Content-Type': 'application/json' }, csrf()),
      body: JSON.stringify(body),
    }).then(function (r) {
      return r.json().then(function (b) { return { ok: r.ok, b: b }; });
    }).then(function (res) {
      el.save.disabled = false;
      if (!res.ok) { showErrors(res.b); return; }
      var b = res.b;
      var msg = pn(b.created) + ' جلسه برای کلاس ' + (b.class_code || '') + ' ساخته شد';
      if (b.holidays_skipped) msg += ' (' + pn(b.holidays_skipped) + ' تعطی رد شد)';
      toast(msg + ' ✓', 'success');
      if (window.__PEN_RES_RELOAD__) window.__PEN_RES_RELOAD__();
      modal.hide();
    }).catch(function (e) { el.save.disabled = false; toast('خطا: ' + e, 'danger'); });
  }

  function errText(b) {
    if (!b) return 'خطای نامشخص';
    if (typeof b === 'string') return b;
    return errorLines(b).join(' — ');
  }
  function errorLines(body) {
    var lines = [];
    Object.keys(body || {}).forEach(function (k) {
      var v = body[k];
      (Array.isArray(v) ? v : [v]).forEach(function (m) {
        lines.push((k === 'non_field_errors' || k === 'detail' || k === 'error') ? String(m) : k + ': ' + m);
      });
    });
    return lines.length ? lines : ['خطای نامشخص'];
  }
  function showErrors(b) {
    el.errors.querySelector('ul').innerHTML = errorLines(b).map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('');
    el.errors.hidden = false;
    el.errors.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  function clearErrors() { el.errors.hidden = true; }

  // ── public entry ────────────────────────────────────────────────────
  window.penOpenClassFormation = function (offeringId) {
    if (!ensureDom()) return;
    loadPickers();
    clearErrors();
    renderPreview(null);
    el.offeringMeta.textContent = '';
    modal.show();
    if (window.penRenderIcons) window.penRenderIcons();
    if (window.penAttachJalaliPickers) window.penAttachJalaliPickers({ format: 'jalali' });
    // reset fields for a clean start
    el.code.value = ''; el.date.value = ''; el.count.value = '';
    el.start.value = ''; el.end.value = ''; el.regen.checked = false;
    document.querySelectorAll('#pf-sched [data-day]').forEach(function (cb) { cb.checked = false; });
    loadOfferings(offeringId);
  };

  document.addEventListener('hidden.bs.modal', function (e) {
    if (e.target && e.target.id === 'pen-formation-modal') {
      state.offering = null; state.prefill = null;
    }
  });
})();
