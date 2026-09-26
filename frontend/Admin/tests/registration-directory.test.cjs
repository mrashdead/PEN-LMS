const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = { module: { exports: {} } };
const source = fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/enrollment-directory.js'), 'utf8');
vm.runInNewContext(source, context);
const { rowMarkup, rowsMarkup, statusMarkup } = context.module.exports;

test('registration rows escape identity text and reject non-workspace links', () => {
  const markup = rowMarkup({
    student: { name: '<img src=x onerror=alert(1)>', url: 'javascript:alert(1)', student_code: 'ST-1' },
    course: { title: 'ریاضی', url: '/workspace/enrollments/courses/course-id/' },
    offering: { title: 'نوبت بهار', code: 'OF-1', url: '/workspace/enrollments/offerings/offering-id/' },
    class_group: { title: 'گروه الف', code: 'A-1', url: '/workspace/enrollments/classes/class-id/', term: 'بهار' },
    status: 'confirmed', status_label: 'تأییدشده', date: '2026-09-26', date_label: '۱۴۰۵/۰۷/۰۴',
    url: '/workspace/enrollments/records/offering/record-id/'
  });

  assert.ok(markup.includes('&lt;img src=x onerror=alert(1)&gt;'));
  assert.ok(!markup.includes('javascript:'));
  assert.ok(markup.includes('href="/workspace/enrollments/courses/course-id/"'));
  assert.ok(markup.includes('تأییدشده'));
});

test('unknown statuses stay text-only and empty rosters have a clear state', () => {
  const badge = statusMarkup({ status: '<script>', status_label: '<script>' });
  assert.ok(!badge.includes('<script>'));
  assert.ok(badge.includes('&lt;script&gt;'));
  assert.ok(rowsMarkup([], 6).includes('موردی مطابق این فیلترها پیدا نشد'));
});

test('record links are rendered only for local enrollment pages', () => {
  const markup = rowsMarkup([{
    student: { name: 'آرمان', url: '/workspace/enrollments/people/student-id/' },
    course: null,
    offering: null,
    class_group: null,
    status: 'pending',
    status_label: 'در انتظار',
    date_label: '۱۴۰۵/۰۷/۰۴',
    url: 'https://attacker.example/record'
  }], 6);

  assert.ok(markup.includes('href="/workspace/enrollments/people/student-id/"'));
  assert.ok(!markup.includes('attacker.example'));
  assert.ok(markup.includes('تخصیص کلاس نشده'));
});