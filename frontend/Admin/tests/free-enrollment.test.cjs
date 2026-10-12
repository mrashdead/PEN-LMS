const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Exercise the real form script through its change and submit handlers.
function formHarness(authorized = true) {
  class Element {
    constructor() {
      this.value = ''; this.checked = false; this.disabled = false;
      this.hidden = false; this.children = []; this.listeners = {}; this.fields = {};
      this.style = {}; this.classList = { add() {}, remove() {}, toggle() {} };
    }
    addEventListener(event, handler) { this.listeners[event] = handler; }
    querySelector(selector) {
      if (selector === '[data-pay="amount"]' && this.children.length) return this.children[0].querySelector(selector);
      return this.fields[selector] || (this.fields[selector] = new Element());
    }
    querySelectorAll(selector) {
      if (selector === '[data-pay="amount"]') return this.children.map(row => row.querySelector(selector));
      return [];
    }
    appendChild(child) { this.children.push(child); }
    setAttribute() {}
    removeAttribute() {}
  }
  const elements = {};
  const element = id => elements[id] || (elements[id] = new Element());
  element('enr-discount-type').value = 'none';
  const document = {
    getElementById(id) {
      if (id === 'enr-recent' || id === 'enr-waitlist' || (!authorized && id === 'enr-is-free')) return null;
      return element(id);
    },
    createElement() {
      const row = new Element();
      row.querySelector('[data-pay="method"]').value = 'cash';
      return row;
    }, addEventListener() {}
  };
  const requests = [];
  const window = { location: { search: '' }, persianNumbers: value => String(value) };
  const fetch = (url, options) => {
    if (options.method === 'POST') {
      requests.push(JSON.parse(options.body));
      return new Promise(() => {});
    }
    const data = url.includes('?') ? { results: [{ id: 'offering', status: 'open', tuition: 100000 }] }
      : { lesson_titles: [{ tuition: 100000 }] };
    return Promise.resolve({ ok: true, json: () => Promise.resolve(data) });
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../src/assets/pen/js/enrollment.js'), 'utf8'),
                     { document, window, fetch, URLSearchParams, setTimeout, clearTimeout });
  return { element, requests };
}

const flush = () => new Promise(resolve => setImmediate(resolve));

test('free mode sends no payment or discount and restores the paid form', async () => {
  const { element, requests } = formHarness();
  await flush();
  element('enr-offering').value = 'offering';
  element('enr-offering').listeners.change();
  element('enr-student').value = 'student';
  await flush();
  assert.equal(element('enr-final').textContent, '100٬000');
  element('enr-discount-type').value = 'percent';
  element('enr-discount-value').value = '10';
  element('enr-free-reason').value = 'بورسیه';
  element('enr-is-free').checked = true;
  element('enr-is-free').listeners.change();
  assert.equal(element('enr-final').textContent, '0');
  assert.equal(element('enr-payment-section').hidden, true);
  assert.equal(element('enr-discount-type').disabled, true);
  element('enr-form').listeners.submit({ preventDefault() {} });
  assert.equal(requests[0].is_free, true);
  assert.deepEqual(requests[0].payments, []);
  assert.equal(requests[0].discount_type, 'none');
  assert.equal(requests[0].discount_value, 0);
  assert.equal(requests[0].free_reason, 'بورسیه');
  assert.equal(requests[0].course_amount, 100000);
  element('enr-is-free').checked = false;
  element('enr-is-free').listeners.change();
  assert.equal(element('enr-payment-section').hidden, false);
  assert.equal(element('enr-discount-type').disabled, false);
  assert.equal(element('enr-final').textContent, '90٬000');
});

test('form without free permission submits the usual positive payment', async () => {
  const { element, requests } = formHarness(false);
  await flush();
  element('enr-offering').value = 'offering';
  element('enr-offering').listeners.change();
  element('enr-student').value = 'student';
  await flush();
  element('enr-form').listeners.submit({ preventDefault() {} });
  assert.ok(requests.length, element('enr-errors').querySelector('ul').innerHTML);
  assert.equal(requests[0].is_free, false);
  assert.equal(requests[0].payments[0].amount, 100000);
  assert.equal(requests[0].payments[0].method, 'cash');
});
