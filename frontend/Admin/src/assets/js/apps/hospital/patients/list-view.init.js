import { icons, createIcons } from "lucide";


//Insurance select
VirtualSelect.init({
    ele: "#insuranceSelect",
    options: [
        { label: "بله", value: "Yes" },
        { label: "نه", value: "No" },
    ],
});

//City select
VirtualSelect.init({
    ele: "#citySelect",
    options: [
        { label: "ایران", value: "Iran" },
        { label: "آرژانتین", value: "Argentina" },
        { label: "بلژیک", value: "Belgium" },
        { label: "مکزیک", value: "Mexico" },
        { label: "روسیه", value: "Russia" },
        { label: "دانمارک", value: "Denmark" },
        { label: "سودان", value: "Sudan" },
        { label: "اسپانیا", value: "Spain" },
        { label: "آلمان", value: "Germany" },
        { label: "فرانسه", value: "France" },
        { label: "نامبیا", value: "Namibia" },
        { label: "لهستان", value: "Brazil" },
        { label: "لهستان", value: "Poland" },
        { label: "صربستان", value: "Serbia" },
        { label: "مالزی", value: "Malaysia" },
        { label: "نروژ", value: "Norway" },
        { label: "رومانی", value: "Romania" },
        { label: "آمریکا", value: "USA" },
        { label: "کانادا", value: "Canada" },
    ],
});

//Gender select
VirtualSelect.init({
    ele: "#genderSelect",
    options: [
        { label: "مرد", value: "Male" },
        { label: "زن", value: "Female" },
        { label: "دیگری", value: "Others" },
    ],
});

//Doctors select
VirtualSelect.init({
    ele: "#doctorsSelect",
    options: [
        { label: "دکتر مایکل", value: "Dr. Michael" },
        { label: "دکتر سارا", value: "Dr. Sarah" },
        { label: "دکتر رابرت", value: "Dr. Robert" },
        { label: "دکتر امیلی", value: "Dr. Emily" },
        { label: "دکتر جیمز", value: "Dr. James" },
        { label: "دکتر اولیویا", value: "Dr. Olivia" },
        { label: "دکتر دیوید", value: "Dr. David" },
        { label: "دکتر سوفیا", value: "Dr. Sophia" },
        { label: "دکتر ویلیام", value: "Dr. William" },
        { label: "دکتر شارلوت", value: "Dr. Charlotte" },
    ],
});

//Patient Status select
VirtualSelect.init({
    ele: "#patientStatusSelect",
    options: [
        { label: "تازه", value: "New" },
        { label: "پیگیری", value: "Follow Up" },
        { label: "قدیمی", value: "Old" },
    ],
});

/**
 * TableManager - A class to manage data tables with search, pagination and delete functionality
 */
class TableManager {
    /**
     * Initialize the TableManager
     * @param {Object} config - Configuration object
     * @param {Array} config.data - Array of data objects to display in the table
     * @param {string} config.containerId - ID of the container element to render the table
     * @param {number} config.itemsPerPage - Number of items to show per page
     * @param {Array} config.searchFields - Fields to search in
     */
    constructor(config) {
        this.data = config.data || [];
        this.container = document.getElementById(config.containerId);
        this.itemsPerPage = config.itemsPerPage || 16;
        this.currentPage = 1;
        this.searchFields = config.searchFields || [];
        this.filteredData = [...this.data];

        // Bind methods to preserve 'this' context
        this.renderTable = this.renderTable.bind(this);
        this.renderPagination = this.renderPagination.bind(this);
        this.handleSearch = this.handleSearch.bind(this);
        this.goToPage = this.goToPage.bind(this);
        this.deleteItem = this.deleteItem.bind(this);

        // Setup event listeners
        this.setupEventListeners();

        // Initial render
        this.renderTable();
        this.renderPagination();
    }

