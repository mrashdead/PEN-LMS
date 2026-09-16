//doctor select
VirtualSelect.init({
    ele: "#doctorSelect",
    options: [
        { label: "دکتر مایکل جانسون", value: "Dr. Michael Johnson" },
        { label: "دکتر سارا ایوانز", value: "Dr. Sarah Evans" },
        { label: "دکتر امیلی کارتر", value: "Dr. Emily Carter" },
        { label: "دکتر رابرت هریس", value: "Dr. Robert Harris" },
    ],
});

  document.addEventListener("DOMContentLoaded", function () {
    jalaliDatepicker.startWatch({
      selector: "input[data-jdp]",  
      autoShow: true,  
      autoHide: true,
      hideAfterChange: true,
      persianDigits: true,
      minDate: "today", 
    });
  });