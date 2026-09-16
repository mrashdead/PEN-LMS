import { createIcons, icons } from 'lucide';


/**
 * AppointmentManager - Core class to handle all appointment table operations
 */
class AppointmentManager {
    constructor() {
        this.appointments = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.totalPages = 0;
        this.tableBody = document.querySelector('tbody');

        // Fixed selectors - this was the main issue
        this.paginationContainer = document.querySelector('.pagination'); // Changed from '.pagination ul'
        this.resultsInfo = document.getElementById('showingResults');

        // Modals
        this.overviewModal = document.getElementById('overviewModal');
        this.deleteModal = document.getElementById('deleteModal');
        this.currentAppointmentId = null; // Added to track which appointment is being deleted

        // Initialize 
        this.init();
    }

    /**
     * Initialize the appointment manager
     */
    init() {
        // Load appointment data
        this.loadAppointments();

        // Set up event listeners
        this.setupEventListeners();
    }

    /**
     * Load appointments from data source (mock data for now)
     */
    loadAppointments() {
        // In a real application, this would fetch from an API
        this.appointments = [
            {
                id: 1,
                patientName: 'سارا وایت',
                patientInitials: 'سو',
                avatar: null, // Uses initials
                date: '18 خرداد 1403',
                time: '14:00 - 15:00',
                treatment: 'چکاپ روتین',
                doctor: 'دکتر مایکل جانسون',
                status: 'در حال بررسی'
            },
            {
                id: 2,
                patientName: 'دانیل آدامز',
                patientInitials: 'دآ',
                avatar: 'assets/images/avatar/user-14.png',
                date: '19 خرداد 1403',
                time: '15:00 - 16:00',
                treatment: 'ارزیابی وضعیت پوست',
                doctor: 'سارا ایونز',
                status: 'جدید'
            },
            {
                id: 3,
                patientName: 'اولیویا لوئیز',
                patientInitials: 'ال',
                avatar: null,
                date: '20 خرداد 1403',
                time: '11:30 - 12:30',
                treatment: 'معاینه بینایی',
                doctor: 'سارا ایونز',
                status: 'جدید'
            },
            {
                id: 4,
                patientName: 'جیمز براون',
                patientInitials: 'جب',
                avatar: null,
                date: '21 خرداد 1403',
                time: '10:00 - 11:00',
                treatment: 'تمیز کردن دندان',
                doctor: 'دکتر امیلی کارتر',
                status: 'در حال بررسی'
            },
            {
                id: 5,
                patientName: 'لیندا تیلور',
                patientInitials: 'لت',
                avatar: 'assets/images/avatar/user-18.png',
                date: '22 خرداد 1403',
                time: '13:00 - 14:00',
                treatment: 'مشاوره قلب و عروق',
                doctor: 'رابرت هریس',
                status: 'تأیید شده'
            },
            {
                id: 6,
                patientName: 'سوفیا مارتینز',
                patientInitials: 'سم',
                avatar: 'assets/images/avatar/user-17.png',
                date: '23 خرداد 1403',
                time: '09:00 - 10:00',
                treatment: 'آزمایش خون',
                doctor: 'دکتر مایکل جانسون',
                status: 'انجام شده'
            },
            {
                id: 7,
                patientName: 'لیام اندرسون',
                patientInitials: 'لا',
                avatar: null,
                date: '24 خرداد 1403',
                time: '11:00 - 12:00',
                treatment: 'بیوپسی پوست',
                doctor: 'سارا ایونز',
                status: 'در حال بررسی'
            },
            {
                id: 8,
                patientName: 'اما ویلسون',
                patientInitials: 'او',
                avatar: 'assets/images/avatar/user-20.png',
                date: '25 خرداد 1403',
                time: '14:00 - 15:00',
                treatment: 'مشاوره ارتوپدی',
                doctor: 'دکتر امیلی کارتر',
                status: 'تأیید شده'
            },
            {
                id: 9,
                patientName: 'نورا دیویس',
                patientInitials: 'ند',
                avatar: null,
                date: '26 خرداد 1403',
                time: '13:00 - 14:00',
                treatment: 'چکاپ قلب',
                doctor: 'رابرت هریس',
                status: 'جدید'
            },
            {
                id: 10,
                patientName: 'آوا جانسون',
                patientInitials: 'آج',
                avatar: null,
                date: '27 خرداد 1403',
                time: '15:00 - 16:00',
                treatment: 'فیزیوتراپی',
                doctor: 'دکتر مایکل جانسون',
                status: 'در حال بررسی'
            },
            // Additional appointments for pagination demonstration
            {
                id: 11,
                patientName: 'ویلیام تامپسون',
                patientInitials: 'وت',
                avatar: null,
                date: '28 خرداد 1403',
                time: '10:30 - 11:30',
                treatment: 'مشاوره عمومی',
                doctor: 'دکتر مایکل جانسون',
                status: 'در حال بررسی'
            },
            {
                id: 12,
                patientName: 'میا رابرتز',
                patientInitials: 'مر',
                avatar: null,
                date: '29 خرداد 1403',
                time: '09:00 - 10:00',
                treatment: 'معاینه عصبی',
                doctor: 'دکتر امیلی کارتر',
                status: 'جدید'
            },
            // Add more appointments as needed to match the "27 Results" from the pagination
        ];

        // Calculate total pages
        this.totalPages = Math.ceil(this.appointments.length / this.itemsPerPage);

        // Render the first page
        this.renderPage(1);

        // Update pagination
        this.renderPagination();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Delegation for pagination clicks
        if (this.paginationContainer) {
            this.paginationContainer.addEventListener('click', (e) => {
                e.preventDefault();

                // Check if a page link was clicked
                if (e.target.classList.contains('page-link') || e.target.parentElement.classList.contains('page-link')) {
                    const pageElement = e.target.classList.contains('page-link') ? e.target : e.target.parentElement;
                    const pageText = pageElement.textContent.trim();

                    // Handle previous, next and numbered pages
                    if (pageText.includes('قبلی')) {
                        if (this.currentPage > 1) {
                            this.goToPage(this.currentPage - 1);
                        }
                    } else if (pageText.includes('بعدی')) {
                        if (this.currentPage < this.totalPages) {
                            this.goToPage(this.currentPage + 1);
                        }
                    } else {
                        // Numbered page
                        const pageNum = parseInt(pageText);
                        if (!isNaN(pageNum)) {
                            this.goToPage(pageNum);
                        }
                    }
                }
            });
        }

        // Table action buttons delegation
        if (this.tableBody) {
            this.tableBody.addEventListener('click', (e) => {
                // Find the closest action button
                const actionBtn = e.target.closest('.btn');
                if (!actionBtn) return;

                // Get the appointment row
                const row = actionBtn.closest('tr');
                if (!row) return;

                // Get the appointment ID (we'll use row index for this demo)
                const rowIndex = Array.from(this.tableBody.querySelectorAll('tr')).indexOf(row);
                const startIndex = (this.currentPage - 1) * this.itemsPerPage;
                const appointmentId = startIndex + rowIndex;
                const appointment = this.appointments[appointmentId];

                // Handle different actions
                if (actionBtn.classList.contains('btn-sub-primary')) {
                    // View button clicked - show appointment details in overview modal
                    this.showAppointmentDetails(appointment);
                } else if (actionBtn.classList.contains('btn-light')) {
                    // Edit button clicked
                    this.editAppointment(appointment);
                } else if (actionBtn.classList.contains('btn-sub-danger')) {
                    // Delete button clicked - show delete confirmation
                    this.currentAppointmentId = appointmentId;

                    // Setup delete confirmation
                    const deleteConfirmBtn = this.deleteModal.querySelector('.btn-danger');
                    // Remove previous event listeners
                    const newDeleteBtn = deleteConfirmBtn.cloneNode(true);
                    deleteConfirmBtn.parentNode.replaceChild(newDeleteBtn, deleteConfirmBtn);

                    // Add new event listener
                    newDeleteBtn.addEventListener('click', () => {
                        this.deleteAppointment(this.currentAppointmentId);
                    });
                }
            });
        }
    }

