let currentPage = 'home';
let state = { persons: [], instances: [], tasks: [], terms: [], classGroups: [], enrollments: [], transitions: [] };

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.sidebar nav a').forEach(a => {
    a.addEventListener('click', e => { e.preventDefault(); navigate(a.dataset.page); });
  });
  navigate('home');
});

function navigate(page) {
  currentPage = page;
  document.querySelectorAll('.sidebar nav a').forEach(a => a.classList.toggle('active', a.dataset.page === page));
  document.getElementById('page-content').innerHTML = '<div class="loading">در حال بارگذاری...</div>';
  const handlers = {
    home: loadHome,
    persons: loadPersons,
    workflow: loadWorkflow,
    tasks: loadTasks,
    academics: loadAcademics,
  };
  (handlers[page] || loadHome)();
}

function showError(msg) {
  document.getElementById('page-content').innerHTML = `<div class="card"><div class="empty-state"><p style="color:var(--danger)">${htmlEscape(msg)}</p></div></div>`;
}

function showLoading(container) {
  if (!container) container = document.getElementById('page-content');
  container.innerHTML = '<div class="loading">در حال بارگذاری...</div>';
}

// ─── Home ──────────────────────────────────────────────────────

async function loadHome() {
  const el = document.getElementById('page-content');
  try {
    const [persons, instances, tasks, terms] = await Promise.all([
      API.get('/api/persons/?limit=1').catch(() => ({ count: 0 })),
      API.get('/api/workflow/instances/?limit=1').catch(() => ({ count: 0 })),
      API.get('/api/tasks/?limit=1').catch(() => ({ count: 0 })),
      API.get('/api/academics/terms/?limit=1').catch(() => ({ count: 0 })),
    ]);
    el.innerHTML = `
      <div class="page-header"><h2>داشبورد</h2></div>
      <div class="stats">
        <div class="stat-card"><div class="num">${persianNumbers(persons.count||0)}</div><div class="label">اشخاص</div></div>
        <div class="stat-card"><div class="num">${persianNumbers(instances.count||0)}</div><div class="label">فرآیندها</div></div>
        <div class="stat-card"><div class="num">${persianNumbers(tasks.count||0)}</div><div class="label">وظایف</div></div>
        <div class="stat-card"><div class="num">${persianNumbers(terms.count||0)}</div><div class="label">ترم‌ها</div></div>
      </div>
      <div class="card">
        <h4 style="margin-bottom:.75rem">دسترسی سریع</h4>
        <div class="flex gap-2" style="flex-wrap:wrap">
          <button class="btn btn-primary" onclick="navigate('persons')">مدیریت اشخاص</button>
          <button class="btn btn-primary" onclick="navigate('workflow')">فرآیندها</button>
          <button class="btn btn-outline" onclick="navigate('tasks')">وظایف من</button>
          <button class="btn btn-outline" onclick="navigate('academics')">مدیریت آموزشی</button>
        </div>
      </div>`;
  } catch (e) { showError(e.message); }
}

// ─── Persons ───────────────────────────────────────────────────

