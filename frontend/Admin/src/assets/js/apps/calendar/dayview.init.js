document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('dayGridViewCalendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
      timeZone: 'local',
      initialView: 'dayGridWeek',
      locale: 'fa',
      direction: 'rtl',
      firstDay: 6, // Start from Saturday
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridWeek,dayGridDay'
      },
      buttonText: {
        today: 'امروز',
        week: 'هفته',
        day: 'روز'
      },
      buttonHints: {
      today: 'رفتن به امروز',
      week: 'نمایش هفته',
      day: 'نمایش روز',
      prev: 'قبلی',
      next: 'بعدی'
      },
      editable: true,

  });

  calendar.render();

  });