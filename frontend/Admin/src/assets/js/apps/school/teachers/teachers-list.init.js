
import tableData from '../../../../json/apps/school/teachers.json';
import { createIcons, icons } from 'lucide';



//title Select
VirtualSelect.init({
    ele: "#titleSelect",
    options: [
        { label: "معلم", value: "Teacher" },
        { label: "استاد", value: "Professor" },
        { label: "دستیار", value: "Assistant" },
        { label: "مدرس", value: "Lecturer" },
        { label: "مربی", value: "Instructor" },
        { label: "مدرس ارشد", value: "Senior Lecturer" },
        { label: "دانشیار", value: "Associate Professor" },
        { label: "استادیار", value: "Assistant Professor" }
    ],
});

// Mapping
const TITLE_EN_TO_FA = {
    'Teacher': 'معلم',
    'Professor': 'استاد',
    'Assistant': 'دستیار',
    'Lecturer': 'مدرس',
    'Instructor': 'مربی',
    'Senior Lecturer': 'مدرس ارشد',
    'Associate Professor': 'دانشیار',
    'Assistant Professor': 'استادیار'
};

/**
 * TableManager - A reusable class for managing data tables with pagination, search, sorting, and deletion
 */
class TableManager {
    /**
     * @param {Object} config - Configuration object
     * @param {string} config.tableId - ID of the table element
     * @param {Array} config.data - Array of data objects
     * @param {Function} config.formatData - Function to format data before display
     * @param {Function} config.createRow - Function that returns HTML for a row
     * @param {number} config.itemsPerPage - Number of items per page
     * @param {Object} config.selectors - DOM element selectors
     * @param {Object} config.sortConfig - Sorting configuration
     * @param {Array} config.sortConfig.columns - Array of sortable column definitions
     * @param {Object} config.editConfig - Edit configuration
     * @param {Array} config.editConfig.fields - Array of editable field definitions
     * @param {Function} config.editConfig.onEdit - Callback function when edit is confirmed
     */
    constructor(config) {
        // Generate unique instance ID
        this.instanceId = 'tm_' + Math.random().toString(36).substring(2, 9);

        // Configuration
        this.tableId = config.tableId;
        this.rawData = config.data;
        this.formatData = config.formatData || (data => data);
        this.createRow = config.createRow;
        this.itemsPerPage = config.itemsPerPage || 10;
        this.sortableColumns = config.sortConfig?.columns || [];
        this.editableFields = config.editConfig?.fields || [];
        this.onEditCallback = config.editConfig?.onEdit;

        // Initialize data
        this.tableData = this.formatData([...this.rawData]);
        this.filteredData = this.tableData;
        this.currentPage = 1;
        this.deleteRecordId = null;
        this.editRecordId = null;
        this.currentRecord = null;

        // Sort state
        this.currentSortColumn = null;
        this.currentSortDirection = 'asc';

        // DOM elements
        this.table = document.getElementById(this.tableId);
        if (!this.table) {
            console.error(`Table with ID ${this.tableId} not found`);
            return;
        }

        this.tableBody = this.table.querySelector(config.selectors.tableBody || 'tbody');
        this.tableHeader = this.table.querySelector(config.selectors.tableHeader || 'thead');
        this.paginationElement = document.getElementById(config.selectors.pagination) || this.table.querySelector('.pagination');
        this.showingResults = document.getElementById(config.selectors.showingResults) || this.table.querySelector('.showing-results');
        this.searchInput = document.getElementById(config.selectors.searchInput);
        this.deleteButton = document.getElementById(config.selectors.deleteButton);
        this.editButton = document.getElementById(config.selectors.editButton);
        this.editForm = document.getElementById(config.selectors.editForm);

        // Create edit modal with unique IDs
        this.createEditModal();

        // Initialize the table
        this.init();
    }

