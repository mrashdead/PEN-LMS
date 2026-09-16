import ApexCharts from '../../libs/apexcharts/apexcharts.esm.js'
import { createIcons, icons } from 'lucide';

function getColor(color) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(color).trim();
    // If the value is in RGB format (e.g., "23, 162, 184"), wrap it in `rgb()`
    if (/^\d{1,3},\s*\d{1,3},\s*\d{1,3}$/.test(value)) {
        return `rgb(${value})`;
    }
    return value;
}
var allCharts = [];

const replaceCSSVariables = (obj) => {
    const updatedObj = JSON.parse(JSON.stringify(obj)); // Deep clone the object

    const traverseAndReplace = (node) => {
        for (const key in node) {
            if (typeof node[key] === 'string' && node[key].startsWith('--dx-')) {
                // Replace the CSS variable with its computed value
                node[key] = getColor(node[key]);
            } else if (typeof node[key] === 'object' && node[key] !== null) {
                // Recursively traverse nested objects/arrays
                traverseAndReplace(node[key]);
            }
        }
    };

    traverseAndReplace(updatedObj);
    return updatedObj;
};

function updateAllCharts(theme = "") {
    theme ? document.documentElement.setAttribute('data-colors', theme) : '';
    allCharts.forEach(chart => {
        const jsonData = JSON.parse(JSON.stringify(chart[0].data));
        const data = replaceCSSVariables(structuredClone(jsonData));
        if (chart[0].chart)
            chart[0].chart.destroy();

        var chart2 = new ApexCharts(document.querySelector("#" + chart[0].id), data);
        chart2.render();
        chart[0].chart = chart2;
    });
}

document.querySelectorAll('input[name="data-colors"]').forEach(radio => {
    radio.addEventListener('change', function () {
        renderCharts(this.value);
    });
});

document.querySelectorAll('input[name="data-bs-theme"]').forEach(radio => {
    radio.addEventListener('change', function () {
        renderCharts(this.value);
    });
});

document.getElementById('darkModeButton')?.addEventListener('click', function () {
    renderCharts(this.value);
})

function renderCharts(val) {
    setTimeout(() => {
        updateAllCharts(val);
    }, 0);
}

//Patient visit Chart
var options = {
    series: [{
        name: 'سود خالص',
        data: [32, 39, 43, 49, 52, 58, 63, 60, 66]
    }],
    chart: {
        height: 320,
        type: "bar",
        toolbar: {
            show: false,
        }
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: '55%',
            endingShape: 'rounded'
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
    },
    xaxis: {
        categories: ['دی', 'آذر', 'آبان', 'مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت'],
    },
    fill: {
        opacity: 1
    },
    yaxis: {
        show: false,
    },
    grid: {
        show: false,
        xaxis: {
            lines: {
                show: false
            }
        },
        yaxis: {
            lines: {
                show: false
            }
        },
        padding: {
            top: -30,
            right: 0,
            bottom: -12,
            left: 0
        },
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        },
        y: {
            formatter: function (val) {
                return "$ " + val + "k"
            }
        }
    },
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-danger", "--dx-secondary"],
};

allCharts.push([{ 'id': 'patientVisitChart', 'data': options }]);

