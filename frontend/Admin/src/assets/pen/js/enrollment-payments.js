/* Payment ledger and later installment entry for the education workspace. */
(function () {
  'use strict';

  function esc(value) { return window.htmlEscape ? window.htmlEscape(value) : (value == null ? '' : String(value)); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', headers: window.penCsrfHeader ? window.penCsrfHeader() : {} })
      .then(function (response) { return response.ok ? response.json() : response.json().then(function (data) { throw new Error(data.detail || data.error || ('HTTP ' + response.status)); }); });
  }
  function toast(message, type) { window.penToast && window.penToast(message, type); }
  function icons() { window.penRenderIcons && window.penRenderIcons(); }
  function fmt(number) {
    number = Number(number) || 0;
    return window.persianNumbers(number.toLocaleString('en-US').replace(/,/g, '٬'));
  }
  function toInt(value) {
    var fa = '۰۱۲۳۴۵۶۷۸۹', ar = '٠١٢٣٤٥٦٧٨٩';
    var digits = String(value || '').replace(/[۰-۹٠-٩]/g, function (digit) {
      var index = fa.indexOf(digit);
      return String(index >= 0 ? index : ar.indexOf(digit));
    }).replace(/[^\d]/g, '');
    return Number(digits) || 0;
  }
  function inputMoney(number) { return number ? Number(number).toLocaleString('en-US').replace(/,/g, '٬') : ''; }

  var $rows = document.getElementById('payment-history-rows');
  var $more = document.getElementById('payment-history-more');
  var $search = document.getElementById('payment-history-search');
  var $methodFilter = document.getElementById('payment-history-method');
  var $modalElement = document.getElementById('payment-add-modal');
  var $form = document.getElementById('payment-add-form');
  var $method = document.getElementById('payment-add-method');
  var $amount = document.getElementById('payment-add-amount');
  var modal = window.bootstrap && window.bootstrap.Modal ? window.bootstrap.Modal.getOrCreateInstance($modalElement) : null;
  var nextPage = null;
  var timer;
  var labels = { cash: 'نقدی', pos: 'کارت‌خوان', card_transfer: 'کارت‌به‌کارت', cheque: 'چک' };

  function load(reset) {
    if (reset) nextPage = null;
    if (!reset && nextPage) {
      get(nextPage).then(render).catch(showError);
      return;
    }
    var params = new URLSearchParams();
    if ($search.value.trim()) params.set('q', $search.value.trim());
    if ($methodFilter.value) params.set('method', $methodFilter.value);
    $rows.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">در حال دریافت سوابق…</td></tr>';
    get('/api/education/payments/?' + params.toString()).then(render).catch(showError);
  }

  function showError(error) {
    $rows.innerHTML = '<tr><td colspan="9" class="text-center text-danger py-4">' + esc(error.message) + '</td></tr>';
    $more.hidden = true;
  }

  function render(data) {
    var payments = data.results || [];
    if (nextPage === null) $rows.innerHTML = '';
    if (!payments.length && !$rows.children.length) {
      $rows.innerHTML = '<tr><td colspan="9" class="text-center py-5 text-muted">پرداختی با این مشخصات ثبت نشده است.</td></tr>';
    } else {
      $rows.insertAdjacentHTML('beforeend', payments.map(function (payment) {
        var course = payment.course_title || payment.offering_title || '—';
        var receipt = payment.method === 'cheque' ? ('چک ' + (payment.cheque_number || '')) : (payment.reference || '—');
        var when = payment.paid_at ? new Date(payment.paid_at).toLocaleString('fa-IR', { dateStyle: 'short', timeStyle: 'short' }) : '—';
        var balance = Math.max(0, Number(payment.remaining_balance) || 0);
        var action = balance > 0
          ? '<button type="button" class="btn btn-outline-primary btn-sm" data-pay-add="' + esc(payment.enrollment) + '" data-remaining-balance="' + balance + '" data-student-name="' + esc(payment.student_name || '') + '" data-course-name="' + esc(course) + '">افزودن پرداخت</button>'
          : '<span class="badge bg-success-subtle text-success">تسویه‌شده</span>';
        return '<tr><td class="fw-medium">' + esc(payment.student_name || '—') + '</td><td>' + esc(course) +
          (payment.offering_title && payment.course_title ? '<div class="fs-13 text-muted">' + esc(payment.offering_title) + '</div>' : '') +
          '</td><td><span class="badge bg-primary-subtle text-primary">' + esc(labels[payment.method] || payment.method) + '</span><div class="mt-1 fw-semibold">' + fmt(payment.amount) + ' تومان</div><div class="fs-13 text-muted">مانده: ' + fmt(balance) + ' تومان</div></td>' +
          '<td dir="ltr"><code>' + esc(payment.tracking_code || '—') + '</code></td><td>' + esc(receipt) +
          (payment.cheque_payee ? '<div class="fs-13 text-muted">در وجه ' + esc(payment.cheque_payee) + '</div>' : '') +
          '</td><td>' + esc(payment.payer_name || '—') + '</td><td>' + esc(payment.recorded_by_name || '—') +
          '</td><td class="text-nowrap">' + esc(when) + '</td><td>' + action + '</td></tr>';
      }).join(''));
    }
    nextPage = data.next || null;
    $more.hidden = !nextPage;
  }

  $search.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { load(true); }, 250);
  });
  $methodFilter.addEventListener('change', function () { load(true); });
  $more.addEventListener('click', function () { load(false); });

  $rows.addEventListener('click', function (event) {
    var button = event.target.closest('[data-pay-add]');
    if (!button) return;
    var balance = Number(button.dataset.remainingBalance) || 0;
    document.getElementById('payment-add-enrollment').value = button.dataset.payAdd;
    document.getElementById('payment-add-context').textContent = button.dataset.studentName + ' · ' + button.dataset.courseName;
    document.getElementById('payment-add-balance').textContent = fmt(balance);
    document.getElementById('payment-add-error').hidden = true;
    $method.value = 'cash';
    $amount.value = inputMoney(balance);
    document.getElementById('payment-add-payer').value = '';
    document.getElementById('payment-add-reference').value = '';
    document.getElementById('payment-add-cheque-fields').classList.add('d-none');
    document.getElementById('payment-add-cheque-number').value = '';
    document.getElementById('payment-add-payee').value = '';
    document.getElementById('payment-add-due').value = '';
    modal && modal.show();
    window.penAttachJalaliPickers && window.penAttachJalaliPickers();
  });

  $method.addEventListener('change', function () {
    document.getElementById('payment-add-cheque-fields').classList.toggle('d-none', $method.value !== 'cheque');
  });
  $amount.addEventListener('input', function () { $amount.value = inputMoney(toInt($amount.value)); });
  $form.addEventListener('submit', function (event) {
    event.preventDefault();
    var error = document.getElementById('payment-add-error');
    error.hidden = true;
    var method = $method.value;
    var body = {
      method: method,
      amount: toInt($amount.value),
      payer_name: document.getElementById('payment-add-payer').value.trim(),
      reference: document.getElementById('payment-add-reference').value.trim()
    };
    if (method === 'cheque') {
      body.cheque_number = document.getElementById('payment-add-cheque-number').value.trim();
      body.cheque_payee = document.getElementById('payment-add-payee').value.trim();
      body.cheque_due_date = document.getElementById('payment-add-due').value.trim();
    }
    var enrollment = document.getElementById('payment-add-enrollment').value;
    fetch('/api/education/enrollments/' + encodeURIComponent(enrollment) + '/payments/', {
      method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(body)
    }).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) throw new Error(data.error || Object.keys(data).map(function (key) { return [].concat(data[key]).join('، '); }).join(' — ') || 'ثبت پرداخت انجام نشد.');
        return data;
      });
    }).then(function () {
      modal && modal.hide();
      toast('پرداخت با کد رهگیری جدید ثبت شد.', 'success');
      load(true);
    }).catch(function (err) {
      error.textContent = err.message;
      error.hidden = false;
    });
  });

  load(true);
  icons();
  window.penAttachJalaliPickers && window.penAttachJalaliPickers();
})();
