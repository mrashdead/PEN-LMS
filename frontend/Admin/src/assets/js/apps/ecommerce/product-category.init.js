// Import the category data
import { createIcons, icons } from 'lucide';

import tableData from '../../../json/apps/ecommerce/category.json';

VirtualSelect.init({
    ele: '#statusSelect',
    options: [
        { label: 'فعال', value: 'Active' },
        { label: 'غیرفعال', value: 'Inactive' }
    ],
});

class TableManager {
    constructor() {
        // Main elements
        this.table = document.querySelector('.table');
        this.tableBody = this.table ? this.table.querySelector('tbody') : null;
        this.tableHead = this.table ? this.table.querySelector('thead') : null;
        this.categoryForm = document.querySelector('#categoryForm');
        this.deleteModal = document.getElementById('deleteModal');

        // Check if required elements exist before proceeding
        if (!this.table || !this.tableBody || !this.categoryForm) {
            console.error('Required DOM elements are missing.');
            return;
        }

        // Bulk action elements
        this.bulkDeleteButton = document.querySelector('button#deleteCategory');

        // Search elements
        this.searchInput = document.getElementById('searchCategoryInput');

        // Pagination elements
        this.paginationContainer = document.querySelector('.pagination');
        this.resultsInfoElement = document.querySelector('#showingResults');

        // Form elements
        this.imageInput = document.getElementById('imageInput');
        this.imagePreview = document.getElementById('imagePreview');
        this.uploadText = document.getElementById('uploadText');
        this.uploadIcon = document.getElementById('uploadIcon');
        this.categoryNameInput = this.categoryForm.querySelector('input[type="email"]');
        this.descriptionInput = this.categoryForm.querySelector('textarea[name="description"]');
        this.statusSelect = document.getElementById('statusSelect');
        this.resetButton = this.categoryForm.querySelector('button#resetBtn');
        this.addButton = this.categoryForm.querySelector('button#addCategoryBtn');

        // Delete modal elements
        this.deleteConfirmButton = this.deleteModal ? this.deleteModal.querySelector('button#confirmDeleteBtn') : null;

        // State variables
        this.editMode = false;
        this.currentEditId = null;
        this.categories = [];
        this.lastId = 0;

        // Pagination state
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.filteredCategories = [];
        this.searchTerm = '';

        // Selected items tracking
        this.selectedItems = new Set();

        // Sorting state
        this.currentSortField = null;
        this.currentSortDirection = 'asc';

        // Initialize
        this.init();
    }

    init() {
        // Load data from imported JSON
        this.loadDataFromJSON();

        // Setup event listeners
        this.setupEventListeners();
        this.initStatusSelect();
        this.setupSortableHeaders();

        // Initialize filtered categories with all categories
        this.filteredCategories = [...this.categories];

        // Render categories with pagination
        this.renderPaginatedCategories();

        // Initialize Lucide icons if available
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    loadDataFromJSON() {
        // Load data from the imported JSON file
        this.categories = Array.isArray(tableData) ? tableData : [];

        // Find the highest ID to continue sequence for new items
        if (this.categories.length > 0) {
            // Assuming IDs are in the format PEC-XXXXX
            this.lastId = Math.max(...this.categories.map(category => {
                const idMatch = category.id.match(/PEC-(\d+)/);
                return idMatch ? parseInt(idMatch[1]) : 0;
            }));
        }
    }

    setupEventListeners() {
        // Image upload preview
        if (this.imageInput) {
            this.imageInput.addEventListener('change', this.handleImageUpload.bind(this));
        }

        // Form submission
        if (this.addButton) {
            this.addButton.addEventListener('click', this.handleFormSubmit.bind(this));
        }

        // Reset form
        if (this.resetButton) {
            this.resetButton.addEventListener('click', this.resetForm.bind(this));
        }

        // Delete confirmation
        if (this.deleteConfirmButton) {
            this.deleteConfirmButton.addEventListener('click', this.confirmDelete.bind(this));
        }

        // Search input with debounce for better performance
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }

        // Bulk delete button
        if (this.bulkDeleteButton) {
            this.bulkDeleteButton.addEventListener('click', this.bulkDelete.bind(this));
        }

        // Check all checkbox
        const checkAllData = document.getElementById('checkAllData');
        if (checkAllData && this.tableBody) {
            checkAllData.addEventListener('change', (e) => {
                if (e.target.checked) {
                    // Select all items in filtered dataset, not just visible ones
                    this.filteredCategories.forEach(category => {
                        this.selectedItems.add(category.id);
                    });
                } else {
                    // Clear all selections
                    this.selectedItems.clear();
                }

                // Update checkboxes on the current page to match the selection state
                const checkboxes = this.tableBody.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(checkbox => {
                    const row = checkbox.closest('tr');
                    if (row && row.dataset.categoryId) {
                        checkbox.checked = this.selectedItems.has(row.dataset.categoryId);
                    }
                });

                this.updateBulkDeleteButtonVisibility();
            });
        }

        // Event delegation for table actions and checkbox changes
        if (this.tableBody) {
            this.tableBody.addEventListener('change', (e) => {
                if (e.target.type === 'checkbox') {
                    this.handleCheckboxChange(e.target);
                    this.updateBulkDeleteButtonVisibility();
                }
            });
        }

        // Global click event for edit, delete actions, and pagination using event delegation
        document.addEventListener('click', this.handleGlobalClick.bind(this));
    }

