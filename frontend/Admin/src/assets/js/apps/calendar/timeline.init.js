import { Calendar } from '../../../../../node_modules/@fullcalendar/core/index.js';
import resourceTimelinePlugin from '../../../../../node_modules/@fullcalendar/resource-timeline';

document.addEventListener('DOMContentLoaded', function () {
  var calendarEl = document.getElementById('timelineCalendar');

  const calendar = new Calendar(calendarEl, {
    plugins: [resourceTimelinePlugin],
    initialView: 'resourceTimelineDay',
    timeZone: 'UTC',
    aspectRatio: 1.5,
    locale: 'fa',
    direction: 'rtl',
    firstDay: 6, // Start from Saturday
    headerToolbar: {
      left: 'prev,next',
      center: 'title',
      right: 'resourceTimelineDay,resourceTimelineWeek,resourceTimelineMonth'
    },
    buttonText: {
      today: 'امروز',
      month: 'ماه',
      week: 'هفته',
      day: 'روز'
    },
    buttonHints: {
      today: 'رفتن به امروز',
      month: 'نمایش ماه',
      week: 'نمایش هفته',
      day: 'نمایش روز',
      prev: 'قبلی',
      next: 'بعدی'
    },
    editable: true,
    resourceAreaHeaderContent: 'اتاق‌ها',
    resources: 'https://fullcalendar.io/api/demo-feeds/resources.json?with-nesting&with-colors',
    events: 'https://fullcalendar.io/api/demo-feeds/events.json?single-day&for-resource-timeline&start=2025-08-01&end=2026-01-12&timezone=UTC'
  });

  calendar.render();
});