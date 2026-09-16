import { createIcons, icons } from "lucide";

// data.js
const employees = [
    {
        name: "مارک جانسون", 
        email: "mark@domiex.com", 
        phone: "512-464-3203",
        department: "رادیولوژی", 
        salary: "13,000 تومان", 
        status: "ناموفق"
    },
    {
        name: "کریستوفر لی", 
        email: "lee@domiex.org", 
        phone: "563-496-7765",
        department: "چشم پزشکی", 
        salary: "13,500 تومان", 
        status: "در حال بررسی"
    },
    {
        name: "بنجامین گارسیا", 
        email: "benjamin@domiex.org", 
        phone: "210-555-0199",
        department: "روانپزشکی", 
        salary: "14,800 تومان", 
        status: "ناموفق"
    },
    {
        name: "دیوید اندرسون", 
        email: "anderson@domiex.org", 
        phone: "312-836-8072",
        department: "اورولوژی", 
        salary: "14,500 تومان", 
        status: "موفق"
    },
    {
        name: "شارلوت مارتینز", 
        email: "charlotte@domiex.com", 
        phone: "305-555-0196",
        department: "روماتولوژی", 
        salary: "15,400 تومان", 
        status: "در حال بررسی"
    },
    {
        name: "سوفیا ویلسون", 
        email: "wilson@domiex.com", 
        phone: "423-386-0823",
        department: "عصب‌شناسی", 
        salary: "16,000 تومان", 
        status: "در حال بررسی"
    }, 
    {
        name: "مایکل براون", 
        email: "brown@domiex.org", 
        phone: "706-766-2961",
        department: "اطفال", 
        salary: "12,000 تومان", 
        status: "ناموفق"
    },
    {
        name: "اما تیلور", 
        email: "emma@domiex.com", 
        phone: "216-420-1175",
        department: "پوست", 
        salary: "13,000 تومان", 
        status: "در حال بررسی"
    },
    {
        name: "لیام رابینسون", 
        email: "liam@domiex.org", 
        phone: "512-555-0178",
        department: "هماتولوژی", 
        salary: "13,700 تومان", 
        status: "موفق"
    },
    {
        name: "ریچل گرین", 
        email: "rachel@domiex.com", 
        phone: "330-733-0164",
        department: "گوارش", 
        salary: "14,000 تومان", 
        status: "ناموفق"
    },
    {
        name: "اولیویا پارکر", 
        email: "olivia@domiex.org", 
        phone: "405-723-9182",
        department: "قلب و عروق", 
        salary: "15,200 تومان", 
        status: "در حال بررسی"
    },
    {
        name: "نوح جانسون", 
        email: "noah@domiex.com", 
        phone: "718-402-3112",
        department: "عصب‌شناسی", 
        salary: "16,500 تومان", 
        status: "موفق"
    },
    {
        name: "آوا مارتینز", 
        email: "ava@domiex.org", 
        phone: "913-555-6789",
        department: "سرطان‌شناسی", 
        salary: "14,900 تومان", 
        status: "در حال بررسی"
    },
    {
        name: "ویلیام لی", 
        email: "william@domiex.com", 
        phone: "702-988-2234",
        department: "رادیولوژی", 
        salary: "13,300 تومان", 
        status: "ناموفق"
    },
    {
        name: "سوفیا آدامز", 
        email: "sophia@domiex.org", 
        phone: "208-445-1234",
        department: "ارتوپدی", 
        salary: "12,800 تومان", 
        status: "موفق"
    },
    {
        name: "جیمز واکر", 
        email: "james@domiex.com", 
        phone: "303-762-7788",
        department: "اورولوژی", 
        salary: "15,100 تومان", 
        status: "در حال بررسی"
    },
    {
        name: "میا تامپسون", 
        email: "mia@domiex.org", 
        phone: "978-556-9922",
        department: "کلیوی", 
        salary: "13,600 تومان", 
        status: "ناموفق"
    },
    {
        name: "بنجامین اسکات", 
        email: "benjamin@domiex.com", 
        phone: "646-223-3147",
        department: "غدد درون‌ریز", 
        salary: "14,500 تومان", 
        status: "ناموفق"
    },
    {
        name: "ایزابلا لوئیس", 
        email: "isabella@domiex.org", 
        phone: "210-412-9841",
        department: "ریه‌شناسی", 
        salary: "13,200 تومان", 
        status: "موفق"
    },
    {
        name: "الیجاه وایت", 
        email: "elijah@domiex.com", 
        phone: "414-909-3478",
        department: "پاتولوژی", 
        salary: "12,600 تومان", 
        status: "در حال بررسی"
    }
];

const rowsPerPage = 10;
let currentPage = 1;
let data = [...employees];
let deleteIndex = null;
let sortConfig = {
    key: null,
    direction: 'asc'
};

const tbody = document.querySelector("tbody");
const pagination = document.querySelector(".pagination");
const tableHeaders = document.querySelectorAll("thead th");

