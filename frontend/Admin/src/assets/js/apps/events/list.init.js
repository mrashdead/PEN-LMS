import { icons, createIcons } from "lucide";



// Status Select
VirtualSelect.init({
    ele: "#StatusSelect",
    options: [
        { label: "منتشر شده", value: "Published" },
        { label: "به زودی", value: "Coming Soon" },
        { label: "منقضی شده", value: "Expired" }
    ],
});

//Event Type Select
VirtualSelect.init({
    ele: "#eventTypeSelect",
    options: [
        { label: "آفلاین", value: "Offline" },
        { label: "آنلاین", value: "Online" }
    ],
});

// Mappings
const statusMapping = {
    'Published': 'منتشر شده',
    'Coming Soon': 'به زودی',
    'Draft': 'پیش‌نویس'
};

const typeMapping = {
    'Online': 'آنلاین',
    'Offline': 'آفلاین',
    'Hybrid': 'ترکیبی'
};

class TableManager {
    constructor() {
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.sortColumn = 'none';
        this.sortDirection = 'asc';
        this.editingId = null;
        this.modal = null;

        // Sample data
        this.loadSampleData();

        // Initialize event listeners
        this.initEventListeners();

        // Initialize Bootstrap modal
        this.modal = new window.bootstrap.Modal(document.getElementById('leadCreateModal'));

        // Initial render
        this.render();
    }

