import { icons, createIcons } from "lucide";




VirtualSelect.init({
    ele: '#assignedSelect',
    options: [
        { label: "مکس بوکو", value: "Max Boucaut" },
        { label: "ناتاشا تگ", value: "Natasha Tegg" },
        { label: "ایتن زاهل", value: "Ethan Zahel" },
        { label: "رایان فریزر", value: "Ryan Frazer" },
        { label: "جولیان مارکونی", value: "Julian Marconi" },
        { label: "پاپی دالی", value: "Poppy Dalley" }
    ],
    selectedValue: 0,
    multiple: true,
});

VirtualSelect.init({
    ele: "#statusSelect2",
    options: [
        { label: "فعال", value: "Active" },
        { label: "در انتظار", value: "On Hold" },
        { label: "در حال انجام", value: "Pending" },
        { label: "تکمیل شده", value: "Completed" }
    ],
});
VirtualSelect.init({
    ele: "#filterStatusSelect",
    options: [
        { label: "فعال", value: "Active" },
        { label: "در انتظار", value: "On Hold" },
        { label: "در حال انجام", value: "Pending" },
        { label: "تکمیل شده", value: "Completed" }
    ],
});

VirtualSelect.init({
    ele: "#filterSelect",
    options: [
        { label: "هفتگی", value: "Weekly" },
        { label: "ماهانه", value: "Monthly" },
        { label: "سالانه", value: "Yearly" },
    ],
});

// Mapping
const STATUS_EN_TO_FA = {
    'Active': "فعال",
    'Completed': "تکمیل شده",
    'Pending': "در حال انجام",
    'On Hold': "در انتظار"
};

class TableManager {
    constructor(options) {
        this.tableContainer = document.querySelector(options.tableContainer || '.table-responsive');
        this.paginationContainer = document.querySelector(options.paginationContainer || '.pagination');
        this.searchInput = document.getElementById(options.searchInputId || 'searchProjectsInput');
        this.itemsPerPage = options.itemsPerPage || 10;
        this.currentPage = 1;
        this.projects = [];
        this.filteredProjects = [];
        this.totalPages = 0;
        this.modalId = options.modalId || 'addProjectModal';
        this.modal = null;
        this.sortColumn = null;
        this.sortDirection = 'asc';


        // Initialize with sample data if provided
        if (options.initialData) {
            this.projects = options.initialData;
            this.filteredProjects = [...this.projects];
        }

        this.init();
    }

    init() {
        this.modal = new window.bootstrap.Modal(document.getElementById(this.modalId));
        this.addEventListeners();
        this.updateProgressBarInForm();
        this.render();
    }
    updateProgressBarInForm() {
        const progressInput = document.getElementById('progressInput');
        const progressBar = document.querySelector('.progress .progress-bar');

        // Set initial progress to 0
        progressBar.style.width = '0%';
        progressBar.parentElement.setAttribute('aria-valuenow', 0);

        progressInput.addEventListener('input', function () {
            // Ensure value doesn't exceed 100
            let value = parseInt(this.value) || 0;
            if (value > 100) {
                value = 100;
                this.value = 100; // Fix: Update the input value too
            }

            // Update the progress bar width
            progressBar.style.width = value + '%';
            progressBar.parentElement.setAttribute('aria-valuenow', value);
        });
    }

