/* Calendar arithmetic uses UTC only as a date container, never as today's timezone. */
(function () {
  'use strict';
  var months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'];
  function english(value) { return String(value).replace(/[۰-۹٠-٩]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'.includes(d) ? '۰۱۲۳۴۵۶۷۸۹'.indexOf(d) : '٠١٢٣٤٥٦٧٨٩'.indexOf(d); }); }
  function addDays(iso, days) { var date = new Date(iso + 'T12:00:00Z'); date.setUTCDate(date.getUTCDate() + days); return date.toISOString().slice(0, 10); }
  function iso(value) {
    var raw = english(value).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw) && Number(raw.slice(0, 4)) >= 1700) {
      var date = new Date(raw + 'T12:00:00Z');
      if (!Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === raw) return raw;
    }
    if (/^1[3-6]\d{2}[/-]\d{1,2}[/-]\d{1,2}$/.test(raw)) {
      var result = window.penJalaliToISO(raw);
      if (result && english(window.penISOToJalali(result)).split('/').map(Number).join('/') === raw.replace(/-/g, '/').split('/').map(Number).join('/')) return result;
    }
    throw new Error('تاریخ شمسی را مانند ۱۴۰۵/۰۷/۰۱ وارد کنید.');
  }
  function range(period, today, year, month, week) {
    if (period === 'daily') return {start: today, end: today};
    if (period === 'weekly') return {start: addDays(today, -6), end: today};
    var start = iso(year + '/' + month + '/01');
    var nextMonth = Number(month) === 12 ? 1 : Number(month) + 1;
    var nextYear = Number(year) + (Number(month) === 12 ? 1 : 0);
    var end = addDays(iso(nextYear + '/' + nextMonth + '/01'), -1);
    if (period === 'month_week') {
      start = addDays(start, (Number(week) - 1) * 7);
      if (start > end) throw new Error('این ماه هفتهٔ انتخاب‌شده را ندارد.');
      end = [end, addDays(start, 6)].sort()[0];
    }
    if (start > today) throw new Error('بازهٔ گزارش نمی‌تواند از آینده شروع شود.');
    return {start: start, end: [end, today].sort()[0]};
  }
  window.penReportDates = {months: months, english: english, iso: iso, range: range};
})();
