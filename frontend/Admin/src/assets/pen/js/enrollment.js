/*
 * Pen LMS — enrollment form (student + offering + discount + payment/cheques).
 *
 * Money is stored as an integer تومان; the UI shows thousands separators and
 * strips them before sending. final_amount is computed server-side (the API
 * recomputes from course_amount + discount) — the client preview is only UX.
 * The offering's course amount = sum of its lessons' tuition (course bundle).
 */
(function () {
  'use strict';

  var PERSONS = '/api/persons/?person_type=student';
  var OFFERINGS = '/api/education/offerings/';
  var ENROLL = '/api/education/enrollments/';
  var WAITLIST = '/api/education/waitlist/';
  var CSRF = window.getCookie ? window.getCookie('csrftoken') : '';

  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : (s == null ? '' : String(s)); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function get(url) { return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} }).then(function (r) { return r.ok ? r.json() : r.json().then(function (b) { throw new Error(b.detail || b.error || ('HTTP ' + r.status)); }); }); }
  function toast(m, k) { window.penToast && window.penToast(m, k); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }

  function fmt(n) {
    n = Number(n) || 0;
    return window.persianNumbers(n.toLocaleString('en-US').replace(/,/g, '٬'));
  }
  function toInt(v) { return Number(String(v || '').replace(/[^\d]/g, '')) || 0; }

  var state = { courseAmount: 0, lessons: [] };

  // ── student search ──────────────────────────────────────────────────
  var $sSearch = document.getElementById('enr-student-search');
  var $sResults = document.getElementById('enr-student-results');
  var $sHidden = document.getElementById('enr-student');
  var $sPicked = document.getElementById('enr-student-picked');
  var sTimer = null;

  function searchStudents(q) {
    $sResults.style.display = 'block';
    $sResults.innerHTML = '<div class="list-group-item text-muted">در حال جستجو…</div>';
    get(PERSONS + '&search=' + encodeURIComponent(q) + '&page_size=15')
      .then(function (d) {
        var rows = d.results || [];
        if (!rows.length) { $sResults.innerHTML = '<div class="list-group-item text-muted">دانش‌آموزی یافت نشد.</div>'; return; }
        $sResults.innerHTML = rows.map(function (p) {
          return '<button type="button" class="list-group-item list-group-item-action text-start" data-id="' + esc(p.id) + '" data-name="' + esc((p.first_name + ' ' + p.last_name).trim()) + '">' +
            esc((p.first_name + ' ' + p.last_name).trim()) +
            (p.student_code ? ' <span class="fs-13 text-muted">· ' + esc(p.student_code) + '</span>' : '') + '</button>';
        }).join('');
        $sResults.querySelectorAll('[data-id]').forEach(function (b) {
          b.addEventListener('click', function () {
            $sHidden.value = b.dataset.id;
            $sPicked.textContent = 'انتخاب‌شده: ' + b.dataset.name;
            $sSearch.value = b.dataset.name;
            $sResults.style.display = 'none';
          });
        });
      })
      .catch(function (e) { $sResults.innerHTML = '<div class="list-group-item text-danger">' + esc(e.message) + '</div>'; });
  }
  $sSearch.addEventListener('input', function () {
    clearTimeout(sTimer);
    var q = $sSearch.value.trim();
    if (q.length < 1) { $sResults.style.display = 'none'; return; }
    sTimer = setTimeout(function () { searchStudents(q); }, 300);
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('#enr-student-search') && !e.target.closest('#enr-student-results')) $sResults.style.display = 'none';
  });

  // ── offerings ───────────────────────────────────────────────────────
  var $offering = document.getElementById('enr-offering');
  var offerings = [];
  function loadOfferings() {
    get(OFFERINGS + '?page_size=100').then(function (d) {
      offerings = (d.results || []).filter(function (o) { return o.status === 'open' || o.status === 'running' || o.status === 'draft'; });
      $offering.innerHTML = '<option value="">— انتخاب برگزاری —</option>' + offerings.map(function (o) {
        var seats = o.seats_left == null ? 'نامحدود' : window.persianNumbers(o.seats_left) + ' خالی';
        return '<option value="' + esc(o.id) + '">' + esc(o.course_title || o.title || o.id) + ' — ' + seats + '</option>';
      }).join('');
    }).catch(function (e) { toast(e.message, 'danger'); });
  }
  $offering.addEventListener('change', function () {
    var o = offerings.filter(function (x) { return x.id === $offering.value; })[0];
    if (!o) { state.courseAmount = 0; state.lessons = []; renderAmount(); return; }
    // fetch full offering to get lesson tuitions (list may omit them)
    get(OFFERINGS + o.id + '/').then(function (full) {
      state.lessons = full.lesson_titles || [];
      var sum = state.lessons.reduce(function (s, l) { return s + (l.tuition || 0); }, 0);
      state.courseAmount = sum || (full.course_tuition || full.tuition || 0);
      renderAmount();
    }).catch(function () {
      state.courseAmount = o.course_tuition || o.tuition || 0;
      renderAmount();
    });
  });

  // ── discount + final amount ─────────────────────────────────────────
  var $dType = document.getElementById('enr-discount-type');
  var $dVal = document.getElementById('enr-discount-value');
  var $dUnit = document.getElementById('enr-discount-unit');
  var $courseAmt = document.getElementById('enr-course-amount');
  var $final = document.getElementById('enr-final');

  function renderAmount() {
    $courseAmt.value = state.courseAmount ? fmt(state.courseAmount) : '—';
    computeFinal();
  }
  function computeFinal() {
    var base = state.courseAmount || 0;
    var t = $dType.value, dv = toInt($dVal.value);
    var final = base;
    if (t === 'percent') final = base - Math.round(base * Math.min(dv, 100) / 100);
    else if (t === 'amount') final = Math.max(base - dv, 0);
    $final.textContent = fmt(final);
  }
  $dType.addEventListener('change', function () {
    var t = $dType.value;
    $dVal.disabled = (t === 'none');
    $dUnit.textContent = t === 'percent' ? '٪' : (t === 'amount' ? 'تومان' : '—');
    $dVal.value = '';
    computeFinal();
  });
  $dVal.addEventListener('input', function () {
    var digits = $dVal.value.replace(/[^\d]/g, '');
    $dVal.value = digits ? Number(digits).toLocaleString('en-US').replace(/,/g, '٬') : '';
    computeFinal();
  });

  // ── payment method + cheques ────────────────────────────────────────
  var $chequeWrap = document.getElementById('pay-cheque-wrap');
  var $refWrap = document.getElementById('pay-ref-wrap');
  var $chequeCount = document.getElementById('enr-cheque-count');
  var $cheques = document.getElementById('enr-cheques');
  document.querySelectorAll('[name="payment_method"]').forEach(function (r) {
    r.addEventListener('change', function () {
      var cheque = r.value === 'cheque' && r.checked;
      $chequeWrap.classList.toggle('d-none', !cheque);
      $refWrap.classList.toggle('d-none', cheque);
      if (cheque && !$cheques.children.length) buildCheques();
    });
  });
  function buildCheques() {
    var n = Math.max(1, Math.min(12, toInt($chequeCount.value) || 1));
    $cheques.innerHTML = '';
    for (var i = 0; i < n; i++) {
      var row = document.createElement('div');
      row.className = 'row g-2 align-items-end';
      row.innerHTML =
        '<div class="col-12 col-md-3"><label class="form-label fs-13">مبلغ (تومان)</label><input class="form-control form-control-sm" data-cheque="amount" dir="ltr" inputmode="numeric"></div>' +
        '<div class="col-12 col-md-3"><label class="form-label fs-13">در وجه</label><input class="form-control form-control-sm" data-cheque="payee"></div>' +
        '<div class="col-12 col-md-3"><label class="form-label fs-13">تاریخ سررسید</label><input class="form-control form-control-sm" data-cheque="due_date" data-jalali dir="ltr" autocomplete="off" placeholder="۱۴۰۴/۰۸/۰۱"></div>' +
        '<div class="col-12 col-md-3"><label class="form-label fs-13">کد پیگیری</label><input class="form-control form-control-sm" data-cheque="tracking_no" dir="ltr"></div>';
      $cheques.appendChild(row);
    }
    rowMoneyInputs($cheques);
    if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  }
  document.getElementById('enr-cheque-build').addEventListener('click', buildCheques);
  function rowMoneyInputs(scope) {
    scope.querySelectorAll('[data-cheque="amount"]').forEach(function (inp) {
      inp.addEventListener('input', function () {
        var d = inp.value.replace(/[^\d]/g, '');
        inp.value = d ? Number(d).toLocaleString('en-US').replace(/,/g, '٬') : '';
      });
    });
  }

  // ── submit ──────────────────────────────────────────────────────────
  document.getElementById('enr-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var $err = document.getElementById('enr-errors');
    function fail(msg) { $err.querySelector('ul').innerHTML = '<li>' + esc(msg) + '</li>'; $err.hidden = false; }
    $err.hidden = true;
    var student = $sHidden.value, offering = $offering.value;
    if (!student) return fail('یک دانش‌آموز انتخاب کنید.');
    if (!offering) return fail('برگزاری را انتخاب کنید.');
    var method = (document.querySelector('[name="payment_method"]:checked') || {}).value || 'cash';
    var payload = {
      offering: offering, student: student,
      course_amount: state.courseAmount,
      discount_type: $dType.value,
      discount_value: toInt($dVal.value),
      payment_method: method,
    };
    var enrolledAt = document.getElementById('enr-date').value.trim();
    if (enrolledAt) payload.enrolled_at = enrolledAt; // empty → server default
    if (method === 'cheque') {
      var cheques = Array.prototype.slice.call($cheques.children).map(function (row) {
        return {
          amount: toInt(row.querySelector('[data-cheque="amount"]').value),
          payee: row.querySelector('[data-cheque="payee"]').value.trim(),
          due_date: row.querySelector('[data-cheque="due_date"]').value.trim(),
          tracking_no: row.querySelector('[data-cheque="tracking_no"]').value.trim(),
        };
      });
      if (!cheques.length) return fail('حداقل یک چک وارد کنید.');
      payload.cheques = cheques;
      payload.cheque_count = cheques.length;
    } else {
      payload.reference = document.getElementById('enr-reference').value.trim();
    }
    fetch(ENROLL, { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(payload) })
      .then(function (r) { return r.json().then(function (b) { return { ok: r.ok, b: b }; }); })
      .then(function (res) {
        if (!res.ok) {
          var lines = Object.keys(res.b).map(function (k) { var v = res.b[k]; return k + ': ' + (Array.isArray(v) ? v.join('، ') : v); });
          return fail(lines.join(' — ') || 'خطا در ثبت‌نام');
        }
        toast(res.b.waitlisted ? 'ظرفیت تکمیل است؛ دانش‌آموز در صف انتظار قرار گرفت.' : 'ثبت‌نام انجام شد ✓', res.b.waitlisted ? 'warning' : 'success');
        document.getElementById('enr-form').reset();
        $sPicked.textContent = ''; state.courseAmount = 0; renderAmount();
        $cheques.innerHTML = ''; $chequeWrap.classList.add('d-none'); $refWrap.classList.remove('d-none');
        loadRecent();
        loadWaitlist();
      })
      .catch(function (e) { fail(e.message); });
  });

  // ── recent enrollments ──────────────────────────────────────────────
  function loadRecent() {
    var $box = document.getElementById('enr-recent');
    $box.setAttribute('aria-busy', 'true');
    get(ENROLL + '?page_size=15').then(function (d) {
      var rows = d.results || [];
      if (!rows.length) { $box.innerHTML = '<div class="pen-empty py-4"><p class="mb-0 fs-14">هنوز ثبت‌نامی نیست.</p></div>'; return; }
      var PM = { cash: 'نقدی', pos: 'کارت‌خوان', cheque: 'چک' };
      $box.innerHTML = rows.map(function (r) {
        return '<div class="px-3 py-2 border-bottom">' +
          '<div class="d-flex align-items-center gap-2"><strong class="fs-14">' + esc(r.student_name || '') + '</strong>' +
          '<span class="badge bg-primary-subtle text-primary ms-auto">' + fmt(r.final_amount) + ' ت</span></div>' +
          '<div class="fs-13 text-muted">' + esc(r.offering_title || '') + ' · ' + esc(PM[r.payment_method] || r.payment_method) +
          (r.discount_type !== 'none' ? ' · تخفیف ' + esc(r.discount_value) + (r.discount_type === 'percent' ? '٪' : 'ت') : '') +
          ' · ' + esc(r.enrolled_at || '') + '</div></div>';
      }).join('');
    }).catch(function (e) { $box.innerHTML = '<div class="pen-empty py-4">' + esc(e.message) + '</div>'; })
      .finally(function () { $box.removeAttribute('aria-busy'); icons(); });
  }

  function loadWaitlist() {
    var $box = document.getElementById('enr-waitlist');
    if (!$box) return;
    get(WAITLIST + '?page_size=15&status=waiting').then(function (d) {
      var rows = d.results || [];
      if (!rows.length) { $box.innerHTML = '<div class="pen-empty py-4"><p class="mb-0 fs-14">صف انتظاری ثبت نشده است.</p></div>'; return; }
      $box.innerHTML = rows.map(function (r) {
        return '<div class="px-3 py-2 border-bottom"><div class="d-flex align-items-center gap-2"><strong class="fs-14">' + esc(r.student_name || '') + '</strong>' +
          '<span class="badge bg-warning-subtle text-warning ms-auto">نفر ' + window.persianNumbers(r.position || 0) + '</span></div>' +
          '<div class="fs-13 text-muted">' + esc(r.offering_title || '') + ' · درخواست ' + esc(r.requested_at || '') + '</div></div>';
      }).join('');
    }).catch(function (e) { $box.innerHTML = '<div class="pen-empty py-4">' + esc(e.message) + '</div>'; });
  }

  // ── boot ────────────────────────────────────────────────────────────
  loadOfferings();
  loadRecent();
  loadWaitlist();
  renderAmount();
  if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
})();
