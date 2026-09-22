/* Pen LMS — Reports & Analytics Dashboard.
 * The browser only formats the read model returned by /api/reports/dashboard/.
 */
(function () {
  'use strict';

  var ctxNode = document.getElementById('pen-reports-ctx');
  if (!ctxNode) return;
  var endpoints = JSON.parse(ctxNode.textContent || '{}');
  var optionsNode = document.getElementById('pen-report-options');
  var options = optionsNode ? JSON.parse(optionsNode.textContent || '{}') : {};
  var charts = {};
  var lastData = null;
  var state = { query: new URLSearchParams(window.location.search), period: new URLSearchParams(window.location.search).get('period') || '' };

  var labels = {
    draft: 'پیش‌نویس', open: 'باز', running: 'در حال برگزاری', closed: 'بسته',
    finished: 'پایان‌یافته', cancelled: 'لغوشده', scheduled: 'برنامه‌ریزی‌شده',
    held: 'برگزارشده', deferred: 'معوقه', present: 'حاضر', absent: 'غایب',
    late: 'تأخیر', excused: 'موجه', paid: 'پرداخت‌شده', partial: 'ناقص', pending: 'در انتظار',
    submitted: 'ثبت‌شده', approved: 'تأییدشده', rejected: 'ردشده', completed: 'تکمیل‌شده',
    in_app: 'درون‌برنامه', email: 'ایمیل', sms: 'پیامک',
  };
  var palette = ['#0f6b67', '#123b5d', '#e5a83b', '#934b70', '#ef6a5b', '#5b7c99'];
  var statusPalette = { present: '#27a88f', absent: '#ef6a5b', late: '#e5a83b', excused: '#4c8ca8' };

  function esc(value) {
    if (window.htmlEscape) return window.htmlEscape(value == null ? '' : String(value));
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[ch];
    });
  }
  function faNumber(value) {
    var raw = Number(value || 0).toLocaleString('en-US');
    return window.persianNumbers ? window.persianNumbers(raw) : raw;
  }
  function faPct(value) {
    return (window.persianNumbers ? window.persianNumbers(Number(value || 0).toFixed(1)) : Number(value || 0).toFixed(1)) + '٪';
  }
  function money(value) { return faNumber(value) + ' تومان'; }
  function showError(message) {
    var box = document.getElementById('report-filter-error');
    box.textContent = message || 'بارگذاری گزارش ناموفق بود.';
    box.hidden = false;
  }
  function hideError() { document.getElementById('report-filter-error').hidden = true; }
  function setLoading(on) {
    document.getElementById('report-loading').hidden = !on;
    document.querySelector('.pen-reports').classList.toggle('is-loading', on);
  }
  function displayLabel(key) { return labels[key] || key || '—'; }
  function dateISO(id) {
    var value = (document.getElementById(id).value || '').trim();
    if (!value) return '';
    var year = Number(value.replace(/[^\d۰-۹]/g, '').slice(0, 4).replace(/[۰-۹]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'.indexOf(d); }));
    if (year >= 1300 && window.penJalaliToISO) return window.penJalaliToISO(value) || value.replace(/\//g, '-');
    return value.replace(/\//g, '-');
  }
  function currentQuery() {
    var query = new URLSearchParams();
    var from = dateISO('report-from');
    var to = dateISO('report-to');
    if (from) query.set('from', from);
    if (to) query.set('to', to);
    if (state.period && !from && !to) query.set('period', state.period);
    ['department', 'course', 'location'].forEach(function (key) {
      var value = document.getElementById('report-' + key).value;
      if (value) query.set(key, value);
    });
    return query;
  }
  function api(url, query) {
    var target = url + (query && query.toString() ? '?' + query.toString() : '');
    return fetch(target, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (response) {
        return response.ok ? response.json() : response.json().then(function (body) {
          throw new Error(body.detail || body.error || ('HTTP ' + response.status));
        });
      });
  }
  function renderChart(id, config) {
    var node = document.getElementById(id);
    if (!node || !window.ApexCharts) return;
    if (charts[id]) charts[id].destroy();
    node.innerHTML = '';
    if (!config.series || !config.series.length || config.series.every(function (series) { return !series.data || !series.data.length || series.data.every(function (v) { return !Number(v); }); })) {
      node.innerHTML = '<div class="pen-empty">برای این بازه داده‌ای ثبت نشده است.</div>';
      return;
    }
    var styles = getComputedStyle(document.documentElement);
    var dark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    var bodyColor = styles.getPropertyValue('--dx-body-color').trim() || '#0f172a';
    var borderColor = styles.getPropertyValue('--dx-border-color').trim() || '#e5eaf0';
    var defaults = {
      chart: { height: 280, fontFamily: 'Vazirmatn, sans-serif', foreColor: bodyColor, toolbar: { show: false }, animations: { enabled: false } },
      dataLabels: { enabled: false }, grid: { borderColor: borderColor, strokeDashArray: 4 },
      tooltip: { theme: dark ? 'dark' : 'light' }, legend: { position: 'bottom', fontFamily: 'Vazirmatn, sans-serif' },
    };
    var chartConfig = Object.assign({}, defaults, config);
    chartConfig.chart = Object.assign({}, defaults.chart, config.chart || {});
    chartConfig.grid = Object.assign({}, defaults.grid, config.grid || {});
    chartConfig.tooltip = Object.assign({}, defaults.tooltip, config.tooltip || {});
    charts[id] = new ApexCharts(node, chartConfig);
    charts[id].render();
  }
  function renderDonut(id, values, names, colors) {
    renderChart(id, { chart: { type: 'donut' }, series: values, labels: names, colors: colors || palette, plotOptions: { pie: { donut: { size: '68%' } } } });
  }
  function renderTable(id, rows, columns, emptyText) {
    var body = document.getElementById(id);
    if (!body) return;
    if (!rows || !rows.length) { body.innerHTML = '<tr><td colspan="' + columns.length + '"><div class="pen-empty mb-0">' + esc(emptyText || 'داده‌ای نیست.') + '</div></td></tr>'; return; }
    body.innerHTML = rows.map(function (row) {
      return '<tr>' + columns.map(function (column) { return '<td>' + (column.render ? column.render(row) : esc(row[column.key])) + '</td>'; }).join('') + '</tr>';
    }).join('');
  }
  function fillSelect(id, rows, labelKey, selected) {
    var select = document.getElementById(id);
    if (!select) return;
    var first = select.options[0].outerHTML;
    select.innerHTML = first + (rows || []).map(function (row) {
      var value = String(row.id);
      return '<option value="' + esc(value) + '"' + (value === String(selected || '') ? ' selected' : '') + '>' + esc(row[labelKey]) + '</option>';
    }).join('');
  }
  function applyQueryToForm(query) {
    var from = query.get('from_jalali') || query.get('from') || '';
    var to = query.get('to_jalali') || query.get('to') || '';
    if (from && /^\d{4}-\d{2}-\d{2}$/.test(from) && window.penISOToJalali) from = window.penISOToJalali(from);
    if (to && /^\d{4}-\d{2}-\d{2}$/.test(to) && window.penISOToJalali) to = window.penISOToJalali(to);
    document.getElementById('report-from').value = from;
    document.getElementById('report-to').value = to;
    ['department', 'course', 'location'].forEach(function (key) { document.getElementById('report-' + key).value = query.get(key) || ''; });
  }
  function renderFinancial(data) {
    var content = document.getElementById('financial-content');
    var locked = document.getElementById('financial-locked');
    var exportButtons = document.querySelectorAll('[data-report-export="financial"]');
    if (!data.visible) {
      content.hidden = true; locked.hidden = false;
      exportButtons.forEach(function (button) { button.disabled = true; });
      document.getElementById('kpi-total-revenue').textContent = '—';
      return;
    }
    content.hidden = false; locked.hidden = true;
    exportButtons.forEach(function (button) { button.disabled = false; });
    var totals = data.totals || {};
    document.getElementById('kpi-total-revenue').textContent = money(totals.revenue);
    document.getElementById('finance-paid').textContent = faNumber(totals.paid_count);
    document.getElementById('finance-partial').textContent = faNumber(totals.partial_count);
    document.getElementById('finance-pending').textContent = faNumber(totals.pending_count);
    document.getElementById('finance-outstanding').textContent = money(totals.pending_amount);
    renderChart('chart-revenue', { chart: { type: 'area' }, colors: ['#0f6b67'], series: [{ name: 'درآمد', data: (data.revenue_trend || []).map(function (row) { return row.value; }) }], xaxis: { categories: (data.revenue_trend || []).map(function (row) { return row.label; }) }, stroke: { curve: 'smooth', width: 3 }, fill: { type: 'gradient', gradient: { opacityFrom: 0.34, opacityTo: 0.03 } } });
    renderDonut('chart-finance', [totals.paid_count || 0, totals.partial_count || 0, totals.pending_count || 0], ['پرداخت‌شده', 'ناقص', 'در انتظار'], ['#27a88f', '#e5a83b', '#934b70']);
    renderTable('financial-course-rows', data.by_course, [
      { key: 'label', render: function (row) { return '<strong>' + esc(row.label) + '</strong>'; } },
      { key: 'enrollments', render: function (row) { return faNumber(row.enrollments); } },
      { key: 'revenue', render: function (row) { return '<span class="text-nowrap">' + money(row.revenue) + '</span>'; } },
    ], 'دوره‌ای در این بازه ثبت نشده است.');
    renderTable('financial-department-rows', data.by_department, [
      { key: 'label', render: function (row) { return '<strong>' + esc(row.label) + '</strong>'; } },
      { key: 'enrollments', render: function (row) { return faNumber(row.enrollments); } },
      { key: 'revenue', render: function (row) { return '<span class="text-nowrap">' + money(row.revenue) + '</span>'; } },
    ], 'دپارتمانی در این بازه ثبت نشده است.');
    renderTable('financial-location-rows', data.by_location, [
      { key: 'label', render: function (row) { return '<strong>' + esc(row.label) + '</strong>'; } },
      { key: 'enrollments', render: function (row) { return faNumber(row.enrollments); } },
      { key: 'revenue', render: function (row) { return '<span class="text-nowrap">' + money(row.revenue) + '</span>'; } },
    ], 'محلی در این بازه ثبت نشده است.');
  }
  function renderEnrollments(data) {
    var status = data.status || {};
    document.getElementById('kpi-active-courses').textContent = faNumber(data.active_courses);
    document.getElementById('kpi-class-utilization').textContent = faPct(data.capacity && data.capacity.occupancy_pct);
    renderTable('popular-course-rows', data.popular, [
      { key: 'label', render: function (row) { return '<strong>' + esc(row.label) + '</strong>'; } },
      { key: 'enrollments', render: function (row) { return faNumber(row.enrollments); } },
      { key: 'capacity', render: function (row) { return row.capacity ? faNumber(row.capacity) : 'نامحدود'; } },
      { key: 'occupancy_pct', render: function (row) { return row.occupancy_pct == null ? '—' : faPct(row.occupancy_pct); } },
    ], 'برگزاری‌ای در این بازه ثبت نشده است.');
    var statusKeys = ['draft', 'open', 'running', 'closed', 'finished', 'cancelled'];
    renderDonut('chart-offering-status', statusKeys.map(function (key) { return status[key] || 0; }), statusKeys.map(displayLabel), palette);
  }
  function renderPeople(data) {
    var roleRows = data.by_role || [];
    document.getElementById('kpi-active-students').textContent = faNumber((roleRows.filter(function (row) { return row.key === 'student'; })[0] || {}).value || 0);
    renderDonut('chart-people', roleRows.map(function (row) { return row.value; }), roleRows.map(function (row) { return row.label; }), palette);
    renderTable('teacher-rows', data.active_teachers, [
      { key: 'label', render: function (row) { return '<strong>' + esc(row.label) + '</strong>'; } },
      { key: 'hours', render: function (row) { return faNumber(row.hours) + ' ساعت'; } },
      { key: 'sessions', render: function (row) { return faNumber(row.sessions); } },
      { key: 'classes', render: function (row) { return faNumber(row.classes); } },
    ], 'جلسه‌ای برای مدرس‌ها در این بازه ثبت نشده است.');
    renderChart('chart-new-students', { chart: { type: 'line' }, colors: ['#934b70'], series: [{ name: 'دانش‌آموز جدید', data: (data.new_students || []).map(function (row) { return row.value; }) }], xaxis: { categories: (data.new_students || []).map(function (row) { return row.label; }) }, stroke: { curve: 'smooth', width: 3 }, markers: { size: 4 } });
  }
  function renderClasses(data) {
    var sessionKeys = ['held', 'scheduled', 'deferred', 'cancelled'];
    renderDonut('chart-sessions', sessionKeys.map(function (key) { return (data.sessions || {})[key] || 0; }), sessionKeys.map(displayLabel), ['#27a88f', '#4c8ca8', '#e5a83b', '#ef6a5b']);
    var attendance = data.attendance || {};
    var counts = attendance.counts || {};
    ['present', 'absent', 'late', 'excused'].forEach(function (key) { document.getElementById('attendance-' + key).textContent = faNumber(counts[key]); });
    document.getElementById('absence-rate').textContent = faPct(attendance.absence_pct);
    document.getElementById('late-rate').textContent = faPct(attendance.late_pct);
    document.getElementById('attendance-average').textContent = 'میانگین ثبت حضور در هر جلسه: ' + faNumber(attendance.average_per_session);
    renderDonut('chart-attendance', ['present', 'absent', 'late', 'excused'].map(function (key) { return counts[key] || 0; }), ['حاضر', 'غایب', 'تأخیر', 'موجه'], ['#27a88f', '#ef6a5b', '#e5a83b', '#4c8ca8']);
    document.getElementById('room-overall').textContent = 'میانگین: ' + faPct(data.room_utilization_pct);
    var roomNode = document.getElementById('room-rows');
    if (!data.rooms || !data.rooms.length) { roomNode.innerHTML = '<div class="pen-empty">محل فعالی برای این بازه پیدا نشد.</div>'; return; }
    roomNode.innerHTML = data.rooms.map(function (row) {
      var pct = Number(row.utilization_pct || 0);
      return '<div class="report-room-row"><div class="d-flex justify-content-between gap-2 mb-1"><span>' + esc(row.label) + '</span><strong>' + faPct(pct) + '</strong></div><div class="progress" role="progressbar" aria-label="بهره‌وری ' + esc(row.label) + '" aria-valuenow="' + pct + '" aria-valuemin="0" aria-valuemax="100"><div class="progress-bar" style="width:' + Math.min(pct, 100) + '%"></div></div></div>';
    }).join('');
  }
  function renderWorkflow(data) {
    document.getElementById('workflow-response-hours').textContent = faNumber(data.avg_response_hours) + ' ساعت';
    document.getElementById('workflow-pending').textContent = faNumber(data.pending_review);
    document.getElementById('workflow-responded').textContent = faNumber(data.responded_requests);
    var statusNode = document.getElementById('workflow-status-rows');
    var statusKeys = ['running', 'completed', 'rejected', 'cancelled'];
    statusNode.innerHTML = statusKeys.map(function (key) {
      return '<div><span>' + esc(displayLabel(key)) + '</span><strong>' + faNumber((data.status || {})[key]) + '</strong></div>';
    }).join('');
    var max = Math.max.apply(null, (data.form_types || []).map(function (row) { return row.value; }).concat([1]));
    var node = document.getElementById('workflow-form-rows');
    if (!data.form_types || !data.form_types.length) { node.innerHTML = '<div class="pen-empty">فرمی در این بازه ثبت نشده است.</div>'; return; }
    node.innerHTML = data.form_types.map(function (row) {
      var pct = Math.round(Number(row.value || 0) * 100 / max);
      return '<div class="report-form-row"><div class="d-flex justify-content-between gap-2 mb-1"><span>' + esc(row.label) + '</span><strong>' + faNumber(row.value) + '</strong></div><div class="progress"><div class="progress-bar" style="width:' + pct + '%"></div></div></div>';
    }).join('');
  }
  function renderCommunications(data) {
    document.getElementById('communications-total').textContent = faNumber(data.total);
    document.getElementById('communications-unread').textContent = faNumber(data.unread_in_app);
    var node = document.getElementById('communications-rows');
    var rows = data.by_channel || [];
    if (!rows.length) { node.innerHTML = '<div class="pen-empty">اعلانی در این بازه ثبت نشده است.</div>'; return; }
    node.innerHTML = rows.map(function (row) {
      var total = Object.keys(row.values || {}).reduce(function (sum, key) { return sum + Number(row.values[key] || 0); }, 0);
      var details = Object.keys(row.values || {}).map(function (key) { return esc(displayLabel(key)) + ': ' + faNumber(row.values[key]); }).join(' · ');
      return '<div class="report-form-row"><div class="d-flex justify-content-between gap-2 mb-1"><span>' + esc(displayLabel(row.label)) + '</span><strong>' + faNumber(total) + '</strong></div><div class="text-muted fs-13">' + details + '</div></div>';
    }).join('');
  }
  function render(data) {
    lastData = data;
    renderFinancial(data.financial || {});
    renderEnrollments(data.enrollments || {});
    renderPeople(data.people || {});
    renderClasses(data.classes || {});
    renderWorkflow(data.workflow || {});
    renderCommunications(data.communications || {});
    document.getElementById('report-last-updated').textContent = new Date().toLocaleString('fa-IR');
    if (window.penRenderIcons) window.penRenderIcons();
  }
  function load(query) {
    hideError(); setLoading(true);
    state.query = query || currentQuery();
    history.replaceState(null, '', window.location.pathname + (state.query.toString() ? '?' + state.query.toString() : ''));
    api(endpoints.dashboard, state.query).then(render).catch(function (error) { showError(error.message); }).finally(function () { setLoading(false); });
  }
  function exportReport(kind) {
    var query = currentQuery();
    query.set('report', kind);
    window.location.href = endpoints.export + '?' + query.toString();
  }

  fillSelect('report-department', options.departments, 'name', state.query.get('department'));
  fillSelect('report-course', options.courses, 'title', state.query.get('course'));
  fillSelect('report-location', options.locations, 'name', state.query.get('location'));
  applyQueryToForm(state.query);
  if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  document.getElementById('report-filter-form').addEventListener('submit', function (event) { event.preventDefault(); load(currentQuery()); });
  document.querySelectorAll('[data-report-period]').forEach(function (button) {
    button.addEventListener('click', function () {
      state.period = button.dataset.reportPeriod === 'custom' ? '' : button.dataset.reportPeriod;
      if (state.period) { document.getElementById('report-from').value = ''; document.getElementById('report-to').value = ''; }
      document.querySelectorAll('[data-report-period]').forEach(function (item) { item.classList.toggle('active', item === button); });
      load(currentQuery());
    });
  });
  document.getElementById('report-from').addEventListener('input', function () { state.period = ''; });
  document.getElementById('report-to').addEventListener('input', function () { state.period = ''; });
  document.getElementById('report-reset').addEventListener('click', function () {
    state.period = '';
    ['report-from', 'report-to'].forEach(function (id) { document.getElementById(id).value = ''; });
    ['report-department', 'report-course', 'report-location'].forEach(function (id) { document.getElementById(id).value = ''; });
    load(new URLSearchParams());
  });
  document.getElementById('report-print').addEventListener('click', function () { window.print(); });
  document.querySelectorAll('[data-report-export]').forEach(function (button) { button.addEventListener('click', function () { if (!button.disabled) exportReport(button.dataset.reportExport); }); });
  window.addEventListener('pen:theme-change', function () { if (lastData) render(lastData); });
  load(state.query);
})();