    /**
     * Setup event listeners for search and other interactions
     */
    setupEventListeners() {
        // Search input listener
        const searchInput = document.getElementById('searchLeaveInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.handleSearch);
        }

        // Delete button listener - using event delegation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-btn') ||
                (e.target.closest('.delete-btn') && e.target.tagName === 'I')) {
                const id = e.target.closest('.delete-btn').dataset.id;
                // Show confirmation modal
                const deleteModal = new window.bootstrap.Modal(document.getElementById('deleteModal'));
                deleteModal.show();

                // Setup confirm delete button
                const confirmDeleteBtn = document.querySelector('#deleteModal .btn-danger');
                confirmDeleteBtn.onclick = () => {
                    this.deleteItem(id);
                    deleteModal.hide();
                };
            }
        });
    }

    /**
     * Render the table with current data and pagination
     */
    renderTable() {
        if (!this.container) return;

        // Calculate pagination values
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const paginatedData = this.filteredData.slice(startIndex, endIndex);

        // Clear existing content
        const rowContainer = document.querySelector('#patientTable');
        rowContainer.innerHTML = '';

        // If no data, show message
        if (paginatedData.length === 0) {
            rowContainer.innerHTML = `
                <td colspan="6" class="text-center py-4">
                    <div class="d-flex flex-column align-items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" class="mx-auto size-12" viewBox="0 0 48 48">
                            <linearGradient id="SVGID_1" x1="34.598" x2="15.982" y1="15.982" y2="34.598" gradientUnits="userSpaceOnUse">
                                <stop offset="0" stop-color="#60e8fe"></stop>
                                <stop offset=".033" stop-color="#6ae9fe"></stop>
                                <stop offset=".197" stop-color="#97f0fe"></stop>
                                <stop offset=".362" stop-color="#bdf5ff"></stop>
                                <stop offset=".525" stop-color="#dafaff"></stop>
                                <stop offset=".687" stop-color="#eefdff"></stop>
                                <stop offset=".846" stop-color="#fbfeff"></stop>
                                <stop offset="1" stop-color="#ffffff"></stop>
                            </linearGradient>
                            <path fill="url(#SVGID_1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748
                                c0-7.27-5.894-13.164-13.164-13.164S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164
                                c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331c1.715,1.715,4.496,1.715,6.211,0
                                C41.751,38.321,41.751,35.541,40.036,33.826z">
                            </path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round"
                                stroke-miterlimit="10" stroke-width="3"
                                d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0l-4.331-4.331">
                            </path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round"
                                stroke-miterlimit="10" stroke-width="3"
                                d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912">
                            </path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round"
                                stroke-miterlimit="10" stroke-width="3"
                                d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814">
                            </path>
                        </svg>
                        <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                        <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                    </div>
                </td>
            `;
            return;
        }

        // Generate card for each patient
        paginatedData.forEach(patient => {
            const patientCard = document.createElement('div');
            patientCard.className = 'col-md-6 col-xxl-3';
            patientCard.innerHTML = `
          <div class="card" data-id="${patient.id}">
            <div class="card-body">
              <div class="dropdown float-end">
                <a href="#!" class="link link-custom-primary" type="button" data-bs-toggle="dropdown" aria-expanded="true" title="dropdown-button">
                  <i class="ri-more-fill"></i>
                </a>
                <ul class="dropdown-menu dropdown-menu-end">
                  <li><a class="dropdown-item" href="#!"><i class="me-2 ri-eye-line"></i><span>نمای کلی</span></a></li>
                  <li><a class="dropdown-item" href="#!"><i class="me-2 ri-pencil-line"></i>ویرایش</a></li>
                  <li><a class="dropdown-item delete-btn" data-id="${patient.id}" href="#!"><i class="me-2 ri-delete-bin-line"></i><span>حذف</span></a></li>
                </ul>
              </div>
              <div class="d-flex align-items-center gap-3">
                <img src="${patient.avatar}" loading="lazy" alt="" class="rounded-2 flex-shrink-0 size-20">
                <div class="flex-grow-1 overflow-hidden">
                  <h6 class="mb-2"><a href="#!" class="text-reset">${patient.name}</a></h6>
                  <p class="mb-1 text-muted text-truncate"><i class="ri-mail-line ms-2"></i><span>${patient.email}</span></p>
                  <p class="text-muted"><i class="ri-phone-line ms-2"></i><span>${patient.phone}</span></p>
                </div>
              </div>
            </div>
          </div>
        `;

            rowContainer.appendChild(patientCard);
        });

        // Update the results count
        this.updateResultsCount();
    }

    /**
     * Update the results count display
     */
    updateResultsCount() {
        const resultsElement = document.querySelector('#showingResults');
        if (resultsElement) {
            const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
            const endIndex = Math.min(startIndex + this.itemsPerPage - 1, this.filteredData.length);
            resultsElement.innerHTML = `نمایش <b class="me-1">${startIndex}-${endIndex}</b>از<b class="ms-1">${this.filteredData.length}</b> نتیجه`;
        }
    }

    /**
     * Render pagination controls
     */
    renderPagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        const paginationContainer = document.querySelector('.pagination');

        if (!paginationContainer) return;

        paginationContainer.innerHTML = '';

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
        paginationContainer.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${this.currentPage === i ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
            pageLi.addEventListener('click', (e) => {
                e.preventDefault();
                this.goToPage(i);
            });
            paginationContainer.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < totalPages) {
                this.goToPage(this.currentPage + 1);
            }
        });
        paginationContainer.appendChild(nextLi);

        createIcons({ icons });
    }

    /**
     * Handle search functionality
     * @param {Event} e - Input event
     */
    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase().trim();

        if (!searchTerm) {
            this.filteredData = [...this.data];
        } else {
            this.filteredData = this.data.filter(item => {
                return this.searchFields.some(field => {
                    const value = item[field];
                    return value && String(value).toLowerCase().includes(searchTerm);
                });
            });
        }

        // Reset to first page and re-render
        this.currentPage = 1;
        this.renderTable();
        this.renderPagination();
    }

    /**
     * Navigate to specific page
     * @param {number} pageNumber - Page to navigate to
     */
    goToPage(pageNumber) {
        this.currentPage = pageNumber;
        this.renderTable();
        this.renderPagination();

        // Scroll to top of container
        if (this.container) {
            this.container.scrollIntoView({ behavior: 'smooth' });
        }
    }

    /**
     * Delete an item from the data
     * @param {string|number} id - ID of the item to delete
     */
    deleteItem(id) {
        // Remove from original data
        this.data = this.data.filter(item => item.id !== id);

        // Remove from filtered data
        this.filteredData = this.filteredData.filter(item => item.id !== id);

        // Adjust current page if necessary
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        if (this.currentPage > totalPages && totalPages > 0) {
            this.currentPage = totalPages;
        }

        // Re-render
        this.renderTable();
        this.renderPagination();
    }

    /**
     * Add new item to the data
     * @param {Object} item - Item to add
     */
    addItem(item) {
        // Add ID if not present
        if (!item.id) {
            item.id = this.generateUniqueId();
        }

        // Add to data
        this.data.push(item);
        this.filteredData = [...this.data];

        // Re-render
        this.renderTable();
        this.renderPagination();
    }

    /**
     * Generate unique ID for new items
     * @return {string} Unique ID
     */
    generateUniqueId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * Update an existing item
     * @param {string|number} id - ID of item to update
     * @param {Object} updatedData - New data for the item
     */
    updateItem(id, updatedData) {
        // Update in original data
        this.data = this.data.map(item => {
            if (item.id === id) {
                return { ...item, ...updatedData };
            }
            return item;
        });

        // Update in filtered data
        this.filteredData = this.filteredData.map(item => {
            if (item.id === id) {
                return { ...item, ...updatedData };
            }
            return item;
        });

        // Re-render
        this.renderTable();
    }
}

