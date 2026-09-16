import ApexCharts from '../../libs/apexcharts/apexcharts.esm.js'
import { icons, createIcons } from "lucide";

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

//Sales Analytics Chart
var options = {
    series: [{
        name: 'بازدیدکننده',
        data: [154, 137, 41, 67, 43, 20, 41, 67, 20, 41, 32, 98]
    }, {
        name: 'افزودن به سبد خرید',
        data: [13, 23, 20, 35, 27, 16, 8, 13, 20, 41, 44, 67]
    }, {
        name: 'پرداخت',
        data: [11, 54, 15, 21, 14, 24, 15, 21, 20, 41, 54, 35]
    }, {
        name: 'علاقه‌مندی ها',
        data: [21, 19, 25, 22, 8, 19, 13, 22, 20, 41, 49, 33]
    }],
    chart: {
        height: 300,
        type: "bar",
        stacked: true,
        toolbar: {
            show: false
        },
        zoom: {
            enabled: true
        }
    },
    dataLabels: {
        enabled: false,
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: '35%',
        },
    },

    xaxis: {
        categories: ['اسفند', 'بهمن', 'دی', 'آذر', 'آبان', 'مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
        axisBorder: {
            show: false,
        }
    },
    legend: {
        position: 'top',
        horizontalAlign: 'right',
        offsetY: -5,
    },
    grid: {
        show: true,
        borderColor: '#90A4AE',
        strokeDashArray: 2,
        position: 'back',
        padding: {
            top: 10,
            right: 0,
        },
        xaxis: {
            lines: {
                show: true
            }
        },
        yaxis: {
            lines: {
                show: true
            }
        },
    },
    fill: {
        opacity: 1
    },
    colors: ["--dx-primary", "--dx-danger-bg-subtle", "--dx-info", "--dx-dark"]
};

allCharts.push([{ 'id': 'salesAnalyticsChart', 'data': options }]);

//Deal Revenue Forecast Chart
var options = {
    series: [87.6],
    chart: {
        height: 250,
        type: "radialBar",
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '60%',
            },
            track: {
                dropShadow: {
                    enabled: true,
                    top: 0,
                    left: 0,
                    blur: 10,
                    opacity: 0.02
                }
            },
            dataLabels: {
                name: {
                    fontSize: '15px',
                },
                value: {
                    show: true,
                    fontSize: '14px',
                    fontWeight: 700,
                    offsetY: 10,
                    formatter: function (val) {
                        return '$' + val + 'k'
                    }
                },
            }
        },
    },
    labels: ['این ماه'],
    colors: ["--dx-dark"]
};

allCharts.push([{ 'id': 'dealRevenueForecastChart', 'data': options }]);

updateAllCharts();

/**
 * TableManager Class - A vanilla JavaScript class for managing table data with pagination, search and export.
 */
class TableManager {
    /**
     * @param {string} tableId - The ID of the table element
     * @param {Array} data - The data to display in the table
     */
    constructor(tableId, data) {
        // Main elements
        this.tableId = tableId;
        this.table = document.getElementById(tableId);
        this.tableBody = document.getElementById('tableBody');
        this.searchInput = document.getElementById('searchInput');
        this.exportBtn = document.getElementById('exportBtn');
        this.paginationEl = document.getElementById('pagination');

        // Display elements
        this.showingStart = document.getElementById('showing-start');
        this.showingEnd = document.getElementById('showing-end');
        this.totalResults = document.getElementById('total-results');
        this.tableTitle = document.getElementById('table-title');

        // Data and pagination settings
        this.allData = data;
        this.filteredData = [...data];
        this.currentPage = 1;
        this.itemsPerPage = 8;
        this.totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
    }

    /**
     * Initialize the Table Manager
     */
    init() {
        this.renderTable();
        this.updatePagination();
        this.updateResultsInfo();
        this.setupEventListeners();
    }

    /**
     * Set up event listeners for search, pagination, and export
     */
    setupEventListeners() {
        // Search functionality
        this.searchInput.addEventListener('input', this.handleSearch.bind(this));
    }

    /**
     * Handle search input
     */
    handleSearch() {
        const searchTerm = this.searchInput.value.toLowerCase().trim();

        if (searchTerm === '') {
            this.filteredData = [...this.allData];
        } else {
            this.filteredData = this.allData.filter(item => {
                return Object.values(item).some(value => {
                    if (value === null || value === undefined) return false;
                    return String(value).toLowerCase().includes(searchTerm);
                });
            });
        }

        this.currentPage = 1;
        this.totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);

