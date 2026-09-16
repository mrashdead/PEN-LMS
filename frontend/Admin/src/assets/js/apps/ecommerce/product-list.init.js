import { icons, createIcons } from "lucide";


// Initialize Virtual Select
VirtualSelect.init({
    ele: "#sampleSelect",
    options: [
        { label: "همه", value: "All" },
        { label: "ساعت", value: "Watch" },
        { label: "کفش", value: "Footwear" },
        { label: "مد", value: "Fashion" },
        { label: "کیف‌ها", value: "Bags" },
        { label: "اکسسوری‌ها", value: "Accessories" }
    ],
});

var slider = document.getElementById('slider');

noUiSlider.create(slider, {
    start: [20, 80],
    connect: true,
    range: {
        'min': 0,
        'max': 100
    }
});

/**
 * TableManager - A class to manage product table functionality
 * - Checkbox selection and "check all" functionality
 * - Delete functionality (single and bulk)
 * - Status toggle functionality
 * - Pagination
 * - Filtering
 */
const productsData = [
    {
        "id": "PEP-19115",
        "name": "تاپ لوله‌ای طرح رافل بلوز",
        "category": "مد",
        "inStock": true,
        "price": "15 تومان",
        "quantity": 154,
        "revenue": "15,236 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-01.png"
    },
    {
        "id": "PEP-19116",
        "name": "تی‌شرت نخی",
        "category": "مد",
        "inStock": true,
        "price": "25 تومان",
        "quantity": 89,
        "revenue": "12,350 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-02.png"
    },
    {
        "id": "PEP-19117",
        "name": "هدفون بی‌سیم",
        "category": "الکترونیکی",
        "inStock": true,
        "price": "100 تومان",
        "quantity": 45,
        "revenue": "8,750 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-03.png"
    },
    {
        "id": "PEP-19118",
        "name": "کیف پول چرمی",
        "category": "اکسسوری‌ها",
        "inStock": false,
        "price": "35 تومان",
        "quantity": 0,
        "revenue": "0",
        "status": "غیرفعال",
        "image": "assets/images/products/img-04.png"
    },
    {
        "id": "PEP-19119",
        "name": "ساعت هوشمند",
        "category": "الکترونیکی",
        "inStock": true,
        "price": "200 تومان",
        "quantity": 32,
        "revenue": "17,890 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-05.png"
    },
    {
        "id": "PEP-19120",
        "name": "کفش ورزشی",
        "category": "کفش",
        "inStock": true,
        "price": "80 تومان",
        "quantity": 67,
        "revenue": "9,875 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-06.png"
    },
    {
        "id": "PEP-19121",
        "name": "شلوار جین",
        "category": "مد",
        "inStock": true,
        "price": "45 تومان",
        "quantity": 120,
        "revenue": "13,450 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-07.png"
    },
    {
        "id": "PEP-19122",
        "name": "عینک آفتابی",
        "category": "اکسسوری‌ها",
        "inStock": false,
        "price": "30 تومان",
        "quantity": 0,
        "revenue": "0",
        "status": "غیرفعال",
        "image": "assets/images/products/img-08.png"
    },
    {
        "id": "PEP-19123",
        "name": "کوله‌پشتی",
        "category": "کیف‌ها",
        "inStock": true,
        "price": "60 تومان",
        "quantity": 43,
        "revenue": "7,890 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-09.png"
    },
    {
        "id": "PEP-19124",
        "name": "بطری آب",
        "category": "اکسسوری‌ها",
        "inStock": true,
        "price": "20 تومان",
        "quantity": 78,
        "revenue": "4,320 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-10.png"
    },
    {
        "id": "PEP-19125",
        "name": "ماوس گیمینگ",
        "category": "الکترونیکی",
        "inStock": true,
        "price": "50 تومان",
        "quantity": 55,
        "revenue": "6,500 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-11.png"
    },
    {
        "id": "PEP-19126",
        "name": "تشک یوگا",
        "category": "ورزشی",
        "inStock": true,
        "price": "30 تومان",
        "quantity": 40,
        "revenue": "3,200 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-12.png"
    },
    {
        "id": "PEP-19127",
        "name": "اسپیکر بلوتوثی",
        "category": "الکترونیکی",
        "inStock": true,
        "price": "90 تومان",
        "quantity": 33,
        "revenue": "4,200 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-13.png"
    },
    {
        "id": "PEP-19128",
        "name": "کمربند چرمی",
        "category": "اکسسوری‌ها",
        "inStock": false,
        "price": "25 تومان",
        "quantity": 0,
        "revenue": "0",
        "status": "غیرفعال",
        "image": "assets/images/products/img-14.png"
    },
    {
        "id": "PEP-19129",
        "name": "پیراهن رسمی",
        "category": "مد",
        "inStock": true,
        "price": "40 تومان",
        "quantity": 90,
        "revenue": "7,199 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-15.png"
    },
    {
        "id": "PEP-19130",
        "name": "کوله‌پشتی مسافرتی",
        "category": "کیف‌ها",
        "inStock": true,
        "price": "70 تومان",
        "quantity": 29,
        "revenue": "2,900 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-16.png"
    },
    {
        "id": "PEP-19131",
        "name": "ژاکت زمستانی",
        "category": "مد",
        "inStock": true,
        "price": "120 تومان",
        "quantity": 18,
        "revenue": "2,100 تومان",
        "status": "منتشر شده",
        "image": "assets/images/products/img-17.png"
    }
]
class TableManager {
    constructor(data) {
        // Store data
        this.data = data || [];

        // Table elements
        this.tableBody = document.querySelector('tbody');
        this.tableHeaders = document.querySelectorAll('th[data-sort]');
        this.checkAll = document.getElementById('checkboxDataAll');
        this.trashButton = document.querySelector('.trash-button');
        this.deleteModal = new window.bootstrap.Modal(document.getElementById('deleteModal'));
        this.deleteConfirmBtn = document.querySelector('#deleteModal .delete-btn');
        this.searchInput = document.getElementById('searchProductInput');
        this.paginationContainer = document.querySelector('.products-pagination');
        this.filterForm = document.querySelector('#filterForm');

        // State variables
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.filteredData = [...this.data];
        this.selectedRows = [];
        this.searchTerm = '';
        this.filters = {
            published: false,
            inactive: false
        };
        this.sortConfig = {
            key: null,
            direction: 'asc'
        };

        // Initialize the table
        this.renderTable();
        this.init();
    }

