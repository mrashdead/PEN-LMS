import { createIcons, icons } from "lucide";

//sorting Select
VirtualSelect.init({
    ele: "#sortingByClass",
    options: [
        { label: "12 (A)", value: "12 (A)" },
        { label: "12 (B)", value: "12 (B)" },
        { label: "11 (A)", value: "11 (A)" },
        { label: "11 (B)", value: "11 (B)" },
        { label: "10 (A)", value: "10 (A)" },
        { label: "10 (B)", value: "10 (B)" },
        { label: "9", value: "9" },
        { label: "8", value: "8" }
    ],
});

// students.js - Contains the student data
const studentsData = [
    {
        id: "PES-1606",
        name: "آوا دیویس",
        avatar: "assets/images/avatar/user-11.png",
        gender: "مرد",
        rollNo: "29",
        class: "10 (A)",
        email: "ava@gmail.com",
        phone: "+1 741 65 2257",
        birthDate: "4 آبان 1383",
        joiningDate: "12 خرداد 1403",
        hasAvatar: true
    },
    {
        id: "PES-1596",
        name: "سیلویا هوور",
        avatar: "assets/images/avatar/user-5.png",
        gender: "زن",
        rollNo: "48",
        class: "11 (B)",
        email: "silvia@gmail.com",
        phone: "+54 4514 45785",
        birthDate: "1 دی 1385",
        joiningDate: "30 اردیبهشت 1403",
        hasAvatar: true
    },
    {
        id: "PES-1597",
        name: "رابرت فرگوسن",
        avatar: "",
        gender: "مرد",
        rollNo: "32",
        class: "11 (A)",
        email: "robert@gmail.com",
        phone: "+245 15 145 74",
        birthDate: "25 خرداد 1381",
        joiningDate: "13 خرداد 1403",
        hasAvatar: false,
        initials: "RF"
    },
    {
        id: "PES-1598",
        name: "امیلی براون",
        avatar: "",
        gender: "زن",
        rollNo: "20",
        class: "9",
        email: "emily@gmail.com",
        phone: "+1 625 15 1523",
        birthDate: "21 بهمن 1382",
        joiningDate: "29 خرداد 1403",
        hasAvatar: false,
        initials: "EB"
    },
    {
        id: "PES-1599",
        name: "مایکل جانسون",
        avatar: "assets/images/avatar/user-3.png",
        gender: "مرد",
        rollNo: "8",
        class: "10 (A)",
        email: "michael@gmail.com",
        phone: "+1 712 25 1525",
        birthDate: "14 اسفند 1385",
        joiningDate: "26 خرداد 1403",
        hasAvatar: true
    },
    {
        id: "PES-1600",
        name: "جسیکا لی",
        avatar: "",
        gender: "زن",
        rollNo: "16",
        class: "12 (A)",
        email: "jessica@gmail.com",
        phone: "+1 845 35 1623",
        birthDate: "6 اردیبهشت 1383",
        joiningDate: "13 خرداد 1403",
        hasAvatar: false,
        initials: "JL"
    },
    {
        id: "PES-1601",
        name: "دنیل هریس",
        avatar: "assets/images/avatar/user-6.png",
        gender: "زن",
        rollNo: "49",
        class: "11 (B)",
        email: "daniel@gmail.com",
        phone: "+1 945 15 1627",
        birthDate: "30 اردیبهشت 1385",
        joiningDate: "21 خرداد 1403",
        hasAvatar: true
    },
    {
        id: "PES-1602",
        name: "اولیویا مارتین",
        avatar: "",
        gender: "مرد",
        rollNo: "57",
        class: "10 (B)",
        email: "olivia@gmail.com",
        phone: "+1 741 25 1823",
        birthDate: "14 خرداد 1386",
        joiningDate: "19 خرداد 1403",
        hasAvatar: false,
        initials: "OM"
    },
    {
        id: "PES-1603",
        name: "ایتن ویلسون",
        avatar: "assets/images/avatar/user-8.png",
        gender: "زن",
        rollNo: "16",
        class: "12 (A)",
        email: "ethan@gmail.com",
        phone: "+1 815 35 1923",
        birthDate: "9 مرداد 1383",
        joiningDate: "17 خرداد 1403",
        hasAvatar: true
    },
    {
        id: "PES-1604",
        name: "سوفیا مور",
        avatar: "assets/images/avatar/user-9.png",
        gender: "زن",
        rollNo: "49",
        class: "11 (B)",
        email: "sophia@gmail.com",
        phone: "+1 912 45 2025",
        birthDate: "14 مرداد 1385",
        joiningDate: "15 خرداد 1403",
        hasAvatar: true
    },
    {
        id: "PES-1605",
        name: "ویلیام جکسون",
        avatar: "",
        gender: "مرد",
        rollNo: "22",
        class: "10 (A)",
        email: "william@gmail.com",
        phone: "+1 847 65 1857",
        birthDate: "21 شهریور 1384",
        joiningDate: "14 خرداد 1403",
        hasAvatar: false,
        initials: "WJ"
    },
    {
        id: "PES-1607",
        name: "ایزابلا تامپسون",
        avatar: "assets/images/avatar/user-10.png",
        gender: "زن",
        rollNo: "35",
        class: "9 (A)",
        email: "isabella@gmail.com",
        phone: "+1 721 65 2357",
        birthDate: "28 آبان 1383",
        joiningDate: "16 خرداد 1403",
        hasAvatar: true
    }
];


