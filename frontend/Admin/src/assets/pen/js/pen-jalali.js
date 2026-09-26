/* Shared Jalali date conversion and picker wiring for workspace and Django admin. */
(function () {
  'use strict';
  // ── Jalali ↔ Gregorian conversion (jalaali-js, verbatim core) ──────
  // Needed because jalalidatepicker always writes Jalali text into inputs,
  // while /api/education/timetable/ and reports/ expect Gregorian ISO.
  function div(a, b) { return ~~(a / b); }
  function mod(a, b) { return a - ~~(a / b) * b; }
  function jalCal(jy) {
    var breaks = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
      1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178];
    var bl = breaks.length, gy = jy + 621, leapJ = -14, jp = breaks[0], jm, jump, leap, leapG, march, n, i;
    if (jy < jp || jy >= breaks[bl - 1]) throw new Error('Invalid Jalali year ' + jy);
    for (i = 1; i < bl; i += 1) {
      jm = breaks[i];
      jump = jm - jp;
      if (jy < jm) break;
      leapJ = leapJ + div(jump, 33) * 8 + div(mod(jump, 33), 4);
      jp = jm;
    }
    n = jy - jp;
    leapJ = leapJ + div(n, 33) * 8 + div(mod(n, 33) + 3, 4);
    if (mod(jump, 33) === 4 && jump - n === 4) leapJ += 1;
    leapG = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150;
    march = 20 + leapJ - leapG;
    if (jump - n < 6) n = n - jump + div(jump + 4, 33) * 33;
    leap = mod(mod(n + 1, 33) - 1, 4);
    if (leap === -1) leap = 4;
    return { leap: leap, gy: gy, march: march };
  }
  function g2d(gy, gm, gd) {
    var d = div((gy + div(gm - 8, 6) + 100100) * 1461, 4)
      + div(153 * mod(gm + 9, 12) + 2, 5)
      + gd - 34840408;
    d = d - div(div(gy + 100100 + div(gm - 8, 6), 100) * 3, 4) + 752;
    return d;
  }
  function d2g(jdn) {
    var j, i, gd, gm, gy;
    j = 4 * jdn + 139361631;
    j = j + div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
    i = div(mod(j, 1461), 4) * 5 + 308;
    gd = div(mod(i, 153), 5) + 1;
    gm = mod(div(i, 153), 12) + 1;
    gy = div(j, 1461) - 100100 + div(8 - gm, 6);
    return { gy: gy, gm: gm, gd: gd };
  }
  function j2d(jy, jm, jd) {
    var r = jalCal(jy);
    return g2d(r.gy, 3, r.march) + (jm - 1) * 31 - div(jm, 7) * (jm - 7) + jd - 1;
  }
  function d2j(jdn) {
    var gy = d2g(jdn).gy, jy = gy - 621, r = jalCal(jy), jdn1f = g2d(gy, 3, r.march), k;
    k = jdn - jdn1f;
    if (k >= 0) {
      if (k <= 185) return { jy: jy, jm: 1 + div(k, 31), jd: mod(k, 31) + 1 };
      k -= 186;
    } else {
      jy -= 1;
      k += 179;
      if (r.leap === 1) k += 1;
    }
    return { jy: jy, jm: 7 + div(k, 30), jd: mod(k, 30) + 1 };
  }

  // "1404/07/01" (or Persian digits) → "2025-09-23"; null on bad input.
  window.penJalaliToISO = function (str) {
    if (!str) return null;
    var s = String(str).replace(/[۰-۹]/g, function (c) { return String('۰۱۲۳۴۵۶۷۸۹'.indexOf(c)); });
    var m = /^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$/.exec(s.trim());
    if (!m) return null;
    try {
      var jy = +m[1], jm = +m[2], jd = +m[3];
      if (jm < 1 || jm > 12 || jd < 1 || jd > 31) return null;
      var day = j2d(jy, jm, jd);
      var actual = d2j(day);
      if (actual.jy !== jy || actual.jm !== jm || actual.jd !== jd) return null;
      var g = d2g(day);
      return g.gy + '-' + String(g.gm).padStart(2, '0') + '-' + String(g.gd).padStart(2, '0');
    } catch (e) { return null; }
  };
  // Date / "2025-09-23" → "1404/07/01"
  window.penISOToJalali = function (d) {
    var dt = (d instanceof Date) ? d : new Date(String(d).slice(0, 10) + 'T12:00:00');
    if (isNaN(dt.getTime())) return '';
    var jdn = g2d(dt.getFullYear(), dt.getMonth() + 1, dt.getDate());
    var j = d2j(jdn);
    return j.jy + '/' + String(j.jm).padStart(2, '0') + '/' + String(j.jd).padStart(2, '0');
  };

  // ── Jalali picker for all workspace date fields, including modal content ──
  // Pages can still call this helper after rendering a field. The shared
  // observer covers fields inserted later by forms, resource editors, etc.
  var jalaliArmed = false;
  window.penAttachJalaliPickers = function () {
    if (!window.jalaliDatepicker) return;
    document.querySelectorAll('input[data-jalali], input[data-jalali-time]').forEach(function (input) {
      if (input.dataset.jdpArmed) return;
      input.dataset.jdpArmed = '1';
      input.setAttribute('data-jdp', '');
      input.setAttribute('autocomplete', 'off');
      input.setAttribute('dir', 'ltr');
      if (input.hasAttribute('data-jalali-time')) {
        input.setAttribute('data-jdp-only-time', '');
        if (!input.value) input.placeholder = '۱۴:۳۰';
      } else if (!input.value && !input.placeholder) {
        input.placeholder = 'سال/ماه/روز';
      }
    });
    if (!jalaliArmed) {
      // Arm inputs before starting the watcher. This is important for pages
      // that add their picker fields dynamically or use data-jalali only.
      window.jalaliDatepicker.startWatch({ zIndex: 2000, hasSecond: false, persianDigits: false });
      jalaliArmed = true;
    }
  };

  document.addEventListener('DOMContentLoaded', function () {
    window.penAttachJalaliPickers();
    // Observe added nodes only: setting data-jdp above must not re-trigger us.
    var pending = false;
    new MutationObserver(function () {
      if (pending) return;
      pending = true;
      queueMicrotask(function () {
        pending = false;
        window.penAttachJalaliPickers();
      });
    }).observe(document.body, { childList: true, subtree: true });
  });

  // Native <dialog> is in the browser's top layer. A picker appended to body
  // would be visible behind its backdrop but could not receive clicks.
  document.addEventListener('focusin', function (event) {
    var dialog = event.target.closest('dialog[open]');
    if (!dialog || !event.target.matches('input[data-jalali]')) return;
    requestAnimationFrame(function () {
      var picker = document.querySelector('jdp-container');
      if (picker && !dialog.contains(picker)) dialog.appendChild(picker);
    });
  }, true);
  document.addEventListener('close', function (event) {
    if (!event.target.matches('dialog')) return;
    var picker = event.target.querySelector('jdp-container');
    if (picker) document.body.appendChild(picker);
  }, true);

})();
