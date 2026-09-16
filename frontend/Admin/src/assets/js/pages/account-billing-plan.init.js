import { icons, createIcons } from "lucide";


VirtualSelect.init({
  ele: '#countrySelect',
  options: [
    { label: 'افغانستان', value: '1' },
    { label: 'ایران', value: '2' },
    { label: 'آلبانی', value: '3' },
    { label: 'الجزیره', value: '3' },
    { label: 'زامبیا', value: '3' },
    { label: 'زیمباموه', value: '3' },
  ],
  selectedValue: 0
});

// Function to handle setting a card as default
function setDefault(cardId) {
  const defaultLinks = document.querySelectorAll(`[id^="setDefault"]`);
  defaultLinks.forEach(link => {
    link.querySelector('span').textContent = 'تنظیم به عنوان پیش‌فرض';
  });
  const currentLink = document.getElementById(`setDefault${cardId}`);
  currentLink.querySelector('span').textContent = 'تنظیم به عنوان پیش‌فرض';
}

// Function to handle setting the card ID when editing
function setCard(cardId) {
  // You can add logic here to populate the modal with the card details
  console.log(`Editing card with ID: ${cardId}`);
}

// Event listeners for setting default cards
document.getElementById('setDefault1').addEventListener('click', () => setDefault(1));
document.getElementById('setDefault2').addEventListener('click', () => setDefault(2));
document.getElementById('setDefault3').addEventListener('click', () => setDefault(3));

// Input formatting for card number
document.getElementById('cardNumberInput').addEventListener('input', function (e) {
  let value = e.target.value.replace(/[^0-9]/g, '').slice(0, 16);
  if (value.length >= 4) value = value.slice(0, 4) + ' ' + value.slice(4);
  if (value.length >= 9) value = value.slice(0, 9) + ' ' + value.slice(9);
  if (value.length >= 14) value = value.slice(0, 14) + ' ' + value.slice(14);
  e.target.value = value;
});

// Input formatting for CVV
document.getElementById('cvvInput').addEventListener('input', function (e) {
  e.target.value = e.target.value.replace(/[^0-9]/g, '').slice(0, 3);
});

// Input formatting for expiry date
document.getElementById('expiryDateInput').addEventListener('input', function (e) {
  let value = e.target.value.replace(/[^0-9]/g, '');
  if (value.length >= 2) value = value.slice(0, 2) + '/' + value.slice(2);
  value = value.slice(0, 7); // Limit to 7 characters (MM/YYYY)
  e.target.value = value;
});

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
  // Find the save/submit button in the modal
  // This uses a more specific selector to find the button in the modal
  const saveButton = document.querySelector('#exampleModal .btn-primary') ||
    document.querySelector('#exampleModal button[type="submit"]');

  if (saveButton) {
    saveButton.addEventListener('click', function () {
      // Get input values from modal
      const name = document.getElementById('namePersonalInput')?.value || '';
      const address = document.getElementById('addressInput')?.value || '';
      const city = document.getElementById('cityInput')?.value || '';
      const state = document.getElementById('stateInput')?.value || '';
      const zip = document.getElementById('zipCodeInput')?.value || '';
      const phone = document.getElementById('phoneNumberInput')?.value || '';

      // Update card content
      if (document.getElementById('displayName')) {
        document.getElementById('displayName').textContent = name;
      }

      if (document.getElementById('displayAddress')) {
        document.getElementById('displayAddress').textContent = `${address}, ${city}, ${state},`;
      }

      if (document.getElementById('displayCountryZip')) {
        document.getElementById('displayCountryZip').textContent = `ایران - ${zip}.`;
      }

      if (document.getElementById('displayPhone')) {
        document.getElementById('displayPhone').textContent = phone;
      }
    });
  } else {
    console.error('Save button not found in modal');
  }
});

