import { icons, createIcons } from "lucide";

// Sample data for initial addresses
let addresses = [
    {
        id: 1,
        firstName: "علی",
        lastName: "جوان",
        phoneNumber: "2015184185",
        alternatePhoneNumber: "",
        address: "شریعتی، طالقانی، نرسیده به کوچه اول پلاک 2",
        city: "تهران",
        country: "تهران، ایران",
        zipCode: "33199 8539",
        addressType: "خانه"
    },
    {
        id: 2,
        firstName: "اردلان",
        lastName: "شجاع کاوه",
        phoneNumber: "6179419815",
        alternatePhoneNumber: "",
        address: "خیابان آزادی، کوچه اول پلاک 8",
        city: "اصفهان",
        country: "ایران",
        zipCode: "62144 1437",
        addressType: "محل کار"
    }
];

document.querySelectorAll('.btn-close').forEach(button => {
    button.addEventListener('click', function () {
        const productItem = this.closest('.mb-3');
        if (productItem) {
            productItem.remove();
        }
    });
});
document.addEventListener('DOMContentLoaded', function () {
    // Initial calculation of cart totals
    calculateCartTotals();

    // Add event listeners to all close buttons
    const closeButtons = document.querySelectorAll('.btn-close');
    closeButtons.forEach(button => {
        button.addEventListener('click', function () {
            // Find the parent item container and remove it
            const itemContainer = this.closest('.mb-3');
            if (itemContainer) {
                itemContainer.remove();
                // Recalculate totals after removing the item
                calculateCartTotals();
            }
        });
    });

    // Function to handle discount code application
    const discountInput = document.getElementById('discountCode');
    if (discountInput) {
        discountInput.addEventListener('blur', function () {
            // Simple implementation - any code applies 10% discount
            if (this.value.trim() !== '') {
                calculateCartTotals(true);
            } else {
                calculateCartTotals(false);
            }
        });
    }

    // Function to calculate all cart totals
    function calculateCartTotals(applyDiscount = false) {
        // Get all product items
        const productItems = document.querySelectorAll('.card-body > .mb-3:not(:last-of-type)');

        // Calculate subtotal
        let subtotal = 0;
        productItems.forEach(item => {
            const priceElement = item.querySelector('.total-price');
            if (priceElement) {
                const price = parseFloat(priceElement.textContent);
                const quantityText = item.querySelector('.text-muted span:first-child').textContent;
                const quantity = parseInt(quantityText.match(/\d+/)[0]);
                subtotal += price * (quantity / quantity); // Quantity is already factored into the displayed price
            }
        });

        // Update subtotal in table
        const subtotalElement = document.querySelector('tr:nth-child(1) span');
        if (subtotalElement) subtotalElement.textContent = subtotal.toFixed(2);

        // Calculate VAT (6%)
        const vatAmount = subtotal * 0.06;
        const vatElement = document.querySelector('tr:nth-child(2) span');
        if (vatElement) vatElement.textContent = vatAmount.toFixed(2);

        // Calculate discount (10% if applied)
        let discountAmount = 0;
        if (applyDiscount) {
            discountAmount = subtotal * 0.1;
        }
        const discountElement = document.querySelector('tr:nth-child(3) span');
        if (discountElement) discountElement.textContent = discountAmount.toFixed(2);

        // Get shipping charge (fixed at $35.00)
        const shippingCharge = 35.00;

        // Calculate total
        const totalAmount = subtotal + vatAmount - discountAmount + shippingCharge;
        const totalElement = document.querySelector('tr:last-child span');
        if (totalElement) totalElement.textContent = totalAmount.toFixed(2);

        // Update UI to show empty cart message if needed
        if (productItems.length === 0) {
            const cardBody = document.querySelector('.card-body');
            if (cardBody) {
                // Remove discount code input and table
                const discountCodeDiv = document.querySelector('.discount-code');
                const table = document.querySelector('table');
                const checkoutButton = document.querySelector('.btn-primary');
                const disclaimer = document.querySelector('#termsAgree');

                if (discountCodeDiv) discountCodeDiv.style.display = 'none';
                if (table) table.style.display = 'none';
                if (checkoutButton) checkoutButton.style.display = 'none';
                if (disclaimer) disclaimer.style.display = 'none';

                // Add empty cart message
                const emptyMessage = document.createElement('div');
                emptyMessage.className = 'text-center py-5';
                emptyMessage.innerHTML = `
                    <i class="fs-40 text-muted" data-lucide="shopping-cart"></i>
                    <h5 class="mt-3">سبد خرید شما خالی است</h5>
                    <p class="text-muted">محصولات ما را مرور کنید و از پیشنهادهای شگفت‌انگیز ما بهره‌مند شوید!</p>
                    <a href="apps-ecommerce-products.html" class="btn btn-primary mt-3">ادامه خرید</a>
                `;
                cardBody.appendChild(emptyMessage);

                createIcons({ icons });
            }
        }
    }
});
// Global variable to track which address is being edited
let editingAddressId = null;

// DOM Elements
const addressForm = document.getElementById('addressForm');
const resetBtn = document.getElementById('resetBtn');
const addressContainer = document.getElementById('addressContainer');
const cardTemplate = document.getElementById('addressCardTemplate');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    renderAddresses();
    setupEventListeners();
});

// Set up event listeners
function setupEventListeners() {
    // Form submit event
    addressForm.addEventListener('submit', handleFormSubmit);

    // Reset button event
    resetBtn.addEventListener('click', resetForm);
}

