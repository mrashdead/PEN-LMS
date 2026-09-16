//Gender select
VirtualSelect.init({
    ele: "#genderSelect",
    options: [
        { label: "مرد", value: "Male" },
        { label: "زن", value: "Female" },
        { label: "دیگری", value: "Others" },
    ],
});

  document.addEventListener("DOMContentLoaded", function () {
    jalaliDatepicker.startWatch({
      // Initial values
      selector: "input[data-jdp]",  // No Change
      autoShow: true,               // Open with auto facuse
      autoHide: true,               // Click outside => closed
      hideAfterChange: true,        // Close after choose date
      persianDigits: true,          // Persian Numbers
    });
  });