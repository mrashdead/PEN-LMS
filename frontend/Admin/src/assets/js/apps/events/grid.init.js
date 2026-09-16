
import { icons, createIcons } from "lucide";


// Status Select
VirtualSelect.init({
    ele: "#StatusSelect",
    options: [
        { label: "منتشر شده", value: "Published" },
        { label: "به زودی", value: "Coming Soon" },
        { label: "منقضی شده", value: "Expired" }
    ]
});

// Event Type Select
VirtualSelect.init({
    ele: "#eventTypeSelect",
    options: [
        { label: "آفلاین", value: "Offline" },
        { label: "آنلاین", value: "Online" }
    ]
});
/**
 * GridManager - A class to manage event grid functionality
 * Handles data display, filtering, pagination, CRUD operations
 */
class GridManager {
    constructor(options = {}) {
        // Main container selector
        this.containerId = options.containerId || 'event-grid-container';
        this.container = document.getElementById(this.containerId);

        // Pagination settings
        this.itemsPerPage = options.itemsPerPage || 6;
        this.currentPage = 1;

        // Sorting and filtering
        this.sortBy = options.sortBy || null;
        this.sortDirection = options.sortDirection || 'asc';
        this.filterValue = '';

        // Data and state
        this.events = [];
        this.filteredEvents = [];
        this.selectedEvent = null;

        // Bind methods to maintain 'this' context
        this.init = this.init.bind(this);
        this.renderEvents = this.renderEvents.bind(this);
        this.renderPagination = this.renderPagination.bind(this);
        this.handlePageChange = this.handlePageChange.bind(this);
        this.handleSort = this.handleSort.bind(this);
        this.handleFilter = this.handleFilter.bind(this);
        this.openAddModal = this.openAddModal.bind(this);
        this.openEditModal = this.openEditModal.bind(this);
        this.openViewModal = this.openViewModal.bind(this);
        this.deleteEvent = this.deleteEvent.bind(this);
        this.saveEvent = this.saveEvent.bind(this);
        this.updateEventCounter = this.updateEventCounter.bind(this);
        this.setupListeners = this.setupListeners.bind(this);
    }

    /**
     * Initialize the GridManager
     * @param {Array} initialData - Initial event data
     */
    init(initialData = []) {
        // Load events
        this.events = initialData;
        this.filteredEvents = [...this.events];

        // Setup event listeners
        this.setupListeners();

        // Initial render
        this.renderEvents();
        this.renderPagination();
        this.updateEventCounter();

        return this;
    }