    /**
     * Initialize the table and attach event listeners
     */
    init() {
        this.setupSortableColumns();
        this.displayData(this.currentPage);
        this.setupPagination();
        this.displayResults();
        this.setupEventListeners();
    }

    /**
     * Create edit modal if it doesn't exist
     */
    createEditModal() {
        // Generate unique IDs for modal elements
        this.modalId = `editModal_${this.instanceId}`;
        this.modalLabelId = `editModalLabel_${this.instanceId}`;
        this.editFormId = `editRecordForm_${this.instanceId}`;
        this.editFormFieldsId = `editFormFields_${this.instanceId}`;
        this.editRecordIdField = `editRecordId_${this.instanceId}`;
        this.saveEditButtonId = `saveEditButton_${this.instanceId}`;

        // Create modal template with unique IDs
        const modalTemplate = `
        <div class="modal fade" id="${this.modalId}" tabindex="-1" aria-labelledby="${this.modalLabelId}" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="${this.modalLabelId}">ویرایش رکورد</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="${this.editFormId}">
                            <div id="${this.editFormFieldsId}"></div>
                            <input type="hidden" id="${this.editRecordIdField}">
                        </form>
                    </div>
                    <div class="modal-footer d-flex justify-content-end p-5">
                        <button type="button" class="btn btn-active-danger" data-bs-dismiss="modal">انصراف</button>
                        <button type="button" class="btn btn-primary ms-3" id="${this.saveEditButtonId}">آپدیت تغییرات</button>
                    </div>
                </div>
            </div>
        </div>`;

        // Check if modal already exists
        if (document.getElementById(this.modalId)) return;

        // Add modal to body
        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalTemplate;

            document.body.appendChild(modalDiv);
        // Set up event listener for save button
        document.getElementById(this.saveEditButtonId).addEventListener('click', this.handleEditSave.bind(this));
    }

    /**
     * Set up sortable column headers
     */
    setupSortableColumns() {
        if (!this.tableHeader || this.sortableColumns.length === 0) return;

        const headerRow = this.tableHeader.querySelector('tr');
        if (!headerRow) return;

        const headerCells = headerRow.querySelectorAll('th');

        this.sortableColumns.forEach(column => {
            const cellIndex = column.index;
            if (cellIndex >= 0 && cellIndex < headerCells.length) {
                const cell = headerCells[cellIndex];

                // Add sort indicator and styling
                cell.classList.add('sortable');
                const originalContent = cell.innerHTML;
                cell.innerHTML = `
                    <div class="d-flex align-items-center gap-2">
                        <span>${originalContent}</span>
                        <div class="sort-icons">
                            <i class="ri-arrow-up-s-line sort-icon sort-up"></i>
                            <i class="ri-arrow-down-s-line sort-icon sort-down"></i>
                        </div>
                    </div>
                `;

                // Add click event listener
                cell.addEventListener('click', () => this.handleSort(column));

                // Store reference to the cell
                column.element = cell;
            }
        });
    }

    /**
     * Handle column sorting
     * @param {Object} column - Column configuration object
     */
    handleSort(column) {
        // Toggle sort direction if clicking the same column
        if (this.currentSortColumn === column.key) {
            this.currentSortDirection = this.currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSortColumn = column.key;
            this.currentSortDirection = 'asc';
        }

        // Update sort UI indicators
        this.updateSortIndicators(column);

        // Sort the data
        this.filteredData.sort((a, b) => {
            let aValue = this.getNestedProperty(a, column.key);
            let bValue = this.getNestedProperty(b, column.key);

            // Apply custom sort function if provided
            if (column.sortFn) {
                return column.sortFn(aValue, bValue, this.currentSortDirection);
            }

            // Default sorting logic
            if (typeof aValue === 'string') {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }

            if (aValue === bValue) return 0;

            const comparison = aValue > bValue ? 1 : -1;
            return this.currentSortDirection === 'asc' ? comparison : -comparison;
        });

        // Refresh display
        this.displayData(this.currentPage);
    }

