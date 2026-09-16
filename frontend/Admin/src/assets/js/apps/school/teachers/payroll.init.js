import { createIcons, icons } from "lucide";

//sorting Select
VirtualSelect.init({
    ele: "#sorting",
    options: [
        { label: "همه", value: "all" },
        { label: "وضعیت", value: "status" },
        { label: "مالیات", value: "taxes" },
        { label: "معلمان", value: "teacherName" },
    ],
});
const teachersData = [
    {
        name: "علی مصفا",
        avatar: "assets/images/avatar/user-1.png",
        email: "john@domiex.com",
        phone: "520-323-0053",
        taxes: "20,000 تومان",
        salary: "50,000 تومان",
        performance: { label: "عالی", badgeClass: "bg-orange-subtle border border-orange-subtle text-orange" },
        status: { label: "فعال", badgeClass: "bg-success-subtle border border-success-subtle text-success" }
    },
    {
        name: "نوید پورفرج",
        avatar: "assets/images/avatar/user-2.png",
        email: "jane@domiex.com",
        phone: "516-741-7919",
        taxes: "22,000 تومان",
        salary: "53,000 تومان",
        performance: { label: "خوب", badgeClass: "bg-secondary-subtle border border-secondary-subtle text-secondary" },
        status: { label: "فعال", badgeClass: "bg-success-subtle border border-success-subtle text-success" }
    },
    {
        name: "مایکل جکسون",
        avatarInitials: "MJ",
        email: "michael@domiex.com",
        phone: "405-275-2667",
        taxes: "25,000 تومان",
        salary: "55,000 تومان",
        performance: { label: "عالی", badgeClass: "bg-orange-subtle border border-orange-subtle text-orange" },
        status: { label: "فعال", badgeClass: "bg-success-subtle border border-success-subtle text-success" }
    },
    // Add all other teachers here similarly...
    {
        name: "گلاره عباسی",
        avatar: "assets/images/avatar/user-4.png",
        email: "davis@domiex.com",
        phone: "231-373-3308",
        taxes: "18,000 تومان",
        salary: "47,000 تومان",
        performance: { label: "خوب", badgeClass: "bg-secondary-subtle border border-secondary-subtle text-secondary" },
        status: { label: "غیرفعال", badgeClass: "bg-warning-subtle border border-warning-subtle text-warning" }
    },
    {
        name: "علی صادقی",
        avatar: "assets/images/avatar/user-5.png",
        email: "james@domiex.com",
        phone: "765-213-8926",
        taxes: "19,000 تومان",
        salary: "49,000 تومان",
        performance: { label: "رضایت‌بخش", badgeClass: "bg-info-subtle border border-info-subtle text-info" },
        status: { label: "فعال", badgeClass: "bg-success-subtle border border-success-subtle text-success" }
    },
    {
        name: "ستاره پسیانی",
        avatar: "assets/images/avatar/user-6.png",
        email: "patricia@domiex.com",
        phone: "717-578-7551",
        taxes: "21,000 تومان",
        salary: "52,000 تومان",
        performance: { label: "عالی", badgeClass: "bg-orange-subtle border border-orange-subtle text-orange" },
        status: { label: "فعال", badgeClass: "bg-success-subtle border border-success-subtle text-success" }
    },
    {
        name: "رابرت ردفورد",
        avatarInitials: "RR",
        email: "rob_robert@domiex.com",
        phone: "253-458-4052",
        taxes: "23,000 تومان",
        salary: "55,000 تومان",
        performance: { label: "خوب", badgeClass: "bg-secondary-subtle border border-secondary-subtle text-secondary" },
        status: { label: "فعال", badgeClass: "bg-success-subtle border border-success-subtle text-success" }
    },
    {
        name: "لیندا اندرسون",
        avatarInitials: "LA",
        email: "anderson@domiex.com",
        phone: "703-715-2022",
        taxes: "20,000 تومان",
        salary: "52,000 تومان",
        performance: { label: "رضایت‌بخش", badgeClass: "bg-info-subtle border border-info-subtle text-info" },
        status: { label: "غیرفعال", badgeClass: "bg-warning-subtle border border-warning-subtle text-warning" }
    },
    {
        name: "بروس لی",
        avatar: "assets/images/avatar/user-9.png",
        email: "thomas@domiex.com",
        phone: "386-313-6709",
        taxes: "22,000 تومان",
        salary: "54,000 تومان",
        performance: { label: "عالی", badgeClass: "bg-orange-subtle border border-orange-subtle text-orange" },
        status: { label: "فعال", badgeClass: "bg-success-subtle border border-success-subtle text-success" }
    },
    {
        name: "باربارا کریمی",
        avatar: "assets/images/avatar/user-10.png",
        email: "barbara@domiex.com",
        phone: "910-539-9223",
        taxes: "20,000 تومان",
        salary: "50,000 تومان",
        performance: { label: "خوب", badgeClass: "bg-secondary-subtle border border-secondary-subtle text-secondary" },
        status: { label: "فعال", badgeClass: "bg-success-subtle border border-success-subtle text-success" }
    }
];

