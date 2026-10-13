(function () {
  'use strict';
  var API = window.__PLAYHOUSE_API__ || '/api/playhouse/';
  var list = document.getElementById('ph-kitchen-orders');
  if (!list) return;
  var known = new Set();
  var lastReady = new Set();
  var hasLoaded = false;
  var renderedRows = null;
  function esc(s) { return window.htmlEscape ? window.htmlEscape(s) : String(s || ''); }
  function fmt(n) { return window.persianNumbers((Number(n) || 0).toLocaleString('en-US')) + ' تومان'; }
  function statusText(s) { return { new: 'جدید', preparing: 'در حال آماده‌سازی', ready: 'آماده', cancelled: 'لغو شده' }[s] || s; }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function render(rows) {
    var visible = rows.filter(function (o) { return o.status !== 'cancelled'; });
    // Polling an unchanged queue should preserve focus and the existing cards.
    var nextRows = JSON.stringify(visible);
    if (nextRows === renderedRows) return;
    renderedRows = nextRows;
    if (!visible.length) { list.innerHTML = '<div class="col-12"><div class="ph-kitchen-empty">سفارشی در صف نیست.</div></div>'; hasLoaded = true; return; }
    list.innerHTML = visible.map(function (o) {
      var isNew = !known.has(o.id);
      var becameReady = hasLoaded && o.status === 'ready' && !lastReady.has(o.id);
      if (isNew) known.add(o.id);
      if (o.status === 'ready') lastReady.add(o.id);
      if (hasLoaded && isNew && window.Notification && Notification.permission === 'granted') new Notification('سفارش جدید کافه', { body: o.member_name + ' · ' + o.items.map(function (i) { return i.name + ' × ' + i.quantity; }).join('، ') });
      if (becameReady) {
        window.penToast && window.penToast('سفارش ' + o.member_name + ' آماده شد.', 'success');
        if (window.Notification && Notification.permission === 'granted') new Notification('سفارش آماده است', { body: o.member_name + ' · آماده تحویل به کانتر' });
      }
      var badgeTone = o.status === 'ready' ? 'success' : (o.status === 'new' ? 'danger' : 'warning');
      return '<article class="col-12 col-md-6 col-xl-4"><section class="ph-kitchen-order ph-kitchen-' + esc(o.status) + '">' +
        '<header class="d-flex justify-content-between align-items-start gap-2"><div><div class="small text-muted">مراجعه‌کننده</div><h2 class="h5 mb-1">' + esc(o.member_name) + '</h2><small dir="ltr">' + esc(o.temporary_id || 'شناسه مراجعه') + '</small></div><span class="badge bg-' + badgeTone + '-subtle text-body">' + statusText(o.status) + '</span></header>' +
        '<div class="ph-kitchen-items">' + o.items.map(function (i) { return '<div class="ph-kitchen-item"><span><b>' + esc(i.quantity) + '×</b> ' + esc(i.name) + (i.note ? '<small class="d-block text-muted">' + esc(i.note) + '</small>' : '') + '</span><strong>' + fmt(i.line_total) + '</strong></div>'; }).join('') + '</div>' +
        (o.kitchen_note ? '<div class="alert alert-warning py-2 px-3 small mb-2">' + esc(o.kitchen_note) + '</div>' : '') +
        '<footer class="d-flex justify-content-between align-items-center"><small>ثبت ' + new Date(o.created_at).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' }) + ' · ' + esc(o.created_by_name) + '</small>' + (o.status === 'ready' ? '<span class="ph-kitchen-handoff fw-bold">تحویل به کانتر</span>' : '<button class="btn btn-sm btn-primary" data-ready="' + esc(o.id) + '">آماده است</button>') + '</footer>' +
        '</section></article>';
    }).join('');
    hasLoaded = true;
  }
  function load() {
    fetch(API + 'kitchen/orders/', { credentials: 'same-origin' }).then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.detail || 'خطا در دریافت سفارش‌ها'); return d; }); })
      .then(function (d) { document.getElementById('ph-kitchen-error').hidden = true; render(d); })
      .catch(function (e) { var err = document.getElementById('ph-kitchen-error'); err.textContent = e.message; err.hidden = false; });
  }
  list.addEventListener('click', function (e) {
    var button = e.target.closest('[data-ready]');
    if (!button) return;
    button.disabled = true;
    fetch(API + 'kitchen/orders/' + encodeURIComponent(button.dataset.ready) + '/status/', { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify({ status: 'ready' }) })
      .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.detail || 'ثبت وضعیت ناموفق بود'); return d; }); })
      .then(load).catch(function (e) { button.disabled = false; var err = document.getElementById('ph-kitchen-error'); err.textContent = e.message; err.hidden = false; });
  });
  document.getElementById('ph-kitchen-refresh').addEventListener('click', load);
  document.getElementById('ph-kitchen-notify').addEventListener('click', function () {
    if (!window.Notification) { window.penToast && window.penToast('اعلان مرورگر پشتیبانی نمی‌شود؛ پنل زنده همچنان هر ۴ ثانیه بروزرسانی می‌شود.', 'warning'); return; }
    Notification.requestPermission().then(function (permission) { window.penToast && window.penToast(permission === 'granted' ? 'اعلان سفارش فعال شد.' : 'اعلان مرورگر فعال نشد؛ صف همچنان خودکار بروز می‌شود.', permission === 'granted' ? 'success' : 'warning'); });
  });
  load(); window.setInterval(load, 4000);
})();
