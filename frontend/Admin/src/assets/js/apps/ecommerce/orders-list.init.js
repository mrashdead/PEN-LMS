import { createIcons, icons } from "lucide";


// Product Name Select
VirtualSelect.init({
    ele: "#productNameSelect",
    options: [
        { label: "ژاکت جین", value: "Denim Jacket" },
        { label: "کیف پول چرمی", value: "Leather Wallet" },
        { label: "هدفون بی‌سیم", value: "Wireless Headphones" },
        { label: "عینک آفتابی", value: "Sunglasses" },
        { label: "کوله‌پشتی", value: "Backpack" },
        { label: "کت زمستانی", value: "Winter Coat" },
        { label: "کیف دستی", value: "Handbag" },
        { label: "ژاکت", value: "Sweater" },
        { label: "ساعت ورزشی", value: "Sports Watch" },
    ],
    allowNewOption: true,
});


// Payment Status Select
VirtualSelect.init({
    ele: "#paymentStatusSelect",
    options: [
        { label: "پرداخت شده", value: "Paid" },
        { label: "پرداخت نشده", value: "Unpaid" },
        { label: "پرداخت در محل", value: "COD" }
    ],
    allowNewOption: true,
});

// Order Status Select
VirtualSelect.init({
    ele: "#orderStatusSelect",
    options: [
        { label: "جدید", value: "New" },
        { label: "در حال بررسی", value: "Pending" },
        { label: "در حال ارسال", value: "Shipping" },
        { label: "تحویل داده شده", value: "Delivered" }
    ],
    allowNewOption: true,
});

// Mappings
const orderStatusMapping = {
    'New': 'جدید',
    'Pending': 'در حال بررسی',
    'Shipping': 'در حال ارسال',
    'Delivered': 'تحویل داده شده'
};

const paymentStatusMapping = {
    'Paid': 'پرداخت شده',
    'Unpaid': 'پرداخت نشده',
    'COD': 'پرداخت در محل'
};

const productNameMapping = {
    'Denim Jacket': 'ژاکت جین',
    'Leather Wallet': 'کیف پول چرمی',
    'Wireless Headphones': 'هدفون بی‌سیم',
    'Sunglasses': 'عینک آفتابی',
    'Backpack': 'کوله‌پشتی',
    'Winter Coat': 'کت زمستانی',
    'Handbag': 'کیف دستی',
    'Sweater': 'ژاکت',
    'Sports Watch': 'ساعت ورزشی'
};

/**
 * TableManager - A class to handle table data and pagination functionality
 */
class TableManager {
    constructor(tableId, rowsPerPage = 10) {
        this.tableId = tableId;
        this.table = document.getElementById(tableId);
        this.tbody = this.table.querySelector('tbody');
        this.rowsPerPage = rowsPerPage;
        this.currentPage = 1;
        this.data = [];
        this.filteredData = [];
        this.totalPages = 0;
        this.paginationContainer = null;
        this.resultsInfoContainer = null;
        this.checkAllCheckbox = document.getElementById('checkDataAll');
        this.deleteSelectedButton = document.querySelector('#deleteOrder');

        // Initialize events
        this.initEvents();
    }

    /**
     * Initialize event listeners
     */
    initEvents() {
        // Add event listener for "check all" checkbox
        if (this.checkAllCheckbox) {
            this.checkAllCheckbox.addEventListener('change', () => {
                const isChecked = this.checkAllCheckbox.checked;
                const checkboxes = this.tbody.querySelectorAll('.form-check-input');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
                this.toggleDeleteSelectedButton();
            });
        }

        // Add event listener for delete selected button
        if (this.deleteSelectedButton) {
            this.deleteSelectedButton.addEventListener('click', () => {
                this.deleteSelectedOrders();
            });
        }

        // Add event listener for individual checkbox changes
        this.tbody.addEventListener('change', (e) => {
            if (e.target && e.target.classList.contains('form-check-input')) {
                this.toggleDeleteSelectedButton();
            }
        });
    }
    /**
    * Toggle visibility of delete selected button based on checkbox selection
    */
    toggleDeleteSelectedButton() {
        const checkboxes = this.tbody.querySelectorAll('.form-check-input');
        const hasChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);

