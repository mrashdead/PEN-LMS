import { createIcons, icons } from "lucide";

//Subscriber Select
VirtualSelect.init({
    ele: "#subscriberSelect",
    options: [
        { label: "بله", value: "1" },
        { label: "نه", value: "2" }
    ],
});

//status Select
VirtualSelect.init({
    ele: "#statusSelect",
    options: [
        { label: "فعال", value: "1" },
        { label: "غیرفعال", value: "2" },
    ],
});

/**
 * TableManager - A vanilla JS class to manage customer data table operations
 * - Handles CRUD operations (add, edit, delete)
 * - Pagination
 * - Search functionality
 * - Table row selection with global select all
 * - Image upload handling
 */
class TableManager {
    constructor(options = {}) {
        // Main elements
        this.tableEl = document.getElementById(options.tableId || 'usersTable');
        this.tableBody = this.tableEl.querySelector('tbody');
        this.tableHead = this.tableEl.querySelector('thead');
        this.searchInput = document.getElementById(options.searchInputId || 'searchCustomerInput');
        this.checkAllBox = document.getElementById(options.checkAllId || 'checkDataAll');

        // Pagination elements
        this.paginationContainer = document.querySelector('.pagination');
        this.resultsInfo = document.querySelector('#showingResults');

        // Modal references
        this.addModal = document.getElementById('addCustomerModals');
        this.overviewModal = document.getElementById('overviewCustomerModals');
        this.deleteModal = document.getElementById('deleteModal');

        // Data management
        this.customers = [];
        this.filteredCustomers = [];
        this.currentPage = 1;
        this.itemsPerPage = options.itemsPerPage || 10;
        this.selectedCustomerIds = new Set(); // Track selected customers across pages
        this.uploadedImageData = null; // Store uploaded image data
        this.isEditing = false; // Flag to track if we're in edit mode
        this.currentEditId = null; // Store the ID of the customer being edited

        // Sorting state
        this.currentSortColumn = 'id'; // Default sort column
        this.currentSortDirection = 'asc'; // Default sort direction

        // Initialize
        this.init();
    }

    init() {
        // Load initial data
        this.loadCustomers();

        // Set up event listeners
        this.setupEventListeners();

        // Initial render
        this.renderTable();
        this.renderPagination();

        // Set up sortable columns
        this.setupSortableColumns();
    }

    setupEventListeners() {
        // Search functionality
        this.searchInput.addEventListener('input', this.handleSearch.bind(this));

        // Select all checkbox
        this.checkAllBox.addEventListener('change', this.handleSelectAll.bind(this));

        // Delete button
        document.querySelector('.btn-danger.btn-icon').addEventListener('click', this.handleBulkDelete.bind(this));

        // Add customer form submission
        if (this.addModal) {
            const addForm = this.addModal.querySelector('form');
            const addBtn = addForm.querySelector('.btn-primary');

            // Use event delegation pattern to avoid conflicts
            addBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (this.isEditing) {
                    this.handleUpdateCustomer();
                } else {
                    this.handleAddCustomer();
                }
            });

            // Image upload handling
            const imageInput = this.addModal.querySelector('#imageInput');
            imageInput.addEventListener('change', this.handleImageUpload.bind(this));

