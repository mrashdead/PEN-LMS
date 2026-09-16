import { icons, createIcons } from "lucide";




VirtualSelect.init({
    ele: "#stdFilterSelect",
    options: [
        { label: "همه", value: "All" },
        { label: "کلاس 12", value: "12" },
        { label: "کلاس 11", value: "11" },
        { label: "کلاس 10", value: "10" },
        { label: "کلاس 9", value: "9" },
        { label: "کلاس 8", value: "8" },
        { label: "کلاس 7", value: "7" },
        { label: "کلاس 6", value: "6" }
    ],
});
//Date Filter select
VirtualSelect.init({
    ele: "#dateFilterSelect",
    options: [
        { label: "همه", value: "All" },
        { label: "امروز", value: "Today" },
        { label: "فردا", value: "Tomorrow" },
        { label: "هفتگی", value: "Weekly" },
        { label: "ماهانه", value: "Monthly" },
        { label: "سالانه", value: "Yearly" }
    ],
});
//Test Category select
VirtualSelect.init({
    ele: "#testCategorySelect",
    options: [
        { label: "آزمون نهایی", value: "Final Test" },
        { label: "آزمون عملی", value: "Practice Test" },
        { label: "آزمون میانترم", value: "Midterm Test" },
        { label: "آزمون پایان ترم", value: "Quarterly Test" },
    ],
});
//Test Type select
VirtualSelect.init({
    ele: "#testTypeSelect",
    options: [
        { label: "عمومی", value: "General" },
        { label: "آزمون تکوینی", value: "Formative" },
        { label: "جمع بندی", value: "Summative" },
        { label: "آنلاین", value: "Online" },
        { label: "آزمون جبرانی", value: "Rejoining" },
    ],
});
//Class select
VirtualSelect.init({
    ele: "#classSelect",
    options: [
        { label: "کلاس 6", value: "6" },
        { label: "کلاس 7", value: "7" },
        { label: "کلاس 8", value: "8" },
        { label: "کلاس 9", value: "9" },
        { label: "کلاس 10", value: "10" },
        { label: "کلاس 11", value: "11" },
        { label: "کلاس 12", value: "12" }
    ],
});
//Status select
VirtualSelect.init({
    ele: "#statusSelect",
    options: [
        { label: "تازه", value: "New" },
        { label: "برنامه‌ریزی‌ شده", value: "Scheduled" },
        { label: "تکمیل شده", value: "Completed" }
    ],
});

const examScheduleData = {
    totalResults: 12,
    pageSize: 10,
    currentPage: 1,
    data: [
        {
            id: "PEE-498",
            testName: "زبان انگلیسی",
            testCategory: "آزمون نهایی",
            testType: "عمومی",
            class: "12",
            startDate: "22 دی 1404",
            endDate: "22 دی 1404",
            status: "تازه"
        },
        {
            id: "PEE-499",
            testName: "کامپیوتر",
            testCategory: "آزمون عملی",
            testType: "آزمون تکوینی",
            class: "12",
            startDate: "29 خرداد 1405",
            endDate: "29 خرداد 1405",
            status: "برنامه‌ریزی‌ شده"
        },
        {
            id: "PEE-500",
            testName: "ریاضیات",
            testCategory: "آزمون میانترم",
            testType: "جمع بندی",
            class: "11",
            startDate: "24 اسفند 1404",
            endDate: "24 اسفند 1404",
            status: "برنامه‌ریزی‌ شده"
        },
        {
            id: "PEE-501",
            testName: "فیزیک",
            testCategory: "آزمون پایان ترم",
            testType: "جمع بندی",
            class: "10",
            startDate: "10 تیر 1405",
            endDate: "10 تیر 1405",
            status: "تکمیل شده"
        },
        {
            id: "PEE-502",
            testName: "شیمی",
            testCategory: "آزمون نهایی",
            testType: "عمومی",
            class: "12",
            startDate: "29 مرداد 1405",
            endDate: "29 مرداد 1405",
            status: "تازه"
        },
        {
            id: "PEE-503",
            testName: "زیست‌شناسی",
            testCategory: "آزمون عملی",
            testType: "آزمون تکوینی",
            class: "11",
            startDate: "22 بهمن 1404",
            endDate: "22 بهمن 1404",
            status: "برنامه‌ریزی‌ شده"
        },
        {
            id: "PEE-504",
            testName: "تاریخ",
            testCategory: "آزمون پایان ترم",
            testType: "جمع بندی",
            class: "10",
            startDate: "8 مهر 1405",
            endDate: "8 مهر 1405",
            status: "تکمیل شده"
        },
        {
            id: "PEE-505",
            testName: "جغرافیا",
            testCategory: "آزمون پایان ترم",
            testType: "جمع بندی",
            class: "9",
            startDate: "4 خرداد 1405",
            endDate: "4 خرداد 1405",
            status: "برنامه‌ریزی‌ شده"
        },
        {
            id: "PEE-506",
            testName: "اقتصاد",
            testCategory: "آزمون نهایی",
            testType: "آنلاین",
            class: "12",
            startDate: "25 مهر 1405",
            endDate: "25 مهر 1405",
            status: "تازه"
        },
        {
            id: "PEE-507",
            testName: "علوم سیاسی",
            testCategory: "آزمون عملی",
            testType: "آزمون تکوینی",
            class: "11",
            startDate: "18 آبان 1405",
            endDate: "18 آبان 1405",
            status: "برنامه‌ریزی‌ شده"
        },
        {
            id: "PEE-508",
            testName: "هنر",
            testCategory: "آزمون نهایی",
            testType: "عمومی",
            class: "10",
            startDate: "21 آذر 1405",
            endDate: "21 آذر 1405",
            status: "تازه"
        },
        {
            id: "PEE-509",
            testName: "موسیقی",
            testCategory: "آزمون عملی",
            testType: "آزمون تکوینی",
            class: "9",
            startDate: "15 دی 1405",
            endDate: "15 دی 1405",
            status: "برنامه‌ریزی‌ شده"
        }
    ]
};

