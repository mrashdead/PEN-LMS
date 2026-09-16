import { icons, ArrowDown, ArrowUp, createIcons } from "lucide";


/**
 * Sortable Holiday Table Manager
 * 
 * A vanilla JavaScript class to manage holiday data with pagination, sorting, add, edit, and delete functionality
 */
class TableManager {
    constructor(options = {}) {
        // Default options
        this.options = {
            itemsPerPage: 10,
            containerSelector: '.table-card',
            paginationSelector: '.pagination',
            resultsInfoSelector: '.col-md-6 p',
            addModalId: 'addHolidayModal',
            deleteModalId: 'deleteModal',
            ...options
        };

        // Initialize data and state
        this.allData = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.editingIndex = null;

        // Sorting state
        this.sortColumn = null;
        this.sortDirection = 'asc';

        // DOM Elements
        this.container = document.querySelector(this.options.containerSelector);
        this.paginationEl = document.querySelector(this.options.paginationSelector);
        this.resultsInfoEl = document.querySelector(this.options.resultsInfoSelector);
        this.addModal = document.getElementById(this.options.addModalId);
        this.deleteModal = document.getElementById(this.options.deleteModalId);

        

        // Initialize with sample data
        this.initializeData();

        // Set up event listeners
        this.setupEventListeners();
    }

    initializeData() {
        // Initial data from the HTML
        this.allData = [
            { name: "22 بهمن", date: "22 بهمن 1405", day: "پنجشنبه" },
            { name: "روز ولنتاین", date: "25 بهمن 1405", day: "دوشنبه" },
            { name: "ملی شدن صنعت نفت", date: "29 اسفند 1405", day: "شنبه" },
            { name: "عید نوروز", date: "1 فروردین 1406", day: "یکشنبه" },
            { name: "سیزده به در", date: "13 فروردین 1406", day: "جمعه" },
            { name: "روز زمین", date: "2 اردیبهشت 1406", day: "چهارشنبه" },
            { name: "روز مادر", date: "22 اردیبهشت 1406", day: "یکشنبه" },
            { name: "روز استقلال", date: "13 تیر 1406", day: "پنجشنبه" },
            { name: "روز کارگر", date: "11 اردیبهشت 1406", day: "شنبه" },
            { name: "روز هالووین", date: "9 آبان 1406", day: "یکشنبه" },
            { name: "روز جانبازان", date: "11 آذر 1406", day: "سه‌شنبه" },
            { name: "عید شکرگزاری", date: "28 آذر 1406", day: "پنجشنبه" },
            { name: "شب کریسمس", date: "3 دی 1406", day: "جمعه" },
            { name: "تعطیلات کریسمس", date: "4 دی 1406", day: "شنبه" },
            { name: "سال نوی میلادی", date: "11 دی 1406", day: "شنبه" },
            { name: "روز مردم کم توان", date: "14 بهمن 1406", day: "دوشنبه" },
            { name: "روز جهانی زن", date: "18 اسفند 1406", day: "چهارشنبه" }
        ];

        this.totalPages = Math.ceil(this.allData.length / this.options.itemsPerPage);

        // Render the initial view
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    setupEventListeners() {
        // Add form submission
        const addForm = document.querySelector(`#${this.options.addModalId} form`);
        if (addForm) {
            addForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit();
            });
        }

