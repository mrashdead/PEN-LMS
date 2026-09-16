import { icons, createIcons } from "lucide";



//Department Select
VirtualSelect.init({
    ele: "#departmentSelect",
    options: [
        { label: "رادیولوژی", value: "Radiology" },
        { label: "ارتوپد", value: "Orthopedics" },
        { label: "مغز و اعصاب", value: "Neurology" },
        { label: "قلب و عروق", value: "Cardiology" },
        { label: "اطفال", value: "Pediatrics" },
        { label: "مدیر", value: "Manager" },
        { label: "پرستار", value: "Nurse" },
        { label: "نگهبان امنیتی", value: "Security Officer" },
        { label: "سایر", value: "Others" },
    ],
});
//staff Select
VirtualSelect.init({
    ele: "#staffSelect",
    options: [
        { label: "رادیولوژی", value: "Radiology" },
        { label: "ارتوپد", value: "Orthopedics" },
        { label: "مغز و اعصاب", value: "Neurology" },
        { label: "قلب و عروق", value: "Cardiology" },
        { label: "اطفال", value: "Pediatrics" },
        { label: "مدیر", value: "Manager" },
        { label: "پرستار", value: "Nurse" },
        { label: "نگهبان امنیتی", value: "Security Officer" },
        { label: "سایر", value: "Others" },
    ],
    selectedValue: "Radiology",
});

// Mappings
const departmentMapping = {
    'Radiology': 'رادیولوژی',
    'Orthopedics': 'ارتوپد',
    'Neurology': 'مغز و اعصاب',
    'Cardiology': 'قلب و عروق',
    'Pediatrics': 'اطفال'
};