const rowsPerPage = 10;  // You can change how many rows per page here
let currentPage = 1;
let filteredData = [...teachersData];
// Sort configuration
let currentSortColumn = null;
let currentSortDirection = "asc";

const tableBody = document.getElementById("teacherTableBody");
const paginationContainer = document.getElementById("pagination");
const resultsInfo = document.getElementById("resultsInfo");
const searchInput = document.getElementById("searchInvoiceInput");

// Add click listeners to the table headers for sorting
function setupSortableHeaders() {
    const headers = document.querySelectorAll("th.sortable");
    headers.forEach(header => {
        header.addEventListener("click", () => {
            const column = header.getAttribute("data-sort");
            toggleSort(column);
        });
    });
}

// Toggle sort direction and update the table
function toggleSort(column) {
    if (currentSortColumn === column) {
        // Toggle direction if the same column is clicked again
        currentSortDirection = currentSortDirection === "asc" ? "desc" : "asc";
    } else {
        // New column, default to ascending
        currentSortColumn = column;
        currentSortDirection = "asc";
    }

    // Update header classes to show sort direction
    updateSortHeaderClasses();

    // Sort the data and re-render
    sortData();
    updateTable();
}

// Update the visual indicators on the table headers
function updateSortHeaderClasses() {
    const headers = document.querySelectorAll("th.sortable");
    headers.forEach(header => {
        const column = header.getAttribute("data-sort");
        // Remove all sort indicators
        header.classList.remove("sort-asc", "sort-desc");

        // Clear existing icons
        const iconSpan = header.querySelector(".sort-icon");
        if (iconSpan) {
            iconSpan.innerHTML = "";
        }

        // Add indicator for the current sort column
        if (column === currentSortColumn) {
            if (currentSortDirection === "asc") {
                header.classList.add("sort-asc");
                if (iconSpan) {
                    // Add up arrow
                    iconSpan.innerHTML = '<i data-lucide="arrow-up" class="size-3"></i>';
                }
            } else {
                header.classList.add("sort-desc");
                if (iconSpan) {
                    // Add down arrow
                    iconSpan.innerHTML = '<i data-lucide="arrow-down" class="size-3"></i>';
                }
            }
        }
    });
}

// Sort the data based on the current sort column and direction
function sortData() {
    if (!currentSortColumn) return;

    filteredData.sort((a, b) => {
        let valueA, valueB;

        // Extract the correct property based on the column
        switch (currentSortColumn) {
            case "name":
                valueA = a.name;
                valueB = b.name;
                break;
            case "email":
                valueA = a.email;
                valueB = b.email;
                break;
            case "phone":
                valueA = a.phone;
                valueB = b.phone;
                break;
            case "taxes":
                // Strip $ and commas for numeric comparison
                valueA = parseFloat(a.taxes.replace(/[$,]/g, ""));
                valueB = parseFloat(b.taxes.replace(/[$,]/g, ""));
                break;
            case "salary":
                // Strip $ and commas for numeric comparison
                valueA = parseFloat(a.salary.replace(/[$,]/g, ""));
                valueB = parseFloat(b.salary.replace(/[$,]/g, ""));
                break;
            case "performance":
                valueA = a.performance.label;
                valueB = b.performance.label;
                break;
            case "status":
                valueA = a.status.label;
                valueB = b.status.label;
                break;
            default:
                return 0;
        }

        // Compare values based on direction
        let comparison = 0;
        if (valueA > valueB) {
            comparison = 1;
        } else if (valueA < valueB) {
            comparison = -1;
        }

        // Reverse for descending sort
        return currentSortDirection === "desc" ? comparison * -1 : comparison;
    });
}

