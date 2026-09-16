import { createIcons, icons } from "lucide";

VirtualSelect.init({
  ele: '#statusSelect2',
  options: [
    { label: 'مشتری', value: '1' },
    { label: 'شخصی', value: '2' },
    { label: 'کارمند', value: '3' },
    { label: 'بازاریاب', value: '4' },
  ],
  selectedValue: 0
});
/**
* ContactManager - Handles operations for contact management
*/
class ContactManager {
  constructor() {
    // Store DOM elements
    this.elements = {
      table: document.querySelector('table tbody'),
      tableHeaders: document.querySelectorAll('table th.table-row'),
      searchInput: document.getElementById('searchContactInput'),
      checkAllBox: document.getElementById('checkAllData'),
      pagination: document.querySelector('.pagination'),
      resultsInfo: document.querySelector('#paginationInfo'),
      addContactForm: document.querySelector('#createContactModal form'),
      deleteBtn: document.querySelector('.btn-danger.btn-icon'),
      exportBtn: document.querySelector('.btn-light:nth-child(2)'),
      sortBtn: document.getElementById('filterDropdown')
    };

    // Contact data and state
    this.contacts = [];
    this.filteredContacts = [];
    this.currentPage = 1;
    this.itemsPerPage = 10;
    this.selectedContacts = new Set();

    // Sort state tracking
    this.currentSortColumn = null;
    this.sortDirection = 'asc';

    // Initialize the application
    this.init();
    this.initializeEventListeners();
  }

  setupSortableTable() {
    // Add click event listeners to all table headers except the first (checkbox) and last (actions)
    const sortableHeaders = Array.from(this.elements.tableHeaders).slice(1, -1);

    sortableHeaders.forEach((header, index) => {
      // Make the headers look clickable
      header.classList.add('cursor-pointer');

      // Add sort icons (initially hidden)
      const headerText = header.textContent;
      header.innerHTML = `
        ${headerText}
        <span class="sort-icon ms-1 opacity-0">
          <i class="ri-arrow-up-line sort-up"></i>
          <i class="ri-arrow-down-line sort-down d-none"></i>
        </span>
      `;

      // Add the column name as data attribute for easier reference
      const columnName = this.getColumnNameByIndex(index);
      header.dataset.column = columnName;

      // Add click event
      header.addEventListener('click', () => this.handleColumnSort(columnName, header));
    });
  }

  // Helper method to map index to column name
  getColumnNameByIndex(index) {
    const columnMap = [
      'id',
      'name',
      'company',
      'role',
      'email',
      'website',
      'status'
    ];
    return columnMap[index];
  }

  // Add this method to handle column sorting
  handleColumnSort(column, headerElement) {
    // Toggle sort direction if clicking the same column again
    if (this.currentSortColumn === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.currentSortColumn = column;
      this.sortDirection = 'asc';
    }

    // Reset all header icons
    document.querySelectorAll('.sort-icon').forEach(icon => {
      icon.classList.add('opacity-0');
      icon.querySelector('.sort-up').classList.remove('d-none');
      icon.querySelector('.sort-down').classList.add('d-none');
    });

    // Show the correct icon for the current sort
    const sortIcon = headerElement.querySelector('.sort-icon');
    sortIcon.classList.remove('opacity-0');

    if (this.sortDirection === 'asc') {
      sortIcon.querySelector('.sort-up').classList.remove('d-none');
      sortIcon.querySelector('.sort-down').classList.add('d-none');
    } else {
      sortIcon.querySelector('.sort-up').classList.add('d-none');
      sortIcon.querySelector('.sort-down').classList.remove('d-none');
    }

    // Sort the contacts
    this.sortContacts(column, this.sortDirection);

    // Update the UI
    this.currentPage = 1;
    this.renderContacts();
    this.setupPagination();
  }

