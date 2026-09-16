VirtualSelect.init({
  ele: '#languageSelect',
  options: [
    { label: 'انگلیسی', value: '1' },
    { label: 'آلمانی', value: '2' },
    { label: 'فرانسوی', value: '3' },
    { label: 'روسی', value: '4' },
  ],
  selectedValue: 0,
  multiple: true,
});
VirtualSelect.init({
  ele: '#currencySelect',
  options: [
    { label: 'دلار ($)', value: '1' },
    { label: 'یورو (€)', value: '2' },
    { label: 'پوند (£)', value: '3' },
    { label: 'ین (¥)', value: '4' },
  ],
  selectedValue: 0,
  multiple: true,
});

// Jalali datepicker
document.addEventListener("DOMContentLoaded", function () {
    if (window.jalaliDatepicker) {
        jalaliDatepicker.startWatch({
            selector: "input[data-jdp]",
            autoShow: true,
            autoHide: true,
            hideAfterChange: true,
            persianDigits: true,
        });
    } else {
        console.error("jalaliDatepicker not loaded!");
    }
});