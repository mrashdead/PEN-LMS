document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('dateClickingSelectingCalendar');
  
    var calendar = new FullCalendar.Calendar(calendarEl, {
      selectable: true,
      locale: 'fa',
      direction: 'rtl',
      firstDay: 6, // Start from Saturday
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

      dayHeaderContent: function(arg) {
        var d = arg.date;

        var weekdayName = new Intl.DateTimeFormat('fa-IR', { weekday: 'long' }).format(d);

        return {
          html: '<span class="fc-col-header-cell-cushion">' + weekdayName + '</span>'
        };
      },
      dateClick: function(info) {
        var d = info.date;
        var j = jalaali.toJalaali(d.getFullYear(), d.getMonth()+1, d.getDate());

        alert('تاریخ انتخاب‌شده: ' + j.jy + '/' + j.jm + '/' + j.jd);
      },
      select: function(info) {
        var s = info.start;
        var e = new Date(info.end.getTime() - 86400000);

        var js = jalaali.toJalaali(s.getFullYear(), s.getMonth()+1, s.getDate());
        var je = jalaali.toJalaali(e.getFullYear(), e.getMonth()+1, e.getDate());

        alert(
          'بازه انتخاب شده: از ' +
          js.jy + '/' + js.jm + '/' + js.jd +
          ' تا ' +
          je.jy + '/' + je.jm + '/' + je.jd
        );
      }
    });
  
    calendar.render();
  });