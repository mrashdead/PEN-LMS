document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('multiMonthGridCalendar');
  
    var calendar = new FullCalendar.Calendar(calendarEl, {
      timeZone: 'local',
      locale: 'fa',
      direction: 'rtl',
      firstDay: 6, //Start from Saturday
      initialView: 'multiMonthYear',
      editable: true,
      buttonText: {
      today: 'امروز'
    },
    buttonHints: {
      today: 'رفتن به امروز',
      prev: 'سال قبلی',
      next: 'سال بعدی'
    },

    datesSet(info) {
      const middle = new Date(
        info.view.currentStart.getFullYear(),
        info.view.currentStart.getMonth() + 6,  // Month = middle year +6
        15    // The middle date of a Month
      );

    const j = window.jalaali.toJalaali(
      middle.getFullYear(),
      middle.getMonth() + 1,
      middle.getDate()
    );

    // Change title
    const titleEl = document.querySelector('.fc-toolbar-title');
      if (titleEl) {
          titleEl.textContent = j.jy.toString(); // Only Jalali Year
      }
    }
  });
  
    calendar.render();
  });