        // Delete confirmation
        const deleteBtn = document.querySelector(`#${this.options.deleteModalId} .btn-danger`);
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                if (this.deleteIndex !== null) {
                    this.deleteHoliday(this.deleteIndex);
                    this.deleteIndex = null;
                }
            });
        }



        // Listen for page changes
        document.addEventListener('click', (e) => {
            // Table header click for sorting
            if (e.target.closest('th.sortable')) {
                const th = e.target.closest('th.sortable');
                const column = th.dataset.column;
                this.handleSort(column);
                return;
            }

            if (e.target.closest('.pagination')) {
                e.preventDefault();

                const pageLink = e.target.closest('.page-link');
                if (!pageLink) return;

                if (pageLink.textContent.includes('قبلی')) {
                    this.goToPage(this.currentPage - 1);
                } else if (pageLink.textContent.includes('بعدی')) {
                    this.goToPage(this.currentPage + 1);
                } else {
                    const page = parseInt(pageLink.textContent);
                    if (!isNaN(page)) {
                        this.goToPage(page);
                    }
                }
            }

            // Edit button click
            if (e.target.closest('.btn-sub-primary')) {
                const row = e.target.closest('tr');
                const index = Array.from(row.parentElement.children).indexOf(row);
                const dataIndex = (this.currentPage - 1) * this.options.itemsPerPage + index;
                this.editingIndex = dataIndex;
                this.populateEditForm(dataIndex);
            }

            // Delete button click
            if (e.target.closest('.btn-sub-danger')) {
                const row = e.target.closest('tr');
                const index = Array.from(row.parentElement.children).indexOf(row);
                const dataIndex = (this.currentPage - 1) * this.options.itemsPerPage + index;
                this.deleteIndex = dataIndex;
            }
        });

        // Search functionality
        const searchInput = document.getElementById('tableSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchHolidays(e.target.value);
            });
        }
    }

    // Helper function to get day of week from date
    getDayOfWeek(date) {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        return days[date.getDay()];
    }

    handleSort(column) {
        // If clicking the same column, toggle direction
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // New column, set to ascending by default
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        // Sort the data
        this.sortData();

        // Refresh the UI
        this.renderTable();
    }

    sortData() {
        if (!this.sortColumn) return;

        const column = this.sortColumn;
        const direction = this.sortDirection;

        this.allData.sort((a, b) => {
            let valueA = a[column];
            let valueB = b[column];

            // Special handling for date columns
            if (column === 'date') {
                // Convert date strings to Date objects for comparison
                const parseDate = (dateStr) => {
                    const [day, month, year] = dateStr.split(' ');
                    const monthMap = {
                        'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                        'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
                    };
                    return new Date(year, monthMap[month], parseInt(day));
                };

                valueA = parseDate(valueA);
                valueB = parseDate(valueB);
            }

            // For string comparison
            if (typeof valueA === 'string' && typeof valueB === 'string') {
                valueA = valueA.toLowerCase();
                valueB = valueB.toLowerCase();
            }

            if (valueA < valueB) {
                return direction === 'asc' ? -1 : 1;
            }
            if (valueA > valueB) {
                return direction === 'asc' ? 1 : -1;
            }
            return 0;
        });
    }

    renderTable() {
        // Calculate the start and end indices for the current page
        const startIndex = (this.currentPage - 1) * this.options.itemsPerPage;
        const endIndex = Math.min(startIndex + this.options.itemsPerPage, this.allData.length);

        // Get the data for the current page
        const currentPageData = this.allData.slice(startIndex, endIndex);

        // Create table HTML with sortable headers
        let tableHTML = `
        <table class="table table-borderless text-nowrap mb-0">
          <thead>
            <tr class="bg-light border-bottom">
              <th class="fw-medium text-muted sortable" data-column="name">
                نام تعطیلی
                ${this.getSortIcon('name')}
              </th>
              <th class="fw-medium text-muted sortable" data-column="date">
                تاریخ
                ${this.getSortIcon('date')}
              </th>
              <th class="fw-medium text-muted sortable" data-column="day">
                روز
                ${this.getSortIcon('day')}
              </th>
              <th class="fw-medium text-muted">عملیات</th>
            </tr>
          </thead>
          <tbody>
      `;

        // Add rows for the current page data
        currentPageData.forEach(holiday => {
            tableHTML += `
          <tr>
            <td>${holiday.name}</td>
            <td>${holiday.date}</td>
            <td>${holiday.day}</td>
            <td>
              <div class="d-flex align-items-center gap-2">
                <button class="btn btn-sub-primary size-8 rounded btn-icon" data-bs-toggle="modal" data-bs-target="#${this.options.addModalId}">
                  <i class="ri-pencil-line"></i>
                </button>
                <button class="btn btn-sub-danger size-8 rounded btn-icon" data-bs-toggle="modal" data-bs-target="#${this.options.deleteModalId}">
                  <i class="ri-delete-bin-line"></i>
                </button>
              </div>
            </td>
          </tr>
        `;
        });

        // Close the table
        tableHTML += `
          </tbody>
        </table>
      `;

        // Update the container with the new table
        this.container.innerHTML = tableHTML;

        // Initialize the sort icons
        createIcons({ icons });
    }

    getSortIcon(column) {
        if (this.sortColumn !== column) {
            return `<span class="sort-icon"></span>`;
        }

        return this.sortDirection === 'asc'
            ? `<span class="sort-icon"><i data-lucide="arrow-up" class="size-4"></i></span>`
            : `<span class="sort-icon"><i data-lucide="arrow-down" class="size-4"></i></span>`;
    }

    renderPagination() {
        let paginationHTML = `
        <ul class="pagination justify-content-center justify-content-md-end mb-0">
          <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#!">
              <i data-lucide="chevron-right" class="size-4"></i> قبلی
            </a>
          </li>
      `;

        // Add page numbers
        for (let i = 1; i <= this.totalPages; i++) {
            paginationHTML += `
          <li class="page-item ${i === this.currentPage ? 'active' : ''}">
            <a class="page-link" href="#!">${i}</a>
          </li>
        `;
        }

        paginationHTML += `
        <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
          <a class="page-link" href="#!">
            بعدی <i data-lucide="chevron-left" class="size-4"></i>
          </a>
        </li>
      </ul>
      `;

        // Update the pagination element
        if (this.paginationEl) {
            this.paginationEl.innerHTML = paginationHTML;
        }

        // Initialize the pagination icons
        createIcons({ icons });
    }

    updateResultsInfo() {
        const startItem = (this.currentPage - 1) * this.options.itemsPerPage + 1;
        const endItem = Math.min(this.currentPage * this.options.itemsPerPage, this.allData.length);

        if (this.resultsInfoEl) {
            this.resultsInfoEl.innerHTML = `نمایش <b class="me-1">${startItem}-${endItem}</b>از<b class="ms-1">${this.allData.length}</b> نتیجه`;
        }
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;

        this.currentPage = page;
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    populateEditForm(index) {
        const holiday = this.allData[index];
        if (!holiday) return;

        document.getElementById('holidayInput').value = holiday.name;

        document.getElementById('dateInput').value = holiday.date;

        document.getElementById('daysInput').value = holiday.day;

        // Change modal title to indicate editing
        const modalTitle = document.querySelector(`#${this.options.addModalId} .modal-title`);
        if (modalTitle) {
            modalTitle.textContent = 'ویرایش تعطیلی';
        }

        // Change submit button text
        const submitBtn = document.querySelector(`#${this.options.addModalId} form button[type="submit"]`);
        if (submitBtn) {
            submitBtn.textContent = 'آپدیت تعطیلی';
        }
    }

    handleFormSubmit() {
        // Get form values
        const name = document.getElementById('holidayInput').value;
        let date;

            date = document.getElementById('dateInput').value;

        const day = document.getElementById('daysInput').value;

        if (!name || !date || !day) {
            alert('لطفا تمام فیلدهای ضروری را پر کنید');
            return;
        }

        const holiday = { name, date, day };

        if (this.editingIndex !== null) {
            // Update existing holiday
            this.allData[this.editingIndex] = holiday;
            this.editingIndex = null;
        } else {
            // Add new holiday
            this.allData.unshift(holiday);
            this.totalPages = Math.ceil(this.allData.length / this.options.itemsPerPage);
        }

        // Sort the data if a sort is active
        if (this.sortColumn) {
            this.sortData();
        }

        // Reset form
        document.getElementById('holidayInput').value = '';
        if (this.datepicker) {
            this.datepicker.clear();
        } else {
            document.getElementById('dateInput').value = '';
        }
        document.getElementById('daysInput').value = '';

        // Reset modal title and button
        const modalTitle = document.querySelector(`#${this.options.addModalId} .modal-title`);
        if (modalTitle) {
            modalTitle.textContent = 'افزودن تعطیلی';
        }

        const submitBtn = document.querySelector(`#${this.options.addModalId} form button[type="submit"]`);
        if (submitBtn) {
            submitBtn.textContent = 'افزودن تعطیلات';
        }

        // Close modal
        const modalInstance = window.bootstrap.Modal.getInstance(document.getElementById(this.options.addModalId));
        if (modalInstance) {
            modalInstance.hide();
        }

        // Update UI
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    deleteHoliday(index) {
        if (index < 0 || index >= this.allData.length) return;

        // Remove the holiday
        this.allData.splice(index, 1);

        // Update total pages
        this.totalPages = Math.ceil(this.allData.length / this.options.itemsPerPage);

        // If current page is now greater than total pages, go to last page
        if (this.currentPage > this.totalPages) {
            this.currentPage = this.totalPages || 1;
        }

        // Update UI
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    // Export data as JSON
    getDataAsJSON() {
        return JSON.stringify(this.allData);
    }

    // Search functionality
    searchHolidays(query) {
        if (!query) {
            // Reset to show all data
            this.renderTable();
            this.renderPagination();
            this.updateResultsInfo();
            return;
        }

        query = query.toLowerCase();
        const filteredData = this.allData.filter(holiday =>
            holiday.name.toLowerCase().includes(query) ||
            holiday.date.toLowerCase().includes(query) ||
            holiday.day.toLowerCase().includes(query)
        );

        // Create temporary backup of all data
        const originalData = this.allData;

        // Replace allData with filtered data temporarily
        this.allData = filteredData;

        // Update total pages based on filtered data
        this.totalPages = Math.ceil(this.allData.length / this.options.itemsPerPage);

        // Reset to page 1 for search results
        this.currentPage = 1;

        // Update UI with filtered data
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();

        // Restore original data
        this.allData = originalData;
    }
}

// Initialize the table manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {

    const tableManager = new TableManager();

    // Make it available globally for debugging or external access
    window.tableManager = tableManager;
});