import ApexCharts from '../../../libs/apexcharts/apexcharts.esm.js'
import { createIcons, icons } from 'lucide';


function getColor(color) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(color).trim();
    // If the value is in RGB format (e.g., "23, 162, 184"), wrap it in `rgb()`
    if (/^\d{1,3},\s*\d{1,3},\s*\d{1,3}$/.test(value)) {
        return `rgb(${value})`;
    }
    return value;
}
var allCharts = [];

const replaceCSSVariables = (obj) => {
    const updatedObj = JSON.parse(JSON.stringify(obj)); // Deep clone the object

    const traverseAndReplace = (node) => {
        for (const key in node) {
            if (typeof node[key] === 'string' && node[key].startsWith('--dx-')) {
                // Replace the CSS variable with its computed value
                node[key] = getColor(node[key]);
            } else if (typeof node[key] === 'object' && node[key] !== null) {
                // Recursively traverse nested objects/arrays
                traverseAndReplace(node[key]);
            }
        }
    };

    traverseAndReplace(updatedObj);
    return updatedObj;
};

function updateAllCharts(theme = "") {
    theme ? document.documentElement.setAttribute('data-colors', theme) : '';
    allCharts.forEach(chart => {
        const jsonData = JSON.parse(JSON.stringify(chart[0].data));
        const data = replaceCSSVariables(structuredClone(jsonData));
        if (chart[0].chart)
            chart[0].chart.destroy();

        var chart2 = new ApexCharts(document.querySelector("#" + chart[0].id), data);
        chart2.render();
        chart[0].chart = chart2;
    });
}

document.querySelectorAll('input[name="data-colors"]').forEach(radio => {
    radio.addEventListener('change', function () {
        renderCharts(this.value);
    });
});

document.querySelectorAll('input[name="data-bs-theme"]').forEach(radio => {
    radio.addEventListener('change', function () {
        renderCharts(this.value);
    });
});

document.getElementById('darkModeButton')?.addEventListener('click', function () {
    renderCharts(this.value);
})

function renderCharts(val) {
    setTimeout(() => {
        updateAllCharts(val);
    }, 0);
}

//Employee Chart
var options = {
    series: [{
        name: "کارمند",
        data: [21, 22, 19, 10, 10, 28, 16]
    }],
    chart: {
        height: 300,
        type: 'bar'
    },
    plotOptions: {
        bar: {
            columnWidth: '25%',
            distributed: true,
        }
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'dark',
            type: "horizontal",
            shadeIntensity: 0.2,
            // gradientToColors: undefined, // optional, if not defined - uses the shades of same color in series
            inverseColors: true,
            opacityFrom: 1,
            opacityTo: 1,
            stops: [0, 50, 30],
            colorStops: []
        }
    },
    states: {
        normal: {
            filter: {
                type: 'none',
                value: 0,
            }
        },
        hover: {
            filter: {
                type: 'none',
                value: 0,
            }
        },
        active: {
            filter: {
                type: 'none',
                value: 0,
            }
        },
    },
    dataLabels: {
        enabled: false
    },
    legend: {
        show: false
    },
    tooltip: {
    style: {
        fontFamily: 'Vazir'
        }
    },
    xaxis: {
        categories: [
            ['سایر'],
            ['پرستار'],
            ['اطفال'],
            ['قلب و عروق'],
            ['مغز و اعصاب'],
            ['ارتوپدی'],
            ['رادیولوژی'],
        ],
    },
    colors: ["--dx-primary", "--dx-pink", "--dx-info", "--dx-success", "--dx-warning", "--dx-orange", "--dx-purple"],
    grid: {
        padding: {
            top: -20,
            right: 0,
            bottom: 0
        },
    },
};

allCharts.push([{ 'id': 'employeeDepartmentChart', 'data': options }]);

updateAllCharts();

//Status Select
const statusMapFaToEn = {
    "فعال": "Active",
    "غیر فعال": "Unactive",
};

const statusMapEnToFa = {
    "Active": "فعال",
    "Unactive": "غیر فعال",
};


