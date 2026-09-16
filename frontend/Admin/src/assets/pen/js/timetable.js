/*
 * Pen LMS — daily timetable grid (rows = locations, cols = 1-hour slots).
 * Data: GET /api/education/timetable/?date=YYYY-MM-DD (read model; the
 * server scopes visibility — this file renders only what it receives).
 *
 * A session block spans ceil(duration) hour-columns via colspan. Hovering a
 * block shows a Bootstrap tooltip: دوره/درس، استاد، کد درس، ساعت، وضعیت.
 */
(function () {
  'use strict';

  var API = '/api/education/timetable/';
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  var $grid = document.getElementById('tt-grid');
  var $head = document.getElementById('tt-hours-row');
  var $body = document.getElementById('tt-body');
  var $date = document.getElementById('tt-date');
  var $label = document.getElementById('tt-date-label');
  if (!$grid) return;

  var STATUS_CLASS = { scheduled: 'tt-scheduled', held: 'tt-held', cancelled: 'tt-cancelled' };

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }

  function todayISO() {
    var d = new Date();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + day;
  }

  function shiftISO(iso, days) {
    var d = new Date(iso + 'T00:00:00');
    d.setDate(d.getDate() + days);
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + day;
  }

  // input shows Jalali (picker writes Jalali); API wants Gregorian ISO.
  function inputValueToISO() {
    var raw = $date.value.trim();
    if (!raw) return todayISO();
    if (window.penJalaliToISO) {
      var iso = window.penJalaliToISO(raw);
      if (iso) return iso;
    }
    return raw; // fallback: user typed ISO directly
  }

  // reflect the loaded date back as Jalali text
  function showJalali(iso) {
    $date.value = window.penISOToJalali ? window.penISOToJalali(iso) : iso;
  }

  function hourToMin(hhmm) {
    var p = (hhmm || '00:00').split(':');
    return parseInt(p[0], 10) * 60 + parseInt(p[1] || '0', 10);
  }

  function tooltipFor(b) {
    var lines = [];
    if (b.offering_title) lines.push('دوره: ' + b.offering_title);
    lines.push('درس: ' + (b.lesson_title || '—'));
    lines.push('استاد: ' + (b.teacher_name || '—'));
    if (b.lesson_code) lines.push('کد درس: ' + b.lesson_code);
    lines.push('ساعت: ' + b.start + ' تا ' + b.end);
    lines.push('وضعیت: ' + (b.status === 'held' ? 'برگزارشده' : 'برنامه‌ریزی‌شده'));
    return lines.join('\n');
  }

  function blockCell(b, span) {
    var cls = STATUS_CLASS[b.status] || 'tt-scheduled';
    return '<td colspan="' + span + '" class="tt-cell">' +
      '<div class="tt-block ' + cls + '" tabindex="0" data-tip="' + esc(tooltipFor(b)) + '">' +
      '<div class="tt-title">' + esc(b.lesson_title || b.offering_title || 'کلاس') + '</div>' +
      '<div class="tt-meta">' + esc(b.teacher_name || '—') +
      (b.lesson_code ? ' <span class="tt-code">' + esc(b.lesson_code) + '</span>' : '') +
      '</div></div></td>';
  }

  function render(data) {
    var hours = data.hours || [];
    $head.innerHTML = '<th scope="col" class="tt-corner">محل / ساعت</th>' +
      hours.map(function (h) { return '<th scope="col" class="tt-hour">' + esc(h) + '</th>'; }).join('');

    var locRows = data.locations || [];
    var blocks = data.blocks || [];
    var byLoc = {};
    var orphans = [];
    blocks.forEach(function (b) {
      if (b.location_id && byLoc[b.location_id] === undefined) byLoc[b.location_id] = [];
      if (b.location_id) (byLoc[b.location_id] = byLoc[b.location_id] || []).push(b);
      else orphans.push(b);
    });

    var rows = [];
    function renderRow(name, sub, list) {
      var cells = '';
      var col = 0; // index into hours
      var gridStart = hours.length ? hourToMin(hours[0]) : 0;
      var placed = {};
      // sort by start so overlaps degrade gracefully (later block skipped cell)
      list.sort(function (a, b2) { return hourToMin(a.start) - hourToMin(b2.start); });
      list.forEach(function (b) {
        var startCol = Math.floor((hourToMin(b.start) - gridStart) / 60);
        var endMin = hourToMin(b.end) || hourToMin(b.start) + 60;
        var span = Math.max(1, Math.ceil((endMin - hourToMin(b.start)) / 60));
        if (startCol < 0) { span += startCol; startCol = 0; }
        if (startCol + span > hours.length) span = hours.length - startCol;
        if (span <= 0 || placed[startCol]) return;
        for (var k = startCol; k < startCol + span; k++) placed[k] = true;
        b.__col = startCol; b.__span = span;
      });
      var byCol = {};
      list.forEach(function (b) { if (b.__col != null) byCol[b.__col] = b; });
      for (var i = 0; i < hours.length; i++) {
        if (byCol[i]) { cells += blockCell(byCol[i], byCol[i].__span); i += byCol[i].__span - 1; }
        else if (!placed[i]) { cells += '<td class="tt-empty"></td>'; }
      }
      rows.push('<tr><th scope="row" class="tt-loc">' + esc(name) +
        (sub ? '<span class="tt-sub">' + esc(sub) + '</span>' : '') + '</th>' + cells + '</tr>');
    }

    locRows.forEach(function (l) { renderRow(l.name, l.building, byLoc[String(l.id)] || []); });
    if (orphans.length) renderRow('بدون مکان', '', orphans);

    if (!rows.length) {
      $body.innerHTML = '<tr><td colspan="' + (hours.length + 1) + '"><div class="pen-empty">' +
        '<i data-lucide="calendar-x-2" class="size-8 opacity-50"></i>' +
        '<p class="mb-0 mt-2">برای این روز جلسه‌ای ثبت نشده است.</p></div></td></tr>';
    } else {
      $body.innerHTML = rows.join('');
    }

    // date label (jalali via Intl if available, else ISO)
    var label = data.date;
    try {
      label = new Intl.DateTimeFormat('fa-IR', { dateStyle: 'full' }).format(new Date(data.date + 'T12:00:00'));
    } catch (e) { /* keep ISO */ }
    $label.textContent = label;

    // tooltips (Bootstrap, multiline via \n → white-space:pre-line)
    if (window.bootstrap && window.bootstrap.Tooltip) {
      $body.querySelectorAll('[data-tip]').forEach(function (el) {
        new window.bootstrap.Tooltip(el, {
          title: el.dataset.tip, html: false, trigger: 'hover focus',
          placement: 'top', customClass: 'tt-tooltip',
        });
      });
    }
    if (window.penRenderIcons) window.penRenderIcons();
  }

  function load(date) {
    $grid.setAttribute('aria-busy', 'true');
    $body.innerHTML = '<tr><td colspan="8"><div class="pen-loading">در حال بارگذاری…</div></td></tr>';
    fetch(API + '?date=' + encodeURIComponent(date), {
      credentials: 'same-origin',
      headers: CSRF ? { 'X-CSRFToken': CSRF } : {},
    })
      .then(function (r) {
        return r.json().then(function (b) {
          if (!r.ok) throw new Error(b.date || b.detail || ('HTTP ' + r.status));
          return b;
        });
      })
      .then(function (data) { showJalali(data.date); render(data); })
      .catch(function (e) { window.penToast(e.message, 'danger'); })
      .finally(function () { $grid.removeAttribute('aria-busy'); });
  }

  function go(iso) {
    showJalali(iso);
    load(iso);
  }

  document.getElementById('tt-prev').addEventListener('click', function () {
    go(shiftISO(inputValueToISO(), -1));
  });
  document.getElementById('tt-next').addEventListener('click', function () {
    go(shiftISO(inputValueToISO(), 1));
  });
  document.getElementById('tt-today').addEventListener('click', function () { go(todayISO()); });
  $date.addEventListener('change', function () {
    if ($date.value) load(inputValueToISO());
  });

  if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  go(todayISO());
})();