class TableManager {
    constructor(options) {
        this.tableBodyId = options.tableBodyId;
        this.paginationId = options.paginationId;
        this.paginationInfoId = options.paginationInfoId;
        this.formId = options.formId;
        this.modalId = options.modalId;
        this.deleteModalId = options.deleteModalId;

        this.itemsPerPage = options.itemsPerPage || 10;
        this.currentPage = 1;

        // Add sorting properties
        this.currentSortColumn = null;
        this.currentSortDirection = 'asc';

        // Initialize sample data (in a real app, this would come from an API/database)
        this.data = [
            {
                id: "PES-1595",
                name: "لین شای",
                role: "فروشنده، خرده‌فروشی",
                department: "Radiology",
                email: "fitzgeraldwilliam@gmail.com",
                phone: "+1 555 123 4567",
                joiningDate: "1400/02/20",
                image: "assets/images/avatar/user-3.png"
            },
            {
                id: "PES-1596",
                name: "رایان رینولدز",
                role: "متخصص ژنتیک مولکولی بالینی",
                department: "Orthopedics",
                email: "wdavidson@warren.org",
                phone: "+44 20 7946 0958",
                joiningDate: "1399/01/26",
                image: "assets/images/avatar/user-2.png"
            },
            {
                id: "PES-1597",
                name: "پیج ویلیامسون",
                role: "مدیر محصول",
                department: "Orthopedics",
                email: "reneehawkins@king-gonzalez.com",
                phone: "+61 2 9374 4000",
                joiningDate: "1401/12/30",
                image: ""
            },
            {
                id: "PES-1598",
                name: "راسل کرو",
                role: "چشم پزشک",
                department: "Neurology",
                email: "connie92@gonzalez.com",
                phone: "+49 30 123456",
                joiningDate: "1400/09/21",
                image: "assets/images/avatar/user-24.png"
            },
            {
                id: "PES-1599",
                name: "ترزا می",
                role: "متخصص سیتوژنتیک",
                department: "Orthopedics",
                email: "eric30@yahoo.com",
                phone: "+33 1 42 68 53 00",
                joiningDate: "1399/09/04",
                image: "assets/images/avatar/user-25.png"
            },
            {
                id: "PES-1600",
                name: "کاتلین کلارک",
                role: "متخصص ژنتیک، مولکولی",
                department: "Orthopedics",
                email: "kevintaylor@gmail.com",
                phone: "+34 91 123 45 67",
                joiningDate: "1399/03/07",
                image: "assets/images/avatar/user-26.png"
            },
            {
                id: "PES-1601",
                name: "استفانی میلر",
                role: "برنامه نویس چندرسانه‌ای",
                department: "Cardiology",
                email: "melaniebaker@yahoo.com",
                phone: "+49 40 123456",
                joiningDate: "1401/04/28",
                image: ""
            },
            {
                id: "PES-1602",
                name: "کلی کلارکسون",
                role: "مهندس مکانیک",
                department: "Cardiology",
                email: "smithmary@gmail.com",
                phone: "+81 3 1234 5678",
                joiningDate: "1399/06/09",
                image: "assets/images/avatar/user-27.png"
            },
            {
                id: "PES-1603",
                name: "نیکلاس کیج",
                role: "تکنسین حسابداری",
                department: "Radiology",
                email: "henry54@yahoo.com",
                phone: "+91 22 1234 5678",
                joiningDate: "1400/02/19",
                image: ""
            },
            {
                id: "PES-1604",
                name: "لیدیا جیمز",
                role: "نقشه بردار، تجاری/مسکونی",
                department: "Radiology",
                email: "patricia63@yahoo.com",
                phone: "+55 11 1234-5678",
                joiningDate: "1399/08/09",
                image: "assets/images/avatar/user-28.png"
            }, {
                id: "PES-1605",
                name: "رابرت ردفورد",
                role: "پرستار، کودکان",
                department: "Radiology",
                email: "brettcampos@yoder.com",
                phone: "+7 495 123-45-67",
                joiningDate: "1400/04/13",
                image: "assets/images/avatar/user-10.png"
            },
            {
                id: "PES-1606",
                name: "سامانتا گاتری",
                role: "بازرس/ارزیاب دعاوی",
                department: "Pediatrics",
                email: "danielle31@myers.org",
                phone: "+27 11 123 4567",
                joiningDate: "1400/11/27",
                image: "assets/images/avatar/user-16.png"
            },
            {
                id: "PES-1607",
                name: "دکتر آرنولد شوارتزنگر",
                role: "بانکدار سرمایه‌گذاری شرکتی",
                department: "Orthopedics",
                email: "ghall@greer.com",
                phone: "+65 6 1234 567",
                joiningDate: "1402/05/27",
                image: ""
            },
            {
                id: "PES-1608",
                name: "کلی اشنایدر",
                role: "پژوهشگر اجتماعی",
                department: "Orthopedics",
                email: "stevensmith@schmidt.net",
                phone: "+39 06 123 4567",
                joiningDate: "1401/03/25",
                image: ""
            },
            {
                id: "PES-1609",
                name: "بریتنی آرنولدز",
                role: "مسئول مدیریت پسماند",
                department: "Orthopedics",
                email: "stacystephens@joyce.biz",
                phone: "+52 55 1234 5678",
                joiningDate: "1399/08/28",
                image: "assets/images/avatar/user-19.png"
            },
            {
                id: "PES-1610",
                name: "هِدر مِیِرز",
                role: "طراح",
                department: "Pediatrics",
                email: "christinaanderson@hotmail.com",
                phone: "+86 10 1234 5678",
                joiningDate: "1403/05/22",
                image: "assets/images/avatar/user-15.png"
            },
            {
                id: "PES-1611",
                name: "الیزابت مارتینز",
                role: "خریدار رسانه",
                department: "Pediatrics",
                email: "amber58@hotmail.com",
                phone: "+31 20 123 4567",
                joiningDate: "1400/04/29",
                image: ""
            }
        ];

        this.bindEvents();
        this.setupImageUpload();
        this.renderTable();
        this.setupSortableColumns();
    }