async function loadPersons() {
  const el = document.getElementById('page-content');
  el.innerHTML = `
    <div class="page-header"><h2>اشخاص</h2><button class="btn btn-primary" onclick="showPersonForm()">+ شخص جدید</button></div>
    <div class="filters">
      <select id="person-type-filter" onchange="loadPersons()">
        <option value="">همه انواع</option>
        <option value="student">دانش‌آموز</option>
        <option value="teacher">معلم / مدرس</option>
        <option value="employee">کارمند</option>
        <option value="parent">والدین</option>
      </select>
      <input type="text" id="person-search" placeholder="جستجو..." oninput="debounceSearch('person-search',loadPersons)">
    </div>
    <div class="table-wrap"><table><thead><tr>
      <th>کد ملی</th><th>نام</th><th>نام خانوادگی</th><th>نوع</th><th>موبایل</th><th>کاربر</th><th>عملیات</th>
    </tr></thead><tbody id="person-tbody"></tbody></table></div>
    <div id="person-pagination" class="flex items-center justify-between mt-2 text-sm"></div>`;

  try {
    const params = {};
    const type = document.getElementById('person-type-filter').value;
    if (type) params.person_type = type;
    const search = document.getElementById('person-search').value;
    if (search) params.search = search;
    const data = await API.persons.list(params);
    const tbody = document.getElementById('person-tbody');
    if (!data.results || data.results.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><p>هیچ شخصی یافت نشد</p></div></td></tr>';
      return;
    }
    tbody.innerHTML = data.results.map(p => `<tr>
      <td>${formatDate(p.national_code)}</td>
      <td>${htmlEscape(p.first_name)}</td>
      <td>${htmlEscape(p.last_name)}</td>
      <td>${htmlEscape(p.person_type_display)}</td>
      <td>${formatDate(p.mobile)}</td>
      <td>${p.has_user ? '✅' : '❌'}</td>
      <td class="flex gap-2">
        <button class="btn btn-sm btn-outline" onclick="showPersonDetail('${p.id}')">جزئیات</button>
        ${p.has_user ? '' : `<button class="btn btn-sm btn-primary" onclick="createUserForPerson('${p.id}')">ساخت کاربر</button>`}
      </td>
    </tr>`).join('');
  } catch (e) { showError(e.message); }
}

async function showPersonDetail(id) {
  try {
    const p = await API.persons.get(id);
    const isRTL = true;
    openModal(`
      <h3>${htmlEscape(p.display_name)}</h3>
      <div class="detail-section">
        <div class="detail-grid">
          <div class="detail-item"><div class="label">کد ملی</div><div class="value">${formatDate(p.display_national_code)}</div></div>
          <div class="detail-item"><div class="label">نوع</div><div class="value">${htmlEscape(p.person_type_display)}</div></div>
          <div class="detail-item"><div class="label">نام پدر</div><div class="value">${htmlEscape(p.father_name||'—')}</div></div>
          <div class="detail-item"><div class="label">تاریخ تولد</div><div class="value">${p.birth_date||'—'}</div></div>
          <div class="detail-item"><div class="label">جنسیت</div><div class="value">${htmlEscape(p.gender_display)}</div></div>
          <div class="detail-item"><div class="label">موبایل</div><div class="value">${formatDate(p.display_mobile)}</div></div>
          <div class="detail-item"><div class="label">ایمیل</div><div class="value">${htmlEscape(p.email||'—')}</div></div>
          <div class="detail-item"><div class="label">وضعیت</div><div class="value">${p.is_active ? 'فعال' : 'غیرفعال'}</div></div>
          <div class="detail-item"><div class="label">کاربر</div><div class="value">${p.has_user ? 'دارد ('+htmlEscape(p.username||'')+')' : 'ندارد'}</div></div>
        </div>
      </div>
      ${p.student_code ? `<div class="detail-section"><h4>دانش‌آموز</h4><div class="detail-grid"><div class="detail-item"><div class="label">کد دانش‌آموزی</div><div class="value">${formatDate(p.student_code)}</div></div></div></div>` : ''}
      ${p.employee_code ? `<div class="detail-section"><h4>کارمند / معلم</h4><div class="detail-grid">
        <div class="detail-item"><div class="label">کد پرسنلی</div><div class="value">${formatDate(p.employee_code)}</div></div>
        <div class="detail-item"><div class="label">دپارتمان</div><div class="value">${htmlEscape(p.department||'—')}</div></div>
        <div class="detail-item"><div class="label">سمت</div><div class="value">${htmlEscape(p.job_title||'—')}</div></div>
      </div></div>` : ''}
      <div class="form-actions">
        <button class="btn btn-outline" onclick="closeModal()">بستن</button>
      </div>
    `);
  } catch (e) { alert(e.message); }
}