// Global variable to store which card is being edited
let currentCardEditing = null;

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
  // Get the modal element and form
  const paymentModal = document.getElementById('paymentModal');
  const cardForm = paymentModal.querySelector('form');
  const modalTitle = document.getElementById('paymentModalLabel');

  // Get all "Set as Default" links
  const defaultLinks = document.querySelectorAll('[id^="setDefault"]');

  // Initialize card data (simulating database)
  const cardData = {
    1: { number: '1547', expiry: '01/2030', name: 'جان دو', type: 'visa' },
    2: { number: '8749', expiry: '24/2030', name: 'جین اسمیت', type: 'american' },
    3: { number: '3641', expiry: '13/2028', name: 'الکس جانسون', type: 'mastercard' }
  };

  // Track existing cards to avoid duplicates
  const existingCards = new Set(Object.keys(cardData).map(Number));
  let nextCardId = Math.max(...existingCards) + 1;

  // Function to set a card as the editing target
  window.setCard = function (cardId) {
    currentCardEditing = cardId;
    modalTitle.textContent = 'ویرایش کارت';

    // Pre-fill form with card data
    const card = cardData[cardId];
    if (card) {
      document.getElementById('cardNumberInput').value = 'xxxx xxxx xxxx ' + card.number;
      document.getElementById('expiryDateInput').value = card.expiry;
      document.getElementById('nameOnTheCardInput').value = card.name;
      document.getElementById('cvvInput').value = ''; // For security, don't pre-fill CVV
    }
  };

  // Find the "Add New Card" button using the exact markup from your DOM
  // This is the link with the circle-plus icon
  const addCardLinks = document.querySelectorAll('[data-bs-target="#paymentModal"]');
  const addCardButton = Array.from(addCardLinks).find(link => {
    return link.classList.contains('card') || link.querySelector('.card-body.avatar');
  });

  if (addCardButton) {
    addCardButton.addEventListener('click', function () {
      currentCardEditing = null;
      modalTitle.textContent = 'افزودن کارت';

      // Clear form inputs
      document.getElementById('cardNumberInput').value = '';
      document.getElementById('expiryDateInput').value = '';
      document.getElementById('nameOnTheCardInput').value = '';
      document.getElementById('cvvInput').value = '';
      document.getElementById('defaultCheck1').checked = false;
    });
  }

  // Handle form submission
  cardForm.addEventListener('submit', function (event) {
    event.preventDefault();

    // Get form values
    const cardNumber = document.getElementById('cardNumberInput').value;
    const expiryDate = document.getElementById('expiryDateInput').value;
    const cardName = document.getElementById('nameOnTheCardInput').value;
    const cvv = document.getElementById('cvvInput').value;
    const isDefault = document.getElementById('defaultCheck1').checked;

    // Validate inputs
    if (!cardNumber || !expiryDate || !cardName || !cvv) {
      return;
    }

    // Format the card number to display only last 4 digits
    const lastFour = cardNumber.replace(/\D/g, '').slice(-4);

    if (currentCardEditing) {
      // Update existing card
      updateCard(currentCardEditing, lastFour, expiryDate, cardName, isDefault);
    } else {
      // Add new card
      addNewCard(lastFour, expiryDate, cardName, isDefault);
    }

    // Close the modal
    const modalInstance = window.bootstrap.Modal.getInstance(paymentModal);
    modalInstance.hide();
  });

  // Set default card functionality
  defaultLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();

      // Remove active class from all default links
      defaultLinks.forEach(item => {
        item.innerHTML = '<span>تنظیم به عنوان پیش‌فرض</span>';
        item.classList.remove('active');
      });

      // Set the selected card as default
      this.innerHTML = '<i data-lucide="check-circle"></i> <span>پیش‌فرض</span>';
      this.classList.add('active');

      createIcons({ icons });
    });
  });

  // Function to add a new card to the UI
  function addNewCard(lastFour, expiryDate, cardName, isDefault) {
    // Determine card type based on first digit (simplified)
    let cardType;
    const firstDigit = document.getElementById('cardNumberInput').value.replace(/\D/g, '')[0];

    if (firstDigit === '4') {
      cardType = 'visa';
    } else if (firstDigit === '5') {
      cardType = 'mastercard';
    } else if (firstDigit === '3') {
      cardType = 'american';
    } else {
      cardType = 'visa'; // Default to visa
    }

    // Create new card ID
    const newCardId = nextCardId++;

    // Add to our simulated database
    cardData[newCardId] = {
      number: lastFour,
      expiry: expiryDate,
      name: cardName,
      type: cardType
    };

    // Add to set of existing cards to prevent duplicates
    existingCards.add(newCardId);

    // Find the exact row container using your DOM structure
    const rowContainer = document.querySelector('.card-body > .payment-cards');
    if (!rowContainer) {
      return;
    }

    // Create the new card element following your exact DOM structure
    const newCardElement = document.createElement('div');
    newCardElement.className = 'col-12 col-sm-6 col-xl-3';
    newCardElement.innerHTML = `
      <div class="card mb-0">
        <div class="card-body payment-gradient">
          <img src="assets/images/payment/${cardType}.png" loading="lazy" alt="${cardType}" class="h-10">
        </div>
        <div class="card-body pt-0">
          <div>
            <h6 class="mb-1">xxxx xxxx xxxx ${lastFour}</h6>
            <p class="text-muted">${expiryDate} انقضا در</p>
          </div>
          <div class="d-flex justify-content-between align-items-center mt-5">
            <a href="#!" class="link link-custom-success" id="setDefault${newCardId}">
              <span>تنظیم به عنوان پیش‌فرض</span>
            </a>
            <a href="#!" class="link link-custom-primary" data-bs-toggle="modal" data-bs-target="#paymentModal" onclick="setCard(${newCardId})">
              <i data-lucide="pencil" class="size-4"></i> ویرایش
            </a>
          </div>
        </div>
      </div>
    `;

    // Find the "Add new card" element to insert before it
    const addNewCardColumn = rowContainer.querySelector('.col-12.col-sm-6.col-xl-3:last-child');

    if (addNewCardColumn) {
      // Insert before the "Add new card" column
      rowContainer.insertBefore(newCardElement, addNewCardColumn);
    } else {
      // Fallback: just append to the row
      rowContainer.appendChild(newCardElement);
    }

    createIcons({ icons });

    // Set up event listener for the new "Set as Default" link
    const newDefaultLink = document.getElementById(`setDefault${newCardId}`);
    if (newDefaultLink) {
      newDefaultLink.addEventListener('click', function (e) {
        e.preventDefault();

        // Get all default links (including the new one)
        const allDefaultLinks = document.querySelectorAll('[id^="setDefault"]');

        // Remove active class from all default links
        allDefaultLinks.forEach(item => {
          item.innerHTML = '<span>تنظیم به عنوان پیش‌فرض</span>';
          item.classList.remove('active');
        });

        // Set the selected card as default
        this.innerHTML = '<i data-lucide="check-circle"></i> <span>پیش‌فرض</span>';
        this.classList.add('active');

        createIcons({ icons });
      });
    }

    // If set as default, update UI
    if (isDefault && newDefaultLink) {
      setTimeout(() => {
        newDefaultLink.click();
      }, 100);
    }
  }

  // Function to update an existing card
  function updateCard(cardId, lastFour, expiryDate, cardName, isDefault) {
    // Update in our simulated database
    if (cardData[cardId]) {
      cardData[cardId].number = lastFour;
      cardData[cardId].expiry = expiryDate;
      cardData[cardId].name = cardName;
    }

    // Find the card using the exact DOM structure from your HTML
    const cardElement = document.querySelector(`[onclick="setCard(${cardId})"]`);
    if (cardElement) {
      const cardContainer = cardElement.closest('.card');
      if (cardContainer) {
        const cardDetails = cardContainer.querySelector('h6');
        const expiryDetails = cardContainer.querySelector('p.text-muted');

        if (cardDetails) cardDetails.textContent = `xxxx xxxx xxxx ${lastFour}`;
        if (expiryDetails) expiryDetails.textContent = `انقضا در ${expiryDate}`;
      }
    }

    // If set as default, update UI
    if (isDefault) {
      const defaultLink = document.getElementById(`setDefault${cardId}`);
      if (defaultLink) {
        defaultLink.click();
      }
    }
  }

  // Input formatting
  const cardNumberInput = document.getElementById('cardNumberInput');
  if (cardNumberInput) {
    cardNumberInput.addEventListener('input', function (e) {
      // Format card number with spaces
      let value = e.target.value.replace(/\D/g, '');
      if (value.length > 16) value = value.slice(0, 16);

      // Add spaces every 4 digits
      let formattedValue = '';
      for (let i = 0; i < value.length; i++) {
        if (i > 0 && i % 4 === 0) {
          formattedValue += ' ';
        }
        formattedValue += value[i];
      }

      e.target.value = formattedValue;
    });
  }

  const cvvInput = document.getElementById('cvvInput');
  if (cvvInput) {
    cvvInput.addEventListener('input', function (e) {
      // Only allow numbers and max 3 digits
      e.target.value = e.target.value.replace(/\D/g, '').slice(0, 3);
    });
  }

  const expiryDateInput = document.getElementById('expiryDateInput');
  if (expiryDateInput) {
    expiryDateInput.addEventListener('input', function (e) {
      // Format as MM/YYYY
      let value = e.target.value.replace(/\D/g, '');

      if (value.length > 6) value = value.slice(0, 6);

      if (value.length > 2) {
        e.target.value = value.slice(0, 2) + '/' + value.slice(2);
      } else {
        e.target.value = value;
      }
    });
  }
});