    bindEvents() {
        // Form submission for adding/editing staff
        document.getElementById(this.formId).addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveStaff();
        });

        // Set up delete confirmation
        document.getElementById('confirmDeleteBtn').addEventListener('click', () => {
            const staffId = document.getElementById('deleteStaffId').value;
            this.deleteStaff(staffId);
        });

        // Reset form when opening modal for adding new staff
        document.getElementById('addStaffBtn').addEventListener('click', () => {
            this.resetForm();
        });
    }

    setupImageUpload() {
        const imageInput = document.getElementById('imageInput');
        const imagePreview = document.getElementById('imagePreview');
        const uploadIcon = document.getElementById('uploadIcon');
        const avatarLabel = imageInput.parentElement;
        const staffImagePath = document.getElementById('staffImagePath');

        // Click on avatar to trigger file input
        avatarLabel.addEventListener('click', () => {
            imageInput.click();
        });

        // Handle image selection
        imageInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();

                reader.onload = (event) => {
                    // Store the actual image data URL
                    imagePreview.src = event.target.result;
                    imagePreview.style.display = 'block';
                    uploadIcon.style.display = 'none';

                    // Store the data URL in the hidden field
                    staffImagePath.value = event.target.result;
                };

                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }

    resetForm() {
        document.getElementById('staffId').value = '';
        document.getElementById('staffImagePath').value = '';
        document.getElementById('staffForm').reset();
        document.getElementById('saveStaffBtn').textContent = 'افزودن کارمند';

        // Reset image preview
        const imagePreview = document.getElementById('imagePreview');
        const uploadIcon = document.getElementById('uploadIcon');
        imagePreview.style.display = 'none';
        uploadIcon.style.display = 'block';
        imagePreview.src = '';

        // Update modal title if needed
        const modalTitle = document.querySelector('#addStaffModal .card-title');
        if (modalTitle) {
            modalTitle.textContent = 'افزودن کارمند جدید';
        }
    }

    // Setup sortable column headers
    setupSortableColumns() {
        const tableHeaders = document.querySelectorAll('.sortable');

        tableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-column');
                this.sortData(column);
            });

            // Add sort icon container if it doesn't exist
            if (!header.querySelector('.sort-icon')) {
                const iconSpan = document.createElement('span');
                iconSpan.className = 'sort-icon ms-1';
                iconSpan.innerHTML = '<i class="ri-arrow-up-down-line text-muted fs-sm"></i>';
                header.appendChild(iconSpan);
            }
        });
    }

    // Sort data based on column
    sortData(column) {
        // Toggle sort direction if same column is clicked again
        if (this.currentSortColumn === column) {
            this.currentSortDirection = this.currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSortColumn = column;
            this.currentSortDirection = 'asc';
        }

        // Update sort icons
        this.updateSortIcons(column);

        // Special case for date sorting
        if (column === 'joiningDate') {
            this.data.sort((a, b) => {
                const dateA = new Date(a[column]);
                const dateB = new Date(b[column]);

                if (this.currentSortDirection === 'asc') {
                    return dateA - dateB;
                } else {
                    return dateB - dateA;
                }
            });
        }
        // Special case for name column (sorting by name not by image)
        else if (column === 'name') {
            this.data.sort((a, b) => {
                const valueA = a[column].toLowerCase();
                const valueB = b[column].toLowerCase();

                if (this.currentSortDirection === 'asc') {
                    return valueA.localeCompare(valueB);
                } else {
                    return valueB.localeCompare(valueA);
                }
            });
        }
        // General case for other columns
        else {
            this.data.sort((a, b) => {
                const valueA = a[column] ? a[column].toString().toLowerCase() : '';
                const valueB = b[column] ? b[column].toString().toLowerCase() : '';

                if (this.currentSortDirection === 'asc') {
                    return valueA.localeCompare(valueB);
                } else {
                    return valueB.localeCompare(valueA);
                }
            });
        }

        // Reset to first page after sorting
        this.currentPage = 1;

        // Re-render the table with sorted data
        this.renderTable();
    }

    // Update sort icons based on current sort state
    updateSortIcons(activeColumn) {
        const tableHeaders = document.querySelectorAll('.sortable');

        tableHeaders.forEach(header => {
            const column = header.getAttribute('data-column');
            const iconContainer = header.querySelector('.sort-icon');

            if (iconContainer) {
                // Reset all icons
                iconContainer.innerHTML = '<i class="ri-arrow-up-down-line text-muted fs-sm"></i>';

                // Set active sort icon
                if (column === activeColumn) {
                    if (this.currentSortDirection === 'asc') {
                        iconContainer.innerHTML = '<i class="ri-arrow-up-line"></i>';
                    } else {
                        iconContainer.innerHTML = '<i class="ri-arrow-down-line"></i>';
                    }
                }
            }
        });
    }

    renderTable() {
        const tableBody = document.getElementById(this.tableBodyId);
        tableBody.innerHTML = '';

        // Calculate pagination
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.data.length);
        const paginatedData = this.data.slice(startIndex, endIndex);

        // Update pagination info text
        document.getElementById(this.paginationInfoId).innerHTML =
            `نمایش <b class="me-1">${startIndex + 1}-${endIndex}</b> از <b class="ms-1">${this.data.length}</b> نتیجه`;

        // Render rows
        if (paginatedData.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center">هیچ پرونده‌ای از کارکنان یافت نشد</td></tr>';
        } else {
            paginatedData.forEach(staff => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${staff.id}</td>
                    <td>
                        <div class="d-flex align-items-center gap-3">
                            ${this.renderStaffAvatar(staff)}
                            <div>
                                <h6 class="mb-1"><a href="#!" class="text-reset">${staff.name}</a></h6>
                                <p class="fs-sm text-muted">${staff.role}</p>
                            </div>
                        </div>
                    </td>
                    <td>${departmentMapping[staff.department] || staff.department}</td>
                    <td>${staff.email}</td>
                    <td>${staff.phone}</td>
                    <td>${staff.joiningDate}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <button class="btn btn-sub-primary size-8 btn-icon edit-btn" data-id="${staff.id}">
                                <i class="ri-pencil-line"></i>
                            </button>
                            <button class="btn btn-sub-danger size-8 btn-icon delete-btn" data-id="${staff.id}">
                                <i class="ri-delete-bin-line"></i>
                            </button>
                        </div>
                    </td>
                `;
                tableBody.appendChild(row);
            });

            // Add event listeners to edit and delete buttons
            this.addActionButtonListeners();
        }

        // Render pagination
        this.renderPagination();
    }

    renderStaffAvatar(staff) {
        if (staff.image) {
            return `<img src="${staff.image}" loading="lazy" alt="${staff.name}" class="size-10 rounded-circle">`;
        } else {
            return `<div class="size-10 bg-light-subtle rounded-circle text-muted fs-sm fw-semibold d-flex justify-content-center align-items-center">
                        ${this.getInitials(staff.name)}
                    </div>`;
        }
    }

    getInitials(name) {
        return name.split(' ')
            .map(part => part.charAt(0))
            .join('')
            .toUpperCase();
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const options = { day: 'numeric', month: 'short', year: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    addActionButtonListeners() {
        // Edit button listeners
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const staffId = btn.getAttribute('data-id');
                this.editStaff(staffId);
            });
        });

        // Delete button listeners
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const staffId = btn.getAttribute('data-id');
                document.getElementById('deleteStaffId').value = staffId;

                // Show delete modal
                const deleteModal = new window.bootstrap.Modal(document.getElementById(this.deleteModalId));
                deleteModal.show();
            });
        });
    }

    renderPagination() {
        const paginationElement = document.getElementById(this.paginationId);
        paginationElement.innerHTML = '';

        const totalPages = Math.ceil(this.data.length / this.itemsPerPage);

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        prevLi.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.renderTable();
            }
        });
        paginationElement.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
            li.addEventListener('click', () => {
                this.currentPage = i;
                this.renderTable();
            });
            paginationElement.appendChild(li);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        nextLi.addEventListener('click', () => {
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.renderTable();
            }
        });
        paginationElement.appendChild(nextLi);

        createIcons({ icons });
    }

    editStaff(staffId) {
        const staff = this.data.find(item => item.id === staffId);
        if (!staff) return;

        // Fill the form with staff data
        document.getElementById('staffId').value = staff.id;
        document.getElementById('staffImagePath').value = staff.image || '';
        document.getElementById('fullName').value = staff.name;
        document.getElementById('role').value = staff.role;

        // Handle department select
        document.getElementById('department').value = staff.department;

        document.getElementById('email').value = staff.email;
        document.getElementById('phone').value = staff.phone;
        document.getElementById('joiningDate').value = staff.joiningDate || '';


        // Update image preview
        const imagePreview = document.getElementById('imagePreview');
        const uploadIcon = document.getElementById('uploadIcon');

        if (staff.image) {
            imagePreview.src = staff.image;
            imagePreview.style.display = 'block';
            uploadIcon.style.display = 'none';
        } else {
            imagePreview.style.display = 'none';
            uploadIcon.style.display = 'block';
        }

        // Update button text
        document.getElementById('saveStaffBtn').textContent = 'آپدیت کارمند';

        // Show modal
        const modal = new window.bootstrap.Modal(document.getElementById(this.modalId));
        modal.show();
    }

    saveStaff() {
        const staffId = document.getElementById('staffId').value;
        const isEditing = staffId !== '';

        // Get image data
        const staffImagePath = document.getElementById('staffImagePath');
        const imagePreview = document.getElementById('imagePreview');
        let imagePath;
        if (imagePreview.style.display !== 'none') {
            // If image is visible, use either the stored path or the actual image data URL
            imagePath = staffImagePath.value || imagePreview.src;
        } else {
            // No image selected
            imagePath = '';
        }

        const staffData = {
            name: document.getElementById('fullName').value,
            role: document.getElementById('role').value,
            department: document.getElementById('department').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            joiningDate: document.getElementById('joiningDate').value,
            image: imagePath
        };

        if (isEditing) {
            // Update existing staff
            const index = this.data.findIndex(item => item.id === staffId);
            if (index !== -1) {
                this.data[index] = {
                    ...this.data[index],
                    ...staffData
                };
            }
        } else {
            // Add new staff
            const newId = `PES-${1599 + this.data.length}`;
            this.data.unshift({
                id: newId,
                ...staffData
            });
        }

        // Hide modal
        const modal = window.bootstrap.Modal.getInstance(document.getElementById(this.modalId));
        modal.hide();

        // Reset form and refresh table
        this.resetForm();
        this.renderTable();
    }

    deleteStaff(staffId) {
        this.data = this.data.filter(item => item.id !== staffId);

        // Hide delete modal
        const deleteModal = window.bootstrap.Modal.getInstance(document.getElementById(this.deleteModalId));
        deleteModal.hide();

        // Calculate new current page if necessary
        const totalPages = Math.ceil(this.data.length / this.itemsPerPage);
        if (this.currentPage > totalPages && totalPages > 0) {
            this.currentPage = totalPages;
        }

        // Re-render table
        this.renderTable();
    }
}

// Initialize the table manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const tableManager = new TableManager({
        tableBodyId: 'staffTableBody',
        paginationId: 'pagination',
        paginationInfoId: 'paginationInfo',
        formId: 'staffForm',
        modalId: 'addStaffModal',
        deleteModalId: 'deleteModal',
        itemsPerPage: 10
    });
});