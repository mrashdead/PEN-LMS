/*
 * Pen LMS — reports dashboard (ApexCharts over real /api/education/reports/*).
 * Server owns the aggregation; this file only renders what it returns.
 */
(function () {
  'use strict';

  var ctxEl = document.getElementById('pen-reports-ctx');
  if (!ctxEl) return;
  var EP = JSON.parse(ctxEl.textContent);
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  var STATUS_LABELS = {
    present: 'حاضر', absent: 'غایب', late: 'تأخیر', excused: 'موجه',
  };
  var STATUS_COLORS = {
    present: '#22c55e', absent: '#ef4444', late: '#eab308', excused: '#0ea5e9',
  };
  var state = { period: 'day', date: '', groupMonth: false };
  var donut = null, trend = null;

  function inputValueToISO() {
    var raw = (document.getElementById('rep-date').value || '').trim();
    if (!raw) return '';
    if (window.penJalaliToISO) {
      var iso = window.penJalaliToISO(raw);
      if (iso) return iso;
    }
    return raw;
  }

  function qs() {
    var p = new URLSearchParams();
    p.set('period', state.period);
    if (state.date) p.set('date', state.date);
    if (state.groupMonth) p.set('group_by', 'jalali_month');
    return p.toString();
  }

  function fetchJson(url) {
    return fetch(url, { credentials: 'same-origin', headers: CSRF ? { 'X-CSRFToken': CSRF } : {} })
      .then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.error || b.detail || ('HTTP ' + r.status)); }); });
  }

  // ── charts ──────────────────────────────────────────────────────────

  function chartOptions(series, labels, colors) {
    return {
      chart: { type: 'donut', height: 280, fontFamily: 'Vazir, sans-serif' },
      series: series, labels: labels, colors: colors,
      legend: { position: 'bottom' },
      dataLabels: { enabled: false },
      plotOptions: { pie: { donut: { size: '68%' } } },
    };
  }

  function render(data) {
    // KPIs
    var totals = data.totals || {};
    document.getElementById('kpi-present').textContent = window.persianNumbers(totals.present || 0);
    document.getElementById('kpi-absent').textContent = window.persianNumbers(totals.absent || 0);
    document.getElementById('kpi-late').textContent = window.persianNumbers((totals.late || 0));
    document.getElementById('kpi-sessions').textContent = window.persianNumbers(data.sessions || 0);

    // donut
    var labels = Object.keys(totals).filter(function (k) { return totals[k] > 0; });
    var series = labels.map(function (k) { return totals[k]; });
    var colors = labels.map(function (k) { return STATUS_COLORS[k] || '#6b7280'; });
    var faLabels = labels.map(function (k) { return STATUS_LABELS[k] || k; });
    if (donut) donut.destroy();
    if (series.length) {
      donut = new ApexCharts(document.querySelector('#chart-donut'), chartOptions(series, faLabels, colors));
      donut.render();
    } else {
      document.getElementById('chart-donut').innerHTML = '<div class="pen-empty">در این بازه داده‌ای نیست.</div>';
    }

    // trend (by_day or by_month)
    var buckets = data.by_month || data.by_day || {};
    var keys = Object.keys(buckets);
    if (trend) trend.destroy();
    if (keys.length) {
      var cats = keys;
      var sPresent = keys.map(function (k) { return buckets[k].present || 0; });
      var sAbsent = keys.map(function (k) { return buckets[k].absent || 0; });
      var sLate = keys.map(function (k) { return buckets[k].late || 0; });
      trend = new ApexCharts(document.querySelector('#chart-trend'), {
        chart: { type: 'area', height: 280, fontFamily: 'Vazir, sans-serif', stacked: true },
        series: [
          { name: STATUS_LABELS.present, data: sPresent },
          { name: STATUS_LABELS.absent, data: sAbsent },
          { name: STATUS_LABELS.late, data: sLate },
        ],
        colors: [STATUS_COLORS.present, STATUS_COLORS.absent, STATUS_COLORS.late],
        xaxis: { categories: cats, labels: { rotate: -40 } },
        dataLabels: { enabled: false },
        stroke: { curve: 'smooth' },
        legend: { position: 'bottom' },
      });
      trend.render();
    } else {
      document.getElementById('chart-trend').innerHTML = '<div class="pen-empty">برای این بازه روندی ثبت نشده است.</div>';
    }
  }

  function renderCapacity(rows) {
    var tbody = document.getElementById('cap-tbody');
    if (!rows || !rows.length) {
      tbody.innerHTML = '<tr><td colspan="5"><div class="pen-empty mb-0">برگزاری‌ای با ظرفیت ثبت نشده است.</div></td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (r) {
      var cap = r.capacity || 0;
      var enr = r.enrolled != null ? r.enrolled : (r.enrolled_count || 0);
      var pct = cap > 0 ? Math.min(100, Math.round(enr * 100 / cap)) : 0;
      return '<tr>' +
        '<td>' + window.htmlEscape(r.title || r.id) + '</td>' +
        '<td>' + window.persianNumbers(cap) + '</td>' +
        '<td>' + window.persianNumbers(enr) + '</td>' +
        '<td>' + (cap > 0 ? window.persianNumbers(Math.max(cap - enr, 0)) : '∞') + '</td>' +
        '<td style="min-width:160px"><div class="progress" style="height:8px"><div class="progress-bar" style="width:' + pct + '%"></div></div>' +
        '<span class="fs-13 text-muted">' + window.persianNumbers(pct) + '٪</span></td>' +
        '</tr>';
    }).join('');
  }

  // ── boot ────────────────────────────────────────────────────────────

  function loadAll() {
    fetchJson(EP.attendance + '?' + qs())
      .then(render)
      .catch(function (e) { window.penToast(e.message, 'danger'); });
    fetchJson(EP.capacity)
      .then(renderCapacity)
      .catch(function (e) { window.penToast(e.message, 'danger'); });
  }

  document.querySelectorAll('[data-period]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('[data-period]').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      state.period = btn.dataset.period;
      loadAll();
    });
  });
  var dateInput = document.getElementById('rep-date');
  dateInput.addEventListener('change', function () { state.date = inputValueToISO(); loadAll(); });
  var jalaliCb = document.getElementById('rep-jalali-month');
  jalaliCb.addEventListener('change', function () { state.groupMonth = jalaliCb.checked; loadAll(); });

  if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  loadAll();
})();
