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
  var OFFERINGS = window.__LEAD_ENROLLMENT_API__ ? window.__LEAD_ENROLLMENT_API__ + 'offerings/' : '/api/education/offerings/';
  var ENROLL = window.__LEAD_ENROLLMENT_API__ ? window.__LEAD_ENROLLMENT_API__ + 'enrollments/' : '/api/education/enrollments/';
  var WAITLIST = '/api/education/waitlist/';
  var LEAD_ID = window.__LEAD_ID__ || new URLSearchParams(window.location.search).get('lead');
  var LEAD_API = LEAD_ID ? '/api/leads/' + encodeURIComponent(LEAD_ID) + '/' : '';
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
  function toInt(v) {
    var digits = String(v || '').replace(/[۰-۹٠-٩]/g, function (d) {
      var fa = '۰۱۲۳۴۵۶۷۸۹', ar = '٠١٢٣٤٥٦٧٨٩';
      return String(fa.indexOf(d) >= 0 ? fa.indexOf(d) : ar.indexOf(d));
    }).replace(/[^\d]/g, '');
    return Number(digits) || 0;
  }
  function inputMoney(n) { return n ? Number(n).toLocaleString('en-US').replace(/,/g, '٬') : ''; }

  var state = { courseAmount: 0, lessons: [] };
  var leadState = null;
  var leadCourseId = '';

  // ── student search ──────────────────────────────────────────────────
  var $sSearch = document.getElementById('enr-student-search');
  var $sResults = document.getElementById('enr-student-results');
  var $sHidden = document.getElementById('enr-student');
  var $sPicked = document.getElementById('enr-student-picked');
  var sTimer = null;
  if (window.__LEAD_ENROLLMENT_API__) $sSearch.readOnly = true;

  function setStudent(id, name) {
    $sHidden.value = id || '';
    $sPicked.textContent = id ? 'انتخاب‌شده: ' + name : '';
    if (id) {
      document.getElementById('enr-person-create-wrap').classList.add('d-none');
    }
  }

  function loadLeadContext() {
    if (!LEAD_ID) return Promise.resolve();
    return get(LEAD_API).then(function (lead) {
      leadState = lead;
      leadCourseId = lead.course || '';
      var context = document.getElementById('enr-lead-context');
      context.classList.remove('d-none');
      document.getElementById('enr-lead-summary').textContent = lead.student_name + ' · ' + (lead.phone || 'بدون شماره') + ' · ' + (lead.course_title || 'دوره‌ای انتخاب نشده') + (lead.assessment_result ? ' · نتیجه: ' + lead.assessment_result : '');
      $sSearch.value = lead.student_name || '';
      if (lead.enrolled_person) {
        setStudent(lead.enrolled_person, lead.enrolled_person_name || lead.student_name);
      } else {
        document.getElementById('enr-person-create-wrap').classList.remove('d-none');
      }
    });
  }

  document.getElementById('enr-create-person').addEventListener('click', function () {
    if (!LEAD_ID) return;
    var nationalCode = document.getElementById('enr-lead-national-code').value.trim().replace(/[۰-۹٠-٩]/g, function (digit) {
      return String('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩'.indexOf(digit) % 10);
    });
    if (!/^\d{10}$/.test(nationalCode) || !window.penNationalCodeChecksumValid(nationalCode)) return toast('کد ملی معتبر نیست.', 'danger');
    var button = document.getElementById('enr-create-person');
    button.disabled = true;
    fetch('/api/leads/' + encodeURIComponent(LEAD_ID) + '/create-person/', { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify({ national_code: nationalCode, father_name: document.getElementById('enr-lead-father-name').value.trim() }) })
      .then(function (r) { return r.json().then(function (b) { if (!r.ok) throw new Error(Object.keys(b).map(function (k) { return Array.isArray(b[k]) ? b[k].join('، ') : b[k]; }).join(' — ') || 'افزودن دانش‌آموز انجام نشد.'); return b; }); })
      .then(function (person) { setStudent(person.person_id, person.person_name); toast('پرونده دانش‌آموز ساخته شد.', 'success'); })
      .catch(function (e) { toast(e.message, 'danger'); })
      .finally(function () { button.disabled = false; });
  });

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
        return '<option value="' + esc(o.id) + '">' + esc(o.course_title || o.title || o.id) + ' — مدرس: ' + esc(o.instructor_name || 'مدرس تعیین نشده') + ' — ' + seats + '</option>';
      }).join('');
      if (leadCourseId) {
        var matching = offerings.filter(function (o) { return String(o.course) === String(leadCourseId); });
        if (matching.length === 1) {
          $offering.value = matching[0].id;
          $offering.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
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
  var $isFree = document.getElementById('enr-is-free');
  function isFree() { return !!($isFree && $isFree.checked); }
  function updateFreeMode() {
    var free = isFree();
    $dType.disabled = free;
    $dVal.disabled = free || $dType.value === 'none';
    document.getElementById('enr-payment-section').hidden = free;
    document.getElementById('enr-payment-section').querySelectorAll('input, select, button').forEach(function (input) { input.disabled = free; });
    var reason = document.getElementById('enr-free-reason-fields');
    if (reason) reason.hidden = !free;
    computeFinal();
  }
  if ($isFree) $isFree.addEventListener('change', updateFreeMode);

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
    if (isFree()) final = 0;
    state.finalAmount = final;
    $final.textContent = fmt(final);
    updatePaymentTotals();
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

  // ── split payments ───────────────────────────────────────────────────
  var $paymentLines = document.getElementById('enr-payment-lines');
  var $paidSum = document.getElementById('enr-paid-sum');
  function updatePaymentTotals() {
    if (!$paymentLines || !$paidSum) return;
    if (isFree()) { $paidSum.textContent = fmt(0); return; }
    var firstAmount = $paymentLines.querySelector('[data-pay="amount"]');
    var suggested = state.finalAmount || 0;
    if (firstAmount && (typeof state.paymentSuggestion === 'undefined' || toInt(firstAmount.value) === state.paymentSuggestion)) {
      firstAmount.value = suggested ? fmt(suggested) : '';
      state.paymentSuggestion = suggested;
    }
    var sum = Array.prototype.reduce.call($paymentLines.querySelectorAll('[data-pay="amount"]'), function (n, input) { return n + toInt(input.value); }, 0);
    $paidSum.textContent = fmt(sum);
  }
  function addPaymentLine(prefill) {
    var row = document.createElement('div');
    row.className = 'border rounded-2 bg-white p-3';
    row.innerHTML = '<div class="row g-2 align-items-end">' +
      '<div class="col-12 col-md-3"><label class="form-label fs-13">روش پرداخت</label><select class="form-select form-select-sm" data-pay="method"><option value="cash">نقدی</option><option value="pos">کارت‌خوان (POS)</option><option value="card_transfer">کارت‌به‌کارت</option><option value="cheque">چک</option></select></div>' +
      '<div class="col-12 col-md-3"><label class="form-label fs-13">مبلغ (تومان)</label><input class="form-control form-control-sm" data-pay="amount" dir="ltr" inputmode="numeric"></div>' +
      '<div class="col-12 col-md-2"><label class="form-label fs-13">پرداخت‌کننده</label><input class="form-control form-control-sm" data-pay="payer" placeholder="اختیاری"></div>' +
      '<div class="col-12 col-md-3"><label class="form-label fs-13">کد رسید / مرجع</label><input class="form-control form-control-sm" data-pay="reference" dir="ltr" placeholder="اختیاری"></div>' +
      '<div class="col-12 col-md-1"><button type="button" class="btn btn-light btn-sm w-100" data-pay="remove" aria-label="حذف ردیف پرداخت"><i data-lucide="x" class="size-4" aria-hidden="true"></i></button></div>' +
      '<div class="col-12 row g-2 d-none" data-pay="cheque-fields"><div class="col-12 col-md-4"><label class="form-label fs-13">شماره چک</label><input class="form-control form-control-sm" data-pay="cheque-number" dir="ltr"></div><div class="col-12 col-md-4"><label class="form-label fs-13">در وجه</label><input class="form-control form-control-sm" data-pay="payee"></div><div class="col-12 col-md-4"><label class="form-label fs-13">سررسید</label><input class="form-control form-control-sm" data-pay="due" data-jalali dir="ltr" autocomplete="off" placeholder="۱۴۰۵/۰۱/۱۵"></div></div></div>';
    $paymentLines.appendChild(row);
    var method = row.querySelector('[data-pay="method"]');
    method.addEventListener('change', function () { row.querySelector('[data-pay="cheque-fields"]').classList.toggle('d-none', method.value !== 'cheque'); });
    row.querySelector('[data-pay="remove"]').addEventListener('click', function () { if ($paymentLines.children.length > 1) row.remove(); updatePaymentTotals(); });
    var amount = row.querySelector('[data-pay="amount"]');
    amount.value = inputMoney(prefill);
    amount.addEventListener('input', function () {
      amount.value = inputMoney(toInt(amount.value));
      updatePaymentTotals();
    });
    icons();
    if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  }
  document.getElementById('enr-payment-add').addEventListener('click', function () { addPaymentLine(); });
  addPaymentLine(state.courseAmount);

  // ── submit ──────────────────────────────────────────────────────────
  document.getElementById('enr-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var $err = document.getElementById('enr-errors');
    function fail(msg) { $err.querySelector('ul').innerHTML = '<li>' + esc(msg) + '</li>'; $err.hidden = false; }
    $err.hidden = true;
    var student = $sHidden.value, offering = $offering.value;
    if (!student) return fail('یک دانش‌آموز انتخاب کنید.');
    if (!offering) return fail('برگزاری را انتخاب کنید.');
    var payments = isFree() ? [] : Array.prototype.map.call($paymentLines.children, function (row) {
      var method = row.querySelector('[data-pay="method"]').value;
      return {
        method: method,
        amount: toInt(row.querySelector('[data-pay="amount"]').value),
        payer_name: row.querySelector('[data-pay="payer"]').value.trim(),
        reference: row.querySelector('[data-pay="reference"]').value.trim(),
        cheque_number: row.querySelector('[data-pay="cheque-number"]').value.trim(),
        cheque_payee: row.querySelector('[data-pay="payee"]').value.trim(),
        cheque_due_date: row.querySelector('[data-pay="due"]').value.trim()
      };
    });
    if (!isFree() && (!payments.length || payments.some(function (line) { return line.amount <= 0; }))) return fail('مبلغ همهٔ ردیف‌های پرداخت باید بیشتر از صفر باشد.');
    if (payments.reduce(function (sum, line) { return sum + line.amount; }, 0) > (state.finalAmount || 0)) return fail('جمع پرداخت‌ها از مبلغ قابل‌پرداخت بیشتر است.');
    var payload = {
      offering: offering, student: student,
      course_amount: state.courseAmount,
      is_free: isFree(),
      discount_type: isFree() ? 'none' : $dType.value,
      discount_value: isFree() ? 0 : toInt($dVal.value),
      payments: payments,
    };
    if (isFree()) payload.free_reason = document.getElementById('enr-free-reason').value.trim();
    if (LEAD_ID) payload.lead = LEAD_ID;
    var enrolledAt = document.getElementById('enr-date').value.trim();
    if (enrolledAt) payload.enrolled_at = enrolledAt; // empty → server default
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
        $paymentLines.innerHTML = ''; state.paymentSuggestion = undefined; addPaymentLine();
        updateFreeMode();
        if (window.__LEAD_ENROLLMENT_API__ && !res.b.waitlisted) {
          window.location.href = '/leads/';
          return;
        }
        loadRecent();
        loadWaitlist();
      })
      .catch(function (e) { fail(e.message); });
  });

  // ── recent enrollments ──────────────────────────────────────────────
  function loadRecent() {
    var $box = document.getElementById('enr-recent');
    if (!$box) return;
    $box.setAttribute('aria-busy', 'true');
    get(ENROLL + '?page_size=15').then(function (d) {
      var rows = d.results || [];
      if (!rows.length) { $box.innerHTML = '<div class="pen-empty py-4"><p class="mb-0 fs-14">هنوز ثبت‌نامی نیست.</p></div>'; return; }
      var PM = { cash: 'نقدی', pos: 'کارت‌خوان', cheque: 'چک' };
      $box.innerHTML = rows.map(function (r) {
        return '<div class="px-3 py-2 border-bottom">' +
          '<div class="d-flex align-items-center gap-2"><strong class="fs-14">' + esc(r.student_name || '') + '</strong>' +
          '<span class="badge bg-primary-subtle text-primary ms-auto">' + (r.is_free ? 'ثبت‌نام رایگان' : fmt(r.final_amount) + ' ت') + '</span></div>' +
          '<div class="fs-13 text-muted">' + esc(r.offering_title || '') + ' · مدرس: ' + esc(r.teacher ? r.teacher.name : 'مدرس تعیین نشده') + (r.is_free ? '' : ' · ' + esc(PM[r.payment_method] || r.payment_method)) +
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
  loadLeadContext().then(loadOfferings).catch(function (e) { toast('اطلاعات ثبت‌شده دریافت نشد: ' + e.message, 'danger'); });
  loadRecent();
  loadWaitlist();
  renderAmount();
  if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
})();