  // Add this method to sort contacts by a column
  sortContacts(column, direction) {
    this.filteredContacts.sort((a, b) => {
      let valueA = a[column];
      let valueB = b[column];

      // Handle case-insensitive string comparison
      if (typeof valueA === 'string') {
        valueA = valueA.toLowerCase();
      }
      if (typeof valueB === 'string') {
        valueB = valueB.toLowerCase();
      }

      // Handle numeric comparison for ID
      if (column === 'id') {
        // Extract numeric part from ID strings like "PEC-12345"
        const numA = parseInt(valueA.replace(/\D/g, ''));
        const numB = parseInt(valueB.replace(/\D/g, ''));

        return direction === 'asc' ? numA - numB : numB - numA;
      }

      // Special handling for nested name within HTML
      if (column === 'name') {
        // Extract just the name part from the contacts
        valueA = a.name.toLowerCase();
        valueB = b.name.toLowerCase();
      }

      // Standard comparison
      if (valueA < valueB) {
        return direction === 'asc' ? -1 : 1;
      }
      if (valueA > valueB) {
        return direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }


  // Initialize the application
  init() {
    this.loadContacts();
    this.setupEventListeners();
    this.setupSortableTable();
  }

  initializeEventListeners() {
    // Store reference to 'this' to use in event listeners
    const self = this;

    // Add event listener for "select all" checkbox
    this.elements.checkAllBox.addEventListener('change', function () {
      self.handleSelectAll();
    });

    // Add event listener for the delete button
    const deleteButton = document.querySelector('.btn-danger.btn-icon');
    if (deleteButton) {
      deleteButton.addEventListener('click', function () {
        self.deleteSelectedContacts();
      });
    }

    // Add event listeners for individual checkboxes
    document.querySelectorAll('.contact-check').forEach(checkbox => {
      checkbox.addEventListener('change', function (e) {
        const contactId = this.id.replace('check-', '');

        if (this.checked) {
          self.selectedContacts.add(contactId);
        } else {
          self.selectedContacts.delete(contactId);
        }

        // Update select all checkbox and delete button
        self.updateSelectAllCheckbox();
        self.updateDeleteButton();
      });
    });
  }

  // Load contact data from JSON (would normally be a fetch call)
  loadContacts() {
    this.contacts = contactsData; // Assuming contactsData is defined elsewhere
    this.filteredContacts = [...this.contacts];
    this.renderContacts();
    this.setupPagination();
  }

  // Set up all event listeners
  setupEventListeners() {
    // Search functionality
    this.elements.searchInput.addEventListener('input', () => this.handleSearch());

    // Check all checkbox functionality
    this.elements.checkAllBox.addEventListener('change', () => this.toggleSelectAll());

    // Delete selected contacts
    this.elements.deleteBtn.addEventListener('click', () => this.deleteSelectedContacts());

    // Export contacts
    this.elements.exportBtn.addEventListener('click', () => this.exportContacts());

    // Add contact form submission
    this.elements.addContactForm.addEventListener('submit', (e) => this.handleAddContact(e));

    // Add reset form when modal is opened to create a new contact
    const createContactBtn = document.querySelector('[data-bs-target="#createContactModal"]');
    if (createContactBtn) {
      createContactBtn.addEventListener('click', () => this.resetContactForm());
    }

    // Reset form when modal is hidden (regardless of how it was closed)
    const createContactModal = document.getElementById('createContactModal');
    createContactModal.addEventListener('hidden.bs.modal', () => this.resetContactForm());

    // Add image input validation
    const imageInput = document.getElementById('imageInput');
    imageInput.addEventListener('change', () => this.validateImage(imageInput));

    // Sort dropdown
    document.querySelectorAll('#filterDropdown + .dropdown-menu .dropdown-item').forEach(item => {
      item.addEventListener('click', (e) => this.handleSort(e));
    });
  }

  // Render contacts based on current page and filters
  renderContacts() {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    const currentPageData = this.filteredContacts.slice(startIndex, endIndex);

    // Clear existing rows
    while (this.elements.table.children.length > 1) {
      this.elements.table.removeChild(this.elements.table.lastChild);
    }

    // Check if there are no contacts to display
    if (this.filteredContacts.length === 0) {
      // Create a new row with the empty state message
      const emptyRow = document.createElement('tr');

      // Count the number of columns in the table
      const colCount = this.elements.table.querySelector('tr').children.length;

      emptyRow.innerHTML = `
        <td colspan="${colCount}" class="text-center py-4">
          <div class="d-flex flex-column align-items-center">
            <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" class="mx-auto size-12" viewBox="0 0 48 48">
              <linearGradient id="SVGID_1__h35ynqzIJzH4_gr1" x1="34.598" x2="15.982" y1="15.982" y2="34.598" gradientUnits="userSpaceOnUse">
                <stop offset="0" stop-color="#60e8fe"></stop>
                <stop offset=".033" stop-color="#6ae9fe"></stop>
                <stop offset=".197" stop-color="#97f0fe"></stop>
                <stop offset=".362" stop-color="#bdf5ff"></stop>
                <stop offset=".525" stop-color="#dafaff"></stop>
                <stop offset=".687" stop-color="#eefdff"></stop>
                <stop offset=".846" stop-color="#fbfeff"></stop>
                <stop offset="1" stop-color="#fff"></stop>
              </linearGradient>
              <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164 S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331 c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
              <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0 l-4.331-4.331"></path>
              <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
              <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
            </svg>
            <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
            <p class="text-muted mb-0">ما نتوانستیم هیچ مخاطبی مطابق با جستجوی شما پیدا کنیم.</p>
          </div>
        </td>
      `;

      this.elements.table.appendChild(emptyRow);

      // Update results info to show 0 results
      this.elements.resultsInfo.innerHTML = 'نمایش <b class="me-1">0-0</b> از <b class="ms-1">0</b> نتیجه';

      return;
    }

    // Add data rows
    currentPageData.forEach(contact => {
      const row = this.createContactRow(contact);
      this.elements.table.appendChild(row);
    });

    // Update results info - only if no selections
    if (this.selectedContacts.size === 0) {
      this.elements.resultsInfo.innerHTML =
        `نمایش <b class="me-1">${startIndex + 1}-${Math.min(endIndex, this.filteredContacts.length)}</b> از <b class="ms-1">${this.filteredContacts.length}</b> نتیجه`;
    } else {
      this.updateSelectionUI();
    }

    // Update the "select all" checkbox based on if all visible items are selected
    this.updateSelectAllCheckbox();
  }

  // Create a table row for a contact
  createContactRow(contact) {
    const tr = document.createElement('tr');
    tr.dataset.id = contact.id;

    tr.innerHTML = `
      <td>
        <div class="form-check check-primary">
          <input class="form-check-input contact-check" type="checkbox" id="check-${contact.id}" 
            ${this.selectedContacts.has(contact.id) ? 'checked' : ''}>
          <label class="form-check-label d-none" for="check-${contact.id}">Check Data</label>
        </div>
      </td>
      <td>${contact.id}</td>
      <td>
        <div class="d-flex align-items-center gap-2">
          <img src="${contact.avatar}" loading="lazy" alt="" class="border-2 border border-2 border-light-subtle rounded-circle size-9">
          <div>
            <h6 class="mb-0"><a class="link link-custom flex-grow-1" href="#!">${contact.name}</a></h6>
            <p class="fs-sm text-muted">${contact.phone}</p>
          </div>
        </div>
      </td>
      <td>${contact.company}</td>
      <td>${contact.role}</td>
      <td>${contact.email}</td>
      <td><span class="badge bg-light-subtle text-muted border border-light-subtle">${contact.website}</span></td>
      <td><span class="badge bg-${contact.statusColor}-subtle text-${contact.statusColor} border border-${contact.statusColor}-subtle">${contact.status}</span></td>
      <td class="whitespace-nowrap">
        <div class="dropdown">
          <a href="#!" class="link link-custom-primary" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="dropdown-button">
            <i class="ri-more-2-fill"></i>
          </a>
          <ul class="dropdown-menu dropdown-menu-end">
            <li><a href="#!" class="dropdown-item d-flex gap-3 align-items-center view-contact" data-id="${contact.id}">
              <i class="ri-eye-line"></i><span>نمای کلی</span></a></li>
            <li><a href="#!" class="dropdown-item d-flex gap-3 align-items-center edit-contact" data-id="${contact.id}">
              <i class="ri-pencil-line"></i>ویرایش</a></li>
            <li><a href="#!" class="dropdown-item d-flex gap-3 align-items-center delete-contact" data-id="${contact.id}">
              <i class="ri-delete-bin-line"></i><span>حذف</span></a></li>
          </ul>
        </div>
      </td>
    `;

    // Add event listeners for this row
    this.setupRowEventListeners(tr, contact.id);

    return tr;
  }

  // Set up event listeners for a contact row
  setupRowEventListeners(row, contactId) {
    // Checkbox toggle for selection
    const checkbox = row.querySelector('.contact-check');
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) {
        this.selectedContacts.add(contactId);
      } else {
        this.selectedContacts.delete(contactId);
      }
      this.updateSelectAllCheckbox();
    });

    // View contact
    // row.querySelector('.view-contact').addEventListener('click', () => this.viewContact(contactId));

    // Edit contact
    row.querySelector('.edit-contact').addEventListener('click', () => this.editContact(contactId));

    // Delete single contact
    row.querySelector('.delete-contact').addEventListener('click', () => this.confirmDeleteContact(contactId));
  }

