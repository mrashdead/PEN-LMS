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

//expense chart
var options = {
    series: [16, 8, 12, 9],
    labels: ['پرداخت شده', 'پرداخت نشده', 'درانتظار', 'معوقه'],
    chart: {
        height: 110,
        type: "donut",
    },
    dataLabels: {
        enabled: false
    },
    plotOptions: {
        pie: {
            expandOnClick: true,
            donut: {
                size: '60%',
            }
        }
    },
    legend: {
        offsetY: -10,
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                height: 200
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-success", "--dx-info", "--dx-warning", "--dx-danger"]
};

allCharts.push([{ 'id': 'invoiceStatusChart', 'data': options }]);

updateAllCharts();

const invoiceData = [
    {
        id: "PEI-15486",
        client: "جان دو",
        avatar: "assets/images/avatar/user-1.png",
        country: "آمریکا",
        invoiceDate: "30 اردیبهشت 1403",
        dueDate: "3 خرداد 1403",
        amount: "154.98 تومان",
        status: "پرداخت شده",
        statusClass: "badge bg-success-subtle border border-success-subtle text-success"
    },
    {
        id: "PEI-15476",
        client: "جین اسمیت",
        avatar: "assets/images/avatar/user-2.png",
        country: "چین",
        invoiceDate: "30 اردیبهشت 1403",
        dueDate: "4 خرداد 1403",
        amount: "200.00 تومان",
        status: "پرداخت نشده",
        statusClass: "badge bg-pink-subtle border border-pink-subtle text-pink"
    },
    {
        id: "PEI-15446",
        client: "مایکل ویلسون",
        avatar: "assets/images/avatar/user-5.png",
        country: "آلمان",
        invoiceDate: "2 حرداد 1403",
        dueDate: "7 خرداد 1403",
        amount: "275.30 تومان",
        status: "پرداخت شده",
        statusClass: "badge bg-success-subtle border border-success-subtle text-success"
    },
    {
        id: "PEI-15466",
        client: "رابرت جانسون",
        avatar: "assets/images/avatar/user-3.png",
        country: "روسیه",
        invoiceDate: "31 اردیبهشت 1403",
        dueDate: "5 خرداد 1403",
        amount: "350.50 تومان",
        status: "معوقه",
        statusClass: "badge bg-danger-subtle border border-danger-subtle text-danger"
    },
    {
        id: "PEI-15456",
        client: "امیلی دیویس",
        avatar: "assets/images/avatar/user-4.png",
        country: "فرانسه",
        invoiceDate: "1 خرداد 1403",
        dueDate: "6 خرداد 1403",
        amount: "420.75 تومان",
        status: "پرداخت نشده",
        statusClass: "badge bg-pink-subtle border border-pink-subtle text-pink"
    },
    {
        id: "PEI-15436",
        client: "سارا براون",
        avatar: "assets/images/avatar/user-6.png",
        country: "ارمنستان",
        invoiceDate: "3 خرداد 1403",
        dueDate: "8 خرداد 1403",
        amount: "180.00 تومان",
        status: "پرداخت نشده",
        statusClass: "badge bg-pink-subtle border border-pink-subtle text-pink"
    },
    {
        id: "PEI-15426",
        client: "دیوید تیلور",
        avatar: "assets/images/avatar/user-7.png",
        country: "انگلیس",
        invoiceDate: "4 خرداد 1403",
        dueDate: "8 خرداد 1403",
        amount: "320.40 تومان",
        status: "پرداخت شده",
        statusClass: "badge bg-success-subtle border border-success-subtle text-success"
    },
    {
        id: "PEI-15416",
        client: "جسیکا مارتینز",
        avatar: "assets/images/avatar/user-8.png",
        country: "گرجستان",
        invoiceDate: "5 خرداد 1403",
        dueDate: "10 حرداد 1403",
        amount: "210.25 تومان",
        status: "در حال بررسی",
        statusClass: "badge bg-warning-subtle border border-warning-subtle text-warning"
    },
    {
        id: "PEI-15406",
        client: "توماس اندرسون",
        avatar: "assets/images/avatar/user-9.png",
        country: "هند",
        invoiceDate: "6 خرداد 1403",
        dueDate: "11 خرداد 1403",
        amount: "450.00 تومان",
        status: "پرداخت شده",
        statusClass: "badge bg-success-subtle border border-success-subtle text-success"
    },
    {
        id: "PEI-15396",
        client: "لیزا جکسون",
        avatar: "assets/images/avatar/user-10.png",
        country: "پاکستان",
        invoiceDate: "7 خرداد 1403",
        dueDate: "12 خرداد 1403",
        amount: "290.75 تومان",
        status: "پرداخت نشده",
        statusClass: "badge bg-pink-subtle border border-pink-subtle text-pink"
    },
    {
        id: "PEI-15397",
        client: "مایکل ترنر",
        avatar: "assets/images/avatar/user-5.png",
        country: "ترکیه",
        invoiceDate: "10 حرداد 1403",
        dueDate: "16 خرداد 1403",
        amount: "475.00 تومان",
        status: "پرداخت شده",
        statusClass: "badge bg-success-subtle border border-success-subtle text-success"
    },
    {
        id: "PEI-15398",
        client: "اما واتسون",
        avatar: "assets/images/avatar/user-12.png",
        country: "کانادا",
        invoiceDate: "2 حرداد 1403",
        dueDate: "7 خرداد 1403",
        amount: "340.50 تومان",
        status: "پرداخت نشده",
        statusClass: "badge bg-pink-subtle border border-pink-subtle text-pink"
    },
    {
        id: "PEI-15399",
        client: "دنیل کریگ",
        avatar: "assets/images/avatar/user-18.png",
        country: "آمریکا",
        invoiceDate: "26 اردیبهشت 1403",
        dueDate: "31 اردیبهشت 1403",
        amount: "620.30 تومان",
        status: "معوقه",
        statusClass: "badge bg-danger-subtle border border-danger-subtle text-danger"
    },
    {
        id: "PEI-15400",
        client: "سوفیا لی",
        avatar: "assets/images/avatar/user-3.png",
        country: "فرانسه",
        invoiceDate: "21 اردیبهشت 1403",
        dueDate: "26 اردیبهشت 1403",
        amount: "150.00 تومان",
        status: "پرداخت شده",
        statusClass: "badge bg-success-subtle border border-success-subtle text-success"
    },
    {
        id: "PEI-15401",
        client: "لیام اسمیت",
        avatar: "assets/images/avatar/user-26.png",
        country: "ایران",
        invoiceDate: "5 خرداد 1403",
        dueDate: "10 حرداد 1403",
        amount: "289.90 تومان",
        status: "پرداخت نشده",
        statusClass: "badge bg-pink-subtle border border-pink-subtle text-pink"
    },
    {
        id: "PEI-15402",
        client: "اولیویا براون",
        avatar: "assets/images/avatar/user-9.png",
        country: "ترکمنستان",
        invoiceDate: "12 خرداد 1403",
        dueDate: "17 خرداد 1403",
        amount: "399.99 تومان",
        status: "پرداخت شده",
        statusClass: "badge bg-success-subtle border border-success-subtle text-success"
    },
    {
        id: "PEI-15403",
        client: "ایتن دیویس",
        avatar: "assets/images/avatar/user-22.png",
        country: "هند",
        invoiceDate: "31 اردیبهشت 1403",
        dueDate: "5 خرداد 1403",
        amount: "510.00 تومان",
        status: "معوقه",
        statusClass: "badge bg-danger-subtle border border-danger-subtle text-danger"
    }
];

// Create a local copy
let workingInvoiceData = [...invoiceData];

// Pagination variables
const itemsPerPage = 10;
let currentPage = 1;
let deleteRecordId = null;

// Sorting variables
let currentSortColumn = 'id';
let currentSortDirection = 'asc';

// Cache DOM elements
const elements = {
    tableBody: document.getElementById('tableBody'),
    pagination: document.getElementById('pagination'),
    deleteButton: document.getElementById('deleteButton'),
    showingResults: document.getElementById('showingResults'),
    bulkDeleteButton: document.querySelector('.btn-danger.btn-icon'),
    checkboxAll: document.getElementById('checkboxDataAll'),
    searchInput: document.getElementById('searchCategoryInput')
};

function createTableRow(item) {
    const row = document.createElement('tr');
    row.dataset.rowId = item.id;

    row.innerHTML = `
        <td>
            <div class="form-check check-primary">
                <input class="form-check-input invoice-checkbox" title="checkbox" type="checkbox" id="checkboxData${item.id}" data-id="${item.id}">
                <label class="form-check-label d-none" for="checkboxData${item.id}">
                    Data ${item.id}
                </label>
            </div>
        </td>
        <td>${item.id}</td>
        <td>
            <div class="d-flex align-items-center gap-2">
                <img src="${item.avatar}" loading="lazy" alt="" class="size-7 flex-shrink-0 rounded-circle">
                <a href="#!" class="link link-custom">${item.client}</a>
            </div>
        </td>
        <td>${item.country}</td>
        <td>${item.invoiceDate}</td>
        <td>${item.dueDate}</td>
        <td>${item.amount}</td>
        <td><span class="badge ${item.statusClass}">${item.status}</span></td>
        <td>
            <div class="dropdown">
                <a href="#!" class="link link-custom-primary" id="invoice${item.id}Dropdown" data-bs-toggle="dropdown" aria-expanded="false" title="dropdown-button">
                    <i class="ri-more-2-fill"></i>
                </a>
                <ul class="dropdown-menu" aria-labelledby="invoice${item.id}Dropdown">
                    <li><a class="dropdown-item" href="#"><i class="me-3 ri-eye-line"></i>نمای کلی</a></li>
                    <li><a class="dropdown-item edit-invoice-btn" href="#"><i class="me-3 ri-pencil-line"></i>ویرایش</a></li>
                    <li><a class="dropdown-item delete-invoice-btn" href="#deleteModal" data-id="${item.id}" data-bs-toggle="modal"><i class="me-3 ri-delete-bin-line"></i>حذف</a></li>
                </ul>
            </div>
        </td>
    `;
    return row;
}

function createEmptyStateRow() {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td colspan="9" class="text-center py-4">
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
                <p class="text-muted mb-0">ما نتوانستیم هیچ فاکتوری مطابق با جستجوی شما پیدا کنیم.</p>
            </div>
        </td>
    `;
    return row;
}

function calculatePagination() {
    const totalItems = workingInvoiceData.length;
    const pageCount = Math.max(1, Math.ceil(totalItems / itemsPerPage));

    currentPage = Math.min(Math.max(1, currentPage), pageCount);

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, totalItems);

    return {
        totalItems,
        pageCount,
        startIndex,
        endIndex,
        currentItems: workingInvoiceData.slice(startIndex, endIndex)
    };
}

function displayData() {
    if (!elements.tableBody) return;

    const { currentItems, totalItems } = calculatePagination();
    elements.tableBody.innerHTML = '';

    // Check if there are no results
    if (totalItems === 0) {
        // Show empty state
        elements.tableBody.appendChild(createEmptyStateRow());

        // Hide select all checkbox since there's nothing to select
        if (elements.checkboxAll) {
            elements.checkboxAll.checked = false;
            elements.checkboxAll.disabled = true;
        }

        // Hide bulk delete button
        toggleBulkDeleteButton(false);
    } else {
        // Enable select all checkbox
        if (elements.checkboxAll) {
            elements.checkboxAll.disabled = false;
        }

        // Add data rows
        const fragment = document.createDocumentFragment();
        currentItems.forEach(item => {
            fragment.appendChild(createTableRow(item));
        });
        elements.tableBody.appendChild(fragment);
        initRowEventListeners();
    }

    updatePaginationUI();
    displayResults();
    setupCheckboxSelection();
    updateSortIcons();
}

function displayResults() {
    if (!elements.showingResults) return;

    const { startIndex, endIndex, totalItems } = calculatePagination();
    const startResult = totalItems > 0 ? startIndex + 1 : 0;

    if (totalItems === 0) {
        elements.showingResults.innerHTML = '';
    } else {
        elements.showingResults.innerHTML = `نمایش <b class="me-1">${startResult}-${endIndex}</b> از <b class="me-1">${totalItems}</b> نتیجه`;
    }
}

function initRowEventListeners() {
    document.querySelectorAll('.delete-invoice-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            deleteRecordId = this.getAttribute('data-id');
        });
    });

    document.querySelectorAll('.invoice-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });
}

function handleCheckboxChange() {
    if (!elements.checkboxAll) return;

    const checkboxes = document.querySelectorAll('.invoice-checkbox');
    const checkedBoxes = document.querySelectorAll('.invoice-checkbox:checked');

    if (checkboxes.length === checkedBoxes.length && checkboxes.length > 0) {
        elements.checkboxAll.checked = true;
    } else if (checkedBoxes.length === 0) {
        elements.checkboxAll.checked = false;
    } else {
        elements.checkboxAll.checked = false;
    }

    toggleBulkDeleteButton(checkedBoxes.length > 0);
}

function setupCheckboxSelection() {
    if (!elements.checkboxAll) return;
    elements.checkboxAll.checked = false;
    elements.checkboxAll.removeEventListener('change', handleSelectAllChange);
    elements.checkboxAll.addEventListener('change', handleSelectAllChange);
    handleCheckboxChange();
}

function handleSelectAllChange() {
    const isChecked = elements.checkboxAll.checked;
    document.querySelectorAll('.invoice-checkbox').forEach(checkbox => {
        checkbox.checked = isChecked;
    });
    toggleBulkDeleteButton(isChecked);
}

function toggleBulkDeleteButton(show) {
    if (!elements.bulkDeleteButton) return;
    elements.bulkDeleteButton.classList.toggle('d-none', !show);
}

function setupPagination() {
    if (!elements.pagination) return;

    const { pageCount, totalItems } = calculatePagination();
    elements.pagination.innerHTML = '';

    // Don't show pagination if there are no results
    if (totalItems === 0) {
        elements.pagination.classList.add('d-none');
        return;
    } else {
        elements.pagination.classList.remove('d-none');
    }

    const fragment = document.createDocumentFragment();

    const prevLi = document.createElement('li');
    prevLi.classList.add('page-item');
    if (currentPage === 1) prevLi.classList.add('disabled');
    prevLi.innerHTML = `<a href="#" class="page-link" id="prev"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
    prevLi.addEventListener('click', handlePrevClick);
    fragment.appendChild(prevLi);

    for (let i = 1; i <= pageCount; i++) {
        const li = document.createElement('li');
        li.classList.add('page-item');
        if (i === currentPage) li.classList.add('active');
        li.innerHTML = `<a href="#" class="page-link" data-page="${i}">${i}</a>`;
        li.addEventListener('click', handlePageClick);
        fragment.appendChild(li);
    }

    const nextLi = document.createElement('li');
    nextLi.classList.add('page-item');
    if (currentPage === pageCount || pageCount === 0) nextLi.classList.add('disabled');
    nextLi.innerHTML = `<a href="#" class="page-link" id="next">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
    nextLi.addEventListener('click', handleNextClick);
    fragment.appendChild(nextLi);

    elements.pagination.appendChild(fragment);
    createIcons({ icons });
}

function handlePrevClick(e) {
    e.preventDefault();
    if (currentPage > 1) {
        currentPage--;
        displayData();
    }
}

function handlePageClick(e) {
    e.preventDefault();
    const pageNum = parseInt(e.target.getAttribute('data-page'), 10);
    if (!isNaN(pageNum) && pageNum !== currentPage) {
        currentPage = pageNum;
        displayData();
    }
}

function handleNextClick(e) {
    e.preventDefault();
    const { pageCount } = calculatePagination();
    if (currentPage < pageCount) {
        currentPage++;
        displayData();
    }
}

function updatePaginationUI() {
    setupPagination();
}

function deleteSingleInvoice() {
    if (!deleteRecordId) return;
    workingInvoiceData = workingInvoiceData.filter(item => item.id !== deleteRecordId);
    adjustPageAfterDelete();
    displayData();
    deleteRecordId = null;
}

function bulkDelete() {
    const checkedBoxes = document.querySelectorAll('.invoice-checkbox:checked');
    if (checkedBoxes.length === 0) return;

    const idsToDelete = Array.from(checkedBoxes).map(cb => cb.getAttribute('data-id'));
    workingInvoiceData = workingInvoiceData.filter(item => !idsToDelete.includes(item.id));
    adjustPageAfterDelete();
    displayData();
    toggleBulkDeleteButton(false);
}

function adjustPageAfterDelete() {
    const { pageCount } = calculatePagination();
    if (currentPage > pageCount) {
        currentPage = Math.max(1, pageCount);
    }
}

function filterInvoiceData(query) {
    if (!query || query.trim() === '') return [...invoiceData];
    query = query.toLowerCase().trim();

    return invoiceData.filter(item => {
        return item.id.toLowerCase().includes(query) ||
            item.client.toLowerCase().includes(query) ||
            item.country.toLowerCase().includes(query) ||
            item.invoiceDate.toLowerCase().includes(query) ||
            item.dueDate.toLowerCase().includes(query) ||
            item.amount.toLowerCase().includes(query) ||
            item.status.toLowerCase().includes(query);
    });
}

function handleSearch() {
    const query = elements.searchInput.value;
    workingInvoiceData = filterInvoiceData(query);
    sortInvoiceData(currentSortColumn, currentSortDirection);
    currentPage = 1;
    displayData();
}

function initSearchFeature() {
    if (elements.searchInput) {
        let searchTimeout;
        elements.searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(handleSearch, 300);
        });

        elements.searchInput.addEventListener('search', handleSearch);
    }
}

function initIcons() {
    createIcons({ icons });
}

// SORTING FUNCTIONALITY
function initSortableColumns() {
    const tableHeaders = document.querySelectorAll('th[data-sort]');

    tableHeaders.forEach(header => {
        // Skip the checkbox column and actions column
        if (header.dataset.sort === 'checkbox' || header.dataset.sort === 'actions') return;

        // Add sort icon and make header clickable
        const headerText = header.textContent;
        header.innerHTML = `
            <div class="d-flex align-items-center cursor-pointer sort-header">
                <span>${headerText}</span>
                <span class="sort-icon ms-1">
                    <i class="ri-arrow-up-line sort-icon-up"></i>
                </span>
            </div>
        `;

        // Add click event listener
        header.addEventListener('click', () => {
            const sortColumn = header.dataset.sort;
            let sortDirection = 'asc';

            // Toggle sort direction if clicking the same column
            if (sortColumn === currentSortColumn) {
                sortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
            }

            sortInvoiceData(sortColumn, sortDirection);
            currentSortColumn = sortColumn;
            currentSortDirection = sortDirection;

            currentPage = 1; // Reset to first page on sort
            displayData();
        });
    });
}

function sortInvoiceData(column, direction) {
    const multiplier = direction === 'asc' ? 1 : -1;

    workingInvoiceData.sort((a, b) => {
        let valueA, valueB;

        // For client column, extract the client name
        if (column === 'client') {
            valueA = a[column].toLowerCase();
            valueB = b[column].toLowerCase();
        }
        // For amount column, convert to number without currency symbol
        else if (column === 'amount') {
            valueA = parseFloat(a[column].replace(/[^0-9.-]+/g, ''));
            valueB = parseFloat(b[column].replace(/[^0-9.-]+/g, ''));
        }
        // For date columns, convert to date objects
        else if (column === 'invoiceDate' || column === 'dueDate') {
            valueA = new Date(a[column]);
            valueB = new Date(b[column]);
        }
        // For other columns, use string comparison
        else {
            valueA = typeof a[column] === 'string' ? a[column].toLowerCase() : a[column];
            valueB = typeof b[column] === 'string' ? b[column].toLowerCase() : b[column];
        }

        if (valueA < valueB) return -1 * multiplier;
        if (valueA > valueB) return 1 * multiplier;
        return 0;
    });
}

function updateSortIcons() {
    // Reset all icons first
    document.querySelectorAll('.sort-icon').forEach(icon => {
        icon.innerHTML = '<i class="ri-arrow-up-line sort-icon-up"></i>';
        icon.classList.remove('active');
    });

    // Update active sort column icon
    const activeHeader = document.querySelector(`th[data-sort="${currentSortColumn}"]`);
    if (activeHeader) {
        const sortIcon = activeHeader.querySelector('.sort-icon');
        if (sortIcon) {
            sortIcon.classList.add('active');
            if (currentSortDirection === 'asc') {
                sortIcon.innerHTML = '<i class="ri-arrow-up-line sort-icon-up active"></i>';
            } else {
                sortIcon.innerHTML = '<i class="ri-arrow-down-line sort-icon-down active"></i>';
            }
        }
    }
}

function init() {
    if (!elements.tableBody) return;

    // Initial sorting
    sortInvoiceData(currentSortColumn, currentSortDirection);

    displayData();

    // Initialize sortable columns
    initSortableColumns();

    if (elements.deleteButton) {
        elements.deleteButton.addEventListener('click', deleteSingleInvoice);
    }

    if (elements.bulkDeleteButton) {
        elements.bulkDeleteButton.addEventListener('click', bulkDelete);
    }

    initSearchFeature();
    initIcons();
}

document.addEventListener('DOMContentLoaded', init);