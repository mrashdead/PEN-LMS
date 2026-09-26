/* Enrollment/capacity report. Only the current page and bounded trend are rendered. */
(function () {
  'use strict';
  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (char) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char];
    });
  }
  function recentDates(days, today) {
    var end = new Date(today + 'T12:00:00Z');
    var start = new Date(end);
    start.setUTCDate(start.getUTCDate() - days + 1);
    return { from: start.toISOString().slice(0, 10), to: end.toISOString().slice(0, 10) };
  }
  function chartMarkup(rows, format) {
    if (!rows.length || !rows.some(function (row) { return row.total > 0; })) {
      return '<p class="text-muted text-center py-5">در این بازه ثبت‌نام فعالی وجود ندارد.</p>';
    }
    var width = 900, height = 180, left = 45, plot = width - left - 15;
    var maximum = Math.max.apply(null, rows.map(function (row) { return row.total; }));
    var step = plot / rows.length;
    var bars = rows.map(function (row, index) {
      var barHeight = row.total / maximum * (height - 15);
      return '<rect x="' + (left + index * step + step * .12).toFixed(2) + '" y="' + (height - barHeight).toFixed(2) + '" width="' + Math.max(.5, step * .76).toFixed(2) + '" height="' + barHeight.toFixed(2) + '" fill="currentColor"><title>' + escapeHtml(row.label + ': ' + format(row.total)) + '</title></rect>';
    }).join('');
    return '<svg viewBox="0 0 900 215" aria-hidden="true" focusable="false">' +
      '<line x1="45" y1="180" x2="885" y2="180" stroke="currentColor" opacity=".25"/>' +
      '<text x="35" y="20" text-anchor="end" fill="currentColor" font-size="12">' + escapeHtml(format(maximum)) + '</text>' +
      '<text x="35" y="180" text-anchor="end" fill="currentColor" font-size="12">' + escapeHtml(format(0)) + '</text>' + bars +
      '<text x="45" y="207" text-anchor="start" direction="ltr" fill="currentColor" font-size="12">' + escapeHtml(rows[0].label) + '</text>' +
      '<text x="885" y="207" text-anchor="end" direction="ltr" fill="currentColor" font-size="12">' + escapeHtml(rows[rows.length - 1].label) + '</text></svg>';
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { escapeHtml: escapeHtml, recentDates: recentDates, chartMarkup: chartMarkup };
  if (typeof document === 'undefined') return;
  var context = document.getElementById('capacity-endpoints');
  if (!context) return;
  var endpoints = JSON.parse(context.textContent);
  var form = document.getElementById('capacity-filters');
  var results = document.getElementById('capacity-results');
  var errorBox = document.getElementById('capacity-error');
  var retry = document.getElementById('capacity-retry');
  var state = { request: null, page: 0, next: null, previous: null, first: '', pickers: {}, timers: {}, rows: [] };
  var format = function (value) { return Number(value || 0).toLocaleString('fa-IR'); };
  var statuses = {
    offerings: { draft: 'پیش‌نویس', open: 'باز (ثبت‌نام)', closed: 'بسته', running: 'در حال برگزاری', finished: 'پایان‌یافته', cancelled: 'لغوشده' },
    classes: { active: 'فعال', inactive: 'غیرفعال' },
  };
  function setText(id, text) { document.getElementById(id).textContent = text; }
  function pressed(selector, value, attribute) {
    document.querySelectorAll(selector).forEach(function (button) {
      var active = button.getAttribute(attribute) === value;
      button.setAttribute('aria-pressed', String(active));
      button.classList.remove('btn-outline-secondary');
      button.classList.toggle('btn-primary', active);
      button.classList.toggle('btn-outline-primary', !active);
    });
  }
  function updateSource() {
    var source = form.elements.source.value;
    var current = form.elements.status.value;
    form.elements.status.innerHTML = '<option value="">همهٔ وضعیت‌ها</option>' + Object.keys(statuses[source]).map(function (key) {
      return '<option value="' + key + '">' + statuses[source][key] + '</option>';
    }).join('');
    if (statuses[source][current]) form.elements.status.value = current;
    pressed('[data-capacity-source]', source, 'data-capacity-source');
    setText('capacity-parent-heading', source === 'offerings' ? 'دوره' : 'ترم');
    setText('capacity-source-help', source === 'offerings'
      ? 'ظرفیت و ثبت‌نام هر برگزاری دوره را بررسی کنید.'
      : 'عضویت در کلاس‌های آموزشی به تفکیک ترم؛ فیلتر دوره بر اساس جلسات متصل به دوره اعمال می‌شود.');
    document.querySelector('label[for="capacity-status"]').textContent = source === 'offerings' ? 'وضعیت برگزاری' : 'وضعیت کلاس';
  }
  function queryUrl() {
    var params = new URLSearchParams();
    new FormData(form).forEach(function (value, key) {
      if (String(value).trim()) params.set(key, String(value).trim());
    });
    return endpoints.report + '?' + params.toString();
  }
  function setPager(busy) {
    document.getElementById('capacity-first').disabled = busy || state.page === 0;
    document.getElementById('capacity-prev').disabled = busy || !state.previous;
    document.getElementById('capacity-next').disabled = busy || !state.next;
  }
  function renderRows(rows) {
    state.rows = rows;
    document.getElementById('capacity-rows').innerHTML = rows.length ? rows.map(function (row) {
      var unlimited = row.capacity == null;
      var occupancy = unlimited ? '<span class="text-muted">نامحدود</span>' :
        '<meter class="capacity-meter" min="0" max="100" value="' + Math.min(100, row.occupancy) + '" aria-label="درصد اشغال ظرفیت ' + escapeHtml(row.title) + '"></meter>' + format(row.occupancy) + '٪';
      var badge = row.full ? '<span class="badge bg-danger-subtle text-danger">تکمیل ظرفیت</span>' :
        '<span class="badge bg-success-subtle text-success">' + (unlimited ? 'نامحدود' : 'دارای ظرفیت') + '</span>';
      return '<tr><td><strong>' + escapeHtml(row.title) + '</strong><small class="d-block text-muted" dir="ltr">' + escapeHtml(row.code) + '</small></td>' +
        '<td>' + escapeHtml(row.parent) + '</td><td class="text-nowrap">' + escapeHtml(row.status) + (!row.is_active && form.elements.source.value === 'offerings' ? '<small class="d-block text-muted">غیرفعال</small>' : '') + '</td>' +
        '<td>' + format(row.enrolled) + '</td><td>' + (unlimited ? 'نامحدود' : format(row.capacity)) + '</td>' +
        '<td>' + (unlimited ? 'نامحدود' : format(row.remaining)) + '<div class="mt-1">' + badge + '</div></td>' +
        '<td>' + occupancy + '</td><td>' + format(row.period_enrollments) + '</td></tr>';
    }).join('') : '<tr><td colspan="8"><div class="text-center py-5"><p class="mb-2">کلاس یا برگزاری‌ای با این فیلترها پیدا نشد.</p><button type="button" class="btn btn-outline-primary btn-sm" data-capacity-reset>بازنشانی فیلترها</button></div></td></tr>';
    setText('capacity-page-label', rows.length ? 'صفحهٔ ' + format(state.page + 1) + ' · ' + format(rows.length) + ' ردیف' + (state.next ? '' : ' · آخرین صفحه') : 'بدون نتیجه');
  }
  function renderOverview(overview) {
    Object.keys(overview.totals).forEach(function (key) { setText('cap-' + key, format(overview.totals[key])); });
    document.getElementById('capacity-chart').innerHTML = chartMarkup(overview.trend, format);
    document.getElementById('capacity-chart').setAttribute('aria-label', 'روند ' + format(overview.totals.registrations) + ' ثبت‌نام فعال؛ جدول آمار در ادامه');
    document.getElementById('capacity-trend-rows').innerHTML = overview.trend.map(function (row) {
      return '<tr><th scope="row">' + escapeHtml(row.label) + '</th><td>' + format(row.total) + '</td></tr>';
    }).join('');
    setText('capacity-date-range', overview.dates.from_jalali + ' تا ' + overview.dates.to_jalali);
    if (!form.elements.from.value) form.elements.from.value = overview.dates.from_jalali;
    if (!form.elements.to.value) form.elements.to.value = overview.dates.to_jalali;
  }
  async function load(url, page, reset) {
    if (state.request) state.request.abort();
    var request = new AbortController(); state.request = request;
    errorBox.hidden = true; retry.hidden = true;
    results.setAttribute('aria-busy', 'true');
    if (reset) results.hidden = true;
    setPager(true);
    setText('capacity-load-status', 'در حال محاسبهٔ گزارش…');
    try {
      var response = await fetch(url, { credentials: 'same-origin', signal: request.signal });
      if (!response.ok) {
        var body = await response.json().catch(function () { return {}; });
        throw new Error(body.detail || (response.status === 403 ? 'شما به این گزارش دسترسی ندارید.' : 'دریافت گزارش ناموفق بود. دوباره تلاش کنید.'));
      }
      var data = await response.json();
      if (state.request !== request) return;
      state.page = page; state.next = data.next; state.previous = data.previous;
      if (reset) {
        state.first = url;
        var browserUrl = new URL(window.location.href);
        browserUrl.search = new URL(url, window.location.href).search;
        window.history.replaceState({}, '', browserUrl.toString());
      }
      if (data.overview) renderOverview(data.overview);
      renderRows(data.results);
      results.hidden = false;
      setText('capacity-load-status', 'گزارش به‌روز است.');
      setText('capacity-updated', 'آخرین محاسبه: ' + new Date().toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' }));
    } catch (error) {
      if (state.request !== request || error.name === 'AbortError') return;
      errorBox.textContent = error.message; errorBox.hidden = false;
      retry.hidden = false; retry.onclick = function () { load(url, page, reset); };
      setText('capacity-load-status', reset ? 'گزارش دریافت نشد.' : 'دریافت صفحه ناموفق بود؛ آخرین صفحهٔ دریافت‌شده نمایش داده می‌شود.');
    } finally {
      if (state.request === request) {
        state.request = null;
        results.setAttribute('aria-busy', 'false'); setPager(false);
      }
    }
  }
  function apply() {
    pressed('[data-capacity-filter]', form.elements.capacity.value, 'data-capacity-filter');
    return load(queryUrl(), 0, true);
  }
  async function picker(kind, selected) {
    var key = kind === 'course' ? 'course' : 'class';
    var select = document.getElementById('capacity-' + key);
    var hint = document.getElementById('capacity-' + key + '-hint');
    if (state.pickers[kind]) state.pickers[kind].abort();
    var request = new AbortController(); state.pickers[kind] = request;
    var params = new URLSearchParams({ kind: kind, source: form.elements.source.value, course: form.elements.course.value, q: document.getElementById('capacity-' + key + '-search').value });
    if (selected) params.set('selected', selected);
    hint.textContent = 'در حال دریافت گزینه‌ها…';
    try {
      var response = await fetch(endpoints.options + '?' + params, { credentials: 'same-origin', signal: request.signal });
      if (!response.ok) throw new Error('دریافت گزینه‌ها ناموفق بود؛ برای تلاش دوباره جست‌وجو کنید.');
      var data = await response.json();
      if (state.pickers[kind] !== request) return;
      var previous = select.value;
      var retained = previous ? select.options[select.selectedIndex].cloneNode(true) : null;
      select.innerHTML = '<option value="">' + (kind === 'course' ? 'همهٔ دوره‌ها' : 'همهٔ کلاس‌ها / برگزاری‌ها') + '</option>';
      data.results.forEach(function (row) { select.add(new Option(row.label, row.id)); });
      if (retained && !data.results.some(function (row) { return row.id === previous; })) select.add(retained);
      select.value = selected || previous;
      if (!select.value) select.value = '';
      hint.textContent = data.has_more ? '۳۰ نتیجهٔ نخست؛ برای یافتن گزینه‌های بیشتر جست‌وجو را دقیق‌تر کنید.' : (data.results.length ? '' : 'گزینه‌ای پیدا نشد.');
    } catch (error) {
      if (state.pickers[kind] === request && error.name !== 'AbortError') hint.textContent = error.message;
    }
  }
  function reset() {
    form.reset(); form.elements.source.value = 'offerings'; updateSource();
    document.getElementById('capacity-course-search').value = '';
    document.getElementById('capacity-class-search').value = '';
    picker('course'); picker('classroom'); apply();
  }
  form.addEventListener('submit', function (event) { event.preventDefault(); apply(); });
  document.getElementById('capacity-reset').addEventListener('click', reset);
  document.getElementById('capacity-rows').addEventListener('click', function (event) {
    if (event.target.closest('[data-capacity-reset]')) reset();
  });
  document.getElementById('capacity-course').addEventListener('change', function () {
    form.elements.classroom.value = ''; document.getElementById('capacity-class-search').value = ''; picker('classroom');
  });
  ['course', 'class'].forEach(function (key) {
    document.getElementById('capacity-' + key + '-search').addEventListener('input', function () {
      clearTimeout(state.timers[key]);
      state.timers[key] = setTimeout(function () { picker(key === 'course' ? 'course' : 'classroom'); }, 300);
    });
  });
  ['capacity-group', 'capacity-page-size'].forEach(function (id) { document.getElementById(id).addEventListener('change', apply); });
  document.querySelectorAll('[data-capacity-source]').forEach(function (button) {
    button.addEventListener('click', function () {
      form.elements.source.value = button.dataset.capacitySource;
      form.elements.classroom.value = ''; form.elements.status.value = '';
      document.getElementById('capacity-class-search').value = '';
      updateSource(); picker('classroom'); apply();
    });
  });
  document.querySelectorAll('[data-capacity-filter]').forEach(function (button) {
    button.addEventListener('click', function () { form.elements.capacity.value = button.dataset.capacityFilter; apply(); });
  });
  document.querySelectorAll('[data-capacity-days]').forEach(function (button) {
    button.addEventListener('click', function () {
      var today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Tehran', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
      var dates = recentDates(Number(button.dataset.capacityDays), today);
      form.elements.from.value = dates.from; form.elements.to.value = dates.to; apply();
    });
  });
  document.getElementById('capacity-first').addEventListener('click', function () { load(state.first, 0, false); });
  document.getElementById('capacity-prev').addEventListener('click', function () { if (state.previous) load(state.previous, Math.max(0, state.page - 1), false); });
  document.getElementById('capacity-next').addEventListener('click', function () { if (state.next) load(state.next, state.page + 1, false); });

  var saved = new URLSearchParams(window.location.search);
  if (saved.get('source') === 'classes') form.elements.source.value = 'classes';
  updateSource();
  ['status', 'capacity', 'from', 'to', 'group', 'page_size'].forEach(function (key) {
    var field = form.elements[key], value = saved.get(key);
    if (value != null && (field.tagName !== 'SELECT' || Array.from(field.options).some(function (option) { return option.value === value; }))) field.value = value;
  });
  // Restore selected picker values before issuing the initial report request.
  ['course', 'classroom'].forEach(function (key) {
    if (saved.get(key)) { form.elements[key].add(new Option('در حال دریافت عنوان…', saved.get(key))); form.elements[key].value = saved.get(key); }
    picker(key, saved.get(key));
  });
  if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  apply();
})();