class TableManager {
    constructor(config) {
        this.tableId = config.tableId;
        this.tableElement = document.getElementById(this.tableId);
        this.data = config.data || [];
        this.columns = config.columns;
        this.itemsPerPage = config.itemsPerPage || 10;
        this.currentPage = 1;
        this.totalPages = Math.ceil(this.data.length / this.itemsPerPage);
        this.sorting = {
            column: null,
            direction: 'asc'
        };

        // Pagination elements
        this.paginationId = config.paginationId;
        this.paginationElement = document.getElementById(this.paginationId);

        // Form elements
        this.addFormId = config.addFormId;
        this.addFormElement = document.getElementById(this.addFormId);

        // Modal elements
        this.addModalId = config.addModalId;
        this.deleteModalId = config.deleteModalId;

        // Initialize
        this.init();
    }

    init() {
        this.renderTable();
        this.renderPagination();
        this.setupEventListeners();
        this.setupImagePreview();
        this.setupModalEvents();
    }

    setupImagePreview() {
        const imageInput = document.getElementById('imageInput');
        const logoPreview = document.getElementById('LogoPreview');
        const uploadIcon = imageInput?.parentElement?.querySelector('.ri-upload-line');

        if (imageInput && logoPreview) {
            imageInput.addEventListener('change', function () {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();

                    reader.onload = function (e) {
                        // Show image preview
                        logoPreview.src = e.target.result;

                        // Remove d-none class instead of just changing display style
                        logoPreview.classList.remove('d-none');

                        // Hide the upload icon when image is selected
                        if (uploadIcon) {
                            uploadIcon.style.display = 'none';
                        }

                        // Clear any previous error
                        const errorElement = document.getElementById('imageError');
                        if (errorElement) {
                            errorElement.textContent = '';
                        }
                    };

                    reader.readAsDataURL(this.files[0]);
                }
            });
        }
    }

    // New method to handle modal events
    setupModalEvents() {
        // Add modal event listener to reset form when the modal opens
        const addModal = document.getElementById(this.addModalId);
        if (addModal) {
            addModal.addEventListener('show.bs.modal', (event) => {
                // Check if the modal is being opened by an "Add New" button rather than an edit button
                const triggerButton = event.relatedTarget;
                if (!triggerButton || !triggerButton.classList.contains('edit-btn')) {
                    // This is an "Add New" operation, so reset the form
                    this.resetForm();
                }
            });
        }
    }

    // New method to reset the form completely
    resetForm() {
        if (this.addFormElement) {
            // Reset form fields
            this.addFormElement.reset();

            // Clear the edit ID
            this.addFormElement.removeAttribute('data-edit-id');

            // Reset image preview
            const logoPreview = document.getElementById('LogoPreview');
            if (logoPreview) {
                logoPreview.src = '';
                // Add d-none class instead of just changing display style
                logoPreview.classList.add('d-none');
            }

            // Show upload icon
            const imageInput = this.addFormElement.querySelector('#imageInput');
            const uploadIcon = imageInput?.parentElement?.querySelector('.ri-upload-line');
            if (uploadIcon) {
                uploadIcon.style.display = 'block';
            }

            // Update button text to "Add" instead of "Update"
            const submitButton = this.addFormElement.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.textContent = 'افزودن دپارتمان';
            }

            // Clear any error messages
            const errorElement = document.getElementById('imageError');
            if (errorElement) {
                errorElement.textContent = '';
            }
        }
    }

    renderTable() {
        if (!this.tableElement) return;

        // Clear existing table content
        const tbody = this.tableElement.querySelector('tbody');
        tbody.innerHTML = '';

        // Calculate start and end indices for current page
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.data.length);

        // Get sorted data
        const sortedData = this.getSortedData();

        // Create rows for current page
        for (let i = startIndex; i < endIndex; i++) {
            const item = sortedData[i];
            if (!item) continue;

            const row = document.createElement('tr');
            row.dataset.id = item.id;

            // Create cells based on column definitions
            this.columns.forEach(column => {
                const cell = document.createElement('td');

                if (column.render) {
                    // Custom renderer function
                    cell.innerHTML = column.render(item[column.key], item);
                } else {
                    // Default rendering
                    cell.textContent = item[column.key];
                }

                row.appendChild(cell);
            });

            // Add action column if specified
            if (this.columns.some(col => col.key === 'action')) {
                const actionCell = row.querySelector('td:last-child');
                actionCell.innerHTML = `
            <div class="d-flex align-items-center gap-2">
              <button class="btn btn-sub-primary size-8 btn-icon edit-btn" data-id="${item.id}" data-bs-toggle="modal" data-bs-target="#${this.addModalId}">
                <i class="ri-pencil-line"></i>
              </button>
              <button class="btn btn-sub-danger size-8 btn-icon delete-btn" data-id="${item.id}" data-bs-toggle="modal" data-bs-target="#${this.deleteModalId}">
                <i class="ri-delete-bin-line"></i>
              </button>
            </div>
          `;
            }

            tbody.appendChild(row);
        }

        // Add sort indicators to table headers
        const headers = this.tableElement.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            const column = this.columns[index];
            if (column && column.sortable) {
                header.classList.add('sortable');
                header.dataset.column = column.key;

                // Remove existing sort indicators
                header.classList.remove('sort-asc', 'sort-desc');

                // Add current sort indicator
                if (this.sorting.column === column.key) {
                    header.classList.add(this.sorting.direction === 'asc' ? 'sort-asc' : 'sort-desc');
                }
            }
        });
    }

    renderPagination() {
        if (!this.paginationElement) return;

        this.totalPages = Math.ceil(this.data.length / this.itemsPerPage);

        const paginationList = this.paginationElement.querySelector('ul');
        if (!paginationList) return;

        paginationList.innerHTML = '';

        // Previous button
        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevItem.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        paginationList.appendChild(prevItem);

        // Page numbers
        const maxPages = Math.min(5, this.totalPages);
        let startPage = Math.max(1, this.currentPage - 2);
        let endPage = Math.min(startPage + maxPages - 1, this.totalPages);

        if (endPage - startPage + 1 < maxPages) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#!" data-page="${i}">${i}</a>`;
            paginationList.appendChild(pageItem);
        }

        // Next button
        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        paginationList.appendChild(nextItem);

        // Results counter
        const resultCounter = this.paginationElement.querySelector('#paginationInfo');
        if (resultCounter) {
            const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
            const endIndex = Math.min(startIndex + this.itemsPerPage - 1, this.data.length);
            resultCounter.innerHTML = `نمایش <b class="me-1">${startIndex}-${endIndex}</b>از<b class="ms-1">${this.data.length}</b> نتیجه`;
        }

        createIcons({ icons });
    }

    setupEventListeners() {
        // Pagination click events
        if (this.paginationElement) {
            this.paginationElement.addEventListener('click', (e) => {
                e.preventDefault();

                const pageLink = e.target.closest('.page-link');
                if (!pageLink) return;

                if (pageLink.textContent.includes('قبلی') && this.currentPage > 1) {
                    this.currentPage--;
                } else if (pageLink.textContent.includes('بعدی') && this.currentPage < this.totalPages) {
                    this.currentPage++;
                } else if (pageLink.dataset.page) {
                    this.currentPage = parseInt(pageLink.dataset.page);
                }

                this.renderTable();
                this.renderPagination();
            });
        }

        // Sort click events
        if (this.tableElement) {
            const thead = this.tableElement.querySelector('thead');
            if (thead) {
                thead.addEventListener('click', (e) => {
                    const th = e.target.closest('th.sortable');
                    if (!th) return;

                    const column = th.dataset.column;

                    if (this.sorting.column === column) {
                        // Toggle direction
                        this.sorting.direction = this.sorting.direction === 'asc' ? 'desc' : 'asc';
                    } else {
                        // New column
                        this.sorting.column = column;
                        this.sorting.direction = 'asc';
                    }

                    this.renderTable();
                });
            }
        }

        // Delete confirmation event
        const deleteModal = document.getElementById(this.deleteModalId);
        if (deleteModal) {
            let itemIdToDelete = null;

            // Set item ID when delete button is clicked
            document.addEventListener('click', (e) => {
                const deleteBtn = e.target.closest('.delete-btn');
                if (deleteBtn) {
                    itemIdToDelete = deleteBtn.dataset.id;
                }
            });

            // Handle delete confirmation
            deleteModal.querySelector('.btn-danger').addEventListener('click', () => {
                if (itemIdToDelete) {
                    this.deleteItem(itemIdToDelete);
                    itemIdToDelete = null;
                }
            });
        }

        // Add/Edit form submit
        if (this.addFormElement) {
            this.addFormElement.addEventListener('submit', (e) => {
                e.preventDefault();

                const formData = new FormData(e.target);
                const itemData = {};
                const itemId = e.target.dataset.editId;

                // Get existing item data if we're editing
                let existingItem = null;
                if (itemId) {
                    existingItem = this.data.find(item => item.id === itemId);
                }

                // Process form data and handle image
                for (const [key, value] of formData.entries()) {
                    // Skip empty file inputs
                    if (key === 'image' && value.size === 0) {
                        continue;
                    }

                    // Store all other form values
                    if (key === "status") {
                        itemData[key] = statusMapEnToFa[value];
                    } else {
                        itemData[key] = value;
                    }
                }

                // Handle image upload
                const imageInput = e.target.querySelector('#imageInput');
                const logoPreview = document.getElementById('LogoPreview');

                if (imageInput && imageInput.files && imageInput.files[0]) {
                    // Create object URL for uploaded image
                    itemData.image = URL.createObjectURL(imageInput.files[0]);
                } else if (logoPreview && logoPreview.src && logoPreview.style.display !== 'none') {
                    // Keep existing image if available and visible
                    if (existingItem && existingItem.image && !imageInput.files.length) {
                        // If editing and no new file selected, preserve existing image
                        itemData.image = existingItem.image;
                    } else {
                        // Otherwise use the current preview
                        itemData.image = logoPreview.src;
                    }
                }

                // Handle doctor image/initials if needed
                const doctorInitialsInput = e.target.querySelector('#doctorInitials');
                if (doctorInitialsInput && doctorInitialsInput.value) {
                    itemData.doctorInitials = doctorInitialsInput.value;
                } else if (itemData.doctor) {
                    // If editing and we already have initials, keep them unless explicitly changed
                    if (existingItem && existingItem.doctorInitials && !doctorInitialsInput) {
                        itemData.doctorInitials = existingItem.doctorInitials;
                    } else {
                        // Generate initials from doctor name if no initials are provided
                        const nameParts = itemData.doctor.split(' ');
                        if (nameParts.length >= 2) {
                            itemData.doctorInitials = (nameParts[0][0] + nameParts[1][0]).toUpperCase();
                        } else {
                            itemData.doctorInitials = nameParts[0].substring(0, 2).toUpperCase();
                        }
                    }
                }

                // Remove the actual File object if present
                delete itemData.imageFile;

                if (itemId) {
                    this.updateItem(itemId, itemData);
                } else {
                    this.addItem(itemData);
                }

                // Reset form completely
                this.resetForm();

                // Close modal
                const modal = window.bootstrap.Modal.getInstance(document.getElementById(this.addModalId));
                if (modal) {
                    modal.hide();
                }
            });
        }

        // Edit button click
        document.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-btn');
            if (editBtn && this.addFormElement) {
                const itemId = editBtn.dataset.id;
                const item = this.data.find(d => d.id === itemId);

                if (item) {
                    // Clear the form first to prevent data persistence issues
                    this.addFormElement.reset();

                    // Set form data for each field
                    for (const key in item) {
                        const input = this.addFormElement.querySelector(`[name="${key}"]`);
                        if (input && input.type !== 'file') { // Skip file inputs
                            if (key === "status") {
                                input.value = statusMapFaToEn[item[key]];
                            } else {
                                input.value = item[key];
                            }
                        }
                    }

                    // Set image preview if exists
                    const logoPreview = document.getElementById('LogoPreview');
                    const uploadIcon = document.querySelector('.ri-upload-line');

                    if (logoPreview && item.image) {
                        logoPreview.src = item.image;
                        logoPreview.classList.remove('d-none');

                        // Hide upload icon
                        if (uploadIcon) {
                            uploadIcon.style.display = 'none';
                        }
                    } else {
                        // No image, reset preview
                        if (logoPreview) {
                            logoPreview.src = '';
                            logoPreview.classList.add('d-none');
                        }

                        // Show upload icon
                        if (uploadIcon) {
                            uploadIcon.style.display = 'block';
                        }
                    }

                    // Set editing state
                    this.addFormElement.dataset.editId = itemId;

                    // Update button text
                    const submitButton = this.addFormElement.querySelector('button[type="submit"]');
                    if (submitButton) {
                        submitButton.textContent = 'آپدیت دپارتمان';
                    }
                }
            }
        });

        // Add a listener for the "Add" button to ensure form is reset
        document.addEventListener('click', (e) => {
            const addBtn = e.target.closest('[data-bs-target="#' + this.addModalId + '"]');
            if (addBtn && !addBtn.classList.contains('edit-btn')) {
                // This is an "Add New" button click, ensure form is reset
                this.resetForm();
            }
        });
    }

    getSortedData() {
        if (!this.sorting.column) return [...this.data];

        return [...this.data].sort((a, b) => {
            const valueA = a[this.sorting.column];
            const valueB = b[this.sorting.column];

            // Handle different types
            if (typeof valueA === 'string' && typeof valueB === 'string') {
                return this.sorting.direction === 'asc'
                    ? valueA.localeCompare(valueB)
                    : valueB.localeCompare(valueA);
            } else {
                return this.sorting.direction === 'asc'
                    ? valueA - valueB
                    : valueB - valueA;
            }
        });
    }

    addItem(item) {
        // Generate ID if not provided
        if (!item.id) {
            const prefix = this.data.length > 0 ? this.data[0].id.split('-')[0] : 'PED';
            const maxNumber = Math.max(...this.data.map(d => {
                const parts = d.id.split('-');
                return parts.length > 1 ? parseInt(parts[1]) : 0;
            }), 0);

            item.id = `${prefix}-${maxNumber + 1}`;
        }

        this.data.unshift(item);
        this.renderTable();
        this.renderPagination();
    }

    updateItem(id, newData) {
        const index = this.data.findIndex(item => item.id === id);
        if (index !== -1) {
            // Get existing data
            const existingData = this.data[index];

            // Merge existing data with new data
            // This preserves any data not present in the form
            const updatedData = { ...existingData, ...newData };

            // Ensure ID is preserved
            updatedData.id = id;

            // Update the record
            this.data[index] = updatedData;
            this.renderTable();
        }
    }

    deleteItem(id) {
        this.data = this.data.filter(item => item.id !== id);

        // Adjust currentPage if necessary
        if (this.data.length <= (this.currentPage - 1) * this.itemsPerPage && this.currentPage > 1) {
            this.currentPage--;
        }

        this.renderTable();
        this.renderPagination();
    }

    // Export data as JSON
    exportJSON() {
        return JSON.stringify(this.data);
    }

    // Import data from JSON
    importJSON(jsonString) {
        try {
            this.data = JSON.parse(jsonString);
            this.currentPage = 1;
            this.renderTable();
            this.renderPagination();
            return true;
        } catch (e) {
            console.error('Invalid JSON data', e);
            return false;
        }
    }

    // Method to validate image before upload
    validateImage(file, maxSizeInMB = 2) {
        const errorElement = document.getElementById('imageError');
        if (!errorElement) return true;

        // Clear previous error
        errorElement.textContent = '';

        // Check if file exists
        if (!file) return true;

        // Check file size (convert MB to bytes)
        const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
        if (file.size > maxSizeInBytes) {
            errorElement.textContent = `حجم تصویر از حد مجاز ${maxSizeInMB}MB بیشتر است`;
            return false;
        }

        // Check file type
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            errorElement.textContent = 'نوع فایل نامعتبر است. لطفا از JPG، PNG، GIF یا WebP استفاده کنید.';
            return false;
        }

        return true;
    }
}