// Sample data
const patientData = [
    { id: "1", name: "آلیس جانسون", email: "alice.johnson1@example.com", phone: "+33 1 42 68 53 00", avatar: "assets/images/avatar/user-1.png" },
    { id: "2", name: "آلیس جانسون", email: "alice.johnson2@example.com", phone: "+44 20 7946 0958", avatar: "assets/images/avatar/user-2.png" },
    { id: "3", name: "مایکل وینسون", email: "michael.wilson3@example.com", phone: "+61 2 9374 4000", avatar: "assets/images/avatar/user-3.png" },
    { id: "4", name: "آلیس جانسون", email: "alice.johnson4@example.com", phone: "+1 555 123 4567", avatar: "assets/images/avatar/user-4.png" },
    { id: "5", name: "سارا مور", email: "sarah.moore5@example.com", phone: "+44 20 7946 0958", avatar: "assets/images/avatar/user-5.png" },
    { id: "6", name: "جین اسمیت", email: "jane.smith6@example.com", phone: "+33 1 42 68 53 00", avatar: "assets/images/avatar/user-6.png" },
    { id: "7", name: "مایکل وینسون", email: "michael.wilson7@example.com", phone: "+81 3 1234 5678", avatar: "assets/images/avatar/user-7.png" },
    { id: "8", name: "رابرت براون", email: "robert.brown8@example.com", phone: "+1 555 123 4567", avatar: "assets/images/avatar/user-8.png" },
    { id: "9", name: "مایکل وینسون", email: "michael.wilson9@example.com", phone: "+61 3 9876 5432", avatar: "assets/images/avatar/user-9.png" },
    { id: "10", name: "دیوید تیلور", email: "david.taylor10@example.com", phone: "+34 91 123 45 67", avatar: "assets/images/avatar/user-10.png" },
    { id: "11", name: "امیلی دیویس", email: "emily.davis11@example.com", phone: "+1 415 555 1234", avatar: "assets/images/avatar/user-11.png" },
    { id: "12", name: "دیوید تیلور", email: "david.taylor12@example.com", phone: "+44 20 7946 0958", avatar: "assets/images/avatar/user-12.png" },
    { id: "13", name: "جین اسمیت", email: "jane.smith13@example.com", phone: "+1 555 123 4567", avatar: "assets/images/avatar/user-13.png" },
    { id: "14", name: "جین اسمیت", email: "jane.smith14@example.com", phone: "+81 3 1234 5678", avatar: "assets/images/avatar/user-14.png" },
    { id: "15", name: "توماس مارتین", email: "thomas.martin15@example.com", phone: "+49 30 123456", avatar: "assets/images/avatar/user-15.png" },
    { id: "16", name: "سارا مور", email: "sarah.moore16@example.com", phone: "+34 91 123 45 67", avatar: "assets/images/avatar/user-16.png" },
    { id: "17", name: "لیسا اندرسون", email: "lisa.anderson17@example.com", phone: "+33 1 42 68 53 00", avatar: "assets/images/avatar/user-17.png" },
    { id: "18", name: "لیسا اندرسون", email: "lisa.anderson18@example.com", phone: "+44 20 7946 0958", avatar: "assets/images/avatar/user-18.png" },
    { id: "19", name: "توماس مارتین", email: "thomas.martin19@example.com", phone: "+61 2 9374 4000", avatar: "assets/images/avatar/user-19.png" },
    { id: "20", name: "دیوید تیلور", email: "david.taylor20@example.com", phone: "+49 89 1234567", avatar: "assets/images/avatar/user-20.png" },
    { id: "21", name: "مایکل وینسون", email: "michael.wilson21@example.com", phone: "+1 415 555 1234", avatar: "assets/images/avatar/user-21.png" },
    { id: "22", name: "لیسا اندرسون", email: "lisa.anderson22@example.com", phone: "+34 91 123 45 67", avatar: "assets/images/avatar/user-22.png" },
    { id: "23", name: "امیلی دیویس", email: "emily.davis23@example.com", phone: "+61 3 9876 5432", avatar: "assets/images/avatar/user-23.png" },
    { id: "24", name: "امیلی دیویس", email: "emily.davis24@example.com", phone: "+49 30 123456", avatar: "assets/images/avatar/user-24.png" },
    { id: "25", name: "رابرت براون", email: "robert.brown25@example.com", phone: "+81 3 1234 5678", avatar: "assets/images/avatar/user-25.png" },
    { id: "26", name: "سارا مور", email: "sarah.moore26@example.com", phone: "+61 2 9374 4000", avatar: "assets/images/avatar/user-26.png" },
    { id: "27", name: "جان دو", email: "john.doe27@example.com", phone: "+49 89 1234567", avatar: "assets/images/avatar/user-27.png" }
];


// Initialize TableManager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the table manager
    const tableManager = new TableManager({
        data: patientData,
        containerId: 'patientTableContainer', // Ensure this ID is on your container
        itemsPerPage: 16,
        searchFields: ['name', 'email', 'phone']
    });

    // Make tableManager accessible globally for debugging
    window.tableManager = tableManager;
});