function showPersonForm(data) {
  const isEdit = !!data;
  openModal(`
    <h3>${isEdit ? 'ویرایش' : 'ثبت'} شخص جدید</h3>
    <form id="person-form" onsubmit="savePerson(event)">
      <input type="hidden" name="id" value="${data?.id||''}">
      <div class="form-row">
        <div class="form-group"><label>کد ملی *</label><input name="national_code" value="${data?.national_code||''}" required pattern="[0-9]{10}" title="۱۰ رقم"></div>
        <div class="form-group"><label>نوع *</label><select name="person_type" required onchange="togglePersonFields()">
          ${['student','teacher','employee','parent'].map(t => `<option value="${t}" ${data?.person_type===t?'selected':''}>${({student:'دانش‌آموز',teacher:'معلم / مدرس',employee:'کارمند',parent:'والدین'})[t]}</option>`).join('')}
        </select></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>نام *</label><input name="first_name" value="${data?.first_name||''}" required></div>
        <div class="form-group"><label>نام خانوادگی *</label><input name="last_name" value="${data?.last_name||''}" required></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>نام پدر</label><input name="father_name" value="${data?.father_name||''}"></div>
        <div class="form-group"><label>موبایل *</label><input name="mobile" value="${data?.mobile||''}" required></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>تاریخ تولد (مثال: ۱۳۸۵/۰۶/۱۵)</label><input name="birth_date" value="${data?.birth_date||''}"></div>
        <div class="form-group"><label>جنسیت</label><select name="gender">
          <option value="unspecified">مشخص نشده</option>
          <option value="male" ${data?.gender==='male'?'selected':''}>مرد</option>
          <option value="female" ${data?.gender==='female'?'selected':''}>زن</option>
        </select></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>ایمیل</label><input name="email" type="email" value="${data?.email||''}"></div>
        <div class="form-group"><label>تلفن ثابت</label><input name="phone" value="${data?.phone||''}"></div>
      </div>
      <div id="person-student-fields" class="form-row" style="display:none">
        <div class="form-group"><label>کد دانش‌آموزی *</label><input name="student_code" value="${data?.student_code||''}" placeholder="مثال: ۹۹۹۰۱۰۰۰۱"></div>
      </div>
      <div id="person-employee-fields" style="display:none">
        <div class="form-row">
          <div class="form-group"><label>کد پرسنلی *</label><input name="employee_code" value="${data?.employee_code||''}"></div>
          <div class="form-group"><label>دپارتمان</label><input name="department" value="${data?.department||''}"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>سمت</label><input name="job_title" value="${data?.job_title||''}"></div>
          <div class="form-group"><label>تاریخ استخدام</label><input name="hire_date" value="${data?.hire_date||''}"></div>
        </div>
      </div>
      <div class="form-group">
        <label><input type="checkbox" name="auto_create_user" value="true" checked> ساخت خودکار کاربر</label>
        <small class="text-muted">نام کاربری و رمز عبور پیش‌فرض هر دو برابر کد ملی هستند.</small>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">انصراف</button>
      </div>
    </form>
  `);
  togglePersonFields();
}

function togglePersonFields() {
  const sel = document.querySelector('#person-form select[name="person_type"]');
  const type = sel?.value;
  const studentFields = document.getElementById('person-student-fields');
  const employeeFields = document.getElementById('person-employee-fields');
  const studentCode = document.querySelector('#person-form input[name="student_code"]');
  const employeeCode = document.querySelector('#person-form input[name="employee_code"]');

  studentFields.style.display = type === 'student' ? '' : 'none';
  employeeFields.style.display = (type === 'employee' || type === 'teacher') ? '' : 'none';
  if (studentCode) {
    studentCode.required = type === "student";
    studentCode.disabled = type !== "student";
  }

  if (employeeCode) {
    employeeCode.required = type === "employee" || type === "teacher";
    employeeCode.disabled = !(type === "employee" || type === "teacher");
  }
}

async function savePerson(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = Object.fromEntries(fd);
  data.auto_create_user = data.auto_create_user === 'true';
  if (data.gender === 'unspecified') data.gender = 'unspecified';
  try {
    await API.persons.create(data);
    closeModal();
    loadPersons();
  } catch (err) { alert(err.message); }
}

