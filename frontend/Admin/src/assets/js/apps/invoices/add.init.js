import * as FilePond from 'filepond';
import FilePondPluginImagePreview from 'filepond-plugin-image-preview';
import FilePondPluginImageExifOrientation from 'filepond-plugin-image-exif-orientation';
import FilePondPluginFileValidateSize from 'filepond-plugin-file-validate-size';
import FilePondPluginImageEdit from 'filepond-plugin-image-edit';
import 'filepond/dist/filepond.min.css';
import 'filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css';

FilePond.registerPlugin(
  FilePondPluginImagePreview,
  FilePondPluginImageExifOrientation,
  FilePondPluginFileValidateSize,
  FilePondPluginImageEdit
);

// Select the file input and use 
// create() to turn it into a pond
FilePond.create(document.querySelector('#companyLogoInput'), {
  labelIdle: `
    <i class="ri-upload-2-line fs-22"></i>
    <h6 class="mb-0 mt-2">Upload Your Company Logo</h6>
  `,
  imagePreviewHeight: 120,
});

document.addEventListener('DOMContentLoaded', function () {
  // Constants
  const VAT_RATE = 0.06; // 6%
  const DISCOUNT_RATE = 0.10; // 10%
  const SHIPPING_CHARGE = 15.00; // Default shipping charge

  // Initialize elements
  const tableBody = document.getElementById('tableBody');
  const addProductItemBtn = document.getElementById('addProductItem');

  // Set default shipping charge
  document.getElementById('shippingCharge').value = SHIPPING_CHARGE.toFixed(2);

  // Add event listener for adding new items
  addProductItemBtn.addEventListener('click', addNewRow);

  // Initialize calculations
  updateAllCalculations();

  // Add event delegation for the entire table body
  tableBody.addEventListener('click', function (event) {
    // Handle remove item button click
    if (event.target.classList.contains('remove-item') ||
      (event.target.parentElement && event.target.parentElement.classList.contains('remove-item'))) {
      const row = getAncestorByTagName(event.target, 'TR');
      if (row && row.cells[0].textContent !== '') {
        row.remove();
        updateRowNumbers();
        updateAllCalculations();
      }
      event.preventDefault();
    }

    // Handle quantity decrease button
    if (event.target.classList.contains('input-spin-minus') ||
      (event.target.parentElement && event.target.parentElement.classList.contains('input-spin-minus'))) {
      const row = getAncestorByTagName(event.target, 'TR');
      const qtyInput = row.querySelector('.input-spin');
      let qty = parseInt(qtyInput.value);
      if (qty > 1) {
        qtyInput.value = --qty;
        updateRowTotal(row);
        updateAllCalculations();
      }
    }

    // Handle quantity increase button
    if (event.target.classList.contains('input-spin-plus') ||
      (event.target.parentElement && event.target.parentElement.classList.contains('input-spin-plus'))) {
      const row = getAncestorByTagName(event.target, 'TR');
      const qtyInput = row.querySelector('.input-spin');
      let qty = parseInt(qtyInput.value);
      qtyInput.value = ++qty;
      updateRowTotal(row);
      updateAllCalculations();
    }
  });

  // Add input event listener for price and discount changes
  tableBody.addEventListener('input', function (event) {
    if (event.target.tagName === 'INPUT' && event.target.type === 'number') {
      const row = getAncestorByTagName(event.target, 'TR');
      if (row && row.cells.length > 1) {
        updateRowTotal(row);
        updateAllCalculations();
      }
    }
  });

  // Function to add a new row
  function addNewRow() {
    // Get the first row as a template
    const firstRow = tableBody.querySelector('tr');
    if (!firstRow) return;

    // Clone the first row
    const newRow = firstRow.cloneNode(true);

    // Reset values in the new row
    const inputs = newRow.querySelectorAll('input[type="text"], input[type="number"]');
    inputs.forEach(input => {
      if (input.classList.contains('input-spin')) {
        input.value = '1';
      } else {
        input.value = '';
      }
    });

    // Insert the new row before the "Add Item" row
    const addBtnRow = tableBody.querySelector('tr:nth-child(2)');
    tableBody.insertBefore(newRow, addBtnRow);

    // Update row numbers
    updateRowNumbers();
  }

  // Function to update row numbers
  function updateRowNumbers() {
    const rows = tableBody.querySelectorAll('tr');
    let itemCount = 1;

    rows.forEach(row => {
      if (row.firstElementChild && !row.firstElementChild.hasAttribute('colspan')) {
        row.firstElementChild.textContent = itemCount++;
      }
    });
  }

  // Function to update a single row's total
  function updateRowTotal(row) {
    // Get the quantity, price, and discount inputs
    const qtyInput = row.querySelector('.input-spin');
    const priceInput = row.querySelector('td:nth-child(4) input');
    const discountInput = row.querySelector('td:nth-child(5) input');
    const totalInput = row.querySelector('td:nth-child(6) input');

    if (!qtyInput || !priceInput || !discountInput || !totalInput) return;

    const qty = parseInt(qtyInput.value) || 0;
    const price = parseFloat(priceInput.value) || 0;
    const discountPercentage = parseFloat(discountInput.value) || 0;

    // Calculate the total for this row
    const discountAmount = price * (discountPercentage / 100);
    const totalRowPrice = (price - discountAmount) * qty;

    // Update the total input for this row
    totalInput.value = totalRowPrice.toFixed(2);
  }

  // Function to update all calculations
  function updateAllCalculations() {
    // Calculate subtotal (sum of all row totals)
    let subTotal = 0;
    const itemRows = Array.from(tableBody.querySelectorAll('tr')).filter(row =>
      row.firstElementChild &&
      !row.firstElementChild.hasAttribute('colspan') &&
      row.cells.length > 5);

    itemRows.forEach(row => {
      const totalInput = row.querySelector('td:nth-child(6) input');
      if (totalInput) {
        subTotal += parseFloat(totalInput.value) || 0;
      }
    });

    // Update subtotal field
    document.getElementById('subTotal').value = subTotal.toFixed(2);

    // Calculate VAT
    const vatAmount = subTotal * VAT_RATE;
    document.getElementById('vatAmount').value = vatAmount.toFixed(2);

    // Calculate discount
    const discountAmount = subTotal * DISCOUNT_RATE;
    document.getElementById('discount').value = discountAmount.toFixed(2);

    // Get shipping charge
    const shippingCharge = parseFloat(document.getElementById('shippingCharge').value) || 0;

    // Calculate total amount
    const totalAmount = subTotal + vatAmount - discountAmount + shippingCharge;
    document.getElementById('totalAmount').value = totalAmount.toFixed(2);
  }

  // Helper function to get ancestor by tag name
  function getAncestorByTagName(element, tagName) {
    while (element && element.tagName !== tagName.toUpperCase()) {
      element = element.parentElement;
    }
    return element;
  }

  // Initialize first row calculations
  const firstRow = tableBody.querySelector('tr');
  if (firstRow) {
    updateRowTotal(firstRow);
  }
});

//Invoice Status
VirtualSelect.init({
  ele: "#invoiceStatus",
  options: [
      { label: "همه", value: "All" },
      { label: "پرداخت شده", value: "Paid" },
      { label: "پرداخت نشده", value: "Unpaid" },
      { label: "در انتظار", value: "Pending" },
      { label: "معوقه", value: "Overdue" },
  ],
});

// Jalali datepicker
  document.addEventListener("DOMContentLoaded", function () {
    jalaliDatepicker.startWatch({
      selector: "input[data-jdp]",
      autoShow: true,  
      autoHide: true,  
      hideAfterChange: true,
      persianDigits: true,          
    });
  });