// Pagination, search, and sorting configuration
let currentPage = 1;
const recordsPerPage = 10;
let filteredStudents = [...studentsData];
let currentSortColumn = null;
let currentSortDirection = 'asc';

// DOM Elements
document.addEventListener('DOMContentLoaded', function () {
    // Initialize the table with data
    renderStudentsTable();

    // Generate pagination on page load
    updatePaginationUI();

    // Setup search functionality
    const searchInput = document.getElementById('searchInvoiceInput');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            searchStudents(this.value);
        });
    }

    // Setup class filter dropdown
    const classFilterDropdown = document.getElementById('sortingByClass');
    if (classFilterDropdown) {
        classFilterDropdown.addEventListener('change', function () {
            filterByClass(this.value);
        });
    }

    // Setup delete modal functionality
    setupDeleteModal();

    // Setup sortable table headers
    setupSortableHeaders();

    // Initialize icons
    createIcons({ icons });
});

// Function to setup sortable headers
function setupSortableHeaders() {
    const sortableHeaders = document.querySelectorAll('th.sortable');
    if (!sortableHeaders) return;

    sortableHeaders.forEach(header => {
        header.addEventListener('click', function () {
            const column = this.getAttribute('data-column');
            if (column) {
                sortStudents(column);
            }
        });
    });
}

// Function to sort students
function sortStudents(column) {
    // If clicking the same column, toggle direction
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'asc';
    }

    // Update sort indicators on all headers
    updateSortIndicators(column, currentSortDirection);

    // Sort the filtered students array
    filteredStudents.sort((a, b) => {
        let valueA, valueB;

        // Special handling for specific columns
        if (column === 'name') {
            valueA = a.name.toLowerCase();
            valueB = b.name.toLowerCase();
        } else if (column === 'rollNo') {
            valueA = parseInt(a.rollNo) || 0;
            valueB = parseInt(b.rollNo) || 0;
        } else {
            valueA = a[column] ? a[column].toLowerCase() : '';
            valueB = b[column] ? b[column].toLowerCase() : '';
        }

        // For numeric values
        if (typeof valueA === 'number' && typeof valueB === 'number') {
            return currentSortDirection === 'asc' ? valueA - valueB : valueB - valueA;
        }

        // For string values
        if (currentSortDirection === 'asc') {
            return valueA.localeCompare(valueB);
        } else {
            return valueB.localeCompare(valueA);
        }
    });

    // Reset to first page after sorting
    currentPage = 1;
    renderStudentsTable();
    updatePaginationUI();
}

