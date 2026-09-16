document.addEventListener('DOMContentLoaded', function () {
  // Date Mask
  const dateMaskElement = document.getElementById('dateMask');
  const dateMask = IMask(dateMaskElement, {
    mask: '00/00/0000',
    definitions: {
      '0': {
        mask: '0-9'
      }
    },
    prepare: function (str) {
      return str.replace(/\D/g, '');
    },
    commit: function (value, masked) {
      // Optional validation could go here
      if (value.length === 10) {
        const month = parseInt(value.substring(0, 2));
        const day = parseInt(value.substring(3, 5));
        if (month < 1 || month > 12 || day < 1 || day > 31) {
          // Handle invalid date if needed
        }
      }
    }
  });

  // Dynamic Mask (Credit Card)
  const dynamicMaskElement = document.getElementById('dynamicMask');
  const dynamicMask = IMask(dynamicMaskElement, {
    mask: '0000 0000 0000 0000',
    lazy: false,
    placeholderChar: '_'
  });

  // Pin Code Mask
  const pinCodeMaskElement = document.getElementById('pinCodeMask');
  const pinCodeMask = IMask(pinCodeMaskElement, {
    mask: '0000',
    lazy: false
  });

  // Phone Number Mask
  const phoneNumberMaskElement = document.getElementById('phoneNumberMask');
  const phoneNumberMask = IMask(phoneNumberMaskElement, {
    mask: '(000) 000-0000',
    lazy: false
  });

  // Money Input 1 - Standard US format
  const moneyInput1Element = document.getElementById('moneyInput1');
  const moneyMask1 = IMask(moneyInput1Element, {
    mask: Number,
    scale: 2,
    signed: false,
    thousandsSeparator: ',',
    padFractionalZeros: true,
    normalizeZeros: true,
    radix: '.',
    mapToRadix: ['.'],
    min: 0,
    max: 9999999.99,
    prefix: '$'
  });

  // Money Input 2 - European format
  const moneyInput2Element = document.getElementById('moneyInput2');
  const moneyMask2 = IMask(moneyInput2Element, {
    mask: Number,
    scale: 2,
    signed: false,
    thousandsSeparator: '.',
    padFractionalZeros: true,
    normalizeZeros: true,
    radix: ',',
    mapToRadix: [','],
    min: 0,
    max: 9999999.99,
    prefix: '€'
  });

  // Money Input 3 - Custom separator (space)
  const moneyInput3Element = document.getElementById('moneyInput3');
  const moneyMask3 = IMask(moneyInput3Element, {
    mask: Number,
    scale: 2,
    signed: false,
    thousandsSeparator: ' ',
    padFractionalZeros: true,
    normalizeZeros: true,
    radix: '.',
    mapToRadix: ['.'],
    min: 0,
    max: 9999999.99,
    prefix: '¥'
  });

  // Money Input 4 - Custom precision (4 decimal places)
  const moneyInput4Element = document.getElementById('moneyInput4');
  const moneyMask4 = IMask(moneyInput4Element, {
    mask: Number,
    scale: 4,
    signed: false,
    thousandsSeparator: ',',
    padFractionalZeros: true,
    normalizeZeros: true,
    radix: '.',
    mapToRadix: ['.'],
    min: 0,
    max: 9999999.9999,
    prefix: '£'
  });

  // Helper function for form submission handling
  function handleFormSubmission(e) {
    // Prevent default form submission
    e.preventDefault();

    // Get the unmasked/raw values if needed
    const dateValue = dateMask.unmaskedValue;
    const cardValue = dynamicMask.unmaskedValue;
    const pinValue = pinCodeMask.unmaskedValue;
    const phoneValue = phoneNumberMask.unmaskedValue;
    const money1Value = moneyMask1.unmaskedValue;
    const money2Value = moneyMask2.unmaskedValue;
    const money3Value = moneyMask3.unmaskedValue;
    const money4Value = moneyMask4.unmaskedValue;

    // Do something with the values (e.g., validation, API submission)
    console.log({
      date: dateValue,
      card: cardValue,
      pin: pinValue,
      phone: phoneValue,
      money1: money1Value,
      money2: money2Value,
      money3: money3Value,
      money4: money4Value
    });

    // Reset form or show success message
    // formElement.reset();
    // showSuccessMessage();
  }

  // Event listeners for input validation
  const allInputs = document.querySelectorAll('input');
  allInputs.forEach(input => {
    input.addEventListener('input', function () {
      this.classList.remove('is-invalid');
      if (this.value) {
        this.classList.add('is-valid');
      } else {
        this.classList.remove('is-valid');
      }
    });
  });
});