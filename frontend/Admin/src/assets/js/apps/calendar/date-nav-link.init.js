document.addEventListener('DOMContentLoaded', function() {
  var calendarEl = document.getElementById('dateNavLinkCalendar');
  var calendar = new FullCalendar.Calendar(calendarEl, {
    locale: 'fa',
    direction: 'rtl',
    firstDay: 6, // Start from Saturday
    navLinks: true,
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
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
    allDayText: 'تمام روز',
    events:
      'https://fullcalendar.io/api/demo-feeds/events.json?single-day&for-resource-timeline',

  });

  calendar.render();
});