/* Pen LMS — persons directory + two-step person definition wizard. */
(function () {
  'use strict';

  var ctxEl = document.getElementById('pen-persons-ctx');
  if (!ctxEl) return;
  var ctx = JSON.parse(ctxEl.textContent);
  var $table = document.getElementById('person-table');
  var $tbody = document.getElementById('person-list-body');
  var $status = document.getElementById('person-list-status');
  var $pageStatus = document.getElementById('person-page-status');
  var $pager = document.getElementById('person-pager');
  var $filters = document.getElementById('person-filter-form');
  var $modalEl = document.getElementById('person-create-modal');
  var $createForm = document.getElementById('person-create-form');
  var modal = $modalEl && window.bootstrap
    ? window.bootstrap.Modal.getOrCreateInstance($modalEl)
    : null;
  var $createUserModalEl = document.getElementById('person-create-user-modal');
  var createUserModal = $createUserModalEl && window.bootstrap
    ? window.bootstrap.Modal.getOrCreateInstance($createUserModalEl, {backdrop: 'static', keyboard: false})
    : null;
  var pendingUserCreation = null;
  var userCreationBusy = false;
  var state = { index: 0, request: null };
  var searchTimer;
  var $retry = document.getElementById("person-list-retry");

  function esc(value) {
    if (window.htmlEscape) return window.htmlEscape(value);
    return value == null ? '' : String(value).replace(/[&<>'"]/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[ch];
    });
  }

  function dateOnly(value) {
    return value == null || value === '' ? '—' : String(value).split(' — ')[0].split(' ')[0];
  }

  function toast(message, kind) {
    if (window.penToast) window.penToast(message, kind);
  }

  function uiErrorMessage(error) {
    var message = error && error.message ? String(error.message) : '';
    if (!message || /failed to fetch|networkerror|load failed|connection/i.test(message)) {
      return 'ارتباط با سامانه برقرار نشد؛ دوباره تلاش کنید.';
    }
    return message;
  }

  function errorLines(errors) {
    var fieldLabels = {
      non_field_errors: 'خطا', national_code: 'کد ملی', first_name: 'نام', last_name: 'نام خانوادگی',
      mobile: 'شماره همراه', email: 'رایانامه', birth_date: 'تاریخ تولد', gender: 'جنسیت',
      student_code: 'کد دانش‌آموزی', employee_code: 'کد پرسنلی', person_type: 'نوع شخص',
      student_profile: 'اطلاعات دانش‌آموز', staff_profile: 'اطلاعات همکار', guardian_profile: 'اطلاعات سرپرست',
      employee_kind: 'نوع همکاری', username: 'نام کاربری', password: 'گذرواژه', target: 'گروه کاربری',
    };
    var lines = [];
    Object.keys(errors || {}).forEach(function (key) {
      (Array.isArray(errors[key]) ? errors[key] : [errors[key]]).forEach(function (message) {
        lines.push(key === 'non_field_errors' ? String(message) : (fieldLabels[key] || 'اطلاعات') + ': ' + message);
      });
    });
    return lines.length ? lines : ['خطای نامشخص'];
  }

  function apiUrlWithParams() {
    var url = new URL(ctx.api_url, window.location.href);
    var params = new URLSearchParams(new FormData($filters));
    Array.from(params.entries()).forEach(function (entry) {
      if (!String(entry[1]).trim()) params.delete(entry[0]);
    });
    params.set('directory', ctx.directory || 'education');
    if (!params.has('page_size')) params.set('page_size', '50');
    url.search = params.toString();
    return url.toString();
  }

  function personResourceUrl(id, action, query) {
    var url = new URL(ctx.api_url, window.location.href);
    url.pathname = url.pathname.replace(/\/+$/, '') + '/' + encodeURIComponent(id) + '/';
    if (action) url.pathname += action.replace(/^\/+|\/+$/g, '') + '/';
    url.search = query || '';
    url.hash = '';
    return url.toString();
  }

  function renderRows(data) {
    var rows = data.results || [];
    if (!rows.length) {
      $tbody.innerHTML = '<tr><td colspan="5"><div class="pen-empty"><p class="mb-0">موردی یافت نشد؛ جست‌وجو را تغییر دهید یا فیلترها را پاک کنید.</p></div></td></tr>';
      return;
    }
    $tbody.innerHTML = rows.map(function (row) {
      var login = row.has_user
        ? (row.user_is_active ? 'حساب فعال' : 'حساب غیرفعال')
        : 'بدون حساب';
      var actions = row.actions || {view: true, edit: false, delete: false};
      var label = (row.first_name || '') + ' ' + (row.last_name || '');
      var menu = '<div class="dropdown pen-actions-dropdown text-end">' +
        '<button class="btn btn-sm btn-light" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="عملیات ' + esc(label) + '"><i data-lucide="more-horizontal" class="size-4"></i></button>' +
        '<ul class="dropdown-menu dropdown-menu-end">' +
        (actions.view ? '<li><button type="button" class="dropdown-item" data-person-view><i data-lucide="eye" class="size-4"></i> مشاهده</button></li>' : '') +
        (actions.edit ? '<li><button type="button" class="dropdown-item" data-person-edit><i data-lucide="pencil" class="size-4"></i> ویرایش</button></li>' : '') +
        (ctx.directory === 'education' && ctx.can_create_user && row.person_type === 'student' && !row.has_user ? '<li><button type="button" class="dropdown-item" data-person-create-user><i data-lucide="user-plus" class="size-4"></i> ساخت حساب کاربری</button></li>' : '') +
        (actions.delete ? '<li><hr class="dropdown-divider"></li><li><button type="button" class="dropdown-item text-danger" data-delete-action data-delete-url="' + esc(personResourceUrl(row.id, 'delete')) + '" data-delete-name="' + esc(label.trim()) + '" data-delete-code="' + esc(row.national_code || row.id) + '"><i data-lucide="trash-2" class="size-4"></i> حذف</button></li>' : '') +
        '</ul></div>';
      return '<tr>' +
        '<td><strong class="persons-name">' + esc(label.trim() || '—') + '</strong><small class="persons-secondary" dir="ltr">' + esc(row.national_code || '—') + '</small></td>' +
        '<td>' + esc(row.role_display || row.person_type_display || roleLabel(row.person_type)) + '</td>' +
        '<td><span dir="ltr">' + esc(row.mobile || '—') + '</span><small class="persons-secondary"><span class="badge rounded-pill ' + (row.has_user ? (row.user_is_active ? 'text-bg-success' : 'text-bg-secondary') : 'text-bg-light text-secondary') + '">' + esc(login) + '</span></small></td>' +
        '<td class="text-nowrap">' + esc(String(row.created_at || '—').split(' — ')[0]) + '</td>' +
        '<td class="text-nowrap text-end">' + menu + '</td>' +
        '</tr>';
    }).join('');
    $tbody.querySelectorAll('tr').forEach(function (tr, index) {
      var row = rows[index];
      tr.dataset.personRow = '';
      tr.dataset.personId = row.id;
      tr.tabIndex = 0;
      tr.setAttribute('aria-label', 'مشاهدهٔ جزئیات ' + labelForPerson(row) + '؛ برای ویرایش از منوی عملیات استفاده کنید');
      tr.addEventListener('click', function (event) {
        if (event.target.closest('button, a, [data-bs-toggle]')) return;
        openPersonDetail(row);
      });
      tr.addEventListener('keydown', function (event) {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        if (event.target !== tr || event.target.closest('button, a, [data-bs-toggle]')) return;
        event.preventDefault();
        openPersonDetail(row);
      });
      var view = tr.querySelector('[data-person-view]');
      var edit = tr.querySelector('[data-person-edit]');
      var createUser = tr.querySelector('[data-person-create-user]');
      if (view) view.addEventListener('click', function () { openPersonDetail(row); });
      if (edit) edit.addEventListener('click', function () { personRequest(row.id).then(openPersonEdit).catch(function (e) { toast(uiErrorMessage(e), 'danger'); }); });
      if (createUser) createUser.addEventListener('click', function () { createUserForPerson(row); });
    });
    if (window.penRenderIcons) window.penRenderIcons();
  }

  function personRequest(id) {
    return fetch(personResourceUrl(id, '', '?include_history=1'), {
      credentials: 'same-origin',
      headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
    }).then(function (response) {
      return response.json().then(function (body) {
        if (!response.ok) throw new Error(errorLines(body).join(' — '));
        return body;
      });
    });
  }

  function openPersonDetail(row) {
    personRequest(row.id).then(function (person) {
      var status = person.is_active ? 'فعال' : 'غیرفعال';
      var accountStatus = person.has_user
        ? (person.user_is_active ? 'فعال' : 'غیرفعال')
        : 'حساب کاربری ندارد';
      var history = Array.isArray(person.audit_trail) && person.audit_trail.length
        ? '<details class="persons-detail-history"><summary>سوابق تغییرات</summary><ol class="pen-timeline mb-0 mt-3">' + person.audit_trail.map(function (event) { return '<li class="pen-timeline-item"><div class="fw-semibold fs-14">' + esc(event.summary || event.kind) + '</div><div class="fs-13 text-muted">' + esc(event.actor || 'سامانه') + ' · ' + esc(dateOnly(event.created_at)) + '</div></li>'; }).join('') + '</ol></details>' : '';
      var student = person.student_profile || {};
      var familyRows = [
        ['پدر', [student.father_first_name, student.father_last_name].filter(Boolean).join(' '), student.father_phone],
        ['مادر', [student.mother_first_name, student.mother_last_name].filter(Boolean).join(' '), student.mother_phone],
      ].filter(function (item) { return item[1] || item[2]; });
      var familyHtml = personHasType(person, 'student') ? '<div class="mt-4 pt-3 border-top"><h6 class="fw-semibold mb-2">والدین و تکفل</h6>' +
        (familyRows.length ? '<div class="row g-2">' + familyRows.map(function (item) {
          return '<div class="col-md-6"><span class="text-muted fs-14">' + esc(item[0]) + ':</span> ' + esc(item[1] || '—') +
            (item[2] ? ' <span class="text-muted" dir="ltr">' + esc(item[2]) + '</span>' : '') + '</div>';
        }).join('') + '</div>' : '<p class="text-muted fs-14 mb-0">اطلاعات والدین ثبت نشده است.</p>') +
        '<div class="mt-2"><span class="text-muted fs-14">وضعیت تکفل:</span> ' +
        esc(student.is_custody_case ? (student.custody_note || 'ویژه') : 'عادی') + '</div></div>' : '';
      var hasStudentRole = personHasType(person, 'student');
      var enrollmentUrl = '/workspace/enrollments/person/' + encodeURIComponent(person.id) + '/';
      var enrollmentHtml = hasStudentRole ? '<section class="mt-4 pt-3 border-top" aria-labelledby="person-enrollments-title"><div class="d-flex align-items-center justify-content-between gap-2 mb-2"><h6 class="fw-semibold mb-0" id="person-enrollments-title">ثبت‌نام‌ها و دوره‌های آموزشی</h6><a class="btn btn-sm btn-outline-primary" href="' + esc(enrollmentUrl) + '">مشاهده همه</a></div><div id="person-enrollment-preview" data-person-id="' + esc(person.id) + '" class="text-muted fs-14" role="status" aria-live="polite">در حال دریافت سابقهٔ ثبت‌نام…</div></section>' : '';
      var body = '<div class="pen-detail-meta">' +
        '<div><small>وضعیت پروندهٔ شخص</small><strong>' + esc(status) + '</strong></div>' +
        '<div><small>وضعیت حساب کاربری</small><strong>' + esc(accountStatus) + '</strong></div>' +
        '<div><small>نوع</small><strong>' + esc(person.person_types_display || person.person_type_display || '—') + '</strong></div>' +
        '<div><small>ایجاد</small><strong dir="ltr">' + esc(dateOnly(person.created_at)) + '</strong></div>' +
        '<div><small>آخرین تغییر</small><strong dir="ltr">' + esc(dateOnly(person.updated_at)) + '</strong></div>' +
        '</div><div class="vstack gap-2 persons-detail-fields">' +
        [['کد ملی', person.display_national_code || person.national_code],
         ['موبایل', person.display_mobile || person.mobile], ['نام پدر', person.father_name],
         ['رایانامه', person.email], ['تلفن ثابت', person.phone], ['نشانی', person.address],
         ['کد دانش‌آموزی', person.student_code], ['کد پرسنلی', person.employee_code],
         ['دپارتمان', person.department], ['سمت', person.job_title], ['نام کاربری', person.username]]
        .filter(function (item) { return item[1] != null && String(item[1]).trim() && item[1] !== '—'; })
        .map(function (item) { return '<div class="row g-2"><div class="col-5 text-muted fs-14">' + esc(item[0]) + '</div><div class="col-7">' + esc(item[1]) + '</div></div>'; }).join('') +
        '</div>' + familyHtml + enrollmentHtml + history;
      document.getElementById('person-detail-title').textContent = person.display_name || labelForPerson(person);
      document.getElementById('person-detail-body').innerHTML = body;
      if (hasStudentRole) {
        fetch('/api/education/registration-directory/context/person/' + encodeURIComponent(person.id) + '/', {
          credentials: 'same-origin',
          headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
        }).then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) throw new Error(data.detail || data.error || 'سابقهٔ ثبت‌نام دریافت نشد.');
            return data;
          });
        }).then(function (data) {
          var preview = document.getElementById('person-enrollment-preview');
          if (!preview || preview.dataset.personId !== String(person.id)) return;
          var records = data.registrations && data.registrations.results || [];
          if (!records.length) { preview.textContent = 'برای این دانش‌آموز ثبت‌نامی ثبت نشده است.'; return; }
          preview.innerHTML = '<ul class="list-unstyled vstack gap-2 mb-0">' + records.slice(0, 3).map(function (record) {
            var target = record.class_group || record.offering || record.course;
            return '<li><a href="' + esc(target && target.url || enrollmentUrl) + '">' + esc(target && target.title || 'دورهٔ آموزشی') + '</a><span class="text-muted"> · ' + esc(record.status_label || 'نامشخص') + ' · ' + esc(record.date_label || record.date || '') + '</span></li>';
          }).join('') + '</ul>';
        }).catch(function () {
          var preview = document.getElementById('person-enrollment-preview');
          if (preview && preview.dataset.personId === String(person.id)) preview.textContent = 'سابقهٔ ثبت‌نام در دسترس نیست.';
        });
      }
      var footer = document.getElementById('person-detail-footer');
      footer.innerHTML = '<button type="button" class="btn btn-light" data-bs-dismiss="modal">بستن</button>';
      if (person.actions && person.actions.edit) {
        var edit = document.createElement('button'); edit.className = 'btn btn-outline-primary'; edit.innerHTML = '<i data-lucide="pencil" class="size-4 me-1"></i> ویرایش';
        edit.addEventListener('click', function () { openPersonEdit(person); }); footer.appendChild(edit);
      }
      if (ctx.directory === 'education' && ctx.can_create_user && hasStudentRole && !person.has_user) {
        var createUser = document.createElement('button');
        createUser.type = 'button';
        createUser.className = 'btn btn-primary';
        createUser.innerHTML = '<i data-lucide="user-plus" class="size-4 me-1"></i> ساخت حساب کاربری';
        createUser.addEventListener('click', function () {
          createUserForPerson(person, function () { openPersonDetail(row); }, function () { openPersonDetail(row); });
        });
        footer.appendChild(createUser);
      }
      if (person.actions && person.actions.delete) {
        var del = document.createElement('button'); del.className = 'btn btn-outline-danger'; del.innerHTML = '<i data-lucide="trash-2" class="size-4 me-1"></i> حذف';
        del.addEventListener('click', function () { window.penOpenDeleteModal({url: personResourceUrl(person.id, 'delete'), name: person.display_name || labelForPerson(person), code: person.national_code || person.id, onSuccess: function () { detailModal.hide(); loadList(apiUrlWithParams(), true); }}); }); footer.appendChild(del);
      }
      detailModal.show();
      if (window.penRenderIcons) window.penRenderIcons();
    }).catch(function (e) { toast(uiErrorMessage(e), 'danger'); });
  }

  function labelForPerson(person) { return ((person.first_name || '') + ' ' + (person.last_name || '')).trim() || 'فرد'; }

  var $detailEl = document.getElementById('person-detail-modal');
  var detailModal = $detailEl && window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance($detailEl) : null;
  var $editEl = document.getElementById('person-edit-modal');
  var editModal = $editEl && window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance($editEl) : null;
  var editingPerson = null;
  var initialEmployeeKind = null;

  function setEditRoleState(person) {
    var typeCodes = person.person_type_codes && person.person_type_codes.length
      ? person.person_type_codes : [person.person_type || ''];
    var userRoles = person.user_role_codes || [];
    var visibleRoles = typeCodes.join(' ');
    if (typeCodes.indexOf('employee') !== -1) {
      if (userRoles.indexOf('manager') !== -1) visibleRoles += ' manager';
      else if (userRoles.indexOf('supervisor') !== -1) visibleRoles += ' supervisor';
    }
    $editEl.querySelectorAll('[data-person-edit-role-fields]').forEach(function (wrapper) {
      var visible = roleMatchesAny(visibleRoles, wrapper.dataset.personEditRoleFields || '');
      wrapper.hidden = !visible;
      wrapper.querySelectorAll('input, select, textarea').forEach(function (field) {
        field.disabled = !visible;
      });
    });
    var employeeKind = document.getElementById('person-edit-employee-kind');
    initialEmployeeKind = userRoles.indexOf('supervisor') !== -1 ? 'supervisor' : 'ordinary';
    if (employeeKind) {
      employeeKind.value = initialEmployeeKind;
      employeeKind.disabled = !person.can_manage_supervisor_role || !person.has_user;
    }
    if (window.penRenderIcons) window.penRenderIcons();
  }

  function roleMatchesAny(current, expected) {
    var currentRoles = current.split(/\s+/);
    return expected.split(/\s+/).some(function (role) { return currentRoles.indexOf(role) !== -1; });
  }

  function setValue(id, value) {
    var el = document.getElementById(id);
    if (el) el.value = value == null ? '' : value;
  }

  function personHasType(person, code) {
    var types = person.person_type_codes && person.person_type_codes.length
      ? person.person_type_codes : [person.person_type || ''];
    return types.indexOf(code) !== -1;
  }

  function roleLabel(code) {
    return ({student: 'دانش‌آموز', teacher: 'مدرس', employee: 'کارمند', guardian: 'سرپرست',
      manager: 'مدیر', supervisor: 'سرپرست'})[code] || 'نامشخص';
  }

  function createUserForPerson(person, onSuccess, onCancel) {
    if (!person || ctx.directory !== 'education' || !ctx.can_create_user || person.has_user || !personHasType(person, 'student')) return;
    personRequest(person.id).then(function (fullPerson) {
      if (fullPerson.has_user) {
        toast('این دانش‌آموز از قبل حساب کاربری دارد.', 'info');
        return;
      }
      var missing = fullPerson.account_creation_missing_fields || [];
      pendingUserCreation = {person: fullPerson, onSuccess: onSuccess, onCancel: onCancel};
      var name = document.getElementById('person-create-user-name');
      var description = document.getElementById('person-create-user-description');
      var missingBox = document.getElementById('person-create-user-missing');
      var missingList = document.getElementById('person-create-user-missing-list');
      var error = document.getElementById('person-create-user-error');
      var submit = document.getElementById('person-create-user-submit');
      var edit = document.getElementById('person-create-user-edit');
      if (name) name.textContent = fullPerson.display_name || labelForPerson(fullPerson);
      if (error) { error.textContent = ''; error.hidden = true; }
      if (description) {
        description.hidden = !!missing.length;
        if (!missing.length) description.textContent = 'نام کاربری و گذرواژهٔ آغازین، کد ملی دانش‌آموز است.';
      }
      if (missingList) missingList.innerHTML = missing.map(function (field) { return '<li>' + esc(field) + '</li>'; }).join('');
      if (missingBox) missingBox.hidden = !missing.length;
      if (submit) submit.hidden = !!missing.length;
      if (edit) {
        edit.hidden = !missing.length;
        edit.onclick = function () {
          var pending = pendingUserCreation;
          if (!pending) return;
          pendingUserCreation = null;
          $createUserModalEl.addEventListener('hidden.bs.modal', function () {
            openPersonEdit(pending.person);
            $editEl.querySelectorAll('details.persons-optional-fields').forEach(function (details) { details.open = true; });
          }, {once: true});
          createUserModal.hide();
        };
      }
      var showConfirmation = function () { if (createUserModal) createUserModal.show(); };
      if (onCancel && detailModal && $detailEl.classList.contains('show')) {
        $detailEl.addEventListener('hidden.bs.modal', showConfirmation, {once: true});
        detailModal.hide();
      } else {
        showConfirmation();
      }
    }).catch(function (error) { toast(uiErrorMessage(error), 'danger'); });
  }

  function submitPendingUserCreation() {
    if (!pendingUserCreation || userCreationBusy) return;
    userCreationBusy = true;
    var pending = pendingUserCreation;
    var submit = document.getElementById('person-create-user-submit');
    var cancel = document.getElementById('person-create-user-cancel');
    var close = document.getElementById('person-create-user-close');
    var error = document.getElementById('person-create-user-error');
    $createUserModalEl.setAttribute('aria-busy', 'true');
    submit.disabled = true;
    cancel.disabled = true;
    close.disabled = true;
    submit.innerHTML = '<span class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span> در حال ساخت حساب…';
    fetch(personResourceUrl(pending.person.id, 'create-user'), {
      method: 'POST', credentials: 'same-origin',
      headers: Object.assign({'Content-Type': 'application/json'}, window.penCsrfHeader ? window.penCsrfHeader() : {}),
      body: JSON.stringify({}),
    }).then(function (response) {
      return response.json().then(function (body) {
        if (!response.ok) throw new Error(errorLines(body).join(' — '));
        return body;
      });
    }).then(function () {
      pendingUserCreation = null;
      userCreationBusy = false;
      resetUserCreationDialog();
      if (pending.onSuccess) {
        $createUserModalEl.addEventListener('hidden.bs.modal', function () { pending.onSuccess(); }, {once: true});
      }
      createUserModal.hide();
      toast('حساب فعال با موفقیت ساخته شد.', 'success');
      loadList(apiUrlWithParams(), true);
    }).catch(function (requestError) {
      userCreationBusy = false;
      resetUserCreationDialog();
      if (error) { error.textContent = uiErrorMessage(requestError); error.hidden = false; }
    });
  }

  function resetUserCreationDialog() {
    userCreationBusy = false;
    $createUserModalEl.removeAttribute('aria-busy');
    document.getElementById('person-create-user-submit').disabled = false;
    document.getElementById('person-create-user-cancel').disabled = false;
    document.getElementById('person-create-user-close').disabled = false;
    document.getElementById('person-create-user-submit').innerHTML = '<i data-lucide="user-plus" class="size-4 me-1" aria-hidden="true"></i> ساخت حساب';
    if (window.penRenderIcons) window.penRenderIcons();
  }

  function editRoleLabel(person) {
    var roles = person.user_role_codes || [];
    if (roles.indexOf('manager') !== -1) return 'مدیریت';
    if (roles.indexOf('supervisor') !== -1) return 'کارمند سرپرست';
    return person.person_types_display || person.person_type_display || roleLabel(person.person_type);
  }

  function openPersonEdit(person) {
    editingPerson = person;
    if (detailModal) detailModal.hide();
    [['person-edit-first-name', person.first_name], ['person-edit-last-name', person.last_name],
     ['person-edit-national-code', person.national_code || person.display_national_code], ['person-edit-person-type', editRoleLabel(person)],
     ['person-edit-mobile', person.mobile], ['person-edit-email', person.email], ['person-edit-birth-date', person.birth_date],
     ['person-edit-job-title', person.job_title]].forEach(function (item) { setValue(item[0], item[1]); });
    var nationalCodeInput = document.getElementById('person-edit-national-code');
    var mayCorrectNationalCode = !person.has_user &&
      (person.account_creation_missing_fields || []).indexOf('کد ملی معتبر') !== -1;
    if (nationalCodeInput) {
      nationalCodeInput.disabled = !mayCorrectNationalCode;
      nationalCodeInput.readOnly = !mayCorrectNationalCode;
    }
    setValue('person-edit-gender', person.gender || 'unspecified');
    var student = person.student_profile || {};
    [['person-edit-father-first', student.father_first_name], ['person-edit-father-last', student.father_last_name],
     ['person-edit-father-phone', student.father_phone], ['person-edit-mother-first', student.mother_first_name],
     ['person-edit-mother-last', student.mother_last_name], ['person-edit-mother-phone', student.mother_phone],
     ['person-edit-custody-note', student.custody_note]].forEach(function (item) { setValue(item[0], item[1]); });
    var staff = person.staff_profile || {};
    setValue('person-edit-specialization', staff.specialization);
    var custody = document.getElementById('person-edit-custody');
    if (custody) custody.checked = !!student.is_custody_case;
    document.getElementById('person-edit-active').checked = person.is_active !== false;
    var accountStatus = document.getElementById('person-edit-account-status');
    if (accountStatus) {
      accountStatus.textContent = person.has_user
        ? 'وضعیت حساب کاربری: ' + (person.user_is_active ? 'فعال' : 'غیرفعال')
        : 'حساب کاربری برای این شخص ثبت نشده است';
    }
    document.getElementById('person-edit-errors').hidden = true;
    $editEl.querySelectorAll('details.persons-optional-fields').forEach(function (details) { details.open = false; });
    var piiNote = document.getElementById('person-edit-pii-note');
    if (piiNote) {
      piiNote.hidden = ![person.mobile, person.email, student.father_phone, student.mother_phone]
        .some(function (value) { return typeof value === 'string' && value.indexOf('*') !== -1; });
    }
    setEditRoleState(person);
    if (editModal) editModal.show();
  }

  function addIfChanged(payload, key, inputId, originalValue) {
    var field = document.getElementById(inputId);
    if (!field || field.disabled) return;
    var value = field.value;
    var original = originalValue == null ? '' : String(originalValue);
    if (value !== original) payload[key] = value;
  }

  function pageLink(label, url, index) {
    var li = document.createElement('li');
    li.className = 'page-item';
    var button = document.createElement('button');
    button.type = 'button'; button.className = 'page-link';
    button.textContent = label; button.disabled = !url;
    button.addEventListener('click', function () { loadList(url, false, index); });
    li.appendChild(button); return li;
  }

  function renderPager(data) {
    $pager.innerHTML = '';
    $pager.appendChild(pageLink('صفحه اول', state.index > 0 ? apiUrlWithParams() : null, 0));
    $pager.appendChild(pageLink('قبلی', data.previous, Math.max(0, state.index - 1)));
    $pager.appendChild(pageLink('بعدی', data.next, state.index + 1));
    $pageStatus.textContent = (data.results || []).length ? 'صفحهٔ ' + window.persianNumbers(state.index + 1) +
      (data.next ? '' : ' · آخرین صفحه') : '';
  }

  function loadList(url, reset, index) {
    if (state.request) state.request.abort();
    var request = new AbortController();
    state.request = request;
    var targetIndex = reset ? 0 : (index == null ? state.index : index);
    $retry.hidden = true;
    $retry.onclick = function () { loadList(url, reset, targetIndex); };
    $pager.querySelectorAll('button').forEach(function (button) { button.disabled = true; });
    $table.setAttribute('aria-busy', 'true');
    $status.textContent = 'در حال بارگذاری…';
    $pageStatus.textContent = '';
    $tbody.innerHTML = '<tr><td colspan="5"><div class="pen-loading">در حال بارگذاری…</div></td></tr>';
    return fetch(url, {
      credentials: 'same-origin', signal: request.signal,
      headers: window.penCsrfHeader ? window.penCsrfHeader() : {},
    }).then(function (response) {
      if (!response.ok) throw new Error('دریافت فهرست ناموفق بود.');
      return response.json();
    }).then(function (data) {
      if (state.request !== request) return;
      state.index = targetIndex;
      renderRows(data); renderPager(data);
      $status.textContent = (data.results || []).length
        ? window.persianNumbers(data.results.length) + ' نفر در این صفحه' : 'نتیجه‌ای پیدا نشد.';
    }).catch(function (error) {
      if (state.request !== request || error.name === 'AbortError') return;
      $tbody.innerHTML = '<tr><td colspan="5"><div class="pen-empty text-danger">بارگذاری فهرست ناموفق بود.</div></td></tr>';
      $status.textContent = 'اتصال را بررسی کنید و دوباره تلاش کنید.';
      $retry.hidden = false;
    }).finally(function () {
      if (state.request !== request) return;
      state.request = null;
      $table.setAttribute('aria-busy', 'false');
    });
  }

  function clearFormErrors() {
    var box = document.getElementById('person-form-errors');
    var list = document.getElementById('person-form-error-list');
    if (box) box.hidden = true;
    if (list) list.innerHTML = '';
    if (!$createForm) return;
    $createForm.querySelectorAll('.is-invalid').forEach(function (field) {
      field.classList.remove('is-invalid');
      field.removeAttribute('aria-invalid');
      var described = (field.getAttribute('aria-describedby') || '').split(/\s+/).filter(function (id) {
        return id && !/-error$/.test(id);
      });
      if (described.length) field.setAttribute('aria-describedby', described.join(' '));
      else field.removeAttribute('aria-describedby');
    });
    $createForm.querySelectorAll('[data-person-error]').forEach(function (node) { node.remove(); });
  }

  function showFormErrors(errors) {
    clearFormErrors();
    var box = document.getElementById('person-form-errors');
    var list = document.getElementById('person-form-error-list');
    var all = errorLines(errors);
    list.innerHTML = all.map(function (line) { return '<li>' + esc(line) + '</li>'; }).join('');
    box.hidden = false;
    if (errors.non_field_errors && document.getElementById('id_target').value === 'student') {
      var studentDetails = document.querySelector('#person-step-two [data-person-role-fields="student"] details');
      if (studentDetails) studentDetails.open = true;
    }
    Object.keys(errors || {}).forEach(function (key) {
      if (key === 'non_field_errors') return;
      var field = document.getElementById('id_' + key);
      if (!field) return;
      var disclosure = field.closest('details');
      if (disclosure) disclosure.open = true;
      field.classList.add('is-invalid');
      field.setAttribute('aria-invalid', 'true');
      var errorId = 'person-error-' + key;
      var node = document.createElement('div');
      node.id = errorId;
      node.dataset.personError = key;
      node.className = 'invalid-feedback d-block';
      node.textContent = (Array.isArray(errors[key]) ? errors[key] : [errors[key]]).join(' ');
      field.insertAdjacentElement('afterend', node);
      var described = (field.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
      if (described.indexOf(errorId) === -1) described.push(errorId);
      field.setAttribute('aria-describedby', described.join(' '));
    });
    if (errors.target) showStep(1);
    box.focus();
  }

  function roleMatches(value, roles) {
    return roles.split(/\s+/).indexOf(value) !== -1;
  }

  function setRequired(name, required) {
    var field = document.getElementById('id_' + name);
    if (!field) return;
    field.required = required;
  }

  function applyRoleState() {
    if (!$createForm) return;
    var target = document.getElementById('id_target').value;
    $createForm.querySelectorAll('[data-person-role-fields]').forEach(function (wrapper) {
      var visible = target && roleMatches(target, wrapper.dataset.personRoleFields || '');
      wrapper.hidden = !visible;
      wrapper.querySelectorAll('input, select, textarea').forEach(function (field) {
        field.disabled = !visible;
      });
    });
    setRequired('employee_kind', target === 'employee');
    setRequired('job_title', target === 'employee' || target === 'manager');
    setRequired('password', target === 'employee' || target === 'manager');
    var father = document.getElementById('id_father_phone_number');
    var mother = document.getElementById('id_mother_phone_number');
    if (target !== 'student') {
      if (father) father.setCustomValidity('');
      if (mother) mother.setCustomValidity('');
    }
    if (window.penRenderIcons) window.penRenderIcons();
  }

  function showStep(step) {
    if (!$createForm) return;
    var one = document.getElementById('person-step-one');
    var two = document.getElementById('person-step-two');
    var back = document.getElementById('person-step-back');
    var next = document.getElementById('person-step-next');
    var submit = document.getElementById('person-submit');
    one.hidden = step !== 1;
    two.hidden = step !== 2;
    back.hidden = step !== 2;
    next.hidden = step !== 1;
    submit.hidden = step !== 2;
    document.getElementById('person-progress').textContent = 'مرحلهٔ ' + window.persianNumbers(step) + ' از ۲';
    if (step === 2) applyRoleState();
  }

  function validateParents() {
    var target = document.getElementById('id_target').value;
    if (target !== 'student') return true;
    var father = document.getElementById('id_father_phone_number');
    var mother = document.getElementById('id_mother_phone_number');
    var fatherValue = father.value.trim();
    var motherValue = mother.value.trim();
    if (!fatherValue && !motherValue) {
      father.setCustomValidity('حداقل یکی از شماره موبایل پدر یا مادر الزامی است.');
      mother.setCustomValidity('حداقل یکی از شماره موبایل پدر یا مادر الزامی است.');
      return false;
    }
    father.setCustomValidity('');
    mother.setCustomValidity('');
    return true;
  }

  function resetWizard() {
    if (!$createForm) return;
    $createForm.reset();
    $createForm.querySelectorAll('details.persons-optional-fields').forEach(function (details) { details.open = false; });
    clearFormErrors();
    showStep(1);
    applyRoleState();
    $createForm.setAttribute('aria-busy', 'false');
    document.getElementById('person-submit').disabled = false;
  }

  function submitWizard(event) {
    event.preventDefault();
    if ($createForm.dataset.submitting === 'true') return;
    clearFormErrors();
    validateParents();
    if (!$createForm.checkValidity()) {
      var invalid = $createForm.querySelector(':invalid');
      if (invalid && invalid.closest('details')) invalid.closest('details').open = true;
      $createForm.reportValidity();
      return;
    }
    $createForm.dataset.submitting = 'true';
    var submit = document.getElementById('person-submit');
    submit.disabled = true;
    submit.setAttribute('aria-busy', 'true');
    $createForm.setAttribute('aria-busy', 'true');
    fetch($createForm.action || ctx.create_url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: Object.assign({ 'X-Requested-With': 'XMLHttpRequest' }, window.penCsrfHeader ? window.penCsrfHeader() : {}),
      body: new FormData($createForm),
    })
      .then(function (response) {
        return response.json().then(function (body) { return { ok: response.ok, body: body }; });
      })
      .then(function (result) {
        if (!result.ok) {
          showFormErrors(result.body.errors || result.body);
          return;
        }
        toast(result.body.message || 'فرد با موفقیت ثبت شد ✓', 'success');
        if (modal) modal.hide();
        resetWizard();
        var listUrl = apiUrlWithParams();
        loadList(listUrl, true);
      })
      .catch(function () { showFormErrors({ non_field_errors: ['ارتباط با سرور برقرار نشد.'] }); })
      .finally(function () {
        $createForm.dataset.submitting = 'false';
        submit.disabled = false;
        submit.removeAttribute('aria-busy');
        $createForm.setAttribute('aria-busy', 'false');
      });
  }

  function syncGroups() {
    document.querySelectorAll('[data-person-group]').forEach(function (button) {
      var active = button.dataset.personGroup === $filters.elements.role.value;
      button.setAttribute('aria-pressed', String(active));
    });
    var advanced = document.getElementById('person-more-filters');
    var count = Array.from($filters.elements).filter(function (field) {
      return ['national_code', 'first_name', 'last_name', 'is_active'].indexOf(field.name) !== -1 && field.value.trim();
    }).length;
    if ($filters.elements.ordering.value !== '-created_at') count += 1;
    if ($filters.elements.page_size.value !== '50') count += 1;
    if ($filters.elements.role.value === 'manager') count += 1;
    var badge = document.getElementById('person-filter-count');
    badge.hidden = !count;
    badge.textContent = count ? window.persianNumbers(count) : '';
    if (advanced && count) advanced.dataset.hasFilters = 'true';
    else if (advanced) delete advanced.dataset.hasFilters;
  }

  function applyFilters() {
    clearTimeout(searchTimer);
    if (!$filters.reportValidity()) return;
    syncGroups();
    if (document.getElementById('person-more-filters').dataset.hasFilters) document.getElementById('person-more-filters').open = true;
    var url = apiUrlWithParams();
    var browserUrl = new URL(window.location.href);
    browserUrl.search = new URL(url).search;
    window.history.replaceState({}, '', browserUrl.toString());
    loadList(url, true);
  }

  if ($filters) {
    var saved = new URLSearchParams(window.location.search);
    Array.from($filters.elements).forEach(function (field) {
      if (!field.name || !saved.has(field.name)) return;
      var value = saved.get(field.name);
      if (field.tagName === 'SELECT' && !Array.from(field.options).some(function (option) { return option.value === value; })) return;
      field.value = value;
    });
    syncGroups();
    if (document.getElementById('person-more-filters').dataset.hasFilters) document.getElementById('person-more-filters').open = true;
    $filters.addEventListener('submit', function (event) { event.preventDefault(); applyFilters(); });
    $filters.addEventListener('change', function (event) {
      if (event.target.tagName === 'SELECT') applyFilters();
    });
    document.getElementById('person-filter-search').addEventListener('input', function (event) {
      clearTimeout(searchTimer);
      if (!event.isComposing) searchTimer = setTimeout(applyFilters, 350);
    });
    document.getElementById('person-filter-reset').addEventListener('click', function () { $filters.reset(); applyFilters(); });
    document.querySelectorAll('[data-person-group]').forEach(function (button) {
      button.addEventListener('click', function () {
        $filters.elements.role.value = button.dataset.personGroup; applyFilters();
      });
    });
  }

  if ($createForm) {
    var target = document.getElementById('id_target');
    target.addEventListener('change', function () { clearFormErrors(); applyRoleState(); });
    document.getElementById('person-step-next').addEventListener('click', function () {
      if (!target.checkValidity()) { target.reportValidity(); return; }
      showStep(2);
    });
    document.getElementById('person-step-back').addEventListener('click', function () { showStep(1); });
    $createForm.addEventListener('submit', submitWizard);
    var add = document.getElementById('person-add');
    if (add && modal) add.addEventListener('click', function () { resetWizard(); modal.show(); });
    ['id_father_phone_number', 'id_mother_phone_number'].forEach(function (id) {
      var field = document.getElementById(id);
      if (field) field.addEventListener('input', validateParents);
    });
    showStep(1);
    applyRoleState();
  }

  var $editForm = document.getElementById('person-edit-form');
  if ($editForm) {
    $editForm.addEventListener('submit', function (event) {
      event.preventDefault();
      if (!editingPerson) return;
      var payload = {};
      addIfChanged(payload, 'first_name', 'person-edit-first-name', editingPerson.first_name);
      addIfChanged(payload, 'last_name', 'person-edit-last-name', editingPerson.last_name);
      addIfChanged(payload, 'national_code', 'person-edit-national-code', editingPerson.national_code);
      addIfChanged(payload, 'mobile', 'person-edit-mobile', editingPerson.mobile);
      addIfChanged(payload, 'email', 'person-edit-email', editingPerson.email);
      addIfChanged(payload, 'gender', 'person-edit-gender', editingPerson.gender || 'unspecified');
      addIfChanged(payload, 'birth_date', 'person-edit-birth-date', editingPerson.birth_date);
      addIfChanged(payload, 'job_title', 'person-edit-job-title', editingPerson.job_title);
      var active = document.getElementById('person-edit-active').checked;
      if (active !== (editingPerson.is_active !== false)) payload.is_active = active;
      var selectedEmployeeKind = document.getElementById('person-edit-employee-kind').value;
      if (selectedEmployeeKind !== initialEmployeeKind) payload.employee_kind = selectedEmployeeKind;
      if (personHasType(editingPerson, 'student')) {
        var profile = editingPerson.student_profile || {};
        var studentData = {};
        addIfChanged(studentData, 'father_first_name', 'person-edit-father-first', profile.father_first_name);
        addIfChanged(studentData, 'father_last_name', 'person-edit-father-last', profile.father_last_name);
        addIfChanged(studentData, 'father_phone', 'person-edit-father-phone', profile.father_phone);
        addIfChanged(studentData, 'mother_first_name', 'person-edit-mother-first', profile.mother_first_name);
        addIfChanged(studentData, 'mother_last_name', 'person-edit-mother-last', profile.mother_last_name);
        addIfChanged(studentData, 'mother_phone', 'person-edit-mother-phone', profile.mother_phone);
        var custody = document.getElementById('person-edit-custody').checked;
        if (custody !== !!profile.is_custody_case) studentData.is_custody_case = custody;
        addIfChanged(studentData, 'custody_note', 'person-edit-custody-note', profile.custody_note);
        if (Object.keys(studentData).length) payload.student_profile = studentData;
      }
      if (personHasType(editingPerson, 'teacher') || personHasType(editingPerson, 'employee')) {
        var staffData = {};
        addIfChanged(staffData, 'specialization', 'person-edit-specialization', (editingPerson.staff_profile || {}).specialization);
        if (Object.keys(staffData).length) payload.staff_profile = staffData;
      }
      fetch(personResourceUrl(editingPerson.id), {
        method: 'PATCH', credentials: 'same-origin',
        headers: Object.assign({'Content-Type': 'application/json'}, window.penCsrfHeader ? window.penCsrfHeader() : {}),
        body: JSON.stringify(payload),
      }).then(function (response) {
        return response.json().then(function (body) { if (!response.ok) throw new Error(errorLines(body).join(' — ')); return body; });
      }).then(function () {
        if (editModal) editModal.hide();
        toast('اطلاعات فرد به‌روز شد ✓', 'success');
        loadList(apiUrlWithParams(), true);
      }).catch(function (e) {
        $editEl.querySelectorAll('details.persons-optional-fields').forEach(function (details) { details.open = true; });
        var box = document.getElementById('person-edit-errors'); box.textContent = uiErrorMessage(e); box.hidden = false;
      });
    });
  }

  var $createUserSubmit = document.getElementById('person-create-user-submit');
  if ($createUserSubmit) $createUserSubmit.addEventListener('click', submitPendingUserCreation);
  if ($createUserModalEl) {
    $createUserModalEl.addEventListener('hidden.bs.modal', function () {
      var cancelled = pendingUserCreation;
      pendingUserCreation = null;
      resetUserCreationDialog();
      if (cancelled && cancelled.onCancel) cancelled.onCancel();
    });
  }

  var initialUrl = apiUrlWithParams();
  loadList(initialUrl, true);
  if (window.penRenderIcons) window.penRenderIcons();
})();