    /**
     * Initialize the table manager with all event listeners
     */
    init() {
        // Check all functionality
        this.initCheckAll();

        // Delete functionality
        this.initDeleteFunctionality();

        // Status toggle functionality
        this.initStatusToggle();

        // Search functionality
        this.initSearch();

        // Pagination functionality
        this.initPagination();

        // Filter functionality
        this.initFilters();

        // Sort functionality
        this.initSorting();
    }

    /**
     * Initialize sorting functionality
     */
    initSorting() {
        // Add click event to all sortable column headers
        this.tableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const key = header.getAttribute('data-sort');
                this.sortData(key);
            });
        });
    }

    /**
     * Sort data based on column key
     * @param {string} key - The column key to sort by
     */
    sortData(key) {
        // Update sort direction
        if (this.sortConfig.key === key) {
            // If already sorting by this key, toggle direction
            this.sortConfig.direction = this.sortConfig.direction === 'asc' ? 'desc' : 'asc';
        } else {
            // First time sorting by this key, default to ascending
            this.sortConfig.key = key;
            this.sortConfig.direction = 'asc';
        }

        // Update sort indicators in UI
        this.updateSortIndicators();

        // Apply the sort
        this.filteredData.sort((a, b) => {
            let valueA = a[key];
            let valueB = b[key];

            // Handle special cases for different data types
            if (key === 'price' || key === 'revenue') {
                // Remove currency symbol and convert to number
                valueA = parseFloat(valueA.replace(/[^0-9.-]+/g, ''));
                valueB = parseFloat(valueB.replace(/[^0-9.-]+/g, ''));
            } else if (typeof valueA === 'string') {
                valueA = valueA.toLowerCase();
                valueB = valueB.toLowerCase();
            }

            // Perform the comparison
            if (valueA < valueB) {
                return this.sortConfig.direction === 'asc' ? -1 : 1;
            }
            if (valueA > valueB) {
                return this.sortConfig.direction === 'asc' ? 1 : -1;
            }
            return 0;
        });

        // Reset to first page and re-render
        this.currentPage = 1;
        this.renderTable();
    }

    /**
     * Update sort indicators in table headers
     */
    updateSortIndicators() {
        // Remove all existing indicators
        this.tableHeaders.forEach(header => {
            // Remove any existing sort indicators
            header.classList.remove('sorted-asc', 'sorted-desc');

            // Remove existing sort icon if any
            const existingIcon = header.querySelector('.sort-icon');
            if (existingIcon) {
                existingIcon.remove();
            }
        });

        // Add indicator to current sort column
        if (this.sortConfig.key) {
            const currentHeader = document.querySelector(`th[data-sort="${this.sortConfig.key}"]`);
            if (currentHeader) {
                // Add class for styling
                currentHeader.classList.add(
                    this.sortConfig.direction === 'asc' ? 'sorted-asc' : 'sorted-desc'
                );

                // Add sort icon
                const iconSpan = document.createElement('span');
                iconSpan.className = 'sort-icon ms-1';
                iconSpan.innerHTML = this.sortConfig.direction === 'asc'
                    ? '<i class="ri-arrow-up-line ms-1"></i>'
                    : '<i class="ri-arrow-down-line ms-1"></i>';
                currentHeader.appendChild(iconSpan);
            }
        }
    }

    /**
     * Render the table with current data
     */
    renderTable() {
        // Clear table body
        this.tableBody.innerHTML = '';

        // Calculate visible items for current page
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const visibleData = this.filteredData.slice(startIndex, endIndex);

        if (visibleData.length === 0) {
            this.renderEmptyState();
        } else {
            // Render each row
            visibleData.forEach((item, index) => {
                const rowIndex = startIndex + index;
                this.tableBody.appendChild(this.createTableRow(item, rowIndex));
            });
        }

        // Update pagination
        this.renderPagination();
        this.updatePageInfo();

        // Update sort indicators
        this.updateSortIndicators();

        // Initialize event listeners on new table elements
        this.checkboxes = document.querySelectorAll('.form-check-input[id^="checkboxData"]');
        this.statusSwitches = document.querySelectorAll('.form-switch input[type="checkbox"]');
        this.tableRows = document.querySelectorAll('tbody tr');
    }

    /**
     * Create a table row for a given data item
     */
    createTableRow(item, index) {
        const row = document.createElement('tr');

        // Checkbox cell
        const checkboxCell = document.createElement('td');
        checkboxCell.innerHTML = `
            <div class="form-check check-primary">
                <input class="form-check-input" title="checkbox" type="checkbox" id="checkboxData${index + 1}">
                <label class="form-check-label d-none" for="checkboxData${index + 1}">
                    Data ${index + 1}
                </label>
            </div>
        `;
        row.appendChild(checkboxCell);

        // ID cell - with link styling
        const idCell = document.createElement('td');
        idCell.innerHTML = `<a href="#!" class="link link-custom-primary">${item.id}</a>`;
        row.appendChild(idCell);

        // Product cell with image and name - updated avatar sizing
        const productCell = document.createElement('td');
        productCell.innerHTML = `
            <div class="d-flex align-items-center gap-2">
                <div class="avatar size-9 border rounded-1 p-1">
                    <img src="${item.image}" loading="lazy" alt="" class="img-fluid">
                </div>
                <a href="apps-ecommerce-product-overview.html" class="text-reset fw-semibold">${item.name}</a>
            </div>
        `;
        row.appendChild(productCell);

        // Category cell
        const categoryCell = document.createElement('td');
        categoryCell.textContent = item.category;
        row.appendChild(categoryCell);

        // Status switch cell - updated switch style
        const switchCell = document.createElement('td');
        switchCell.innerHTML = `
            <div class="form-switch switch-light-secondary">
                <input type="checkbox" id="switchProduct${index + 1}" ${item.inStock ? 'checked' : ''} />
                <label class="label" for="switchProduct${index + 1}"></label>
            </div>
        `;
        row.appendChild(switchCell);

        // Price cell
        const priceCell = document.createElement('td');
        priceCell.textContent = item.price;
        row.appendChild(priceCell);

        // Quantity cell
        const quantityCell = document.createElement('td');
        quantityCell.textContent = item.quantity;
        row.appendChild(quantityCell);

        // Revenue cell
        const revenueCell = document.createElement('td');
        revenueCell.textContent = item.revenue;
        row.appendChild(revenueCell);

        // Status cell with badge
        const statusCell = document.createElement('td');
        const badgeClass = item.status === "منتشر شده"
            ? 'badge bg-success-subtle border border-success-subtle text-success'
            : 'badge bg-light-subtle border border-dark-subtle text-dark';
        statusCell.innerHTML = `<span class="${badgeClass}">${item.status}</span>`;
        row.appendChild(statusCell);

        // Action cell with improved dropdown
        const actionCell = document.createElement('td');
        actionCell.innerHTML = `
            <div class="dropdown">
                <a href="#!" class="link link-custom-primary" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="dropdown-button">
                    <i class="ri-more-2-fill"></i>
                </a>
                <ul class="dropdown-menu">
                    <li>
                        <a href="apps-ecommerce-product-overview.html" class="dropdown-item d-flex gap-3 align-items-center">
                            <i class="ri-eye-line"></i>
                            <span>نمای کلی</span>
                        </a>
                    </li>
                    <li>
                        <a href="apps-ecommerce-create-products.html" class="dropdown-item d-flex gap-3 align-items-center">
                            <i class="ri-pencil-line"></i>
                            ویرایش
                        </a>
                    </li>
                    <li>
                        <a href="#!" class="dropdown-item d-flex gap-3 align-items-center" data-bs-toggle="modal" data-bs-target="#deleteModal">
                            <i class="ri-delete-bin-line"></i>
                            <span>حذف</span>
                        </a>
                    </li>
                </ul>
            </div>
        `;
        row.appendChild(actionCell);

        // Store data-id for reference
        row.dataset.id = item.id;

        return row;
    }

    /**
     * Render empty state when no data is available
     */
    renderEmptyState() {
        const colSpan = 10; // Adjust based on your table columns
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `
            <td colspan="${colSpan}" class="text-center py-4">
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
                        <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164 S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331    c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                        <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0 l-4.331-4.331"></path>
                        <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                        <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                    </svg>
                    <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                    <p class="text-muted mb-0">ما نتوانستیم محصولی مطابق با جستجوی شما پیدا کنیم.</p>
                </div>
            </td>
        `;
        this.tableBody.appendChild(emptyRow);
    }

    /**
     * Initialize check all functionality
     */
    initCheckAll() {
        // Check all checkbox event
        this.checkAll.addEventListener('change', () => {
            if (this.checkboxes) {
                this.checkboxes.forEach(checkbox => {
                    checkbox.checked = this.checkAll.checked;
                });
                this.updateSelectedRows();
                this.updateTrashButtonVisibility();
            }
        });

        // Delegate event for individual checkboxes
        this.tableBody.addEventListener('change', (e) => {
            if (e.target && e.target.type === 'checkbox' && e.target.id.startsWith('checkboxData')) {
                this.updateCheckAllState();
                this.updateSelectedRows();
                this.updateTrashButtonVisibility();
            }
        });
    }

    /**
     * Update the "check all" checkbox state based on individual checkboxes
     */
    updateCheckAllState() {
        if (this.checkboxes && this.checkboxes.length > 0) {
            const allChecked = Array.from(this.checkboxes).every(checkbox => checkbox.checked);
            const someChecked = Array.from(this.checkboxes).some(checkbox => checkbox.checked);

            this.checkAll.checked = allChecked;
        } else {
            this.checkAll.checked = false;
        }
    }

    /**
     * Update the selected rows array based on checkbox states
     */
    updateSelectedRows() {
        this.selectedRows = Array.from(this.checkboxes || [])
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.closest('tr'));
    }

    /**
     * Show/hide the trash button based on selection
     */
    updateTrashButtonVisibility() {
        if (this.selectedRows.length > 0) {
            this.trashButton.classList.remove('d-none');
        } else {
            this.trashButton.classList.add('d-none');
        }
    }

    /**
     * Initialize delete functionality
     */
    initDeleteFunctionality() {
        // Bulk delete button
        this.trashButton.addEventListener('click', () => {
            // Show confirmation modal
            this.deleteModal.show();
        });

        // Delete confirmation
        this.deleteConfirmBtn.addEventListener('click', () => {
            this.deleteSelectedRows();
            this.deleteModal.hide();
        });

        // Delegate for individual delete buttons
        document.addEventListener('click', (e) => {
            if (e.target && e.target.closest('.remove-item-btn')) {
                // Store the row to be deleted
                this.selectedRows = [e.target.closest('tr')];
            }
        });
    }

    /**
     * Delete selected rows
     */
    deleteSelectedRows() {
        // Get IDs of selected rows
        const selectedIds = this.selectedRows.map(row => row.dataset.id);

        // Filter out the selected items from data
        this.data = this.data.filter(item => !selectedIds.includes(item.id));

        // Update filtered data
        this.applyFiltersAndSearch();

        // Reset selection
        this.selectedRows = [];
        this.checkAll.checked = false;
        this.updateTrashButtonVisibility();

        // Re-render the table
        this.renderTable();
    }

    /**
     * Initialize status toggle functionality
     */
    initStatusToggle() {
        // Delegate for status switches
        this.tableBody.addEventListener('change', (e) => {
            if (e.target && e.target.type === 'checkbox' && e.target.id.startsWith('switchProduct')) {
                const row = e.target.closest('tr');
                const itemId = row.dataset.id;
                const isChecked = e.target.checked;

                // Update data
                const dataItem = this.data.find(item => item.id === itemId);
                if (dataItem) {
                    dataItem.inStock = isChecked;
                    dataItem.status = isChecked ? "منتشر شده" : "غیرفعال";
                }

                // Update UI directly - adjusting selectors for new structure
                const statusCell = row.querySelector('td:nth-child(9)'); // Updated index for status cell
                const statusBadge = statusCell.querySelector('.badge');
                const revenueCell = row.querySelector('td:nth-child(8)'); // Updated index for revenue cell
                const quantityCell = row.querySelector('td:nth-child(7)'); // Updated index for quantity cell

                if (isChecked) {
                    statusBadge.className = 'badge bg-success-subtle border border-success-subtle text-success';
                    statusBadge.textContent = 'منتشر شده';
                } else {
                    statusBadge.className = 'badge bg-light-subtle border border-dark-subtle text-dark';
                    statusBadge.textContent = 'غیرفعال';
                }
            }
        });
    }

    /**
     * Generate a random revenue value for demonstration purposes
     */
    generateRandomRevenue() {
        return (Math.floor(Math.random() * 20000) + 1000).toLocaleString() + 'تومان';
    }

    /**
     * Initialize search functionality
     */
    initSearch() {
        this.searchInput.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.currentPage = 1; // Reset to first page
            this.applyFiltersAndSearch();
            this.renderTable();
        });
    }

    /**
     * Apply current filters and search term to data
     */
    applyFiltersAndSearch() {
        this.filteredData = this.data.filter(item => {
            // Apply search
            const matchesSearch = this.searchTerm === '' ||
                item.name.toLowerCase().includes(this.searchTerm) ||
                item.id.toLowerCase().includes(this.searchTerm) ||
                item.category.toLowerCase().includes(this.searchTerm);

            // Apply status filters
            let matchesFilter = true;
            if (this.filters.published || this.filters.inactive) {
                matchesFilter = (this.filters.published && item.status === "منتشر شده") ||
                    (this.filters.inactive && item.status === "غیرفعال");
            }

            return matchesSearch && matchesFilter;
        });
    }

    /**
     * Initialize pagination functionality
     */
    initPagination() {
        // Delegate click events for pagination
        this.paginationContainer.addEventListener('click', (e) => {
            e.preventDefault();

            if (e.target && e.target.classList.contains('page-link')) {
                const link = e.target;

                if (link.textContent.includes('قبلی')) {
                    if (this.currentPage > 1) {
                        this.currentPage--;
                    }
                } else if (link.textContent.includes('بعدی')) {
                    const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
                    if (this.currentPage < totalPages) {
                        this.currentPage++;
                    }
                } else {
                    // Number links
                    this.currentPage = parseInt(link.textContent);
                }

                this.renderTable();
            }
        });
    }

    /**
     * Render pagination links
     */
    renderPagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);

        // Clear pagination
        this.paginationContainer.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = '<a class="page-link" href="#"><i data-lucide="chevron-right" class="size-4"></i>قبلی</a>';
        this.paginationContainer.appendChild(prevLi);

        // Page links
        for (let i = 1; i <= totalPages; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            this.paginationContainer.appendChild(pageLi);
        }

        // If no pages, show page 1
        if (totalPages === 0) {
            const pageLi = document.createElement('li');
            pageLi.className = 'page-item active';
            pageLi.innerHTML = '<a class="page-link" href="#">1</a>';
            this.paginationContainer.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage >= totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = '<a class="page-link" href="#">بعدی<i data-lucide="chevron-left" class="size-4"></i></a>';
        this.paginationContainer.appendChild(nextLi);

        createIcons({ icons });
    }

    /**
     * Update the pagination info text
     */
    updatePageInfo() {
        const infoElement = document.querySelector('.col-md-6 p.text-muted');
        if (!infoElement) return;

        const totalItems = this.filteredData.length;
        const startItem = totalItems === 0 ? 0 : Math.min((this.currentPage - 1) * this.itemsPerPage + 1, totalItems);
        const endItem = Math.min(startItem + this.itemsPerPage - 1, totalItems);

        infoElement.innerHTML = `نمایش <b class="me-1">${startItem}-${endItem}</b> از <b class="ms-1">${totalItems}</b> نتیجه`;
    }

    /**
     * Initialize filters functionality
     */
    initFilters() {
        if (!this.filterForm) return;

        // Status filters checkboxes
        const publishedStatusCheckbox = document.getElementById('publishedStatus');
        const inactiveStatusCheckbox = document.getElementById('inactiveStatus');

        if (!publishedStatusCheckbox || !inactiveStatusCheckbox) return;

        // Reset button
        const resetButton = this.filterForm.querySelector('button[type="reset"]');

        // Apply filters button
        this.filterForm.addEventListener('submit', (e) => {
            e.preventDefault();

            this.filters.published = publishedStatusCheckbox.checked;
            this.filters.inactive = inactiveStatusCheckbox.checked;

            this.currentPage = 1; // Reset to first page
            this.applyFiltersAndSearch();
            this.renderTable();
        });

        // Reset filters
        if (resetButton) {
            resetButton.addEventListener('click', () => {
                publishedStatusCheckbox.checked = false;
                inactiveStatusCheckbox.checked = false;

                this.filters.published = false;
                this.filters.inactive = false;

                this.applyFiltersAndSearch();
                this.renderTable();
            });
        }
    }
}

// Initialize the table manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const tableManager = new TableManager(productsData);
});
