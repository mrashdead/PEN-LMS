const API = {
  async request(method, url, body) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      credentials: 'same-origin',
    };
    if (body && method !== 'GET') opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    if (res.status === 403) { window.location.href = '/dashboard/login/'; return; }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(formatApiError(err, res.statusText));
    }
    if (res.status === 204) return null;
    return res.json();
  },
  get(url) { return this.request('GET', url); },
  post(url, body) { return this.request('POST', url, body); },
  patch(url, body) { return this.request('PATCH', url, body); },
  del(url) { return this.request('DELETE', url); },

  // Persons
  persons: {
    list(params) { return API.get('/api/persons/?' + new URLSearchParams(params)); },
    get(id) { return API.get(`/api/persons/${id}/`); },
    create(data) { return API.post('/api/persons/', data); },
    update(id, data) { return API.patch(`/api/persons/${id}/`, data); },
    createUser(personId, data) { return API.post(`/api/persons/${personId}/create-user/`, data); },
  },

  // Workflow
  workflow: {
    instances(params) { return API.get('/api/workflow/instances/?' + new URLSearchParams(params)); },
    get(id) { return API.get(`/api/workflow/instances/${id}/`); },
    create(data) { return API.post('/api/workflow/instances/', data); },
    transitions(id) { return API.get(`/api/workflow/instances/${id}/available-transitions/`); },
    execute(id, data) { return API.post(`/api/workflow/instances/${id}/execute-transition/`, data); },
    cancel(id, data) { return API.post(`/api/workflow/instances/${id}/cancel/`, data); },
    logs(id) { return API.get(`/api/workflow/instances/${id}/logs/`); },
  },

  // Tasks
  tasks: {
    list(params) { return API.get('/api/tasks/?' + new URLSearchParams(params)); },
    get(id) { return API.get(`/api/tasks/${id}/`); },
  },

  // Academics
  academics: {
    terms(params) { return API.get('/api/academics/terms/?' + new URLSearchParams(params)); },
    createTerm(data) { return API.post('/api/academics/terms/', data); },
    getTerm(id) { return API.get(`/api/academics/terms/${id}/`); },
    activateTerm(id) { return API.post(`/api/academics/terms/${id}/activate/`); },
    classGroups(params) { return API.get('/api/academics/class-groups/?' + new URLSearchParams(params)); },
    createClassGroup(data) { return API.post('/api/academics/class-groups/', data); },
    getClassGroup(id) { return API.get(`/api/academics/class-groups/${id}/`); },
    enrollments(params) { return API.get('/api/academics/enrollments/?' + new URLSearchParams(params)); },
    createEnrollment(data) { return API.post('/api/academics/enrollments/', data); },
  },
};

function formatApiError(error, fallback = 'خطای نامشخص') {
  if (typeof error === 'string') return error;
  if (!error || typeof error !== 'object') return fallback;

  const messages = [];
  for (const [field, value] of Object.entries(error)) {
    const items = Array.isArray(value) ? value : [value];
    for (const item of items) {
      if (item === null || item === undefined || item === '') continue;
      messages.push(field === 'non_field_errors' ? String(item) : `${field}: ${item}`);
    }
  }
  return messages.join('\n') || fallback;
}

function getCookie(name) {
  let c = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return c ? c[2] : '';
}

function persianNumbers(s) {
  const d = {'0':'۰','1':'۱','2':'۲','3':'۳','4':'۴','5':'۵','6':'۶','7':'۷','8':'۸','9':'۹'};
  return String(s).replace(/[0-9]/g, c => d[c]);
}

function formatDate(s) {
  if (!s) return '—';
  return s.replace(/[0-9]/g, c => '۰۱۲۳۴۵۶۷۸۹'[c]);
}

function htmlEscape(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
