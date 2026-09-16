document.addEventListener('DOMContentLoaded', function () {
  var calendarEl = document.getElementById('weekNumberCalendar');

  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    weekNumbers: true,
    locale: 'fa',
    direction: 'rtl',
    firstDay: 6, // Start from Saturday

    buttonText: {
      today: 'امروز'
    },

    buttonHints: {
      today: 'رفتن به امروز',
      prev: 'ماه قبلی',
      next: 'ماه بعدی'
    },

    weekNumberContent: function(arg) {
      var week = getJalaliWeekNumberFromGregorianDate(arg.date);
      return { html: week };
    }

  });

  calendar.render();
});