    /**
     * Navigate to a specific page
     * @param {Number} pageNum - The page number to navigate to
     */
    goToPage(pageNum) {
        if (pageNum < 1 || pageNum > this.totalPages) return;

        this.currentPage = pageNum;
        this.renderPage(pageNum);
        this.updatePaginationActive();
    }

    /**
     * Render appointments for a specific page
     * @param {Number} pageNum - The page number to render
     */
    renderPage(pageNum) {
        if (!this.tableBody) return;

        // Clear current content
        this.tableBody.innerHTML = '';

        // Calculate start and end index
        const startIndex = (pageNum - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.appointments.length);

        // Update results info
        this.updateResultsInfo(startIndex, endIndex);

        // Render appointments for this page
        for (let i = startIndex; i < endIndex; i++) {
            const appointment = this.appointments[i];
            const row = this.createAppointmentRow(appointment);
            this.tableBody.appendChild(row);
        }
    }

    /**
     * Create HTML row for an appointment
     * @param {Object} appointment - The appointment data
     * @returns {HTMLTableRowElement} - The created table row
     */
    createAppointmentRow(appointment) {
        const row = document.createElement('tr');

        // Status badge class based on status
        let statusClass = '';
        switch (appointment.status) {
            case 'جدید':
                statusClass = 'bg-primary-subtle text-primary border border-primary-subtle';
                break;
            case 'در حال بررسی':
                statusClass = 'bg-light-subtle text-muted border border-dark-subtle';
                break;
            case 'تأیید شده':
                statusClass = 'bg-success-subtle text-success border border-success-subtle';
                break;
            case 'انجام شده':
                statusClass = 'bg-secondary-subtle text-secondary border border-secondary-subtle';
                break;
            default:
                statusClass = 'bg-light-subtle text-muted border border-dark-subtle';
        }

        // Create patient avatar or initials
        let avatarHtml = '';
        if (appointment.avatar) {
            avatarHtml = `<img src="${appointment.avatar}" loading="lazy" alt="" class="size-8 rounded-circle">`;
        } else {
            avatarHtml = `<div class="size-8 rounded-circle bg-light-subtle avatar text-muted fw-semibold fs-12">${appointment.patientInitials}</div>`;
        }

        // Fill in the row
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center gap-3">
                    ${avatarHtml}
                    <h6 class="mb-0"><a href="#!" class="text-body">${appointment.patientName}</a></h6>
                </div>
            </td>
            <td>${appointment.date}</td>
            <td>${appointment.time}</td>
            <td>${appointment.treatment}</td>
            <td>${appointment.doctor}</td>
            <td>
                <span class="badge ${statusClass}">${appointment.status}</span>
            </td>
            <td>
                <div class="d-flex align-items-center gap-2">
                    <button class="btn btn-sub-primary size-8 btn-icon" data-bs-toggle="modal" data-bs-target="#overviewModal"><i class="ri-eye-line"></i></button>
                    <button class="btn btn-light size-8 btn-icon"><i class="ri-pencil-line"></i></button>
                    <button class="btn btn-sub-danger size-8 btn-icon" data-bs-toggle="modal" data-bs-target="#deleteModal"><i class="ri-delete-bin-line"></i></button>
                </div>
            </td>
        `;

        return row;
    }

    /**
     * Render pagination controls
     */
    renderPagination() {
        if (!this.paginationContainer) return;

        // Create the UL element if it doesn't exist
        let paginationUl = this.paginationContainer.querySelector('ul');
        if (!paginationUl) {
            paginationUl = document.createElement('ul');
            paginationUl.className = 'pagination justify-content-center justify-content-md-end mb-0';
            this.paginationContainer.appendChild(paginationUl);
        }

        // Clear current pagination
        paginationUl.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        paginationUl.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= Math.min(this.totalPages, 3); i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
            paginationUl.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        paginationUl.appendChild(nextLi);

        createIcons({ icons });
    }

    /**
     * Update active state in pagination
     */
    updatePaginationActive() {
        if (!this.paginationContainer) return;

        const paginationUl = this.paginationContainer.querySelector('ul');
        if (!paginationUl) return;

        // Update the previous button
        const prevBtn = paginationUl.querySelector('li:first-child');
        if (prevBtn) {
            if (this.currentPage === 1) {
                prevBtn.classList.add('disabled');
            } else {
                prevBtn.classList.remove('disabled');
            }
        }

        // Update page number buttons
        const pageButtons = paginationUl.querySelectorAll('li:not(:first-child):not(:last-child)');
        pageButtons.forEach((btn, index) => {
            const pageNum = index + 1;
            if (pageNum === this.currentPage) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update the next button
        const nextBtn = paginationUl.querySelector('li:last-child');
        if (nextBtn) {
            if (this.currentPage === this.totalPages) {
                nextBtn.classList.add('disabled');
            } else {
                nextBtn.classList.remove('disabled');
            }
        }
    }

    /**
     * Update the results info text
     * @param {Number} startIndex - The start index
     * @param {Number} endIndex - The end index
     */
    updateResultsInfo(startIndex, endIndex) {
        if (!this.resultsInfo) return;

        const startDisplay = startIndex + 1;
        const endDisplay = endIndex;
        this.resultsInfo.innerHTML = `نمایش <b class="me-1">${startDisplay}-${endDisplay}</b>از<b class="ms-1">${this.appointments.length}</b> نتیجه`;
    }

    /**
     * Show appointment details in the overview modal
     * @param {Object} appointment - The appointment to show details for
     */
    showAppointmentDetails(appointment) {
        if (!this.overviewModal) return;

        const patientInfo = this.overviewModal.querySelector('#patientInfo');
        const overViewStatus = this.overviewModal.querySelector('#overViewStatus');
        const doctorInfo = this.overviewModal.querySelector('#doctorInfo');

        if (!patientInfo || !overViewStatus || !doctorInfo) return;

        // Update status badge
        overViewStatus.textContent = appointment.status;
        overViewStatus.className = '';

        // Set appropriate status class
        switch (appointment.status) {
            case 'جدید':
                overViewStatus.className = 'badge bg-primary-subtle text-primary border border-primary-subtle';
                break;
            case 'در حال بررسی':
                overViewStatus.className = 'badge bg-light-subtle text-muted border border-dark-subtle';
                break;
            case 'تأیید شده':
                overViewStatus.className = 'badge bg-success-subtle text-success border border-success-subtle';
                break;
            case 'انجام شده':
                overViewStatus.className = 'badge bg-secondary-subtle text-secondary border border-secondary-subtle';
                break;
        }

        // Update patient info
        let avatarHtml = '';
        if (appointment.avatar) {
            avatarHtml = `<img src="${appointment.avatar}" loading="lazy" alt="" class="size-10 rounded-circle flex-shrink-0">`;
        } else {
            avatarHtml = `<div class="size-10 rounded-circle bg-light-subtle avatar text-muted fw-semibold fs-12">${appointment.patientInitials}</div>`;
        }

        patientInfo.innerHTML = `
            ${avatarHtml}
            <div class="flex-grow-1">
                <h6 class="mb-1">${appointment.patientName}</h6>
                <p class="text-muted">${appointment.treatment}</p>
            </div>
        `;

        // Update date and time info
        const dateTimeInfo = this.overviewModal.querySelectorAll('.modal-body > div')[1];
        if (dateTimeInfo) {
            const dateTimeH6 = dateTimeInfo.querySelector('h6');
            const dateTimeP = dateTimeInfo.querySelector('p');

            if (dateTimeH6) dateTimeH6.textContent = appointment.date;
            if (dateTimeP) dateTimeP.textContent = appointment.time;
        }

        // Update doctor info
        const doctorH6 = doctorInfo.querySelector('h6');
        if (doctorH6) doctorH6.textContent = appointment.doctor;
    }

    /**
     * Delete an appointment
     * @param {Number} index - The index of the appointment to delete
     */
    deleteAppointment(index) {
        // Remove the appointment
        this.appointments.splice(index, 1);

        // Recalculate total pages
        this.totalPages = Math.ceil(this.appointments.length / this.itemsPerPage);

        // Adjust current page if needed
        if (this.currentPage > this.totalPages) {
            this.currentPage = this.totalPages;
        }

        if (this.totalPages === 0) {
            this.totalPages = 1;
        }

        // Close the modal
        if (this.deleteModal && typeof bootstrap !== 'undefined') {
            const modalInstance = window.bootstrap.Modal.getInstance(this.deleteModal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }

        // Re-render page and pagination
        this.renderPage(this.currentPage);
        this.renderPagination();
    }

    /**
     * Edit an appointment (stub for now)
     * @param {Object} appointment - The appointment to edit
     */
    editAppointment(appointment) {
        alert(`ویرایش نوبت‌دهی برای ${appointment.patientName}`);
    }
}

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the appointment manager
    const appointmentManager = new AppointmentManager();

    // Store in global scope for debugging purposes
    window.appointmentManager = appointmentManager;
});