    /**
     * Set up all event listeners
     */
    setupListeners() {
        // Filter dropdown handler
        // Filter dropdown handler
        const filterDropdown = document.getElementById('filterDropdown');
        if (filterDropdown) {
            filterDropdown.querySelectorAll('.dropdown-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const sortType = e.target.textContent.trim();
                    this.handleSort(sortType);
                });
            });
        }
        document.querySelectorAll('.dropdown-item[data-sort]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const sortType = e.target.getAttribute('data-sort') || e.target.textContent.trim();
                this.handleSort(sortType);
            });
        });

        // Add Event button
        const addEventBtn = document.querySelector('button[data-bs-target="#addEventModal"]');
        if (addEventBtn) {
            addEventBtn.addEventListener('click', this.openAddModal);
        }

        // Add Event form submission
        const addEventForm = document.querySelector('#addEventModal form');
        if (addEventForm) {
            addEventForm.querySelector('button.btn-primary').addEventListener('click', () => {
                this.saveEvent(addEventForm);
            });
        }

        // Book event calculator
        const bookForm = document.querySelector('#bookEventModal form');
        if (bookForm) {
            const ticketInput = bookForm.querySelector('#totalTicketInput');
            const priceInput = bookForm.querySelector('#pricePerTicketInput');
            const totalInput = bookForm.querySelector('#totalAmountInput');

            [ticketInput, priceInput].forEach(input => {
                input.addEventListener('input', () => {
                    const tickets = parseInt(ticketInput.value) || 0;
                    const price = parseInt(priceInput.value) || 0;
                    totalInput.value = tickets * price;
                });
            });
        }
    }

    /**
     * Render events to the grid
     */
    renderEvents() {
        const eventsContainer = document.querySelector('#event-grid');
        if (!eventsContainer) return;

        // Clear current content
        eventsContainer.innerHTML = '';

        // Calculate slice for pagination
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const eventsToShow = this.filteredEvents.slice(startIndex, endIndex);

        if (eventsToShow.length === 0) {
            eventsContainer.innerHTML = `
          <div class="col-12 text-center py-5">
            <p>هیچ رویدادی یافت نشد.</p>
          </div>
        `;
            return;
        }

        // Render each event
        eventsToShow.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.className = 'col-md-6 col-xl-4';
            eventCard.innerHTML = this.getEventCardHTML(event);
            eventsContainer.appendChild(eventCard);

            // Add event listeners to the card actions
            const cardActions = eventCard.querySelectorAll('.dropdown-item');
            cardActions.forEach(action => {
                action.addEventListener('click', (e) => {
                    e.preventDefault();
                    const actionType = e.target.textContent.trim();

                    if (actionType === 'نمای کلی') {
                        this.openViewModal(event);
                    } else if (actionType === 'ویرایش') {
                        this.openEditModal(event);
                    } else if (actionType === 'حذف') {
                        this.deleteEvent(event.id);
                    }
                });
            });

            // Add listener to book button
            const bookBtn = eventCard.querySelector('button[data-bs-target="#bookEventModal"]');
            if (bookBtn) {
                bookBtn.addEventListener('click', () => this.setupBookModal(event));
            }
        });
    }

    /**
     * Generate HTML for an event card
     * @param {Object} event - Event data
     * @returns {String} HTML markup
     */
    getEventCardHTML(event) {
        return `
        <div class="card card-h-100">
          <div class="card-body">
            <div class="d-flex align-items-center gap-3">
              <img src="${event.organizerAvatar}" loading="lazy" alt="" class="size-12 rounded-circle flex-shrink-0" id="eventOrganizerAvatar">
              <div class="flex-grow-1">
                <h6 class="mb-1"><a href="#!" class="text-reset">${event.organizer}</a></h6>
                <p class="fs-sm text-muted">${event.dateFormatted}, ${event.time}</p>
              </div>
              <div class="dropdown">
                <a href="#!" class="link link-custom-primary" id="actionDropdown${event.id}" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="dropdown-button">
                  <i class="ri-more-fill"></i>
                </a>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="actionDropdown${event.id}">
                  <li><a class="dropdown-item" href="#!"><i class="me-3 ri-eye-line"></i><span>نمای کلی</span></a></li>
                  <li><a class="dropdown-item" href="#!"><i class="me-3 ri-pencil-line"></i>ویرایش</a></li>
                  <li><a class="dropdown-item" href="#!"><i class="me-3 ri-delete-bin-line"></i><span>حذف</span></a></li>
                </ul>
              </div>
            </div>
            <div class="mt-5">
              <img src="${event.image}" loading="lazy" alt="" class="w-100 h-48 rounded object-fit-cover" id="eventImage">
            </div>
            <div class="d-flex mt-5 gap-3">
              <div>
                <div class="size-16 mx-auto mb-10px rounded-2 bg-danger-subtle border border-danger-subtle avatar flex-column" id="eventDate">
                  <p class="mb-0.5 text-danger">${event.dayOfWeek}</p>
                  <h3 class="mb-0 fs-2xl text-danger">${event.day}</h3>
                </div>
                <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#bookEventModal">
                  ذخیره کنید
                </button>
              </div>
              <div>
                <h6 class="mb-1"><a href="#!" class="link link-custom event-name">${event.name}</a></h6>
                <p class="mb-2 text-muted" id="eventLocation"><span>${event.dateFormatted}</span><span class="ps-2 ms-2 border-start">${event.location}</span></p>
                <p class="mb-1 text-muted">مشارکت‌کنندگان</p>
                <div class="avatar-group">
                  ${this.getContributorsHTML(event.contributors)}
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    /**
     * Generate HTML for contributors avatars
     * @param {Array} contributors - List of contributor objects
     * @returns {String} HTML markup
     */
    getContributorsHTML(contributors) {
        return contributors.map(contributor => `
        <a href="#!" class="avatar-group-item" aria-label="avatar-link">
          <img src="${contributor.avatar}" loading="lazy" alt="" class="size-8">
        </a>
      `).join('');
    }

    /**
     * Setup the booking modal with event data
     * @param {Object} event - Event data
     */
    setupBookModal(event) {
        const modal = document.getElementById('bookEventModal');
        if (!modal) return;

        // Update modal content with event data
        modal.querySelector('#eventCount').textContent = event.name;
        modal.querySelector('#eventOrganizer h6 a').textContent = event.organizer;
        modal.querySelector('#eventOrganizer p').textContent = `${event.dateFormatted}, ${event.time}`;

        // Set the organizer avatar - This line is missing
        const organizerAvatar = modal.querySelector('#eventOrganizerAvatar');
        if (organizerAvatar) organizerAvatar.src = event.organizerAvatar;

        modal.querySelector('#eventImage').src = event.image;
        modal.querySelector('#eventDate p').textContent = event.dayOfWeek;
        modal.querySelector('#eventDate h3').textContent = event.day;
        modal.querySelector('h6 a.event-name').textContent = event.name;
        modal.querySelector('p#eventLocation span:first-child').textContent = event.dateFormatted;
        modal.querySelector('p#eventLocation span:last-child').textContent = event.location;

        // Reset form values
        const form = modal.querySelector('form');
        form.reset();
        form.querySelector('#totalAmountInput').value = '0';
    }

    /**
     * Render pagination controls
     */
    renderPagination() {
        const paginationContainer = document.querySelector('.pagination');
        if (!paginationContainer) return;

        // Calculate total pages
        const totalPages = Math.ceil(this.filteredEvents.length / this.itemsPerPage);

        // Update results text
        const resultsText = document.querySelector('#showingResults');
        if (resultsText) {
            const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
            const endIndex = Math.min(startIndex + this.itemsPerPage - 1, this.filteredEvents.length);
            resultsText.innerHTML = `نمایش <b class="me-1">${startIndex}-${endIndex}</b>از<b class="ms-1">${this.filteredEvents.length}</b> نتیجه`;
        }

        // Clear current pagination
        paginationContainer.innerHTML = '';

        // Previous button
        const prevButton = document.createElement('li');
        prevButton.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevButton.innerHTML = '<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>';
        paginationContainer.appendChild(prevButton);

        if (this.currentPage > 1) {
            prevButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handlePageChange(this.currentPage - 1);
            });
        }

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
            paginationContainer.appendChild(pageItem);

            if (i !== this.currentPage) {
                pageItem.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handlePageChange(i);
                });
            }
        }

        // Next button
        const nextButton = document.createElement('li');
        nextButton.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
        nextButton.innerHTML = '<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>';
        paginationContainer.appendChild(nextButton);

        if (this.currentPage < totalPages) {
            nextButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handlePageChange(this.currentPage + 1);
            });
        }
        createIcons({ icons });
    }

    /**
     * Handle page change
     * @param {Number} page - Page number
     */
    handlePageChange(page) {
        this.currentPage = page;
        this.renderEvents();
        this.renderPagination();
    }

    /**
     * Handle sorting of events
     * @param {String} sortType - Type of sorting
     */
    handleSort(sortType) {
        switch (sortType) {
            case 'No Sorting':
                // Reset to original order
                this.filteredEvents = [...this.events];
                break;

            case 'Alphabetical (A -> Z)':
                this.filteredEvents.sort((a, b) => a.name.localeCompare(b.name));
                break;

            case 'Reverse Alphabetical (Z -> A)':
                this.filteredEvents.sort((a, b) => b.name.localeCompare(a.name));
                break;

            case 'Status':
                this.filteredEvents.sort((a, b) => a.status.localeCompare(b.status));
                break;

            default:
                // By default, sort by date (newest first)
                this.filteredEvents.sort((a, b) => new Date(b.date) - new Date(a.date));
        }

        // Reset to first page when sorting
        this.currentPage = 1;
        this.renderEvents();
        this.renderPagination();
    }

    /**
     * Handle filtering of events
     * @param {String} filterValue - Filter text value
     */
    handleFilter(filterValue) {
        this.filterValue = filterValue.toLowerCase();

        if (!this.filterValue) {
            this.filteredEvents = [...this.events];
        } else {
            this.filteredEvents = this.events.filter(event =>
                event.name.toLowerCase().includes(this.filterValue) ||
                event.location.toLowerCase().includes(this.filterValue) ||
                event.organizer.toLowerCase().includes(this.filterValue)
            );
        }

        // Reset to first page when filtering
        this.currentPage = 1;
        this.renderEvents();
        this.renderPagination();
        this.updateEventCounter();
    }

    /**
     * Open add event modal
     */
    openAddModal() {
        const modal = document.getElementById('addEventModal');
        if (!modal) return;

        // Reset the form
        const form = modal.querySelector('form');
        form.reset();

        // Reset any validation messages
        form.querySelectorAll('.text-danger').forEach(el => el.style.display = 'none');

        // Reset image preview
        const preview = document.getElementById('eventLogoPreview');
        if (preview) preview.classList.add('d-none');

        // Show upload placeholder
        const uploadText = document.querySelector('#uploadLabel span');
        if (uploadText) uploadText.classList.remove('d-none');

        // Set button text to "Add Event"
        const submitBtn = form.querySelector('button.btn-primary');
        if (submitBtn) submitBtn.textContent = 'افزودن رویداد';

        // Clear selected event
        this.selectedEvent = null;
    }

    /**
     * Open edit event modal
     * @param {Object} event - Event data to edit
     */
    openEditModal(event) {
        const modal = document.getElementById('addEventModal');
        if (!modal) return;

        // Store the event being edited
        this.selectedEvent = event;

        // Update modal title
        modal.querySelector('.modal-header h6').textContent = 'ویرایش رویداد';

        // Fill the form with event data
        const form = modal.querySelector('form');
        form.querySelector('input[name="event-name"]').value = event.name;
        form.querySelector('input[name="event-time"]').value = event.time;
        form.querySelector('input[name="total-people"]').value = event.capacity;
        form.querySelector('input[name="price"]').value = event.price;
        form.querySelector('input[name="location"]').value = event.location;

        // Show image preview if available
        if (event.image) {
            const preview = document.getElementById('eventLogoPreview');
            const previewImg = document.getElementById('eventLogoImage');

            if (preview && previewImg) {
                preview.classList.remove('d-none');
                previewImg.src = event.image;

                // Hide upload placeholder
                const uploadText = document.querySelector('#uploadLabel span');
                if (uploadText) uploadText.classList.add('d-none');
            }
        }

        // Set button text to "Update Event"
        const submitBtn = form.querySelector('button.btn-primary');
        if (submitBtn) submitBtn.textContent = 'آپدیت رویداد';

        // Show the modal
        const bsModal = new window.bootstrap.Modal(modal);
        bsModal.show();
    }

    /**
     * Open view event modal (overview)
     * @param {Object} event - Event data to view
     */
    openViewModal(event) {
        // In a real implementation, this would navigate to a detailed view
        // For now, we'll just open the book modal with the event details
        this.setupBookModal(event);
        const modal = document.getElementById('bookEventModal');
        const bsModal = new window.bootstrap.Modal(modal);
        bsModal.show();
    }
    /**
     * Delete an event
     * @param {String|Number} eventId - ID of event to delete
     */
    deleteEvent(eventId) {
        // Get the delete modal
        const deleteModal = document.getElementById('deleteModal');
        if (!deleteModal) return;

        // Update modal text for events
        const modalTitle = deleteModal.querySelector('h5');
        if (modalTitle) {
            modalTitle.textContent = 'آیا از حذف این رویداد مطمئن هستید؟';
        }

        // Get the delete button
        const deleteButton = deleteModal.querySelector('.btn-danger');

        // Remove any existing click handlers to prevent duplicates
        const newDeleteButton = deleteButton.cloneNode(true);
        deleteButton.parentNode.replaceChild(newDeleteButton, deleteButton);

        // Add click handler to the delete button
        newDeleteButton.addEventListener('click', () => {
            // Find and remove the event
            const eventIndex = this.events.findIndex(event => event.id === eventId);
            if (eventIndex > -1) {
                this.events.splice(eventIndex, 1);

                // Update filtered events
                this.filteredEvents = this.filteredEvents.filter(event => event.id !== eventId);

                // Refresh display
                this.renderEvents();
                this.renderPagination();
                this.updateEventCounter();
            }

            // Hide the modal
            const bsModal = window.bootstrap.Modal.getInstance(deleteModal);
            bsModal.hide();
        });

        // Show the modal
        const bsModal = new window.bootstrap.Modal(deleteModal);
        bsModal.show();
    }

    /**
     * Save event (add new or update existing)
     * @param {HTMLFormElement} form - Form element containing event data
     */
    saveEvent(form) {
        // Validate form
        if (!this.validateEventForm(form)) return;

        // Get form data
        const name = form.querySelector('input[name="event-name"]').value;
        const dateStr = dueDateInput.value;
        const time = form.querySelector('input[name="event-time"]').value;
        const capacity = form.querySelector('input[name="total-people"]').value;
        const price = form.querySelector('input[name="price"]').value;
        const location = form.querySelector('input[name="location"]').value;

        // Get image from file input or use random local image
        const fileInput = form.querySelector('input[name="event-logo"]');

        let image;

        // If user choose a file
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            image = document.getElementById('eventLogoImage').src;
        } else {
            const localImages = [
                "assets/images/event/img-04.jpg",
                "assets/images/event/img-05.jpg",
                "assets/images/event/img-06.jpg",
                "assets/images/event/img-07.png"
            ];

            // Choose random local image
            image = localImages[Math.floor(Math.random() * localImages.length)];
        }

        // Convert date to Jalali (Shamsi)
        function getJalaliWeekdayIndex(jy, jm, jd) {
            jy = jy - 1;
            var a = 365 * jy
                + Math.floor(jy / 33) * 8
                + Math.floor(((jy % 33) + 3) / 4)
                + jd;

            var monthDays = [0,31,62,93,124,155,186,216,246,276,306,336];
            a += monthDays[jm - 1];

            var weekdayIndex = (a + 4) % 7; // ❗Demo-only weekday calc (offset tuned for 1405)
            return weekdayIndex; 
        }

        const JALALI_WEEKDAYS = [
            "شنبه",
            "یکشنبه",
            "دوشنبه",
            "سه‌شنبه",
            "چهارشنبه",
            "پنجشنبه",
            "جمعه"
        ];

        const JALALI_MONTHS = [
            "",
            "فروردین",
            "اردیبهشت",
            "خرداد",
            "تیر",
            "مرداد",
            "شهریور",
            "مهر",
            "آبان",
            "آذر",
            "دی",
            "بهمن",
            "اسفند"
        ];

        const jalaliDateStr = dateStr;

        // Separate Year, Month, Day
        const [jy, jm, jd] = jalaliDateStr.split('-').map(Number);

        const weekdayIndex = getJalaliWeekdayIndex(jy, jm, jd);

        const day = jd;
        const dayOfWeek = JALALI_WEEKDAYS[weekdayIndex];
        const monthName = JALALI_MONTHS[jm];
        const year = jy;
        // Create date formatted string
        const dateFormatted = `${day} ${monthName} ${year}`;

        if (this.selectedEvent) {
            // Update existing event
            const eventIndex = this.events.findIndex(e => e.id === this.selectedEvent.id);
            if (eventIndex > -1) {
                this.events[eventIndex] = {
                    ...this.selectedEvent,
                    name,
                    date: dateStr,
                    dateFormatted,
                    time,
                    capacity: parseInt(capacity),
                    price: parseInt(price),
                    location,
                    image,
                    day,
                    dayOfWeek
                };
            }
        } else {
            // Add new event
            const newEvent = {
                id: Date.now(), // Use timestamp as ID
                name,
                organizer: 'جمشید بهاری‌فر', // Normally would be from logged in user
                organizerAvatar: 'assets/images/avatar/user-5.png', // Placeholder
                date: dateStr,
                dateFormatted,
                time,
                capacity: parseInt(capacity),
                price: parseInt(price),
                location,
                image,
                day,
                dayOfWeek,
                status: 'فعال',
                contributors: [
                    { avatar: 'assets/images/avatar/user-5.png' }
                ]
            };

            this.events.unshift(newEvent);
        }

        // Update filtered events and refresh display
        this.filterValue ? this.handleFilter(this.filterValue) : this.filteredEvents = [...this.events];
        this.renderEvents();
        this.renderPagination();
        this.updateEventCounter();

        // Close the modal
        const modal = window.bootstrap.Modal.getInstance(document.getElementById('addEventModal'));
        modal.hide();
    }

    /**
     * Validate event form
     * @param {HTMLFormElement} form - Form to validate
     * @returns {Boolean} Is form valid
     */
    validateEventForm(form) {
        let isValid = true;

        // Required fields
        const requiredFields = [
            'event-name',
            'event-date',
            'event-time',
            'total-people',
            'price',
            'location'
        ];

        // Check each required field
        requiredFields.forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            const errorMsg = field.parentElement.querySelector('.text-danger');

            if (!field.value.trim()) {
                errorMsg.style.display = 'block';
                isValid = false;
            } else {
                errorMsg.style.display = 'none';
            }
        });

        return isValid;
    }

    /**
     * Update event counter in header
     */
    updateEventCounter() {
        const counter = document.querySelector('#eventCount span');
        if (counter) {
            counter.textContent = this.events.length;
        }
    }

    /**
     * Add search functionality
     * @param {String} searchInputId - ID of search input element
     */
    setupSearch(searchInputId) {
        const searchInput = document.getElementById(searchInputId);
        if (!searchInput) return;

        searchInput.addEventListener('input', (e) => {
            this.handleFilter(e.target.value);
        });
    }

    /**
     * Handle file input for event logo
     * @param {String} fileInputSelector - Selector for file input
     */
    setupFileUpload(fileInputSelector = 'input[type="file"]') {
        const fileInput = document.querySelector(fileInputSelector);
        if (!fileInput) return;

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            // Check file type
            if (!file.type.match('image.*')) {
                alert('لطفا یک فایل تصویری انتخاب کنید');
                return;
            }

            // Read and preview the image
            const reader = new FileReader();
            reader.onload = (event) => {
                const preview = document.getElementById('eventLogoPreview');
                const previewImg = document.getElementById('eventLogoImage');
                const uploadText = document.querySelector('#uploadLabel span');

                if (preview && previewImg) {
                    preview.classList.remove('d-none');
                    previewImg.src = event.target.result;

                    // Hide the "Upload Your Event Logo" text
                    if (uploadText) uploadText.classList.add('d-none');
                }
            };

            reader.readAsDataURL(file);
        });
    }
}

// Sample event data
const sampleEvents = [
    {
        id: 1,
        name: 'اجلاس نوآوری‌های فناوری',
        organizer: 'بهرام رادان',
        organizerAvatar: 'assets/images/avatar/user-5.png',
        date: '2024-05-19T10:00:00',
        dateFormatted: '30 اردیبهشت 1403',
        time: '10:00 صبح',
        day: '30',
        dayOfWeek: 'یکشنبه',
        location: 'ایران، جزیره کیش',
        image: 'assets/images/event/img-01.jpg',
        capacity: 200,
        price: 500,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-5.png' },
            { avatar: 'assets/images/avatar/user-20.png' },
            { avatar: 'assets/images/avatar/user-13.png' }
        ]
    },
    {
        id: 2,
        name: 'نمایشگاه سلامت و تندرستی',
        organizer: 'مهرداد صدیقیان',
        organizerAvatar: 'assets/images/avatar/user-20.png',
        date: '2024-06-24T09:00:00',
        dateFormatted: '4 تیر 1403',
        time: '9:00 صبح',
        day: '4',
        dayOfWeek: 'دوشنبه',
        location: 'ایران، تهران',
        image: 'assets/images/event/img-02.jpg',
        capacity: 150,
        price: 350,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-20.png' },
            { avatar: 'assets/images/avatar/user-5.png' }
        ]
    },
    {
        id: 3,
        name: 'کنفرانس بازاریابی',
        organizer: 'صوفیا ابراهیمی',
        organizerAvatar: 'assets/images/avatar/user-10.png',
        date: '2024-07-15T13:30:00',
        dateFormatted: '25 تیر 1403',
        time: '1:30 بعد از ظهر',
        day: '25',
        dayOfWeek: 'دوشنبه',
        location: 'ایران، اصفهان',
        image: 'assets/images/event/img-03.jpg',
        capacity: 300,
        price: 450,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-10.png' },
            { avatar: 'assets/images/avatar/user-15.png' }
        ]
    },
    {
        id: 4,
        name: 'نمایشگاه هوش مصنوعی و رباتیک',
        organizer: 'لیام نلسون',
        organizerAvatar: 'assets/images/avatar/user-15.png',
        date: '2024-08-10T11:00:00',
        dateFormatted: '20 مرداد 1403',
        time: '11:00 صبح',
        day: '20',
        dayOfWeek: 'شنبه',
        location: 'ترکیه استانبول',
        image: 'assets/images/event/img-01.jpg',
        capacity: 250,
        price: 400,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-15.png' },
            { avatar: 'assets/images/avatar/user-20.png' }
        ]
    },
    {
        id: 5,
        name: 'نمایشگاه جهانی آموزش',
        organizer: 'سارا شریفی‌نیا',
        organizerAvatar: 'assets/images/avatar/user-13.png',
        date: '2024-09-05T10:00:00',
        dateFormatted: '15 شهریور 1403',
        time: '10:00 صبح',
        day: '15',
        dayOfWeek: 'پنجشنبه',
        location: 'ایران، کاشان',
        image: 'assets/images/event/img-02.jpg',
        capacity: 180,
        price: 300,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-13.png' },
            { avatar: 'assets/images/avatar/user-10.png' }
        ]
    },
    {
        id: 6,
        name: 'شب ارائه استارتاپی',
        organizer: 'حامد کمیلی',
        organizerAvatar: 'assets/images/avatar/user-20.png',
        date: '2024-10-14T17:00:00',
        dateFormatted: '23 مهر 1403',
        time: '5:00 بعد از ظهر',
        day: '23',
        dayOfWeek: 'دوشنبه',
        location: 'ایران، تهران',
        image: 'assets/images/event/img-03.jpg',
        capacity: 100,
        price: 200,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-20.png' },
            { avatar: 'assets/images/avatar/user-5.png' }
        ]
    },
    {
        id: 7,
        name: 'بوت کمپ طراحی UX/UI',
        organizer: 'اولیویا رودریگر',
        organizerAvatar: 'assets/images/avatar/user-5.png',
        date: '2024-11-02T09:30:00',
        dateFormatted: '12 آبان 1403',
        time: '9:30 صبح',
        day: '12',
        dayOfWeek: 'شنبه',
        location: 'ایران، تهران',
        image: 'assets/images/event/img-01.jpg',
        capacity: 120,
        price: 280,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-5.png' },
            { avatar: 'assets/images/avatar/user-10.png' }
        ]
    },
    {
        id: 8,
        name: 'اجلاس رهبران مالی',
        organizer: 'بارت سیمپسون',
        organizerAvatar: 'assets/images/avatar/user-10.png',
        date: '2024-12-11T14:00:00',
        dateFormatted: '21 آذر 1403',
        time: '2:00 بعد از ظهر',
        day: '21',
        dayOfWeek: 'چهارشنبه',
        location: 'ایران، تهران',
        image: 'assets/images/event/img-02.jpg',
        capacity: 220,
        price: 520,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-10.png' },
            { avatar: 'assets/images/avatar/user-13.png' }
        ]
    },
    {
        id: 9,
        name: 'انجمن انرژی سبز',
        organizer: 'کامران مهین‌دوست',
        organizerAvatar: 'assets/images/avatar/user-15.png',
        date: '2025-01-20T10:30:00',
        dateFormatted: '6 بهمن 1403',
        time: '10:30 صبح',
        day: '6',
        dayOfWeek: 'دوشنبه',
        location: 'ایران، یزد',
        image: 'assets/images/event/img-03.jpg',
        capacity: 270,
        price: 480,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-15.png' },
            { avatar: 'assets/images/avatar/user-20.png' }
        ]
    },
    {
        id: 10,
        name: 'گردهمایی بلاکچین و کریپتو',
        organizer: 'الیزابت تیلور',
        organizerAvatar: 'assets/images/avatar/user-13.png',
        date: '2025-02-16T15:00:00',
        dateFormatted: '25 بهمن 1403',
        time: '3:00 بعد از ظهر',
        day: '25',
        dayOfWeek: 'یکشنبه',
        location: 'ایران، تهران',
        image: 'assets/images/event/img-01.jpg',
        capacity: 160,
        price: 450,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-13.png' },
            { avatar: 'assets/images/avatar/user-5.png' }
        ]
    },
    {
        id: 11,
        name: 'جشنواره هنرهای خلاق',
        organizer: 'لیام پین',
        organizerAvatar: 'assets/images/avatar/user-20.png',
        date: '2025-03-08T12:00:00',
        dateFormatted: '18 اسفند 1043',
        time: '12:00 بعد از ظهر',
        day: '18',
        dayOfWeek: 'شنبه',
        location: 'ایران، تهران',
        image: 'assets/images/event/img-02.jpg',
        capacity: 350,
        price: 320,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-20.png' },
            { avatar: 'assets/images/avatar/user-10.png' }
        ]
    },
    {
        id: 12,
        name: 'انجمن فناوری نسل بعدی',
        organizer: 'صدف اسپهبد',
        organizerAvatar: 'assets/images/avatar/user-10.png',
        date: '2025-04-05T13:00:00',
        dateFormatted: '16 فروردین 1404',
        time: '1:00 بعد از ظهر',
        day: '16',
        dayOfWeek: 'شنبه',
        location: 'ایران، شیراز',
        image: 'assets/images/event/img-03.jpg',
        capacity: 300,
        price: 550,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-10.png' },
            { avatar: 'assets/images/avatar/user-15.png' }
        ]
    },
    {
        id: 13,
        name: 'نشست زنان در حوزه فناوری',
        organizer: 'مادام شارلوت',
        organizerAvatar: 'assets/images/avatar/user-5.png',
        date: '2025-05-18T16:00:00',
        dateFormatted: '28 اردیبهشت 1404',
        time: '4:00 بعد از ظهر',
        day: '28',
        dayOfWeek: 'یکشنبه',
        location: 'ارمنستان، ایروان',
        image: 'assets/images/event/img-01.jpg',
        capacity: 200,
        price: 250,
        status: 'فعال',
        contributors: [
            { avatar: 'assets/images/avatar/user-5.png' },
            { avatar: 'assets/images/avatar/user-13.png' }
        ]
    }
];
// Initialize the grid manager when document is ready
document.addEventListener('DOMContentLoaded', () => {
    const gridManager = new GridManager({
        containerId: 'event-listing-container',
        itemsPerPage: 6
    });

    gridManager.init(sampleEvents);

    // Setup additional event handlers
    gridManager.setupSearch('event-search');
    gridManager.setupFileUpload('input[name="event-logo"]');

    // Make gridManager available globally for debugging
    window.gridManager = gridManager;
});