/*
 * Pen LMS — teacher descriptive report cards (پنل مدرس › کارنامه توصیفی).
 *
 * Flow (task spec §3): pick one of MY active classes → every student loads as
 * a row → per student: قبول/مردود + required descriptive feedback → bulk save.
 *
 * API: GET  /api/education/offerings/{id}/report-cards/ → {roster, cards}
 *      POST the same URL with {rows:[{student,result,teacher_note}]}.
 * Idempotent server-side (update_or_create): re-saving corrects, never
 * duplicates. Each selected result requires descriptive feedback, enforced in
 * the model + service and mirrored by the client before submit.
 */
(function () {
  'use strict';

  var CLASSES_URL = '/api/education/teacher/classes/';
  var CARDS = function (oid) { return '/api/education/offerings/' + oid + '/report-cards/'; };

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function pn(s) { return window.persianNumbers ? window.persianNumbers(s) : s; }
  function headers() {
    return Object.assign({ 'Content-Type': 'application/json' },
      window.penCsrfHeader ? window.penCsrfHeader() : {});
  }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (r) {
        return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); });
      });
  }
  function post(url, body) {
    return fetch(url, { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body) })
      .then(function (r) {
        return r.json().then(function (b) {
          if (r.ok) return b;
          var msg = b.error || b.detail || ('HTTP ' + r.status);
          throw new Error(msg);
        });
      });
  }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }
  function param(name) { return new URLSearchParams(location.search).get(name) || ''; }

  var $cls = document.getElementById('rc-class');
  var $info = document.getElementById('rc-info');
  var $sessionStatus = document.getElementById('rc-session-status');
  var $rows = document.getElementById('rc-rows');
  var $count = document.getElementById('rc-count');
  var $summary = document.getElementById('rc-summary');
  var $save = document.getElementById('rc-save');

  var classes = [];
  var rows = [];   // [{id,name,student_code,result,teacher_note}]
  var canSubmit = false;

  function showSessionProgress(progress) {
    var total = Number(progress.total || 0);
    var remaining = Number(progress.remaining || 0);
    canSubmit = progress.ready === true;
    $sessionStatus.className = 'alert mt-3 mb-0 py-2 fs-13 ' +
      (canSubmit ? 'alert-success' : 'alert-warning');
    $sessionStatus.textContent = !total
      ? 'برای ثبت کارنامه، ابتدا جلسات این دوره را تعریف کنید.'
      : canSubmit
        ? 'برای همهٔ ' + pn(total) + ' جلسه حضور و غیاب ثبت شده؛ ثبت کارنامه فعال است.'
        : 'ثبت کارنامه پس از ثبت حضور و غیاب همهٔ جلسات فعال می‌شود؛ ' + pn(remaining) + ' جلسه بدون ثبت حضور و غیاب است.';
  }

  function resultSeg(row) {
    return '<div class="pen-seg" role="group" aria-label="وضعیت ' + esc(row.name) + '">' +
      '<button type="button" class="btn btn-sm ' + (row.result === 'passed' ? 'btn-success' : 'btn-outline-success') + '" data-result="passed"' + (!canSubmit ? ' disabled' : '') + '>' +
      '<i data-lucide="check" class="size-4 me-1"></i>قبول</button>' +
      '<button type="button" class="btn btn-sm ' + (row.result === 'failed' ? 'btn-danger' : 'btn-outline-danger') + '" data-result="failed"' + (!canSubmit ? ' disabled' : '') + '>' +
      '<i data-lucide="x" class="size-4 me-1"></i>مردود</button>' +
      '</div>';
  }

  function renderRows() {
    if (!rows.length) {
      $rows.innerHTML = '<tr><td colspan="4"><div class="pen-empty">' +
        ($cls.value ? 'این کلاس دانش‌آموز فعالی ندارد.' : 'کلاس را انتخاب کنید تا فهرست دانش‌آموزان بارگذاری شود.') +
        '</div></td></tr>';
      $count.textContent = ''; $save.disabled = true; updateSummary();
      return;
    }
    $count.textContent = '— ' + pn(rows.length) + ' دانش‌آموز';
    $save.disabled = !canSubmit;
    $rows.innerHTML = rows.map(function (r, i) {
      return '<tr data-id="' + esc(r.id) + '">' +
        '<td class="text-muted">' + pn(i + 1) + '</td>' +
        '<td><div class="fw-semibold">' + esc(r.name) + '</div>' +
        '<div class="fs-13 text-muted" dir="ltr">' + esc(r.student_code || '') + '</div></td>' +
        '<td>' + resultSeg(r) + '</td>' +
        '<td><textarea class="form-control form-control-sm rc-note" rows="2" maxlength="1000" aria-required="true" aria-describedby="rc-note-required"' + (!canSubmit ? ' disabled' : '') + ' ' +
          'placeholder="پیشرفت در مکالمه، درک شنیداری و واژگان، نیاز به تمرین و دلیل ارزیابی را بنویسید…" ' +
          'aria-label="بازخورد ' + esc(r.name) + '">' + esc(r.teacher_note || '') + '</textarea></td>' +
        '</tr>';
    }).join('');

    $rows.querySelectorAll('tr').forEach(function ($tr) {
      var id = $tr.dataset.id;
      function row() { return rows.filter(function (x) { return x.id === id; })[0]; }
      $tr.querySelectorAll('[data-result]').forEach(function ($btn) {
        $btn.addEventListener('click', function () {
          var r = row(); if (!r) return;
          r.result = (r.result === $btn.dataset.result) ? '' : $btn.dataset.result;
          paintResultButtons($tr, r);
          validateRow($tr, r);
          updateSummary();
        });
      });
      var $note = $tr.querySelector('.rc-note');
      $note.addEventListener('input', function () {
        var r = row(); if (!r) return;
        r.teacher_note = $note.value;
        validateRow($tr, r);
        updateSummary();
      });
    });
    updateSummary();
    icons();
  }

  function paintResultButtons($tr, r) {
    $tr.querySelectorAll('[data-result]').forEach(function (b) {
      var kind = b.dataset.result;
      var on = r.result === kind;
      b.className = 'btn btn-sm ' + (
        kind === 'passed'
          ? (on ? 'btn-success' : 'btn-outline-success')
          : (on ? 'btn-danger' : 'btn-outline-danger'));
    });
  }

  function validateRow($tr, r) {
    var bad = !!r.result && !(r.teacher_note || '').trim();
    var $note = $tr.querySelector('.rc-note');
    $note.classList.toggle('is-invalid', bad);
    if (bad) $note.setAttribute('aria-invalid', 'true');
    else $note.removeAttribute('aria-invalid');
    return !bad;
  }

  function updateSummary() {
    var passed = rows.filter(function (r) { return r.result === 'passed'; }).length;
    var failed = rows.filter(function (r) { return r.result === 'failed'; }).length;
    var unset = rows.filter(function (r) { return !r.result; }).length;
    $summary.innerHTML = rows.length
      ? 'قبول ' + pn(passed) + ' · مردود ' + pn(failed) +
        (unset ? ' · <span class="text-danger">بدون تصمیم: ' + pn(unset) + '</span>' : '')
      : '—';
  }

  function openClass(oid) {
    var c = classes.filter(function (x) { return x.id === oid; })[0];
    $info.textContent = c
      ? ('محل: ' + (c.location || '—') + ' · ظرفیت: ' + pn(c.capacity || 0) +
         ' · جلسات برگزارشده: ' + pn((c.stats && c.stats.held) || 0))
      : '';
    return get(CARDS(oid)).then(function (d) {
      showSessionProgress(d.session_progress || {});
      var byStudent = {};
      (d.cards || []).forEach(function (card) { byStudent[card.student] = card; });
      rows = (d.roster || []).map(function (r) {
        var card = byStudent[r.id] || {};
        return { id: r.id, name: r.name, student_code: r.student_code,
                 result: card.result || '', teacher_note: card.teacher_note || '' };
      });
      renderRows();
    });
  }

  $cls.addEventListener('change', function () {
    rows = [];
    canSubmit = false;
    $save.disabled = true;
    $sessionStatus.className = 'alert d-none mt-3 mb-0 py-2 fs-13';
    $sessionStatus.textContent = '';
    if (!$cls.value) { renderRows(); return; }
    openClass($cls.value).catch(function (e) {
      $sessionStatus.className = 'alert alert-danger mt-3 mb-0 py-2 fs-13';
      $sessionStatus.textContent = 'وضعیت جلسات بررسی نشد؛ دوباره تلاش کنید.';
      toast(e.message, 'danger');
    });
  });

  $save.addEventListener('click', function () {
    if (!$cls.value || !rows.length || !canSubmit) return;
    var ok = true;
    $rows.querySelectorAll('tr').forEach(function ($tr) {
      var r = rows.filter(function (x) { return x.id === $tr.dataset.id; })[0];
      if (r && !validateRow($tr, r)) ok = false;
    });
    if (!ok) { toast('برای هر دانش‌آموزی که نتیجه دارد، نوشتن بازخورد توصیفی الزامی است.', 'warning'); return; }
    var unset = rows.filter(function (r) { return !r.result; });
    if (unset.length && !window.confirm(pn(unset.length) + ' دانش‌آموز هنوز نتیجه‌ای ندارند. فقط ' + pn(rows.length - unset.length) + ' ردیف ذخیره شود؟')) return;
    var payload = {
      rows: rows.filter(function (r) { return r.result; }).map(function (r) {
        return { student: r.id, result: r.result, teacher_note: (r.teacher_note || '').trim() };
      }),
    };
    if (!payload.rows.length) { toast('هیچ نتیجه‌ای انتخاب نشده است.', 'warning'); return; }
    $save.disabled = true;
    post(CARDS($cls.value), payload)
      .then(function (res) {
        toast('کارنامه ذخیره شد — ' + pn(res.created || 0) + ' جدید، ' + pn(res.updated || 0) + ' اصلاحی.', 'success');
      })
      .catch(function (e) { toast(e.message, 'danger'); })
      .finally(function () { $save.disabled = false; });
  });

  document.addEventListener('DOMContentLoaded', function () {
    get(CLASSES_URL).then(function (d) {
      classes = (d.results || []).filter(function (c) { return c.can_manage !== false; });
      $cls.innerHTML = '<option value="">— انتخاب کلاس —</option>' + classes.map(function (c) {
        return '<option value="' + esc(c.id) + '">' + esc(c.title || c.course) +
          ' (' + pn(c.roster_size || 0) + ' دانش‌آموز)</option>';
      }).join('');
      var q = param('class');
      if (q && classes.some(function (c) { return c.id === q; })) {
        $cls.value = q;
        return openClass(q);
      }
    }).catch(function (e) { toast(e.message, 'danger'); });
  });
})();