async function createUserForPerson(personId) {
  if (!confirm('آیا از ساخت کاربر برای این شخص اطمینان دارید؟')) return;
  try {
    await API.persons.createUser(personId, {});
    loadPersons();
  } catch (err) { alert(err.message); }
}

// ─── Workflow ──────────────────────────────────────────────────

async function loadWorkflow() {
  const el = document.getElementById('page-content');
  el.innerHTML = `
    <div class="page-header"><h2>فرآیندها</h2><button class="btn btn-primary" onclick="showWorkflowForm()">درخواست جدید</button></div>
    <div class="filters">
      <select id="wf-status-filter" onchange="loadWorkflow()">
        <option value="">همه وضعیت‌ها</option>
        <option value="running">در حال اجرا</option>
        <option value="completed">تکمیل شده</option>
        <option value="rejected">رد شده</option>
        <option value="cancelled">لغو شده</option>
      </select>
    </div>
    <div class="table-wrap"><table><thead><tr>
      <th>عنوان</th><th>فرآیند</th><th>وضعیت فعلی</th><th>درخواست‌کننده</th><th>وضعیت</th><th>تاریخ</th><th>عملیات</th>
    </tr></thead><tbody id="wf-tbody"></tbody></table></div>`;

  try {
    const params = {};
    const status = document.getElementById('wf-status-filter').value;
    if (status) params.status = status;
    const data = await API.workflow.instances(params);
    const tbody = document.getElementById('wf-tbody');
    if (!data.results || data.results.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><p>هیچ فرآیندی یافت نشد</p></div></td></tr>';
      return;
    }
    tbody.innerHTML = data.results.map(inst => `
      <tr>
        <td>${htmlEscape(inst.title)}</td>
        <td>${htmlEscape(inst.workflow_definition_code)}</td>
        <td>${htmlEscape(inst.current_state_code||'—')}</td>
        <td>${htmlEscape(inst.requester_username)}</td>
        <td><span class="badge badge-${inst.status}">${inst.status}</span></td>
        <td>${formatDate(inst.created_at)}</td>
        <td><button class="btn btn-sm btn-outline" onclick="showWorkflowDetail('${inst.id}')">جزئیات</button></td>
      </tr>
    `).join('');
  } catch (e) { showError(e.message); }
}

function showWorkflowForm() {
  openModal(`
    <h3>درخواست جدید</h3>
    <form id="wf-form" onsubmit="createWorkflowInstance(event)">
      <div class="form-group"><label>کد فرآیند *</label><input name="workflow_code" required placeholder="مثال: leave-request"></div>
      <div class="form-group"><label>عنوان *</label><input name="title" required></div>
      <div class="form-group"><label>توضیحات</label><textarea name="description" rows="3"></textarea></div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">ایجاد</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">انصراف</button>
      </div>
    </form>
  `);
}

async function createWorkflowInstance(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = Object.fromEntries(fd);
  try {
    const inst = await API.workflow.create(data);
    closeModal();
    loadWorkflow();
    showWorkflowDetail(inst.id);
  } catch (err) { alert(err.message); }
}

