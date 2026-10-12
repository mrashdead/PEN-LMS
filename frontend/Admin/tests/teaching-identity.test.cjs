const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function renderers(file, functions) {
  const elements = new Map();
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, { innerHTML: '', textContent: '', value: '', addEventListener() {}, querySelectorAll() { return []; } });
      return elements.get(id);
    },
    querySelectorAll() { return []; },
    addEventListener() {}
  };
  const window = {
    htmlEscape: (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]),
    persianNumbers: (value) => String(value),
  };
  const source = fs.readFileSync(path.join(__dirname, '../src/assets/pen/js', file), 'utf8');
  vm.runInNewContext(source.replace(/\}\)\(\);\s*$/, `window.renderers = {${functions.join(',')}}; })();`), { window, document });
  return { elements, ...window.renderers };
}

test('teacher courses have distinct running, preregistration and other groups', () => {
  const ui = renderers('teacher-dashboard.js', ['renderClasses', 'renderStandaloneClasses']);
  ui.renderClasses([
    { id: 'running', title: 'دوره جاری', status: 'running', status_label: 'در حال برگزاری', instructor: { name: '<مدرس>' }, can_manage: false, sessions: [{id: 'session', number: 1, date: '2026-11-01', start: '10:00', end: '11:00'}] },
    { id: 'open', title: 'دوره آینده', status: 'open', status_label: 'پیش‌ثبت‌نام' },
    { id: 'finished', title: 'دوره قدیمی', status: 'finished', status_label: 'پایان‌یافته', is_active: false }
  ]);
  const html = ui.elements.get('td-classes').innerHTML;
  assert.match(html, /در حال برگزاری \(1\)/);
  assert.match(html, /پیش‌ثبت‌نام \(1\)/);
  assert.match(html, /سایر وضعیت‌ها \(1\)/);
  assert.match(html, /پایان‌یافته · غیرفعال/);
  assert.match(html, /&lt;مدرس&gt;/);
  assert.ok(!html.includes("attendance/?class=running"));
  assert.match(html, /مدرس تعیین نشده/);
  ui.renderStandaloneClasses([{ name: 'کلاس مستقل', code: 'A', term: 'پاییز', is_active: true, schedule: { days: ['شنبه'], start_time: '10:00', end_time: '11:00' } }]);
  assert.match(ui.elements.get('td-standalone-classes').innerHTML, /شنبه · 10:00 تا 11:00/);
});

test('learner weekly schedule shows the session teacher and a missing-teacher state', () => {
  const ui = renderers('learner-portal.js', ['renderSchedule']);
  ui.renderSchedule({days: [{date: '2026-10-12', sessions: [
    {title: 'درس من', teacher: '<مدرس جلسه>', start: '10:00', end: '11:00'},
    {title: 'درس دیگر', teacher: '', start: '11:00', end: '12:00'}
  ]}]});
  const html = ui.elements.get('lp-schedule').innerHTML;
  assert.match(html, /<th scope="col">استاد<\/th>/);
  assert.match(html, /&lt;مدرس جلسه&gt;/);
  assert.match(html, /مدرس تعیین نشده/);
  assert.ok(!html.includes('<مدرس جلسه>'));
  ui.renderSchedule({days: []});
  assert.match(ui.elements.get('lp-schedule').innerHTML, /جلسه‌ای در برنامه ثبت نشده/);
});

test('registration directory renders teacher identity as escaped text', () => {
  const context = { module: { exports: {} } };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/enrollment-directory.js'), 'utf8'), context);
  const render = context.module.exports.rowMarkup;
  assert.match(render({ teacher: { name: '<مدرس>' } }), /مدرس: &lt;مدرس&gt;/);
  assert.match(render({}), /مدرس تعیین نشده/);
});