    /**
     * Get a nested property value using dot notation
     * @param {Object} obj - The object to get property from
     * @param {string} path - Property path (e.g., 'user.address.city')
     * @returns {*} Property value
     */
    getNestedProperty(obj, path) {
        if (!path) return obj;

        const parts = path.split('.');
        let value = obj;

        for (let i = 0; i < parts.length; i++) {
            if (value == null) return undefined;
            value = value[parts[i]];
        }

        return value;
    }

    /**
     * Update sort indicators in the UI
     * @param {Object} activeColumn - Currently sorted column
     */
    updateSortIndicators(activeColumn) {
        // Reset all columns
        this.sortableColumns.forEach(column => {
            if (column.element) {
                column.element.classList.remove('sort-asc', 'sort-desc');
            }
        });

        // Mark active column
        if (activeColumn.element) {
            activeColumn.element.classList.add(
                this.currentSortDirection === 'asc' ? 'sort-asc' : 'sort-desc'
            );
        }
    }

    /**
     * Display data for the current page
     * @param {number} page - Current page number
     */
    displayData(page) {
        const startIndex = (page - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const paginatedData = this.filteredData.slice(startIndex, endIndex);

        this.tableBody.innerHTML = '';

        if (paginatedData.length === 0) {
            // No data found, display the "No matching records found" message
            const noDataRow = document.createElement('tr');
            noDataRow.innerHTML = `
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
                        <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                    </div>
                </td>
            `;
            this.tableBody.appendChild(noDataRow);
        } else {
            paginatedData.forEach(item => {
                const row = document.createElement('tr');
                row.setAttribute('data-row-id', item.id);
                row.innerHTML = this.createRow(item);
                this.tableBody.appendChild(row);
            });
        }

        this.updateActions();
    }


    /**
     * Initialize the add teacher modal with
     */
    initAddTeacherModal() {
        

        // Create a standard select dropdown for title instead of using TomSelect
        const titleSelectContainer = document.getElementById('titleSelect');
        if (titleSelectContainer) {
            // Create select element
            const selectElement = document.createElement('select');
            selectElement.className = 'form-select';
            selectElement.id = 'titleSelectDropdown';
            selectElement.name = 'title';

            // Add options
            const titles = [
                { value: '', title: 'انتخاب عنوان' },
                { value: 'Teacher', title: 'معلم' },
                { value: 'Professor', title: 'استاد' },
                { value: 'Assistant', title: 'دستیار' },
                { value: 'Lecturer', title: 'مدرس' },
                { value: 'Instructor', title: 'مربی' },
                { value: 'Senior Lecturer', title: 'مدرس ارشد' },
                { value: 'Associate Professor', title: 'دانشیار' },
                { value: 'Assistant Professor', title: 'استادیار' }
            ];

            titles.forEach(title => {
                const option = document.createElement('option');
                option.value = title.value;
                option.textContent = title.title;
                selectElement.appendChild(option);
            });

            // Add to container
            titleSelectContainer.innerHTML = '';
            titleSelectContainer.appendChild(selectElement);
        }

        // Set up form submission handling
        const addTeacherForm = document.querySelector('#addTeacherModal form');
        if (addTeacherForm) {
            addTeacherForm.addEventListener('submit', this.handleAddTeacher.bind(this));
        }
    }

    /**
     * Handle adding a new teacher
     * @param {Event} e - Form submit event
     */
    handleAddTeacher(e) {
        e.preventDefault();

        // Get form values
        const form = e.target;
        const titleSelect = document.querySelector('#titleSelectDropdown');
        const titleValue = titleSelect ? titleSelect.value : '';

        // Validate title (required field)
        if (!titleValue) {
            document.getElementById('titleError').style.display = 'block';
            return;
        } else {
            document.getElementById('titleError').style.display = 'none';
        }

        // Get other form fields
        const name = form.querySelector('[name="teacherName"]').value;
        const email = form.querySelector('[name="email"]').value;
        const phone = form.querySelector('[name="phone"]').value;
        const salary = form.querySelector('[name="salary"]').value;
        const experience = form.querySelector('[name="experience"]').value;
        const joiningDate = document.getElementById('joiningDateSelect').value;

        // Generate initials for avatar
        const initials = this.getInitials(name);
        const avatarBackground = this.getRandomColor();

        // Create new teacher object
        const newTeacher = {
            id: this.generateUniqueId(),
            name,
            email,
            phone,
            salary:  parseFloat(salary).toLocaleString() +' تومان' ,
            experience: experience + ' سال سابقه',
            title: titleValue,
            joiningDate: joiningDate,
            // Store initials and background color for avatar
            initials: initials,
            avatarColor: avatarBackground,
            hasCustomAvatar: true
        };

        // Add new teacher to data arrays
        this.rawData.unshift(newTeacher);
        this.tableData = this.formatData([...this.rawData]);
        this.filteredData = this.tableData;

        // Refresh the display
        this.displayData(this.currentPage);
        this.setupPagination();
        this.updatePaginationUI();

        // Hide modal and reset form
        const addModal = window.bootstrap.Modal.getInstance(document.getElementById('addTeacherModal'));
        if (addModal) {
            addModal.hide();
            form.reset();
            if (titleSelect) {
                titleSelect.selectedIndex = 0;
            }
        }
    }

    /**
     * Get initials from a name (first 2 letters)
     * @param {string} name - Full name
     * @returns {string} Initials (2 letters)
     */
    getInitials(name) {
        if (!name) return 'NA';

        const nameParts = name.trim().split(' ');
        if (nameParts.length === 1) {
            // If only one name, take first two letters
            return (nameParts[0].substring(0, 2)).toUpperCase();
        } else {
            // If multiple names, take first letter of first and last names
            return (nameParts[0].charAt(0) + nameParts[nameParts.length - 1].charAt(0)).toUpperCase();
        }
    }

    /**
     * Get a random background color for avatar
     * @returns {string} CSS color value
     */
    getRandomColor() {
        const colors = [
            'bg-primary', 'bg-secondary', 'bg-success', 'bg-danger',
            'bg-warning', 'bg-info', 'bg-dark'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    /**
     * Generate a unique ID for new records
     * @returns {string} Unique ID
     */
    generateUniqueId() {
        // Find the highest existing ID and increment by 1
        const maxId = Math.max(...this.rawData.map(item => {
            const numericPart = item.id.replace(/\D/g, '');
            return parseInt(numericPart);
        })
    );

    return `PET-${maxId + 1}`;
    }

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Search functionality
        if (this.searchInput) {
            this.searchInput.addEventListener('keyup', this.handleSearch.bind(this));
        }

        // Delete functionality
        if (this.deleteButton) {
            this.deleteButton.addEventListener('click', this.handleDelete.bind(this));
        }

        // Initialize Add Teacher modal
        this.initAddTeacherModal();
    }

    /**
     * Handle search input
     * @param {Event} e - Keyup event
     */
    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();
        this.filteredData = this.tableData.filter(item => {
            return Object.values(item).some(value =>
                value && value.toString().toLowerCase().includes(searchTerm)
            );
        });

        // Reapply current sort if active
        if (this.currentSortColumn) {
            const activeColumn = this.sortableColumns.find(col => col.key === this.currentSortColumn);
            if (activeColumn) {
                this.handleSort(activeColumn);
            }
        }

        this.currentPage = 1; // Reset to first page
        this.displayData(this.currentPage);
        this.setupPagination(); // Rebuild pagination
        this.updatePaginationUI();
    }

    /**
     * Handle record deletion
     */
    handleDelete() {
        if (!this.deleteRecordId) return;

        // Filter out the deleted item from both data arrays
        this.tableData = this.tableData.filter(item => item.id !== this.deleteRecordId);
        this.filteredData = this.filteredData.filter(item => item.id !== this.deleteRecordId);

        // Adjust current page if necessary
        const maxPage = Math.max(1, Math.ceil(this.filteredData.length / this.itemsPerPage));
        if (this.currentPage > maxPage) {
            this.currentPage = maxPage;
        }

        // Refresh the display
        this.displayData(this.currentPage);
        this.setupPagination(); // Rebuild pagination
        this.updatePaginationUI();

        // Reset delete ID
        this.deleteRecordId = null;
    }

    /**
     * Handle edit button click
     * @param {string} recordId - ID of the record to edit
     */
    handleEdit(recordId) {
        this.editRecordId = recordId;
        this.currentRecord = this.tableData.find(item => item.id === recordId);

        if (!this.currentRecord) return;

        // Update hidden field
        document.getElementById(this.editRecordIdField).value = recordId;

        // Generate form fields based on editableFields configuration
        const formFieldsContainer = document.getElementById(this.editFormFieldsId);
        formFieldsContainer.innerHTML = '';

        this.editableFields.forEach(field => {
            const fieldValue = this.getNestedProperty(this.currentRecord, field.key);
            let fieldHtml = '';

            // Create different input types based on field type
            switch (field.type) {
                case 'select':
                    const options = field.options.map(option =>
                        `<option value="${option.value}" ${fieldValue === option.value ? 'selected' : ''}>${option.label}</option>`
                    ).join('');

                    fieldHtml = `
                    <div class="mb-3">
                        <label for="${field.key}_${this.instanceId}" class="form-label">${field.label}</label>
                        <select class="form-select" id="${field.key}_${this.instanceId}" name="${field.key}">
                            ${options}
                        </select>
                    </div>`;
                    break;

                case 'textarea':
                    fieldHtml = `
                    <div class="mb-3">
                        <label for="${field.key}_${this.instanceId}" class="form-label">${field.label}</label>
                        <textarea class="form-control" id="${field.key}_${this.instanceId}" name="${field.key}" rows="3">${fieldValue || ''}</textarea>
                    </div>`;
                    break;

                case 'date':
                    //❗ If You Want Format Date for Input 
                    // const date = new Date(fieldValue);
                    // const day = date.getDate().toString().padStart(2, '0');
                    // const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Months are 0-indexed
                    // const year = date.getFullYear();
                    // const dateValue = `${year}-${month}-${day}`;

                    fieldHtml = `
                    <div class="mb-3">
                        <label for="${field.key}_${this.instanceId}" class="form-label">${field.label}</label>
                        <input type="text" data-type="date" class="form-control" 
                        id="${field.key}_${this.instanceId}" 
                        name="${field.key}" 
                        value="${fieldValue || ''}">
                    </div>`;

                    break;

                case 'number':
                    fieldHtml = `
                    <div class="mb-3">
                        <label for="${field.key}_${this.instanceId}" class="form-label">${field.label}</label>
                        <input type="number" class="form-control" id="${field.key}_${this.instanceId}" name="${field.key}" value="${fieldValue || ''}">
                    </div>`;
                    break;

                default: // text input as default
                    fieldHtml = `
                    <div class="mb-3">
                        <label for="${field.key}_${this.instanceId}" class="form-label">${field.label}</label>
                        <input type="text" class="form-control" id="${field.key}_${this.instanceId}" name="${field.key}" value="${fieldValue || ''}">
                    </div>`;
            }

            formFieldsContainer.innerHTML += fieldHtml;
        });

        // Show the modal
        const editModal = new window.bootstrap.Modal(document.getElementById(this.modalId), { backdrop: 'static' });
        editModal.show();
    }

    /**
     * Handle edit save button click
     */
    handleEditSave() {
        if (!this.editRecordId || !this.currentRecord) return;

        // Get form values
        const updatedData = {};
        this.editableFields.forEach(field => {
            const input = document.getElementById(`${field.key}_${this.instanceId}`);
            if (!input) return;

            let value = input.value;

            // Type conversions based on field type
            if (field.type === 'number') {
                value = parseFloat(value);
            } else if (field.type === 'date' || field.dataType === 'date') {
                // Convert to date object if needed
                const parts = value.split('/');
                const backToDate = new Date(parts[2], parts[1] - 1, parts[0]);
                const options = { year: 'numeric', month: 'long', day: 'numeric' };
                const originalFormat = backToDate.toLocaleDateString('en-US', options);
                value = originalFormat;
            }

            updatedData[field.key] = value;
        });

        // If name changed, update initials for the avatar
        if (updatedData.name && updatedData.name !== this.currentRecord.name) {
            updatedData.initials = this.getInitials(updatedData.name);
        }

        // Update record in both data arrays
        this.tableData = this.tableData.map(item => {
            if (item.id === this.editRecordId) {
                return { ...item, ...updatedData };
            }
            return item;
        });

        this.filteredData = this.filteredData.map(item => {
            if (item.id === this.editRecordId) {
                return { ...item, ...updatedData };
            }
            return item;
        });

        // Execute callback if provided
        if (typeof this.onEditCallback === 'function') {
            this.onEditCallback(this.editRecordId, updatedData);
        }

        // Refresh the display
        this.displayData(this.currentPage);

        // Hide modal
        const editModal = window.bootstrap.Modal.getInstance(document.getElementById(this.modalId));
        if (editModal) {
            editModal.hide();
        }

        // Reset edit state
        this.editRecordId = null;
        this.currentRecord = null;
    }

    /**
     * Update action buttons (edit/delete)
     */
    updateActions() {
        const deleteButtons = this.tableBody.querySelectorAll('.delete-record-btn');
        const editButtons = this.tableBody.querySelectorAll('.edit-record-btn');

        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.deleteRecordId = button.getAttribute('data-id');
            });
        });

        editButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleEdit(button.getAttribute('data-id'));
            });
        });
    }

    /**
     * Display the result count information
     */
    displayResults() {
        if (!this.showingResults) return;

        const totalItems = this.filteredData.length;
        const start = Math.min(totalItems, this.currentPage * this.itemsPerPage - this.itemsPerPage + 1);
        const end = Math.min(this.currentPage * this.itemsPerPage, totalItems);

        this.showingResults.innerHTML = `نمایش <b class="me-1">${start}-${end}</b> از <b class="me-1">${totalItems}</b> نتیجه`;
    }

    /**
     * Update pagination UI to reflect current page
     */
    updatePaginationUI() {
        if (!this.paginationElement) return;

        const pageLinks = this.paginationElement.querySelectorAll('.page-link[data-page]');
        pageLinks?.forEach(link => {
            link.classList.remove('active');
            if (parseInt(link.getAttribute('data-page')) === this.currentPage) {
                link.classList.add('active');
            }
        });

        this.displayResults();
    }

    /**
     * Set up pagination controls
     */
    setupPagination() {
        if (!this.paginationElement) return;

        const pageCount = Math.max(1, Math.ceil(this.filteredData.length / this.itemsPerPage));
        this.paginationElement.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.innerHTML = `<a href="#" class="page-link" id="prev"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        prevLi.classList.add('page-item');
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.currentPage--;
                this.displayData(this.currentPage);
                this.updatePaginationUI();
            }
        });
        this.paginationElement.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= pageCount; i++) {
            const li = document.createElement('li');
            li.innerHTML = `<a href="#" class="page-link ${i === this.currentPage ? 'active' : ''}" data-page="${i}">${i}</a>`;
            li.classList.add('page-item');
            li.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = parseInt(e.target.getAttribute('data-page'));
                this.displayData(this.currentPage);
                this.updatePaginationUI();
            });
            this.paginationElement.appendChild(li);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.innerHTML = `<a href="#" class="page-link" id="next">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        nextLi.classList.add('page-item');
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < pageCount) {
                this.currentPage++;
                this.displayData(this.currentPage);
                this.updatePaginationUI();
            }
        });
        this.paginationElement.appendChild(nextLi);
        createIcons({ icons });
    }

    /**
     * Update the data and refresh the table
     * @param {Array} newData - New data array to use
     */
    updateData(newData) {
        this.rawData = newData;
        this.tableData = this.formatData([...this.rawData]);
        this.filteredData = this.tableData;
        this.currentPage = 1;
        this.currentSortColumn = null;
        this.currentSortDirection = 'asc';
        this.displayData(this.currentPage);
        this.setupPagination();
        this.updatePaginationUI();
    }
}

