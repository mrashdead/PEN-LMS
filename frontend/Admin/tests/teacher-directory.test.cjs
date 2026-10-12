const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = {module: {exports: {}}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/enrollment-directory.js'), 'utf8'), context);
const { renderTeaching, teachingOfferingMarkup, teachingClassMarkup } = context.module.exports;

test('management teaching profile separates running and preregistration and preserves empty states', () => {
  const elements = new Map();
  const doc = { getElementById(id) { if (!elements.has(id)) elements.set(id, {innerHTML: '', hidden: true}); return elements.get(id); } };
  renderTeaching(doc, {teaching: {summary: {offerings: 2, running: 1, preregistration: 1, classes: 0}, offerings: [
    {title: 'دوره جاری', status: 'running', status_label: 'در حال برگزاری', instructor: {name: 'مدرس الف'}},
    {title: 'دوره آینده', status: 'open', status_label: 'پیش‌ثبت‌نام'}
  ]}});
  const html = elements.get('registration-teaching-offerings').innerHTML;
  assert.match(html, /دوره‌های در حال برگزاری \(1\)/);
  assert.match(html, /دوره‌های پیش‌ثبت‌نام \(1\)/);
  assert.match(html, /سایر وضعیت‌های دوره \(0\)/);
  assert.match(html, /مدرس تعیین نشده/);
  assert.match(elements.get('registration-teaching-classes').innerHTML, /کلاسی به این مدرس اختصاص داده نشده/);
  assert.equal(elements.get('registration-teaching-content').hidden, false);
});

test('teaching rows escape content, reject unsafe URLs and distinguish session assignment', () => {
  const offering = teachingOfferingMarkup({title: '<script>', url: 'javascript:alert(1)', course: '<دوره>', assignment_label: 'مدرس جلسات', schedule: {days: ['sat'], start: '10:00', end: '12:00'}, location: '<محل>'});
  assert.match(offering, /&lt;script&gt;/);
  assert.ok(!offering.includes('javascript:'));
  assert.match(offering, /ارتباط مدرس: مدرس جلسات/);
  assert.match(offering, /شنبه/);
  assert.match(offering, /10:00–12:00/);
  const group = teachingClassMarkup({title: 'کلاس', class_teacher: {name: '<مدرس>'}, is_active: false, status_label: 'غیرفعال', schedule: {days: ['شنبه'], start_time: '08:00', end_time: '09:00'}});
  assert.match(group, /&lt;مدرس&gt;/);
  assert.match(group, /غیرفعال/);
  assert.match(group, /08:00–09:00/);
});
