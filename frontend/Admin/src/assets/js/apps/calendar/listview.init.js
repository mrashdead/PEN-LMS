document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('listViewCalendar');
  
    var calendar = new FullCalendar.Calendar(calendarEl, {
      timeZone: 'local',
      initialView: 'listWeek',
      locale: 'fa',
      direction: 'rtl',
      buttonText: {
      today: 'امروز',
    },
    buttonHints: {
      today: 'رفتن به امروز',
      prev: 'هفته قبلی',
      next: 'هفته بعدی'
    },
      firstDay: 6, // Start from Saturday
      events: [
        { title: 'جلسه', start: new Date() },
        { title: 'آپدیت هفتگی', start: new Date() }
    ]
    });
  
    calendar.render();
  });