// Add some CSS for sorting
const style = document.createElement('style');
style.textContent = `
    .sortable {
        cursor: pointer;
        position: relative;
    }
    
    .sortable:hover {
        background-color: rgba(0, 0, 0, 0.05);
    }
    
    .sort-icons {
        display: flex;
        flex-direction: column;
        opacity: 0.3;
    }
    
    .sort-icon {
        font-size: 14px;
        line-height: 0.5;
    }
    
    .sort-asc .sort-up,
    .sort-desc .sort-down {
        opacity: 1;
    }
    
    .sort-asc .sort-icons,
    .sort-desc .sort-icons {
        opacity: 0.8;
    }
`;
document.head.appendChild(style);

// Example usage with the teacher table
document.addEventListener('DOMContentLoaded', function () {
    // define your badge class here
    const getBadgeClass = (title) => {
        switch (title) {
            case "Teacher":
                return "badge bg-primary-subtle text-primary border border-primary-subtle";
            case "Professor":
                return "badge bg-secondary-subtle text-secondary border border-secondary-subtle";
            case "Assistant":
                return "badge bg-warning-subtle text-warning border border-warning-subtle";
            case "Lecturer":
                return "badge bg-danger-subtle text-danger border border-danger-subtle";
            case "Instructor":
                return "badge bg-info-subtle text-info border border-info-subtle";
            case "Senior Lecturer":
                return "badge bg-orange-subtle text-orange border border-orange-subtle";
            case "Associate Professor":
                return "badge bg-light-subtle text-dark border border-dark-subtle";
            case "Assistant Professor":
                return "badge bg-success-subtle text-success border border-success-subtle";
            default:
                return "badge bg-primary-subtle text-primary border border-primary-subtle";
        }
    };

    // Format function for teacher data
    function formatTeacherData(data) {
        return data.map(item => {
            const formattedItem = { ...item };
            // joiningDate is already a final persian string; convert for displaying only if you need

            // formattedItem.joiningDate = new Date(item.joiningDate).toLocaleDateString('fa-IR', {
            //         year: 'numeric',
            //         month: 'long',
            //         day: 'numeric'
            //     });

            // Store the raw date for sorting
            // formattedItem._rawJoiningDate = new Date(item.joiningDate);  // _rawJoiningDate will be added once backend sends real ISO/timestamp
            formattedItem.className = getBadgeClass(item.title);
            return formattedItem;
        });
    }

    // Create row HTML for teacher data
    function createTeacherRow(item) {
        // Check if the item has a custom avatar with initials
        let avatarContent;
        if (item.hasCustomAvatar) {
            avatarContent = `<div class="size-8 rounded-pill d-flex align-items-center justify-content-center ${item.avatarColor} text-white">${item.initials}</div>`;
        } else {
            avatarContent = `<img src="${item.avatar}" loading="lazy" alt="" class="size-8 rounded-pill">`;
        }

        return `<td>${item.id}</td>
        <td>
            <div class="d-flex align-items-center gap-3">
                ${avatarContent}
                <h6 class="mb-0"><a href="apps-school-teachers-overview.html" class="text-body">${item.name}</a></h6>
            </div>
        </td>
        <td>${item.email}</td>
        <td>${item.phone}</td>
        <td>${item.salary}</td>
        <td>${item.experience}</td>
        <td><span class="${item.className}">${TITLE_EN_TO_FA[item.title] || item.title}</span></td>
        <td>${item.joiningDate}</td>
        <td>
            <div class="d-flex align-items-center gap-2">
                <button class="btn btn-sub-primary size-8 btn-icon edit-record-btn" data-id="${item.id}"><i class="ri-pencil-line"></i></button>
                <button class="btn btn-sub-danger size-8 btn-icon delete-record-btn" data-id="${item.id}" data-bs-toggle="modal" data-bs-target="#deleteModal"><i class="ri-delete-bin-line"></i></button>
            </div>
        </td>`;
    }

    // Initialize teacher table if it exists
    if (document.getElementById('teacherTable')) {
        const teacherTableManager = new TableManager({
            tableId: 'teacherTable',
            data: tableData, // Assuming tableData is defined globally
            formatData: formatTeacherData,
            createRow: createTeacherRow,
            itemsPerPage: 10,
            selectors: {
                tableBody: '#tableBody',
                tableHeader: 'thead',
                pagination: 'pagination',
                showingResults: 'showingResults',
                searchInput: 'searchTeacherInput',
                deleteButton: 'deleteButton'
            },
            sortConfig: {
                columns: [
                    { index: 0, key: 'id', label: 'شناسه' },
                    { index: 1, key: 'name', label: 'نام' },
                    { index: 2, key: 'email', label: 'ایمیل' },
                    {
                        index: 4, key: 'salary', label: 'حقوق',
                        // Custom sort function for salary (removes currency symbols and commas)
                        sortFn: (a, b, direction) => {
                            const numA = parseFloat(a.replace(/[^0-9.-]+/g, ''));
                            const numB = parseFloat(b.replace(/[^0-9.-]+/g, ''));
                            return direction === 'asc' ? numA - numB : numB - numA;
                        }
                    },
                    {
                        index: 5, key: 'experience', label: 'سابقه کاری',
                        // Custom sort function for experience (extracts years)
                        sortFn: (a, b, direction) => {
                            const numA = parseInt(a.replace(/[^0-9]+/g, ''));
                            const numB = parseInt(b.replace(/[^0-9]+/g, ''));
                            return direction === 'asc' ? numA - numB : numB - numA;
                        }
                    },
                    { index: 7, key: '_rawJoiningDate', label: 'تاریخ عضویت' }
                ]
            },
            editConfig: {
                fields: [
                    { key: 'name', label: 'نام', type: 'text' },
                    { key: 'email', label: 'ایمیل', type: 'text' },
                    { key: 'phone', label: 'شماره تلفن', type: 'text' },
                    { key: 'salary', label: 'حقوق', type: 'text' },
                    { key: 'experience', label: 'سابقه کاری', type: 'text' },
                    {
                        key: 'title',
                        label: 'عنوان',
                        type: 'select',
                        options: [
                            { value: 'Teacher', label: 'معلم' },
                            { value: 'Professor', label: 'استاد' },
                            { value: 'Assistant', label: 'دستیار' },
                            { value: 'Lecturer', label: 'مدرس' },
                            { value: 'Instructor', label: 'مربی' },
                            { value: 'Senior Lecturer', label: 'مدرس ارشد' },
                            { value: 'Associate Professor', label: 'دانشیار' },
                            { value: 'Assistant Professor', label: 'استادیار' }
                        ]
                    },
                    //❗❗ NOTE: Using 'text' instead of 'date' because the value is stored in Persian string format.
                    // The current form logic tries to parse 'date' fields with new Date(), which causes "Invalid Date".
                    // If the date format is later changed to ISO/Gregorian, switch this back to type: 'date'.
                    { key: 'joiningDate', label: 'تاریخ عضویت', type: 'text' }
                ],
                onEdit: (recordId, updatedData) => {
                    console.log('Record updated:', recordId, updatedData);
                }
            }
        });
    }
});