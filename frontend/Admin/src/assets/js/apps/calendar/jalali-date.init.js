// jalaali.js - نسخه ساده و بدون وابستگی

  window.jalaali = {
    toJalaali: function(gy, gm, gd) {
      var g_d_m, jy;
      g_d_m = [0,31,59,90,120,151,181,212,243,273,304,334];
      var gy2 = (gm>2)?(gy+1):gy;
      var days = 355666 + (365*gy) + parseInt((gy2+3)/4) - parseInt((gy2+99)/100) + parseInt((gy2+399)/400) + gd + g_d_m[gm-1];
      jy = -1595 + 33 * parseInt(days / 12053);
      days %= 12053;
      jy += 4 * parseInt(days / 1461);
      days %= 1461;
      if (days > 365) {
        jy += parseInt((days - 1)/365);
        days = (days-1)%365;
      }
      var jm = (days < 186)?1 + parseInt(days/31):7 + parseInt((days-186)/30);
      var jd = 1 + ((days < 186)?(days%31):((days-186)%30));
      return { jy: jy, jm: jm, jd: jd };
    }
  };

  // محاسبه روز سال شمسی
  window.getJalaliDayOfYear = function(jy, jm, jd) {

    var days = jd;

    if (jm <= 6) {
      days += (jm - 1) * 31;
    } else {
      days += (6 * 31) + ((jm - 7) * 30);
    }

    return days;
  };


  // محاسبه شماره هفته شمسی از تاریخ میلادی
  window.getJalaliWeekNumberFromGregorianDate = function(date) {

    var gy = date.getFullYear();
    var gm = date.getMonth() + 1;
    var gd = date.getDate();

    var j = window.jalaali.toJalaali(gy, gm, gd);

    var dayOfYear = window.getJalaliDayOfYear(j.jy, j.jm, j.jd);

    var weekNumber = Math.floor((dayOfYear - 1) / 7) + 1;

    return weekNumber;
  };

  // تبدیل معکوس: از تاریخ شمسی به میلادی
  window.jalaali.fromJalaali = function (jy, jm, jd) {

    var gy, gm, gd;
    jy = parseInt(jy);
    jm = parseInt(jm);
    jd = parseInt(jd);

    // تبدیل سال جلالی به روزهای گذشته
    var jy2 = jy - 979;
    var days =
      365 * jy2 +
      Math.floor(jy2 / 33) * 8 +
      Math.floor(((jy2 % 33) + 3) / 4) +
      jd;

    if (jm < 7) days += (jm - 1) * 31;
    else days += (6 * 31) + (jm - 7) * 30;

    // تبدیل روزها به میلادی
    var gy2 = 1600 + Math.floor(days / 146097) * 400;
    days %= 146097;

    var leap = true;

    if (days >= 36525) {
      days--;
      gy2 += Math.floor(days / 36524) * 100;
      days %= 36524;
      if (days >= 365) days++;
      else leap = false;
    }

    gy2 += Math.floor(days / 1461) * 4;
    days %= 1461;

    if (days >= 366) {
      leap = false;
      days--;
      gy2 += Math.floor(days / 365);
      days %= 365;
    }

    var sal_a = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

    gm = 0;
    while (gm < 12 && days >= sal_a[gm]) {
      days -= sal_a[gm];
      gm++;
    }

    gd = days + 1;

    return {
      gy: gy2,
      gm: gm + 1,
      gd: gd
    };
  };