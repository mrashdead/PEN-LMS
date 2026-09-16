VirtualSelect.init({
    ele: "#leaveTypeSelect",
    options: [
        { label: "مرخصی موقت", value: "casual" },
        { label: "مرخصی استعلاجی", value: "sick" },
        { label: "مرخصی زایمان", value: "maternity" },
        { label: "مرخصی اضطراری", value: "emergency" },
        { label: "مرخصی تعطیلات", value: "vacation" },
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