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

//email Campaign Performance chart
var options = {
    series: [
        {
            name: "ارسال شده",
            data: [28, 29, 33, 36, 32, 32, 33]
        },
        {
            name: "باز شده",
            data: [12, 11, 14, 18, 17, 13, 13]
        }
    ],
    chart: {
        defaultLocale: "en",
        height: 280,
        type: "area",
        toolbar: {
            show: false
        }
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    stroke: {
        curve: 'smooth'
    },
    grid: {
        xaxis: {
            lines: {
                show: true
            }
        },
        padding: {
            right: 0,
            top: -20
        }
    },
    fill: {
        type: 'gradient',
        gradient: {
            shadeIntensity: 1,
            inverseColors: false,
            opacityFrom: 0.4,
            opacityTo: 0,
            stops: [0, 90, 100]
        },
    },
    xaxis: {
        categories: ["مهر", "شهریور", "مرداد", "تیر", "خرداد", "اردیبهشت", "فروردین"]
    },
    colors: ["--dx-primary", "--dx-dark"],
};

allCharts.push([{ 'id': 'emailCampaignPerformanceChart', 'data': options }]);

//Click Rate chart
var options = {
    series: [33, 57],
    labels: ["نرخ باز شدن", "نرخ کلیک"],
    chart: {
        height: 176,
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
        position: 'bottom'
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: '100%',
                height: 200
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-primary", "--dx-danger"],
};

allCharts.push([{ 'id': 'clickRateChart', 'data': options }]);


//Total Revenue Bar chart
var options = {
    series: [{
        name: 'کل درآمد',
        data: [5, 4, 7, 9, 2, 6, 10, 6, 3, 7, 9, 5]
    }],
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    chart: {
        height: 100,
        type: "bar",
        toolbar: {
            show: false,
        },
        sparkline: { enabled: !0 },
    },
    colors: ["--dx-white"]
};

allCharts.push([{ 'id': 'totalRevenueBarChart', 'data': options }]);

//Mail Statistic Charts
var options = {
    series: [
        {
            name: 'ارسال شده',
            data: [
                {
                    x: 'اردیبهشت',
                    y: 43,
                },
                {
                    x: 'فروردین',
                    y: 58,
                },
            ],
        },
        {
            name: 'در حال انجام',
            data: [
                {
                    x: 'اردیبهشت',
                    y: 33,
                },
                {
                    x: 'فروردین',
                    y: 38,
                },
            ],
        },
        {
            name: 'لغو شده',
            data: [
                {
                    x: 'اردیبهشت',
                    y: 55,
                },
                {
                    x: 'فروردین',
                    y: 21,
                },
            ],
        },
    ],
    chart: {
        height: 315,
        type: "line",
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    stroke: {
        curve: 'smooth'
    },
    plotOptions: {
        line: {
            isSlopeChart: true,
        },
    },
    legend: {
        show: true,
        position: 'bottom',
        horizontalAlign: 'center',
    },
    xaxis: {
        type: 'category',
        axisBorder: {
            show: false,
        }
    },
    grid: {
        padding: {
            bottom: 0,
            right: 0
        }
    },
    colors: ["--dx-primary", "--dx-success", "--dx-danger"]
};

allCharts.push([{ 'id': 'mailStatisticChart', 'data': options }]);

//Time Spending Charts
var options = {
    series: [
        {
            name: "کل هزینه‌ها",
            data: [10, 41, 35, 51, 49, 62, 69, 91, 148]
        },
        {
            name: "فروش",
            data: [62, 69, 91, 54, 10, 41, 35, 51, 49]
        }
    ],
    chart: {
        defaultLocale: "en",
        height: 120,
        type: "line",
        zoom: {
            enabled: true
        },
        sparkline: { enabled: !0 },
    },
    stroke: {
        curve: 'straight'
    },
    xaxis: {
        title: {
            text: "Xaxis"
        },
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
        y: {
            formatter: (val) => {
                return this.formatCurrency(val);
            }
        }
    },
    legend: {
        show: true,
        position: 'bottom',
        horizontalAlign: 'center',
        offsetY: 8,
    },
    stroke: {
        width: 1,
    },
    grid: {
        padding: {
            top: 0,
            right: 5,
            bottom: 20,
        },
    },
    colors: ["--dx-primary", "--dx-success"]
};

allCharts.push([{ 'id': 'timeSpendingChart', 'data': options }]);

updateAllCharts();

// Email data in JSON format
const emailData = [
    {
        id: 1,
        email: "خدمات مالی",
        publishDate: "14 اردیبهشت 1403",
        sent: 4,
        clickRate: "3.47%",
        deliveredRate: "7.89%",
        spanReportRate: "0.14%"
    },
    {
        id: 2,
        email: "آپدیت مراقبت‌های بهداشتی",
        publishDate: "21 اردیبهشت 1403",
        sent: 5,
        clickRate: "4.12%",
        deliveredRate: "8.45%",
        spanReportRate: "0.20%"
    },
    {
        id: 3,
        email: "خبرنامه خرده فروشی",
        publishDate: "26 اردیبهشت 1403",
        sent: 6,
        clickRate: "2.98%",
        deliveredRate: "7.65%",
        spanReportRate: "0.10%"
    },
    {
        id: 4,
        email: "بینش‌های فنی",
        publishDate: "31 اردیبهشت 1403",
        sent: 7,
        clickRate: "5.21%",
        deliveredRate: "9.12%",
        spanReportRate: "0.30%"
    },
    {
        id: 5,
        email: "معاملات مسافرتی",
        publishDate: "5 خرداد 1403",
        sent: 3,
        clickRate: "6.34%",
        deliveredRate: "8.79%",
        spanReportRate: "0.25%"
    },
    {
        id: 6,
        email: "هفتگی آموزش",
        publishDate: "10 خرداد 1403",
        sent: 8,
        clickRate: "3.89%",
        deliveredRate: "8.23%",
        spanReportRate: "0.18%"
    },
    {
        id: 7,
        email: "ترندهای خودروسازی",
        publishDate: "15 خرداد 1403",
        sent: 4,
        clickRate: "4.50%",
        deliveredRate: "7.95%",
        spanReportRate: "0.12%"
    },
    {
        id: 8,
        email: "بولتن مد",
        publishDate: "20 خرداد 1403",
        sent: 5,
        clickRate: "5.78%",
        deliveredRate: "9.34%",
        spanReportRate: "0.15%"
    },
    {
        id: 9,
        email: "اخبار غذا و نوشیدنی",
        publishDate: "25 خرداد 1403",
        sent: 6,
        clickRate: "4.65%",
        deliveredRate: "8.56%",
        spanReportRate: "0.22%"
    },
    {
        id: 10,
        email: "بازار املاک",
        publishDate: "30 خرداد 1403",
        sent: 7,
        clickRate: "3.78%",
        deliveredRate: "7.92%",
        spanReportRate: "0.19%"
    },
    {
        id: 11,
        email: "هفتگی سرگرمی",
        publishDate: "4 تیر 1403",
        sent: 9,
        clickRate: "6.12%",
        deliveredRate: "9.45%",
        spanReportRate: "0.28%"
    },
    {
        id: 12,
        email: "به روزرسانی‌های ورزشی",
        publishDate: "9 تیر 1403",
        sent: 5,
        clickRate: "5.34%",
        deliveredRate: "8.67%",
        spanReportRate: "0.17%"
    },
    {
        id: 13,
        email: "کشفیات علمی",
        publishDate: "14 تیر 1403",
        sent: 4,
        clickRate: "4.89%",
        deliveredRate: "8.12%",
        spanReportRate: "0.21%"
    },
    {
        id: 14,
        email: "فرهنگ و هنر",
        publishDate: "19 تیر 1403",
        sent: 6,
        clickRate: "3.56%",
        deliveredRate: "7.78%",
        spanReportRate: "0.15%"
    },
    {
        id: 15,
        email: "اخبار محیط زیست",
        publishDate: "24 تیر 1403",
        sent: 5,
        clickRate: "4.23%",
        deliveredRate: "8.34%",
        spanReportRate: "0.23%"
    }
];

/**
 * TableManager class for managing table data, pagination, search, and export functionality
 */
class TableManager {
    /**
     * Constructor for TableManager
     * @param {string} tableId - The ID of the table element
     * @param {Array} data - The data to populate the table with
     */
    constructor(tableId, data) {
        // Main elements
        this.tableId = tableId;
        this.tableElement = document.getElementById(tableId);
        this.tableBody = this.tableElement.querySelector('tbody');
        this.searchInput = document.getElementById('searchInput');
        this.exportBtn = document.getElementById('exportBtn');
        this.checkboxAll = document.getElementById('checkboxDataAll');
        this.resultInfo = document.getElementById('resultInfo');
        this.paginationElement = document.getElementById('pagination');

        // Data and state
        this.data = data;
        this.filteredData = [...data];
        this.currentPage = 1;
        this.itemsPerPage = 8;
        this.totalPages = Math.ceil(this.data.length / this.itemsPerPage);
    }

    /**
     * Initialize the TableManager
     */
    init() {
        // Initial render
        this.renderTable();
        this.renderPagination();
        this.updateResultInfo();

        // Add event listeners
        this.searchInput.addEventListener('input', this.handleSearch.bind(this));
        this.exportBtn.addEventListener('click', this.handleExport.bind(this));
        this.checkboxAll.addEventListener('change', this.handleSelectAll.bind(this));
    }

    /**
     * Render the table with current data and page
     */
    renderTable() {
        // Clear existing table rows except header
        const headerRow = this.tableBody.querySelector('tr');
        this.tableBody.innerHTML = '';
        this.tableBody.appendChild(headerRow);

        // Calculate start and end indices for current page
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredData.length);

        // If no data to render
        if (startIndex >= endIndex) {
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
                    </div>
                </td>
            `;
            this.tableBody.appendChild(noDataRow);
            return;
        }

        // Create and append table rows for current page
        for (let i = startIndex; i < endIndex; i++) {
            const item = this.filteredData[i];
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>
                    <div class="form-check check-primary">
                        <input class="form-check-input item-checkbox" title="checkbox" type="checkbox" id="checkboxData${item.id}">
                        <label class="form-check-label d-none" for="checkboxData${item.id}">
                            Data ${item.id}
                        </label>
                    </div>
                </td>
                <td>${item.email}</td>
                <td>${item.publishDate}</td>
                <td>${item.sent}</td>
                <td>${item.clickRate}</td>
                <td>${item.deliveredRate}</td>
                <td>${item.spanReportRate}</td>
            `;

            this.tableBody.appendChild(row);
        }

        // Add event listeners to individual checkboxes
        const checkboxes = this.tableBody.querySelectorAll('.item-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', this.handleCheckboxChange.bind(this));
        });
    }


    /**
     * Render pagination controls
     */
    renderPagination() {
        this.totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        this.paginationElement.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.goToPage(this.currentPage - 1);
            }
        });
        this.paginationElement.appendChild(prevLi);

        // Page numbers
        const maxVisiblePages = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(this.totalPages, startPage + maxVisiblePages - 1);

        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageLi.addEventListener('click', (e) => {
                e.preventDefault();
                this.goToPage(i);
            });
            this.paginationElement.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < this.totalPages) {
                this.goToPage(this.currentPage + 1);
            }
        });
        this.paginationElement.appendChild(nextLi);

        createIcons({ icons });
    }

    /**
     * Update the result info text
     */
    updateResultInfo() {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endIndex = Math.min(startIndex + this.itemsPerPage - 1, this.filteredData.length);

        this.resultInfo.innerHTML = `نمایش <b class="me-1">${startIndex} - ${endIndex}</b> از <b class="ms-1">${this.filteredData.length}</b> نتیجه`;
    }

    /**
     * Go to a specific page
     * @param {number} page - The page number to go to
     */
    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;

        this.currentPage = page;
        this.renderTable();
        this.renderPagination();
        this.updateResultInfo();

        // Reset select all checkbox
        this.checkboxAll.checked = false;
    }

    /**
     * Handle search input
     */
    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();

        if (searchTerm === '') {
            this.filteredData = [...this.data];
        } else {
            this.filteredData = this.data.filter(item => {
                return (
                    item.email.toLowerCase().includes(searchTerm) ||
                    item.publishDate.toLowerCase().includes(searchTerm) ||
                    item.sent.toString().includes(searchTerm) ||
                    item.clickRate.toLowerCase().includes(searchTerm) ||
                    item.deliveredRate.toLowerCase().includes(searchTerm) ||
                    item.spanReportRate.toLowerCase().includes(searchTerm)
                );
            });
        }

        this.currentPage = 1;
        this.renderTable();
        this.renderPagination();
        this.updateResultInfo();
    }

    /**
     * Handle export button click
     */
    handleExport() {
        // Get selected items or all filtered items if none selected
        const selectedCheckboxes = this.tableBody.querySelectorAll('.item-checkbox:checked');
        let dataToExport = [];

        if (selectedCheckboxes.length > 0) {
            // Export selected items
            selectedCheckboxes.forEach(checkbox => {
                const id = parseInt(checkbox.id.replace('checkboxData', ''));
                const item = this.data.find(item => item.id === id);
                if (item) dataToExport.push(item);
            });
        } else {
            // Export all filtered items
            dataToExport = [...this.filteredData];
        }

        // Convert to CSV
        const headers = ['Email', 'Publish Date', 'Sent', 'Click Rate (%)', 'Delivered Rate', 'Span Report Rate'];
        const csvRows = [headers.join(',')];

        dataToExport.forEach(item => {
            const values = [
                `"${item.email}"`,
                `"${item.publishDate}"`,
                item.sent,
                item.clickRate,
                item.deliveredRate,
                item.spanReportRate
            ];
            csvRows.push(values.join(','));
        });

        const csvContent = csvRows.join('\n');

        // Create and download the CSV file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'email_performance.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * Handle select all checkbox change
     */
    handleSelectAll(e) {
        const isChecked = e.target.checked;
        const checkboxes = this.tableBody.querySelectorAll('.item-checkbox');

        checkboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
    }

    /**
     * Handle individual checkbox change
     */
    handleCheckboxChange() {
        const checkboxes = this.tableBody.querySelectorAll('.item-checkbox');
        const checkedCount = this.tableBody.querySelectorAll('.item-checkbox:checked').length;

        // Update select all checkbox state
        this.checkboxAll.checked = checkedCount === checkboxes.length;
    }
}
document.addEventListener('DOMContentLoaded', function () {

    // Initialize the table manager
    const tableManager = new TableManager('emailTable', emailData);
    tableManager.init();
});