    loadSampleData() {
        this.data = [
    {
        id: 1,
        logo: "assets/images/brands/img-01.png",
        name: "اجلاس نوآوری‌های فناوری",
        date: "1403/06/15",
        duration: "09:00",
        people: 500,
        location: "نیویورک، نیویورک",
        type: "Offline",
        price: 899,
        status: "Published"
    },
    {
        id: 2,
        logo: "assets/images/brands/img-02.png",
        name: "استراتژی‌های بازاریابی 2024",
        date: "1403/07/20",
        duration: "10:00",
        people: 300,
        location: "سان فرانسیسکو، کالیفرنیا",
        type: "Offline",
        price: 499,
        status: "Published"
    },
    {
        id: 3,
        logo: "assets/images/brands/img-03.png",
        name: "نمایشگاه هوش مصنوعی و یادگیری ماشین",
        date: "1403/08/10",
        duration: "11:00",
        people: 800,
        location: "شیکاگو، ایلینوی",
        type: "Online",
        price: 599,
        status: "Coming Soon"
    },
    {
        id: 4,
        logo: "assets/images/brands/img-04.png",
        name: "کنفرانس جهانی بلاکچین",
        date: "1403/09/05",
        duration: "09:30",
        people: 1000,
        location: "لس‌آنجلس، کالیفرنیا",
        type: "Offline",
        price: 1099,
        status: "Published"
    },
    {
        id: 5,
        logo: "assets/images/brands/img-05.png",
        name: "اجلاس امنیت سایبری",
        date: "1403/10/18",
        duration: "10:30",
        people: 600,
        location: "بوستون، ماساچوست",
        type: "Offline",
        price: 799,
        status: "Published"
    },
    {
        id: 6,
        logo: "assets/images/brands/img-06.png",
        name: "فروم نوآوری‌های سلامت",
        date: "1403/11/15",
        duration: "12:00",
        people: 400,
        location: "سیاتل، واشینگتن",
        type: "Online",
        price: 399,
        status: "Coming Soon"
    },
    {
        id: 7,
        logo: "assets/images/brands/img-07.png",
        name: "روندهای تجارت الکترونیک 2024",
        date: "1403/12/05",
        duration: "13:00",
        people: 700,
        location: "آستین، تگزاس",
        type: "Offline",
        price: 699,
        status: "Published"
    },
    {
        id: 8,
        logo: "assets/images/brands/img-08.png",
        name: "کنفرانس فین‌تک",
        date: "1403/06/30",
        duration: "09:00",
        people: 200,
        location: "میامی، فلوریدا",
        type: "Online",
        price: 499,
        status: "منقضی شده"
    },
    {
        id: 9,
        logo: "assets/images/brands/img-09.png",
        name: "اجلاس تحول دیجیتال",
        date: "1403/07/25",
        duration: "09:00",
        people: 900,
        location: "دالاس، تگزاس",
        type: "Offline",
        price: 899,
        status: "Published"
    },
    {
        id: 10,
        logo: "assets/images/brands/img-10.png",
        name: "نمایشگاه فناوری سبز",
        date: "1403/08/15",
        duration: "10:00",
        people: 500,
        location: "دنور، کلرادو",
        type: "Online",
        price: 599,
        status: "Coming Soon"
    },
    {
        id: 11,
        logo: "assets/images/brands/img-11.png",
        name: "کنفرانس شهرهای هوشمند",
        date: "1403/09/10",
        duration: "11:00",
        people: 600,
        location: "لاس وگاس، نوادا",
        type: "Offline",
        price: 999,
        status: "Published"
    },
    {
        id: 12,
        logo: "assets/images/brands/img-12.png",
        name: "نمایشگاه واقعیت مجازی",
        date: "1403/10/22",
        duration: "12:00",
        people: 300,
        location: "اورلاندو، فلوریدا",
        type: "Online",
        price: 399,
        status: "Coming Soon"
    },
    {
        id: 13,
        logo: "assets/images/brands/img-13.png",
        name: "اجلاس انرژی‌های تجدیدپذیر",
        date: "1403/11/05",
        duration: "09:00",
        people: 1000,
        location: "سن دیگو، کالیفرنیا",
        type: "Offline",
        price: 1099,
        status: "Published"
    },
    {
        id: 14,
        logo: "assets/images/brands/img-14.png",
        name: "فروم جهانی اینترنت اشیا",
        date: "1403/12/01",
        duration: "10:00",
        people: 700,
        location: "فنیکس، آریزونا",
        type: "Online",
        price: 499,
        status: "Published"
    },
    {
        id: 15,
        logo: "assets/images/brands/img-15.png",
        name: "کنفرانس فناوری آموزشی",
        date: "1403/08/25",
        duration: "11:00",
        people: 400,
        location: "هیوستون، تگزاس",
        type: "Offline",
        price: 699,
        status: "Coming Soon"
    },
    {
        id: 16,
        logo: "assets/images/brands/img-16.png",
        name: "اجلاس رایانش ابری",
        date: "1403/09/18",
        duration: "12:00",
        people: 800,
        location: "سالت لیک سیتی، یوتا",
        type: "Offline",
        price: 899,
        status: "Published"
    }
        ];

        this.filteredData = [...this.data];
    }

    initEventListeners() {
        // Sort event listeners - we'll now add this to table headers instead of separate buttons
        this.addSortableHeaders();

        // Form submission
        document.getElementById('event-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveEvent();
        });
        // Add file input change handler
        document.getElementById('event-logo').addEventListener('change', (e) => {
            this.handleImageUpload(e);
        });
        // Reset form when modal is opened for new event
        document.querySelector('[data-bs-target="#leadCreateModal"]').addEventListener('click', () => {
            this.resetForm();
        });

