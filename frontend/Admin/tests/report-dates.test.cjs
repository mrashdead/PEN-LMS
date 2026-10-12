const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
function calendar() {
  const window = {};
  const context = {window, document: {readyState: 'loading', addEventListener() {}}, MutationObserver: class {observe() {}}, Date, Intl};
  for (const file of ['pen-jalali.js', 'report-dates.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../src/assets/pen/js', file), 'utf8'), context);
  return {window, context, dates: window.penReportDates};
}
test('daily defaults to supplied project day and week spans seven days', () => {
  const {dates} = calendar();
  assert.equal(dates.range('daily', '2026-10-11').start, '2026-10-11');
  assert.equal(dates.range('weekly', '2026-10-11').start, '2026-10-05');
  assert.equal(dates.range('weekly', '2026-10-11').end, '2026-10-11');
});
test('Mehr selection and partial current month use the Jalali calendar', () => {
  const {dates} = calendar();
  assert.equal(dates.months[6], 'مهر');
  assert.equal(dates.range('monthly', '2026-11-15', 1405, 7).start, '2026-09-23');
  assert.equal(dates.range('monthly', '2026-11-15', 1405, 7).end, '2026-10-22');
  assert.equal(dates.range('monthly', '2026-10-11', 1405, 7).end, '2026-10-11');
  assert.equal(dates.range('month_week', '2026-11-15', 1405, 7, 5).start, '2026-10-21');
  assert.equal(dates.range('month_week', '2026-11-15', 1405, 7, 5).end, '2026-10-22');
});
test('date input accepts Persian, Arabic, and ISO digits and rejects impossible days', () => {
  const {dates} = calendar();
  for (const date of ['۱۴۰۵/۰۷/۱۹', '١٤٠٥/٠٧/١٩', '2026-10-11']) assert.equal(dates.iso(date), '2026-10-11');
  for (const date of ['1405/07/31', '1404/12/30', '2026-02-30', 'wrong', '']) assert.throws(() => dates.iso(date), /تاریخ/);
  assert.throws(() => dates.range('monthly', '2026-10-11', 1405, 8), /آینده/);
});
test('teacher form preserves manual range on submit and on editing a draft', async () => {
  const {window, context} = calendar();
  const nodes = new Map();
  function node(id) {
    if (!nodes.has(id)) nodes.set(id, {value: '', dataset: {}, children: [], listeners: {}, append(...children) {this.children.push(...children);}, replaceChildren(...children) {this.children = children;}, addEventListener(event, fn) {this.listeners[event] = fn;}, setAttribute() {}, removeAttribute() {}, focus() {}});
    return nodes.get(id);
  }
  node('progress-teacher').dataset.systemDate = '2026-10-11';
  const fields = ['period', 'period_start', 'period_end', 'start_time', 'end_time', 'title', 'summary', 'strengths', 'improvements', 'homework', 'next_steps'];
  const elements = fields.map(field => node('field-' + field)); fields.forEach((field, i) => {elements[field] = elements[i];});
  elements.period_start = node('progress-start'); elements.period_end = node('progress-end');
  node('progress-form').elements = elements;
  context.document = {getElementById(id) {return id === 'progress-learner' ? null : node(id);}, createElement(tag) {return node('new-' + tag + '-' + Math.random());}, addEventListener() {}};
  context.Option = function (name, value) {this.textContent = name; this.value = value;};
  context.location = {search: '', pathname: '/workspace/teacher/progress-reports/'};
  context.URLSearchParams = URLSearchParams;
  window.addEventListener = () => {};
  window.confirm = () => true;
  const requests = [];
  context.fetch = async (url, options) => {
    requests.push({url, options});
    const report = {id: 'report', status: 'draft', period: 'daily', period_start: '۱۴۰۵/۰۷/۱۸', period_end: '۱۴۰۵/۰۷/۱۸', start_time: '09:00:00', end_time: '10:00:00', title: 'draft'};
    return {ok: true, json: async () => url.includes('teacher/classes') ? {results: []} : options.method ? report : {results: [report]}};
  };
  let source = fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/progress-reports.js'), 'utf8');
  source = source.replace("  api('/api/education/teacher/classes/')", "  window.testReport = {loadHistory, setActive() { activeClass = 'class'; activeStudent = 'student'; }};\n  api('/api/education/teacher/classes/')");
  vm.runInNewContext(source, context);
  window.testReport.setActive();
  await window.testReport.loadHistory();
  const article = node('progress-history').children[0];
  article.children[0].children.at(-1).listeners.click();
  assert.equal(node('progress-range-mode').value, 'custom');
  assert.equal(elements.period_start.value, '۱۴۰۵/۰۷/۱۸');
  elements.title.value = 'edited';
  await node('progress-form').listeners.submit({preventDefault() {}, submitter: node('progress-save')});
  const sent = JSON.parse(requests.find(r => r.options.method === 'PATCH').options.body);
  assert.equal(sent.period_start, '۱۴۰۵/۰۷/۱۸');
  assert.equal(sent.start_time, '09:00:00');
  assert.equal(sent.period_end, '۱۴۰۵/۰۷/۱۸');
});
test('dashboard preserves calendar selections, manual times and invalid date text for server validation', () => {
  const nodes = new Map();
  const node = id => {if (!nodes.has(id)) nodes.set(id, {value: '', textContent: '{}', hidden: false}); return nodes.get(id);};
  const context = {window: {location: {search: ''}}, document: {getElementById: node, querySelector: () => ({dataset: {reportPage: 'financial'}})}, URLSearchParams};
  let source = fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/reports-dashboard.js'), 'utf8');
  source = source.slice(0, source.indexOf('  var monthInput =')) + "  window.filters = {currentQuery, applyQueryToForm, period(value) {state.period = value;}}; })();";
  vm.runInNewContext(source, context);
  context.window.filters.period('month');
  node('report-year').value = '1405'; node('report-month').value = '7'; node('report-week').value = '1';
  let query = context.window.filters.currentQuery();
  assert.equal(query.get('month'), '7'); assert.equal(query.get('year'), '1405'); assert.equal(query.get('period'), 'month');
  context.window.filters.applyQueryToForm(new URLSearchParams({from: '1405-07-19', to: '۱۴۰۵/۰۷/۱۹', start_time: '09:00', end_time: '10:00'}));
  query = context.window.filters.currentQuery();
  assert.equal(query.get('from'), '1405-07-19'); assert.equal(query.get('to'), '۱۴۰۵/۰۷/۱۹'); assert.equal(query.get('start_time'), '09:00'); assert.equal(query.get('end_time'), '10:00');
  assert.equal(query.get('period'), null);
  node('report-from').value = '1405/07/31';
  assert.equal(context.window.filters.currentQuery().get('from'), '1405/07/31');
});