        if (this.deleteSelectedButton) {
            if (hasChecked) {
                this.deleteSelectedButton.classList.remove('d-none');
            } else {
                this.deleteSelectedButton.classList.add('d-none');
            }
        }
    }

    /**
   * Delete selected orders
   */
    deleteSelectedOrders() {
        const checkboxes = this.tbody.querySelectorAll('.form-check-input:checked');
        const selectedOrderIds = [];

        // Get selected order IDs
        checkboxes.forEach(checkbox => {
            const row = checkbox.closest('tr');
            const orderIdElement = row.querySelector('.link-custom-primary');
            if (orderIdElement) {
                selectedOrderIds.push(orderIdElement.textContent);
            }
        });

        // Confirm deletion
        if (selectedOrderIds.length > 0) {
            const deleteConfirmModal = new window.window.bootstrap.Modal(document.getElementById('deleteModal'));

            // Update the confirmation message
            const confirmationMessage = document.querySelector('#deleteModal .modal-body p');
            if (confirmationMessage) {
                confirmationMessage.textContent = selectedOrderIds.length === 1
                    ? 'آیا از حذف این سفارش مطمئن هستید؟'
                    : `آیا مطمئن هستید که می‌خواهید این سفارش‌های ${selectedOrderIds.length} را حذف کنید؟`;
            }

            // Update the confirm button
            const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
            if (confirmDeleteBtn) {
                confirmDeleteBtn.dataset.orderIds = JSON.stringify(selectedOrderIds);

                // Remove any existing event listeners
                const newConfirmBtn = confirmDeleteBtn.cloneNode(true);
                confirmDeleteBtn.parentNode.replaceChild(newConfirmBtn, confirmDeleteBtn);

                // Add new event listener
                newConfirmBtn.addEventListener('click', () => {
                    const orderIds = JSON.parse(newConfirmBtn.dataset.orderIds);
                    this.deleteMultipleOrders(orderIds);
                    deleteConfirmModal.hide();
                });
            }

            deleteConfirmModal.show();
        }
    }

    /**
     * Delete multiple orders
     * @param {Array} orderIds - Array of order IDs to delete
     */
    deleteMultipleOrders(orderIds) {
        // Filter out the orders to delete
        this.data = this.data.filter(order => !orderIds.includes(order.orderId));
        this.filteredData = [...this.data];

        // Reset checkAll checkbox
        if (this.checkAllCheckbox) {
            this.checkAllCheckbox.checked = false;
        }

        // Hide delete selected button
        if (this.deleteSelectedButton) {
            this.deleteSelectedButton.classList.add('d-none');
        }

        // Update table
        this.totalPages = Math.ceil(this.filteredData.length / this.rowsPerPage);

        // Adjust current page if needed
        if (this.currentPage > this.totalPages && this.totalPages > 0) {
            this.currentPage = this.totalPages;
        }

        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();

        // Update stats if they exist
        if (typeof updateOrderStats === 'function') {
            updateOrderStats(this.data);
        }
    }

    /**
     * Set table data
     * @param {Array} data - Array of order objects
     */
    setData(data) {
        this.data = data;
        this.filteredData = [...data];
        this.totalPages = Math.ceil(this.filteredData.length / this.rowsPerPage);
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    /**
     * Set pagination container element
     * @param {string} elementId - ID of pagination container element
     */
    setPaginationContainer(elementId) {
        this.paginationContainer = document.getElementById(elementId);
        this.renderPagination();
    }

    /**
     * Set results info container element
     * @param {string} elementId - ID of results info container element
     */
    setResultsInfoContainer(elementId) {
        this.resultsInfoContainer = document.getElementById(elementId);
        this.updateResultsInfo();
    }

    /**
     * Render table with current page data
     */
    renderTable() {
        // Clear table body
        this.tbody.innerHTML = '';

        // If no data, show "Not found" message
        if (this.filteredData.length === 0) {
            const notFoundRow = document.createElement('tr');
            notFoundRow.className = 'NotFoundData';
            notFoundRow.innerHTML = `
           <td colspan="11" class="text-center py-4">
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
            this.tbody.appendChild(notFoundRow);
            return;
        }

        // Calculate start and end indices for current page
        const startIndex = (this.currentPage - 1) * this.rowsPerPage;
        const endIndex = Math.min(startIndex + this.rowsPerPage, this.filteredData.length);

        // Create rows for current page
        for (let i = startIndex; i < endIndex; i++) {
            const order = this.filteredData[i];
            const row = this.createTableRow(order, i + 1);
            this.tbody.appendChild(row);
        }
    }

    /**
     * Create a table row for an order
     * @param {Object} order - Order object
     * @param {number} index - Row index
     * @returns {HTMLTableRowElement} - Table row element
     */
    createTableRow(order, index) {
        const row = document.createElement('tr');

        // Get status badge class based on status
        const getStatusBadgeClass = (status) => {
            switch (status) {
                case 'Delivered':
                    return 'bg-success-subtle text-success border border-success-subtle';
                case 'Pending':
                    return 'bg-warning-subtle text-warning border border-warning-subtle';
                case 'New':
                    return 'bg-primary-subtle text-primary border border-primary-subtle';
                case 'Shipping':
                    return 'bg-secondary-subtle text-secondary border border-secondary-subtle';
                default:
                    return 'bg-body-tertiary text-body-tertiary border';
            }
        };

        // Get payment badge class based on payment status
        const getPaymentBadgeClass = (payment) => {
            switch (payment) {
                case 'Paid':
                    return 'bg-success-subtle text-success border border-success-subtle';
                case 'Unpaid':
                    return 'bg-danger-subtle text-danger border border-danger-subtle';
                default:
                    return 'bg-body-tertiary text-body-tertiary border';
            }
        };

        // Convert to Persian for display
        const persianPayment = paymentStatusMapping[order.payment] || order.payment;
        const persianStatus = orderStatusMapping[order.status] || order.status;
        const persianProduct = productNameMapping[order.product] || order.product;

        row.innerHTML = `
        <td>
          <div class="form-check check-primary">
            <input class="form-check-input" type="checkbox" aria-label="Check Data Checkbox" id="checkData${index}">
            <label class="form-check-label d-none" for="checkData${index}">
              Data ${index}
            </label>
          </div>
        </td>
        <td><a href="#!" class="link link-custom-primary">${order.orderId}</a></td>
        <td>${order.orderDate}</td>
        <td>${order.deliveredDate}</td>
        <td>${order.customer}</td>
        <td>${persianProduct}</td>
        <td><span class="badge ${getPaymentBadgeClass(order.payment)}">${persianPayment}</span></td>
        <td>${order.total}</td>
        <td>${order.qty}</td>
        <td><span class="badge ${getStatusBadgeClass(order.status)}">${persianStatus}</span></td>
        <td>
          <a href="#!" class="link link-custom-primary" type="button" id="actionDropdown${index}" data-bs-toggle="dropdown" aria-expanded="false" aria-label="dropdown-button">
            <i class="ri-more-2-fill"></i>
          </a>
          <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="actionDropdown${index}">
            <li>
              <a href="#overviewOrderModal" data-bs-toggle="modal" class="dropdown-item d-flex gap-3 align-items-center">
                <i class="ri-eye-line"></i>
                <span>نمای کلی</span>
              </a>
            </li>
            <li>
              <a href="#addOrderModal" data-bs-toggle="modal" class="dropdown-item d-flex gap-3 align-items-center edit-order-btn" data-order-id="${order.orderId}">
                <i class="ri-pencil-line"></i>
                ویرایش
              </a>
            </li>
            <li>
              <a href="#!" class="dropdown-item d-flex gap-3 align-items-center delete-order-btn" data-order-id="${order.orderId}">
                <i class="ri-delete-bin-line"></i>
                <span>حذف</span>
              </a>
            </li>
          </ul>
        </td>
      `;

        // Setup edit button
        const editBtn = row.querySelector('.edit-order-btn');
        editBtn.addEventListener('click', () => {
            this.populateEditForm(order);
        });

        // Setup delete button
        const deleteBtn = row.querySelector('.delete-order-btn');
        deleteBtn.addEventListener('click', (e) => {
            e.preventDefault();
            // Store orderId for deletion
            document.getElementById('confirmDeleteBtn').dataset.orderId = order.orderId;
            // Show delete modal
            const deleteModal = new window.window.bootstrap.Modal(document.getElementById('deleteModal'));
            deleteModal.show();
        });

        // Add event listener for checkbox
        const checkbox = row.querySelector('.form-check-input');
        checkbox.addEventListener('change', () => {
            this.toggleDeleteSelectedButton();
        });

        return row;
    }
    /**
    * Populate the edit form with order data
    * @param {Object} order - Order data to populate the form with
    */
    populateEditForm(order) {
        // Set form title and button text
        document.querySelector('#addOrderModal .modal-header h6').textContent = 'ویرایش سفارش';
        const updateBtn = document.querySelector('#addOrderModal .btn-primary');
        updateBtn.textContent = 'آپدیت سفارش';
        updateBtn.dataset.orderId = order.orderId;

        // Populate form fields with order data
        document.getElementById('orderIDInput').value = order.orderId;
        document.getElementById('orderIDInput').disabled = true; // Disable order ID input when editing

        // Populate date fields
        const dateInputs = document.querySelectorAll('#addOrderModal input[placeholder="dd MMM, yyyy"]');
        dateInputs[0].value = order.orderDate;
        dateInputs[1].value = order.deliveredDate;

        // Populate other fields
        document.querySelector('#addOrderModal input[placeholder="نام مشتری"]').value = order.customer;
        document.querySelector('#addOrderModal .input-spin').value = order.qty;
        document.querySelector('#addOrderModal input[placeholder="مبلغ کل"]').value = order.total;

        document.querySelector('#productNameSelect').setValue(order.product);
        document.querySelector('#paymentStatusSelect').setValue(order.payment);
        document.querySelector('#orderStatusSelect').setValue(order.status);
    }

    /**
     * Helper method to set dropdown value
     * @param {string} selector - Dropdown selector
     * @param {string} value - Value to set
     */
    setDropdownValue(selector, value) {
        const dropdown = document.querySelector(`${selector} .select-dropdown`);
        if (dropdown) {
            dropdown.textContent = value;

            // Update the hidden input value if it exists
            const hiddenInput = document.querySelector(`${selector} input[type="hidden"]`);
            if (hiddenInput) {
                hiddenInput.value = value;
            }

            // Also update the actual select element if it exists
            const selectElement = document.querySelector(selector);
            if (selectElement && selectElement.tagName === 'SELECT') {
                // Find and select the matching option
                Array.from(selectElement.options).forEach(option => {
                    if (option.textContent === value || option.value === value) {
                        option.selected = true;
                    }
                });
            }
        }
    }

    /**
     * Render pagination
     */
    renderPagination() {
        if (!this.paginationContainer) {
            return;
        }

        this.paginationContainer.innerHTML = '';

        // Create pagination UL element
        const paginationUl = document.createElement('ul');
        paginationUl.className = 'pagination justify-content-center justify-content-md-end mb-0';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.goToPage(this.currentPage - 1);
            }
        });
        paginationUl.appendChild(prevLi);

        // Page numbers
        const maxPagesToShow = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(this.totalPages, startPage + maxPagesToShow - 1);

        if (endPage - startPage + 1 < maxPagesToShow) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
            pageLi.addEventListener('click', (e) => {
                e.preventDefault();
                this.goToPage(i);
            });
            paginationUl.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < this.totalPages) {
                this.goToPage(this.currentPage + 1);
            }
        });
        paginationUl.appendChild(nextLi);

        // Append pagination UL to container
        this.paginationContainer.appendChild(paginationUl);
        createIcons({ icons });
    }

    /**
     * Update results info text
     */
    updateResultsInfo() {
        if (!this.resultsInfoContainer) {
            return;
        }

        const startIndex = (this.currentPage - 1) * this.rowsPerPage + 1;
        const endIndex = Math.min(startIndex + this.rowsPerPage - 1, this.filteredData.length);

        this.resultsInfoContainer.innerHTML = `نمایش <b class="me-1">${this.filteredData.length > 0 ? startIndex : 0}-${endIndex}</b>از<b class="ms-1">${this.filteredData.length}</b> نتیجه`;
    }

    /**
     * Add a new order
     * @param {Object} orderData - New order data
     */
    addOrder(orderData) {
        // Generate a new order ID if not provided
        if (!orderData.orderId) {
            orderData.orderId = `#PEO-${Math.floor(10000 + Math.random() * 90000)}`;
        }

        // Add order to data array
        this.data.unshift(orderData);
        this.filteredData = [...this.data];

        // Update table
        this.totalPages = Math.ceil(this.filteredData.length / this.rowsPerPage);
        this.currentPage = 1;
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();

        // Update stats if they exist
        if (typeof updateOrderStats === 'function') {
            updateOrderStats(this.data);
        }
    }

    /**
     * Edit an existing order
     * @param {string} orderId - ID of the order to edit
     * @param {Object} updatedData - Updated order data
     */
    editOrder(orderId, updatedData) {
        // Find the order index
        const orderIndex = this.data.findIndex(order => order.orderId === orderId);

        if (orderIndex !== -1) {
            // Update the order
            this.data[orderIndex] = {
                ...this.data[orderIndex],
                ...updatedData,
                orderId: orderId // Ensure order ID remains unchanged
            };

            // Update filtered data to reflect changes
            const filteredIndex = this.filteredData.findIndex(order => order.orderId === orderId);
            if (filteredIndex !== -1) {
                this.filteredData[filteredIndex] = { ...this.data[orderIndex] };
            } else {
                this.filteredData = [...this.data]; // Reset filtered data if item not found
            }

            // Update table
            this.renderTable();
            this.renderPagination();
            this.updateResultsInfo();

            // Update stats if they exist
            if (typeof updateOrderStats === 'function') {
                updateOrderStats(this.data);
            }
        }
    }

    /**
     * Delete an order
     * @param {string} orderId - ID of the order to delete
     */
    deleteOrder(orderId) {
        // Filter out the order to delete
        this.data = this.data.filter(order => order.orderId !== orderId);
        this.filteredData = [...this.data];

        // Update table
        this.totalPages = Math.ceil(this.filteredData.length / this.rowsPerPage);

        // Adjust current page if needed
        if (this.currentPage > this.totalPages && this.totalPages > 0) {
            this.currentPage = this.totalPages;
        }

        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();

        // Update stats if they exist
        if (typeof updateOrderStats === 'function') {
            updateOrderStats(this.data);
        }
    }

    /**
     * Go to a specific page
     * @param {number} pageNumber - Page number to go to
     */
    goToPage(pageNumber) {
        if (pageNumber < 1 || pageNumber > this.totalPages) {
            return;
        }

        this.currentPage = pageNumber;
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    /**
     * Search/filter table data
     * @param {string} searchTerm - Search term
     */
    search(searchTerm) {
        if (!searchTerm) {
            this.filteredData = [...this.data];
        } else {
            const term = searchTerm.toLowerCase();
            this.filteredData = this.data.filter(order =>
                order.orderId.toLowerCase().includes(term) ||
                order.customer.toLowerCase().includes(term) ||
                order.product.toLowerCase().includes(term) ||
                order.status.toLowerCase().includes(term)
            );
        }

        this.totalPages = Math.ceil(this.filteredData.length / this.rowsPerPage);
        this.currentPage = 1;
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    /**
     * Sort table data by column
     * @param {string} column - Column key to sort by
     * @param {boolean} ascending - Sort direction (true for ascending, false for descending)
     */
    sort(column, ascending = true) {
        this.filteredData.sort((a, b) => {
            let valueA = a[column];
            let valueB = b[column];

            // Handle numeric values
            if (!isNaN(valueA) && !isNaN(valueB)) {
                valueA = Number(valueA);
                valueB = Number(valueB);
            } else {
                valueA = String(valueA).toLowerCase();
                valueB = String(valueB).toLowerCase();
            }

            if (valueA < valueB) {
                return ascending ? -1 : 1;
            }
            if (valueA > valueB) {
                return ascending ? 1 : -1;
            }
            return 0;
        });

        this.renderTable();
    }
}

// Sample data (extracted from the provided HTML)
const orderData = [
    {
        orderId: "PEO-14521",
        orderDate: "24 اسفند 1400",
        deliveredDate: "1 فروردین 1401",
        customer: "لاوان پاتل",
        product: "کت جین",
        payment: "Paid",
        total: 45.99,
        qty: 1,
        status: "Delivered"
    },
    {
        orderId: "PEO-14522",
        orderDate: "13 فروردین 1401",
        deliveredDate: "20 فروردین 1401",
        customer: "لوکاس نگوین",
        product: "کیف چرمی",
        payment: "COD",
        total: 35.5,
        qty: 1,
        status: "Pending"
    },
    {
        orderId: "PEO-14523",
        orderDate: "28 خرداد 1401",
        deliveredDate: "5 تیر 1401",
        customer: "ایزابلا توماس",
        product: "پیراهن تابستانی",
        payment: "Unpaid",
        total: 28.75,
        qty: 2,
        status: "New"
    },
    {
        orderId: "PEO-14524",
        orderDate: "8 مرداد 1401",
        deliveredDate: "16 مرداد 1401",
        customer: "ماسون ویلسون",
        product: "هدفون بی‌سیم",
        payment: "Paid",
        total: 79.99,
        qty: 1,
        status: "Delivered"
    },
    {
        orderId: "PEO-14525",
        orderDate: "21 شهریور 1401",
        deliveredDate: "28 شهریور 1401",
        customer: "اولیویا براون",
        product: "عینک آفتابی",
        payment: "COD",
        total: 19.95,
        qty: 1,
        status: "Pending"
    },
    {
        orderId: "PEO-14526",
        orderDate: "2 آبان 1401",
        deliveredDate: "9 آبان 1401",
        customer: "ویلیام گارسیا",
        product: "ساعت ورزشی",
        payment: "Paid",
        total: 55,
        qty: 1,
        status: "Delivered"
    },
    {
        orderId: "PEO-14527",
        orderDate: "14 آبان 1401",
        deliveredDate: "21 آبان 1401",
        customer: "آوا مارتینز",
        product: "کوله پشتی",
        payment: "COD",
        total: 42.75,
        qty: 1,
        status: "Pending"
    },
    {
        orderId: "PEO-14528",
        orderDate: "23 آذر 1401",
        deliveredDate: "1 دی 1401",
        customer: "لیام پین",
        product: "کت زمستانی",
        payment: "Unpaid",
        total: 89.99,
        qty: 1,
        status: "New"
    },
    {
        orderId: "PEO-14529",
        orderDate: "11 دی 1401",
        deliveredDate: "19 دی 1401",
        customer: "شارلوت لوئیس",
        product: "شال",
        payment: "Paid",
        total: 12.5,
        qty: 2,
        status: "Pending"
    },
    {
        orderId: "PEO-14530",
        orderDate: "22 بهمن 1403",
        deliveredDate: "30 بهمن 1403",
        customer: "جیمز تیلور",
        product: "کاور تلفن همراه",
        payment: "COD",
        total: 15.99,
        qty: 1,
        status: "Shipping"
    },
    {
        orderId: "PEO-14531",
        orderDate: "30 اسفند 1403",
        deliveredDate: "7 فروردین 1404",
        customer: "اما هرناندز",
        product: "دستبند سلامت",
        payment: "Paid",
        total: 69,
        qty: 1,
        status: "Delivered"
    },
    {
        orderId: "PEO-14532",
        orderDate: "16 فروردین 1404",
        deliveredDate: "23 فروردین 1404",
        customer: "نوح یانگ",
        product: "کتانی",
        payment: "COD",
        total: 49.95,
        qty: 1,
        status: "Shipping"
    },
    {
        orderId: "PEO-14533",
        orderDate: "28 اردیبهشت 1404",
        deliveredDate: "4 خرداد 1404",
        customer: "سوفی جانسون",
        product: "کیف دستی",
        payment: "Paid",
        total: 65.50,
        qty: 1,
        status: "Delivered"
    },
    {
        orderId: "PEO-14534",
        orderDate: "1 تیر 1404",
        deliveredDate: "8 تیر 1404",
        customer: "ایتن دیویس",
        product: "کفش‌های مسابقه",
        payment: "Unpaid",
        total: 89.95,
        qty: 1,
        status: "New"
    },
    {
        orderId: "PEO-14535",
        orderDate: "19 تیر 1404",
        deliveredDate: "26 تیر 1404",
        customer: "امیلیا رودریگز",
        product: "اسپیکر بلوتوث",
        payment: "COD",
        total: 45.99,
        qty: 1,
        status: "Pending"
    },
    {
        orderId: "PEO-14536",
        orderDate: "14 مرداد 1404",
        deliveredDate: "21 مرداد 1404",
        customer: "الکساندر وایت",
        product: "کیف لپ‌تاپ",
        payment: "Paid",
        total: 38.75,
        qty: 1,
        status: "Delivered"
    },
    {
        orderId: "PEO-14537",
        orderDate: "28 شهریور 1404",
        deliveredDate: "4 مهر 1404",
        customer: "هارپر اسکات",
        product: "ماوس بی‌سیم",
        payment: "COD",
        total: 22.50,
        qty: 1,
        status: "Pending"
    },
];

// Function to update order statistics cards
function updateOrderStats(data) {
    // Count orders by status
    const stats = {
        new: data.filter(order => order.status.toLowerCase() === 'new').length,
        pending: data.filter(order => order.status.toLowerCase() === 'pending').length,
        delivered: data.filter(order => order.status.toLowerCase() === 'delivered').length,
        total: data.length
    };

    // Update card values
    document.querySelector('.card.border-primary-subtle h4').textContent = stats.new;
    document.querySelector('.card.border-warning-subtle h4').textContent = stats.pending;
    document.querySelector('.card.border-success-subtle h4').textContent = stats.delivered;
    document.querySelector('.card.border-secondary-subtle h4').textContent = stats.total;

    // Note: The percentage changes would typically come from comparing with previous period data
    // For now, they remain static unless you have historical data to calculate real percentages
}

// Call this function after loading your data
document.addEventListener('DOMContentLoaded', function () {
    // After initializing tableManager and setting data
    updateOrderStats(orderData);
});
function generateOrderId() {
    // Example: generate something like "PEO-14539"
    const randomNum = Math.floor(Math.random() * 100000);
    return `PEO-${randomNum}`;
}
// Function to calculate and update total price
function updateTotalPrice() {
    const qty = parseInt(document.querySelector('.input-spin').value) || 0;
    const price = parseFloat(document.querySelector('input[placeholder="مبلغ"]').value) || 0;
    const total = (qty * price).toFixed(2);

    // Update total price field and make it read-only
    const totalPriceInput = document.querySelector('input[placeholder="مبلغ کل"]');
    totalPriceInput.value = total;
    totalPriceInput.readOnly = true;
}

// Event listeners for input change on product amount
document.querySelector('input[placeholder="مبلغ"]').addEventListener('input', updateTotalPrice);

// Event listener for plus button
document.querySelector('.input-spin-plus').addEventListener('click', () => {
    const input = document.querySelector('.input-spin');
    let current = parseInt(input.value) || 1;
    input.value = current + 1;
    updateTotalPrice();
});

// Event listener for minus button
document.querySelector('.input-spin-minus').addEventListener('click', () => {
    const input = document.querySelector('.input-spin');
    let current = parseInt(input.value) || 1;
    // Prevent quantity from going below 1
    if (current > 1) {
        input.value = current - 1;
    }
    updateTotalPrice();
});

// Initialize total price calculation and make total price input read-only on page load
document.addEventListener('DOMContentLoaded', function () {
    const totalPriceInput = document.querySelector('input[placeholder="مبلغ کل"]');
    totalPriceInput.readOnly = true;

    // Add a visual indicator that the field is read-only (optional)
    totalPriceInput.classList.add('bg-light');

    // Initial calculation
    updateTotalPrice();
});
document.addEventListener('DOMContentLoaded', function () {
    // Create table manager instance
    const tableManager = new TableManager('orderTable');

    // Set data
    tableManager.setData(orderData);

    // Set pagination container
    tableManager.setPaginationContainer('paginationContainer');

    // Set results info container
    tableManager.setResultsInfoContainer('resultsInfo');

    // Add search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            tableManager.search(this.value);
        });
    }





    // Add sort functionality to table headers
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function () {
            const column = this.dataset.column;
            const currentDirection = this.dataset.direction || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

            // Reset all headers
            sortableHeaders.forEach(h => {
                h.dataset.direction = '';
                h.querySelector('i').className = 'ri-arrow-up-down-line ms-1';
            });

            // Set new direction for clicked header
            this.dataset.direction = newDirection;
            this.querySelector('i').className = newDirection === 'asc' ? 'ri-arrow-up-line ms-1' : 'ri-arrow-down-line ms-1';

            // Sort table
            tableManager.sort(column, newDirection === 'asc');
        });
    });
    // Add filter functionality to order tabs
    const orderTabs = document.querySelectorAll('#ordersTab .nav-link');
    if (orderTabs.length > 0) {
        orderTabs.forEach(tab => {
            tab.addEventListener('click', function () {
                // Update active tab
                orderTabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                const reverseStatusMapping = {
                    'جدید': 'New',
                    'در حال بررسی': 'Pending',
                    'در حال ارسال': 'Shipping',
                    'تحویل داده شده': 'Delivered'
                };

                // Get the filter value from tab text (or use 'All' for the first tab)
                const filterValue = this.textContent.trim();

                // Apply filter based on tab
                if (filterValue === 'همه سفارشات') {
                    // Show all orders
                    tableManager.filteredData = [...tableManager.data];
                } else {
                    // Filter orders by status
                    const englishStatus = reverseStatusMapping[filterValue] || filterValue;
                    tableManager.filteredData = tableManager.data.filter(order =>
                        order.status.toLowerCase() === englishStatus.toLowerCase()
                    );
                }

                // Reset to first page and update display
                tableManager.totalPages = Math.ceil(tableManager.filteredData.length / tableManager.rowsPerPage);
                tableManager.currentPage = 1;
                tableManager.renderTable();
                tableManager.renderPagination();
                tableManager.updateResultsInfo();
            });
        });
    }
    const orderFormBtn = document.querySelector('#addOrderModal .btn-primary');
    if (orderFormBtn) {
        orderFormBtn.addEventListener('click', function () {
            // Clear any previous error messages
            clearValidationErrors();

            // Validate all required fields
            if (!validateOrderForm()) {
                return; // Stop if validation fails
            }

            const orderId = document.getElementById('orderIDInput').value;

            const orderData = {
                orderId,
                orderDate: document.getElementById('orderDateInput').value || '',
                deliveredDate: document.getElementById('deliveredDateInput').value || '',
                customer: document.querySelector('#addOrderModal input[placeholder="نام مشتری"]').value || '',
                qty: document.querySelector('#addOrderModal .input-spin').value || '0',
                total: document.querySelector('#addOrderModal input[placeholder="مبلغ کل"]').value || '0',
                product: document.querySelector('#productNameSelect').value || 'محصول پیش‌فرض',
                payment: document.querySelector('#paymentStatusSelect').value || 'پرداخت نشده',
                status: document.querySelector('#orderStatusSelect').value || 'جدید'
            };

            // Logic to add or edit order
            if (this.dataset.orderId) {
                tableManager.editOrder(this.dataset.orderId, orderData);
                delete this.dataset.orderId;
            } else {
                tableManager.addOrder(orderData);
            }

            document.querySelector('#addOrderModal .modal-header h6').textContent = 'افزودن سفارش';
            this.textContent = 'Add Order';

            const modal = window.bootstrap.Modal.getInstance(document.getElementById('addOrderModal'));
            modal.hide();
        });
    }



    // Setup delete functionality
    document.getElementById('confirmDeleteBtn').addEventListener('click', function () {
        if (this.dataset.orderId) {
            tableManager.deleteOrder(this.dataset.orderId);
            // Clear the orderId data attribute
            delete this.dataset.orderId;
            // Close modal
            const modal = window.bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
            modal.hide();
        }
    });

    // Update populateEditForm to handle new input IDs
    const originalPopulateEditForm = TableManager.prototype.populateEditForm;

    TableManager.prototype.populateEditForm = function (order) {
        // Set form title and button text
        document.querySelector('#addOrderModal .modal-header h6').textContent = 'ویرایش سفارش';
        const updateBtn = document.querySelector('#addOrderModal .btn-primary');
        updateBtn.textContent = 'آپدیت سفارش';
        updateBtn.dataset.orderId = order.orderId;

        // Populate form fields with order data
        document.getElementById('orderIDInput').value = order.orderId;
        document.getElementById('orderIDInput').disabled = true; // Disable order ID input when editing

        // Populate date fields with updated IDs
        document.getElementById('orderDateInput').value = order.orderDate;
        document.getElementById('deliveredDateInput').value = order.deliveredDate;

        // Populate other fields
        document.querySelector('#addOrderModal input[placeholder="نام مشتری"]').value = order.customer;
        document.querySelector('#addOrderModal .input-spin').value = order.qty;
        document.querySelector('#addOrderModal input[placeholder="مبلغ کل"]').value = order.total;

        // Update the price field if it exists (assuming there's an amount field that should be populated)
        const amountInput = document.querySelector('input[placeholder="مبلغ"]');
        if (amountInput && order.qty > 0) {
            // Calculate the unit price from the total and quantity
            const unitPrice = (parseFloat(order.total) / parseInt(order.qty)).toFixed(2);
            amountInput.value = unitPrice;
        }

        // Handle dropdowns if available
        if (typeof this.setDropdownValue === 'function') {
            this.setDropdownValue('#productNameSelect', order.product);
            this.setDropdownValue('#paymentStatusSelect', order.payment);
            this.setDropdownValue('#orderStatusSelect', order.status);
        }
    };

    /**
     * Validates the order form
     * @returns {boolean} - True if form is valid, false otherwise
     */
    function validateOrderForm() {
        let isValid = true;

        // Clear any previous error messages
        clearValidationErrors();

        // Validate Order ID (required, alphanumeric)
        const orderIdInput = document.getElementById('orderIDInput');
        if (!orderIdInput.value.trim()) {
            showValidationError(orderIdInput, 'شماره سفارش الزامی است');
            isValid = false;
        } else if (!/^[a-zA-Z0-9-]+$/.test(orderIdInput.value)) {
            showValidationError(orderIdInput, 'شناسه سفارش فقط باید شامل حروف، اعداد و خط فاصله باشد');
            isValid = false;
        }

        // Validate Order Date (required, valid date format)
        const orderDateInput = document.getElementById('orderDateInput');
        if (!orderDateInput.value.trim()) {
            showValidationError(orderDateInput, 'تاریخ سفارش الزامی است');
            isValid = false;
        } else if (!isValidDate(orderDateInput.value)) {
            showValidationError(orderDateInput, 'لطفا یک تاریخ معتبر با فرمت dd MM yyyy وارد کنید.');
            isValid = false;
        }

        // Validate Customer Name (required)
        const customerInput = document.querySelector('#addOrderModal input[placeholder="نام مشتری"]');
        if (!customerInput.value.trim()) {
            showValidationError(customerInput, 'نام مشتری الزامی است');
            isValid = false;
        }

        // Validate Quantity (required, positive number)
        const qtyInput = document.querySelector('#addOrderModal .input-spin');
        if (!qtyInput.value.trim() || isNaN(qtyInput.value) || parseInt(qtyInput.value) <= 0) {
            showValidationError(qtyInput, 'لطفا تعداد معتبری وارد کنید (بیشتر از 0)');
            isValid = false;
        }

        // Validate Total Amount (required, positive number)
        const totalInput = document.querySelector('#addOrderModal input[placeholder="مبلغ کل"]');
        if (!totalInput.value.trim() || isNaN(totalInput.value) || parseFloat(totalInput.value) <= 0) {
            showValidationError(totalInput, 'لطفا مبلغ معتبری وارد کنید (بیشتر از 0)');
            isValid = false;
        }

        // Validate Product (required)
        const productSelect = document.querySelector('#productNameSelect');
        if (!productSelect.value) {
            showValidationError(productSelect, 'لطفا یک محصول انتخاب کنید');
            isValid = false;
        }

        // Validate Delivered Date (if provided, should be valid date and not before order date)
        const deliveredDateInput = document.getElementById('deliveredDateInput');
        if (deliveredDateInput.value.trim()) {
            if (!isValidDate(deliveredDateInput.value)) {
                showValidationError(deliveredDateInput, 'لطفا یک تاریخ معتبر با فرمت dd MMM  yyyy وارد کنید.');
                isValid = false;
            } else if (orderDateInput.value.trim() && isValidDate(orderDateInput.value)) {
                // Compare if delivery date is before order date
                const comparison = compareDates(orderDateInput.value, deliveredDateInput.value);
                if (comparison > 0) {
                    showValidationError(deliveredDateInput, 'تاریخ تحویل نمی‌تواند قبل از تاریخ سفارش باشد');
                    isValid = false;
                }
            }
        }

        return isValid;
    }

    /**
     * Shows validation error message below the input field
     * @param {HTMLElement} element - The input element
     * @param {string} message - Error message to display
     */
    function showValidationError(element, message) {
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.textContent = message;

        // Add error styling to the input
        element.classList.add('is-invalid');

        // Insert error message after the input element
        element.parentNode.insertBefore(errorDiv, element.nextSibling);
    }

    /**
     * Clears all validation errors
     */
    function clearValidationErrors() {
        // Remove all error messages
        document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

        // Remove error styling from inputs
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    }

    /**
     * Checks if a string is a valid date in dd MMM, yyyy format
     * @param {string} dateString - Date string to validate
     * @returns {boolean} - True if valid date, false otherwise
     */
    function isValidDate(dateString) {
        if (!dateString || !dateString.trim()) {
            return false;
        }

        // Check if it matches the dd MMM, yyyy format pattern
        // e.g., "25 May, 2023" or "01 Jan, 2025"
        const regex = /^(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec),\s+(\d{4})$/i;
        const match = dateString.match(regex);

        if (!match) {
            return false;
        }

        // Extract day, month, and year from the match
        const day = parseInt(match[1], 10);
        const monthStr = match[2].toLowerCase();
        const year = parseInt(match[3], 10);

        // Map month strings to month numbers (0-based)
        const months = {
            'jan': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'may': 4, 'jun': 5,
            'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9, 'nov': 10, 'dec': 11
        };

        const month = months[monthStr.toLowerCase()];

        // Create date object and verify it's valid
        const date = new Date(year, month, day);

        // Check if the date is valid and if the components match what was entered
        return date.getFullYear() === year &&
            date.getMonth() === month &&
            date.getDate() === day;
    }

    function compareDates(date1, date2) {
        // Parse the first date
        const regex1 = /^(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec),\s+(\d{4})$/i;
        const match1 = date1.match(regex1);
        if (!match1) return null;

        const day1 = parseInt(match1[1], 10);
        const month1 = new Date(Date.parse(`${match1[2]} 1, 2000`)).getMonth();
        const year1 = parseInt(match1[3], 10);

        // Parse the second date
        const regex2 = /^(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec),\s+(\d{4})$/i;
        const match2 = date2.match(regex2);
        if (!match2) return null;

        const day2 = parseInt(match2[1], 10);
        const month2 = new Date(Date.parse(`${match2[2]} 1, 2000`)).getMonth();
        const year2 = parseInt(match2[3], 10);

        // Create Date objects
        const dateObj1 = new Date(year1, month1, day1);
        const dateObj2 = new Date(year2, month2, day2);

        // Return comparison result
        if (dateObj1 < dateObj2) return -1;
        if (dateObj1 > dateObj2) return 1;
        return 0;
    }

    // Reset modal form when "Add New Order" button is clicked
    document.querySelector('[data-bs-target="#addOrderModal"]').addEventListener('click', () => {
        document.querySelector('#addOrderModal form').reset();

        // Enable & populate new Order ID
        const orderIDInput = document.getElementById('orderIDInput');
        orderIDInput.disabled = true;
        orderIDInput.value = generateOrderId(); // <-- Set new generated ID

        // Reset modal text
        document.querySelector('#addOrderModal .modal-header h6').textContent = 'افزودن سفارش';
        const addBtn = document.querySelector('#addOrderModal .btn-primary');
        addBtn.textContent = 'افزودن سفارش';
        delete addBtn.dataset.orderId;
    });
});