async function showWorkflowDetail(id) {
  try {
    const [inst, transitions, logs] = await Promise.all([
      API.workflow.get(id),
      API.workflow.transitions(id),
      API.workflow.logs(id),
    ]);
    openModal(`
      <h3>${htmlEscape(inst.title)}</h3>
      <div class="detail-section">
        <div class="detail-grid">
          <div class="detail-item"><div class="label">فرآیند</div><div class="value">${htmlEscape(inst.workflow_definition?.code||'')}</div></div>
          <div class="detail-item"><div class="label">وضعیت فعلی</div><div class="value">${htmlEscape(inst.current_state_code||'—')}</div></div>
          <div class="detail-item"><div class="label">وضعیت کلی</div><div class="value"><span class="badge badge-${inst.status}">${inst.status}</span></div></div>
          <div class="detail-item"><div class="label">درخواست‌کننده</div><div class="value">${htmlEscape(inst.requester_username)}</div></div>
          <div class="detail-item"><div class="label">تاریخ</div><div class="value">${formatDate(inst.created_at)}</div></div>
          <div class="detail-item"><div class="label">تسک‌ها</div><div class="value">${persianNumbers(inst.task_count?.pending||0)} در انتظار / ${persianNumbers(inst.task_count?.total||0)} کل</div></div>
        </div>
        ${inst.description ? `<div class="mt-2"><div class="label">توضیحات</div><div class="value">${htmlEscape(inst.description)}</div></div>` : ''}
      </div>
      ${transitions.length > 0 ? `
        <div class="detail-section"><h4>انتقالات مجاز</h4>
          ${transitions.map(t => `
            <div class="card" style="padding:.75rem;margin-bottom:.5rem">
              <div><strong>${htmlEscape(t.name)}</strong> (${htmlEscape(t.from_state_code)} → ${htmlEscape(t.to_state_code)})</div>
              <div class="text-sm text-muted">نقش‌های مجاز: ${htmlEscape(t.allowed_role_codes?.join(', ')||'همه')}</div>
              ${t.requires_comment ? '<div class="text-sm text-muted">نیاز به توضیح دارد</div>' : ''}
              <button class="btn btn-sm btn-primary mt-2" onclick="executeTransition('${id}','${t.id}','${htmlEscape(t.name)}',${t.requires_comment})">${htmlEscape(t.name)}</button>
            </div>
          `).join('')}
        </div>` : ''}
      ${inst.status === 'running' ? `<button class="btn btn-sm btn-danger mt-2" onclick="cancelInstance('${id}')">لغو درخواست</button>` : ''}
      <div class="detail-section mt-4"><h4>تاریخچه اقدامات</h4>
        <div class="log-timeline">
          ${logs.map(l => `
            <div class="log-item">
              <div class="log-action">${htmlEscape(l.action)}</div>
              <div class="log-meta">${htmlEscape(l.actor_username)} — ${formatDate(l.created_at)}</div>
              ${l.comment ? `<div class="log-comment">${htmlEscape(l.comment)}</div>` : ''}
              ${l.from_state_code ? `<div class="log-meta">${htmlEscape(l.from_state_code)} → ${htmlEscape(l.to_state_code||'—')}</div>` : ''}
            </div>
          `).join('')}
        </div>
      </div>
      <div class="form-actions"><button class="btn btn-outline" onclick="closeModal()">بستن</button></div>
    `);
  } catch (e) { alert(e.message); }
}

function executeTransition(instanceId, transitionId, name, needsComment) {
  const comment = needsComment ? prompt(`توضیح برای "${name}":`) : '';
  if (needsComment && comment === null) return;
  openModal(`
    <h3>${htmlEscape(name)}</h3>
    <p class="text-sm text-muted mb-2">آیا از انجام این انتقال اطمینان دارید؟</p>
    ${needsComment ? '' : ''}
    <form id="exec-form" onsubmit="doExecute(event,'${instanceId}','${transitionId}')">
      <div class="form-group"><label>توضیح (اختیاری)</label><textarea name="comment" rows="2">${needsComment ? htmlEscape(comment) : ''}</textarea></div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">تأیید</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">انصراف</button>
      </div>
    </form>
  `);
}

async function doExecute(e, instanceId, transitionId) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = { transition_id: transitionId, comment: fd.get('comment') || '' };
  try {
    await API.workflow.execute(instanceId, data);
    closeModal();
    showWorkflowDetail(instanceId);
  } catch (err) { alert(err.message); }
}

async function cancelInstance(id) {
  const reason = prompt('دلیل لغو:');
  if (reason === null) return;
  try {
    await API.workflow.cancel(id, { reason });
    closeModal();
    loadWorkflow();
  } catch (err) { alert(err.message); }
}

// ─── Tasks ─────────────────────────────────────────────────────