function renderTable(data, page) {
    tableBody.innerHTML = "";
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const pageData = data.slice(start, end);

    if (pageData.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td colspan="7" class="text-center py-4">
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
                        <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164 S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331 c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                        <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0 l-4.331-4.331"></path>
                        <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                        <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                    </svg>
                    <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                    <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    } else {
        pageData.forEach(item => {
            const avatarHtml = item.avatar
                ? `<img src="${item.avatar}" loading="lazy" alt="" class="size-6 rounded-pill">`
                : `<div class="size-6 rounded-pill text-muted fw-semibold fs-11 bg-light-subtle avatar">${item.avatarInitials}</div>`;

            const row = document.createElement("tr");
            row.innerHTML = `
                <td>
                    <div class="d-flex align-items-center gap-3">
                        ${avatarHtml}
                        <h6 class="mb-0"><a href="apps-school-students-overview.html" class="text-reset">${item.name}</a></h6>
                    </div>
                </td>
                <td>${item.email}</td>
                <td>${item.phone}</td>
                <td>${item.taxes}</td>
                <td>${item.salary}</td>
                <td><span class="badge ${item.performance.badgeClass}">${item.performance.label}</span></td>
                <td><span class="badge ${item.status.badgeClass}">${item.status.label}</span></td>
            `;
            tableBody.appendChild(row);
        });
    }

    const showingFrom = data.length === 0 ? 0 : start + 1;
    const showingTo = Math.min(end, data.length);
    resultsInfo.innerHTML = `نمایش <b>${showingFrom}-${showingTo}</b> از <b>${data.length}</b> نتیجه`;
}

function renderPagination(data) {
    paginationContainer.innerHTML = "";

    const totalPages = Math.ceil(data.length / rowsPerPage);
    if (totalPages === 0) return;

    // Previous Button
    const prevLi = document.createElement("li");
    prevLi.className = `page-item ${currentPage === 1 ? "disabled" : ""}`;
    prevLi.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
    prevLi.addEventListener("click", e => {
        e.preventDefault();
        if (currentPage > 1) {
            currentPage--;
            updateTable();
        }
    });
    paginationContainer.appendChild(prevLi);

    // Page numbers (simple max 5 pages showing)
    const maxPagesToShow = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = startPage + maxPagesToShow - 1;
    if (endPage > totalPages) {
        endPage = totalPages;
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement("li");
        pageLi.className = `page-item ${i === currentPage ? "active" : ""}`;
        pageLi.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
        pageLi.addEventListener("click", e => {
            e.preventDefault();
            currentPage = i;
            updateTable();
        });
        paginationContainer.appendChild(pageLi);
    }

    // Next Button
    const nextLi = document.createElement("li");
    nextLi.className = `page-item ${currentPage === totalPages ? "disabled" : ""}`;
    nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
    nextLi.addEventListener("click", e => {
        e.preventDefault();
        if (currentPage < totalPages) {
            currentPage++;
            updateTable();
        }
    });
    paginationContainer.appendChild(nextLi);
    createIcons({ icons });
}

function updateTable() {
    renderTable(filteredData, currentPage);
    renderPagination(filteredData);
}

// Search filter
searchInput.addEventListener("input", () => {
    const term = searchInput.value.trim().toLowerCase();
    filteredData = teachersData.filter(item =>
        item.name.toLowerCase().includes(term) ||
        item.email.toLowerCase().includes(term) ||
        item.phone.toLowerCase().includes(term) ||
        item.performance.label.toLowerCase().includes(term) ||
        item.status.label.toLowerCase().includes(term)
    );
    currentPage = 1;
    // Re-apply current sort if one is active
    if (currentSortColumn) {
        sortData();
    }
    updateTable();
});

// Initialize
updateTable();
// Add sort functionality to headers after table is initialized
setupSortableHeaders()
// Initialize the Lucide icons
createIcons({ icons });