// Function to update sort indicators in the UI
function updateSortIndicators(activeColumn, direction) {
    const headers = document.querySelectorAll('th.sortable');
    headers.forEach(header => {
        const column = header.getAttribute('data-column');
        const iconContainer = header.querySelector('.sort-icon');

        if (!iconContainer) {
            // Create icon container if it doesn't exist
            const container = document.createElement('span');
            container.className = 'sort-icon ms-1';
            header.appendChild(container);
        }

        if (column === activeColumn) {
            if (direction === 'asc') {
                iconContainer.innerHTML = '<i data-lucide="arrow-up" class="size-3"></i>';
            } else {
                iconContainer.innerHTML = '<i data-lucide="arrow-down" class="size-3"></i>';
            }
        } else {
            iconContainer.innerHTML = ''; // Clear other column icons
        }
    });

    // Reinitialize Lucide icons
    createIcons({ icons });
}

// Function to filter by class
function filterByClass(classValue) {
    if (!classValue || classValue === '') {
        filteredStudents = [...studentsData];
    } else {
        filteredStudents = studentsData.filter(student => student.class === classValue);
    }

    currentPage = 1; // Reset to first page when filtering
    renderStudentsTable();
    updatePaginationUI();
}

// Function to search students
function searchStudents(query) {
    query = query.toLowerCase().trim();

    if (query === '') {
        filteredStudents = [...studentsData];
    } else {
        filteredStudents = studentsData.filter(student => {
            return (
                student.name.toLowerCase().includes(query) ||
                student.id.toLowerCase().includes(query) ||
                student.class.toLowerCase().includes(query) ||
                student.email.toLowerCase().includes(query) ||
                student.gender.toLowerCase().includes(query) ||
                student.rollNo.includes(query)
            );
        });
    }

    currentPage = 1; // Reset to first page when searching
    renderStudentsTable();
    updatePaginationUI();
}

