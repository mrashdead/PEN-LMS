/* Period progress reports: teacher composition and learner reading. */
(() => {
  'use strict';
  const ALL_STUDENTS = '__all_students__';
  const teacher = document.getElementById('progress-teacher');
  const learner = document.getElementById('progress-learner');
  if (!teacher && !learner) return;
  const fields = ['period', 'period_start', 'period_end', 'start_time', 'end_time', 'title', 'summary', 'strengths', 'improvements', 'homework', 'next_steps'];
  const sections = {summary: 'شرح عملکرد و پیشرفت', strengths: 'نقاط قوت', improvements: 'موارد نیازمند تمرین', homework: 'تکالیف', next_steps: 'برنامهٔ ادامهٔ یادگیری'};
  const api = async (url, options = {}) => {
    const response = await fetch(url, {credentials: 'same-origin', ...options, headers: {
      'Content-Type': 'application/json', ...(window.penCsrfHeader ? window.penCsrfHeader() : {}), ...(options.headers || {}),
    }});
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const labels = {period_start: 'از تاریخ', period_end: 'تا تاریخ', start_time: 'ساعت شروع', end_time: 'ساعت پایان', summary: 'شرح عملکرد', title: 'عنوان', student: 'دانش‌آموز'};
      const errors = Object.entries(body).map(([key, value]) => `${labels[key] || ''} ${Array.isArray(value) ? value.join('، ') : value}`.trim());
      throw new Error(body.detail || body.error || errors.join('؛ ') || 'دریافت اطلاعات انجام نشد. دوباره تلاش کنید.');
    }
    return body;
  };
  const el = (tag, css, text) => {
    const node = document.createElement(tag);
    if (css) node.className = css;
    if (text != null) node.textContent = text;
    return node;
  };
  const message = (text, error = false) => {
    const node = document.getElementById(teacher ? 'progress-message' : 'progress-learner-message');
    node.textContent = text; node.hidden = !text;
    node.className = `alert ${error ? 'alert-danger' : 'alert-success'}`;
  };
  const card = (report, onEdit, onRead) => {
    const article = el('article', 'card progress-report');
    const body = el('div', 'card-body');
    const header = el('div', 'd-flex flex-wrap align-items-center gap-2 mb-2');
    header.append(el(teacher ? 'h4' : 'h3', 'h6 mb-0 flex-grow-1', report.title), el('span', 'badge bg-primary-subtle text-primary', report.period_display));
    if (report.is_class_report) header.append(el('span', 'badge bg-info-subtle text-info', 'گزارش کل کلاس'));
    let reportDates = `${report.period_start}${report.start_time ? ' ' + report.start_time.slice(0, 5) : ''} تا ${report.period_end}${report.end_time ? ' ' + report.end_time.slice(0, 5) : ''}`;
    if (report.period === 'daily' && report.period_start === report.period_end) {
      let label = `روزانه · ${report.period_start}`;
      if (teacher && window.penReportDates && teacher.dataset.systemDate === window.penReportDates.iso(report.period_start)) label = `امروز · ${report.period_start}`;
      reportDates = `${label}${report.start_time ? ' · ' + report.start_time.slice(0, 5) : ''}${report.end_time ? ' تا ' + report.end_time.slice(0, 5) : ''}`;
    }
    body.append(header, el('p', 'text-muted fs-13 mb-2', `${report.offering_name} · ${reportDates}`), el('p', 'text-muted fs-13 mb-3', `مدرس: ${report.author_name || 'نامشخص'}`));
    const classAudienceStatus = teacher && report.is_class_report && Number.isFinite(report.recipient_count)
      ? `ارسال‌شده برای ${report.recipient_count.toLocaleString('fa-IR')} هنرجو · مشاهده‌شده توسط ${Number(report.read_count || 0).toLocaleString('fa-IR')} هنرجو`
      : null;
    const status = el('span', 'badge bg-secondary-subtle text-secondary mb-3', classAudienceStatus || (report.status === 'draft' ? 'پیش‌نویس' : report.read_at ? 'مشاهده‌شده توسط دانش‌آموز' : teacher ? 'ارسال‌شده؛ هنوز مشاهده نشده' : 'جدید'));
    body.append(status);
    const details = el('details', 'progress-report-details');
    if (teacher) details.open = true;
    details.append(el('summary', '', 'مطالعهٔ گزارش کامل'));
    Object.entries(sections).forEach(([field, label]) => {
      if (!report[field]) return;
      const section = el('section', 'mt-3');
      const text = el('div', 'progress-report-text', report[field]); text.dir = 'auto';
      section.append(el(teacher ? 'h5' : 'h4', 'h6', label), text); details.append(section);
    });
    if (onRead && !report.read_at) {
      let marking = false;
      details.addEventListener('toggle', async () => {
        if (!details.open || marking || report.read_at) return;
        marking = true;
        try { report.read_at = (await onRead(report)).read_at; if (report.read_at) status.textContent = 'مشاهده‌شده'; }
        catch (error) { message(error.message, true); }
        finally { marking = false; }
      });
    }
    body.append(details);
    if (onEdit && report.status === 'draft') {
      const edit = el('button', 'btn btn-sm btn-outline-primary mt-3', 'ویرایش و ارسال پیش‌نویس'); edit.type = 'button';
      edit.addEventListener('click', () => onEdit(report)); body.append(edit);
    }
    article.append(body); return article;
  };

  if (learner) {
    const history = document.getElementById('progress-learner-history');
    const filter = document.getElementById('progress-learner-filter');
    const startDate = document.getElementById('progress-learner-start');
    const endDate = document.getElementById('progress-learner-end');
    const dateReset = document.getElementById('progress-learner-date-reset');
    const more = document.getElementById('progress-learner-more');
    let student = '', next = null, version = 0;
    const load = async (append = false) => {
      const current = ++version, selected = student;
      const params = new URLSearchParams({student: selected, period: filter.value});
      const start = startDate.value.trim(), end = endDate.value.trim();
      if (Boolean(start) !== Boolean(end)) { message('برای فیلتر تاریخ، هر دو تاریخ شروع و پایان را وارد کنید.', true); return; }
      if (start && end) {
        const startIso = window.penJalaliToISO ? window.penJalaliToISO(start) : null;
        const endIso = window.penJalaliToISO ? window.penJalaliToISO(end) : null;
        if (!startIso || !endIso) { message('تاریخ را به شکل سال/ماه/روز وارد کنید.', true); return; }
        if (startIso > endIso) { message('تاریخ پایان باید برابر یا بعد از شروع باشد.', true); return; }
        params.set('start', start); params.set('end', end);
      }
      const url = append ? next : `/api/education/portal/progress-reports/?${params}`;
      if (!url) return;
      more.disabled = true;
      if (!append) history.replaceChildren(el('p', 'text-muted', 'در حال دریافت گزارش‌ها…'));
      try {
        const body = await api(url); if (current !== version) return;
        if (!append) history.replaceChildren();
        (Array.isArray(body) ? body : body.results || []).forEach(report => history.append(card(report, null,
          r => api(`/api/education/portal/progress-reports/${r.id}/read/`, {method: 'POST', body: JSON.stringify({student: selected})}))));
        if (!history.children.length) history.append(el('p', 'pen-empty', 'هنوز گزارشی با این نوع برای شما ارسال نشده است.'));
        next = body.next || null; more.hidden = !next;
      } catch (error) {
        if (current !== version) return;
        if (!append) history.replaceChildren(el('p', 'text-muted', 'گزارش‌ها دریافت نشدند. صفحه را تازه کنید.'));
        message(error.message, true);
      } finally { if (current === version) more.disabled = false; }
    };
    document.addEventListener('pen:learner-selected', event => {
      student = event.detail.student || ''; version++; next = null; more.hidden = true; message('');
      if (student) load();
      else history.replaceChildren(el('p', 'pen-empty', 'برای مشاهدهٔ گزارش‌ها دانش‌آموز را انتخاب کنید.'));
    });
    filter.addEventListener('change', () => { if (student) load(); });
    [startDate, endDate].forEach(input => input.addEventListener('change', () => { if (student) load(); }));
    dateReset.addEventListener('click', () => { startDate.value = ''; endDate.value = ''; if (student) load(); });
    more.addEventListener('click', () => load(true));
    const query = new URLSearchParams(location.search);
    startDate.value = query.get('start') || '';
    endDate.value = query.get('end') || '';
    return;
  }

  const cls = document.getElementById('progress-class'), student = document.getElementById('progress-student');
  const page = document.getElementById('progress-student-page'), form = document.getElementById('progress-form');
  const history = document.getElementById('progress-history'), filter = document.getElementById('progress-filter');
  const more = document.getElementById('progress-more'), save = document.getElementById('progress-save'), send = document.getElementById('progress-send');
  const newButton = document.getElementById('progress-new');
  const periodRange = document.getElementById('progress-period-range');
  const periodStart = document.getElementById('progress-start');
  const periodEnd = document.getElementById('progress-end');
  const classReportHelp = document.getElementById('progress-class-report-help');
  const saveHint = document.getElementById('progress-save-hint');
  const currentSystemDate = document.getElementById('progress-teacher').dataset.systemDate;
  const dates = window.penReportDates;
  const todayParts = dates.english(window.penISOToJalali(currentSystemDate)).split('/');
  let preserveSavedRange = false;
  const showRange = () => {
    const isDaily = form.elements.period.value === 'daily' && periodStart.value && periodStart.value === periodEnd.value;
    let isToday = false;
    if (isDaily) { try { isToday = dates.iso(periodStart.value) === currentSystemDate; } catch (_) {} }
    document.getElementById('progress-period-label').textContent = isDaily ? 'تاریخ گزارش' : 'بازه گزارش';
    periodRange.textContent = isDaily ? `${isToday ? 'امروز' : 'روزانه'} · ${periodStart.value}` : `${periodStart.value} تا ${periodEnd.value}`;
  };
  const syncPeriodRange = () => {
    if (!preserveSavedRange) {
      try {
        const range = dates.range(form.elements.period.value, currentSystemDate, todayParts[0], todayParts[1]);
        periodStart.value = window.penISOToJalali(range.start);
        periodEnd.value = window.penISOToJalali(range.end);
        message('');
      } catch (error) { message(error.message, true); periodStart.value = ''; periodEnd.value = ''; }
    }
    showRange();
  };
  let reportId = null, dirty = false, next = null, version = 0, rosterVersion = 0, activeClass = '', activeStudent = '', saving = false;
  const discard = () => !dirty || window.confirm('تغییرات ذخیره نشده‌اند. از آن‌ها صرف‌نظر می‌کنید؟');
  const fresh = () => {
    form.reset(); reportId = null; dirty = false; preserveSavedRange = false;
    syncPeriodRange();
    document.getElementById('progress-form-title').textContent = 'گزارش جدید';
  };
  const updateAudienceControls = () => {
    const classWide = activeStudent === ALL_STUDENTS;
    save.hidden = classWide;
    send.textContent = classWide ? 'ارسال به کل کلاس' : 'ارسال به دانش‌آموز';
    classReportHelp.hidden = !classWide;
    saveHint.hidden = classWide;
  };
  const loadHistory = async (append = false) => {
    const current = ++version; if (!activeStudent) return;
    const classWide = activeStudent === ALL_STUDENTS;
    const params = new URLSearchParams({offering: activeClass, period: filter.value});
    if (!classWide) params.set('student', activeStudent);
    const url = append ? next : `/api/education/progress-reports/${classWide ? 'class/' : ''}?${params}`;
    if (!url) return;
    more.disabled = true;
    if (!append) history.replaceChildren(el('p', 'text-muted', 'در حال دریافت گزارش‌ها…'));
    try {
      const body = await api(url); if (current !== version) return;
      if (!append) history.replaceChildren();
      (Array.isArray(body) ? body : body.results || []).forEach(report => history.append(card(report, r => {
        if (saving || !discard()) return;
        reportId = r.id; fields.forEach(field => { form.elements[field].value = r[field] || ''; }); preserveSavedRange = true; showRange(); dirty = false;
        document.getElementById('progress-form-title').textContent = 'ویرایش پیش‌نویس'; form.scrollIntoView({behavior: 'smooth', block: 'start'}); form.elements.title.focus({preventScroll: true});
      })));
      if (!history.children.length) history.append(el('p', 'pen-empty', 'برای این دانش‌آموز هنوز گزارشی ثبت نکرده‌اید.'));
      next = body.next || null; more.hidden = !next;
    } catch (error) {
      if (current !== version) return;
      if (!append) history.replaceChildren(el('p', 'text-muted', 'سوابق دریافت نشدند. صفحه را تازه کنید.'));
      message(error.message, true);
    } finally { if (current === version) more.disabled = false; }
  };
  const selectStudent = () => {
    activeStudent = student.value; version++; next = null; more.hidden = true; page.hidden = !activeStudent; fresh(); message('');
    if (activeStudent) {
      const classWide = activeStudent === ALL_STUDENTS;
      document.getElementById('progress-student-name').textContent = classWide ? 'گزارش برای کل کلاس' : student.selectedOptions[0].textContent;
      document.getElementById('progress-form-title').textContent = classWide ? 'گزارش جدید برای کل کلاس' : 'گزارش جدید';
      updateAudienceControls();
      window.history.replaceState(null, '', `${location.pathname}?${new URLSearchParams({offering: activeClass, student: classWide ? 'all' : activeStudent})}`);
      loadHistory();
    } else updateAudienceControls();
  };
  const loadRoster = async (initial = '') => {
    const current = ++rosterVersion;
    activeClass = cls.value; activeStudent = ''; version++; page.hidden = true; student.disabled = true;
    student.replaceChildren(new Option(activeClass ? 'در حال دریافت دانش‌آموزان…' : 'ابتدا کلاس را انتخاب کنید', ''));
    if (!activeClass) return;
    try {
      const body = await api(`/api/education/offerings/${activeClass}/roster/`); if (current !== rosterVersion) return;
      student.replaceChildren(new Option(body.results.length ? 'دانش‌آموز یا کل کلاس را انتخاب کنید' : 'این کلاس دانش‌آموز فعالی ندارد', ''));
      if (body.results.length) student.append(new Option(`همهٔ کلاس (${body.results.length} هنرجو)`, ALL_STUDENTS));
      body.results.forEach(s => student.append(new Option(s.name, s.id))); student.disabled = !body.results.length;
      if (initial === 'all' && body.results.length) { student.value = ALL_STUDENTS; selectStudent(); }
      else if (initial && body.results.some(s => s.id === initial)) { student.value = initial; selectStudent(); }
    } catch (error) { if (current === rosterVersion) message(error.message, true); }
  };
  cls.addEventListener('change', () => { if (!discard()) { cls.value = activeClass; return; } dirty = false; message(''); loadRoster(); });
  student.addEventListener('change', () => { if (!discard()) { student.value = activeStudent; return; } selectStudent(); });
  form.addEventListener('input', () => { dirty = true; }); form.addEventListener('change', () => { dirty = true; });
  form.elements.period.addEventListener('change', () => { preserveSavedRange = false; syncPeriodRange(); dirty = true; });
  if (window.penAttachJalaliPickers) window.penAttachJalaliPickers();
  newButton.addEventListener('click', () => { if (!saving && discard()) { fresh(); form.scrollIntoView({behavior: 'smooth', block: 'start'}); form.elements.title.focus({preventScroll: true}); } });
  filter.addEventListener('change', () => loadHistory()); more.addEventListener('click', () => loadHistory(true));
  window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  form.addEventListener('submit', async event => {
    event.preventDefault(); if (saving || !activeStudent) return;
    const publish = event.submitter === send;
    const classWide = activeStudent === ALL_STUDENTS;
    if (classWide && !publish) return;
    const data = Object.fromEntries(fields.map(field => [field, form.elements[field].value]));
    try {
      // Send the visible Jalali strings; validation also accepts Gregorian ISO.
      const start = dates.iso(data.period_start), end = dates.iso(data.period_end);
      if (end < start || (start === end && data.start_time && data.end_time && data.end_time <= data.start_time)) throw new Error('تاریخ و ساعت پایان باید بعد از شروع باشد.');
      if (start > currentSystemDate || end > currentSystemDate) throw new Error('تاریخ گزارش نمی‌تواند در آینده باشد.');
      data.start_time = data.start_time || null; data.end_time = data.end_time || null;
      [periodStart, periodEnd].forEach(input => input.removeAttribute('aria-invalid'));
    } catch (error) { message(error.message, true); [periodStart, periodEnd].forEach(input => input.setAttribute('aria-invalid', 'true')); return; }
    data.offering = activeClass;
    if (!classWide) data.student = activeStudent;
    saving = true; form.setAttribute('aria-busy', 'true');
    [...form.elements, newButton, cls, student].forEach(control => { control.disabled = true; });
    try {
      if (classWide) {
        const result = await api('/api/education/progress-reports/class/', {method: 'POST', body: JSON.stringify(data)});
        reportId = null; dirty = false; fresh();
        message(`گزارش برای ${result.count} هنرجوی فعال کلاس ارسال شد.`);
      } else {
        const report = await api(reportId ? `/api/education/progress-reports/${reportId}/` : '/api/education/progress-reports/', {
          method: reportId ? 'PATCH' : 'POST', body: JSON.stringify(data),
        }); reportId = report.id; dirty = false;
        if (publish) {
        await api(`/api/education/progress-reports/${reportId}/send/`, {method: 'POST', body: '{}'});
        fresh(); message('گزارش ارسال شد و در پرتال دانش‌آموز قابل مشاهده است.');
        } else { document.getElementById('progress-form-title').textContent = 'ویرایش پیش‌نویس'; message('پیش‌نویس ذخیره شد. هنوز برای دانش‌آموز ارسال نشده است.'); }
      }
      await loadHistory();
    } catch (error) { message(error.message, true); await loadHistory(); }
    finally {
      saving = false; form.removeAttribute('aria-busy');
      [...form.elements, newButton, cls, student].forEach(control => { control.disabled = false; });
    }
  });
  api('/api/education/teacher/classes/').then(async body => {
    body.results = (body.results || []).filter(item => item.can_write_progress_report !== false);
    cls.replaceChildren(new Option(body.results.length ? 'کلاس را انتخاب کنید' : 'کلاس فعالی به شما اختصاص داده نشده است', ''));
    body.results.forEach(item => cls.append(new Option(item.title || item.course, item.id)));
    const initial = new URLSearchParams(location.search);
    if (body.results.some(item => item.id === initial.get('offering'))) { cls.value = initial.get('offering'); await loadRoster(initial.get('student') || ''); }
  }).catch(error => { cls.replaceChildren(new Option('کلاس‌ها دریافت نشدند', '')); message(error.message, true); });
})();