  // Set up pagination controls
  setupPagination() {
    const totalPages = Math.ceil(this.filteredContacts.length / this.itemsPerPage);
    let paginationHTML = '';

    // Previous button
    paginationHTML += `
      <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#!" data-page="${this.currentPage - 1}">
          <i data-lucide="chevron-right" class="size-4"></i> قبلی
        </a>
      </li>
    `;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
      paginationHTML += `
        <li class="page-item ${this.currentPage === i ? 'active' : ''}">
          <a class="page-link" href="#!" data-page="${i}">${i}</a>
        </li>
      `;
    }

    // Next button
    paginationHTML += `
      <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#!" data-page="${this.currentPage + 1}">
          بعدی <i data-lucide="chevron-left" class="size-4"></i>
        </a>
      </li>
    `;
    this.elements.pagination.innerHTML = paginationHTML;

    // Add event listeners to pagination buttons
    this.elements.pagination.querySelectorAll('.page-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = parseInt(e.currentTarget.dataset.page);
        if (!isNaN(page) && page !== this.currentPage && page > 0 && page <= totalPages) {
          this.currentPage = page;
          this.renderContacts();
          this.setupPagination();
        }
      });
    });

    createIcons({ icons });
  }
  validateImage(imageInput) {
    const errorElement = document.getElementById('imageError');
    errorElement.textContent = '';

    if (imageInput.files && imageInput.files[0]) {
      const file = imageInput.files[0];

      // Check file type
      if (!file.type.match('image.*')) {
        errorElement.textContent = 'لطفا یک فایل تصویری معتبر انتخاب کنید';
        imageInput.value = '';
        return false;
      }

      // Check file size (max 2MB)
      if (file.size > 2 * 1024 * 1024) {
        errorElement.textContent = 'حجم تصویر باید کمتر از 2 مگابایت باشد';
        imageInput.value = '';
        return false;
      }

      // Show image preview (optional enhancement)
      const imagePreview = document.querySelector('#imagePreview');
      if (imagePreview) {
        const reader = new FileReader();
        reader.onload = function (e) {
          imagePreview.style.backgroundImage = `url(${e.target.result})`;
          imagePreview.style.backgroundSize = 'cover';
          imagePreview.style.backgroundPosition = 'center';
          imagePreview.querySelector('i').style.display = 'none';
        };
        reader.readAsDataURL(file);
      }

      return true;
    }

    return false;
  }
  // Handle search functionality
  handleSearch() {
    const searchTerm = this.elements.searchInput.value.toLowerCase().trim();

    if (searchTerm === '') {
      this.filteredContacts = [...this.contacts];
    } else {
      this.filteredContacts = this.contacts.filter(contact =>
        contact.name.toLowerCase().includes(searchTerm) ||
        contact.email.toLowerCase().includes(searchTerm) ||
        contact.company.toLowerCase().includes(searchTerm) ||
        contact.role.toLowerCase().includes(searchTerm)
      );
    }

    this.currentPage = 1;
    this.renderContacts();
    this.setupPagination();
  }

  // Toggle select all contacts
  toggleSelectAll() {
    const isChecked = this.elements.checkAllBox.checked;

    // Update the selectedContacts set
    if (isChecked) {
      // Select all contacts in the filtered list, not just the current page
      this.filteredContacts.forEach(contact => {
        this.selectedContacts.add(contact.id);
      });
    } else {
      // Clear all selections
      this.selectedContacts.clear();
    }

    // Update checkboxes on the current page to match
    const checkboxes = document.querySelectorAll('.contact-check');
    checkboxes.forEach(checkbox => {
      const contactId = checkbox.id.replace('check-', '');
      checkbox.checked = this.selectedContacts.has(contactId);
    });

    // Update UI to reflect selection status
    this.updateSelectionUI();
  }
  updateSelectionUI() {
    // Update result info to show how many are selected
    if (this.selectedContacts.size > 0) {
      this.elements.resultsInfo.innerHTML =
        `انتخاب شده <b class="me-1">${this.selectedContacts.size}</b> از <b class="ms-1">${this.filteredContacts.length}</b> نتیجه`;
    } else {
      // Reset to normal view
      const startIndex = (this.currentPage - 1) * this.itemsPerPage;
      const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredContacts.length);
      this.elements.resultsInfo.innerHTML =
        `نمایش <b class="me-1">${startIndex + 1}-${endIndex}</b> از <b class="ms-1">${this.filteredContacts.length}</b> نتیجه`;
    }

    // Optionally enable/disable action buttons based on selection
    if (this.elements.deleteBtn) {
      this.elements.deleteBtn.disabled = this.selectedContacts.size === 0;
    }
    if (this.elements.exportBtn) {
      this.elements.exportBtn.disabled = this.selectedContacts.size === 0;
    }
  }

  // Handle "select all" checkbox functionality
  handleSelectAll() {
    const checkAllBox = this.elements.checkAllBox;
    const isChecked = checkAllBox.checked;

    // Get all visible contact checkboxes
    const checkboxes = document.querySelectorAll('.contact-check');

    checkboxes.forEach(checkbox => {
      const contactId = checkbox.id.replace('check-', '');

      // Update checkbox state
      checkbox.checked = isChecked;

      // Update selected contacts collection
      if (isChecked) {
        this.selectedContacts.add(contactId);
      } else {
        this.selectedContacts.delete(contactId);
      }
    });

    // Update delete button visibility
    this.updateDeleteButton();
  }

  // Function to update delete button visibility
  updateDeleteButton() {
    const deleteButton = document.querySelector('.btn-danger.btn-icon');
    if (this.selectedContacts.size > 0) {
      deleteButton.classList.remove('d-none');
    } else {
      deleteButton.classList.add('d-none');
    }
  }

  updateSelectAllCheckbox() {
    const checkboxes = document.querySelectorAll('.contact-check');

    // Check if all visible contacts are selected
    let allSelected = true;
    checkboxes.forEach(checkbox => {
      const contactId = checkbox.id.replace('check-', '');
      if (!this.selectedContacts.has(contactId)) {
        allSelected = false;
      }
    });

    this.elements.checkAllBox.checked = checkboxes.length > 0 && allSelected;

    // Update delete button visibility
    this.updateDeleteButton();
  }

  // Delete selected contacts
  deleteSelectedContacts() {
    this.contacts = this.contacts.filter(contact => !this.selectedContacts.has(contact.id));
    this.filteredContacts = this.filteredContacts.filter(contact => !this.selectedContacts.has(contact.id));
    this.selectedContacts.clear();

    this.currentPage = 1;
    this.renderContacts();
    this.setupPagination();
  }

  // Confirm deletion of a single contact
  confirmDeleteContact(contactId) {
    // Use the modal instead of confirm for better UX
    const deleteModal = document.getElementById('deleteModal');
    const deleteBtn = deleteModal.querySelector('.btn-danger');

    // Store the contactId to be deleted
    deleteModal.dataset.contactId = contactId;

    // Set up the delete button click handler
    const deleteHandler = () => {
      const idToDelete = deleteModal.dataset.contactId;
      this.deleteContact(idToDelete);
      deleteBtn.removeEventListener('click', deleteHandler);
      window.bootstrap.Modal.getInstance(deleteModal).hide();
    };

    // Remove any existing event listeners and add the new one
    deleteBtn.removeEventListener('click', deleteHandler);
    deleteBtn.addEventListener('click', deleteHandler);

    // Show the modal
    const modal = new window.bootstrap.Modal(deleteModal);
    modal.show();
  }

  // Delete a single contact
  deleteContact(contactId) {
    this.contacts = this.contacts.filter(contact => contact.id !== contactId);
    this.filteredContacts = this.filteredContacts.filter(contact => contact.id !== contactId);
    this.selectedContacts.delete(contactId);

    this.renderContacts();
    this.setupPagination();
  }

  // Export contacts as CSV
  exportContacts() {
    // Determine which contacts to export
    const contactsToExport = this.selectedContacts.size > 0
      ? this.contacts.filter(contact => this.selectedContacts.has(contact.id))
      : this.filteredContacts;

    // Create CSV content
    const headers = ['ID', 'Name', 'Company', 'Role', 'Email', 'Phone', 'Website', 'Status'];
    let csvContent = headers.join(',') + '\n';

    contactsToExport.forEach(contact => {
      const row = [
        contact.id,
        `"${contact.name}"`,
        `"${contact.company}"`,
        `"${contact.role}"`,
        contact.email,
        contact.phone,
        contact.website,
        contact.status
      ].join(',');
      csvContent += row + '\n';
    });

    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'contacts.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Handle the add contact form submission
  handleAddContact(e) {
    e.preventDefault();

    // Get form data
    const contactId = document.getElementById('contactId').value.trim();
    const fullName = document.getElementById('fullName').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const company = document.getElementById('companyName').value.trim();
    const role = document.getElementById('role').value.trim();
    const website = document.getElementById('website').value.trim();
    const imageInput = document.getElementById('imageInput');

    // Basic validation
    if (!fullName || !email || !phone) {
      alert('لطفا تمام فیلدهای ضروری را پر کنید');
      return;
    }

    // Determine if this is an edit or an add
    const isEdit = contactId !== '';

    // Get the existing contact if editing
    let existingContact = null;
    if (isEdit) {
      existingContact = this.contacts.find(c => c.id === contactId);
      if (!existingContact) {
        alert('مخاطب یافت نشد');
        return;
      }
    }
    const statusMap = {
      '1': { label: 'مشتری', color: 'pink' },
      '2': { label: 'شخصی', color: 'warning' },
      '3': { label: 'کارمند', color: 'success' },
      '4': { label: 'بازاریاب', color: 'info' }
    };


    // Define the processContact function before using it
    const processContact = (avatar) => {
      const selectedValue = document.querySelector('#statusSelect2').virtualSelect.getValue();
      const statusInfo = statusMap[selectedValue] || statusMap['1']; // Default to 'Customer'

      const status = statusInfo.label;
      const statusColor = statusInfo.color;

      if (isEdit) {
        existingContact.name = fullName;
        existingContact.email = email;
        existingContact.phone = phone;
        existingContact.company = company || 'مشخص نشده';
        existingContact.role = role || 'مشخص نشده';
        existingContact.website = website || 'example.com';
        existingContact.avatar = avatar;
        existingContact.status = status;
        existingContact.statusColor = statusColor;
      } else {
        const newContact = {
          id: `PEC-${Math.floor(10000 + Math.random() * 90000)}`,
          name: fullName,
          email: email,
          phone: phone,
          company: company || 'مشخص نشده',
          role: role || 'مشخص نشده',
          website: website || 'example.com',
          status: status,
          statusColor: statusColor,
          avatar: avatar
        };

        this.contacts.unshift(newContact);
      }

      // Update filtered contacts
      this.filteredContacts = [...this.contacts];

      // Reset the form and image preview
      this.resetContactForm();

      // Close the modal
      const modal = window.bootstrap.Modal.getInstance(document.getElementById('createContactModal'));
      modal.hide();

      // Update the display
      this.renderContacts();
      this.setupPagination();
    };

    // Handle image upload
    let avatarUrl = isEdit ? existingContact.avatar : 'assets/images/avatar/user-1.png';

    if (imageInput.files && imageInput.files[0]) {
      // In a real application, you would upload the file to a server
      // For this example, we'll use FileReader to create a data URL
      const reader = new FileReader();
      reader.onload = (event) => {
        avatarUrl = event.target.result;
        processContact(avatarUrl);
      };
      reader.readAsDataURL(imageInput.files[0]);
    } else {
      processContact(avatarUrl);
    }
  }

  resetContactForm() {
    // Get the modal and form elements
    const modal = document.getElementById('createContactModal');
    const form = this.elements.addContactForm;
    const modalTitle = modal.querySelector('.modal-title');
    const submitBtn = form.querySelector('button[type="submit"]');

    // Reset to "Add Contact" mod

    // Clear the contact ID
    document.getElementById('contactId').value = '';

    // Reset all form fields
    form.reset();
    document.getElementById('imageError').textContent = '';

    // Reset the image preview
    const imagePreview = document.querySelector('#imageLabel');
    if (imagePreview) {
      imagePreview.style.backgroundImage = '';
      imagePreview.style.backgroundSize = '';
      imagePreview.style.backgroundPosition = '';
      imagePreview.querySelector('i').style.display = 'block';
    }
  }


  // View contact details
  // viewContact(contactId) {
  //   const contact = this.contacts.find(c => c.id === contactId);
  //   if (contact) {
  //     alert(`Contact Details:\nName: ${contact.name}\nEmail: ${contact.email}\nPhone: ${contact.phone}`);
  //     // In a real app, you would show a detailed view modal or page
  //   }
  // }

  // Edit a contact
  editContact(contactId) {
    const contact = this.contacts.find(c => c.id === contactId);
    if (!contact) return;

    // Get the modal and form elements
    const modal = document.getElementById('createContactModal');
    const form = this.elements.addContactForm;

    // Check if modal and form elements exist
    if (!modal || !form) {
      console.error('Modal or form not found in DOM');
      return;
    }

    // Find the modal title - be more flexible in the selector
    const modalTitle = modal.querySelector('.modal-title');
    const submitBtn = form.querySelector('button[type="submit"]');

    // Safely update modal title and button text for edit mode
    if (modalTitle) {
      modalTitle.textContent = 'ویرایش مخاطب';
    }

    if (submitBtn) {
      submitBtn.textContent = 'آپدیت مخاطب';
    }

    // Get contactId input and validate it exists
    const contactIdInput = document.getElementById('contactId');
    if (contactIdInput) {
      contactIdInput.value = contact.id;
    }

    // Safely populate form fields with contact data - check each field exists
    const fullNameInput = document.getElementById('fullName');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const companyInput = document.getElementById('companyName');
    const roleInput = document.getElementById('role');
    const websiteInput = document.getElementById('website');

    if (fullNameInput) fullNameInput.value = contact.name;
    if (emailInput) emailInput.value = contact.email;
    if (phoneInput) phoneInput.value = contact.phone;
    if (companyInput) companyInput.value = contact.company;
    if (roleInput) roleInput.value = contact.role;
    if (websiteInput) websiteInput.value = contact.website;

    // Set the image preview if available
    const imagePreview = document.querySelector('#imageLabel');
    if (imagePreview && contact.avatar) {
      imagePreview.style.backgroundImage = `url(${contact.avatar})`;
      imagePreview.style.backgroundSize = 'cover';
      imagePreview.style.backgroundPosition = 'center';

      // Make sure the icon element exists before trying to hide it
      const icon = imagePreview.querySelector('i');
      if (icon) {
        icon.style.display = 'none';
      }
    }

    // Show the modal
    try {
      const bsModal = new window.bootstrap.Modal(modal);
      bsModal.show();
    } catch (error) {
      console.error('Failed to show modal:', error);
      alert('فرم ویرایش باز نشد. لطفا دوباره امتحان کنید.');
    }
  }


  // Handle sorting
  handleSort(e) {
    const sortType = e.target.textContent.trim();

    switch (sortType) {
      case 'No Sorting':
        this.filteredContacts = [...this.contacts];
        this.currentSortColumn = null;
        break;
      case 'Alphabetical (A -> Z)':
        this.handleColumnSort('name', document.querySelector('[data-column="name"]'));
        break;
      case 'Reverse Alphabetical (Z -> A)':
        this.currentSortColumn = 'name';
        this.sortDirection = 'desc';
        this.sortContacts('name', 'desc');
        break;
      case 'Status':
        this.handleColumnSort('status', document.querySelector('[data-column="status"]'));
        break;
    }

    this.currentPage = 1;
    this.renderContacts();
    this.setupPagination();
  }
}