        this.renderTable();
        this.updatePagination();
        this.updateResultsInfo();
        this.updateTableTitle();
    }

    /**
     * Update the table title with the count of filtered results
     */
    updateTableTitle() {
        this.tableTitle.textContent = `مدیران (${this.filteredData.length})`;
    }

    /**
     * Render table data for the current page
     */
    renderTable() {
        this.tableBody.innerHTML = '';

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredData.length);
        const currentPageData = this.filteredData.slice(startIndex, endIndex);

        if (currentPageData.length === 0) {
            const noDataRow = document.createElement('tr');
            noDataRow.innerHTML = `
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
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0	l-4.331-4.331"></path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                        </svg>
                        <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                        <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                    </div></td>
            `;
            this.tableBody.appendChild(noDataRow);
            return;
        }

        currentPageData.forEach(item => {
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${item.name}</td>
                <td><i class="ri-star-fill text-warning align-baseline"></i> (${item.rating})</td>
                <td>${item.date}</td>
                <td>${item.contact}</td>
                <td><span class="badge bg-body-tertiary text-muted border">${item.source}</span></td>
                <td><span class="badge bg-${item.statusClass}-subtle text-${item.statusClass} border border-${item.statusClass}-subtle">${item.status}</span></td>
                <td>${item.balance}</td>
            `;

            this.tableBody.appendChild(row);
        });
    }

    /**
     * Update pagination controls
     */
    updatePagination() {
        this.paginationEl.innerHTML = '';

        if (this.totalPages <= 1) {
            return;
        }

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#"><i class="ri-arrow-right-s-line"></i> قبلی</a>`;
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.goToPage(this.currentPage - 1);
            }
        });
        this.paginationEl.appendChild(prevLi);

        // Page numbers
        let startPage = Math.max(1, this.currentPage - 2);
        let endPage = Math.min(this.totalPages, startPage + 4);

        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageLi.addEventListener('click', (e) => {
                e.preventDefault();
                this.goToPage(i);
            });
            this.paginationEl.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#">بعدی <i class="ri-arrow-left-s-line"></i></a>`;
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < this.totalPages) {
                this.goToPage(this.currentPage + 1);
            }
        });
        this.paginationEl.appendChild(nextLi);
    }

    /**
     * Go to a specific page
     * @param {number} pageNumber - The page number to navigate to
     */
    goToPage(pageNumber) {
        this.currentPage = pageNumber;
        this.renderTable();
        this.updatePagination();
        this.updateResultsInfo();
    }

    /**
     * Update the "Showing X-Y of Z results" text
     */
    updateResultsInfo() {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endIndex = Math.min(startIndex + this.itemsPerPage - 1, this.filteredData.length);

        if (this.filteredData.length === 0) {
            this.showingStart.textContent = '0';
            this.showingEnd.textContent = '0';
        } else {
            this.showingStart.textContent = startIndex.toString();
            this.showingEnd.textContent = endIndex.toString();
        }

        this.totalResults.textContent = this.filteredData.length.toString();
    }
}

// Initialize the Table Manager once the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const tableManager = new TableManager('leadsTable', leadsData);
    tableManager.init();

    createIcons({ icons });
});

// Sample data for the table
const leadsData = [
    {
        name: "دنیل گریک",
        rating: 3.7,
        date: "18 تیر 1403",
        contact: "daniel@example.com",
        source: "منبع آنلاین",
        status: "مذاکره",
        statusClass: "secondary",
        balance: "9,000 تومان"
    },
    {
        name: "جین ایر",
        rating: 3.9,
        date: "1 فروردین 1403",
        contact: "jane@example.com",
        source: "منبع آنلاین",
        status: "علاقه‌مند",
        statusClass: "warning",
        balance: "8,000 تومان"
    },
    {
        name: "توماس ادیسون",
        rating: 3.8,
        date: "5 تیر 1403",
        contact: "thomas@example.com",
        source: "زیر مجموعه",
        status: "تماس گرفته‌شده",
        statusClass: "success",
        balance: "7,500 تومان"
    },
    {
        name: "دیوید هسلهوف",
        rating: 3.5,
        date: "10 خرداد 1403",
        contact: "wilson@example.com",
        source: "کمپین ایمیل",
        status: "بسته",
        statusClass: "danger",
        balance: "5,000 تومان"
    },
    {
        name: "امیلیا کلارک",
        rating: 4.2,
        date: "21 اردیبهشت 1403",
        contact: "emily@example.com",
        source: "وبسایت",
        status: "بسته",
        statusClass: "danger",
        balance: "25,000 تومان"
    },
    {
        name: "مایکل جانسون",
        rating: 4.5,
        date: "30 فروردین 1403",
        contact: "michael@example.com",
        source: "نمایشگاه تجاری",
        status: "مذاکره",
        statusClass: "secondary",
        balance: "20,000 تومان"
    },
    {
        name: "سارا میلر",
        rating: 4.6,
        date: "11 تیر 1403",
        contact: "sarah@example.com",
        source: "نمایشگاه تجاری",
        status: "علاقه‌مند",
        statusClass: "warning",
        balance: "18,000 تومان"
    },
    {
        name: "دوروتی آزبورتک",
        rating: 4.3,
        date: "22 دی 1402",
        contact: "dorothy@example.com",
        source: "منبع آنلاین",
        status: "تازه",
        statusClass: "info",
        balance: "15,000 تومان"
    },
    {
        name: "رابرت ردفورد",
        rating: 4.1,
        date: "16 بهمن 1402",
        contact: "robert@example.com",
        source: "تماس تلفنی",
        status: "تازه",
        statusClass: "info",
        balance: "12,500 تومان"
    },
    {
        name: "جنیفر انستین",
        rating: 4.0,
        date: "1 اسفند 1402",
        contact: "jennifer@example.com",
        source: "وبسایت",
        status: "تماس گرفته‌شده",
        statusClass: "success",
        balance: "22,000 تومان"
    },
    {
        name: "ویلیام ویندزور",
        rating: 3.9,
        date: "3 اردیبهشت 1403",
        contact: "william@example.com",
        source: "کمپین ایمیل",
        status: "علاقه‌مند",
        statusClass: "warning",
        balance: "17,500 تومان"
    },
    {
        name: "الیزابت تیلور",
        rating: 4.4,
        date: "14 خرداد 1403",
        contact: "elizabeth@example.com",
        source: "زیر مجموعه",
        status: "مذاکره",
        statusClass: "secondary",
        balance: "30,000 تومان"
    }
];