class TableManager {
    constructor(options) {
        this.tableData = options.data || [];
        this.originalData = [...this.tableData]; // Keep a copy of original data
        this.totalResults = options.totalResults || this.tableData.length;
        this.tableContainer = options.tableContainer;
        this.pageSize = options.pageSize || 10;
        this.currentPage = options.currentPage || 1;
        this.paginationContainer = options.paginationContainer;
        this.resultsInfoContainer = options.resultsInfoContainer;
        this.addModalId = options.addModalId || 'addExamScheduleModal';
        this.editModalId = options.editModalId || 'ExamScheduleModal';
        this.deleteModalId = options.deleteModalId || 'deleteModal';

        // Add sort state properties
        this.sortColumn = null;
        this.sortDirection = null;

        this.statusClasses = {
            "تازه": "bg-info-subtle border border-info-subtle text-info",
            "برنامه‌ریزی‌ شده": "bg-warning-subtle border border-warning-subtle text-warning",
            "تکمیل شده": "bg-success-subtle border border-success-subtle text-success"
        };

        // Form select options
        this.testCategoryOptions = ["آزمون نهایی", "آزمون عملی", "آزمون میان ترم", "آزمون پایان ترم"];
        this.testTypeOptions = ["عمومی", "آزمون تکوینی", "جمع‌بندی", "آنلاین"];
        this.classOptions = ["9", "10", "11", "12"];
        this.statusOptions = ["تازه", "برنامه‌ریزی‌ شده", "تکمیل شده"];

        this.init();
    }

    init() {
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
        this.setupFormSelects();
        this.attachEventListeners();
    }

