const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const window = {};
function Input() {}
Object.defineProperty(Input.prototype, 'value', {get() { return ''; }, set() {}});
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/pen-time.js'), 'utf8'), {
  window, HTMLInputElement: Input, WeakMap, document: {readyState: 'loading', addEventListener() {}}
});
const time = window.penTime;
test('accepts Persian, Arabic and Latin digits with the same 24-hour value', () => {
  for (const value of ['۱۴:۳۷', '١٤:٣٧', '14:37']) assert.equal(time.format(time.parse(value)), '14:37');
  assert.equal(time.format(time.parse('9:05')), '09:05');
});
test('accepts midnight and the final minute without rounding', () => {
  for (const value of ['00:00', '00:01', '12:00', '23:59', '14:37']) assert.equal(time.format(time.parse(value)), value);
});
test('rejects out-of-range and incomplete input instead of silently changing it', () => {
  for (const value of ['', '24:00', '23:60', '09:', ':15', '09:5', '9', '9:5 AM', 'wrong', '-1:30', '09:00:60']) assert.equal(time.parse(value), null, value);
});
test('preserves existing seconds in edited values', () => {
  for (const value of ['09:12:00', '09:12:37', '23:59:59']) assert.equal(time.format(time.parse(value)), value);
});
