import { icons, createIcons } from "lucide";


//Gender select
VirtualSelect.init({
    ele: "#genderSelect",
    options: [
        { label: "مرد", value: "Male" },
        { label: "زن", value: "Female" },
    ],
});

// Gender Mapping
const genderMapping = {
    'Male': 'مرد',
    'Female': 'زن',
    'Other': 'دیگری'
};

// Table Manager Class for Parent Management
class TableManager {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            itemsPerPage: options.itemsPerPage || 10,
            searchField: options.searchField || 'searchInvoiceInput',
            addBtnModal: options.addBtnModal || 'leadCreateModal',
            deleteModal: options.deleteModal || 'deleteModal',
            ...options
        };

        this.currentPage = 1;
        this.data = [];
        this.filteredData = [];
        this.currentEditId = null;
        this.currentDeleteId = null;

        // Add sorting properties
        this.sortColumn = null;
        this.sortDirection = 'asc';

        this.init();
    }

    init() {
        // Load initial data
        this.loadData();

        // Initialize event listeners
        this.initEventListeners();

        // Render the table initially
        this.renderTable();

        // Initialize sortable columns
        this.initSortableColumns();
    }


    loadData() {
        // Sample JSON data - in a real app this might come from an API
        this.data = [
            {
                id: 1,
                parentName: "تینا مک پیک",
                studentName: "دوروتی آزبورتک",
                studentImage: "assets/images/avatar/user-1.png",
                relation: "مادر",
                occupation: "پرستار",
                gender: "Female",
                email: "tina@gmail.com",
                phone: "+ 1541151542",
                address: "بلژیک"
            },
            {
                id: 2,
                parentName: "جان مک پیک",
                studentName: "جاش دیلی",
                studentImage: "assets/images/avatar/user-1.png",
                relation: "پدر",
                occupation: "مدیر",
                gender: "Male",
                email: "elmer@gmail.com",
                phone: "+ 1541151542",
                address: "بلژیک"
            },
            {
                id: 3,
                parentName: "پاول بالز",
                studentName: "سیلویا بالز",
                studentImage: "assets/images/avatar/user-5.png",
                relation: "پدر",
                occupation: "مدیر اداری",
                gender: "Male",
                email: "paulballs@gmail.com",
                phone: "+ 544514457",
                address: "لهستان"
            },
            {
                id: 4,
                parentName: "جودی سودو",
                studentName: "رابرت سودو",
                studentImage: "",
                relation: "مادر",
                occupation: "دستیار مدیر",
                gender: "Female",
                email: "judy@gmail.com",
                phone: "+ 2451514574",
                address: "رومانی"
            },
            {
                id: 5,
                parentName: "جان هارپر",
                studentName: "ایمیلی هارپر",
                studentImage: "assets/images/avatar/user-8.png",
                relation: "پدر",
                occupation: "مدیر حساب",
                gender: "Male",
                email: "johnh@gmail.com",
                phone: "+ 1625151523",
                address: "مکزیک"
            },
            {
                id: 6,
                parentName: "آماندا هنسن",
                studentName: "مایکل هنسن",
                studentImage: "assets/images/avatar/user-14.png",
                relation: "مادر",
                occupation: "هماهنگ‌کننده",
                gender: "Female",
                email: "amanda@gmail.com",
                phone: "+ 1712251525",
                address: "اوکراین"
            },
            {
                id: 7,
                parentName: "جاستینا لی",
                studentName: "جسیکا لی",
                studentImage: "assets/images/avatar/user-15.png",
                relation: "مادر",
                occupation: "پرستار",
                gender: "Female",
                email: "clarissa@gmail.com",
                phone: "+ 1845351623",
                address: "اوکراین"
            },
            {
                id: 8,
                parentName: "ساموئل جکسون",
                studentName: "دنیل جکسون",
                studentImage: "",
                relation: "پدر",
                occupation: "مدیر مدرسه",
                gender: "Male",
                email: "samuel@gmail.com",
                phone: "+ 1945151627",
                address: "ایتالیا"
            },
            {
                id: 9,
                parentName: "اولیویا کارل",
                studentName: "جیکوب کارل",
                studentImage: "assets/images/avatar/user-17.png",
                relation: "مادر",
                occupation: "تحلیل‌گر مالی",
                gender: "Female",
                email: "jacque@gmail.com",
                phone: "+ 1741251823",
                address: "مجارستان"
            },
            {
                id: 10,
                parentName: "جوزف ویلسون",
                studentName: "ایتان ویلسون",
                studentImage: "assets/images/avatar/user-4.png",
                relation: "پدر",
                occupation: "منابع انسانی",
                gender: "Male",
                email: "joseph@gmail.com",
                phone: "+ 1815351923",
                address: "اسپانیا"
            },
            {
                id: 11,
                parentName: "نانسی اسمیت",
                studentName: "چارلز اسمیت",
                studentImage: "assets/images/avatar/user-19.png",
                relation: "مادر",
                occupation: "معلم",
                gender: "Female",
                email: "nancy@gmail.com",
                phone: "+ 1952362024",
                address: "آلمان"
            },
            {
                id: 12,
                parentName: "دیوید براون",
                studentName: "سوفیا براون",
                studentImage: "assets/images/avatar/user-20.png",
                relation: "پدر",
                occupation: "مهندس نرم‌افزار",
                gender: "Male",
                email: "david@gmail.com",
                phone: "+ 1963472125",
                address: "فرانسه"
            },
            {
                id: 13,
                parentName: "پاتریشیا دیویس",
                studentName: "بنیامین دیویس",
                studentImage: "assets/images/avatar/user-21.png",
                relation: "مادر",
                occupation: "مدیر بازاریابی",
                gender: "Female",
                email: "patricia@gmail.com",
                phone: "+ 1974582226",
                address: "هلند"
            },
            {
                id: 14,
                parentName: "مایکل مارتینز",
                studentName: "اما مارتینز",
                studentImage: "assets/images/avatar/user-22.png",
                relation: "پدر",
                occupation: "پزشک",
                gender: "Male",
                email: "michael@gmail.com",
                phone: "+ 1985692327",
                address: "سوئد"
            },
            {
                id: 15,
                parentName: "باربارا تیلور",
                studentName: "بریتنی تیلور",
                studentImage: "assets/images/avatar/user-23.png",
                relation: "مادر",
                occupation: "طراح گرافیک",
                gender: "Female",
                email: "barbara@gmail.com",
                phone: "+ 1996702428",
                address: "نروژ"
            },
            {
                id: 16,
                parentName: "کریستوفر والتز",
                studentName: "آوا والتز",
                studentImage: "assets/images/avatar/user-24.png",
                relation: "پدر",
                occupation: "سرآشپز",
                gender: "Male",
                email: "christopher@gmail.com",
                phone: "+ 1907812529",
                address: "فنلاند"
            },
            {
                id: 17,
                parentName: "لیسا لی",
                studentName: "ایزابلا لی",
                studentImage: "assets/images/avatar/user-25.png",
                relation: "مادر",
                occupation: "مدیر پروژه",
                gender: "Female",
                email: "lisa@gmail.com",
                phone: "+ 1918922630",
                address: "دانمارک"
            },
            {
                id: 18,
                parentName: "جاشوا کلارک",
                studentName: "لوکاس کلارک",
                studentImage: "assets/images/avatar/user-28.png",
                relation: "پدر",
                occupation: "دندان‌پزشک",
                gender: "Male",
                email: "joshua@gmail.com",
                phone: "+ 1941252933",
                address: "ایرلند"
            }
        ];

        this.filteredData = [...this.data];
    }

    initEventListeners() {
        // Search functionality
        const searchInput = document.getElementById(this.options.searchField);
        if (searchInput) {
            searchInput.addEventListener('input', () => this.handleSearch(searchInput.value));
        }

        // Form submission for adding new parent
        const form = document.querySelector('#leadCreateModal form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Image upload preview
        const imageInput = document.getElementById('imageInput');
        if (imageInput) {
            imageInput.addEventListener('change', this.handleImageUpload);
        }

        // Initialize delete confirmation modal
        const deleteModal = document.getElementById(this.options.deleteModal);
        if (deleteModal) {
            deleteModal.addEventListener('show.bs.modal', (event) => {
                this.currentDeleteId = event.relatedTarget.dataset.id;
            });

            const deleteBtn = deleteModal.querySelector('.btn-danger');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => this.deleteItem(this.currentDeleteId));
            }
        }

        // Initialize gender select dropdown (using a simple implementation)
        this.initGenderSelect();

        // Initialize pagination events
        this.initPaginationEvents();
    }

    // Initialize sortable column headers
    initSortableColumns() {
        // Add click event listeners to table headers with data-sort attribute
        const tableHeaders = document.querySelectorAll('th[data-sort]');

        tableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.sort;
                this.handleSort(column);
            });

            // Add sort indicator and cursor style
            header.style.cursor = 'pointer';
            header.classList.add('sortable');

            // Add sort icon container
            if (!header.querySelector('.sort-icon')) {
                const iconSpan = document.createElement('span');
                iconSpan.className = 'sort-icon ms-2';
                header.appendChild(iconSpan);
            }
        });
    }

    // Handle sorting when a column header is clicked
    handleSort(column) {
        // If clicking the same column, toggle direction
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // New column, default to ascending
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        // Sort the data
        this.sortData();

        // Update the UI to show sort direction
        this.updateSortIndicators();

        // Reset to first page and render
        this.currentPage = 1;
        this.renderTable();
    }

    // Sort the data based on current column and direction
    sortData() {
        const column = this.sortColumn;
        const direction = this.sortDirection;

        if (!column) return;

        this.filteredData.sort((a, b) => {
            let valueA = a[column];
            let valueB = b[column];

            // Handle string comparisons (case-insensitive)
            if (typeof valueA === 'string' && typeof valueB === 'string') {
                valueA = valueA.toLowerCase();
                valueB = valueB.toLowerCase();
            }

            // Compare values
            if (valueA < valueB) {
                return direction === 'asc' ? -1 : 1;
            }
            if (valueA > valueB) {
                return direction === 'asc' ? 1 : -1;
            }
            return 0;
        });
    }

    // Update the UI to show sort indicators
    updateSortIndicators() {
        // Clear all indicators first
        document.querySelectorAll('th.sortable').forEach(header => {
            const iconSpan = header.querySelector('.sort-icon');
            if (iconSpan) {
                iconSpan.innerHTML = '';
                header.classList.remove('sorted-asc', 'sorted-desc');
            }
        });

        // Set the indicator for the current sort column
        if (this.sortColumn) {
            const activeHeader = document.querySelector(`th[data-sort="${this.sortColumn}"]`);
            if (activeHeader) {
                const iconSpan = activeHeader.querySelector('.sort-icon');
                if (iconSpan) {
                    const iconName = this.sortDirection === 'asc' ? 'arrow-up' : 'arrow-down';
                    iconSpan.innerHTML = `<i data-lucide="${iconName}" class="size-4"></i>`;
                    activeHeader.classList.add(`sorted-${this.sortDirection}`);

                    // Initialize the new icons
                    createIcons({ icons });
                }
            }
        }
    }

    initGenderSelect() {
        const genderSelectContainer = document.getElementById('genderSelect');
        if (genderSelectContainer) {
            const selectHtml = `
          <select class="form-select" required>
            <option value="">انتخاب جنسیت</option>
            <option value="Male">مرد</option>
            <option value="Female">زن</option>
            <option value="Other">دیگری</option>
          </select>
        `;
            genderSelectContainer.innerHTML = selectHtml;
        }
    }

    initPaginationEvents() {
        document.addEventListener('click', (e) => {
            // Handle pagination clicks
            if (e.target.closest('.pagination')) {
                const pageLink = e.target.closest('.page-link');
                if (pageLink) {
                    e.preventDefault();

                    if (pageLink.textContent.includes('قبلی')) {
                        this.goToPage(this.currentPage - 1);
                    } else if (pageLink.textContent.includes('بعدی')) {
                        this.goToPage(this.currentPage + 1);
                    } else {
                        const pageNum = parseInt(pageLink.textContent);
                        if (!isNaN(pageNum)) {
                            this.goToPage(pageNum);
                        }
                    }
                }
            }

            // Handle edit button clicks
            if (e.target.closest('.btn-sub-primary')) {
                const row = e.target.closest('tr');
                const itemId = parseInt(row.dataset.id);
                this.editItem(itemId);
            }

            // Handle delete button clicks (to open modal)
            if (e.target.closest('.btn-sub-danger')) {
                const row = e.target.closest('tr');
                e.target.closest('.btn-sub-danger').dataset.id = row.dataset.id;
            }
        });
    }

    handleSearch(query) {
        query = query.toLowerCase().trim();

        if (query === '') {
            this.filteredData = [...this.data];
        } else {
            this.filteredData = this.data.filter(item => {
                return (
                    item.parentName.toLowerCase().includes(query) ||
                    item.studentName.toLowerCase().includes(query) ||
                    item.email.toLowerCase().includes(query) ||
                    item.relation.toLowerCase().includes(query) ||
                    item.occupation.toLowerCase().includes(query)
                );
            });
        }

        // If we're sorting, maintain the sort after filtering
        if (this.sortColumn) {
            this.sortData();
        }

        this.currentPage = 1;
        this.renderTable();
    }

    handleFormSubmit(e) {
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);

        // Validate form
        const genderSelect = document.querySelector('#genderSelect select');
        const genderError = document.getElementById('genderSelectError');

        if (!genderSelect.value) {
            genderError.style.display = 'block';
            return;
        } else {
            genderError.style.display = 'none';
        }

        // Create new item object
        const newItem = {
            id: this.currentEditId || this.data.length + 1,
            parentName: formData.get('parentsInput'),
            studentName: formData.get('studentNameInput'),
            studentImage: document.getElementById('imagePreview').src || '',
            relation: formData.get('relationInput'),
            occupation: formData.get('occupationInput'),
            gender: genderSelect.value,
            email: formData.get('email'),
            phone: formData.get('phoneNumberInput'),
            address: this.currentEditId ? this.data.find(item => item.id === this.currentEditId).address : "مشخص نشده" // This field isn't in the form, added as default
        };

        if (this.currentEditId) {
            // Update existing item
            const index = this.data.findIndex(item => item.id === this.currentEditId);
            if (index !== -1) {
                this.data[index] = newItem;
            }
            this.currentEditId = null;
        } else {
            // Add new item
            this.data.unshift(newItem);
        }

        // Reset form
        form.reset();
        document.getElementById('imagePreview').style.display = 'none';
        document.getElementById('uploadIcon').style.display = 'block';

        // Close modal
        const modal = window.bootstrap.Modal.getInstance(document.getElementById('leadCreateModal'));
        modal.hide();

        // Update filtered data and render
        this.filteredData = [...this.data];

        // If we're sorting, maintain the sort after adding/editing
        if (this.sortColumn) {
            this.sortData();
        }

        this.renderTable();
    }

    handleImageUpload(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (event) {
                const imgPreview = document.getElementById('imagePreview');
                const uploadIcon = document.getElementById('uploadIcon');

                imgPreview.src = event.target.result;
                imgPreview.style.display = 'block';
                uploadIcon.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }
    }

    editItem(id) {
        const item = this.data.find(item => item.id === id);
        if (!item) return;

        this.currentEditId = id;

        // Fill form with data
        document.getElementById('parentsInput').value = item.parentName;
        document.getElementById('studentNameInput').value = item.studentName;
        document.getElementById('relationInput').value = item.relation;
        document.getElementById('occupationInput').value = item.occupation;
        document.getElementById('email').value = item.email;
        document.getElementById('phoneNumberInput').value = item.phone;

        // Set gender dropdown
        const genderSelect = document.querySelector('#genderSelect select');
        if (genderSelect) {
            genderSelect.value = item.gender; // 'Male', 'Female', 'Other'
        }

        // Set image preview if available
        const imgPreview = document.getElementById('imagePreview');
        const uploadIcon = document.getElementById('uploadIcon');

        if (item.studentImage) {
            imgPreview.src = item.studentImage;
            imgPreview.style.display = 'block';
            uploadIcon.style.display = 'none';
        } else {
            imgPreview.style.display = 'none';
            uploadIcon.style.display = 'block';
        }

        // Open modal
        const modal = new window.bootstrap.Modal(document.getElementById('leadCreateModal'));
        modal.show();
    }

    deleteItem(id) {
        id = parseInt(id);
        this.data = this.data.filter(item => item.id !== id);
        this.filteredData = this.filteredData.filter(item => item.id !== id);
        this.renderTable();
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredData.length / this.options.itemsPerPage);

        if (page < 1) page = 1;
        if (page > totalPages) page = totalPages;

        this.currentPage = page;
        this.renderTable();
    }

    renderTable() {
        const tableBody = document.querySelector('table tbody');
        if (!tableBody) return;

        // Calculate pagination
        const startIdx = (this.currentPage - 1) * this.options.itemsPerPage;
        const endIdx = startIdx + this.options.itemsPerPage;
        const paginatedItems = this.filteredData.slice(startIdx, endIdx);
        const totalPages = Math.ceil(this.filteredData.length / this.options.itemsPerPage);

        // Generate table rows
        let tableHTML = '';

        if (paginatedItems.length === 0) {
            tableHTML = `<tr><td colspan="9" class="text-center py-4">
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
                </td></tr>`;
        } else {
            paginatedItems.forEach(item => {
                tableHTML += `
            <tr data-id="${item.id}">
              <td>${item.parentName}</td>
              <td>
                <div class="d-flex align-items-center gap-3">
                  ${item.studentImage ?
                        `<img src="${item.studentImage}" loading="lazy" alt="" class="size-8 rounded-pill">` :
                        `<div class="size-8 rounded-pill bg-light-subtle fs-12 fw-semibold text-dark d-flex justify-content-center align-items-center">${item.studentName.split(' ').map(n => n[0]).join('')}</div>`
                    }
                  <h6 class="mb-0"><a href="apps-school-students-overview.html" class="text-body">${item.studentName}</a></h6>
                </div>
              </td>
              <td>${item.relation}</td>
              <td>${item.occupation}</td>
              <td>${genderMapping[item.gender] || item.gender}</td>
              <td>${item.email}</td>
              <td>${item.phone}</td>
              <td>${item.address}</td>
              <td>
                <div class="d-flex align-items-center gap-2">
                  <button class="btn btn-sub-primary size-8 btn-icon"><i class="ri-pencil-line"></i></button>
                  <button class="btn btn-sub-danger size-8 btn-icon" data-bs-toggle="modal" data-bs-target="#deleteModal" data-id="${item.id}"><i class="ri-delete-bin-line"></i></button>
                </div>
              </td>
            </tr>
          `;
            });
        }

        tableBody.innerHTML = tableHTML;

        // Update pagination info
        const paginationInfo = document.querySelector('#paginationInfo p');
        if (paginationInfo) {
            const start = this.filteredData.length > 0 ? startIdx + 1 : 0;
            const end = Math.min(endIdx, this.filteredData.length);
            paginationInfo.innerHTML = `نمایش <b class="me-1">${start}-${end}</b>از<b class="ms-1">${this.filteredData.length}</b> نتیجه`;
        }

        // Generate pagination controls
        const paginationUl = document.querySelector('.pagination');
        if (paginationUl) {
            let paginationHTML = `
          <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>
          </li>
        `;

            for (let i = 1; i <= totalPages; i++) {
                paginationHTML += `
            <li class="page-item ${this.currentPage === i ? 'active' : ''}">
              <a class="page-link" href="#!">${i}</a>
            </li>
          `;
            }

            paginationHTML += `
          <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>
          </li>
        `;

            paginationUl.innerHTML = paginationHTML;

            createIcons({ icons });
        }

        // Update sort indicators after rendering table
        if (this.sortColumn) {
            this.updateSortIndicators();
        }
    }

    // Export data as JSON
    exportData() {
        return JSON.stringify(this.data, null, 2);
    }

    // Import data from JSON
    importData(jsonString) {
        try {
            const parsedData = JSON.parse(jsonString);
            if (Array.isArray(parsedData)) {
                this.data = parsedData;
                this.filteredData = [...this.data];
                this.currentPage = 1;
                this.renderTable();
                return true;
            }
            return false;
        } catch (e) {
            console.error("Error importing data:", e);
            return false;
        }
    }
}

// Initialize the table manager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    // Create an instance of TableManager
    const parentsTable = new TableManager('parent-table-container', {
        itemsPerPage: 10,
        searchField: 'searchInvoiceInput',
        addBtnModal: 'leadCreateModal',
        deleteModal: 'deleteModal'
    });

    // Make it available globally for debugging
    window.parentsTable = parentsTable;
});