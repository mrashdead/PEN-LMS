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
  var reportPage = document.querySelector('.pen-reports').dataset.reportPage || 'overview';
  var charts = {};
  var lastData = null;
  var state = { query: new URLSearchParams(window.location.search), period: new URLSearchParams(window.location.search).get('period') || '' };

  var labels = {
    draft: 'پیش‌نویس', open: 'باز', running: 'در حال برگزاری', closed: 'بسته',
    finished: 'پایان‌یافته', cancelled: 'لغوشده', scheduled: 'برنامه‌ریزی‌شده',
    held: 'برگزارشده', deferred: 'معوقه', present: 'حاضر', absent: 'غایب',
    late: 'تأخیر', excused: 'موجه', paid: 'پرداخت‌شده', partial: 'ناقص', pending: 'در انتظار',
    submitted: 'ثبت‌شده', approved: 'تأییدشده', rejected: 'ردشده', completed: 'تکمیل‌شده',
    in_review: 'در حال بررسی', awaiting_action: 'منتظر اقدام', changes_requested: 'نیازمند اصلاح',
    blocked_assignment: 'بدون مسئول', archived: 'بایگانی‌شده',
    in_app: 'درون‌برنامه', email: 'ایمیل', sms: 'پیامک',
  };
  var palette = ['#0f6b67', '#123b5d', '#e5a83b', '#934b70', '#ef6a5b', '#5b7c99'];

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
  function updateReportUrl() {
    var query = new URLSearchParams(state.query);
    history.replaceState(null, '', window.location.pathname + (query.toString() ? '?' + query.toString() : ''));
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
  function render(data) {
    lastData = data;
    if (reportPage === 'overview') {
      document.getElementById('kpi-active-courses').textContent = faNumber(data.enrollments && data.enrollments.active_courses);
      document.getElementById('kpi-class-utilization').textContent = faPct(data.enrollments && data.enrollments.capacity && data.enrollments.capacity.occupancy_pct);
      var people = data.people || {};
      var students = (people.by_role || []).filter(function (row) { return row.key === 'student'; })[0] || {};
      document.getElementById('kpi-active-students').textContent = faNumber(students.value);
      document.getElementById('kpi-total-revenue').textContent = data.financial && data.financial.visible ? money(data.financial.totals && data.financial.totals.revenue) : '—';
    } else if (reportPage === 'financial') renderFinancial(data.financial || {});
    else if (reportPage === 'enrollments') renderEnrollments(data.enrollments || {});
    if (window.penRenderIcons) window.penRenderIcons();
  }
  function load(query) {
    hideError(); setLoading(true);
    state.query = query || currentQuery();
    updateReportUrl();
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
  document.querySelectorAll('.report-nav a, .report-index-link').forEach(function (link) {
    link.addEventListener('click', function () {
      var target = new URL(link.href, window.location.origin);
      currentQuery().forEach(function (value, key) { target.searchParams.set(key, value); });
      link.href = target.pathname + target.search;
    });
  });
  window.addEventListener('pen:theme-change', function () { if (lastData) render(lastData); });
  load(state.query);
})();
