(function () {
  'use strict';

  var API = window.__LEADS_API__ || '/api/leads/';
  var appRoot = document.querySelector('[data-lead-app]');
  var teacherMode = Boolean(appRoot && appRoot.dataset.leadMode === 'teacher');
  var state = { rows: [], filter: 'all', assessors: [], page: 1, pageSize: 20, count: 0, request: 0, query: '', status: '' };
  var searchTimer = null;
  var modal = null;

  function esc(value) { return window.htmlEscape ? window.htmlEscape(value) : (value == null ? '' : String(value).replace(/[&<>"']/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[c]; })); }
  function headers() { return Object.assign({ 'Content-Type': 'application/json' }, window.penCsrfHeader ? window.penCsrfHeader() : {}); }
  function toast(message, kind) { if (window.penToast) window.penToast(message, kind); }
  function icons() { if (window.penRenderIcons) window.penRenderIcons(); }
  function get(url) { return fetch(url, { credentials: 'same-origin', headers: headers() }).then(function (r) { return r.json().then(function (b) { if (!r.ok) throw new Error(b.detail || 'خطا در دریافت اطلاعات'); return b; }); }); }
  function post(url, payload) { return fetch(url, { method: 'POST', credentials: 'same-origin', headers: headers(), body: JSON.stringify(payload || {}) }).then(function (r) { return r.json().then(function (b) { if (!r.ok) throw new Error(errorText(b)); return b; }); }); }
  function errorText(body) { return Object.keys(body || {}).map(function (k) { var v = body[k]; return Array.isArray(v) ? v.join('، ') : String(v); }).join(' — ') || 'عملیات انجام نشد.'; }
  function fmtDate(value) { if (!value) return 'تعیین نشده'; return String(value).replace(/-/g, '/'); }
  function fmtTime(value) { return value ? String(value).slice(0, 5) : ''; }
  function toAsciiDigits(value) { return String(value || '').replace(/[۰-۹٠-٩]/g, function (c) { return String('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩'.indexOf(c) % 10); }); }

  function statusClass(status) { return 'lead-status lead-status-' + status; }
  function card(row) {
    var date = row.assessment_date ? 'جلسه ' + fmtDate(row.assessment_date) + (row.assessment_time ? '، ' + fmtTime(row.assessment_time) : '') : 'جلسه تعیین نشده';
    return '<article class="lead-card" data-id="' + esc(row.id) + '" data-status="' + esc(row.status) + '">' +
      '<div class="lead-card-main"><div class="lead-avatar">' + esc((row.student_name || '؟').slice(0, 1)) + '</div><div class="min-w-0"><div class="d-flex align-items-center gap-2 flex-wrap"><strong class="lead-card-name">' + esc(row.student_name) + '</strong><span class="' + statusClass(row.status) + '">' + esc(row.status_label) + '</span></div><p class="lead-card-meta mb-0"><span dir="ltr">' + esc(row.phone) + '</span>' + (row.neighborhood ? ' · ' + esc(row.neighborhood) : '') + '</p><p class="lead-card-meta mb-0">' + esc(date) + '</p>' + (teacherMode ? '' : '<p class="lead-card-meta mb-0">ثبت‌کننده: ' + esc(row.created_by_name || '—') + '</p>') + '</div></div>' +
      '<div class="lead-card-side"><span class="lead-code">' + esc(row.code) + '</span><button type="button" class="btn btn-sm btn-outline-primary lead-open" data-id="' + esc(row.id) + '">مشاهده</button></div></article>';
  }

  function renderRows() {
    var list = document.getElementById('lead-list');
    if (!list) return;
    if (!teacherMode) {
      var rows = state.rows;
      list.innerHTML = rows.length ? rows.map(function (row) {
        var date = row.assessment_date ? fmtDate(row.assessment_date) + (row.assessment_time ? ' · ' + fmtTime(row.assessment_time) : '') : '—';
        return '<tr><td><strong class="lead-table-name">' + esc(row.student_name) + '</strong><small dir="ltr">' + esc(row.phone) + ' · ' + esc(row.code) + '</small></td><td>' + esc(date) + '</td><td>' + esc(row.assessor_name || '—') + '</td><td><span class="' + statusClass(row.status === 'scheduled' ? 'sent' : row.status) + '">' + esc(row.status_label) + '</span></td><td>' + esc(row.created_by_name || '—') + '</td><td><button type="button" class="btn btn-sm btn-outline-primary lead-open" data-id="' + esc(row.id) + '">جزئیات</button></td></tr>';
      }).join('') : '<tr><td colspan="6" class="lead-table-message"><strong>' + (state.query || state.status ? 'نتیجه‌ای پیدا نشد' : 'هنوز لیدی ثبت نشده') + '</strong><span>' + (state.query || state.status ? 'عبارت جست‌وجو یا فیلتر وضعیت را تغییر دهید.' : 'با ثبت لید جدید، پیگیری آن را از همین فهرست انجام دهید.') + '</span></td></tr>';
      var start = state.count ? (state.page - 1) * state.pageSize + 1 : 0;
      var end = Math.min(state.page * state.pageSize, state.count);
      var pages = Math.max(1, Math.ceil(state.count / state.pageSize));
      var summary = document.getElementById('lead-result-summary');
      if (summary) summary.textContent = state.count ? 'نمایش ' + start.toLocaleString('fa-IR') + ' تا ' + end.toLocaleString('fa-IR') + ' از ' + state.count.toLocaleString('fa-IR') + ' لید' : '۰ لید';
      var pageSummary = document.getElementById('lead-page-summary');
      if (pageSummary) pageSummary.textContent = state.count ? state.count.toLocaleString('fa-IR') + ' مورد' : 'بدون نتیجه';
      var indicator = document.getElementById('lead-page-indicator');
      if (indicator) indicator.textContent = 'صفحهٔ ' + state.page.toLocaleString('fa-IR') + ' از ' + pages.toLocaleString('fa-IR');
      var prev = document.getElementById('lead-prev'), next = document.getElementById('lead-next');
      if (prev) prev.disabled = state.page <= 1;
      if (next) next.disabled = state.page >= pages;
    } else {
      var filtered = state.rows.filter(function (row) {
        if (state.filter === 'all') return true;
        if (state.filter === 'pending') return row.status === 'sent' || row.status === 'scheduled';
        if (state.filter === 'completed') return row.status === 'assessed' || row.status === 'recommended' || row.status === 'enrolled';
        return row.status === state.filter;
      });
      list.innerHTML = filtered.length ? filtered.map(card).join('') : '<div class="lead-empty"><i data-lucide="clipboard-check" aria-hidden="true"></i><strong>تعیین‌سطحی در این فیلتر نیست</strong><span>لیدهای تخصیص‌یافته پس از ارسال کارمند در این صف دیده می‌شوند.</span></div>';
    }
    icons();
    list.querySelectorAll('.lead-open').forEach(function (button) { button.addEventListener('click', function () { openDetail(button.dataset.id); }); });
  }

  function loadRows() {
    var list = document.getElementById('lead-list');
    if (!list) return Promise.resolve();
    list.setAttribute('aria-busy', 'true');
    var request = ++state.request;
    if (teacherMode) return get(API).then(function (data) { state.rows = data.results || data || []; renderRows(); }).finally(function () { list.setAttribute('aria-busy', 'false'); });
    var params = new URLSearchParams({ page: String(state.page), page_size: String(state.pageSize) });
    if (state.query) params.set('q', state.query);
    if (state.status) params.set('status', state.status);
    return get(API + '?' + params.toString()).then(function (data) {
      if (request !== state.request) return;
      state.rows = data.results || []; state.count = data.count || 0; renderRows();
    }).finally(function () { if (request === state.request) list.setAttribute('aria-busy', 'false'); });
  }

  function loadAssessors() {
    return get(API + 'assessors/').then(function (data) { state.assessors = data.results || []; });
  }

  function showModal() {
    var el = document.getElementById('lead-detail-modal');
    if (window.bootstrap && window.bootstrap.Modal) { modal = modal || new bootstrap.Modal(el); modal.show(); }
  }

  function actionButton(label, action, cls) { return '<button type="button" class="btn ' + (cls || 'btn-outline-primary') + ' lead-action" data-action="' + action + '">' + label + '</button>'; }

  function openDetail(id) {
    get(API + id + '/').then(function (lead) {
      var body = document.getElementById('lead-detail-body');
      document.getElementById('lead-detail-title').textContent = lead.student_name || 'جزئیات لید';
      document.getElementById('lead-detail-code').textContent = lead.code || '';
      body.innerHTML =
        '<div class="lead-detail-grid"><div><span>وضعیت</span><strong><span class="' + statusClass(lead.status) + '">' + esc(lead.status_label) + '</span></strong></div><div><span>شماره تماس</span><strong dir="ltr">' + esc(lead.phone) + '</strong></div><div><span>سن</span><strong>' + esc(lead.age || '—') + '</strong></div><div><span>محله</span><strong>' + esc(lead.neighborhood || '—') + '</strong></div><div><span>جلسه</span><strong>' + esc(fmtDate(lead.assessment_date) + (lead.assessment_time ? ' · ' + fmtTime(lead.assessment_time) : '')) + '</strong></div><div><span>استاد / مسئول</span><strong>' + esc(lead.assessor_name || 'تعیین نشده') + '</strong></div>' + (teacherMode ? '' : '<div><span>ثبت‌کننده</span><strong>' + esc(lead.created_by_name || '—') + '</strong></div>') + '</div>' +
        '<div class="lead-detail-note"><span>حساسیت یا آلرژی</span><p>' + esc(lead.allergy_notes || 'موردی ثبت نشده') + '</p></div>' +
        (lead.assessment_result ? '<div class="lead-detail-note"><span>نتیجه تعیین سطح' + (lead.assessment_score != null ? ' · امتیاز ' + esc(lead.assessment_score) : '') + '</span><p>' + esc(lead.assessment_result) + '</p></div>' : '') +
        (lead.course_title ? '<div class="lead-detail-note"><span>پیشنهاد آموزشی</span><p>' + esc(lead.course_title) + (lead.lesson_title ? ' · ' + esc(lead.lesson_title) : '') + (lead.recommendation ? '<br>' + esc(lead.recommendation) : '') + '</p></div>' : '') +
        '<div class="lead-detail-actions" data-lead-id="' + esc(lead.id) + '">' + actionMarkup(lead) + '</div>';
      body.querySelectorAll('.lead-action').forEach(function (button) { button.addEventListener('click', function () { runAction(lead, button.dataset.action); }); });
      icons(); showModal();
    }).catch(function (e) { toast(e.message, 'danger'); });
  }

  function actionMarkup(lead) {
    if (teacherMode) return lead.status === 'sent' || lead.status === 'scheduled' ? actionButton('ثبت نتیجه تعیین سطح', 'assess', 'btn-primary') : '';
    if (lead.status === 'new' || lead.status === 'scheduled') return actionButton('ارسال برای استاد', 'send', 'btn-primary') + actionButton('حذف تعیین سطح', 'delete', 'btn-outline-danger') + actionButton('بایگانی', 'archive', 'btn-light');
    if (lead.status === 'sent') return actionButton('ثبت نتیجه تعیین سطح', 'assess', 'btn-primary') + actionButton('حذف تعیین سطح', 'delete', 'btn-outline-danger') + actionButton('بایگانی', 'archive', 'btn-light');
    if (lead.status === 'lost') return actionButton('حذف تعیین سطح', 'delete', 'btn-outline-danger');
    if (lead.status === 'assessed') return actionButton('معرفی دوره', 'recommend', 'btn-primary');
    if (lead.status === 'recommended') return actionButton('ادامه ثبت‌نام', 'enroll', 'btn-primary');
    return '';
  }

  function runAction(lead, action) {
    var body = document.getElementById('lead-detail-body');
    if (action === 'send') {
      var options = state.assessors.map(function (a) { return '<option value="' + esc(a.id) + '"' + (String(a.id) === String(lead.assessor) ? ' selected' : '') + '>' + esc(a.name) + ' · ' + esc(a.type) + '</option>'; }).join('');
      body.querySelector('.lead-detail-actions').innerHTML = '<div class="lead-inline-form"><label class="form-label">انتخاب استاد یا مسئول</label><select id="lead-action-assessor" class="form-select"><option value="">— انتخاب کنید —</option>' + options + '</select><button type="button" class="btn btn-primary" id="lead-action-save">ارسال</button></div>';
      document.getElementById('lead-action-save').addEventListener('click', function () { post(API + lead.id + '/send/', { assessor: document.getElementById('lead-action-assessor').value }).then(done).catch(fail); });
    } else if (action === 'assess') {
      body.querySelector('.lead-detail-actions').innerHTML = '<div class="lead-inline-form"><div class="row g-2"><div class="col-4"><label class="form-label" for="lead-action-score">امتیاز از ۱۰۰</label><input id="lead-action-score" class="form-control" type="number" min="0" max="100" dir="ltr" inputmode="numeric"></div><div class="col-8"><label class="form-label" for="lead-action-result">نتیجه و سطح پیشنهادی</label><textarea id="lead-action-result" class="form-control" rows="2" required aria-describedby="lead-action-result-help" placeholder="مثلاً سطح A2؛ نیاز به تمرین مکالمه دارد"></textarea><div id="lead-action-result-help" class="form-text">سطح، توانایی فعلی و نکتهٔ مهم برای ادامهٔ پیگیری را بنویسید.</div></div></div><button type="button" class="btn btn-primary" id="lead-action-save">ثبت نتیجه</button></div>';
      document.getElementById('lead-action-save').addEventListener('click', function () {
        var resultInput = document.getElementById('lead-action-result');
        var result = resultInput.value.trim();
        if (!result) {
          resultInput.setAttribute('aria-invalid', 'true');
          resultInput.focus();
          fail(new Error('ثبت توضیح نتیجه تعیین سطح الزامی است.'));
          return;
        }
        resultInput.removeAttribute('aria-invalid');
        post(API + lead.id + '/assess/', { score: document.getElementById('lead-action-score').value || null, result: result }).then(done).catch(fail);
      });
    } else if (action === 'recommend') {
      body.querySelector('.lead-detail-actions').innerHTML = '<div class="lead-inline-form"><div class="row g-2"><div class="col-6"><label class="form-label" for="lead-action-course">دوره پیشنهادی</label><select id="lead-action-course" class="form-select" required aria-describedby="lead-action-course-help"><option value="">— انتخاب دوره —</option></select><div id="lead-action-course-help" class="form-text" role="status" aria-live="polite">در حال دریافت دوره‌ها…</div></div><div class="col-6"><label class="form-label" for="lead-action-lesson">درس پیشنهادی</label><select id="lead-action-lesson" class="form-select" disabled aria-describedby="lead-action-lesson-help"><option value="">ابتدا دوره را انتخاب کنید</option></select><div id="lead-action-lesson-help" class="form-text" aria-live="polite">درس‌های همان دوره پس از انتخاب نمایش داده می‌شوند.</div></div><div class="col-12"><label class="form-label" for="lead-action-recommendation">توضیح معرفی</label><textarea id="lead-action-recommendation" class="form-control" rows="2"></textarea></div></div><button type="button" class="btn btn-primary" id="lead-action-save">ثبت معرفی دوره</button></div>';
      var courseSelect = document.getElementById('lead-action-course');
      var lessonSelect = document.getElementById('lead-action-lesson');
      var courseHelp = document.getElementById('lead-action-course-help');
      var lessonHelp = document.getElementById('lead-action-lesson-help');
      var saveRecommendation = document.getElementById('lead-action-save');
      var courses = [];
      courseSelect.disabled = true;
      saveRecommendation.disabled = true;
      courseSelect.addEventListener('change', function () {
        courseSelect.removeAttribute('aria-invalid');
        var selectedCourse = courses.find(function (course) { return String(course.id) === courseSelect.value; });
        var lessons = selectedCourse ? (selectedCourse.lesson_titles || []) : [];
        lessonSelect.innerHTML = '<option value="">' + (selectedCourse ? (lessons.length ? '— انتخاب درس (اختیاری) —' : 'برای این دوره درسی تعریف نشده') : 'ابتدا دوره را انتخاب کنید') + '</option>';
        lessons.forEach(function (lesson) {
          var option = document.createElement('option');
          option.value = lesson.id;
          option.textContent = lesson.title;
          lessonSelect.appendChild(option);
        });
        lessonSelect.disabled = !selectedCourse || !lessons.length;
        lessonHelp.textContent = selectedCourse
          ? (lessons.length ? 'فقط درس‌های دورهٔ انتخاب‌شده نمایش داده می‌شوند.' : 'برای این دوره درسی ثبت نشده است.')
          : 'درس‌های همان دوره پس از انتخاب نمایش داده می‌شوند.';
      });
      get('/api/education/courses/?page_size=100').then(function (data) {
        courses = data.results || [];
        courseSelect.innerHTML += courses.map(function (course) { return '<option value="' + esc(course.id) + '">' + esc(course.title) + '</option>'; }).join('');
        courseSelect.disabled = !courses.length;
        saveRecommendation.disabled = !courses.length;
        courseHelp.textContent = courses.length ? 'یک دوره را برای دیدن درس‌های مربوط انتخاب کنید.' : 'دوره‌ای برای انتخاب وجود ندارد.';
        if (!courses.length) lessonHelp.textContent = 'دوره‌ای برای انتخاب وجود ندارد.';
      }).catch(function (error) { courseHelp.textContent = 'دریافت دوره‌ها ناموفق بود.'; fail(error); });
      saveRecommendation.addEventListener('click', function () {
        if (!courseSelect.value) {
          courseSelect.setAttribute('aria-invalid', 'true');
          courseSelect.focus();
          fail(new Error('دوره را انتخاب کنید.'));
          return;
        }
        courseSelect.removeAttribute('aria-invalid');
        post(API + lead.id + '/recommend/', { course: courseSelect.value, lesson: lessonSelect.value || null, recommendation: document.getElementById('lead-action-recommendation').value.trim() }).then(done).catch(fail);
      });
    } else if (action === 'delete') {
      window.penOpenDeleteModal({
        url: API + lead.id + '/delete/',
        message: 'مورد تعیین سطح «' + (lead.student_name || '') + '» حذف شود؟',
        successMessage: 'مورد تعیین سطح حذف شد.',
        onSuccess: function () { if (modal) modal.hide(); window.location.reload(); }
      });
    } else if (action === 'enroll') {
      window.location.href = '/workspace/enrollments/?lead=' + encodeURIComponent(lead.id);
    } else if (action === 'archive') post(API + lead.id + '/archive/', {}).then(done).catch(fail);
  }

  function done() { toast('لید به‌روزرسانی شد.', 'success'); if (modal) modal.hide(); loadRows(); window.location.reload(); }
  function fail(error) { toast(error.message || 'عملیات انجام نشد.', 'danger'); }

  var form = document.getElementById('lead-form');
  if (form) {
    if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
    var dateInput = document.getElementById('lead-date');
    var timeInput = document.getElementById('lead-time');
    var phoneInput = document.getElementById('lead-phone');
    var calendarButton = document.getElementById('lead-calendar-open');

    if (calendarButton && dateInput) calendarButton.addEventListener('click', function () {
      dateInput.focus();
      if (window.jalaliDatepicker) window.jalaliDatepicker.show(dateInput);
    });

    document.querySelectorAll('[data-date-offset]').forEach(function (button) {
      button.addEventListener('click', function () {
        var day = new Date(form.dataset.todayIso + 'T12:00:00');
        day.setHours(12, 0, 0, 0);
        day.setDate(day.getDate() + Number(button.dataset.dateOffset || 0));
        dateInput.value = window.penISOToJalali ? window.penISOToJalali(day) : '';
        dateInput.dispatchEvent(new Event('change', { bubbles: true }));
        dateInput.classList.remove('is-invalid');
        syncTodayTimeLimit();
      });
    });

    function syncTodayTimeLimit() {
      var iso = window.penJalaliToISO ? window.penJalaliToISO(dateInput.value) : '';
      if (iso === form.dataset.todayIso) {
        timeInput.min = form.dataset.todayMinTime || '';
      } else {
        timeInput.removeAttribute('min');
      }
    }
    dateInput.addEventListener('change', function () { dateInput.classList.remove('is-invalid'); syncTodayTimeLimit(); });
    dateInput.addEventListener('input', function () { dateInput.classList.remove('is-invalid'); });
    phoneInput.addEventListener('input', function () {
      phoneInput.value = toAsciiDigits(phoneInput.value).replace(/[^0-9]/g, '').slice(0, 11);
      phoneInput.classList.remove('is-invalid');
    });

    var courseInput = document.getElementById('lead-course');
    var lessonInput = document.getElementById('lead-lesson');
    courseInput.addEventListener('change', function () {
      lessonInput.disabled = true;
      lessonInput.innerHTML = '<option value="">' + (courseInput.value ? 'در حال دریافت درس‌ها…' : 'ابتدا دوره را انتخاب کنید') + '</option>';
      if (!courseInput.value) return;
      get('/api/education/courses/' + encodeURIComponent(courseInput.value) + '/').then(function (course) {
        var lessons = course.lesson_titles || [];
        lessonInput.innerHTML = '<option value="">— انتخاب درس (اختیاری) —</option>' + lessons.map(function (lesson) {
          return '<option value="' + esc(lesson.id) + '">' + esc(lesson.title) + '</option>';
        }).join('');
        if (!lessons.length) lessonInput.innerHTML = '<option value="">برای این دوره درسی تعریف نشده</option>';
        lessonInput.disabled = !lessons.length;
      }).catch(function () {
        lessonInput.innerHTML = '<option value="">دریافت درس‌ها ناموفق بود</option>';
        lessonInput.disabled = true;
      });
    });

    form.addEventListener('submit', function (event) {
    event.preventDefault();
    var errors = document.getElementById('lead-form-errors');
    var required = form.querySelectorAll('[required]');
    var missing = [];
    required.forEach(function (input) {
      var value = String(input.value || '').trim();
      var invalid = !value || (input === phoneInput && !/^09\d{9}$/.test(toAsciiDigits(value)));
      if (input === dateInput && value && !(window.penJalaliToISO && window.penJalaliToISO(value))) invalid = true;
      if (input === dateInput && value) {
        var isoDate = window.penJalaliToISO(value);
        if (isoDate && isoDate < form.dataset.todayIso) invalid = true;
      }
      if (input === timeInput && value && input.min && value < input.min) invalid = true;
      input.classList.toggle('is-invalid', invalid);
      input.setAttribute('aria-invalid', invalid ? 'true' : 'false');
      if (invalid) missing.push(input === dateInput && value ? 'تاریخ جلسه باید معتبر و امروز یا آینده باشد' : input === timeInput && value ? 'ساعت جلسه را بعد از زمان فعلی انتخاب کنید' : input === phoneInput && value ? 'شماره تماس باید با ۰۹ شروع شود و ۱۱ رقم باشد' : (input.labels && input.labels[0] ? input.labels[0].textContent.replace('*', '').trim() : 'فیلد'));
    });
    if (missing.length) { errors.querySelector('ul').innerHTML = '<li>این موارد را تکمیل کنید: ' + esc(missing.join('، ')) + '</li>'; errors.hidden = false; return; }
    errors.hidden = true;
    var date = document.getElementById('lead-date').value.trim();
    var iso = window.penJalaliToISO ? window.penJalaliToISO(date) : null;
    var submit = form.querySelector('[type="submit"]');
    submit.disabled = true;
    post(API, { student_name: document.getElementById('lead-student-name').value.trim(), age: Number(document.getElementById('lead-age').value), phone: toAsciiDigits(phoneInput.value), neighborhood: document.getElementById('lead-neighborhood').value.trim(), father_job: document.getElementById('lead-father-job').value.trim(), mother_job: document.getElementById('lead-mother-job').value.trim(), allergy_notes: document.getElementById('lead-allergy').value.trim(), assessment_date: iso, assessment_time: timeInput.value, assessor: document.getElementById('lead-assessor').value, course: courseInput.value || null, lesson: lessonInput.value || null })
      .then(function () { toast('لید ثبت و برای استاد ارسال شد.', 'success'); window.location.reload(); })
      .catch(function (e) { errors.querySelector('ul').innerHTML = '<li>' + esc(e.message) + '</li>'; errors.hidden = false; })
      .finally(function () { submit.disabled = false; });
    });
  }

  document.querySelectorAll('.lead-filters button').forEach(function (button) { button.addEventListener('click', function () { document.querySelectorAll('.lead-filters button').forEach(function (b) { b.classList.remove('is-active'); b.setAttribute('aria-pressed', 'false'); }); button.classList.add('is-active'); button.setAttribute('aria-pressed', 'true'); state.filter = button.dataset.filter; renderRows(); }); });
  var searchInput = document.getElementById('lead-search');
  var statusInput = document.getElementById('lead-status-filter');
  var sizeInput = document.getElementById('lead-page-size');
  if (searchInput) searchInput.addEventListener('input', function () { clearTimeout(searchTimer); searchTimer = setTimeout(function () { state.query = searchInput.value.trim(); state.page = 1; loadRows().catch(function (e) { toast(e.message, 'danger'); }); }, 300); });
  if (statusInput) statusInput.addEventListener('change', function () { state.status = statusInput.value; state.page = 1; loadRows().catch(function (e) { toast(e.message, 'danger'); }); });
  if (sizeInput) sizeInput.addEventListener('change', function () { state.pageSize = Number(sizeInput.value) || 20; state.page = 1; loadRows().catch(function (e) { toast(e.message, 'danger'); }); });
  var prevButton = document.getElementById('lead-prev'), nextButton = document.getElementById('lead-next');
  if (prevButton) prevButton.addEventListener('click', function () { if (state.page > 1) { state.page--; loadRows().catch(function (e) { toast(e.message, 'danger'); }); } });
  if (nextButton) nextButton.addEventListener('click', function () { if (state.page * state.pageSize < state.count) { state.page++; loadRows().catch(function (e) { toast(e.message, 'danger'); }); } });
  function refreshRows() {
    return loadRows().then(function () { return form ? loadAssessors() : null; });
  }
  document.getElementById('lead-refresh') && document.getElementById('lead-refresh').addEventListener('click', function () { refreshRows().then(function () { toast('صف به‌روز شد.', 'success'); }).catch(function (e) { toast(e.message, 'danger'); }); });
  refreshRows().catch(function (e) { toast(e.message, 'danger'); });
}());