async function loadTasks() {
  const el = document.getElementById('page-content');
  el.innerHTML = `
    <div class="page-header"><h2>وظایف من</h2></div>
    <div class="filters">
      <select id="task-status-filter" onchange="loadTasks()">
        <option value="">همه</option>
        <option value="pending">در انتظار</option>
        <option value="completed">انجام شده</option>
        <option value="skipped">رد شده</option>
      </select>
    </div>
    <div class="table-wrap"><table><thead><tr>
      <th>عنوان فرآیند</th><th>وضعیت</th><th>فرآیند</th><th>مرحله</th><th>تاریخ</th><th>عملیات</th>
    </tr></thead><tbody id="task-tbody"></tbody></table></div>`;

  try {
    const params = {};
    const status = document.getElementById('task-status-filter').value;
    if (status) params.status = status;
    const data = await API.tasks.list(params);
    const tbody = document.getElementById('task-tbody');
    if (!data.results || data.results.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><p>هیچ وظیفه‌ای یافت نشد</p></div></td></tr>';
      return;
    }
    tbody.innerHTML = data.results.map(t => `
      <tr>
        <td>${htmlEscape(t.instance_title||t.instance?.title||'')}</td>
        <td><span class="badge badge-${t.status}">${t.status}</span></td>
        <td>${htmlEscape(t.workflow_definition_code||t.instance?.workflow_definition?.code||'')}</td>
        <td>${htmlEscape(t.state_code||t.state?.code||'')}</td>
        <td>${formatDate(t.created_at)}</td>
        <td><button class="btn btn-sm btn-outline" onclick="showTaskDetail('${t.id}')">نمایش</button></td>
      </tr>
    `).join('');
  } catch (e) { showError(e.message); }
}

async function showTaskDetail(id) {
  try {
    const t = await API.tasks.get(id);
    openModal(`
      <h3>جزئیات وظیفه</h3>
      <div class="detail-section">
        <div class="detail-grid">
          <div class="detail-item"><div class="label">فرآیند</div><div class="value">${htmlEscape(t.instance?.workflow_definition?.code||'')}</div></div>
          <div class="detail-item"><div class="label">مرحله</div><div class="value">${htmlEscape(t.state?.code||'')}</div></div>
          <div class="detail-item"><div class="label">وضعیت</div><div class="value"><span class="badge badge-${t.status}">${t.status}</span></div></div>
          <div class="detail-item"><div class="label">عنوان درخواست</div><div class="value">${htmlEscape(t.instance?.title||'')}</div></div>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn btn-outline" onclick="closeModal()">بستن</button>
        <button class="btn btn-primary" onclick="closeModal();showWorkflowDetail('${t.instance_id}')">مشاهده فرآیند</button>
      </div>
    `);
  } catch (e) { alert(e.message); }
}

// ─── Academics ─────────────────────────────────────────────────

