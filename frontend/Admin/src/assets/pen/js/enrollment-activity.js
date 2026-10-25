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

  function dateTime(value) {
    if (!value) return '';
    var date = new Date(value);
    return isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('fa-IR', {dateStyle: 'short', timeStyle: 'short'}).format(date);
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
      var methods = { cash: 'نقدی', pos: 'کارت‌خوان', cheque: 'چک', card_transfer: 'کارت‌به‌کارت', split: 'ترکیبی', mixed: 'ترکیبی' };
      box.innerHTML = rows.map(function (row) {
        var payment = row.is_free ? 'رایگان' : number(row.final_amount) + ' تومان';
        var method = row.is_free ? '' : ' · ' + (methods[row.payment_method] || row.payment_method || '');
        return '<article class="registration-activity-item"><div class="d-flex flex-wrap align-items-center gap-2">' +
          '<strong class="fs-14">' + escape(row.student_name || 'دانش‌آموز') + '</strong>' +
          '<span class="badge bg-primary-subtle text-primary">' + payment + '</span></div>' +
          '<div class="fs-13 text-muted mt-1">' + escape(row.offering_title || 'برگزاری مشخص نشده') + method +
          (row.enrolled_at ? ' · ' + escape(row.enrolled_at) : '') + '</div></article>';
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
        return '<article class="registration-activity-item"><div class="d-flex flex-wrap align-items-center gap-2">' +
          '<strong class="fs-14">' + escape(row.student_name || 'دانش‌آموز') + '</strong>' +
          '<span class="badge bg-warning-subtle text-warning">جایگاه ' + number(row.position) + '</span></div>' +
          '<div class="fs-13 text-muted mt-1">' + escape(row.offering_title || 'برگزاری مشخص نشده') +
          (row.requested_at ? ' · درخواست ' + escape(dateTime(row.requested_at)) : '') + '</div></article>';
      }).join('');
    }).catch(function (error) {
      box.innerHTML = '<div class="pen-empty py-4">' + escape(error.message) + '</div>';
    }).finally(function () {
      box.removeAttribute('aria-busy');
    });
  }

  function setupActivityTabs() {
    var tabs = Array.from(document.querySelectorAll('[data-activity-tab]'));
    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () { activate(tab); });
      tab.addEventListener('keydown', function (event) {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        var next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 :
          (index + (event.key === 'ArrowLeft' ? 1 : -1) + tabs.length) % tabs.length;
        tabs[next].focus();
        activate(tabs[next]);
      });
    });
    function activate(tab) {
      tabs.forEach(function (item) {
        var selected = item === tab;
        item.classList.toggle('active', selected);
        item.setAttribute('aria-selected', selected ? 'true' : 'false');
        item.tabIndex = selected ? 0 : -1;
        var panel = document.getElementById(item.getAttribute('aria-controls'));
        if (panel) panel.hidden = !selected;
      });
    }
  }

  setupActivityTabs();
  renderRecent();
  renderWaitlist();
}());