    addEventListeners() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.handleSearch.bind(this));
        }

        // Add project form
        const addProjectForm = document.querySelector(`#${this.modalId} form`);
        if (addProjectForm) {
            addProjectForm.addEventListener('submit', this.handleAddProject.bind(this));
        }

        const addButton = document.querySelector(`#${this.modalId} #addProjectBtn`);
        if (addButton) {
            addButton.addEventListener('click', this.handleAddProject.bind(this));
        }

        // Master checkbox
        const masterCheckbox = document.getElementById('checAllData');
        if (masterCheckbox) {
            masterCheckbox.addEventListener('change', this.handleMasterCheckbox.bind(this));
        }

        // Delete button
        const deleteButton = document.querySelector('.trash-btn');
        if (deleteButton) {
            deleteButton.addEventListener('click', this.handleBulkDelete.bind(this));
        }

        this.tableContainer.addEventListener('click', this.handleTableActions.bind(this));

        // Add event listeners for sortable headers
        this.addSortableHeaderListeners();
    }

    // Add new method to handle sortable headers
    addSortableHeaderListeners() {
        const sortableHeaders = this.tableContainer.querySelectorAll('th[data-sort]');
        if (sortableHeaders.length) {
            sortableHeaders.forEach(header => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {
                    const column = header.getAttribute('data-sort');
                    this.sortProjects(column);
                });

                // Add sort indicators
                const sortIndicator = document.createElement('span');
                sortIndicator.className = 'sort-indicator ms-1';
                sortIndicator.innerHTML = '';
                header.appendChild(sortIndicator);
            });
        }
    }

    handleSearch(e) {
        const searchTerm = e.target.value;

        this.filteredProjects = this.projects.filter(project => {
            return (
                project.id.includes(searchTerm) ||
                project.name.includes(searchTerm) ||
                project.client.includes(searchTerm)
            );
        });

        this.currentPage = 1;
        this.render();
    }
    handleAddProject(e) {
        e.preventDefault();

        // Clear previous validation errors
        this.clearValidationErrors();

        // Get form values
        const projectTitle = document.getElementById('projectTitleInput').value;
        const clientName = document.getElementById('clientName').value;
        const dueDate = dueDateInput.value;
        const totalAmount = document.getElementById('totalAmountInput').value;
        let progress = document.getElementById('progressInput').value;

        // Get the status value from statusSelect2
        const statusSelect = document.querySelector("#statusSelect2");
        const status = statusSelect && statusSelect.value ? statusSelect.value : 'فعال';

        // Validate required fields
        let isValid = true;

        // Validate project title (required)
        if (!projectTitle.trim()) {
            this.showValidationError('projectTitleInput', 'عنوان پروژه الزامی است');
            isValid = false;
        }

        // Validate client name (required)
        if (!clientName.trim()) {
            this.showValidationError('clientName', 'نام مشتری الزامی است');
            isValid = false;
        }

        // Validate total amount (must be a valid number if provided)
        if (totalAmount && (isNaN(parseFloat(totalAmount)) || parseFloat(totalAmount) < 0)) {
            this.showValidationError('totalAmountInput', 'لطفا مبلغ معتبری وارد کنید');
            isValid = false;
        }

        // Validate progress (must be a number between 0-100)
        if (progress) {
            if (isNaN(parseInt(progress)) || parseInt(progress) < 0 || parseInt(progress) > 100) {
                this.showValidationError('progressInput', 'پیشرفت باید بین 0 تا 100 باشد');
                isValid = false;
            }
        }

        // If validation fails, stop here
        if (!isValid) {
            return;
        }

        // Ensure progress doesn't exceed 100
        progress = progress ? Math.min(parseInt(progress), 100).toString() : '0';

        // Get assigned users
        const assignedSelect = document.querySelector("#assignedSelect");
        const assignee = assignedSelect ? assignedSelect.value : [];
        let assigneesImages = [];

        // Map selected assignees to their respective images
        if (Array.isArray(assignee)) {
            assignee.forEach(element => {
                if (element == "Max Boucaut")
                    assigneesImages.push('assets/images/avatar/user-14.png');
                else if (element == "Poppy Dalley")
                    assigneesImages.push('assets/images/avatar/user-17.png');
                else if (element == "Ethan Zahel")
                    assigneesImages.push('assets/images/avatar/user-16.png');
                else if (element == "Ryan Frazer")
                    assigneesImages.push('assets/images/avatar/user-18.png');
                else if (element == "Natasha Tegg")
                    assigneesImages.push('assets/images/avatar/user-15.png');
                else if (element == "Julian Marconi")
                    assigneesImages.push('assets/images/avatar/user-20.png');
            });
        }

        // If no assignees selected, use default
        if (assigneesImages.length === 0) {
            assigneesImages = ['assets/images/avatar/user-14.png', 'assets/images/avatar/user-16.png'];
        }

        // Check if we're editing an existing project
        const editId = document.querySelector(`#${this.modalId} form`).dataset.editId;

        if (editId) {
            // Find the project to update
            const projectIndex = this.projects.findIndex(p => p.id === editId);

            if (projectIndex !== -1) {
                this.projects[projectIndex] = {
                    ...this.projects[projectIndex],
                    name: projectTitle,
                    client: clientName,
                    dueDate: dueDate || this.projects[projectIndex].dueDate,
                    totalAmount: totalAmount ? `${parseInt(totalAmount).toLocaleString('en-US')} تومان` : this.projects[projectIndex].totalAmount,
                    progress: progress,
                    assignedTo: assigneesImages,
                    status: status
                };
                this.filteredProjects = [...this.projects];

                document.getElementById('addProjectModalLabel').textContent = 'اضافه کردن پروژه';
                document.querySelector(`#${this.modalId} .btn-primary`).textContent = 'اضافه کردن پروژه';

                // Remove the edit ID from the form
                delete document.querySelector(`#${this.modalId} form`).dataset.editId;
            }
        } else {
            const newProject = {
                id: `PEP-${Math.floor(10000 + Math.random() * 90000)}`,
                name: projectTitle,
                client: clientName,
                assignedTo: assigneesImages,
                dueDate: dueDate || new Date().toLocaleDateString('fa-IR', { day: 'numeric', month: 'long', year: 'numeric' }),
                totalAmount: totalAmount ? `${parseInt(totalAmount).toLocaleString('en-US')} تومان` : '0 تومان',
                progress: progress,
                status: status
            };

            // Add to projects array
            this.projects.unshift(newProject);
            this.filteredProjects = [...this.projects];
        }

        // Close modal and reset form
        this.modal.hide();
        const progressBar = document.querySelector('.progress .progress-bar');
        progressBar.style.width = '0%';
        progressBar.parentElement.setAttribute('aria-valuenow', 0);

        document.querySelector(`#${this.modalId} form`).reset();

        // Reset assignee select safely
        if (window.VirtualSelect && typeof window.VirtualSelect.reset === 'function' && assignedSelect) {
            try {
                window.VirtualSelect.reset(assignedSelect);
            } catch (error) {
                console.warn('Could not reset VirtualSelect assignedSelect:', error);
                if (typeof VirtualSelect.setValue === 'function') {
                    try {
                        VirtualSelect.setValue(assignedSelect, []);
                    } catch (err) {
                        console.warn('Could not setValue for VirtualSelect assignedSelect:', err);
                    }
                }
            }
        }

        // Reset status select safely
        if (window.VirtualSelect && typeof window.VirtualSelect.reset === 'function' && statusSelect) {
            try {
                window.VirtualSelect.reset(statusSelect);
            } catch (error) {
                console.warn('Could not reset VirtualSelect statusSelect:', error);
                if (typeof VirtualSelect.setValue === 'function') {
                    try {
                        VirtualSelect.setValue(statusSelect, 'فعال');
                    } catch (err) {
                        console.warn('Could not setValue for VirtualSelect statusSelect:', err);
                    }
                }
            }
        }
        this.render();
    }

    /**
     * Shows validation error for a specific form field
     * @param {string} inputId - ID of the input element
     * @param {string} message - Error message to display
     */
    showValidationError(inputId, message) {
        const inputElement = document.getElementById(inputId);
        if (!inputElement) return;

        // Add error class to input
        inputElement.classList.add('is-invalid');

        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        errorDiv.style.display = 'block'; // Ensure it's visible

        // Add error message after the input
        inputElement.parentNode.insertBefore(errorDiv, inputElement.nextSibling);
    }

    /**
     * Clears all validation errors from the form
     */
    clearValidationErrors() {
        // Remove error messages
        document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

        // Remove error styling from inputs
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    }

    /**
     * Validates a date string
     * @param {string} dateString - The date string to validate
     * @returns {boolean} - True if valid date, false otherwise
     */
    isValidDate(dateString) {
        // Basic pattern match for common date formats
        // This is a simplified check - adapt as needed based on your date format
        if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString) && // YYYY-MM-DD
            !/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(dateString) && // MM/DD/YYYY or M/D/YYYY
            !/^\d{1,2}-\d{1,2}-\d{4}$/.test(dateString) && // MM-DD-YYYY or M-D-YYYY
            !/^[A-Za-z]{3} \d{1,2}, \d{4}$/.test(dateString)) { // MMM DD, YYYY
            return false;
        }

        // Check if it's a valid date
        const date = new Date(dateString);
        return !isNaN(date.getTime());
    }

    handleEditProject(projectId) {
        const project = this.projects.find(p => p.id === projectId);

        if (!project) return;

        document.getElementById('projectTitleInput').value = project.name;
        document.getElementById('clientName').value = project.client;
        document.getElementById('dueDateInput').value = project.dueDate;
        document.getElementById('totalAmountInput').value = project.totalAmount.replace('تومان', '').replace(/[,٬]/g, '').trim();

        // Fix for progress bar update on edit
        const progressInput = document.getElementById('progressInput');
        const progressBar = document.querySelector('.progress .progress-bar');

        // First set the progress input value
        progressInput.value = project.progress;

        // Then manually update the progress bar
        // This ensures the progress bar updates even if the input event isn't triggered
        progressBar.style.width = project.progress + '%';
        progressBar.parentElement.setAttribute('aria-valuenow', project.progress);

        // Trigger the input event to ensure any event listeners update the UI
        // This creates a new event and dispatches it on the progress input
        const inputEvent = new Event('input', { bubbles: true });
        progressInput.dispatchEvent(inputEvent);

        const statusSelect = document.querySelector('#statusSelect2');
        if (window.VirtualSelect && statusSelect && project.status) {
            try {
                VirtualSelect.setValue(statusSelect, project.status);
            } catch (error) {
                console.warn('Could not set status value:', error);
            }
        }

        // Set assigned users in select
        const assignedSelect = document.querySelector('#assignedSelect');
        if (window.VirtualSelect && assignedSelect && project.assignedTo) {
            const selectedNames = project.assignedTo.map(imagePath => {
                if (imagePath.includes('user-14')) return 'Max Boucaut';
                if (imagePath.includes('user-17')) return 'Poppy Dalley';
                if (imagePath.includes('user-16')) return 'Ethan Zahel';
                if (imagePath.includes('user-18')) return 'Ryan Frazer';
                if (imagePath.includes('user-15')) return 'Natasha Tegg';
                if (imagePath.includes('user-20')) return 'Julian Marconi';
                return null;
            }).filter(Boolean);

            try {
                VirtualSelect.setValue(assignedSelect, selectedNames);
            } catch (error) {
                console.warn('Could not set assignee values:', error);
            }
        }

        this.modal.show();

        document.getElementById('addProjectModalLabel').textContent = 'ویرایش پروژه';
        document.querySelector(`#${this.modalId} .btn-primary`).textContent = 'آپدیت پروژه';

        document.querySelector(`#${this.modalId} form`).dataset.editId = projectId;
    }

    handleDeleteProject(projectId) {
        if (confirm('آیا از حذف این پروژه مطمئن هستید؟')) {
            this.projects = this.projects.filter(p => p.id !== projectId);
            this.filteredProjects = this.filteredProjects.filter(p => p.id !== projectId);
            this.render();
        }
    }

    handleBulkDelete() {
        const checkedProjects = this.tableContainer.querySelectorAll('.form-check-input:checked:not(#checAllData)');

        if (checkedProjects.length === 0) return;

        if (confirm(`آیا از حذف این ${checkedProjects.length} پروژه مطمئن هستید؟`)) {
            const projectIds = Array.from(checkedProjects).map(checkbox => {
                const row = checkbox.closest('tr');
                return row.querySelector('td:nth-child(2)').textContent.trim();
            });

            this.projects = this.projects.filter(p => !projectIds.includes(p.id));
            this.filteredProjects = this.filteredProjects.filter(p => !projectIds.includes(p.id));

            const deleteButton = document.querySelector('.btn-danger.btn-icon');
            if (deleteButton) {
                deleteButton.classList.add('d-none');
            }

            const masterCheckbox = document.getElementById('checAllData');
            if (masterCheckbox) {
                masterCheckbox.checked = false;
            }
            this.render();
        }
    }


    handleMasterCheckbox(e) {
        const isChecked = e.target.checked;
        const checkboxes = this.tableContainer.querySelectorAll('.form-check-input:not(#checAllData)');

        checkboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });

        // Toggle delete button
        const deleteButton = document.querySelector('.btn-danger.btn-icon');
        if (deleteButton) {
            if (isChecked && checkboxes.length > 0) {
                deleteButton.classList.remove('d-none');
            } else {
                deleteButton.classList.add('d-none');
            }
        }
    }


    handleCheckboxChange() {
        const checkedBoxes = this.tableContainer.querySelectorAll('.form-check-input:checked:not(#checAllData)');
        const deleteButton = document.querySelector('.btn-danger.btn-icon');

        if (deleteButton) {
            if (checkedBoxes.length > 0) {
                deleteButton.classList.remove('d-none');
            } else {
                deleteButton.classList.add('d-none');
            }
        }
    }

    handleTableActions(e) {
        const target = e.target;

        // Handle checkbox changes
        if (target.classList.contains('form-check-input') && target.id !== 'checAllData') {
            this.handleCheckboxChange();
            return;
        }

        // Rest of the code remains the same
        if (target.classList.contains('ri-pencil-line') || (target.closest('.dropdown-item') && target.closest('.dropdown-item').querySelector('.ri-pencil-line'))) {
            const row = target.closest('tr');
            const projectId = row.querySelector('td:nth-child(2)').textContent.trim();
            this.handleEditProject(projectId);
            return;
        }

        if (target.classList.contains('ri-delete-bin-line') || (target.closest('.dropdown-item') && target.closest('.dropdown-item').querySelector('.ri-delete-bin-line'))) {
            const row = target.closest('tr');
            const projectId = row.querySelector('td:nth-child(2)').textContent.trim();
            this.handleDeleteProject(projectId);
            return;
        }
    }

    // Enhanced sort method with proper comparison for different data types
    sortProjects(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        this.filteredProjects.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];

            // Special handling for formatted values
            if (column === 'totalAmount') {
                // Extract numeric value from currency format (e.g., "$1,000" → 1000)
                valA = parseFloat(valA.replace(/[^0-9.-]+/g, ''));
                valB = parseFloat(valB.replace(/[^0-9.-]+/g, ''));
            } else if (column === 'dueDate') {
                valA = new Date(valA).getTime();
                valB = new Date(valB).getTime();
            } else if (column === 'progress') {
                // Progress is already a number, but ensure it's parsed as such
                valA = parseFloat(valA);
                valB = parseFloat(valB);
            } else if (!isNaN(valA) && !isNaN(valB)) {
                valA = parseFloat(valA);
                valB = parseFloat(valB);
            }

            if (valA < valB) return this.sortDirection === 'asc' ? -1 : 1;
            if (valA > valB) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        this.renderTable();
    }

    renderTable() {
        // Calculate pagination
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const paginatedProjects = this.filteredProjects.slice(startIndex, endIndex);
        this.totalPages = Math.ceil(this.filteredProjects.length / this.itemsPerPage);

        // Check if there are no projects to display
        if (paginatedProjects.length === 0) {
            this.tableContainer.innerHTML = `
        <table class="table align-middle text-nowrap mb-0">
            <thead class="bg-light border-bottom">
              <tr>
                <th>
                  <div class="form-check check-primary">
                    <input class="form-check-input" type="checkbox" aria-label="checkbox" id="checAllData">
                    <label class="form-check-label d-none" for="checAllData">
                      Check All Data
                    </label>
                  </div>
                </th>
                <th class="fw-medium text-muted" data-sort="id">شناسه</th>
                <th class="fw-medium text-muted" data-sort="name">نام پروژه و کارفرما</th>
                <th class="fw-medium text-muted">تفویض به</th>
                <th class="fw-medium text-muted" data-sort="dueDate">تاریخ سررسید</th>
                <th class="fw-medium text-muted" data-sort="totalAmount">مبلغ کل (تومان)</th>
                <th class="fw-medium text-muted" data-sort="progress">درصد تکمیل</th>
                <th class="fw-medium text-muted" data-sort="status">وضعیت</th>
                <th class="fw-medium text-muted">عملیات</th>
              </tr>
            </thead>
            <tbody id="projectsTableBody">
              <tr>
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
                      <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164 S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331    c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                      <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0 l-4.331-4.331"></path>
                      <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                      <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                    </svg>
                    <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                    <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                  </div>
                </td>
              </tr>
            </tbody>
        </table>`;

            // Add sortable header listeners even when no data
            this.addSortableHeaderListeners();
            return;
        }

        // Generate table rows
        const rows = paginatedProjects.map((project, index) => {

        const statusFa = STATUS_EN_TO_FA[project.status] || project.status;

            return `
        <tr>
          <td>
            <div class="form-check check-primary">
              <input class="form-check-input" type="checkbox" aria-label="checkbox" id="checData${index + 1}">
              <label class="form-check-label d-none" for="checData${index + 1}">
                Check Data ${index + 1}
              </label>
            </div>
          </td>
          <td>${project.id}</td>
          <td>
            <a href="#!" class="link link-custom fw-semibold">${project.name}</a>
            <p class="text-muted fs-sm">${project.client}</p>
          </td>
          <td>
            <div class="avatar-group">
              ${project.assignedTo.map(avatar => `
                <a href="#!" class="avatar-group-item" aria-label="avatar-link">
                  <img src="${avatar}" loading="lazy" alt="" class="size-8">
                </a>
              `).join('')}
            </div>
          </td>
          <td>${project.dueDate}</td>
          <td>${project.totalAmount}</td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <p class="flex-shrink-0">${project.progress}%</p>
              <div class="progress progress-1 flex-grow-1" role="progressbar" aria-label="${project.name}" aria-valuenow="${project.progress}" aria-valuemin="0" aria-valuemax="100">
                <div class="progress-bar" style="width: ${project.progress}%"></div>
              </div>
            </div>
          </td>
          <td><span class="badge bg-${project.status === 'Active' ? 'secondary' : project.status === 'Completed' ? 'success' : project.status === 'Pending' ? 'warning' : project.status === 'On Hold' ? 'info' : 'danger'}-subtle text-${project.status === 'Active' ? 'secondary' : project.status === 'Completed' ? 'success' : project.status === 'Pending' ? 'warning' : project.status === 'On Hold' ? 'info' : 'danger'} border border-${project.status === 'Active' ? 'secondary' : project.status === 'Completed' ? 'success' : project.status === 'Pending' ? 'warning' : project.status === 'On Hold' ? 'info' : 'danger'}-subtle">${statusFa}</span></td>
          <td>
            <div class="dropdown">
              <a href="#!" class="link link-custom-primary" aria-label="dropdown button" id="actionDropdown${index + 1}" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="ri-more-2-fill"></i>
              </a>
              <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="actionDropdown${index + 1}">
                <li><a class="dropdown-item" href="#"> <i class="ri-eye-line me-2"></i>نمای کلی</a></li>
                <li><a class="dropdown-item" href="#"><i class="ri-pencil-line me-2"></i>ویرایش</a></li>
                <li><a class="dropdown-item" href="#"> <i class="ri-delete-bin-line me-2"></i>حذف</a></li>
              </ul>
            </div>
          </td>
        </tr>
      `;
        }).join('');

        // Update table content with sortable headers
        const tableContent = `
      <table class="table align-middle text-nowrap mb-0">
        <thead class="bg-light border-bottom">
          <tr>
            <th>
              <div class="form-check check-primary">
                <input class="form-check-input" type="checkbox" aria-label="checkbox" id="checAllData">
                <label class="form-check-label d-none" for="checAllData">
                  Check All Data
                </label>
              </div>
            </th>
            <th class="fw-medium text-muted" data-sort="id">شناسه ${this.sortColumn === 'id' ? (this.sortDirection === 'asc' ? '↑' : '↓') : ''}</th>
            <th class="fw-medium text-muted" data-sort="name">نام پروژه و کارفرما ${this.sortColumn === 'name' ? (this.sortDirection === 'asc' ? '↑' : '↓') : ''}</th>
            <th class="fw-medium text-muted">تفویض شده به</th>
            <th class="fw-medium text-muted" data-sort="dueDate">تاریخ سررسید ${this.sortColumn === 'dueDate' ? (this.sortDirection === 'asc' ? '↑' : '↓') : ''}</th>
            <th class="fw-medium text-muted" data-sort="totalAmount">مبلغ کل (تومان) ${this.sortColumn === 'totalAmount' ? (this.sortDirection === 'asc' ? '↑' : '↓') : ''}</th>
            <th class="fw-medium text-muted" data-sort="progress">درصد تکمیل ${this.sortColumn === 'progress' ? (this.sortDirection === 'asc' ? '↑' : '↓') : ''}</th>
            <th class="fw-medium text-muted" data-sort="status">وضعیت ${this.sortColumn === 'status' ? (this.sortDirection === 'asc' ? '↑' : '↓') : ''}</th>
            <th class="fw-medium text-muted">عملیات</th>
          </tr>
        </thead>
        <tbody id="projectsTableBody">
          ${rows}
        </tbody>
      </table>
    `;

        this.tableContainer.innerHTML = tableContent;

        // Re-add event listeners for master checkbox
        const masterCheckbox = document.getElementById('checAllData');
        if (masterCheckbox) {
            masterCheckbox.addEventListener('change', this.handleMasterCheckbox.bind(this));
        }

        // Add event listeners to individual checkboxes
        const checkboxes = this.tableContainer.querySelectorAll('.form-check-input:not(#checAllData)');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', this.handleCheckboxChange.bind(this));
        });

        // Add event listeners for sorting
        const sortableHeaders = this.tableContainer.querySelectorAll('th[data-sort]');
        sortableHeaders.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-sort');
                this.sortProjects(column);
            });
        });
    }

    renderPagination() {
        // Generate pagination controls
        let paginationHTML = `
      <div class="row align-items-center g-3 mt-2">
        <div class="col-md-6">
          <p class="text-muted text-center text-md-start mb-0">
            نمایش <b class="me-1">${(this.currentPage - 1) * this.itemsPerPage + 1}-${Math.min(this.currentPage * this.itemsPerPage, this.filteredProjects.length)}</b>
            از<b class="ms-1">${this.filteredProjects.length}</b> نتیجه
          </p>
        </div>
        <div class="col-md-6">
          <nav aria-label="Page navigation example">
            <ul class="pagination justify-content-center justify-content-md-end mb-0">
              <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#!" data-page="${this.currentPage - 1}">
                  <i data-lucide="chevron-right" class="size-4"></i> قبلی
                </a>
              </li>
    `;

        // Add page numbers
        for (let i = 1; i <= this.totalPages; i++) {
            paginationHTML += `
        <li class="page-item ${this.currentPage === i ? 'active' : ''}">
          <a class="page-link" href="#!" data-page="${i}">${i}</a>
        </li>
      `;
        }

        paginationHTML += `
              <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#!" data-page="${this.currentPage + 1}">
                  بعدی <i data-lucide="chevron-left" class="size-4"></i>
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    `;

        // Add pagination container after the table
        const paginationContainer = document.querySelector('.row.align-items-center.g-3.mt-2');
        if (paginationContainer) {
            paginationContainer.innerHTML = paginationHTML;
        } else {
            const paginationDiv = document.createElement('div');
            paginationDiv.innerHTML = paginationHTML;
            this.tableContainer.after(paginationDiv);
        }

        // Add event listeners to pagination buttons
        document.querySelectorAll('.page-link').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.currentTarget.dataset.page);
                if (!isNaN(page) && page > 0 && page <= this.totalPages) {
                    this.currentPage = page;
                    this.render();
                }
            });
        });
    }

    render() {
        this.renderTable();
        this.renderPagination();

        createIcons({ icons });
    }

    // Filter methods
    filterByStatus(status) {
        if (!status || status === 'All') {
            this.filteredProjects = [...this.projects];
        } else {
            this.filteredProjects = this.projects.filter(p => p.status === status);
        }
        this.currentPage = 1;
        this.render();
    }

    filterByDate(dateRange) {
        // Implementation depends on your date format and requirements
        this.render();
    }

    filterByAssignee(assignees) {
        // Implementation depends on your assignee data structure
        this.render();
    }

    // Data operations
    setData(data) {
        this.projects = data;
        this.filteredProjects = [...data];
        this.currentPage = 1;
        this.render();
    }

    getData() {
        return this.projects;
    }
}