// Sample data
const contactsData = [
  {
    id: 'PEC-24151',
    name: 'پات مارتینز',
    company: 'استار تک داینامیکس',
    role: 'طراح وب',
    email: 'pat.martinez@gmail.com',
    phone: '+890 1829 15781',
    website: 'patmartizen.com',
    status: 'مشتری',
    statusColor: 'pink',
    avatar: 'assets/images/avatar/user-1.png'
  },
  {
    id: 'PEC-24152',
    name: 'جین براون',
    company: 'استار تک داینامیکس',
    role: 'طراح وب',
    email: 'jane.brown@email.com',
    phone: '+957 6326 78821',
    website: 'janebrown.com',
    status: 'شخصی',
    statusColor: 'warning',
    avatar: 'assets/images/avatar/user-2.png'
  },
  {
    id: 'PEC-24153',
    name: 'جان دیویس',
    company: 'استار تک داینامیکس',
    role: 'طراح UI / UX',
    email: 'john.davis@email.com',
    phone: '+264 1427 33002',
    website: 'johndavis.com',
    status: 'مشتری',
    statusColor: 'pink',
    avatar: 'assets/images/avatar/user-3.png'
  },
  {
    id: 'PEC-24154',
    name: 'جردن دیویس',
    company: 'بریت فیوچر تک',
    role: 'طراح گرافیک',
    email: 'jordan.davis@gmail.com',
    phone: '+688 9444 65363',
    website: 'jordandavis.com',
    status: 'مشتری',
    statusColor: 'pink',
    avatar: 'assets/images/avatar/user-4.png'
  },
  {
    id: 'PEC-24155',
    name: 'الکس لی',
    company: 'کوانتوم اینوویشنز',
    role: 'هم‌بنیان‌گذار',
    email: 'alex.lee@outlook.com',
    phone: '+300 8108 69119',
    website: 'alexlee.com',
    status: 'شخصی',
    statusColor: 'warning',
    avatar: 'assets/images/avatar/user-5.png'
  },
  {
    id: 'PEC-24156',
    name: 'کیسی مارتینز',
    company: 'بریت فیوچر تک',
    role: 'طراح گرافیک',
    email: 'casey.martinez@email.com',
    phone: '+646 9347 84543',
    website: 'casetmartinez.com',
    status: 'شخصی',
    statusColor: 'warning',
    avatar: 'assets/images/avatar/user-6.png'
  },
  {
    id: 'PEC-24157',
    name: 'تیلور ویلسون',
    company: 'بریت فیوچر تک',
    role: 'توسعه‌دهنده ASP.Net',
    email: 'taylor.wilson@outlook.com',
    phone: '+749 6102 50325',
    website: 'taylor.com',
    status: 'مشتری',
    statusColor: 'pink',
    avatar: 'assets/images/avatar/user-7.png'
  },
  {
    id: 'PEC-24158',
    name: 'کریس اسمیت',
    company: 'بلواسکای اینترپرایز',
    role: 'مدیر محصول',
    email: 'chris.smith@gmail.com',
    phone: '+829 5728 93265',
    website: 'chrissmith.com',
    status: 'کارمند',
    statusColor: 'info',
    avatar: 'assets/images/avatar/user-8.png'
  },
  {
    id: 'PEC-24159',
    name: 'جین براون',
    company: 'بریت فیوچر تک',
    role: 'توسعه‌دهنده وب',
    email: 'jane.brown@outlook.com',
    phone: '+213 9689 10505',
    website: 'jane.brigth.com',
    status: 'شخصی',
    statusColor: 'warning',
    avatar: 'assets/images/avatar/user-9.png'
  },
  {
    id: 'PEC-24160',
    name: 'جان گارسیا',
    company: 'کوانتوم اینوویشنز',
    role: 'مدیر محصول',
    email: 'john.garcia@yahoo.com',
    phone: '+846 9274 23870',
    website: 'johangarcia.com',
    status: 'شخصی',
    statusColor: 'warning',
    avatar: 'assets/images/avatar/user-10.png'
  },
  {
    id: 'PEC-24161',
    name: 'کریس ویلسون',
    company: 'بلواسکای اینترپرایز',
    role: 'توسعه‌دهنده React',
    email: 'chris.wilson@gmail.com',
    phone: '+285 1994 96029',
    website: 'chriswilson.com',
    status: 'مشتری',
    statusColor: 'pink',
    avatar: 'assets/images/avatar/user-11.png'
  },
  {
    id: 'PEC-24162',
    name: 'الکس لی',
    company: 'بریت فیوچر تک',
    role: 'مهندس نرم‌افزار',
    email: 'alex.lee@email.com',
    phone: '+695 2025 51582',
    website: 'alextech.com',
    status: 'مشتری',
    statusColor: 'pink',
    avatar: 'assets/images/avatar/user-12.png'
  },
  {
    id: 'PEC-24163',
    name: 'کامرون ویلسون',
    company: 'بلواسکای اینترپرایز',
    role: 'توسعه‌دهنده Laravel',
    email: 'cameron.wilson@gmail.com',
    phone: '+840 4447 94334',
    website: 'cameron.com',
    status: 'مشتری',
    statusColor: 'pink',
    avatar: 'assets/images/avatar/user-13.png'
  },
  {
    id: 'PEC-24164',
    name: 'سم براون',
    company: 'بلواسکای اینترپرایز',
    role: 'کارشناس بازاریابی',
    email: 'sam.brown@yahoo.com',
    phone: '+438 6305 33828',
    website: 'sambrown.com',
    status: 'بازاریاب',
    statusColor: 'warning',
    avatar: 'assets/images/avatar/user-14.png'
  },
  {
    id: 'PEC-24165',
    name: 'پات مارتینز',
    company: 'سینرژی سلوشنز',
    role: 'توسعه‌دهنده Laravel',
    email: 'pat.martinez@gmail.com',
    phone: '+356 8229 92921',
    website: 'patmartiz.com',
    status: 'کارمند',
    statusColor: 'info',
    avatar: 'assets/images/avatar/user-15.png'
  },
  {
    id: 'PEC-24166',
    name: 'کریس اسمیت',
    company: 'بریت فیوچر تک',
    role: 'طراح UI / UX',
    email: 'chris.smith@yahoo.com',
    phone: '+880 8152 56315',
    website: 'chrissmith.com',
    status: 'شخصی',
    statusColor: 'warning',
    avatar: 'assets/images/avatar/user-16.png'
  },
  {
    id: 'PEC-24167',
    name: 'کامرون ویلسون',
    company: 'بلواسکای اینترپرایز',
    role: 'هم‌بنیان‌گذار',
    email: 'cameron.wilson@email.com',
    phone: '+599 4447 23760',
    website: 'cameronwilson.com',
    status: 'کارمند',
    statusColor: 'info',
    avatar: 'assets/images/avatar/user-17.png'
  },
  {
    id: 'PEC-24168',
    name: 'کیسی مارتینز',
    company: 'استار پث داینامیکس',
    role: 'طراح UI / UX',
    email: 'casey.martinez@gmail.com',
    phone: '+590 5863 84911',
    website: 'caseystarpath.com',
    status: 'مشتری',
    statusColor: 'pink',
    avatar: 'assets/images/avatar/user-18.png'
  }
];

// Initialize the contact manager when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const contactManager = new ContactManager();
});