        // Table body event delegation for edit/delete
        document.getElementById('event-table-body').addEventListener('click', (e) => {
            const action = e.target.closest('.dropdown-item');
            if (!action) return;

            const row = e.target.closest('tr');
            const id = parseInt(row.dataset.id);

            if (action.innerText.includes('ویرایش')) {
                this.editEvent(id);
            } else if (action.innerText.includes('حذف')) {
                this.deleteEvent(id);
            }
        });
    }

    addSortableHeaders() {
        // Define the sortable columns
        const sortableColumns = [
            { column: 'name', headerIndex: 0, label: 'عنوان رویداد' },
            { column: 'date', headerIndex: 1, label: 'تاریخ رویداد' },
            { column: 'people', headerIndex: 2, label: 'شرکت‌کنندگان' },
            { column: 'location', headerIndex: 3, label: 'مکان' },
            { column: 'type', headerIndex: 4, label: 'نوع رویداد' },
            { column: 'price', headerIndex: 5, label: 'قیمت' },
            { column: 'status', headerIndex: 6, label: 'وضعیت' }
        ];

        // Get the table header row
        const headerRow = document.querySelector('thead tr');
        if (!headerRow) return;

        // Get all header cells
        const headerCells = headerRow.querySelectorAll('th');

        // Add sort icons and click handlers to each sortable column
        sortableColumns.forEach(({ column, headerIndex, label }) => {
            if (headerIndex < headerCells.length) {
                const cell = headerCells[headerIndex];

                // Replace the content with a button that has the sort functionality
                cell.innerHTML = `
                    <div class="d-flex align-items-center gap-2">
                        <span class="fw-medium text-muted">${label}</span>
                        <a href="#!" class="sort-btn text-muted" data-column="${column}">
                            <i class="ri-arrow-up-down-line sort-icon"></i>
                        </a>
                    </div>
                `;

                // Add click event to the sort button
                const sortBtn = cell.querySelector('.sort-btn');
                sortBtn.addEventListener('click', () => this.toggleSort(column));
            }
        });
    }

    toggleSort(column) {
        // If clicking on the same column, toggle direction
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // New column, default to ascending
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        // Reset to first page
        this.currentPage = 1;

        // Sort the data
        this.sortData();

        // Update the sort icons
        this.updateSortIcons();

        // Render the table
        this.render();
    }

    updateSortIcons() {
        // Reset all icons first
        document.querySelectorAll('.sort-icon').forEach(icon => {
            icon.className = 'ri-arrow-up-down-line sort-icon';
        });

        // Update the active sort column's icon
        const activeButton = document.querySelector(`.sort-btn[data-column="${this.sortColumn}"]`);
        if (activeButton) {
            const icon = activeButton.querySelector('.sort-icon');
            if (icon) {
                icon.className = this.sortDirection === 'asc'
                    ? 'ri-arrow-up-line sort-icon'
                    : 'ri-arrow-down-line sort-icon';
            }
        }
    }

    sortData() {
        if (this.sortColumn === 'none') {
            this.filteredData = [...this.data];
            return;
        }

        this.filteredData.sort((a, b) => {
            let valueA = a[this.sortColumn];
            let valueB = b[this.sortColumn];

            // Handle numeric values
            if (this.sortColumn === 'people' || this.sortColumn === 'price') {
                valueA = Number(valueA);
                valueB = Number(valueB);
                return this.sortDirection === 'asc' ? valueA - valueB : valueB - valueA;
            }

            // Handle date values
            if (this.sortColumn === 'date') {
                valueA = new Date(valueA);
                valueB = new Date(valueB);
                return this.sortDirection === 'asc' ? valueA - valueB : valueB - valueA;
            }

            // Handle string values (case-insensitive)
            valueA = String(valueA).toLowerCase();
            valueB = String(valueB).toLowerCase();

            if (valueA < valueB) return this.sortDirection === 'asc' ? -1 : 1;
            if (valueA > valueB) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }

    render() {
        this.renderTable();
        this.renderPagination();
        this.updateTotalCount();
    }

    renderTable() {
        const tableBody = document.getElementById('event-table-body');
        tableBody.innerHTML = '';

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = this.filteredData.slice(startIndex, endIndex);

        pageData.forEach(event => {
            const row = document.createElement('tr');
            row.dataset.id = event.id;

        // Persian showing status
        const persianStatus = statusMapping[event.status] || event.status;

            const statusClass = event.status === 'Published'
                ? 'bg-success-subtle text-success border border-success-subtle'
                : event.status === 'Coming Soon'
                    ? 'bg-warning-subtle text-warning border border-warning-subtle'
                    : 'bg-danger-subtle text-danger border border-danger-subtle';

        //  Persian showing type
        const persianType = typeMapping[event.type] || event.type;

            row.innerHTML = `
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="size-9 border avatar rounded">
                            <img src="${event.logo}" loading="lazy" alt="" class="size-7">
                        </div>
                        <h6 class="mb-0"><a href="#!" class="text-reset">${event.name}</a></h6>
                    </div>
                </td>
                <td>${event.date}</td>
                <td>${event.people} نفر</td>
                <td>${event.location}</td>
                <td>${persianType}</td>
                <td>${event.price} تومان</td>
                <td>
                    <span class="badge ${statusClass}">${persianStatus}</span>
                </td>
                <td>
                    <div class="dropdown">
                        <a href="#!" class="link link-custom-primary" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="ri-more-2-fill"></i>
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="#!"><i class="ri-eye-line me-2"></i><span>مشاهده</span></a></li>
                            <li><a class="dropdown-item" href="#!"><i class="ri-pencil-line me-2"></i>ویرایش</a></li>
                            <li><a class="dropdown-item" href="#!"><i class="ri-delete-bin-line me-2"></i><span>حذف</span></a></li>
                        </ul>
                    </div>
                </td>
            `;

            tableBody.appendChild(row);
        });

        // Update pagination info
        const startItem = this.filteredData.length > 0 ? startIndex + 1 : 0;
        const endItem = Math.min(endIndex, this.filteredData.length);
        document.getElementById('pagination-info').innerHTML = `
            نمایش <b class="me-1">${startItem}-${endItem}</b> از <b class="ms-1">${this.filteredData.length}</b> نتیجه
        `;
    }

    renderPagination() {
        const pagination = document.getElementById('pagination');
        pagination.innerHTML = '';

        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#"> <i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.currentPage--;
                this.render();
            }
        });
        pagination.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${this.currentPage === i ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageLi.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = i;
                this.render();
            });
            pagination.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.render();
            }
        });
        pagination.appendChild(nextLi);
        createIcons({ icons });
    }

    updateTotalCount() {
        document.getElementById('total-count').textContent = this.data.length;
    }

    resetForm() {
        document.getElementById('modal-title').textContent = 'افزودن رویداد تازه';
        document.getElementById('submit-btn').textContent = 'افزودن رویداد';
        document.getElementById('event-id').value = '';
        document.getElementById('event-form').reset();
        this.editingId = null;
        // Reset the logo preview
        const uploadLabel = document.querySelector('#uploadLabel');
        uploadLabel.innerHTML = `
        <i class="ri-upload-2-line"></i>
        <span class="block mt-3">آپلود لوگوی رویداد</span>
        <input type="file" id="event-logo" class="d-none" />
    `;

        // Reset temp logo data
        this.tempLogoDataUrl = null;

        // Make sure to reconnect the event listener for the new input element
        document.getElementById('event-logo').addEventListener('change', (e) => {
            this.handleImageUpload(e);
        });

        // Hide all error messages
        document.querySelectorAll('.text-danger').forEach(el => el.classList.add('d-none'));
    }


    // Add this new method to handle image preview
    handleImageUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Check if file is an image
        if (!file.type.match('image.*')) {
            alert('لطفاً یک فایل تصویر انتخاب کنید');
            return;
        }

        // Create preview
        const reader = new FileReader();
        reader.onload = (event) => {
            // Show preview in the upload area
            const uploadLabel = document.querySelector('#uploadLabel');
            uploadLabel.innerHTML = '';

            const img = document.createElement('img');
            img.src = event.target.result;
            img.className = 'img-fluid';
            img.style.maxHeight = '100%';
            img.style.maxWidth = '100%';
            img.style.objectFit = 'contain';

            uploadLabel.appendChild(img);

            // Store the data URL to use when saving
            this.tempLogoDataUrl = event.target.result;
        };

        reader.readAsDataURL(file);
    }

    editEvent(id) {
        const event = this.data.find(e => e.id === id);
        if (!event) return;

        this.editingId = id;
        document.getElementById('modal-title').textContent = 'ویرایش رویداد';
        document.getElementById('submit-btn').textContent = 'آپدیت رویداد';

        // Fill form with event data
        document.getElementById('event-id').value = event.id;
        document.getElementById('event-name').value = event.name;
        document.getElementById('event-date').value = event.date;
        document.getElementById('event-duration').value = event.duration;
        document.getElementById('event-people').value = event.people;
        document.getElementById('event-price').value = event.price;
        document.getElementById('event-location').value = event.location;

        // Set select values (regular select, not Virtual Select)
        document.getElementById('event-type').value = event.type || '';
        document.getElementById('event-status').value = event.status || '';

        // Handle image preview for existing logo
        if (event.logo) {
            const uploadLabel = document.querySelector('#uploadLabel');

            // Clear the upload area first
            uploadLabel.innerHTML = '';

            // Create and add the image
            const img = document.createElement('img');
            img.src = event.logo;
            img.className = 'img-fluid';
            img.style.maxHeight = '100%';
            img.style.maxWidth = '100%';
            img.style.objectFit = 'contain';

            // Add the file input
            const input = document.createElement('input');
            input.type = 'file';
            input.id = 'event-logo';
            input.className = 'd-none';

            // Add both elements to the upload label
            uploadLabel.appendChild(img);
            uploadLabel.appendChild(input);

            // Store the logo URL for later use
            this.tempLogoDataUrl = event.logo;

            // Reattach the event listener
            input.addEventListener('change', (e) => {
                this.handleImageUpload(e);
            });
        }

        // Show modal
        this.modal.show();
    }

    deleteEvent(id) {
        if (confirm('آیا از حذف این رویداد مطمئن هستید؟')) {
            this.data = this.data.filter(e => e.id !== id);
            this.filteredData = this.filteredData.filter(e => e.id !== id);
            this.render();
        }
    }

    validateForm() {
        let isValid = true;
        const fields = [
            { id: 'event-name', error: 'name-error' },
            { id: 'event-date', error: 'date-error' },
            { id: 'event-duration', error: 'duration-error' },
            { id: 'event-people', error: 'people-error' },
            { id: 'event-price', error: 'price-error' },
            { id: 'event-location', error: 'location-error' },
            { id: 'event-type', error: 'type-error' },
            { id: 'event-status', error: 'status-error' }
        ];

        // Hide all error messages first
        document.querySelectorAll('.text-danger').forEach(el => el.classList.add('d-none'));

        fields.forEach(field => {
            const input = document.getElementById(field.id);
            const error = document.getElementById(field.error);

            if (!input.value.trim()) {
                error.classList.remove('d-none');
                isValid = false;
            }
        });

        return isValid;
    }

    saveEvent() {
        if (!this.validateForm()) return;

        const formData = {
            name: document.getElementById('event-name').value,
            date: document.getElementById('event-date').value,
            duration: document.getElementById('event-duration').value,
            people: parseInt(document.getElementById('event-people').value),
            price: parseInt(document.getElementById('event-price').value),
            location: document.getElementById('event-location').value,
            type: document.getElementById('event-type').value,
            status: document.getElementById('event-status').value,
            logo: this.tempLogoDataUrl || "assets/images/brands/img-01.png"
        };

        if (this.editingId) {
            // Update existing event
            const index = this.data.findIndex(e => e.id === this.editingId);
            if (index !== -1) {
                this.data[index] = { ...this.data[index], ...formData };
            }
        } else {
            // Add new event
            const newId = Math.max(...this.data.map(e => e.id), 0) + 1;
            this.data.unshift({ id: newId, ...formData });
        }

        // Reset and close modal
        this.resetForm();
        this.modal.hide();

        // Update filtered data and render
        this.filteredData = [...this.data];
        this.sortData();
        this.render();
    }

    
}



// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.tableManager = new TableManager();
});