//Patient Visit by Department Chart
var options = {
    series: [44, 55, 41, 18],
    labels: ["قلب و عروق", "مغز و اعصاب", "ارتوپدی", "اطفال"],
    chart: {
        height: 160,
        type: "donut",
    },
    plotOptions: {
        pie: {
            startAngle: -90,
            endAngle: 270
        }
    },
    dataLabels: {
        enabled: false
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    fill: {
        type: 'gradient',
    },
    legend: {
        formatter: function (val, opts) {
            return val + " - " + opts.w.globals.series[opts.seriesIndex]
        }
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: '100%',
                height: 150,
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary"],
};

allCharts.push([{ 'id': 'patientDepartmentChart', 'data': options }]);

//Patients History
var options = {
    series: [
        {
            name: "تزریق به بیماران",
            data: [24, 32, 28, 62, 67, 80, 96, 106]
        },
        {
            name: "بیماران جراحی",
            data: [5, 14, 19, 27, 35, 44, 22, 49]
        }
    ],
    chart: {
        defaultLocale: "en",
        height: 205,
        type: "line",
        toolbar: {
            show: false,
        }
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        curve: 'smooth',
        width: 3,
        lineCap: 'butt',
    },
    xaxis: {
        categories: [
            "اسفند",
            "بهمن",
            "دی",
            "آذر",
            "آبان",
            "مهر",
            "شهریور",
            "مرداد",
            "تیر",
            "خرداد",
            "اردیبهشت",
            "فروردین"
        ],
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        },
        x: {
            show: true
        },
    },
    grid: {
        strokeDashArray: 4,
        position: 'back',
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-secondary"],
};

allCharts.push([{ 'id': 'patientsHistoryChart', 'data': options }]);


//Hospital Birth & Death Chart
var options = {
    series: [{
        name: 'مورد تولد',
        data: [80, 50, 30, 70, 99, 36],
    }, {
        name: 'مورد مرگ و میر',
        data: [10, 14, 28, 16, 34, 87],
    }, {
        name: 'مورد تصادف',
        data: [44, 98, 54, 46, 34, 22],
    }],
    chart: {
        height: 325,
        type: 'radar',
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    stroke: {
        width: 1
    },
    fill: {
        opacity: 0.1
    },
    xaxis: {
        categories: ['1398', '1399', '1400', '1401', '1402', '1403'],
        labels: {
            style: {
                fontFamily: 'Vazir, sans-serif'
            }
        }
    },
    colors: ["--dx-primary", "--dx-danger", "--dx-success"],
};

allCharts.push([{ 'id': 'hospitalBirthDeathChart', 'data': options }]);

updateAllCharts();

//Appointment Request
document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('[data-action]');
    buttons.forEach(button => {
        button.addEventListener('click', function () {
            const userId = button.getAttribute('data-user-id'); // Get the user ID
            const action = button.getAttribute('data-action'); // Get the action (accepted or rejected)

            const buttonContainer = button.closest('.d-flex.align-items-center.gap-2.flex-shrink-0');
            buttonContainer.classList.add('d-none');

            const badge = document.querySelector(`[data-user-id="${userId}"][data-badge="${action}"]`);
            if (badge)
                badge.classList.remove('d-none');
        });
    });
});

class TableManager {
    constructor(config) {
        this.tableId = config.tableId;
        this.searchInputId = config.searchInputId;
        this.paginationId = config.paginationId;
        this.showingResultsId = config.showingResultsId;
        this.checkAllId = config.checkAllId;

        this.itemsPerPage = config.itemsPerPage || 8;
        this.currentPage = 1;

        this.data = config.data;
        this.filteredData = [...this.data];

        this.init();
    }

    init() {
        // Initialize the table
        this.renderTable();

        // Add event listeners
        this.initSearch();
        this.initCheckAll();
        this.initPagination();
    }

    renderTable() {
        const table = document.getElementById(this.tableId);
        const tbody = table.querySelector('tbody');

        // Clear existing rows except the header row
        const headerRow = tbody.querySelector('tr');
        tbody.innerHTML = '';
        tbody.appendChild(headerRow);

        // Calculate start and end index for current page
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const currentPageData = this.filteredData.slice(startIndex, endIndex);

        // If no data, show "no records" row
        if (currentPageData.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `
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
                            <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164
                                S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331
                                c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3"
                                d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0
                                l-4.331-4.331"></path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3"
                                d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3"
                                d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                        </svg>
                        <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                        <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        } else {
            // Render rows for current page
            currentPageData.forEach((patient, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <div class="form-check check-primary">
                            <input class="form-check-input patient-checkbox" title="checkbox" type="checkbox" id="checkboxData${startIndex + index + 1}">
                            <label class="form-check-label d-none" for="checkboxData${startIndex + index + 1}">
                                Data ${startIndex + index + 1}
                            </label>
                        </div>
                    </td>
                    <td>${patient.name}</td>
                    <td>${patient.age}</td>
                    <td>${patient.phone}</td>
                    <td>${patient.email}</td>
                    <td>${patient.condition}</td>
                    <td>${patient.medications}</td>
                    <td>${patient.lastVisit}</td>
                    <td>
                        <div class="d-flex gap-3">
                            <a class="link link-custom-primary" href="apps-hospital-patients-overview.html" aria-label="overview"><i class="ri-eye-line"></i></a>
                            <a class="link link-custom-primary" href="apps-hospital-patients-create.html" aria-label="edit"><i class="ri-edit-2-line"></i></a>
                            <a href="#!" class="link link-custom-danger" aria-label="delete"><i class="ri-delete-bin-6-line"></i></a>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        // Update showing results text
        this.updateResultsCount();

        // Update pagination
        this.updatePagination();
    }

    initSearch() {
        const searchInput = document.getElementById(this.searchInputId);
        searchInput.addEventListener('input', () => {
            const searchTerm = searchInput.value.toLowerCase();

            this.filteredData = this.data.filter(patient => {
                return (
                    patient.name.toLowerCase().includes(searchTerm) ||
                    patient.email.toLowerCase().includes(searchTerm) ||
                    patient.condition.toLowerCase().includes(searchTerm) ||
                    patient.medications.toLowerCase().includes(searchTerm)
                );
            });

            this.currentPage = 1;
            this.renderTable();
        });
    }

    initCheckAll() {
        const checkAllBox = document.getElementById(this.checkAllId);
        checkAllBox.addEventListener('change', () => {
            const checkboxes = document.querySelectorAll('.patient-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = checkAllBox.checked;
            });
        });

        // Update check all box when individual checkboxes change
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('patient-checkbox')) {
                this.updateCheckAllStatus();
            }
        });
    }

    updateCheckAllStatus() {
        const checkAllBox = document.getElementById(this.checkAllId);
        const checkboxes = document.querySelectorAll('.patient-checkbox');
        const checkedBoxes = document.querySelectorAll('.patient-checkbox:checked');

        if (checkboxes.length === 0) {
            checkAllBox.checked = false;
        } else if (checkedBoxes.length === 0) {
            checkAllBox.checked = false;
        } else if (checkedBoxes.length === checkboxes.length) {
            checkAllBox.checked = true;
        } else {
            checkAllBox.checked = false;
        }
    }

    initPagination() {
        const pagination = document.getElementById(this.paginationId);
        pagination.addEventListener('click', (e) => {
            e.preventDefault();

            if (e.target.tagName === 'A' || e.target.closest('a')) {
                const link = e.target.tagName === 'A' ? e.target : e.target.closest('a');
                const pageText = link.textContent.trim();

                if (pageText === 'قبلی') {
                    if (this.currentPage > 1) {
                        this.currentPage--;
                        this.renderTable();
                    }
                } else if (pageText.includes('بعدی')) {
                    const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
                    if (this.currentPage < totalPages) {
                        this.currentPage++;
                        this.renderTable();
                    }
                } else {
                    // Handle numeric page links
                    const pageNumber = parseInt(pageText, 10);
                    if (!isNaN(pageNumber)) {
                        this.currentPage = pageNumber;
                        this.renderTable();
                    }
                }
            }
        });
    }

    updatePagination() {
        const pagination = document.getElementById(this.paginationId);
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);

        let paginationHTML = '';

        // Previous button
        paginationHTML += `
        <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
          <a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>
        </li>
      `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            paginationHTML += `
          <li class="page-item ${this.currentPage === i ? 'active' : ''}">
            <a class="page-link" href="#!">${i}</a>
          </li>
        `;
        }

        // Next button
        paginationHTML += `
        <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
          <a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>
        </li>
      `;

        pagination.innerHTML = paginationHTML;
        createIcons({ icons });
    }

    updateResultsCount() {
        const resultsElement = document.getElementById(this.showingResultsId);
        const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endIndex = Math.min(startIndex + this.itemsPerPage - 1, this.filteredData.length);

        resultsElement.innerHTML = `نمایش <b class="me-1">${startIndex}-${endIndex}</b>از<b class="ms-1">${this.filteredData.length}</b> نتیجه`;
    }
}

// Patient data in JSON format
const patientData = [
    {
        name: "دوروتی دیلی",
        age: 45,
        phone: "+1 0123 4567",
        email: "dorothy.daley@example.com",
        condition: "فشار خون بالا",
        medications: "Lisinopril, Amlodipine",
        lastVisit: "23 خرداد 1403"
    },
    {
        name: "اوا گرین",
        age: 41,
        phone: "+1 0678 9012",
        email: "eve.green@example.com",
        condition: "اضطراب",
        medications: "Alprazolam",
        lastVisit: "20 تیر 1403"
    },
    {
        name: "فرانک براون",
        age: 36,
        phone: "+1 0789 0123",
        email: "frank.brown@example.com",
        condition: "درد کمر",
        medications: "Acetaminophen",
        lastVisit: "30 مرداد 1403"
    },
    {
        name: "گریس میلر",
        age: 50,
        phone: "+1 0890 1234",
        email: "grace.miller@example.com",
        condition: "اختلال تیروئید",
        medications: "Levothyroxine",
        lastVisit: "11 شهریور 1403"
    },
    {
        name: "هنری ویلسون",
        age: 28,
        phone: "+1 0901 2345",
        email: "henry.wilson@example.com",
        condition: "میگرن",
        medications: "Sumatriptan",
        lastVisit: "24 مهر 1403"
    },
    {
        name: "ایرنه مارتینز",
        age: 60,
        phone: "+1 1012 3456",
        email: "irene.martinez@example.com",
        condition: "پوکی استخوان",
        medications: "Alendronate",
        lastVisit: "30 آبان 1403"
    },
    {
        name: "جک دیویس",
        age: 34,
        phone: "+1 1123 4567",
        email: "jack.davis@example.com",
        condition: "رفلاکس معده",
        medications: "Omeprazole",
        lastVisit: "15 آذر 1403"
    },
    {
        name: "کارن تیلور",
        age: 42,
        phone: "+1 1234 5678",
        email: "karen.taylor@example.com",
        condition: "سندرم خستگی مزمن",
        medications: "Modafinil",
        lastVisit: "30 آذر 1403"
    },
    {
        name: "لئوناردو هریس",
        age: 55,
        phone: "+1 2345 6789",
        email: "leonard.harris@example.com",
        condition: "دیابت",
        medications: "Metformin",
        lastVisit: "21 دی 1403"
    },
    {
        name: "ماریا اسکات",
        age: 39,
        phone: "+1 3456 7890",
        email: "maria.scott@example.com",
        condition: "آسم",
        medications: "Albuterol",
        lastVisit: "27 بهمن 1403"
    },
    {
        name: "نورمان کلارک",
        age: 47,
        phone: "+1 4567 8901",
        email: "norman.clark@example.com",
        condition: "آرتروز",
        medications: "Ibuprofen",
        lastVisit: "30 اسفند 1403"
    },
    {
        name: "اولیویا بیکر",
        age: 33,
        phone: "+1 5678 9012",
        email: "olivia.baker@example.com",
        condition: "افسردگی",
        medications: "Sertraline",
        lastVisit: "5 اردیبهشت 1404"
    }
];

// Initialize table manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const tableManager = new TableManager({
        tableId: 'patientsTable',
        searchInputId: 'allPatientSearch',
        paginationId: 'pagination',
        showingResultsId: 'showingResults',
        checkAllId: 'checkboxDataAll',
        data: patientData,
        itemsPerPage: 8
    });
});