    renderTable() {
        if (!this.tableContainer) return;

        // Calculate start and end indices based on current page
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = Math.min(startIndex + this.pageSize, this.tableData.length);
        const pageData = this.tableData.slice(startIndex, endIndex);

        // Get current sort state if any
        const sortColumn = this.sortColumn || '';
        const sortDirection = this.sortDirection || '';

        const tableHtml = `
        <div class="table-card table-responsive">
          <table class="table table-borderless text-nowrap mb-0">
            <thead>
              <tr class="bg-light border-bottom">
                <th class="fw-medium text-muted sortable" data-sort="id">
                  شناسه ${sortColumn === 'id' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="fw-medium text-muted sortable" data-sort="testName">
                  نام آزمون ${sortColumn === 'testName' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="fw-medium text-muted sortable" data-sort="testCategory">
                  دسته‌بندی آزمون ${sortColumn === 'testCategory' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="fw-medium text-muted sortable" data-sort="testType">
                  نوع آزمون ${sortColumn === 'testType' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="fw-medium text-muted sortable" data-sort="class">
                  کلاس ${sortColumn === 'class' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="fw-medium text-muted sortable" data-sort="startDate">
                  تاریخ شروع ${sortColumn === 'startDate' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="fw-medium text-muted sortable" data-sort="endDate">
                  تاریخ پایان ${sortColumn === 'endDate' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="fw-medium text-muted sortable" data-sort="status">
                  وضعیت ${sortColumn === 'status' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="fw-medium text-muted">عملیات</th>
              </tr>
            </thead>
            <tbody>
              ${pageData.length > 0
                ? pageData.map(item => this.renderTableRow(item)).join('')
                : `<tr><td colspan="9" class="text-center">هیچ داده‌ای یافت نشد</td></tr>`}
            </tbody>
          </table>
        </div>
        `;

        this.tableContainer.innerHTML = tableHtml;

        // Attach event listeners for sorting
        const sortableHeaders = this.tableContainer.querySelectorAll('th.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-sort');
                this.handleSort(column);
            });
        });

        // Attach edit and delete button event listeners
        this.attachRowActionListeners();
    }

    renderTableRow(rowData) {
        return `
        <tr data-id="${rowData.id}">
          <td>${rowData.id}</td>
          <td>${rowData.testName}</td>
          <td>${rowData.testCategory}</td>
          <td>${rowData.testType}</td>
          <td>${rowData.class}</td>
          <td>${rowData.startDate}</td>
          <td>${rowData.endDate}</td>
          <td><span class="badge ${this.statusClasses[rowData.status] || ''}">${rowData.status}</span></td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <button class="btn btn-sub-primary size-8 btn-icon edit-btn" data-id="${rowData.id}">
                <i class="ri-pencil-line"></i>
              </button>
              <button class="btn btn-sub-danger size-8 btn-icon delete-btn" data-id="${rowData.id}">
                <i class="ri-delete-bin-line"></i>
              </button>
            </div>
          </td>
        </tr>
        `;
    }

    // New method to handle sorting when a column header is clicked
    handleSort(column) {
        // If clicking the same column, toggle sort direction
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // If clicking a new column, default to ascending sort
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        // Perform the sort
        this.sort(column, this.sortDirection);
    }

    // Enhanced sort method to handle different data types properly
    sort(columnKey, direction = 'asc') {
        this.sortColumn = columnKey;
        this.sortDirection = direction;

        this.tableData.sort((a, b) => {
            let valueA = a[columnKey];
            let valueB = b[columnKey];

            // Special handling for dates
            if (columnKey === 'startDate' || columnKey === 'endDate') {
                // Parse dates for proper comparison
                valueA = this.parseDateString(valueA);
                valueB = this.parseDateString(valueB);
            }

            // Special handling for numeric values that might be stored as strings
            else if (columnKey === 'class') {
                valueA = parseInt(valueA, 10);
                valueB = parseInt(valueB, 10);
            }

            // Comparison logic
            if (direction === 'asc') {
                if (valueA < valueB) return -1;
                if (valueA > valueB) return 1;
                return 0;
            } else {
                if (valueA > valueB) return -1;
                if (valueA < valueB) return 1;
                return 0;
            }
        });

        this.renderTable();
    }

    // Helper method to parse date strings in the format used in the data
    parseDateString(dateStr) {
        // Format is like "12 Jan, 2024"
        const parts = dateStr.split(' ');
        const day = parseInt(parts[0], 10);
        const month = this.getMonthNumber(parts[1].replace(',', ''));
        const year = parseInt(parts[2], 10);

        return new Date(year, month, day);
    }

    // Helper to convert month name to number
    getMonthNumber(monthName) {
        const months = {
            'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
            'Jul': 6, 'Aug': 7, 'Sept': 8, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
        };
        return months[monthName] || 0;
    }

    renderPagination() {
        if (!this.paginationContainer) return;

        const totalPages = Math.max(1, Math.ceil(this.totalResults / this.pageSize));

        let paginationHtml = `
        <nav aria-label="Page navigation example">
          <ul class="pagination justify-content-center justify-content-md-end mb-0">
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
              <a class="page-link" href="#" data-page="${this.currentPage - 1}">
                <i data-lucide="chevron-right" class="size-4"></i> قبلی
              </a>
            </li>
      `;

        // Logic for showing page numbers with ellipsis for many pages
        const maxVisiblePages = 5;
        let startPage = 1;
        let endPage = totalPages;

        if (totalPages > maxVisiblePages) {
            // Always show current page and some pages before and after
            const pagesBeforeAndAfter = Math.floor((maxVisiblePages - 1) / 2);

            startPage = Math.max(1, this.currentPage - pagesBeforeAndAfter);
            endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

            // Adjust if we're near the end
            if (endPage - startPage + 1 < maxVisiblePages) {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }
        }

        // Add first page and ellipsis if needed
        if (startPage > 1) {
            paginationHtml += `
          <li class="page-item">
            <a class="page-link" href="#" data-page="1">1</a>
          </li>
        `;

            if (startPage > 2) {
                paginationHtml += `
            <li class="page-item disabled">
              <a class="page-link" href="#">...</a>
            </li>
          `;
            }
        }

        // Add visible page numbers
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
          <li class="page-item ${i === this.currentPage ? 'active' : ''}">
            <a class="page-link" href="#" data-page="${i}">${i}</a>
          </li>
        `;
        }

        // Add last page and ellipsis if needed
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHtml += `
            <li class="page-item disabled">
              <a class="page-link" href="#">...</a>
            </li>
          `;
            }

            paginationHtml += `
          <li class="page-item">
            <a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a>
          </li>
        `;
        }

        paginationHtml += `
          <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${this.currentPage + 1}">
              بعدی <i data-lucide="chevron-left" class="size-4"></i>
            </a>
          </li>
        </ul>
      </nav>
      `;

        this.paginationContainer.innerHTML = paginationHtml;

        createIcons({ icons });

    }

    updateResultsInfo() {
        if (!this.resultsInfoContainer) return;

        // Handle case with no results
        if (this.totalResults === 0) {
            this.resultsInfoContainer.innerHTML = `
          <p class="text-muted text-center text-md-start mb-0">
            هیچ نتیجه‌ای یافت نشد
          </p>
        `;
            return;
        }

        const startItem = (this.currentPage - 1) * this.pageSize + 1;
        const endItem = Math.min(startItem + this.pageSize - 1, this.totalResults);

        this.resultsInfoContainer.innerHTML = `
        <p class="text-muted text-center text-md-start mb-0">
          نمایش <b class="me-1">${startItem}-${endItem}</b> از <b class="ms-1">${this.totalResults}</b> نتیجه
        </p>
      `;
    }

    setupFormSelects() {
        // Test Category Select
        this.setupSelect('testCategorySelect', this.testCategoryOptions);

        // Test Type Select
        this.setupSelect('testTypeSelect', this.testTypeOptions);

        // Class Select
        this.setupSelect('classSelect', this.classOptions);

        // Status Select
        this.setupSelect('statusSelect', this.statusOptions);
    }

    setupSelect(elementId, options) {
        const element = document.getElementById(elementId);
        if (!element) return;

        let selectHtml = `<select class="form-select" id="${elementId}-dropdown" name="${elementId}">`;
        options.forEach(option => {
            selectHtml += `<option value="${option}">${option}</option>`;
        });
        selectHtml += `</select>`;

        element.innerHTML = selectHtml;
    }

    attachEventListeners() {
        // Pagination clicks
        if (this.paginationContainer) {
            this.paginationContainer.addEventListener('click', (e) => {
                e.preventDefault();

                const pageLink = e.target.closest('[data-page]');
                if (!pageLink) return;

                const page = parseInt(pageLink.dataset.page, 10);
                if (isNaN(page) || page < 1 || page > Math.ceil(this.totalResults / this.pageSize)) return;

                this.goToPage(page);
            });
        }

        // Add new exam form submission
        const addExamForm = document.querySelector(`#${this.addModalId} form`);
        if (addExamForm) {
            addExamForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addExam(e.target);
            });
        } else {
            console.error(`Form not found in modal #${this.addModalId}`);
        }

        // Reset form when add modal is opened
        const addModal = document.getElementById(this.addModalId);
        if (addModal) {
            addModal.addEventListener('show.bs.modal', () => {
                const form = addModal.querySelector('form');
                if (form) form.reset();
            });
        }

        // Handle edit modal initialization
        const editModal = document.getElementById(this.editModalId);
        if (editModal) {
            editModal.addEventListener('show.bs.modal', (e) => {
                const button = e.relatedTarget;
                const id = button.getAttribute('data-id');
                this.populateEditForm(id);
            });
        }

        // Handle edit form submission
        const editForm = editModal ? editModal.querySelector('form') : null;
        if (editForm) {
            editForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.updateExam(e.target);
            });
        }

        // Handle delete confirmation
        const deleteModal = document.getElementById(this.deleteModalId);
        if (deleteModal) {
            deleteModal.addEventListener('show.bs.modal', (e) => {
                const button = e.relatedTarget;
                const id = button.getAttribute('data-id');

                // Set the ID on the delete button for reference
                const deleteButton = deleteModal.querySelector('.btn-danger');
                if (deleteButton) {
                    deleteButton.setAttribute('data-id', id);
                }
            });

            // Handle actual delete action
            const deleteButton = deleteModal.querySelector('.btn-danger');
            if (deleteButton) {
                deleteButton.addEventListener('click', (e) => {
                    const id = e.target.getAttribute('data-id');
                    this.deleteExam(id);
                });
            }
        }
    }

    attachRowActionListeners() {
        // Attach edit button event listeners
        const editButtons = this.tableContainer.querySelectorAll('.edit-btn');
        editButtons.forEach(button => {
            button.addEventListener('click', () => {
                const id = button.getAttribute('data-id');
                // Open the edit modal and pass the ID
                const editModal = new window.bootstrap.Modal(document.getElementById(this.editModalId));
                button.setAttribute('data-bs-toggle', 'modal');
                button.setAttribute('data-bs-target', `#${this.editModalId}`);
                this.populateEditForm(id);
                editModal.show();
            });
        });

        // Attach delete button event listeners
        const deleteButtons = this.tableContainer.querySelectorAll('.delete-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const id = button.getAttribute('data-id');

                // Open the delete confirmation modal
                const deleteModal = document.getElementById(this.deleteModalId);
                if (deleteModal) {
                    // Set the ID directly on the delete confirmation button
                    const confirmDeleteButton = deleteModal.querySelector('.btn-danger');
                    if (confirmDeleteButton) {
                        confirmDeleteButton.setAttribute('data-id', id);
                    }

                    // Show the modal
                    const bsDeleteModal = new window.bootstrap.Modal(deleteModal);
                    bsDeleteModal.show();
                }
            });
        });
    }

    goToPage(page) {
        this.currentPage = page;
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    filter(filterFn) {
        const filteredData = this.originalData.filter(filterFn);
        this.tableData = filteredData;
        this.totalResults = filteredData.length;
        this.currentPage = 1;
        this.init();
    }

    sort(columnKey, direction = 'asc') {
        this.tableData.sort((a, b) => {
            const valueA = a[columnKey];
            const valueB = b[columnKey];

            if (direction === 'asc') {
                return valueA > valueB ? 1 : -1;
            } else {
                return valueA < valueB ? 1 : -1;
            }
        });

        this.renderTable();
    }

    reset() {
        this.tableData = [...this.originalData];
        this.totalResults = this.tableData.length;
        this.currentPage = 1;
        this.init();
    }

    // CRUD Operations

    addExam(form) {
        // Get form data
        const formData = new FormData(form);

        // For select fields, ensure we get values from the actual select elements
        const testCategorySelect = document.getElementById('testCategorySelect-dropdown');
        const testTypeSelect = document.getElementById('testTypeSelect-dropdown');
        const classSelect = document.getElementById('classSelect-dropdown');
        const statusSelect = document.getElementById('statusSelect-dropdown');

        const newExam = {
            id: this.generateNewId(),
            testName: formData.get('testName'),
            testCategory: testCategorySelect ? testCategorySelect.value : 'آزمون نهایی',
            testType: testTypeSelect ? testTypeSelect.value : 'عمومی',
            class: classSelect ? classSelect.value : '12',
            startDate: dueDateInput.value,
            endDate: endDateInput.value,
            status: statusSelect ? statusSelect.value : 'تازه'
        };

        // Add to data
        this.tableData.unshift(newExam);
        this.originalData.unshift(newExam);
        this.totalResults++;

        // Reset and update table
        form.reset();
        this.currentPage = 1; // Go to first page to see the new entry
        this.init();

        // Close modal
        const modal = window.bootstrap.Modal.getInstance(document.getElementById(this.addModalId));
        if (modal) modal.hide();
    }

    populateEditForm(id) {
        const exam = this.tableData.find(item => item.id === id);
        if (!exam) return;

        const form = document.querySelector(`#${this.editModalId} form`);
        if (!form) return;

        // Set hidden ID field or create one if it doesn't exist
        let idField = form.querySelector('input[name="examId"]');
        if (!idField) {
            idField = document.createElement('input');
            idField.type = 'hidden';
            idField.name = 'examId';
            form.appendChild(idField);
        }
        idField.value = exam.id;

        // Populate form fields
        const testNameInput = form.querySelector('input[name="testName"]');
        if (testNameInput) testNameInput.value = exam.testName;

        // Select dropdowns
        this.setSelectValue(`testCategorySelect-dropdown`, exam.testCategory);
        this.setSelectValue(`testTypeSelect-dropdown`, exam.testType);
        this.setSelectValue(`classSelect-dropdown`, exam.class);
        this.setSelectValue(`statusSelect-dropdown`, exam.status);

        // Date fields
        const startDateInput = form.querySelector('input[name="startDate"]');
        if (startDateInput) {
            // Set the date
                startDateInput.value = exam.startDate;
        }

        const endDateInput = form.querySelector('input[name="endDate"]');
        if (endDateInput) {
            // Set the date
                endDateInput.value = exam.endDate;
        }
    }

    setSelectValue(selectId, value) {
        const select = document.getElementById(selectId);
        if (select && select.tagName === 'SELECT') {
            select.value = value;
        }
    }

    updateExam(form) {
        const formData = new FormData(form);
        const id = formData.get('examId');

        // Find the exam to update
        const examIndex = this.tableData.findIndex(item => item.id === id);
        if (examIndex === -1) return;

        const updatedExam = {
            id: id,
            testName: formData.get('testName'),
            testCategory: formData.get('testCategorySelect') || this.tableData[examIndex].testCategory,
            testType: formData.get('testTypeSelect') || this.tableData[examIndex].testType,
            class: formData.get('classSelect') || this.tableData[examIndex].class,
            startDate: formData.get('startDate') || this.tableData[examIndex].startDate,
            endDate: formData.get('endDate') || this.tableData[examIndex].endDate,
            status: formData.get('statusSelect') || this.tableData[examIndex].status
        };

        // Update in both data sets
        this.tableData[examIndex] = updatedExam;

        const originalIndex = this.originalData.findIndex(item => item.id === id);
        if (originalIndex !== -1) {
            this.originalData[originalIndex] = updatedExam;
        }

        // Update table
        this.renderTable();

        // Close modal
        const modal = window.bootstrap.Modal.getInstance(document.getElementById(this.editModalId));
        if (modal) modal.hide();
    }

    deleteExam(id) {
        // Remove from data
        this.tableData = this.tableData.filter(item => item.id !== id);
        this.originalData = this.originalData.filter(item => item.id !== id);
        this.totalResults--;

        // If current page has no more items and it's not the first page, go to previous page
        const totalPages = Math.max(1, Math.ceil(this.totalResults / this.pageSize));
        if (this.currentPage > totalPages) {
            this.currentPage = Math.max(1, totalPages);
        }

        // Update table
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();

        // Close modal
        const modal = window.bootstrap.Modal.getInstance(document.getElementById(this.deleteModalId));
        if (modal) modal.hide();
    }


    // Helper methods

    generateNewId() {
        // Find the highest current ID number
        const ids = this.originalData.map(item => {
            // Assuming IDs are in format PEE-XXX where XXX is a number
            const match = item.id.match(/PEE-(\d+)/);
            return match ? parseInt(match[1], 10) : 0;
        });

        const highestId = Math.max(...ids, 0);
        return `PEE-${(highestId + 1).toString().padStart(3, '0')}`;
    }

    formatDate(date) {
        const months = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'
        ];

        const day = date.getDate();
        const month = months[date.getMonth()];
        const year = date.getFullYear();

        return `${day} ${month}, ${year}`;
    }
}
const dueDateInput = document.getElementById('dueDateInput');
const endDateInput = document.getElementById('endDateInput');  // Change the ID here


document.addEventListener('DOMContentLoaded', function () {
    // Initialize the TableManager
    const tableManager = new TableManager({
        data: examScheduleData.data,
        totalResults: examScheduleData.totalResults,
        pageSize: examScheduleData.pageSize,
        currentPage: examScheduleData.currentPage,
        tableContainer: document.getElementById('exam-table-container'),
        paginationContainer: document.getElementById('pagination-container'),
        resultsInfoContainer: document.getElementById('results-info-container')
    });

    const filterByStatus = document.getElementById('filter-by-status');
    if (filterByStatus) {
        filterByStatus.addEventListener('change', function (e) {
            const status = e.target.value;

            if (status === 'all') {
                tableManager.reset(examScheduleData.data);
            } else {
                tableManager.filter(item => item.status === status);
            }
        });
    }

    // Same for the sort-by-date element
    const sortByDate = document.getElementById('sort-by-date');
    if (sortByDate) {
        sortByDate.addEventListener('click', function () {
            const direction = this.dataset.direction || 'asc';
            tableManager.sort('startDate', direction);

            // Toggle direction for next click
            this.dataset.direction = direction === 'asc' ? 'desc' : 'asc';
        });
    }
});