    setupSortableHeaders() {
        if (!this.tableHead) return;

        // Get all header cells except the first (checkbox) and last (actions) columns
        const headerCells = this.tableHead.querySelectorAll('th');

        // Define the sortable columns and their corresponding data fields
        const sortableColumns = [
            { index: 1, field: 'id', label: 'شماره دسته‌بندی' },
            { index: 2, field: 'category', label: 'نام دسته‌بندی' },
            { index: 3, field: 'quantity', label: 'محصولات' },
            { index: 4, field: 'status', label: 'وضعیت' }
        ];

        // Add click handlers and sort indicators to sortable headers
        sortableColumns.forEach(column => {
            if (headerCells[column.index]) {
                const headerCell = headerCells[column.index];

                // Make the header look clickable
                headerCell.classList.add('sortable');
                headerCell.style.cursor = 'pointer';

                // Update header text to include sort indicators
                const originalText = headerCell.textContent.trim();
                headerCell.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span>${originalText}</span>
                        <span class="sort-icon ms-1">
                            <i class="ri-arrow-up-down-line text-muted opacity-50"></i>
                        </span>
                    </div>
                `;

                // Add click handler
                headerCell.addEventListener('click', () => {
                    this.handleSortClick(column.field);
                });
            }
        });
    }

    // NEW: Handle sort header clicks
    handleSortClick(field) {
        // Toggle direction if clicking the same field
        if (this.currentSortField === field) {
            this.currentSortDirection = this.currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // New field, start with ascending sort
            this.currentSortField = field;
            this.currentSortDirection = 'asc';
        }

        // Update sort indicators in headers
        this.updateSortIndicators(field, this.currentSortDirection);

        // Sort the data
        this.sortCategories(field, this.currentSortDirection);
    }

    // NEW: Update sort indicators in headers
    updateSortIndicators(field, direction) {
        if (!this.tableHead) return;

        // Reset all headers
        const headers = this.tableHead.querySelectorAll('th');
        headers.forEach(header => {
            const sortIcon = header.querySelector('.sort-icon');
            if (sortIcon) {
                sortIcon.innerHTML = '<i class="ri-arrow-up-down-line text-muted opacity-50"></i>';
            }
        });

        // Define the field to header index mapping
        const fieldToIndex = {
            'id': 1,
            'category': 2,
            'quantity': 3,
            'status': 4
        };

        // Update active sort header
        const activeIndex = fieldToIndex[field];
        if (activeIndex !== undefined && headers[activeIndex]) {
            const sortIcon = headers[activeIndex].querySelector('.sort-icon');
            if (sortIcon) {
                sortIcon.innerHTML = direction === 'asc'
                    ? '<i class="ri-arrow-up-line"></i>'
                    : '<i class="ri-arrow-down-line"></i>';
            }
        }
    }

    handleGlobalClick(event) {
        const target = event.target;

        // Edit action
        if (target.closest('a[class*="edit"]') ||
            (target.closest('.dropdown-item') && target.closest('.dropdown-item').innerHTML.includes('ویرایش'))) {
            event.preventDefault();
            const row = target.closest('tr');
            if (row) {
                const categoryId = row.dataset.categoryId;
                this.editCategory(categoryId);
            }
        }

        // Delete action (open modal)
        if (target.closest('a[href="#deleteModal"]') ||
            (target.closest('.dropdown-item') && target.closest('.dropdown-item').innerHTML.includes('حذف'))) {
            event.preventDefault();
            const row = target.closest('tr');
            if (row) {
                const categoryId = row.dataset.categoryId;
                this.openDeleteModal(categoryId);
            }
        }

        // Pagination handlers
        if (target.closest('.page-link')) {
            event.preventDefault();
            const pageLink = target.closest('.page-link');

            if (pageLink.textContent.includes('قبلی')) {
                this.goToPreviousPage();
            } else if (pageLink.textContent.includes('بعدی')) {
                this.goToNextPage();
            } else {
                // Navigate to specific page
                const pageNumber = parseInt(pageLink.textContent);
                if (!isNaN(pageNumber)) {
                    this.goToPage(pageNumber);
                }
            }
        }
    }

    // Manage checkbox changes and selected items tracking
    handleCheckboxChange(checkbox) {
        const row = checkbox.closest('tr');
        if (!row) return;

        const categoryId = row.dataset.categoryId;
        if (!categoryId) return;

        if (checkbox.checked) {
            this.selectedItems.add(categoryId);
        } else {
            this.selectedItems.delete(categoryId);
        }

        this.updateBulkDeleteButtonVisibility();
    }

    // Show/hide bulk delete button based on selections
    updateBulkDeleteButtonVisibility() {
        if (this.bulkDeleteButton) {
            if (this.selectedItems.size > 0) {
                this.bulkDeleteButton.classList.remove('d-none');
            } else {
                this.bulkDeleteButton.classList.add('d-none');
            }
        }
    }

    // Debounce helper for search input
    debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
    updateCheckAllState() {
        const checkAllData = document.getElementById('checkAllData');
        if (!checkAllData) return;

        // Check if all filtered items are selected
        const allSelected = this.filteredCategories.length > 0 &&
            this.filteredCategories.every(category => this.selectedItems.has(category.id));

        // Set the "Check All" checkbox state without triggering its change event
        checkAllData.checked = allSelected;
    }

    // Update handleSearch to NOT clear selections on new search
    handleSearch(event) {
        const searchTerm = event.target.value.trim().toLowerCase();
        this.searchTerm = searchTerm;
        this.currentPage = 1; // Reset to first page on new search

        // Don't clear selections on search
        // this.selectedItems.clear(); <- Remove this line

        this.filterCategories(searchTerm);
        this.renderPaginatedCategories();
        this.updateBulkDeleteButtonVisibility();
    }

    filterCategories(searchTerm) {
        if (!searchTerm) {
            this.filteredCategories = [...this.categories];
        } else {
            this.filteredCategories = this.categories.filter(category =>
                category.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
                category.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (category.description && category.description.toLowerCase().includes(searchTerm.toLowerCase()))
            );
        }
    }

    goToPreviousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.renderPaginatedCategories();
        }
    }

    goToNextPage() {
        const totalPages = Math.ceil(this.filteredCategories.length / this.itemsPerPage);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.renderPaginatedCategories();
        }
    }

    goToPage(pageNumber) {
        const totalPages = Math.ceil(this.filteredCategories.length / this.itemsPerPage);
        if (pageNumber >= 1 && pageNumber <= totalPages) {
            this.currentPage = pageNumber;
            this.renderPaginatedCategories();
        }
    }

    renderPagination() {
        const totalItems = this.filteredCategories.length;
        const totalPages = Math.ceil(totalItems / this.itemsPerPage);
        const startItem = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endItem = Math.min(this.currentPage * this.itemsPerPage, totalItems);

        // Update results info text
        if (this.resultsInfoElement) {
            this.resultsInfoElement.innerHTML = `نمایش <b class="me-1">${totalItems > 0 ? startItem : 0}-${endItem}</b>از<b class="ms-1">${totalItems}</b> نتیجه`;
        }

        // Create pagination controls
        if (this.paginationContainer) {
            // Create pagination HTML
            const paginationHTML = this.createPaginationHTML(totalPages);
            this.paginationContainer.innerHTML = paginationHTML;

            createIcons({ icons });
        }
    }

    createPaginationHTML(totalPages) {
        let html = '';

        // Previous button
        html += `<li class="page-item${this.currentPage === 1 ? ' disabled' : ''}">
            <a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>
        </li>`;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            html += `<li class="page-item${i === this.currentPage ? ' active' : ''}">
                <a class="page-link" href="#!">${i}</a>
            </li>`;
        }

        // Next button
        html += `<li class="page-item${this.currentPage === totalPages || totalPages === 0 ? ' disabled' : ''}">
            <a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>
        </li>`;

        return html;
    }

    renderPaginatedCategories() {
        if (!this.tableBody) return;

        // Clear table body
        this.tableBody.innerHTML = '';

        // Note: we're NOT clearing selected items here anymore
        // this.selectedItems.clear(); <- Remove this line

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredCategories.length);
        const paginatedCategories = this.filteredCategories.slice(startIndex, endIndex);

        if (paginatedCategories.length === 0) {
            // Display no results message
            const noResultsRow = document.createElement('tr');
            noResultsRow.innerHTML = `
                 <td colspan="6" class="text-center py-4">
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
                                                <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164	S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331	c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                                                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0	l-4.331-4.331"></path>
                                                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                                                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                                            </svg>
                                            <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                        <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                    </div>
                </td>
            `;
            this.tableBody.appendChild(noResultsRow);
        } else {
            // Create document fragment for better performance
            const fragment = document.createDocumentFragment();

            // Add each category to the fragment
            paginatedCategories.forEach(category => {
                const row = this.createCategoryRow(category);

                // Make sure checkbox reflects selection state
                const checkbox = row.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.checked = this.selectedItems.has(category.id);
                }

                fragment.appendChild(row);
            });

            // Append all rows at once
            this.tableBody.appendChild(fragment);
        }

        // Update "Check All" checkbox state
        this.updateCheckAllState();

        // Update pagination
        this.renderPagination();

        // Update bulk delete button visibility
        this.updateBulkDeleteButtonVisibility();
    }


    handleImageUpload(event) {
        const file = event.target.files[0];
        if (file && this.imagePreview && this.uploadText) {
            const reader = new FileReader();
            reader.onload = (e) => {
                this.imagePreview.src = e.target.result;
                this.imagePreview.style.display = 'block';
                this.uploadText.classList.add('d-none');
            };
            reader.readAsDataURL(file);
        }
    }

    resetForm() {
        // Reset form fields
        if (this.categoryForm) {
            this.categoryForm.reset();
        }

        if (this.imagePreview) {
            this.imagePreview.style.display = 'none';
        }

        if (this.uploadText) {
            this.uploadText.classList.remove('d-none');
        }

        this.editMode = false;
        this.currentEditId = null;

        if (this.addButton) {
            this.addButton.textContent = 'افزودن دسته‌بندی';
        }
    }

    handleFormSubmit(event) {
        event.preventDefault();

        // Check if necessary form elements exist
        if (!this.categoryNameInput) {
            console.error('Category name input element not found');
            return;
        }

        // Get form values
        const categoryName = this.categoryNameInput.value;
        const description = this.descriptionInput ? this.descriptionInput.value : '';
        const status = this.getSelectedStatus();
        const imageUrl = (this.imagePreview && this.imagePreview.style.display !== 'none')
            ? this.imagePreview.src
            : 'assets/images/products/img-01.png';
        const showAlert = (message) => {
            const alertContainer = document.getElementById('alertContainer');
            if (!alertContainer) return;

            alertContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert" id="formAlert">
                        <span>${message}</span>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
        };
        const categoryInput = document.querySelector('input[placeholder="نام دسته‌بندی"]');

        categoryInput.addEventListener('input', () => {
            const existingAlert = document.getElementById('formAlert');
            if (existingAlert) {
                existingAlert.remove();
            }
        });

        if (!categoryName) {
            showAlert('لطفا نام دسته‌بندی را وارد نمایید');
            return;
        }

        if (this.editMode && this.currentEditId) {
            // Update existing category
            const existingCategory = this.getCategoryById(this.currentEditId);
            if (existingCategory) {
                this.updateCategory({
                    ...existingCategory, // Keep all existing properties
                    category: categoryName,
                    description: description,
                    status: status,
                    image: imageUrl
                });
            }
        } else {
            // Add new category
            this.addCategory({
                id: `PEC-${++this.lastId}`,
                category: categoryName,
                description: description,
                status: status,
                image: imageUrl,
                quantity: 0
            });
        }

        // Reset the form
        this.resetForm();
    }

    getSelectedStatus() {
        // Get the value from the status dropdown
        return this.statusSelect.options[this.statusSelect.selectedIndex].textContent;
    }

    initStatusSelect() {
        // Initialize status dropdown
        const statusOptions = ['فعال', 'غیرفعال', 'پیش‌نویس'];
        const selectContainer = document.createElement('select');
        selectContainer.className = 'form-select';

        statusOptions.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.toLowerCase();
            optionElement.textContent = option;
            selectContainer.appendChild(optionElement);
        });

        // Replace the placeholder with the actual select
        this.statusSelect.parentNode.replaceChild(selectContainer, this.statusSelect);
        this.statusSelect = selectContainer;
    }

    createCategoryRow(category) {
        const row = document.createElement('tr');
        row.dataset.categoryId = category.id;

        // Determine status styling
        const statusClass = category.status.toLowerCase() === 'فعال' ? 'success' :
            category.status.toLowerCase() === 'پیش‌نویس' ? 'warning' : 'danger';

        row.innerHTML = `
            <td>
                <div class="form-check check-primary">
                    <input class="form-check-input" type="checkbox" aria-label="Check Data Checkbox" id="check${category.id}">
                    <label class="form-check-label d-none" for="check${category.id}">
                        ${category.category}
                    </label>
                </div>
            </td>
            <td><a href="#!" class="link link-custom-primary">${category.id}</a></td>
            <td>
                <div class="d-flex align-items-center gap-2">
                    <div class="avatar size-9 border rounded p-1">
                        <img src="${category.image}" loading="lazy" alt="${category.category}" class="img-fluid rounded-pill">
                    </div>
                    <h6 class="mb-0"><a href="#" class="text-reset">${category.category}</a></h6>
                </div>
            </td>
            <td>${category.quantity}</td>
            <td><span class="badge bg-${statusClass}-subtle text-${statusClass} border border-${statusClass}-subtle">${category.status}</span></td>
            <td>
                <div class="dropdown">
                    <a href="#!" class="link link-custom-primary" type="button" data-bs-toggle="dropdown" aria-expanded="true" title="dropdown-button">
                        <i class="ri-more-2-fill"></i>
                    </a>
                    <ul class="dropdown-menu">
                        <li>
                            <a href="#!" class="dropdown-item d-flex gap-3 align-items-center">
                                <i class="ri-eye-line"></i>
                                <span>نمای کلی</span>
                            </a>
                        </li>
                        <li>
                            <a href="#!" class="dropdown-item d-flex gap-3 align-items-center edit-category">
                                <i class="ri-pencil-line"></i>
                                ویرایش
                            </a>
                        </li>
                        <li>
                            <a href="#deleteModal" data-bs-toggle="modal" class="dropdown-item d-flex gap-3 align-items-center delete-category">
                                <i class="ri-delete-bin-line"></i>
                                <span>حذف</span>
                            </a>
                        </li>
                    </ul>
                </div>
            </td>
        `;

        return row;
    }

    addCategory(category) {
        this.categories.unshift(category); // Add to the beginning for better visibility

        // Re-apply current filter
        this.filterCategories(this.searchTerm);

        // Reset to first page to show the new category
        this.currentPage = 1;
        this.renderPaginatedCategories();

        // You might want to save the updated data back to the server here
    }

    getCategoryById(id) {
        return this.categories.find(category => category.id === id);
    }

    editCategory(categoryId) {
        const category = this.getCategoryById(categoryId);
        if (!category) return;

        // Set form values
        if (this.categoryNameInput) {
            this.categoryNameInput.value = category.category;
        }

        if (this.descriptionInput) {
            this.descriptionInput.value = category.description || '';
        }
        // Set status
        if (category.status) {
            for (let i = 0; i < this.statusSelect.options.length; i++) {
                if (this.statusSelect.options[i].textContent === category.status) {
                    this.statusSelect.selectedIndex = i;
                    break;
                }
            }
        }

        // Set image if available
        if (category.image && this.imagePreview && this.uploadText) {
            this.imagePreview.src = category.image;
            this.imagePreview.style.display = 'block';
            this.uploadText.classList.add('d-none');
        }

        // Set edit mode
        this.editMode = true;
        this.currentEditId = categoryId;

        if (this.addButton) {
            this.addButton.textContent = 'آپدیت دسته‌بندی';
        }

        // Scroll to form
        if (this.categoryForm) {
            this.categoryForm.scrollIntoView({ behavior: 'smooth' });
        }
    }

    updateCategory(updatedCategory) {
        const index = this.categories.findIndex(category => category.id === updatedCategory.id);
        if (index !== -1) {
            this.categories[index] = updatedCategory;

            // Re-apply current filter
            this.filterCategories(this.searchTerm);
            this.renderPaginatedCategories();

            // You might want to save the updated data back to the server here
        }
    }

    openDeleteModal(categoryId) {
        this.currentEditId = categoryId;
    }

    confirmDelete() {
        if (this.currentEditId) {
            this.deleteCategory(this.currentEditId);
            this.currentEditId = null;

            // Close modal programmatically
            if (typeof bootstrap !== 'undefined' && this.deleteModal) {
                const modalInstance = window.bootstrap.Modal.getInstance(this.deleteModal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        }
    }

    deleteCategory(categoryId) {
        const index = this.categories.findIndex(category => category.id === categoryId);
        if (index !== -1) {
            this.categories.splice(index, 1);

            // Re-apply current filter
            this.filterCategories(this.searchTerm);

            // Check if current page is still valid
            const totalPages = Math.ceil(this.filteredCategories.length / this.itemsPerPage);
            if (this.currentPage > totalPages && totalPages > 0) {
                this.currentPage = totalPages;
            }

            this.renderPaginatedCategories();

            // You might want to save the updated data back to the server here
        }
    }

    // Sorting method - can be connected to table headers
    sortCategories(field, direction = 'asc') {
        const fieldMap = {
            'name': 'category',
            'products': 'quantity',
            'imageUrl': 'image'
        };

        // Map the field name if needed
        const sortField = fieldMap[field] || field;

        this.categories.sort((a, b) => {
            let valueA = a[sortField];
            let valueB = b[sortField];

            // Convert to lowercase for string comparison
            if (typeof valueA === 'string') valueA = valueA.toLowerCase();
            if (typeof valueB === 'string') valueB = valueB.toLowerCase();

            if (valueA < valueB) return direction === 'asc' ? -1 : 1;
            if (valueA > valueB) return direction === 'asc' ? 1 : -1;
            return 0;
        });

        // Re-apply current filter
        this.filterCategories(this.searchTerm);
        this.renderPaginatedCategories();
    }

    // Bulk actions
    bulkDelete() {
        if (confirm(`آیا مطمئن هستید که می‌خواهید دسته‌های انتخاب‌شده‌ی ${this.selectedItems.size} را حذف کنید؟`)) {
            // Convert Set to Array for iteration
            Array.from(this.selectedItems).forEach(id => {
                this.deleteCategory(id);
            });

            // Clear selected items
            this.selectedItems.clear();
            this.updateBulkDeleteButtonVisibility();
        }
    }

    bulkChangeStatus(newStatus) {
        // Convert Set to Array for iteration
        Array.from(this.selectedItems).forEach(id => {
            const category = this.getCategoryById(id);
            if (category) {
                this.updateCategory({
                    ...category,
                    status: newStatus
                });
            }
        });
    }
}

// Initialize the TableManager when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const tableManager = new TableManager();

    // Make it globally accessible if needed
    window.tableManager = tableManager;
});

export default TableManager;