async function loadAcademics() {
  const el = document.getElementById('page-content');
  el.innerHTML = `
    <div class="page-header"><h2>مدیریت آموزشی</h2></div>
    <div class="card"><h4 style="margin-bottom:.75rem">ترم‌های تحصیلی</h4>
      <div class="flex justify-between items-center mb-2">
        <div class="filters" style="margin:0">
          <select id="term-current-filter" onchange="loadAcademics()"><option value="">همه</option><option value="true">فقط جاری</option></select>
        </div>
        <button class="btn btn-sm btn-primary" onclick="showTermForm()">+ ترم جدید</button>
      </div>
      <div class="table-wrap"><table><thead><tr><th>عنوان</th><th>شروع</th><th>پایان</th><th>جاری</th><th>فعال</th><th>عملیات</th></tr></thead><tbody id="term-tbody"></tbody></table></div>
    </div>
    <div class="card"><h4 style="margin-bottom:.75rem">کلاس‌ها</h4>
      <div class="flex justify-between items-center mb-2">
        <div class="filters" style="margin:0">
          <select id="cg-term-filter" onchange="loadAcademics()"><option value="">همه ترم‌ها</option></select>
        </div>
        <button class="btn btn-sm btn-primary" onclick="showClassGroupForm()">+ کلاس جدید</button>
      </div>
      <div class="table-wrap"><table><thead><tr><th>نام</th><th>کد</th><th>ترم</th><th>معلم</th><th>ظرفیت</th><th>ثبت‌نام</th></tr></thead><tbody id="cg-tbody"></tbody></table></div>
    </div>
    <div class="card"><h4 style="margin-bottom:.75rem">ثبت‌نام‌ها</h4>
      <div class="flex justify-between items-center mb-2">
        <button class="btn btn-sm btn-primary" onclick="showEnrollmentForm()">+ ثبت‌نام جدید</button>
      </div>
      <div class="table-wrap"><table><thead><tr><th>دانش‌آموز</th><th>کلاس</th><th>تاریخ ثبت‌نام</th><th>وضعیت</th></tr></thead><tbody id="enroll-tbody"></tbody></table></div>
    </div>`;

  try {
    const [terms, classGroups, enrollments] = await Promise.all([
      API.academics.terms({}),
      API.academics.classGroups({}),
      API.academics.enrollments({}),
    ]);

    // Terms
    const termBody = document.getElementById('term-tbody');
    if (terms.results?.length) {
      termBody.innerHTML = terms.results.map(t => `
        <tr>
          <td>${htmlEscape(t.title)}</td>
          <td>${formatDate(t.start_date)}</td>
          <td>${formatDate(t.end_date)}</td>
          <td>${t.is_current ? '✅' : '—'}</td>
          <td>${t.is_active ? 'فعال' : 'غیرفعال'}</td>
          <td>${t.is_current ? '' : `<button class="btn btn-sm btn-primary" onclick="activateTerm('${t.id}')">فعال‌سازی</button>`}</td>
        </tr>
      `).join('');
    } else {
      termBody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><p>ترمی وجود ندارد</p></div></td></tr>';
    }

    // Populate term filter for class groups
    const cgFilter = document.getElementById('cg-term-filter');
    if (terms.results) {
      terms.results.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.title;
        cgFilter.appendChild(opt);
      });
    }

    // Class groups
    const cgBody = document.getElementById('cg-tbody');
    if (classGroups.results?.length) {
      cgBody.innerHTML = classGroups.results.map(cg => `
        <tr>
          <td>${htmlEscape(cg.name)}</td>
          <td>${htmlEscape(cg.code)}</td>
          <td>${htmlEscape(cg.term_title||'')}</td>
          <td>${htmlEscape(cg.teacher_name||'—')}</td>
          <td>${formatDate(cg.display_capacity||cg.capacity)}</td>
          <td>${persianNumbers(cg.enrollment_count||0)}</td>
        </tr>
      `).join('');
    } else {
      cgBody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><p>کلاسی وجود ندارد</p></div></td></tr>';
    }

    // Enrollments
    const enrBody = document.getElementById('enroll-tbody');
    if (enrollments.results?.length) {
      enrBody.innerHTML = enrollments.results.map(e => `
        <tr>
          <td>${htmlEscape(e.student_name)}</td>
          <td>${htmlEscape(e.class_group_name)}</td>
          <td>${formatDate(e.enrollment_date)}</td>
          <td>${e.is_active ? 'فعال' : 'غیرفعال'}</td>
        </tr>
      `).join('');
    } else {
      enrBody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><p>ثبت‌نامی وجود ندارد</p></div></td></tr>';
    }
  } catch (e) { showError(e.message); }
}

function showTermForm() {
  openModal(`
    <h3>ترم جدید</h3>
    <form id="term-form" onsubmit="saveTerm(event)">
      <div class="form-group"><label>عنوان *</label><input name="title" required></div>
      <div class="form-row">
        <div class="form-group"><label>تاریخ شروع *</label><input name="start_date" required placeholder="۱۴۰۴/۰۷/۰۱"></div>
        <div class="form-group"><label>تاریخ پایان *</label><input name="end_date" required placeholder="۱۴۰۵/۰۱/۱۵"></div>
      </div>
      <div class="form-group"><label><input type="checkbox" name="is_current" value="true"> ترم جاری</label></div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">انصراف</button>
      </div>
    </form>
  `);
}

