/* Shared 24-hour time control. The original input remains the form/API value. */
(function () {
  'use strict';
  var selector = 'input[type="time"], input[data-jalali-time], input[data-pen-time]';
  var instances = new WeakMap();
  var datetimes = new WeakMap();
  var serial = 0;
  var active = null;
  var valueProperty = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');

  function digits(value) {
    return String(value).replace(/[۰-۹٠-٩]/g, function (char) {
      return String(char.charCodeAt(0) - (char >= '۰' ? 1776 : 1632));
    });
  }
  function parse(value) {
    var match = /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(digits(value).trim());
    if (!match || +match[1] > 23 || +match[2] > 59 || (match[3] && +match[3] > 59)) return null;
    return {hour: +match[1], minute: +match[2], second: match[3] ? +match[3] : null};
  }
  function pad(value) { return String(value).padStart(2, '0'); }
  function format(parts) {
    return pad(parts.hour) + ':' + pad(parts.minute) + (parts.second === null ? '' : ':' + pad(parts.second));
  }
  function currentTime() {
    var parts = new Intl.DateTimeFormat('en-GB', {timeZone: 'Asia/Tehran', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'}).formatToParts(new Date());
    return parts.find(function (part) { return part.type === 'hour'; }).value + ':' + parts.find(function (part) { return part.type === 'minute'; }).value;
  }
  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }
  function button(text, name, action) {
    var node = element('button', 'pen-time-button', text);
    node.type = 'button';
    if (name) node.setAttribute('aria-label', name);
    node.addEventListener('click', action);
    return node;
  }

  // Schema forms store one Jalali date + HH:mm string. Split only the UI;
  // forms.js still reads and converts the original named field at submission.
  function attachDatetime(source) {
    if (datetimes.has(source)) return;
    var key = 'pen-datetime-' + (++serial);
    var label = source.getAttribute('aria-label') || (source.labels && source.labels[0] ? source.labels[0].textContent.trim() : 'تاریخ و ساعت');
    var group = element('div', 'pen-datetime-control');
    source.before(group); group.appendChild(source); source.hidden = true; source.tabIndex = -1;
    var dateBox = element('div'); var timeBox = element('div');
    var date = element('input', 'form-control'); date.type = 'text'; date.id = key + '-date';
    date.setAttribute('data-jalali', ''); date.dir = 'ltr'; date.placeholder = 'سال/ماه/روز';
    date.setAttribute('aria-label', 'تاریخِ ' + label);
    var time = element('input', 'form-control'); time.type = 'time'; time.id = key + '-time';
    time.step = '60'; time.setAttribute('aria-label', 'ساعتِ ' + label);
    var dateLabel = element('label', 'form-label', 'تاریخ'); dateLabel.htmlFor = date.id;
    var timeLabel = element('label', 'form-label', 'ساعت'); timeLabel.htmlFor = time.id;
    dateBox.append(dateLabel, date); timeBox.append(timeLabel, time); group.append(dateBox, timeBox);
    function reflect() {
      [date, time].forEach(function (input) {
        input.disabled = source.disabled; input.readOnly = source.readOnly;
        input.required = source.required || source.getAttribute('aria-required') === 'true';
        var describedBy = source.getAttribute('aria-describedby');
        if (describedBy) input.setAttribute('aria-describedby', describedBy);
      });
    }
    function sync() {
      var parts = valueProperty.get.call(source).trim().split(/[T\s]+/);
      date.value = parts[0] || ''; time.value = parts[1] || '';
      reflect();
    }
    function commit() {
      valueProperty.set.call(source, date.value + (time.value ? ' ' + time.value : ''));
      source.dispatchEvent(new Event('input', {bubbles: true}));
      source.dispatchEvent(new Event('change', {bubbles: true}));
    }
    Object.defineProperty(source, 'value', {configurable: true, get: function () { return valueProperty.get.call(this); }, set: function (value) { valueProperty.set.call(this, value); sync(); }});
    source.focus = function (options) { date.focus(options); };
    Array.from(source.labels || []).forEach(function (node) { node.addEventListener('click', function (event) { event.preventDefault(); date.focus(); }); });
    date.addEventListener('input', commit); date.addEventListener('change', commit); time.addEventListener('input', commit);
    source.addEventListener('invalid', function (event) { event.preventDefault(); date.focus(); });
    datetimes.set(source, {sync: sync, reflect: reflect}); sync();
    date.defaultValue = date.value; time.defaultValue = time.value;
    attach(time);
  }

  function attach(source) {
    if (instances.has(source) || source.dataset.penTimeNative === 'true') return;
    var key = 'pen-time-' + (++serial);
    var label = source.getAttribute('aria-label') || (source.labels && source.labels[0] ? source.labels[0].textContent.replace(/\*/g, '').trim() : 'زمان');
    var control = element('div', source.className + ' pen-time-control');
    control.dir = 'ltr';
    control.setAttribute('role', 'group');
    control.setAttribute('aria-label', label + '، ۲۴ ساعته');
    source.before(control);
    control.appendChild(source);
    source.hidden = true;
    source.tabIndex = -1;
    var seconds = null;
    var dirty = false;
    var notified = false;
    var customError = '';
    var error = element('div', 'pen-time-error');
    error.id = key + '-error';
    error.hidden = true;
    error.setAttribute('aria-live', 'polite');
    control.after(error);

    function segment(name, maximum) {
      var input = element('input', 'pen-time-segment');
      input.type = 'text';
      input.inputMode = 'numeric';
      input.maxLength = 2;
      input.placeholder = '––';
      input.autocomplete = 'off';
      input.id = key + '-' + name;
      input.setAttribute('role', 'spinbutton');
      input.setAttribute('aria-label', (name === 'hour' ? 'ساعتِ ' : 'دقیقهٔ ') + label);
      input.setAttribute('aria-valuemin', '0');
      input.setAttribute('aria-valuemax', String(maximum));
      input.title = name === 'hour' ? 'ساعت (۰ تا ۲۳)' : 'دقیقه (۰ تا ۵۹)';
      input.addEventListener('focus', function () { input.select(); });
      input.addEventListener('input', function () {
        input.value = digits(input.value);
        commit();
        if (input === hour && input.value.length === 2 && /^\d{2}$/.test(input.value) && +input.value <= 23) minute.focus();
      });
      input.addEventListener('change', function () {
        if (/^\d{1,2}$/.test(input.value) && +input.value <= maximum) input.value = pad(input.value);
      });
      input.addEventListener('keydown', function (event) {
        if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
          event.preventDefault(); adjust(input, event.key === 'ArrowUp' ? 1 : -1);
        } else if (event.key === ':' && input === hour) {
          event.preventDefault(); minute.focus();
        }
      });
      input.addEventListener('paste', function (event) {
        var parsed = parse(event.clipboardData.getData('text'));
        if (!parsed) return;
        event.preventDefault(); setValue(format(parsed)); minute.focus();
      });
      control.appendChild(input);
      return input;
    }
    var hour = segment('hour', 23);
    var colon = element('span', 'pen-time-colon', ':'); colon.setAttribute('aria-hidden', 'true'); control.appendChild(colon);
    var minute = segment('minute', 59);
    var trigger = button('', 'تنظیم ' + label, function () { if (active === api) close(true); else open(); });
    trigger.classList.add('pen-time-trigger');
    // Static Lucide clock geometry, so dynamically inserted fields need no icon refresh.
    trigger.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><path d="M12 6v6l4 2"></path></svg>';
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', key + '-panel');
    control.appendChild(trigger);
    var panel = element('div', 'pen-time-panel');
    panel.id = key + '-panel';
    panel.dir = 'rtl';
    panel.hidden = true;
    panel.setAttribute('role', 'region');
    panel.setAttribute('aria-label', 'تنظیم ' + label);
    var nativePopover = typeof panel.showPopover === 'function';
    if (nativePopover) panel.setAttribute('popover', 'manual');
    control.appendChild(panel);
    var heading = element('div', 'pen-time-heading');
    heading.appendChild(element('strong', '', 'انتخاب ساعت'));
    var preview = element('output', 'pen-time-preview'); preview.dir = 'ltr'; preview.setAttribute('aria-live', 'polite'); heading.appendChild(preview);
    panel.appendChild(heading);
    var steps = element('div', 'pen-time-steps');
    function stepper(input, title) {
      var group = element('div', 'pen-time-stepper');
      group.appendChild(element('span', '', title));
      var actions = element('div', 'pen-time-step-actions'); actions.dir = 'ltr';
      actions.appendChild(button('−', 'کاهش ' + title, function () { adjust(input, -1); }));
      var value = element('output'); actions.appendChild(value);
      actions.appendChild(button('+', 'افزایش ' + title, function () { adjust(input, 1); }));
      group.appendChild(actions); steps.appendChild(group); return value;
    }
    var hourPreview = stepper(hour, 'ساعت');
    var minutePreview = stepper(minute, 'دقیقه');
    panel.appendChild(steps);
    panel.appendChild(element('p', 'pen-time-caption', 'انتخاب سریع دقیقه'));
    var shortcuts = element('div', 'pen-time-shortcuts'); shortcuts.dir = 'ltr';
    [0, 15, 30, 45].forEach(function (value) {
      var shortcut = button(pad(value), 'دقیقهٔ ' + value, function () {
        minute.value = pad(value); commit();
        if (!hour.value) { close(false); hour.focus(); }
      });
      shortcut.dataset.minute = String(value); shortcuts.appendChild(shortcut);
    });
    panel.appendChild(shortcuts);
    var footer = element('div', 'pen-time-footer');
    footer.appendChild(button('اکنون', null, function () { setValue(currentTime()); close(true); }));
    footer.appendChild(button('پاک‌کردن', null, function () { setValue(''); close(false); hour.focus(); }));
    var done = button('انجام شد', null, function () { close(true); }); done.classList.add('pen-time-done'); footer.appendChild(done);
    panel.appendChild(footer);

    function message() {
      if (customError) return customError;
      if (source.validity.valueMissing) return 'ساعت و دقیقه را وارد کنید.';
      if (source.validity.rangeUnderflow || source.validity.rangeOverflow) return 'زمان باید در بازهٔ ' + (source.min || '00:00') + ' تا ' + (source.max || '23:59') + ' باشد.';
      if (source.validity.stepMismatch) return 'زمان را با فاصلهٔ ' + Number(source.step || 60) / 60 + ' دقیقه انتخاب کنید.';
      return source.validationMessage;
    }
    function reflect() {
      var invalid = source.getAttribute('aria-invalid') === 'true' || source.classList.contains('is-invalid') || Boolean(source.closest('.pen-field.is-invalid')) || (notified && !source.validity.valid);
      control.classList.toggle('pen-time-invalid', invalid);
      control.classList.toggle('pen-time-disabled', source.disabled);
      control.classList.toggle('pen-time-readonly', source.readOnly);
      error.textContent = invalid ? message() : ''; error.hidden = !error.textContent;
      [hour, minute].forEach(function (input) {
        input.disabled = source.disabled; input.readOnly = source.readOnly;
        input.setAttribute('aria-required', String(source.required || source.getAttribute('aria-required') === 'true'));
        input.setAttribute('aria-invalid', String(invalid));
        var field = source.closest('.pen-field');
        var serverError = field && field.querySelector('.pen-field-errors[id]');
        input.setAttribute('aria-describedby', ((source.getAttribute('aria-describedby') || '') + ' ' + error.id + (serverError ? ' ' + serverError.id : '')).trim());
        if (/^\d{1,2}$/.test(input.value)) input.setAttribute('aria-valuenow', String(+input.value)); else input.removeAttribute('aria-valuenow');
      });
      trigger.disabled = source.disabled || source.readOnly;
      if (active === api && (trigger.disabled || !control.isConnected || !control.getClientRects().length)) close(false);
      preview.textContent = hour.value && minute.value ? hour.value + ':' + minute.value : '––:––';
      hourPreview.textContent = hour.value || '––'; minutePreview.textContent = minute.value || '––';
      shortcuts.querySelectorAll('button').forEach(function (shortcut) { shortcut.setAttribute('aria-pressed', String(minute.value !== '' && +minute.value === +shortcut.dataset.minute)); });
    }
    function sync() {
      var raw = digits(valueProperty.get.call(source));
      var parsed = parse(raw);
      hour.value = parsed ? pad(parsed.hour) : (raw.split(':')[0] || '');
      minute.value = parsed ? pad(parsed.minute) : (raw.split(':')[1] || '');
      seconds = parsed ? parsed.second : null;
      if (parsed) valueProperty.set.call(source, format(parsed));
      customError = raw && !parsed ? 'ساعت بین ۰ تا ۲۳ و دقیقه بین ۰ تا ۵۹ است؛ هر دو بخش را کامل کنید.' : '';
      source.setCustomValidity(customError); dirty = false; notified = Boolean(customError); reflect();
    }
    function commit() {
      var parsed = parse(hour.value + ':' + pad(minute.value));
      if (!hour.value || !minute.value || !/^\d{1,2}$/.test(hour.value) || !/^\d{1,2}$/.test(minute.value)) parsed = null;
      var empty = !hour.value && !minute.value;
      customError = !empty && !parsed ? 'ساعت بین ۰ تا ۲۳ و دقیقه بین ۰ تا ۵۹ است؛ هر دو بخش را کامل کنید.' : '';
      if (parsed) parsed.second = seconds;
      valueProperty.set.call(source, parsed ? format(parsed) : '');
      source.setCustomValidity(customError); dirty = true;
      source.dispatchEvent(new Event('input', {bubbles: true}));
      source.dispatchEvent(new Event('change', {bubbles: true}));
      reflect();
    }
    function setValue(value) {
      source.value = value;
      source.dispatchEvent(new Event('input', {bubbles: true}));
      source.dispatchEvent(new Event('change', {bubbles: true}));
      dirty = true; notified = true;
      reflect();
    }
    function adjust(input, delta) {
      if (source.disabled || source.readOnly) return;
      var maximum = input === hour ? 24 : 60;
      input.value = pad(((Number(input.value) || 0) + delta + maximum) % maximum);
      if (!hour.value) hour.value = '00';
      if (!minute.value) minute.value = '00';
      commit();
    }
    function position() {
      var rect = control.getBoundingClientRect();
      var width = Math.min(288, window.innerWidth - 16);
      panel.style.width = width + 'px';
      panel.style.left = Math.max(8, Math.min(rect.right - width, window.innerWidth - width - 8)) + 'px';
      var height = panel.getBoundingClientRect().height;
      panel.style.top = Math.max(8, Math.min(rect.bottom + 6 + height > window.innerHeight - 8 ? rect.top - height - 6 : rect.bottom + 6, window.innerHeight - height - 8)) + 'px';
    }
    function open() {
      if (trigger.disabled) return;
      if (active) active.close(false);
      active = api; panel.hidden = false;
      if (nativePopover) panel.showPopover();
      trigger.setAttribute('aria-expanded', 'true'); reflect(); position();
      panel.querySelector('button').focus({preventScroll: true});
    }
    function close(restore) {
      if (active !== api) return;
      if (nativePopover && panel.matches(':popover-open')) panel.hidePopover();
      panel.hidden = true; trigger.setAttribute('aria-expanded', 'false'); active = null;
      if (restore && trigger.isConnected) trigger.focus({preventScroll: true});
    }
    var api = {source: source, control: control, panel: panel, trigger: trigger, sync: sync, reflect: reflect, close: close};
    instances.set(source, api);
    // Existing pages assign input.value directly when loading edits or resetting filters.
    Object.defineProperty(source, 'value', {
      configurable: true,
      get: function () { return valueProperty.get.call(this); },
      set: function (value) { valueProperty.set.call(this, value); sync(); }
    });
    source.addEventListener('invalid', function (event) {
      event.preventDefault(); notified = true; reflect();
      if (!document.activeElement || !document.activeElement.closest('.pen-time-invalid')) hour.focus();
    });
    source.addEventListener('focus', function () { hour.focus(); });
    source.focus = function (options) { hour.focus(options); };
    control.addEventListener('focusout', function (event) {
      if (!control.contains(event.relatedTarget) && dirty) { notified = true; reflect(); }
    });
    // Preserve label-to-input behavior while the canonical field is hidden.
    Array.from(source.labels || []).forEach(function (node) {
      node.addEventListener('click', function (event) { event.preventDefault(); hour.focus(); });
    });
    source.addEventListener('change', function () {
      var parsed = parse(source.value);
      if ((parsed && (pad(parsed.hour) !== pad(hour.value) || pad(parsed.minute) !== pad(minute.value))) || (!source.value && !hour.value && !minute.value)) sync();
    });
    sync();
  }
  function attachAll(root) {
    if (root.matches && root.matches('input[data-jalali-dt]')) attachDatetime(root);
    root.querySelectorAll('input[data-jalali-dt]').forEach(attachDatetime);
    if (root.matches && root.matches(selector)) attach(root);
    root.querySelectorAll(selector).forEach(attach);
  }
  window.penTime = {parse: parse, format: format, digits: digits};
  window.penAttachTimePickers = function () { attachAll(document); };
  window.penValidateTimePickers = function (root) {
    var fields = Array.from(root.querySelectorAll(selector));
    var invalid = fields.find(function (source) { return source.willValidate && !source.validity.valid; });
    if (!invalid) return true;
    invalid.reportValidity();
    return false;
  };
  function start() {
    attachAll(document);
    new MutationObserver(function (records) {
      records.forEach(function (record) {
        if (record.type === 'childList') record.addedNodes.forEach(function (node) { if (node.nodeType === 1) attachAll(node); });
        else if (instances.has(record.target)) {
          var api = instances.get(record.target);
          if (record.attributeName === 'value') api.sync(); else api.reflect();
        } else if (datetimes.has(record.target)) {
          var datetime = datetimes.get(record.target);
          if (record.attributeName === 'value') datetime.sync(); else datetime.reflect();
        } else if (record.target.matches(selector)) attach(record.target);
        else if (record.attributeName === 'class' && record.target.matches('.pen-field')) {
          record.target.querySelectorAll(selector).forEach(function (source) { var api = instances.get(source); if (api) api.reflect(); });
        }
      });
      if (active && !active.control.isConnected) active.close(false);
    }).observe(document.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['value', 'required', 'disabled', 'readonly', 'min', 'max', 'step', 'aria-required', 'aria-describedby', 'aria-invalid', 'class', 'type', 'data-jalali-time', 'data-pen-time']});
    document.addEventListener('reset', function (event) {
      if (active && active.source.form === event.target) active.close(false);
      queueMicrotask(function () {
        event.target.querySelectorAll('input[data-jalali-dt]').forEach(function (source) { var api = datetimes.get(source); if (api) api.sync(); });
        event.target.querySelectorAll(selector).forEach(function (source) { var api = instances.get(source); if (api) api.sync(); });
      });
    }, true);
    // Some existing AJAX forms use novalidate and their own field validation.
    // A partially typed optional time must still be rejected rather than cleared.
    document.addEventListener('submit', function (event) {
      if (!window.penValidateTimePickers(event.target)) { event.preventDefault(); event.stopImmediatePropagation(); }
    }, true);
    document.addEventListener('pointerdown', function (event) { if (active && !active.control.contains(event.target)) active.close(false); }, true);
    document.addEventListener('focusin', function (event) { if (active && !active.control.contains(event.target)) active.close(false); });
    document.addEventListener('keydown', function (event) { if (active && event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); active.close(true); } }, true);
    document.addEventListener('scroll', function (event) { if (active && !active.panel.contains(event.target)) active.close(false); }, true);
    document.addEventListener('close', function () { if (active) active.close(false); }, true);
    window.addEventListener('resize', function () { if (active) active.close(false); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
