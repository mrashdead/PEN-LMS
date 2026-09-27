(function () {
  'use strict';

  function escape(value) {
    return window.htmlEscape ? window.htmlEscape(value) : String(value == null ? '' : value).replace(/[&<>"']/g, function (char) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char];
    });
  }

  function number(value) {
    var formatted = (Number(value) || 0).toLocaleString('en-US').replace(/,/g, '٬');
    return window.persianNumbers ? window.persianNumbers(formatted) : formatted;
  }

  function fetchList(url) {
    return fetch(url, {
      credentials: 'same-origin',
      headers: window.penCsrfHeader ? window.penCsrfHeader() : {}
    }).then(function (response) {
      return response.json().then(function (body) {
        if (!response.ok) throw new Error(body.detail || body.error || 'دریافت اطلاعات انجام نشد.');
        return body;
      });
    });
  }

  function renderRecent() {
    var box = document.getElementById('enr-recent');
    if (!box) return;
    box.setAttribute('aria-busy', 'true');
    fetchList('/api/education/enrollments/?page_size=15').then(function (data) {
      var rows = data.results || [];
      if (!rows.length) {
        box.innerHTML = '<div class="pen-empty py-4"><p class="mb-0 fs-14">هنوز ثبت‌نامی نیست.</p></div>';
        return;
      }
      var methods = { cash: 'نقدی', pos: 'کارت‌خوان', cheque: 'چک' };
      box.innerHTML = rows.map(function (row) {
        return '<div class="px-3 py-2 border-bottom"><div class="d-flex align-items-center gap-2"><strong class="fs-14">' +
          escape(row.student_name || '') + '</strong><span class="badge bg-primary-subtle text-primary ms-auto">' + number(row.final_amount) + ' ت</span></div>' +
          '<div class="fs-13 text-muted">' + escape(row.offering_title || '') + ' · ' + escape(methods[row.payment_method] || row.payment_method || '') +
          (row.discount_type && row.discount_type !== 'none' ? ' · تخفیف ' + escape(row.discount_value) + (row.discount_type === 'percent' ? '٪' : 'ت') : '') +
          ' · ' + escape(row.enrolled_at || '') + '</div></div>';
      }).join('');
    }).catch(function (error) {
      box.innerHTML = '<div class="pen-empty py-4">' + escape(error.message) + '</div>';
    }).finally(function () {
      box.removeAttribute('aria-busy');
      if (window.penRenderIcons) window.penRenderIcons();
    });
  }

  function renderWaitlist() {
    var box = document.getElementById('enr-waitlist');
    if (!box) return;
    box.setAttribute('aria-busy', 'true');
    fetchList('/api/education/waitlist/?page_size=15&status=waiting').then(function (data) {
      var rows = data.results || [];
      if (!rows.length) {
        box.innerHTML = '<div class="pen-empty py-4"><p class="mb-0 fs-14">صف انتظاری ثبت نشده است.</p></div>';
        return;
      }
      box.innerHTML = rows.map(function (row) {
        return '<div class="px-3 py-2 border-bottom"><div class="d-flex align-items-center gap-2"><strong class="fs-14">' +
          escape(row.student_name || '') + '</strong><span class="badge bg-warning-subtle text-warning ms-auto">نفر ' + number(row.position) + '</span></div>' +
          '<div class="fs-13 text-muted">' + escape(row.offering_title || '') + ' · درخواست ' + escape(row.requested_at || '') + '</div></div>';
      }).join('');
    }).catch(function (error) {
      box.innerHTML = '<div class="pen-empty py-4">' + escape(error.message) + '</div>';
    }).finally(function () {
      box.removeAttribute('aria-busy');
    });
  }

  renderRecent();
  renderWaitlist();
}());
