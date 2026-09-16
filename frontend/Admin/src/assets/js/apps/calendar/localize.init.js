
document.addEventListener('DOMContentLoaded', function() {
    var localeSelectorEl = document.getElementById('localizeSelect');
    var calendarEl = document.getElementById('localizeCalendar');
  
    var calendar = new FullCalendar.Calendar(calendarEl, {
    });
  
    calendar.render();  
    localeSelectorEl.addEventListener('change', function() {
      if (this.value) {
        calendar.setOption('locale', this.value);
      }
    });
  
  });

// Initialize VirtualSelect
VirtualSelect.init({
    ele: "#localizeSelect",
    options: [
        { label: "English (EN-AU)", value: "en-au" },
        { label: "فارسی (FA)", value: "fa" },
        { label: "Arabic (AR)", value: "ar" },
        { label: "German (DE)", value: "de" },
        { label: "Russian (RU)", value: "ru" },
        { label: "French (FR)", value: "fr" },
        { label: "Italian (IT)", value: "it" },
        { label: "Danish (DA)", value: "da" },
        { label: "Chinese (ZH)", value: "zh" },
        { label: "Korean (KO)", value: "ko" },
        { label: "Greek (EL)", value: "el" },
        { label: "Finnish (FI)", value: "fi" },
        { label: "Catalan, Valencian (CA)", value: "ca" },
    ]
});