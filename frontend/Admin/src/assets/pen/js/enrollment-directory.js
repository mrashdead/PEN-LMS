(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root && root.document) api.boot(root);
}(typeof window !== 'undefined' ? window : null, function () {
  'use strict';

  var DIRECTORY_API = '/api/education/registration-directory/';
  var STATUS = {
    confirmed: ['تأییدشده', 'success'], pending: ['در انتظار تأیید', 'warning'],
    cancelled: ['لغوشده', 'secondary'], inactive: ['غیرفعال', 'secondary'],
    partially_refunded: ['عودت جزئی', 'warning'], refunded: ['عودت کامل', 'danger']
  };
  var ATTENDANCE = { present: 'حاضر', absent: 'غایب', late: 'با تأخیر', excused: 'موجه' };

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (character) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character];
    });
  }

  function number(value) {
    var text = Number(value || 0).toLocaleString('en-US');
    return text.replace(/,/g, '٬');
  }

  function safeHref(value) {
    var href = String(value || '');
    return /^\/workspace\/[A-Za-z0-9_./-]+$/.test(href) ? href : '';
  }

  function link(label, href, className) {
    var safe = safeHref(href);
    if (!safe) return escapeHtml(label || '—');
    return '<a' + (className ? ' class="' + escapeHtml(className) + '"' : '') + ' href="' + escapeHtml(safe) + '">' + escapeHtml(label || '—') + '</a>';
  }

  function statusMarkup(row) {
    var status = STATUS[row.status] || [row.status_label || 'نامشخص', 'secondary'];
    return '<span class="badge bg-' + status[1] + '-subtle text-' + status[1] + ' registration-status">' + escapeHtml(status[0]) + '</span>';
  }

  function rowMarkup(row) {
    var person = row.student || {};
    var course = row.course || {};
    var offering = row.offering || {};
    var group = row.class_group || {};
    var courseText = link(course.title || 'بدون دوره', course.url, 'fw-semibold');
    var offeringText = offering.title ? '<div class="fs-13 text-muted">' + link(offering.title + (offering.code ? ' · ' + offering.code : ''), offering.url) + '</div>' : '';
    var groupText = group.title ? link(group.title + (group.code ? ' · ' + group.code : ''), group.url) : '<span class="text-muted">تخصیص کلاس نشده</span>';
    return '<tr>' +
      '<td><div class="fw-semibold">' + link(person.name || 'شخص', person.url) + '</div><div class="text-muted fs-13">' + escapeHtml(person.student_code || '') + '</div></td>' +
      '<td>' + courseText + offeringText + '</td>' +
      '<td>' + groupText + (group.term ? '<div class="text-muted fs-13">' + escapeHtml(group.term) + '</div>' : '') + '</td>' +
      '<td>' + statusMarkup(row) + '</td>' +
      '<td><time datetime="' + escapeHtml(row.date || '') + '">' + escapeHtml(row.date_label || row.date || '—') + '</time></td>' +
      '<td>' + link('جزئیات', row.url, 'btn btn-sm btn-light text-nowrap') + '</td>' +
      '</tr>';
  }

  function rowsMarkup(rows, colspan) {
    if (!rows || !rows.length) return '<tr><td colspan="' + Number(colspan || 6) + '"><div class="pen-empty py-5 text-center"><p class="mb-0">موردی مطابق این فیلترها پیدا نشد.</p></div></td></tr>';
    return rows.map(rowMarkup).join('');
  }

  function metricMarkup(entries) {
    return entries.map(function (entry) {
      return '<div><dt>' + escapeHtml(entry[0]) + '</dt><dd>' + escapeHtml(entry[1]) + '</dd></div>';
    }).join('');
  }

  function request(url, signal) {
    return fetch(url, { credentials: 'same-origin', signal: signal, headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (response) {
        return response.json().then(function (body) {
          if (!response.ok) throw new Error(body.detail || body.error || 'دریافت اطلاعات انجام نشد.');
          return body;
        });
      });
  }

  function boot(windowRef) {
    var doc = windowRef.document;
    var directory = doc.getElementById('registration-directory');
    var detailRoot = doc.getElementById('registration-detail-root');
    if (directory) bootDirectory(windowRef, directory);
    if (detailRoot) bootDetail(windowRef, detailRoot);
    if (windowRef.penAttachJalaliPickers) windowRef.penAttachJalaliPickers();
  }

  function bootDirectory(windowRef, root) {
    var doc = windowRef.document;
    var form = doc.getElementById('registration-filters');
    var table = doc.getElementById('reg-results');
    var rows = doc.getElementById('reg-rows');
    var error = doc.getElementById('reg-error');
    var retry = doc.getElementById('reg-retry');
    var state = { cursor: '', page: 1, data: null, controller: null, requestUrl: '', filters: '' };
    var query = new URLSearchParams(windowRef.location.search);

    var initialFilters = new URLSearchParams();
    ['search', 'course', 'offering', 'class_group', 'student', 'status', 'from', 'to', 'page_size'].forEach(function (name) {
      if (!query.has(name) || !form.elements[name]) return;
      var value = query.get(name);
      if (form.elements[name].tagName !== 'SELECT') form.elements[name].value = value;
      if (value) initialFilters.set(name, value);
    });

    function updateSummary(summary) {
      summary = summary || {};
      doc.getElementById('reg-total').textContent = number(summary.total);
      doc.getElementById('reg-active').textContent = number(summary.active);
      doc.getElementById('reg-inactive').textContent = number(summary.inactive);
      doc.getElementById('reg-pending').textContent = number(summary.pending);
    }

    function filterQuery() {
      var params = new URLSearchParams(new FormData(form));
      params.delete('cursor');
      return params.toString();
    }

    function load(cursor, page) {
      var params = new URLSearchParams(state.filters);
      if (cursor) params.set('cursor', cursor);
      var url = DIRECTORY_API + (params.toString() ? '?' + params.toString() : '');
      state.requestUrl = url;
      state.cursor = cursor || '';
      state.page = page || 1;
      if (state.controller) state.controller.abort();
      var controller = new AbortController();
      state.controller = controller;
      error.hidden = true;
      retry.hidden = true;
      table.setAttribute('aria-busy', 'true');
      doc.getElementById('reg-prev').disabled = true;
      doc.getElementById('reg-next').disabled = true;
      doc.getElementById('reg-load-status').textContent = 'در حال بارگذاری ثبت‌نام‌ها…';
      rows.innerHTML = '<tr><td colspan="6" class="text-center py-5 text-muted">در حال بارگذاری…</td></tr>';
      return request(url, controller.signal).then(function (data) {
        state.data = data;
        rows.innerHTML = rowsMarkup(data.results, 6);
        if (data.summary) updateSummary(data.summary);
        doc.getElementById('reg-load-status').textContent = (data.results || []).length ? 'ثبت‌نام‌های این صفحه' : 'فهرست خالی است';
        doc.getElementById('reg-page-label').textContent = 'صفحهٔ ' + number(state.page) + ' · ' + number((data.results || []).length) + ' ردیف';
        doc.getElementById('reg-prev').disabled = !data.previous_cursor;
        doc.getElementById('reg-next').disabled = !data.next_cursor;
        if (windowRef.penRenderIcons) windowRef.penRenderIcons();
      }).catch(function (exception) {
        if (exception.name === 'AbortError') return;
        error.textContent = exception.message || 'دریافت ثبت‌نام‌ها انجام نشد.';
        error.hidden = false;
        retry.hidden = false;
        doc.getElementById('reg-load-status').textContent = 'بارگذاری ناموفق بود.';
      }).finally(function () {
        if (state.controller === controller && !controller.signal.aborted) table.setAttribute('aria-busy', 'false');
      });
    }

    function loadPicker(kind, term) {
      var select = root.querySelector('[data-picker="' + kind + '"]');
      if (!select) return;
      var selected = select.value || query.get(select.name) || '';
      var params = new URLSearchParams({ kind: kind });
      if (term) params.set('q', term);
      if (selected) params.set('selected', selected);
      if (kind === 'offering' && doc.getElementById('reg-course').value) params.set('course', doc.getElementById('reg-course').value);
      if (kind === 'class_group' && doc.getElementById('reg-offering').value) params.set('offering', doc.getElementById('reg-offering').value);
      request(DIRECTORY_API + 'picker/?' + params.toString()).then(function (data) {
        var first = select.options[0];
        var allLabel = first ? first.textContent : 'همه';
        select.innerHTML = '<option value="">' + escapeHtml(allLabel) + '</option>' + (data.results || []).map(function (item) {
          return '<option value="' + escapeHtml(item.id) + '">' + escapeHtml(item.label) + '</option>';
        }).join('');
        if (selected && Array.from(select.options).some(function (option) { return option.value === selected; })) select.value = selected;
        if (data.has_more && term) select.setAttribute('aria-description', 'برای نتیجه‌های بیشتر عبارت دقیق‌تری وارد کنید.');
      }).catch(function () {});
    }

    root.querySelectorAll('[data-picker]').forEach(function (select) { loadPicker(select.dataset.picker, ''); });
    root.querySelectorAll('[data-picker-search]').forEach(function (input) {
      var timer;
      input.addEventListener('input', function () {
        windowRef.clearTimeout(timer);
        timer = windowRef.setTimeout(function () { loadPicker(input.dataset.pickerSearch, input.value.trim()); }, 220);
      });
    });
    doc.getElementById('reg-course').addEventListener('change', function () {
      doc.getElementById('reg-offering').value = '';
      doc.getElementById('reg-class').value = '';
      loadPicker('offering', '');
      loadPicker('class_group', '');
    });
    doc.getElementById('reg-offering').addEventListener('change', function () {
      doc.getElementById('reg-class').value = '';
      loadPicker('class_group', '');
    });
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      state.filters = filterQuery();
      load('', 1);
    });
    form.addEventListener('reset', function () {
      windowRef.setTimeout(function () {
        state.filters = filterQuery();
        root.querySelectorAll('[data-picker]').forEach(function (select) { loadPicker(select.dataset.picker, ''); });
        load('', 1);
      }, 0);
    });
    doc.getElementById('reg-next').addEventListener('click', function () {
      if (state.data && state.data.next_cursor) load(state.data.next_cursor, state.page + 1);
    });
    doc.getElementById('reg-prev').addEventListener('click', function () {
      if (state.data && state.data.previous_cursor) load(state.data.previous_cursor, Math.max(1, state.page - 1));
    });
    retry.addEventListener('click', function () { load(state.cursor, state.page); });
    state.filters = initialFilters.toString() || filterQuery();
    load('', 1);
  }

  function renderCapacity(element, capacity) {
    if (!capacity) return;
    element.innerHTML = metricMarkup([
      ['ثبت‌نام فعال', number(capacity.enrolled)],
      ['ظرفیت', capacity.total == null ? 'نامحدود' : number(capacity.total)],
      ['ظرفیت باقی‌مانده', capacity.remaining == null ? 'نامحدود' : number(capacity.remaining)],
      ['وضعیت ظرفیت', capacity.full ? 'تکمیل‌شده' : 'دارای ظرفیت']
    ]);
    element.hidden = false;
  }

  function contextMarkup(data) {
    var rows = [];
    function add(label, value, href) {
      if (value) rows.push('<div><small>' + escapeHtml(label) + '</small>' + link(value, href) + '</div>');
    }
    add('کد', data.code);
    add('وضعیت', data.status);
    add('ترم', data.term);
    add('توضیحات', data.description);
    (data.links || []).forEach(function (item) { add('مرتبط', item.title, item.url); });
    return rows.join('');
  }

  function renderRowsInDetail(doc, data) {
    var listing = data.registrations || {};
    doc.getElementById('registration-detail-rows').innerHTML = rowsMarkup(listing.results, 6);
    doc.getElementById('registration-related-count').textContent = number(listing.summary && listing.summary.total || (listing.results || []).length) + ' ثبت‌نام';
    doc.getElementById('registration-detail-results').setAttribute('aria-busy', 'false');
  }

  function renderEntity(doc, data) {
    doc.getElementById('registration-context-title').textContent = data.title || 'جزئیات آموزشی';
    doc.getElementById('registration-identity').innerHTML = data.identity ?
      '<div class="fw-semibold">' + link(data.identity.name, data.identity.url) + '</div>' +
      '<div class="text-muted fs-14">' + [data.identity.student_code, data.identity.national_code, data.identity.mobile].filter(Boolean).map(escapeHtml).join(' · ') + '</div>' : '';
    doc.getElementById('registration-context-meta').innerHTML = contextMarkup(data);
    renderCapacity(doc.getElementById('registration-capacity'), data.capacity);
    renderRowsInDetail(doc, data);
    doc.getElementById('registration-entity-content').hidden = false;
  }

  function renderRecord(doc, data) {
    doc.getElementById('registration-context-title').textContent = 'ثبت‌نام ' + (data.student && data.student.name ? '· ' + data.student.name : '');
    var entries = [
      ['شخص', data.student && data.student.name, data.student && data.student.url],
      ['دوره', data.course && data.course.title, data.course && data.course.url],
      ['برگزاری', data.offering && data.offering.title, data.offering && data.offering.url],
      ['کلاس', data.class_group && data.class_group.title, data.class_group && data.class_group.url],
      ['وضعیت', (STATUS[data.status] || [data.status_label || 'نامشخص'])[0]],
      ['تاریخ ثبت‌نام', data.date_label || data.date]
    ];
    doc.getElementById('registration-record-summary').innerHTML = entries.filter(function (entry) { return entry[1]; }).map(function (entry) {
      return '<div><small>' + escapeHtml(entry[0]) + '</small>' + link(entry[1], entry[2]) + '</div>';
    }).join('');
    renderCapacity(doc.getElementById('registration-record-capacity'), data.capacity);
    var attendance = data.attendance || [];
    doc.getElementById('registration-attendance').innerHTML = attendance.length ? attendance.map(function (item) {
      return '<span class="badge bg-light text-body me-2 mb-2">' + escapeHtml(ATTENDANCE[item.status] || item.status) + ': ' + number(item.total) + '</span>';
    }).join('') : 'اطلاعات حضور ثبت نشده است.';
    var history = data.history || [];
    doc.getElementById('registration-history').innerHTML = history.length ? history.map(function (item) {
      return '<li class="pen-timeline-item"><div class="fw-semibold fs-14">' + escapeHtml(item.summary) + '</div><div class="fs-13 text-muted">' + escapeHtml(item.actor) + ' · ' + escapeHtml(item.date) + '</div></li>';
    }).join('') : '<li class="text-muted fs-14">تاریخچه‌ای ثبت نشده است.</li>';
    doc.getElementById('registration-record-content').hidden = false;
  }

  function bootDetail(windowRef, root) {
    var doc = windowRef.document;
    var config = JSON.parse(doc.getElementById('registration-page-context').textContent);
    var error = doc.getElementById('registration-detail-error');
    var retry = doc.getElementById('registration-detail-retry');
    var requestUrl = config.mode === 'record'
      ? DIRECTORY_API + 'records/' + encodeURIComponent(config.source) + '/' + encodeURIComponent(config.id) + '/'
      : DIRECTORY_API + 'context/' + encodeURIComponent(config.kind) + '/' + encodeURIComponent(config.id) + '/';
    function load() {
      error.hidden = true;
      retry.hidden = true;
      root.setAttribute('aria-busy', 'true');
      request(requestUrl).then(function (data) {
        if (config.mode === 'record') renderRecord(doc, data);
        else renderEntity(doc, data);
      }).catch(function (exception) {
        error.textContent = exception.message || 'دریافت جزئیات انجام نشد.';
        error.hidden = false;
        retry.hidden = false;
      }).finally(function () { root.setAttribute('aria-busy', 'false'); });
    }
    retry.addEventListener('click', load);
    load();
  }

  return {
    boot: boot,
    escapeHtml: escapeHtml,
    rowMarkup: rowMarkup,
    rowsMarkup: rowsMarkup,
    statusMarkup: statusMarkup
  };
}));
