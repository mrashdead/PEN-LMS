(function () {
  'use strict';
  var API = window.__PLAYHOUSE_API__ || '/api/playhouse/';
  var modalEl = document.getElementById('ph-cafe-order-modal');
  if (!modalEl) return;
  var itemsEl = document.getElementById('ph-cafe-order-items');
  var paymentsEl = document.getElementById('ph-cafe-payments');
  var presets = [];
  var fmt = function (n) { return window.persianNumbers((Number(n) || 0).toLocaleString('en-US')) + ' تومان'; };
  var digits = function (v) { return String(v || '').replace(/[۰-۹]/g, function (d) { return String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)); }).replace(/[٠-٩]/g, function (d) { return String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)); }).replace(/\D/g, ''); };
  var amount = function (v) { return Number(digits(v)) || 0; };
  function row(name, price, quantity) {
    var div = document.createElement('div');
    div.className = 'row g-2 align-items-center ph-order-item-row';
    div.innerHTML = '<div class="col-5"><input class="form-control" data-item-name maxlength="200" aria-label="نام آیتم" placeholder="نام آیتم"></div>' +
      '<div class="col-2"><input class="form-control" data-item-quantity type="number" min="1" max="99" value="1" aria-label="تعداد"></div>' +
      '<div class="col-4"><input class="form-control" data-item-price inputmode="numeric" dir="ltr" aria-label="قیمت واحد" placeholder="قیمت"></div>' +
      '<div class="col-1"><button class="btn btn-sm btn-light" type="button" data-remove-item aria-label="حذف آیتم">×</button></div>';
    div.querySelector('[data-item-name]').value = name || '';
    div.querySelector('[data-item-price]').value = price ? Number(price).toLocaleString('en-US') : '';
    div.querySelector('[data-item-quantity]').value = quantity || 1;
    div.addEventListener('input', total);
    div.querySelector('[data-remove-item]').addEventListener('click', function () { div.remove(); if (!itemsEl.children.length) row(); total(); });
    itemsEl.appendChild(div);
    return div;
  }
  function paymentRow() {
    var div = document.createElement('div');
    div.className = 'row g-2 align-items-center ph-order-payment-row';
    div.innerHTML = '<div class="col-4"><select class="form-select" data-pay-method aria-label="روش پرداخت"><option value="cash">نقدی</option><option value="pos">کارت‌خوان</option><option value="card_transfer">کارت‌به‌کارت</option></select></div>' +
      '<div class="col-3"><input class="form-control" data-pay-amount inputmode="numeric" dir="ltr" placeholder="مبلغ" aria-label="مبلغ پرداخت"></div>' +
      '<div class="col-4"><input class="form-control" data-pay-tracking dir="ltr" placeholder="کد رهگیری" aria-label="کد رهگیری"></div>' +
      '<div class="col-1"><button class="btn btn-sm btn-light" type="button" data-remove-pay aria-label="حذف پرداخت">×</button></div>';
    div.querySelector('[data-pay-method]').addEventListener('change', function () { div.querySelector('[data-pay-tracking]').required = this.value === 'card_transfer'; });
    div.querySelector('[data-pay-amount]').addEventListener('input', paymentSummary);
    div.querySelector('[data-remove-pay]').addEventListener('click', function () { div.remove(); paymentSummary(); });
    paymentsEl.appendChild(div);
  }
  function itemsData() {
    return Array.prototype.slice.call(itemsEl.querySelectorAll('.ph-order-item-row')).map(function (el) {
      var name = el.querySelector('[data-item-name]').value.trim();
      var unit = amount(el.querySelector('[data-item-price]').value);
      var quantity = Number(el.querySelector('[data-item-quantity]').value) || 1;
      if (!name && !unit) return null;
      return { name: name, unit_price: unit, quantity: quantity };
    }).filter(Boolean);
  }
  function total() {
    var sum = itemsData().reduce(function (n, item) { return n + item.unit_price * item.quantity; }, 0);
    document.getElementById('ph-cafe-order-total').textContent = fmt(sum);
    paymentSummary();
    return sum;
  }
  function paymentSummary() {
    var paid = Array.prototype.slice.call(paymentsEl.querySelectorAll('[data-pay-amount]')).reduce(function (n, el) { return n + amount(el.value); }, 0);
    var sum = itemsData().reduce(function (n, item) { return n + item.unit_price * item.quantity; }, 0);
    document.getElementById('ph-cafe-payment-summary').textContent = 'پرداخت واردشده: ' + fmt(paid) + ' · مانده سفارش: ' + fmt(Math.max(0, sum - paid));
  }
  function open(tr) {
    var modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    document.getElementById('ph-cafe-order-session').value = tr.getAttribute('data-id');
    document.getElementById('ph-cafe-order-visitor').textContent = tr.querySelector('.ph-child-name').textContent + ' · شناسه ' + (tr.getAttribute('data-national-code') || tr.getAttribute('data-temporary-id') || 'ثبت نشده');
    document.getElementById('ph-cafe-order-note').value = '';
    document.getElementById('ph-cafe-order-error').hidden = true;
    itemsEl.innerHTML = ''; row(); paymentsEl.innerHTML = '';
    document.getElementById('ph-cafe-order-submit').disabled = false;
    total();
    modal.show();
  }
  window.openPlayhouseCafeOrder = open;
  document.getElementById('ph-cafe-order-add-row').addEventListener('click', function () { row(); });
  document.getElementById('ph-cafe-payment-add').addEventListener('click', paymentRow);
  document.getElementById('ph-cafe-order-add-preset').addEventListener('click', function () {
    var id = document.getElementById('ph-cafe-order-preset').value;
    var item = presets.find(function (p) { return String(p.id) === id; });
    if (item) row(item.name, item.price, 1);
    total();
  });
  fetch(API + 'cafe-presets/', { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (rows) {
    presets = rows || [];
    var select = document.getElementById('ph-cafe-order-preset');
    presets.forEach(function (p) { var opt = document.createElement('option'); opt.value = p.id; opt.textContent = p.name + ' · ' + fmt(p.price); select.appendChild(opt); });
  }).catch(function () {});
  document.getElementById('ph-cafe-order-submit').addEventListener('click', function () {
    var button = this;
    var error = document.getElementById('ph-cafe-order-error');
    var session = document.getElementById('ph-cafe-order-session').value;
    var items = itemsData();
    var incomplete = Array.prototype.slice.call(itemsEl.querySelectorAll('.ph-order-item-row')).some(function (el) {
      var name = el.querySelector('[data-item-name]').value.trim();
      var price = el.querySelector('[data-item-price]').value.trim();
      var quantity = Number(el.querySelector('[data-item-quantity]').value);
      return (name || price) && (!name || !price || !Number.isInteger(quantity) || quantity < 1 || quantity > 99);
    });
    var payments = Array.prototype.slice.call(paymentsEl.querySelectorAll('.ph-order-payment-row')).map(function (el) {
      return { method: el.querySelector('[data-pay-method]').value, amount: amount(el.querySelector('[data-pay-amount]').value), tracking_code: el.querySelector('[data-pay-tracking]').value.trim() };
    }).filter(function (p) { return p.amount > 0; });
    if (!items.length || incomplete || items.some(function (i) { return !i.name || i.unit_price < 0; })) { error.textContent = 'نام، تعداد و قیمت آیتم‌ها را کامل کنید.'; error.hidden = false; return; }
    if (payments.some(function (p) { return p.method === 'card_transfer' && !p.tracking_code; })) { error.textContent = 'برای کارت‌به‌کارت کد رهگیری وارد کنید.'; error.hidden = false; return; }
    if (payments.reduce(function (n, p) { return n + p.amount; }, 0) > total()) { error.textContent = 'جمع پرداخت از جمع سفارش بیشتر است.'; error.hidden = false; return; }
    button.disabled = true; error.hidden = true;
    fetch(API + 'sessions/' + session + '/cafe-orders/', {
      method: 'POST', credentials: 'same-origin',
      headers: Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}),
      body: JSON.stringify({ items: items, payments: payments, kitchen_note: document.getElementById('ph-cafe-order-note').value.trim() })
    }).then(function (r) { return r.json().then(function (data) { if (!r.ok) throw new Error(data.detail || JSON.stringify(data)); return data; }); }).then(function () {
      window.penToast && window.penToast('سفارش برای آشپزخانه ثبت شد.', 'success');
      window.dispatchEvent(new CustomEvent('ph-cafe-order-created'));
      window.bootstrap.Modal.getInstance(modalEl).hide();
    }).catch(function (e) { error.textContent = e.message; error.hidden = false; }).finally(function () { button.disabled = false; });
  });
})();
