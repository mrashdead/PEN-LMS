//Status Select
VirtualSelect.init({
    ele: "#statusSelect",
    options: [
        { label: "پرداخت شده", value: "Paid" },
        { label: "در حال بررسی", value: "Pending" },
        { label: "پرداخت نشده", value: "Unpaid" },
    ],
});

//Gender Select
VirtualSelect.init({
    ele: "#genderSelect",
    options: [
        { label: "مرد", value: "Male" },
        { label: "زن", value: "Female" },
        { label: "دیگری", value: "Others" },
    ],
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