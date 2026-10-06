/* Period progress reports: teacher composition and learner reading. */
(() => {
  'use strict';
  const teacher = document.getElementById('progress-teacher');
  const learner = document.getElementById('progress-learner');
  if (!teacher && !learner) return;
  const fields = ['period', 'period_start', 'period_end', 'title', 'summary', 'strengths', 'improvements', 'homework', 'next_steps'];
  const sections = {summary: 'شرح عملکرد و پیشرفت', strengths: 'نقاط قوت', improvements: 'موارد نیازمند تمرین', homework: 'تکالیف', next_steps: 'برنامهٔ ادامهٔ یادگیری'};
  const api = async (url, options = {}) => {
    const response = await fetch(url, {credentials: 'same-origin', ...options, headers: {
      'Content-Type': 'application/json', ...(window.penCsrfHeader ? window.penCsrfHeader() : {}), ...(options.headers || {}),
    }});
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const labels = {period_start: 'از تاریخ', period_end: 'تا تاریخ', summary: 'شرح عملکرد', title: 'عنوان', student: 'دانش‌آموز'};
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
    body.append(header, el('p', 'text-muted fs-13 mb-2', `${report.offering_name} · ${report.period_start} تا ${report.period_end}`), el('p', 'text-muted fs-13 mb-3', `مدرس: ${report.author_name}`));
    const status = el('span', 'badge bg-secondary-subtle text-secondary mb-3', report.status === 'draft' ? 'پیش‌نویس' : report.read_at ? 'مشاهده‌شده توسط دانش‌آموز' : teacher ? 'ارسال‌شده؛ هنوز مشاهده نشده' : 'جدید');
    body.append(status);
    const details = el('details', 'progress-report-details');
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
  const currentSystemDate = document.getElementById('progress-teacher').dataset.systemDate;
  const dateFromIso = value => {
    const parts = value.split('-').map(Number);
    return parts.length === 3 ? new Date(Date.UTC(parts[0], parts[1] - 1, parts[2])) : null;
  };
  const isoFromDate = date => `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}-${String(date.getUTCDate()).padStart(2, '0')}`;
  const syncPeriodRange = () => {
    const today = dateFromIso(currentSystemDate);
    if (!today || Number.isNaN(today.getTime())) return;
    let start = new Date(today), end = new Date(today);
    if (form.elements.period.value === 'weekly') {
      start.setUTCDate(start.getUTCDate() - ((start.getUTCDay() + 1) % 7));
      end = new Date(start); end.setUTCDate(end.getUTCDate() + 6);
    } else if (form.elements.period.value === 'monthly') {
      const [jalaliYear, jalaliMonth] = window.penISOToJalali(currentSystemDate).split('/').map(Number);
      const nextYear = jalaliMonth === 12 ? jalaliYear + 1 : jalaliYear;
      const nextMonth = jalaliMonth === 12 ? 1 : jalaliMonth + 1;
      const nextMonthIso = window.penJalaliToISO(`${nextYear}/${String(nextMonth).padStart(2, '0')}/01`);
      const monthEnd = dateFromIso(nextMonthIso);
      monthEnd.setUTCDate(monthEnd.getUTCDate() - 1);
      start = dateFromIso(window.penJalaliToISO(`${jalaliYear}/${String(jalaliMonth).padStart(2, '0')}/01`));
      end = monthEnd;
    }
    const startIso = isoFromDate(start), endIso = isoFromDate(end);
    periodStart.value = startIso;
    periodEnd.value = endIso;
    const jalali = value => window.penISOToJalali ? window.penISOToJalali(value) : value;
    const persian = value => window.persianNumbers ? window.persianNumbers(value) : value;
    const startLabel = persian(jalali(startIso)), endLabel = persian(jalali(endIso));
    const datePart = value => {
      const part = el('span', 'progress-period-date', value);
      part.dir = 'ltr';
      return part;
    };
    const parts = [datePart(startLabel)];
    if (startIso !== endIso) {
      const separator = el('span', 'progress-period-separator', 'تا');
      separator.dir = 'rtl';
      parts.push(separator, datePart(endLabel));
    }
    periodRange.replaceChildren(...parts);
    return {start: startIso, end: endIso};
  };
  let reportId = null, dirty = false, next = null, version = 0, rosterVersion = 0, activeClass = '', activeStudent = '', saving = false;
  const discard = () => !dirty || window.confirm('تغییرات ذخیره نشده‌اند. از آن‌ها صرف‌نظر می‌کنید؟');
  const fresh = () => {
    form.reset(); reportId = null; dirty = false;
    syncPeriodRange();
    document.getElementById('progress-form-title').textContent = 'گزارش جدید';
  };
  const loadHistory = async (append = false) => {
    const current = ++version; if (!activeStudent) return;
    const url = append ? next : `/api/education/progress-reports/?${new URLSearchParams({offering: activeClass, student: activeStudent, period: filter.value})}`;
    if (!url) return;
    more.disabled = true;
    if (!append) history.replaceChildren(el('p', 'text-muted', 'در حال دریافت گزارش‌ها…'));
    try {
      const body = await api(url); if (current !== version) return;
      if (!append) history.replaceChildren();
      (Array.isArray(body) ? body : body.results || []).forEach(report => history.append(card(report, r => {
        if (saving || !discard()) return;
        reportId = r.id; fields.forEach(field => { form.elements[field].value = r[field] || ''; }); syncPeriodRange(); dirty = false;
        document.getElementById('progress-form-title').textContent = 'ویرایش پیش‌نویس'; form.elements.title.focus();
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
      document.getElementById('progress-student-name').textContent = student.selectedOptions[0].textContent;
      window.history.replaceState(null, '', `${location.pathname}?${new URLSearchParams({offering: activeClass, student: activeStudent})}`);
      loadHistory();
    }
  };
  const loadRoster = async (initial = '') => {
    const current = ++rosterVersion;
    activeClass = cls.value; activeStudent = ''; version++; page.hidden = true; student.disabled = true;
    student.replaceChildren(new Option(activeClass ? 'در حال دریافت دانش‌آموزان…' : 'ابتدا کلاس را انتخاب کنید', ''));
    if (!activeClass) return;
    try {
      const body = await api(`/api/education/offerings/${activeClass}/roster/`); if (current !== rosterVersion) return;
      student.replaceChildren(new Option(body.results.length ? 'دانش‌آموز را انتخاب کنید' : 'این کلاس دانش‌آموز فعالی ندارد', ''));
      body.results.forEach(s => student.append(new Option(s.name, s.id))); student.disabled = !body.results.length;
      if (initial && body.results.some(s => s.id === initial)) { student.value = initial; selectStudent(); }
    } catch (error) { if (current === rosterVersion) message(error.message, true); }
  };
  cls.addEventListener('change', () => { if (!discard()) { cls.value = activeClass; return; } dirty = false; message(''); loadRoster(); });
  student.addEventListener('change', () => { if (!discard()) { student.value = activeStudent; return; } selectStudent(); });
  form.addEventListener('input', () => { dirty = true; }); form.addEventListener('change', () => { dirty = true; });
  form.elements.period.addEventListener('change', () => { syncPeriodRange(); dirty = true; });
  newButton.addEventListener('click', () => { if (!saving && discard()) { fresh(); form.elements.title.focus(); } });
  filter.addEventListener('change', () => loadHistory()); more.addEventListener('click', () => loadHistory(true));
  window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  form.addEventListener('submit', async event => {
    event.preventDefault(); if (saving || !activeStudent) return;
    const publish = event.submitter === send;
    const range = syncPeriodRange();
    const data = Object.fromEntries(fields.map(field => [field, form.elements[field].value]));
    data.period_start = range.start; data.period_end = range.end;
    data.offering = activeClass; data.student = activeStudent;
    saving = true; form.setAttribute('aria-busy', 'true');
    [...form.elements, newButton, cls, student].forEach(control => { control.disabled = true; });
    try {
      const report = await api(reportId ? `/api/education/progress-reports/${reportId}/` : '/api/education/progress-reports/', {
        method: reportId ? 'PATCH' : 'POST', body: JSON.stringify(data),
      }); reportId = report.id; dirty = false;
      if (publish) {
        await api(`/api/education/progress-reports/${reportId}/send/`, {method: 'POST', body: '{}'});
        fresh(); message('گزارش ارسال شد و در پرتال دانش‌آموز قابل مشاهده است.');
      } else { document.getElementById('progress-form-title').textContent = 'ویرایش پیش‌نویس'; message('پیش‌نویس ذخیره شد. هنوز برای دانش‌آموز ارسال نشده است.'); }
      await loadHistory();
    } catch (error) { message(error.message, true); await loadHistory(); }
    finally {
      saving = false; form.removeAttribute('aria-busy');
      [...form.elements, newButton, cls, student].forEach(control => { control.disabled = false; });
    }
  });
  api('/api/education/teacher/classes/').then(async body => {
    cls.replaceChildren(new Option(body.results.length ? 'کلاس را انتخاب کنید' : 'کلاس فعالی به شما اختصاص داده نشده است', ''));
    body.results.forEach(item => cls.append(new Option(item.title || item.course, item.id)));
    const initial = new URLSearchParams(location.search);
    if (body.results.some(item => item.id === initial.get('offering'))) { cls.value = initial.get('offering'); await loadRoster(initial.get('student') || ''); }
  }).catch(error => { cls.replaceChildren(new Option('کلاس‌ها دریافت نشدند', '')); message(error.message, true); });
})();