// Sample data
const sampleProjects = [
    {
        id: 'PEC-24567',
        name: 'توسعه برنامه موبایل',
        client: 'FitLife',
        assignedTo: ['assets/images/avatar/user-12.png', 'assets/images/avatar/user-20.png'],
        dueDate: '30 مهر 1403',
        totalAmount: '48,000 تومان',
        progress: '30',
        status: 'Active'
    },
    {
        id: 'PEC-24623',
        name: 'بازنگری سیستم CRM',
        client: 'BizWorks',
        assignedTo: ['assets/images/avatar/user-14.png', 'assets/images/avatar/user-1.png'],
        dueDate: '22 آذر 1403',
        totalAmount: '75,000 تومان',
        progress: '80',
        status: 'Completed'
    },
    {
        id: 'PEC-24888',
        name: 'مهاجرت داده',
        client: 'CloudNet',
        assignedTo: ['assets/images/avatar/user-18.png', 'assets/images/avatar/user-30.png'],
        dueDate: '18 اسفند 1403',
        totalAmount: '28,000 تومان',
        progress: '55',
        status: 'Active'
    },
    {
        id: 'PEC-24990',
        name: 'بهینه‌سازی سئو',
        client: 'MediaGenix',
        assignedTo: ['assets/images/avatar/user-4.png', 'assets/images/avatar/user-8.png'],
        dueDate: '12 اردیبهشت 1404',
        totalAmount: '10,000 تومان',
        progress: '90',
        status: 'Pending'
    },
    {
        id: 'PEC-25001',
        name: 'سیستم مدیریت موجودی',
        client: 'WarehousePro',
        assignedTo: ['assets/images/avatar/user-6.png', 'assets/images/avatar/user-23.png'],
        dueDate: '03 مرداد 1403',
        totalAmount: '55,000 تومان',
        progress: '35',
        status: 'Active'
    },
    {
        id: 'PEC-25123',
        name: 'بازنگری پورتال منابع انسانی',
        client: 'PeopleFirst',
        assignedTo: ['assets/images/avatar/user-15.png', 'assets/images/avatar/user-19.png'],
        dueDate: '25 فروردین 1404',
        totalAmount: '20,000 تومان',
        progress: '12',
        status: 'Pending'
    },
    {
        id: 'PEC-25245',
        name: 'کمپین بازاریابی دیجیتال',
        client: 'ClickPoint',
        assignedTo: ['assets/images/avatar/user-13.png', 'assets/images/avatar/user-10.png'],
        dueDate: '08 خرداد 1404',
        totalAmount: '16,000 تومان',
        progress: '78',
        status: 'Active'
    },
    {
        id: 'PEC-25367',
        name: 'بررسی و اصلاح وب‌سایت',
        client: 'WebInsight',
        assignedTo: ['assets/images/avatar/user-27.png', 'assets/images/avatar/user-21.png'],
        dueDate: '01 بهمن 1403',
        totalAmount: '8,000 تومان',
        progress: '92',
        status: 'Completed'
    },
    {
        id: 'PEC-25488',
        name: 'ادغام بلاک‌چین',
        client: 'CoinTrust',
        assignedTo: ['assets/images/avatar/user-28.png', 'assets/images/avatar/user-7.png'],
        dueDate: '11 مهر 1403',
        totalAmount: '70,000 تومان',
        progress: '20',
        status: 'Active'
    },
    {
        id: 'PEC-25590',
        name: 'برنامه دسکتاپ برای تجزیه و تحلیل',
        client: 'DataMine',
        assignedTo: ['assets/images/avatar/user-25.png', 'assets/images/avatar/user-22.png'],
        dueDate: '15 آبان 1403',
        totalAmount: '43,000 تومان',
        progress: '40',
        status: 'Pending'
    },
    {
        id: 'PEC-25701',
        name: 'تحقیق و آزمایش UX',
        client: 'DesignHive',
        assignedTo: ['assets/images/avatar/user-11.png', 'assets/images/avatar/user-26.png'],
        dueDate: '05 آذر 1403',
        totalAmount: '12,000 تومان',
        progress: '70',
        status: 'Active'
    },
    {
        id: 'PEC-25812',
        name: 'راه‌اندازی درگاه پرداخت',
        client: 'PayHub',
        assignedTo: ['assets/images/avatar/user-17.png', 'assets/images/avatar/user-2.png'],
        dueDate: '20 تیر 1403',
        totalAmount: '18,000 تومان',
        progress: '22',
        status: 'Pending'
    },
    {
        id: 'PEC-25923',
        name: 'راهکار پشتیبان‌گیری ابری',
        client: 'SecureStor',
        assignedTo: ['assets/images/avatar/user-24.png', 'assets/images/avatar/user-29.png'],
        dueDate: '29 شهریور 1404',
        totalAmount: '39,000 تومان',
        progress: '50',
        status: 'Active'
    },
    {
        id: 'PEC-26034',
        name: 'ابزار مدیریت رسانه‌های اجتماعی',
        client: 'InstaTools',
        assignedTo: ['assets/images/avatar/user-16.png', 'assets/images/avatar/user-3.png'],
        dueDate: '13 مرداد 1403',
        totalAmount: '25,000 تومان',
        progress: '10',
        status: 'Pending'
    },
    {
        id: 'PEC-26145',
        name: 'پلتفرم اتوماسیون ایمیل',
        client: 'MailLaunch',
        assignedTo: ['assets/images/avatar/user-5.png', 'assets/images/avatar/user-20.png'],
        dueDate: '07 دی 1403',
        totalAmount: '30,000 تومان',
        progress: '60',
        status: 'Active'
    }
];

// Initialize the table manager with sample data
document.addEventListener('DOMContentLoaded', function () {
    const tableManager = new TableManager({
        tableContainer: '.table-responsive',
        searchInputId: 'searchProjectsInput',
        modalId: 'addProjectModal',
        itemsPerPage: 10,
        initialData: sampleProjects
    });

    window.tableManager = tableManager;

    // Initialize filter selects
    if (typeof initializeFilters === 'function') {
        initializeFilters(tableManager);
    }
});

// Initialize filter dropdowns
function initializeFilters(tableManager) {
    document.getElementById('filterStatusSelect')?.addEventListener('change', function (e) {
        tableManager.filterByStatus(e.target.value);
    });
    document.getElementById('filterSelect')?.addEventListener('change', function (e) {
        tableManager.filterByDate(e.target.value);
    });

    document.querySelectorAll('#filterAssigneeDropdown .form-check-input').forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const selectedAssignees = Array.from(
                document.querySelectorAll('#filterAssigneeDropdown .form-check-input:checked')
            ).map(cb => cb.value);

            tableManager.filterByAssignee(selectedAssignees);
        });
    });
}