// Render all addresses using template
function renderAddresses() {
    addressContainer.innerHTML = '';

    addresses.forEach((address, index) => {
        const card = createAddressCard(address);

        // Mark the first one as selected by default
        if (index === 0) {
            card.querySelector('.select-address').classList.add('btn-primary');
            card.querySelector('.select-address').classList.remove('btn-light');
        }

        addressContainer.appendChild(card);
    });
}

// Create address card using the template
function createAddressCard(address) {
    // Clone the template
    const cardClone = cardTemplate.content.cloneNode(true);

    // Set address data in the card
    cardClone.querySelector('.address-type').textContent = address.addressType;
    cardClone.querySelector('.address-name').textContent = `${address.firstName} ${address.lastName} - ${address.phoneNumber}`;
    cardClone.querySelector('.address-details').textContent =
        `${address.address}, ${address.city}, ${address.country} - ${address.zipCode}`;

    // Add data attributes for identifying the address
    const cardElement = cardClone.querySelector('.card');
    cardElement.dataset.addressId = address.id;

    // Add event listeners
    const editBtn = cardClone.querySelector('.edit-address');
    editBtn.addEventListener('click', () => editAddress(address.id));

    const deleteBtn = cardClone.querySelector('.delete-address');
    deleteBtn.addEventListener('click', () => deleteAddress(address.id));

    const selectBtn = cardClone.querySelector('.select-address');
    selectBtn.addEventListener('click', () => selectAddress(address.id));

    return cardClone;
}

// Handle form submission
function handleFormSubmit(event) {
    event.preventDefault();

    // Get form values
    const formData = {
        firstName: document.getElementById('firstNameInput').value,
        lastName: document.getElementById('lastNameInput').value,
        phoneNumber: document.getElementById('phoneNumberInput').value,
        alternatePhoneNumber: document.getElementById('alternatePhoneNumberInput').value,
        address: document.getElementById('addressInput').value,
        city: document.getElementById('cityDistrictTownInput').value,
        country: document.getElementById('countryNameInput').value,
        zipCode: document.getElementById('zipCodeInput').value,
        addressType: document.querySelector('input[name="addressType"]:checked').value
    };

    if (editingAddressId) {
        // Update existing address
        updateAddress(editingAddressId, formData);
    } else {
        // Add new address
        addAddress(formData);
    }

    // Reset form and collapse
    resetForm();
    const formCollapse = window.bootstrap.Collapse.getInstance(document.getElementById('addressFormCollapse'));
    formCollapse.hide();
}

// Add new address
function addAddress(formData) {
    // Generate new ID
    const newId = addresses.length > 0 ? Math.max(...addresses.map(addr => addr.id)) + 1 : 1;

    // Create new address object
    const newAddress = {
        id: newId,
        ...formData
    };

    // Add to addresses array
    addresses.push(newAddress);

    // Re-render addresses
    renderAddresses();
}

// Update existing address
function updateAddress(id, formData) {
    // Find the address index
    const index = addresses.findIndex(addr => addr.id === id);

    if (index !== -1) {
        // Update the address
        addresses[index] = {
            ...addresses[index],
            ...formData
        };

        // Reset editing state
        editingAddressId = null;
        document.getElementById('formTitle').textContent = 'افزودن آدرس جدید';

        // Re-render addresses
        renderAddresses();
    }
}

// Edit address
function editAddress(id) {
    // Find the address
    const address = addresses.find(addr => addr.id === id);

    if (address) {
        // Set editing state
        editingAddressId = id;
        document.getElementById('formTitle').textContent = 'ویرایش آدرس';

        // Fill form with address data
        document.getElementById('firstNameInput').value = address.firstName;
        document.getElementById('lastNameInput').value = address.lastName;
        document.getElementById('phoneNumberInput').value = address.phoneNumber;
        document.getElementById('alternatePhoneNumberInput').value = address.alternatePhoneNumber || '';
        document.getElementById('addressInput').value = address.address;
        document.getElementById('cityDistrictTownInput').value = address.city;
        document.getElementById('countryNameInput').value = address.country;
        document.getElementById('zipCodeInput').value = address.zipCode;

        // Set address type radio button
        document.getElementById(address.addressType).checked = true;

        // Show form
        const formCollapse = new window.bootstrap.Collapse(document.getElementById('addressFormCollapse'));
        formCollapse.show();
    }
}

// Delete address
function deleteAddress(id) {
    // Remove address from array
    addresses = addresses.filter(addr => addr.id !== id);

    // Re-render addresses
    renderAddresses();
}

// Select address
function selectAddress(id) {
    // Find the address
    const address = addresses.find(addr => addr.id === id);

    if (address) {
        // Get all select buttons
        const buttons = document.querySelectorAll('.select-address');

        buttons.forEach(button => {
            const card = button.closest('.card');
            const cardId = parseInt(card.dataset.addressId);

            if (cardId === id) {
                button.classList.remove('btn-light');
                button.classList.add('btn-primary');
            } else {
                button.classList.remove('btn-primary');
                button.classList.add('btn-light');
            }
        });
    }
}

// Reset form
function resetForm() {
    // Clear form fields
    addressForm.reset();

    // Reset editing state
    editingAddressId = null;
    document.getElementById('formTitle').textContent = 'افزودن آدرس جدید';
}