// Sample usage:
document.addEventListener('DOMContentLoaded', function () {
    // Sample data from parsed HTML table
    const departmentData = [
        {
            id: 'PED-1',
            departmentName: 'قلب و عروق',
            doctor: 'دکتر مارک تامپسون',
            doctorInitials: 'م.ت',
            totalEmployee: 8,
            headOfDept: 'دکتر سارا پاتل',
            status: "فعال"
        },
        {
            id: 'PED-2',
            departmentName: 'پوست‌شناسی',
            doctor: 'دکتر امیلی چن',
            image: 'assets/images/avatar/user-22.png',
            totalEmployee: 7,
            headOfDept: 'دکتر بنجامین دیویس',
            status: "فعال"
        },
        {
            id: 'PED-3',
            departmentName: 'کودکان',
            doctor: 'دکتر جنیفر رامیرز',
            doctorInitials: 'ج.ر',
            totalEmployee: 12,
            headOfDept: 'دکتر دانیال اسمیت',
            status: "فعال"
        },
        {
            id: 'PED-4',
            departmentName: 'عصب‌شناسی',
            doctor: 'دکتر ربکا ایوانز',
            doctorInitials: 'ر.ا',
            totalEmployee: 7,
            headOfDept: 'دکتر اندرو کلارک',
            status: "فعال"
        },
        {
            id: 'PED-5',
            departmentName: 'چشم پزشکی',
            doctor: 'دکتر سوفیا لی',
            image: 'assets/images/avatar/user-23.png',
            totalEmployee: 6,
            headOfDept: 'دکتر دیوید وونگ',
            status: "غیر فعال"
        }
    ];

    // Column definitions
    const columns = [
        { key: 'id', label: 'شناسه', sortable: true },
        { key: 'departmentName', label: 'نام دپارتمان', sortable: true },
        {
            key: 'doctor',
            label: 'Doctor',
            sortable: true,
            render: (value, item) => {
                if (item.image) {
                    return `
              <div class="d-flex align-items-center gap-3">
                <img src="${item.image}" loading="lazy" alt="" class="size-10 rounded-circle">
                <div>
                  <h6 class="mb-1"><a href="#!" class="text-body">${value}</a></h6>
                </div>
              </div>
            `;
                } else {
                    return `
              <div class="d-flex align-items-center gap-3">
                <span class="size-10 rounded-circle bg-light-subtle avatar text-muted fw-semibold fs-sm">${item.doctorInitials}</span>
                <div>
                  <h6 class="mb-1"><a href="#!" class="text-body">${value}</a></h6>
                </div>
              </div>
            `;
                }
            }
        },
        { key: 'totalEmployee', label: 'کل کارکنان', sortable: true },
        {
            key: 'headOfDept',
            label: 'رئیس دپارتمان',
            render: value => `<a href="#!" class="link link-custom-primary">${value}</a>`
        },
        {
            key: 'status',
            label: 'وضعیت',
            sortable: true,
            render: value => {
                const statusClass = value === 'فعال' ? 'success' : 'danger';
                return `<span class="badge bg-${statusClass}-subtle text-${statusClass} border border-${statusClass}-subtle">${value}</span>`;
            }
        },
        { key: 'action', label: 'عملیات' }
    ];

    // Initialize table manager
    const departmentTable = new TableManager({
        tableId: 'departmentTable',
        paginationId: 'paginationContainer',
        addFormId: 'addDepartmentForm',
        addModalId: 'addDepartmentModal',
        deleteModalId: 'deleteModal',
        data: departmentData,
        columns: columns,
        itemsPerPage: 5
    });
});