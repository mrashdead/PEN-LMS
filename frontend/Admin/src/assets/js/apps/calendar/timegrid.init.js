document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('listViewCalendar');
  
    var calendar = new FullCalendar.Calendar(calendarEl, {
      timeZone: 'local',
      initialView: 'timeGridWeek',
      locale: 'fa',
      direction: 'rtl',
      firstDay: 6, // Start from Saturday
      headerToolbar: {
        left: 'prev,next',
        center: 'title',
        right: 'timeGridWeek,timeGridDay'
      },
      buttonText: {
        week: 'هفته',
        day: 'روز'
      },
      buttonHints: {
      week: 'نمایش هفته',
      day: 'نمایش روز',
      prev: 'قبلی',
      next: 'بعدی'
      },
      allDayText: 'تمام روز',

    });
    calendar.render();
  });