// Function to render the students table
function renderStudentsTable() {
    const tableBody = document.querySelector('tbody');
    if (!tableBody) return;

    const startIndex = (currentPage - 1) * recordsPerPage;
    const endIndex = startIndex + recordsPerPage;
    const currentPageData = filteredStudents.slice(startIndex, endIndex);

    let tableHTML = '';

    if (currentPageData.length === 0) {
        tableHTML = `<tr><td colspan="10" class="text-center py-4">
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
        currentPageData.forEach(student => {
            let avatarHTML = '';
            if (student.hasAvatar) {
                avatarHTML = `<img src="${student.avatar}" loading="lazy" alt="${student.name}" class="size-8 rounded-pill">`;
            } else {
                avatarHTML = `<div class="size-8 rounded-pill bg-light-subtle avatar fs-12 fw-semibold text-muted">${student.initials}</div>`;
            }

            tableHTML += `
                <tr data-student-id="${student.id}">
                    <td>${student.id}</td>
                    <td>
                        <div class="d-flex align-items-center gap-3">
                            ${avatarHTML}
                            <h6 class="mb-0"><a href="apps-school-students-overview.html" class="link link-custom">${student.name}</a></h6>
                        </div>
                    </td>
                    <td>${student.gender}</td>
                    <td>${student.rollNo}</td>
                    <td>${student.class}</td>
                    <td>${student.email}</td>
                    <td>${student.phone}</td>
                    <td>${student.birthDate}</td>
                    <td>${student.joiningDate}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <a href="#!" class="btn btn-sub-primary size-8 btn-icon" aria-label="edit-button"><i class="ri-pencil-line"></i></a>
                            <button role="button" class="btn btn-sub-danger size-8 btn-icon delete-btn" aria-label="delete-button" data-bs-toggle="modal" data-bs-target="#deleteModal" data-student-id="${student.id}"><i class="ri-delete-bin-line"></i></button>
                        </div>
                    </td>
                </tr>
            `;
        });
    }

    tableBody.innerHTML = tableHTML;

    // Update the pagination info
    updatePaginationInfo();

    // Reattach event listeners to delete buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const studentId = this.getAttribute('data-student-id');
            handleDeleteButtonClick(studentId);
        });
    });
}

// Function to update pagination info text
function updatePaginationInfo() {
    const paginationInfo = document.querySelector('#showingResults');
    if (!paginationInfo) return;

    const startIndex = filteredStudents.length === 0 ? 0 : (currentPage - 1) * recordsPerPage + 1;
    const endIndex = Math.min(startIndex + recordsPerPage - 1, filteredStudents.length);

    paginationInfo.innerHTML = `نمایش <b class="me-1">${startIndex === 0 ? 0 : startIndex}-${endIndex}</b>از<b class="ms-1">${filteredStudents.length}</b> نتیجه`;
}

// Function to create pagination UI
function updatePaginationUI() {
    const totalPages = Math.max(1, Math.ceil(filteredStudents.length / recordsPerPage));
    const paginationEl = document.querySelector('.pagination');
    if (!paginationEl) return;

    let paginationHTML = '';

    // Previous button
    paginationHTML += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>
    </li>`;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        paginationHTML += `<li class="page-item ${currentPage === i ? 'active' : ''}">
            <a class="page-link" href="#!">${i}</a>
        </li>`;
    }

    // Next button
    paginationHTML += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>
    </li>`;

    paginationEl.innerHTML = paginationHTML;

    // Reattach event listeners
    setupPaginationEvents();

    createIcons({ icons });
}

// Function to set up pagination event listeners
function setupPaginationEvents() {
    document.querySelectorAll('.pagination .page-link').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();

            // Previous button
            if (this.innerHTML.includes('قبلی')) {
                if (currentPage > 1) {
                    currentPage--;
                    renderStudentsTable();
                    updatePaginationUI();
                }
                return;
            }

            // Next button
            if (this.innerHTML.includes('بعدی')) {
                const totalPages = Math.ceil(filteredStudents.length / recordsPerPage);
                if (currentPage < totalPages) {
                    currentPage++;
                    renderStudentsTable();
                    updatePaginationUI();
                }
                return;
            }

            // Number buttons
            const pageNum = parseInt(this.textContent);
            if (!isNaN(pageNum)) {
                currentPage = pageNum;
                renderStudentsTable();
                updatePaginationUI();
            }
        });
    });
}

// Delete functionality
let studentToDelete = null;

function handleDeleteButtonClick(studentId) {
    studentToDelete = studentId;
    // The modal will be shown automatically through bootstrap's data-bs-toggle attribute
}

function setupDeleteModal() {
    const deleteButton = document.querySelector('#deleteModal .btn-danger');
    if (deleteButton) {
        deleteButton.addEventListener('click', function () {
            if (studentToDelete) {
                deleteStudent(studentToDelete);
                studentToDelete = null;
            }
        });
    }
}

function deleteStudent(studentId) {
    // Remove from the original data array
    const studentIndex = studentsData.findIndex(student => student.id === studentId);
    if (studentIndex !== -1) {
        studentsData.splice(studentIndex, 1);
    }

    // Remove from filtered data array as well
    const filteredIndex = filteredStudents.findIndex(student => student.id === studentId);
    if (filteredIndex !== -1) {
        filteredStudents.splice(filteredIndex, 1);
    }

    // Check if we need to adjust the current page
    const totalPages = Math.max(1, Math.ceil(filteredStudents.length / recordsPerPage));
    if (currentPage > totalPages) {
        currentPage = totalPages;
    }

    // Re-render the table
    renderStudentsTable();
    updatePaginationUI();
}