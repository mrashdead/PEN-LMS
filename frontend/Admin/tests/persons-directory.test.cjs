const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

// Exercise the production request coordinator with deliberately out-of-order responses.
const source = fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/persons.js'), 'utf8');
const template = fs.readFileSync(path.join(__dirname, '../pen-templates/persons.html'), 'utf8');
const coordinator = source.slice(source.indexOf('  function loadList('), source.indexOf('  function clearFormErrors('));
function setup() {
  const pending = [];
  const table = { setAttribute(key, value) { this[key] = value; } };
  const context = {
    state: { index: 0, request: null }, $retry: {}, $table: table,
    $status: {}, $pageStatus: {}, $tbody: {},
    $pager: { querySelectorAll: () => [] }, AbortController,
    window: { persianNumbers: String },
    fetch(url, options) { return new Promise((resolve, reject) => pending.push({ url, options, resolve, reject })); },
    renderRows(data) { context.rendered = data; },
    renderPager() {},
  };
  vm.createContext(context);
  vm.runInContext(coordinator, context);
  return { context, pending };
}
const reply = (request, name) => request.resolve({ ok: true, json: async () => ({ results: [{ name }] }) });

test('directory exposes separate employee and supervisor filters', () => {
  assert.match(template, /data-person-group="employee"[^>]*>کارمندان<\/button>/);
  assert.match(template, /data-person-group="supervisor"[^>]*>سرپرست‌ها<\/button>/);
});

test('older responses cannot overwrite a newer result or clear its loading state', async () => {
  const { context: c, pending } = setup();
  const first = c.loadList('/first', true);
  const second = c.loadList('/second', true);
  assert.equal(pending[0].options.signal.aborted, true);
  reply(pending[0], 'old');
  await first;
  assert.equal(c.$table['aria-busy'], 'true');
  assert.equal(c.rendered, undefined);
  reply(pending[1], 'new');
  await second;
  assert.equal(c.rendered.results[0].name, 'new');
  assert.equal(c.$table['aria-busy'], 'false');
});

test('a failed page does not advance the page number and retry uses the same cursor', async () => {
  const { context: c, pending } = setup();
  c.state.index = 2;
  const failed = c.loadList('/persons?cursor=next', false, 3);
  pending[0].reject(new Error('offline'));
  await failed;
  assert.equal(c.state.index, 2);
  assert.equal(c.$retry.hidden, false);
  c.$retry.onclick();
  assert.equal(pending[1].url, '/persons?cursor=next');
  reply(pending[1], 'retried');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(c.state.index, 3);
  assert.equal(c.$retry.hidden, true);
});