            // Reset on modal close
            this.addModal.addEventListener('hidden.bs.modal', () => {
                const avatarLabel = this.addModal.querySelector('label.avatar');
                if (avatarLabel) {
                    avatarLabel.style.backgroundImage = '';
                    avatarLabel.style.backgroundSize = '';
                    avatarLabel.style.backgroundPosition = '';

                    const uploadIcon = avatarLabel.querySelector('svg');
                    if (uploadIcon) uploadIcon.style.display = '';
                }

                // Optionally reset the form or other state if needed
                this.isEditing = false;
                this.currentEditId = null;
            });

        }

        // Delete confirmation
        if (this.deleteModal) {
            const deleteBtn = this.deleteModal.querySelector('.btn-danger');
            deleteBtn.addEventListener('click', this.confirmDelete.bind(this));
        }

        // Pagination clicks
        this.paginationContainer.addEventListener('click', this.handlePaginationClick.bind(this));
    }
    resetAddEditModal() {
        // Reset form
        if (this.addModal) {
            const form = this.addModal.querySelector('form');
            if (form) form.reset();

            // Reset button text
            const submitBtn = this.addModal.querySelector('.btn-primary');
            submitBtn.textContent = 'افزودن مشتری';

            // Reset modal title
            const modalTitle = this.addModal.querySelector('.modal-title');
            if (modalTitle) modalTitle.textContent = 'افزودن مشتری';

            // Reset VirtualSelect elements
            if (window.VirtualSelect) {
                const subscriberSelect = document.querySelector('#subscriberSelect');
                const statusSelect = document.querySelector('#statusSelect');

                if (subscriberSelect && subscriberSelect.reset) {
                    subscriberSelect.reset();
                }

                if (statusSelect && statusSelect.reset) {
                    statusSelect.reset();
                }
            }

            // Reset image upload
            this.resetImageUpload();

            // Reset edit mode flags
            this.isEditing = false;
            this.currentEditId = null;

            // Clear any alerts
            const alertContainer = this.addModal.querySelector('#alertContainer');
            if (alertContainer) alertContainer.innerHTML = '';
        }
    }


    resetImageUpload() {
        if (!this.addModal) return;

        const avatarLabel = this.addModal.querySelector('label.avatar');
        if (avatarLabel) {
            avatarLabel.style.backgroundImage = '';
            avatarLabel.style.backgroundSize = '';
            avatarLabel.style.backgroundPosition = '';

            // Make sure the upload icon is visible again
            const uploadIcon = avatarLabel.querySelector('svg');
            if (uploadIcon) {
                uploadIcon.style.display = ''; // This resets to default display value
            }
        }

        this.uploadedImageData = null;
        const imageInput = this.addModal.querySelector('#imageInput');
        if (imageInput) imageInput.value = '';
    }

    // Set up sortable columns
    setupSortableColumns() {
        // Add sort icons and make headers clickable
        const headers = this.tableHead.querySelectorAll('th:not(:first-child):not(:last-child)');

        headers.forEach(header => {
            // Get the column name from the header text
            const columnName = this.getColumnNameFromHeader(header.textContent.trim());

            if (columnName) {
                // Make the header sortable
                header.classList.add('sortable');
                header.style.cursor = 'pointer';

                // Add sort icon container
                const headerContent = header.textContent;
                header.innerHTML = `
                    <div class="d-flex align-items-center justify-content-between">
                        <span>${headerContent}</span>
                        <span class="sort-icon ms-2">
                            <i class="ri-arrow-up-down-line text-muted"></i>
                        </span>
                    </div>
                `;

                // Add click event
                header.addEventListener('click', () => this.handleSort(columnName));
            }
        });
    }

    // Map header text to customer object property
    getColumnNameFromHeader(headerText) {
        const columnMap = {
            'ID': 'id',
            'Name': 'name',
            'Email': 'email',
            'Phone Number': 'phone',
            'Subscriber': 'subscriber',
            'Gender': 'gender',
            'Location': 'location',
            'Status': 'status'
        };

        return columnMap[headerText];
    }

    // Handle sorting when a column header is clicked
    handleSort(columnName) {
        // If clicking the same column, toggle sort direction
        if (this.currentSortColumn === columnName) {
            this.currentSortDirection = this.currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // New column, start with ascending
            this.currentSortColumn = columnName;
            this.currentSortDirection = 'asc';
        }

        // Sort the data
        this.sortData(columnName, this.currentSortDirection);

        // Update the UI to reflect the sort state
        this.updateSortIcons();

        // Reset to first page and update the table
        this.currentPage = 1;
        this.renderTable();
        this.renderPagination();
    }

    // Sort the filtered data based on column and direction
    sortData(columnName, direction) {
        this.filteredCustomers.sort((a, b) => {
            let valueA = a[columnName];
            let valueB = b[columnName];

            // Special case for name field - sort by actual name, not by HTML content
            if (columnName === 'name') {
                valueA = valueA || '';
                valueB = valueB || '';
            }

            // Case insensitive string comparison
            if (typeof valueA === 'string' && typeof valueB === 'string') {
                valueA = valueA.toLowerCase();
                valueB = valueB.toLowerCase();
            }

            // For numeric values that might be stored as strings with prefixes like "+"
            if (columnName === 'phone') {
                valueA = valueA.replace(/\D/g, '');
                valueB = valueB.replace(/\D/g, '');
            }

            // Basic comparison
            if (valueA < valueB) {
                return direction === 'asc' ? -1 : 1;
            }
            if (valueA > valueB) {
                return direction === 'asc' ? 1 : -1;
            }
            return 0;
        });
    }

    // Update the appearance of sort icons to reflect current sort state
    updateSortIcons() {
        const headers = this.tableHead.querySelectorAll('th.sortable');

        headers.forEach(header => {
            const columnName = this.getColumnNameFromHeader(header.textContent.trim());
            const iconContainer = header.querySelector('.sort-icon');

            if (columnName === this.currentSortColumn) {
                // Update icon for the active sort column
                iconContainer.innerHTML = this.currentSortDirection === 'asc'
                    ? '<i class="ri-arrow-up-line text-primary"></i>'
                    : '<i class="ri-arrow-down-line text-primary"></i>';
            } else {
                // Reset other columns
                iconContainer.innerHTML = '<i class="ri-arrow-up-down-line text-muted"></i>';
            }
        });
    }

    // Handle image upload
    handleImageUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        const showAlert = (message) => {
            const alertContainer = this.addModal.querySelector('#alertContainer');
            if (alertContainer) {
                alertContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <span>${message}</span>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
            }
        };

        // Check if file is an image
        if (!file.type.match('image.*')) {
            showAlert('لطفا یک فایل تصویری انتخاب کنید');
            return;
        }

        // Check file size (max 2MB)
        if (file.size > 2 * 1024 * 1024) {
            showAlert('حجم تصویر باید کمتر از ۲ مگابایت باشد');
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            // Store the image data
            this.uploadedImageData = event.target.result;

            // Update the avatar preview
            const avatarLabel = this.addModal.querySelector('label.avatar');
            if (avatarLabel) {
                avatarLabel.style.backgroundImage = `url(${this.uploadedImageData})`;
                avatarLabel.style.backgroundSize = 'cover';
                avatarLabel.style.backgroundPosition = 'center';

                // Hide the upload icon
                const uploadIcon = avatarLabel.querySelector('svg');
                if (uploadIcon) uploadIcon.style.display = 'none';
            }

            // Clear any previous alerts
            const alertContainer = this.addModal.querySelector('#alertContainer');
            if (alertContainer) alertContainer.innerHTML = '';
        };

        reader.readAsDataURL(file);
    }

    // Load customer data (in real app, this would fetch from API)
    loadCustomers() {
        // Sample data - in a real app, this would be an API call
        this.customers = [
            {
                id: 'PEC-24151',
                name: 'جان دو',
                email: 'john.doe@example.com',
                phone: '+1234567890',
                subscriber: 'بله',
                gender: 'مرد',
                location: 'نیویورک',
                status: 'فعال',
                avatar: 'assets/images/avatar/user-1.png'
            },
            {
                id: 'PEC-24152',
                name: 'جین اسمیت',
                email: 'jane.smith@example.com',
                phone: '+1987654321',
                subscriber: 'بله',
                gender: 'زن',
                location: 'لس آنجلس',
                status: 'غیرفعال',
                avatar: 'assets/images/avatar/user-2.png'
            }, 
            {
                id: "PEC-24161",
                name: "لیام پارکر",
                email: "liam.parker@example.com",
                phone: "+1234509876",
                subscriber: "خیر",
                gender: "مرد",
                location: "سیاتل",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-1.png"
            },
            {
                id: "PEC-24162",
                name: "آوا مگان",
                email: "ava.morgan@example.com",
                phone: "+1987632450",
                subscriber: "بله",
                gender: "زن",
                location: "دنور",
                status: "فعال",
                avatar: "assets/images/avatar/user-2.png"
            },
            {
                id: "PEC-24163",
                name: "نوح رید",
                email: "noah.reed@example.com",
                phone: "+1654789032",
                subscriber: "خیر",
                gender: "مرد",
                location: "آتلانتا",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-3.png"
            },
            {
                id: "PEC-24164",
                name: "ایزابللا ریورا",
                email: "isabella.rivera@example.com",
                phone: "+1789567340",
                subscriber: "بله",
                gender: "زن",
                location: "میامی",
                status: "فعال",
                avatar: "assets/images/avatar/user-4.png"
            },
            {
                id: "PEC-24165",
                name: "ماسون هیز",
                email: "mason.hayes@example.com",
                phone: "+1324098765",
                subscriber: "بله",
                gender: "مرد",
                location: "پورتلند",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-5.png"
            },
            {
                id: "PEC-24166",
                name: "سوفیا سیمونز",
                email: "sophia.simmons@example.com",
                phone: "+1897432650",
                subscriber: "خیر",
                gender: "زن",
                location: "اورلاندو",
                status: "فعال",
                avatar: "assets/images/avatar/user-6.png"
            },
            {
                id: "PEC-24167",
                name: "ایتن جیمز",
                email: "ethan.james@example.com",
                phone: "+1654327809",
                subscriber: "بله",
                gender: "مرد",
                location: "لاس وگاس",
                status: "فعال",
                avatar: "assets/images/avatar/user-7.png"
            },
            {
                id: "PEC-24168",
                name: "امیلیا بروکس",
                email: "amelia.brooks@example.com",
                phone: "+1789432765",
                subscriber: "خیر",
                gender: "زن",
                location: "شارلوت",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-8.png"
            },
            {
                id: "PEC-24169",
                name: "لوگان بنت",
                email: "logan.bennett@example.com",
                phone: "+1324765890",
                subscriber: "بله",
                gender: "مرد",
                location: "ایندیاناپولیس",
                status: "فعال",
                avatar: "assets/images/avatar/user-9.png"
            },
            {
                id: "PEC-24170",
                name: "میا واتسون",
                email: "mia.watson@example.com",
                phone: "+1897654912",
                subscriber: "بله",
                gender: "زن",
                location: "نشویل",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-10.png"
            },
            {
                id: "PEC-24171",
                name: "جیکوب فلورز",
                email: "jacob.flores@example.com",
                phone: "+1456789234",
                subscriber: "خیر",
                gender: "مرد",
                location: "آستین",
                status: "فعال",
                avatar: "assets/images/avatar/user-1.png"
            },
            {
                id: "PEC-24172",
                name: "الا کوپر",
                email: "ella.cooper@example.com",
                phone: "+1908763452",
                subscriber: "بله",
                gender: "زن",
                location: "توسن",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-2.png"
            },
            {
                id: "PEC-24173",
                name: "ویلیام وارد",
                email: "william.ward@example.com",
                phone: "+1346789052",
                subscriber: "بله",
                gender: "مرد",
                location: "کلولند",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-3.png"
            },
            {
                id: "PEC-24174",
                name: "چلسی بیلی",
                email: "chloe.bailey@example.com",
                phone: "+1765432987",
                subscriber: "خیر",
                gender: "زن",
                location: "مینیاپولیس",
                status: "فعال",
                avatar: "assets/images/avatar/user-4.png"
            },
            {
                id: "PEC-24175",
                name: "الکساندر هیوز",
                email: "alexander.hughes@example.com",
                phone: "+1223456789",
                subscriber: "بله",
                gender: "مرد",
                location: "کانزاس سیتی",
                status: "فعال",
                avatar: "assets/images/avatar/user-5.png"
            },
            {
                id: "PEC-24176",
                name: "گریس فاستر",
                email: "grace.foster@example.com",
                phone: "+1876543210",
                subscriber: "بله",
                gender: "زن",
                location: "کلمبوس",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-6.png"
            },
            {
                id: "PEC-24177",
                name: "جیمز هاوارد",
                email: "james.howard@example.com",
                phone: "+1678905432",
                subscriber: "خیر",
                gender: "مرد",
                location: "ال پاسو",
                status: "فعال",
                avatar: "assets/images/avatar/user-7.png"
            },
            {
                id: "PEC-24178",
                name: "لیلی رامیرز",
                email: "lily.ramirez@example.com",
                phone: "+1789456129",
                subscriber: "بله",
                gender: "زن",
                location: "فورت ورث",
                status: "غیرفعال",
                avatar: "assets/images/avatar/user-8.png"
            },
            {
                id: "PEC-24179",
                name: "دنیل براینت",
                email: "daniel.bryant@example.com",
                phone: "+1324098754",
                subscriber: "خیر",
                gender: "مرد",
                location: "دیترایت",
                status: "فعال",
                avatar: "assets/images/avatar/user-9.png"
            },
            {
                id: "PEC-24180",
                name: "آریا گریفیین",
                email: "aria.griffin@example.com",
                phone: "+1897632456",
                subscriber: "بله",
                gender: "زن",
                location: "ممفیس",
                status: "فعال",
                avatar: "assets/images/avatar/user-10.png"
            }
];

        this.filteredCustomers = [...this.customers];

        // Initial sort by ID ascending
        this.sortData('id', 'asc');
    }

    // Render table with current page data
    renderTable() {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const currentPageData = this.filteredCustomers.slice(startIndex, endIndex);

        // Clear table
        this.tableBody.innerHTML = '';

        // If no records found, show empty state row
        if (currentPageData.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
              <td colspan="10" class="text-center py-4">
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
                  <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                </div>
              </td>
            `;
            this.tableBody.appendChild(emptyRow);
            this.updateResultsInfo();
            this.updateSelectAllState();
            return;
        }

        // Add rows
        currentPageData.forEach((customer, index) => {
            const row = document.createElement('tr');
            row.dataset.id = customer.id;

            const statusClass = customer.status === 'فعال'
                ? 'bg-success-subtle text-success border border-success-subtle'
                : 'bg-danger-subtle text-danger border border-danger-subtle';

            const isChecked = this.selectedCustomerIds.has(customer.id) ? 'checked' : '';

            row.innerHTML = `
              <td>
                <div class="form-check check-primary">
                  <input class="form-check-input customer-check" type="checkbox" aria-label="Check Data Checkbox" id="checkData${startIndex + index + 1}" data-customer-id="${customer.id}" ${isChecked}>
                  <label class="form-check-label d-none" for="checkData${startIndex + index + 1}">Data ${startIndex + index + 1}</label>
                </div>
              </td>
              <td>${customer.id}</td>
              <td>
                <div class="d-flex gap-2 align-items-center">
                  <img src="${customer.avatar}" loading="lazy" alt="" class="size-8 rounded-circle">
                  <a href="#!" class="link link-custom-primary">${customer.name}</a>
                </div>
              </td>
              <td>${customer.email}</td>
              <td>${customer.phone}</td>
              <td>${customer.subscriber}</td>
              <td>${customer.gender}</td>
              <td>${customer.location}</td>
              <td><span class="badge ${statusClass}">${customer.status}</span></td>
              <td>
                <a href="#!" class="link link-custom-primary action-dropdown" type="button" id="actionDropdown${startIndex + index + 1}" data-bs-toggle="dropdown" aria-expanded="false" aria-label="dropdown-button">
                  <i class="ri-more-2-fill"></i>
                </a>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="actionDropdown${startIndex + index + 1}">
                  <li>
                    <a href="#overviewCustomerModals" data-bs-toggle="modal" class="dropdown-item d-flex gap-3 align-items-center overview-btn">
                      <i class="ri-eye-line"></i>
                      <span>نمای کلی</span>
                    </a>
                  </li>
                  <li>
                    <a href="#!" class="dropdown-item d-flex gap-3 align-items-center edit-btn">
                      <i class="ri-pencil-line"></i>
                      ویرایش
                    </a>
                  </li>
                  <li>
                    <a href="#deleteModal" class="dropdown-item d-flex gap-3 align-items-center delete-btn" data-bs-toggle="modal">
                      <i class="ri-delete-bin-line"></i>
                      <span>حذف</span>
                    </a>
                  </li>
                </ul>
              </td>
            `;
            this.tableBody.appendChild(row);
        });

        // Add event listeners to the new rows
        this.attachRowEventListeners();

        // Update results info and checkbox state
        this.updateResultsInfo();
        this.updateSelectAllState();
    }

    // Attach event listeners to table rows
    attachRowEventListeners() {
        // Overview buttons
        const overviewBtns = this.tableBody.querySelectorAll('.overview-btn');
        overviewBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const row = e.target.closest('tr');
                const customerId = row.dataset.id;
                this.showCustomerOverview(customerId);
            });
        });

        // Edit buttons
        const editBtns = this.tableBody.querySelectorAll('.edit-btn');
        editBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const row = e.target.closest('tr');
                const customerId = row.dataset.id;
                this.editCustomer(customerId);
            });
        });

        // Delete buttons
        const deleteBtns = this.tableBody.querySelectorAll('.delete-btn');
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const row = e.target.closest('tr');
                const customerId = row.dataset.id;
                this.currentDeleteId = customerId;
            });
        });

        // Checkboxes
        const checkboxes = this.tableBody.querySelectorAll('.customer-check');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const customerId = e.target.dataset.customerId;
                const deleteButton = document.querySelector('#deleteCustomer');

                if (e.target.checked) {
                    this.selectedCustomerIds.add(customerId);
                    // Remove d-none class when any checkbox is checked
                    deleteButton.classList.remove('d-none');
                } else {
                    this.selectedCustomerIds.delete(customerId);
                    // Add d-none class back if no checkboxes are selected
                    if (this.selectedCustomerIds.size === 0) {
                        deleteButton.classList.add('d-none');
                    }
                }

                this.updateDeleteButtonVisibility();
                this.updateSelectAllState();
            });
        });
    }

    // Render pagination controls
    renderPagination() {
        const totalPages = Math.ceil(this.filteredCustomers.length / this.itemsPerPage);
        let paginationHTML = '';

        // Previous button
        paginationHTML += `
        <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
          <a class="page-link" href="#!" data-page="prev">
            <i data-lucide="chevron-right" class="size-4"></i> قبلی
          </a>
        </li>
      `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (
                i === 1 ||
                i === totalPages ||
                (i >= this.currentPage - 1 && i <= this.currentPage + 1)
            ) {
                paginationHTML += `
            <li class="page-item ${i === this.currentPage ? 'active' : ''}">
              <a class="page-link" href="#!" data-page="${i}">${i}</a>
            </li>
          `;
            } else if (i === this.currentPage - 2 || i === this.currentPage + 2) {
                paginationHTML += `<li class="page-item disabled"><a class="page-link" href="#!">...</a></li>`;
            }
        }

        // Next button
        paginationHTML += `
        <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
          <a class="page-link" href="#!" data-page="next">
            بعدی <i data-lucide="chevron-left" class="size-4"></i>
          </a>
        </li>
      `;

        this.paginationContainer.innerHTML = paginationHTML;

        createIcons({ icons });
    }

    // Update the results info text
    updateResultsInfo() {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endIndex = Math.min(startIndex + this.itemsPerPage - 1, this.filteredCustomers.length);
        const totalItems = this.filteredCustomers.length;

        this.resultsInfo.innerHTML = `نمایش <b class="me-1">${startIndex}-${endIndex}</b>از<b class="ms-1">${totalItems}</b> نتیجه`;
    }

    // Handle pagination click events
    handlePaginationClick(e) {
        e.preventDefault();

        if (!e.target.matches('a.page-link') || e.target.parentElement.classList.contains('disabled')) {
            return;
        }

        const pageAction = e.target.dataset.page;
        const totalPages = Math.ceil(this.filteredCustomers.length / this.itemsPerPage);

        if (pageAction === 'prev') {
            this.currentPage = Math.max(1, this.currentPage - 1);
        } else if (pageAction === 'next') {
            this.currentPage = Math.min(totalPages, this.currentPage + 1);
        } else {
            this.currentPage = parseInt(pageAction, 10);
        }

        this.renderTable();
        this.renderPagination();
    }

    // Handle search input
    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();

        this.filteredCustomers = this.customers.filter(customer => {
            return (
                customer.name.toLowerCase().includes(searchTerm) ||
                customer.email.toLowerCase().includes(searchTerm) ||
                customer.gender.toLowerCase().includes(searchTerm) ||
                customer.location.toLowerCase().includes(searchTerm) ||
                customer.status.toLowerCase().includes(searchTerm) ||
                customer.id.toLowerCase().includes(searchTerm)
            );
        });

        this.currentPage = 1;  // Reset to first page on search
        this.renderTable();
        this.renderPagination();
    }

    updateDeleteButtonVisibility() {
        const deleteButton = document.querySelector('#deleteCustomer');

        if (this.selectedCustomerIds.size > 0) {
            // Show delete button when at least one checkbox is selected
            deleteButton.classList.remove('d-none');
        } else {
            // Hide delete button when no checkboxes are selected
            deleteButton.classList.add('d-none');
        }
    }

    // Handle select all checkbox - now selects ALL customers across ALL pages
    handleSelectAll(e) {
        const isChecked = e.target.checked;
        const deleteButton = document.querySelector('#deleteCustomer');

        if (isChecked) {
            // Add all customer IDs to selected set
            this.filteredCustomers.forEach(customer => {
                this.selectedCustomerIds.add(customer.id);
            });
            // Show delete button
            deleteButton.classList.remove('d-none');
        } else {
            // Clear all selections
            this.selectedCustomerIds.clear();
            // Hide delete button
            deleteButton.classList.add('d-none');
        }

        // Update visible checkboxes
        const checkboxes = this.tableBody.querySelectorAll('.customer-check');
        checkboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
        this.updateDeleteButtonVisibility();
    }

    // Update "select all" checkbox state based on individual selections
    updateSelectAllState() {
        const totalFilteredCustomers = this.filteredCustomers.length;
        const selectedFilteredCount = this.filteredCustomers.filter(
            customer => this.selectedCustomerIds.has(customer.id)
        ).length;

        // Update the select all checkbox state
        if (totalFilteredCustomers === 0) {
            this.checkAllBox.checked = false;
        } else if (selectedFilteredCount === 0) {
            this.checkAllBox.checked = false;
        } else if (selectedFilteredCount === totalFilteredCustomers) {
            this.checkAllBox.checked = true;
        } else {
            this.checkAllBox.checked = false;
        }
    }

    // Handle bulk delete
    handleBulkDelete() {
        const deleteButton = document.querySelector('#deleteCustomer');
        if (confirm(`آیا مطمئن هستید که می‌خواهید مشتری(های) ${this.selectedCustomerIds.size} را حذف کنید؟`)) {
            const idsToDelete = Array.from(this.selectedCustomerIds);

            this.customers = this.customers.filter(customer => !idsToDelete.includes(customer.id));
            this.filteredCustomers = this.filteredCustomers.filter(customer => !idsToDelete.includes(customer.id));

            // Clear selected IDs
            this.selectedCustomerIds.clear();

            deleteButton.classList.add('d-none');
            this.renderTable();
            this.renderPagination();
        }
    }

    // Delete a single customer
    confirmDelete() {
        if (this.currentDeleteId) {
            this.customers = this.customers.filter(customer => customer.id !== this.currentDeleteId);
            this.filteredCustomers = this.filteredCustomers.filter(customer => customer.id !== this.currentDeleteId);

            // Remove from selected IDs if present
            this.selectedCustomerIds.delete(this.currentDeleteId);

            // Hide modal programmatically
            const bsModal = window.bootstrap.Modal.getInstance(this.deleteModal);
            bsModal.hide();

            this.renderTable();
            this.renderPagination();

            // Clear the current delete ID
            this.currentDeleteId = null;
        }
    }

    // Show customer overview in modal
    showCustomerOverview(customerId) {
        const customer = this.customers.find(c => c.id === customerId);
        if (!customer) return;

        const modal = this.overviewModal;

        // Update modal content
        modal.querySelector('img.custom-image').src = customer.avatar;

        const tableRows = modal.querySelectorAll('table tbody tr');
        tableRows[0].querySelector('td').textContent = customer.name;
        tableRows[1].querySelector('td').textContent = customer.email;
        tableRows[2].querySelector('td').textContent = customer.phone;
        tableRows[3].querySelector('td').textContent = customer.subscriber;
        tableRows[4].querySelector('td').textContent = customer.location;

        // Set up edit button
        const editBtn = modal.querySelector('.btn-primary');

        // Remove old event listeners and add new one
        const newEditBtn = editBtn.cloneNode(true);
        editBtn.parentNode.replaceChild(newEditBtn, editBtn);

        newEditBtn.addEventListener('click', () => {
            // Hide current modal
            const bsModal = window.bootstrap.Modal.getInstance(modal);
            bsModal.hide();

            // Open edit form with this customer's data
            this.editCustomer(customerId);
        });
    }


    // Reset the image upload area
    resetImageUpload() {
        const avatarLabel = this.addModal.querySelector('label.avatar');
        avatarLabel.style.backgroundImage = '';
        avatarLabel.style.backgroundSize = '';
        avatarLabel.style.backgroundPosition = '';

        const uploadIcon = avatarLabel.querySelector('i');
        if (uploadIcon) {
            uploadIcon.style.display = '';
        }

        this.uploadedImageData = null;
        const imageInput = this.addModal.querySelector('#imageInput');
        imageInput.value = '';
    }

    // Edit a customer
    editCustomer(customerId) {
        const customer = this.customers.find(c => c.id === customerId);
        if (!customer) return;

        // Reset modal first
        this.resetAddEditModal();

        // Set edit mode
        this.isEditing = true;
        this.currentEditId = customerId;

        // Update modal title
        const modalTitle = this.addModal.querySelector('.modal-title');
        if (modalTitle) modalTitle.textContent = 'ویرایش مشتری';

        // Update button text
        const submitBtn = this.addModal.querySelector('.btn-primary');
        submitBtn.textContent = 'آپدیت مشتری';

        // Fill form with customer data
        const form = this.addModal.querySelector('form');
        form.querySelector('#orderIDInput').value = customer.name.split(' ')[0] || ''; // First name
        form.querySelector('#lastNameInput').value = customer.name.split(' ')[1] || ''; // Last name
        form.querySelector('#emailInput').value = customer.email || '';
        form.querySelector('#phoneNumberInput').value = customer.phone ? customer.phone.replace(/\D/g, '') : '';

        // Gender radio button
        if (customer.gender === 'مرد') {
            form.querySelector('#maleGender').checked = true;
        } else {
            form.querySelector('#femaleGender').checked = true;
        }

        // Location
        const locationInput = form.querySelector('input[placeholder="مکان"]');
        if (locationInput) locationInput.value = customer.location || '';

        // Set subscriber and status in Virtual Selects
        if (window.VirtualSelect) {
            const subscriberSelect = document.querySelector('#subscriberSelect');
            const statusSelect = document.querySelector('#statusSelect');

            // Set subscriber value (Yes = 1, No = 2)
            if (subscriberSelect && subscriberSelect.setValue) {
                subscriberSelect.setValue(customer.subscriber === 'بله' ? '1' : '2');
            }

            // Set status value (Active = 1, Inactive = 2)
            if (statusSelect && statusSelect.setValue) {
                statusSelect.setValue(customer.status === 'فعال' ? '1' : '2');
            }
        }
        // Set avatar image if exists
        if (customer.avatar) {
            const avatarLabel = this.addModal.querySelector('label.avatar');
            if (avatarLabel) {
                avatarLabel.style.backgroundImage = `url(${customer.avatar})`;
                avatarLabel.style.backgroundSize = 'cover';
                avatarLabel.style.backgroundPosition = 'center';

                const uploadIcon = avatarLabel.querySelector('svg');
                if (uploadIcon) uploadIcon.style.display = 'none';
            }
        }

        // Show modal
        const bsModal = new window.bootstrap.Modal(this.addModal);
        bsModal.show();
    }


    // Handle add customer submission
    handleAddCustomer() {
        if (this.isEditing) return; // Don't proceed if in edit mode

        const form = this.addModal.querySelector('form');

        // Validate form (simple validation)
        const firstName = form.querySelector('#orderIDInput').value.trim();
        const lastName = form.querySelector('#lastNameInput').value.trim();
        const email = form.querySelector('#emailInput').value.trim();
        const phone = form.querySelector('#phoneNumberInput').value.trim();
        const gender = form.querySelector('#maleGender').checked ? 'مرد' : 'زن';
        const location = form.querySelector('input[placeholder="مکان"]').value.trim();

        // Get values from VirtualSelect elements
        let subscriberValue = '1'; // Default to "Yes"
        let statusValue = '1'; // Default to "Active"

        if (window.VirtualSelect) {
            const subscriberSelect = document.querySelector('#subscriberSelect');
            const statusSelect = document.querySelector('#statusSelect');

            if (subscriberSelect) subscriberValue = subscriberSelect.value || '1';
            if (statusSelect) statusValue = statusSelect.value || '1';
        }

        const showAlert = (message) => {
            const alertContainer = this.addModal.querySelector('#alertContainer');
            if (alertContainer) {
                alertContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <span>${message}</span>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
            }
        };

        // Validation
        if (!firstName || !lastName || !email || !phone || !location) {
            showAlert('لطفا تمام فیلدهای ضروری را پر کنید');
            return;
        }

        // Use uploaded image or default avatar
        const avatarImage = this.uploadedImageData || 'assets/images/avatar/user-1.png';

        // Map subscriber and status values to text
        const subscriberText = subscriberValue === '1' ? 'بله' : 'خیر';
        const statusText = statusValue === '1' ? 'فعال' : 'غیرفعال';

        // Create new customer
        const newCustomer = {
            id: `PEC-${Math.floor(Math.random() * 10000) + 24000}`,
            name: `${firstName} ${lastName}`,
            email,
            phone: `+${phone}`,
            subscriber: subscriberText,
            gender,
            location,
            status: statusText,
            avatar: avatarImage
        };

        // Add to data array
        this.customers.unshift(newCustomer);
        this.filteredCustomers.unshift(newCustomer);

        // Hide modal
        const bsModal = window.bootstrap.Modal.getInstance(this.addModal);
        bsModal.hide();

        // Update table
        this.renderTable();
        this.renderPagination();
    }


    // Handle update customer
    handleUpdateCustomer() {
        if (!this.isEditing || !this.currentEditId) return;

        const customer = this.customers.find(c => c.id === this.currentEditId);
        if (!customer) return;

        const form = this.addModal.querySelector('form');

        // Get updated values
        const firstName = form.querySelector('#orderIDInput').value.trim();
        const lastName = form.querySelector('#lastNameInput').value.trim();
        const email = form.querySelector('#emailInput').value.trim();
        const phone = form.querySelector('#phoneNumberInput').value.trim();
        const gender = form.querySelector('#maleGender').checked ? 'مرد' : 'زن';
        const location = form.querySelector('input[placeholder="مکان"]').value.trim();

        // Get values from VirtualSelect elements
        let subscriberValue = ''; // Default to "Yes"
        let statusValue = ''; // Default to "Active"

        if (window.VirtualSelect) {
            const subscriberSelect = document.querySelector('#subscriberSelect');
            const statusSelect = document.querySelector('#statusSelect');

            if (subscriberSelect) subscriberValue = subscriberSelect.value || '1';
            if (statusSelect) statusValue = statusSelect.value || '1';
        }


        const showAlert = (message) => {
            const alertContainer = this.addModal.querySelector('#alertContainer');
            if (alertContainer) {
                alertContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <span>${message}</span>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
            }
        };

        // Validation
        if (!firstName || !lastName || !email || !phone || !location) {
            showAlert('لطفا تمام فیلدهای ضروری را پر کنید');
            return;
        }

        // Map subscriber and status values to text
        const subscriberText = subscriberValue === '1' ? 'بله' : 'نه';
        const statusText = statusValue === '1' ? 'فعال' : 'غیرفعال';

        // Update customer data
        customer.name = `${firstName} ${lastName}`;
        customer.email = email;
        customer.phone = `+${phone}`;
        customer.gender = gender;
        customer.location = location;
        customer.subscriber = subscriberText;
        customer.status = statusText;

        // Update avatar if a new one was uploaded
        if (this.uploadedImageData) {
            customer.avatar = this.uploadedImageData;
        }

        // Hide modal
        const bsModal = window.bootstrap.Modal.getInstance(this.addModal);
        bsModal.hide();

        // Update table
        this.renderTable();
    }

}

// Initialize the table manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the TableManager
    const tableManager = new TableManager({
        tableId: 'usersTable',
        searchInputId: 'searchCustomerInput',
        checkAllId: 'checkDataAll',
        itemsPerPage: 10
    });
});