async function saveTerm(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = Object.fromEntries(fd);
  data.is_current = data.is_current === 'true';
  try {
    await API.academics.createTerm(data);
    closeModal();
    loadAcademics();
  } catch (err) { alert(err.message); }
}

async function activateTerm(id) {
  try {
    await API.academics.activateTerm(id);
    loadAcademics();
  } catch (err) { alert(err.message); }
}

function showClassGroupForm() {
  openModal(`
    <h3>کلاس جدید</h3>
    <form id="cg-form" onsubmit="saveClassGroup(event)">
      <div class="form-group"><label>ترم *</label>
        <select name="term" id="cg-term-select" required><option value="">انتخاب...</option></select>
      </div>
      <div class="form-row">
        <div class="form-group"><label>کد *</label><input name="code" required placeholder="MATH-101-A"></div>
        <div class="form-group"><label>نام *</label><input name="name" required placeholder="ریاضی ۱"></div>
      </div>
      <div class="form-group"><label>معلم</label>
        <select name="teacher"><option value="">—</option></select>
      </div>
      <div class="form-row">
        <div class="form-group"><label>ظرفیت</label><input name="capacity" type="number" min="0"></div>
        <div class="form-group"><label>محل</label><input name="room"></div>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">انصراف</button>
      </div>
    </form>
  `);
  // Populate term dropdown
  API.academics.terms({}).then(d => {
    const sel = document.getElementById('cg-term-select');
    d.results?.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id; opt.textContent = t.title;
      sel.appendChild(opt);
    });
  });
  // Populate teacher dropdown
  API.persons.list({person_type:'teacher'}).then(d => {
    const sel = document.querySelector('#cg-form select[name="teacher"]');
    d.results?.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.first_name} ${p.last_name}`;
      sel.appendChild(opt);
    });
  });
}

async function saveClassGroup(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = Object.fromEntries(fd);
  if (!data.teacher) delete data.teacher;
  if (!data.capacity) data.capacity = 0;
  try {
    await API.academics.createClassGroup(data);
    closeModal();
    loadAcademics();
  } catch (err) { alert(err.message); }
}

function showEnrollmentForm() {
  openModal(`
    <h3>ثبت‌نام جدید</h3>
    <form id="enroll-form" onsubmit="saveEnrollment(event)">
      <div class="form-group"><label>دانش‌آموز *</label>
        <select name="student" required><option value="">انتخاب...</option></select>
      </div>
      <div class="form-group"><label>کلاس *</label>
        <select name="class_group" required><option value="">انتخاب...</option></select>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">انصراف</button>
      </div>
    </form>
  `);
  Promise.all([
    API.persons.list({person_type:'student'}),
    API.academics.classGroups({}),
  ]).then(([students, groups]) => {
    const sSel = document.querySelector('#enroll-form select[name="student"]');
    students.results?.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id; opt.textContent = `${p.first_name} ${p.last_name}`;
      sSel.appendChild(opt);
    });
    const cSel = document.querySelector('#enroll-form select[name="class_group"]');
    groups.results?.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.id; opt.textContent = g.name;
      cSel.appendChild(opt);
    });
  });
}

async function saveEnrollment(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = Object.fromEntries(fd);
  try {
    await API.academics.createEnrollment(data);
    closeModal();
    loadAcademics();
  } catch (err) { alert(err.message); }
}

// ─── Modal helpers ─────────────────────────────────────────────

function openModal(html) {
  let overlay = document.querySelector('.modal-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
    document.body.appendChild(overlay);
  }
  overlay.innerHTML = `<div class="modal">${html}</div>`;
  overlay.classList.add('open');
}

function closeModal() {
  const overlay = document.querySelector('.modal-overlay');
  if (overlay) overlay.classList.remove('open');
}

// ─── Debounce ──────────────────────────────────────────────────

const debounceTimers = {};
function debounceSearch(id, fn) {
  clearTimeout(debounceTimers[id]);
  debounceTimers[id] = setTimeout(fn, 300);
}