// Function to compare values for sorting
function compareValues(key, order = 'asc') {
    return function (a, b) {
        // Handle salary as special case (remove $ and convert to number)
        if (key === 'salary') {
            const valA = parseFloat(a[key].replace('$', '').replace(',', ''));
            const valB = parseFloat(b[key].replace('$', '').replace(',', ''));
            return order === 'asc' ? valA - valB : valB - valA;
        }

        // Regular string comparison
        if (a[key] < b[key]) {
            return order === 'asc' ? -1 : 1;
        }
        if (a[key] > b[key]) {
            return order === 'asc' ? 1 : -1;
        }
        return 0;
    };
}

// Sort the data based on current configuration
function sortData() {
    if (sortConfig.key) {
        data.sort(compareValues(sortConfig.key, sortConfig.direction));
    }
}

// Add sorting functionality to table headers
function setupSortableHeaders() {
    const sortableColumns = ['name', 'email', 'phone', 'department', 'salary', 'status'];

    tableHeaders.forEach((header, index) => {
        if (index < sortableColumns.length) {
            const columnKey = sortableColumns[index];

            // Add sort indicator and styling
            header.classList.add('sortable');
            header.style.cursor = 'pointer';
            const headerText = header.textContent;
            header.innerHTML = `${headerText} <span class="sort-icon"></span>`;

            // Add click event
            header.addEventListener('click', () => {
                // Toggle sort direction or set new sort key
                if (sortConfig.key === columnKey) {
                    sortConfig.direction = sortConfig.direction === 'asc' ? 'desc' : 'asc';
                } else {
                    sortConfig.key = columnKey;
                    sortConfig.direction = 'asc';
                }

                // Update headers to show sort direction
                updateSortHeaders();

                // Sort and render data
                sortData();
                currentPage = 1; // Reset to first page when sorting
                renderTable();
            });
        }
    });
}

// Update headers to show current sort direction
function updateSortHeaders() {
    tableHeaders.forEach((header, index) => {
        const sortIndicator = header.querySelector('.sort-icon');
        if (sortIndicator) {
            sortIndicator.innerHTML = '';

            if (index === ['name', 'email', 'phone', 'department', 'salary', 'status'].indexOf(sortConfig.key)) {
                // Add the appropriate sort icon
                const icon = document.createElement('i');
                icon.setAttribute('data-lucide', sortConfig.direction === 'asc' ? 'arrow-up' : 'arrow-down');
                icon.classList.add('size-4', 'ml-1', 'inline-block');
                sortIndicator.appendChild(icon);

                createIcons({ icons });
            }
        }
    });
}

function renderTable() {
    tbody.innerHTML = "";
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const pageData = data.slice(start, end);

    pageData.forEach((emp, index) => {
        const row = document.createElement("tr");
        row.innerHTML = `
        <td>${emp.name}</td>
        <td>${emp.email}</td>
        <td>${emp.phone}</td>
        <td>${emp.department}</td>
        <td>${emp.salary}</td>
        <td>
          <span class="badge ${emp.status === 'موفق' ? 'bg-success-subtle text-success border border-success-subtle' :
                emp.status === 'در حال بررسی' ? 'bg-warning-subtle text-warning border border-warning-subtle' :
                    'bg-danger-subtle text-danger border border-danger-subtle'
            }">${emp.status}</span>
        </td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <button class="btn btn-sub-primary size-8 btn-icon"><i class="ri-pencil-line"></i></button>
            <button class="btn btn-sub-danger size-8 btn-icon" data-bs-toggle="modal" data-bs-target="#deleteModal" data-index="${start + index}">
              <i class="ri-delete-bin-line"></i>
            </button>
          </div>
        </td>`;
        tbody.appendChild(row);
    });

    document.getElementById("range-start").textContent = data.length === 0 ? 0 : start + 1;
    document.getElementById("range-end").textContent = Math.min(end, data.length);
    document.getElementById("range-total").textContent = data.length;

    updatePagination();
}

function updatePagination() {
    const pageCount = Math.ceil(data.length / rowsPerPage);
    const pageLinks = [];

    for (let i = 1; i <= pageCount; i++) {
        pageLinks.push(`<li class="page-item ${i === currentPage ? 'active' : ''}">
        <a class="page-link" href="#">${i}</a></li>`);
    }

    pagination.innerHTML = `
      <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" data-nav="prev"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>
      </li>
      ${pageLinks.join('')}
      <li class="page-item ${currentPage === pageCount ? 'disabled' : ''}">
        <a class="page-link" href="#" data-nav="next">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>
      </li>
    `;

    document.querySelectorAll(".page-link").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            if (link.dataset.nav === "prev" && currentPage > 1) currentPage--;
            else if (link.dataset.nav === "next" && currentPage < pageCount) currentPage++;
            else if (!isNaN(+link.textContent)) currentPage = +link.textContent;
            renderTable();
        });
    });
    createIcons({ icons });
}

document.getElementById('deleteModal').addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    deleteIndex = +button.getAttribute('data-index');
});

document.querySelector('#deleteModal .btn-danger').addEventListener('click', function () {
    if (deleteIndex !== null) {
        data.splice(deleteIndex, 1);
        const pageCount = Math.ceil(data.length / rowsPerPage);
        if (currentPage > pageCount) currentPage = pageCount;
        renderTable();
        deleteIndex = null;
    }
});

// Initialize sorting and table
setupSortableHeaders();
renderTable();