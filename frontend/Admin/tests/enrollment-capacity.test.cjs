const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/enrollment-capacity.js'), 'utf8');
const context = { module: { exports: {} } };
vm.runInNewContext(source, context);
const { recentDates, chartMarkup, escapeHtml } = context.module.exports;

test('quick ranges include both boundaries and cross leap days/year boundaries', () => {
  assert.equal(recentDates(7, '2026-01-03').from, '2025-12-28');
  assert.equal(recentDates(7, '2026-01-03').to, '2026-01-03');
  assert.equal(recentDates(2, '2024-03-01').from, '2024-02-29');
  assert.equal(recentDates(1, '2026-09-26').from, '2026-09-26');
});

test('labels are escaped before being inserted into SVG or HTML', () => {
  const value = '<script>alert("x")</script>';
  assert.ok(!escapeHtml(value).includes('<script>'));
  const markup = chartMarkup([{ label: value, total: 3 }], String);
  assert.ok(!markup.includes('<script>'));
  assert.ok(markup.includes('&lt;script&gt;'));
});

test('empty and zero-only trends show an explicit empty state', () => {
  assert.ok(!chartMarkup([], String).includes('<svg'));
  assert.ok(!chartMarkup([{ label: 'روز', total: 0 }], String).includes('<svg'));
});

test('a year of daily data produces bounded, finite chart geometry', () => {
  const rows = Array.from({ length: 366 }, (_, i) => ({ label: String(i), total: i % 25 }));
  const chart = chartMarkup(rows, String);
  assert.equal((chart.match(/<rect /g) || []).length, 366);
  assert.ok(!chart.includes('NaN'));
  assert.ok(!chart.includes('Infinity'));
});

function requestHarness() {
  const pending = [];
  const ctx = {
    state: { request: null, page: 0 }, errorBox: {}, retry: {},
    results: { hidden: false, setAttribute(key, value) { this[key] = value; } },
    AbortController, URL, Date, window: { location: { href: 'http://localhost/report/' }, history: { replaceState() {} } },
    setPager() {}, setText() {}, renderOverview() {},
    renderRows(rows) { ctx.rendered = rows; },
    fetch(url, options) { return new Promise((resolve, reject) => pending.push({ url, options, resolve, reject })); },
  };
  vm.createContext(ctx);
  vm.runInContext(source.slice(source.indexOf('  async function load('), source.indexOf('  function apply()')), ctx);
  return { ctx, pending };
}
const reply = (request, label) => request.resolve({ ok: true, json: async () => ({ results: [label], next: null, previous: null }) });

test('a slow response cannot replace a newer filter result or clear its busy state', async () => {
  const { ctx, pending } = requestHarness();
  const old = ctx.load('/report?capacity=full', 0, true);
  const fresh = ctx.load('/report?capacity=available', 0, true);
  assert.equal(pending[0].options.signal.aborted, true);
  reply(pending[0], 'old'); await old;
  assert.equal(ctx.results['aria-busy'], 'true');
  assert.equal(ctx.rendered, undefined);
  reply(pending[1], 'new'); await fresh;
  assert.equal(ctx.rendered[0], 'new');
  assert.equal(ctx.results['aria-busy'], 'false');
});

test('failed navigation preserves page position and retries the same cursor', async () => {
  const { ctx, pending } = requestHarness();
  ctx.state.page = 1;
  const request = ctx.load('/report?cursor=next', 2, false);
  pending[0].reject(new Error('offline')); await request;
  assert.equal(ctx.state.page, 1);
  assert.equal(ctx.retry.hidden, false);
  ctx.retry.onclick();
  assert.equal(pending[1].url, '/report?cursor=next');
  reply(pending[1], 'recovered');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(ctx.state.page, 2);
  assert.equal(ctx.errorBox.hidden, true);
});
