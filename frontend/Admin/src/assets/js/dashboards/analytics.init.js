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

//Sales revenue Charts
var options = {
    series: [{
        name: 'درآمد کل',
        data: [31, 40, 28, 51, 42, 119, 100]
    }],
    labels: ['مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
    tooltip: {
    style: {
            fontFamily: 'Vazir'
        }
    },
    chart: {
        defaultLocale: "en",
        height: 140,
        type: "line",
        zoom: {
            enabled: false
        },
        toolbar: {
            show: false,
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 3,
        curve: 'smooth',
        dashArray: [10]
    },
    legend: {
        tooltipHoverFormatter: function (val, opts) {
            return val + ' - <strong>' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + '</strong>'
        }
    },
    markers: {
        size: 0,
        hover: {
            sizeOffset: 5
        }
    },
    colors: ["--dx-primary"],
    grid: {
        borderColor: ["--dx-border-color"],
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
            left: 7
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
    xaxis: {
    labels: {
            style: {
                fontFamily: 'Vazir',
                fontSize: '11px'
            }
        }
    },
    yaxis: {
        show: false,
    },
};

allCharts.push([{ 'id': 'salesRevenueChart', 'data': options }]);

//ads revenue Charts
var options = {
    series: [{
        name: 'درآمد کل',
        data: [31, 77, 44, 31, 63, 94, 109]
    }],
    labels: ['مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    chart: {
        defaultLocale: "en",
        height: 140,
        type: "line",
        zoom: {
            enabled: false
        },
        toolbar: {
            show: false,
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 3,
        curve: 'smooth',
        dashArray: [10]
    },
    legend: {
        tooltipHoverFormatter: function (val, opts) {
            return val + ' - <strong>' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + '</strong>'
        }
    },
    markers: {
        size: 0,
        hover: {
            sizeOffset: 5
        }
    },
    grid: {
        borderColor: ["--dx-border-color"],
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
            left: 7
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
    xaxis: {
        labels: {
            style: {
                fontFamily: 'Vazir',
                fontSize: '11px'
            }
        }
    },
    yaxis: {
        show: false,
    },
    colors: ["--dx-danger"],

};

allCharts.push([{ 'id': 'adsRevenueChart', 'data': options }]);

//Web Analytics Charts
var options = {
    series: [
        {
            name: 'ریفرال',
            data: [
                {
                    x: 'آبان',
                    y: 43,
                },
                {
                    x: 'مهر',
                    y: 58,
                },
                {
                    x: 'شهریور',
                    y: 66,
                },
                {
                    x: 'مرداد',
                    y: 44,
                },
            ],
        },
        {
            name: 'دایرکت',
            data: [
                {
                    x: 'آبان',
                    y: 33,
                },
                {
                    x: 'مهر',
                    y: 43,
                },
                {
                    x: 'شهریور',
                    y: 34,
                },
                {
                    x: 'مرداد',
                    y: 53,
                },
            ],
        },
        {
            name: 'تبلیغات',
            data: [
                {
                    x: 'آبان',
                    y: 55,
                },
                {
                    x: 'مهر',
                    y: 33,
                },
                {
                    x: 'شهریور',
                    y: 54,
                },
                {
                    x: 'مرداد',
                    y: 65,
                },
            ],
        },
    ],
    
    chart: {
        height: 300,
        type: "line",
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    stroke: {
        curve: 'smooth',
        width: 3,
    },
    plotOptions: {
        line: {
            isSlopeChart: true,
        },
    },
    dataLabels: {
        background: {
            enabled: true,
        },
        formatter(val, opts) {
            const seriesName = opts.w.config.series[opts.seriesIndex].name
            return val !== null ? seriesName : ''
        },
    },
    legend: {
        show: false,
        position: 'bottom',
        horizontalAlign: 'center',
    },
    grid: {
        padding: {
            bottom: -15,
            right: 0
        }
    },
    xaxis: {
        axisBorder: {
            show: false,
        },
        labels: {
            style: {
            fontFamily: 'Vazir',
            fontSize: '11px'
            }
        }
    },
    colors: ["--dx-primary", "--dx-success", "--dx-secondary"],
};

allCharts.push([{ 'id': 'webAnalyticsChart', 'data': options }]);

//Average Online Sales Chart
var options = {
    series: [{
        name: 'کل فروش',
        data: [44, 55, 41, 67, 22, 43, 21, 33]
    }],
    chart: {
        height: 160,
        type: 'bar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        bar: {
            borderRadius: 10,
            columnWidth: '50%',
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
    stroke: {
        width: 1
    },
    xaxis: {
        labels: {
            rotate: -45
        },
        categories: ['آبان', 'مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
        tickPlacement: 'on'
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'light',
            type: "horizontal",
            shadeIntensity: 0.25,
            gradientToColors: undefined,
            inverseColors: true,
            opacityFrom: 0.85,
            opacityTo: 0.85,
            stops: [50, 0, 100]
        },
    },
    colors: ["--dx-info"],
};

allCharts.push([{ 'id': 'averageOnlineSalesChart', 'data': options }]);

//Average Weekly Sales Chart
var options = {
    series: [{
        name: 'کل فروش',
        data: [22, 43, 21, 44, 55, 33, 41]
    }],
    chart: {
        height: 160,
        type: 'bar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        bar: {
            borderRadius: 10,
            columnWidth: '50%',
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
    stroke: {
        width: 1
    },
    xaxis: {
        labels: {
            rotate: -45
        },
        categories: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        tickPlacement: 'on'
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'light',
            type: "horizontal",
            shadeIntensity: 0.25,
            gradientToColors: undefined,
            inverseColors: true,
            opacityFrom: 0.85,
            opacityTo: 0.85,
            stops: [50, 0, 100]
        },
    },
    colors: ["--dx-info"],
};

allCharts.push([{ 'id': 'averageOnlineWeeklyChart', 'data': options }]);


//followers Chart
var options = {
    series: [{
        name: 'دنبال‌کنندگان',
        data: [44, 55, 41, 67, 22, 43]
    }, {
        name: 'لغو دنبال کردن',
        data: [13, 23, 20, 8, 13, 27]
    }],
    chart: {
        height: 348,
        type: "bar",
        stacked: true,
        toolbar: {
            show: false
        },
        zoom: {
            enabled: true
        }
    },
    plotOptions: {
        bar: {
            columnWidth: '40%',
            horizontal: false,
            borderRadius: 13,
        },
    },
    labels: ['شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
    legend: {
        position: 'bottom',
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    grid: {
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
        padding: {
            top: -20,
            right: 0,
            bottom: -10,
        },
    },
    colors: ["--dx-primary", "--dx-primary-bg-subtle"],
};

allCharts.push([{ 'id': 'followersChart', 'data': options }]);

//Visit Browsers Chart
var options = {
    series: [44, 55, 41],
    chart: {
        height: 150,
        type: "donut",
    },
    dataLabels: {
        enabled: false
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    plotOptions: {
        pie: {
            startAngle: -90,
            endAngle: 90,
            offsetY: 10
        }
    },
    labels: ['کروم', 'سافاری', 'مایکروسافت'],
    fill: {
        type: 'gradient',
    },
    grid: {
        padding: {
            bottom: -80
        }
    },
    legend: {
        position: 'bottom'
    },
    colors: ["--dx-primary", "--dx-orange", "--dx-warning"],
};

allCharts.push([{ 'id': 'visitBrowsersChart', 'data': options }]);

//Traffic Source Chart
var options = {
    series: [{
        name: 'ترافیک مستقیم',
        data: [44, 55, 57, 56, 61, 58, 63, 60, 66]
    }, {
        name: 'ترافیک موتور جستجو',
        data: [76, 85, 101, 98, 87, 105, 91, 114, 94]
    }],
    chart: {
        height: 145,
        type: "bar",
        sparkline: { enabled: !0 },
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
    legend: {
        show: true,
        position: 'top',
        horizontalAlign: 'start',
        offsetY: -3,
    },
    stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
    },
    xaxis: {
        categories: ['آذر', 'آبان', 'مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
    },
    grid: {
        padding: {
            top: 4,
            right: 0,
            left: 0,
        }
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        },
        y: {
            formatter: function (val) {
                return "$" + val + "k"
            }
        }
    },
    colors: ["--dx-primary", "--dx-border-color"],
};

allCharts.push([{ 'id': 'trafficSourceChart', 'data': options }]);

updateAllCharts();

const campaignData = [
    {
        campaign: "حراج تابستانی",
        clicks: "4.5%",
        deliveredRate: "98%",
        impressions: 15000,
        cpc: "0.25 تومان",
        cr: "2.3%",
        revenue: "850 تومان"
    },
    {
        campaign: "تبلیغات زمستانی",
        clicks: "3.8%",
        deliveredRate: "95%",
        impressions: 12000,
        cpc: "0.30 تومان",
        cr: "1.8%",
        revenue: "650 تومان"
    },
    {
        campaign: "تخفیف بهاری",
        clicks: "5.2%",
        deliveredRate: "99%",
        impressions: 18000,
        cpc: "0.20 تومان",
        cr: "2.5%",
        revenue: "900 تومان"
    },
    {
        campaign: "پیشنهاد پاییزی",
        clicks: "4.0%",
        deliveredRate: "97%",
        impressions: 14000,
        cpc: "0.28 تومان",
        cr: "2.0%",
        revenue: "750 تومان"
    },
    {
        campaign: "ویژه تعطیلات",
        clicks: "5.0%",
        deliveredRate: "96%",
        impressions: 16000,
        cpc: "0.22 تومان",
        cr: "2.4%",
        revenue: "800 تومان"
    },
    {
        campaign: "بازگشت به مدرسه",
        clicks: "4.3%",
        deliveredRate: "97%",
        impressions: 13000,
        cpc: "0.27 تومان",
        cr: "2.1%",
        revenue: "720 تومان"
    },
    {
        campaign: "بلک فرایدی",
        clicks: "6.0%",
        deliveredRate: "95%",
        impressions: 20000,
        cpc: "0.18 تومان",
        cr: "3.0%",
        revenue: "1000 تومان"
    },
    {
        campaign: "سایبر ماندی",
        clicks: "5.5%",
        deliveredRate: "94%",
        impressions: 19000,
        cpc: "0.20 تومان",
        cr: "2.9%",
        revenue: "950 تومان"
    },
    {
        campaign: "ویژه سال نو",
        clicks: "5.3%",
        deliveredRate: "93%",
        impressions: 17000,
        cpc: "0.21 تومان",
        cr: "2.7%",
        revenue: "920 تومان"
    },
    {
        campaign: "شب یلدا",
        clicks: "4.7%",
        deliveredRate: "96%",
        impressions: 13500,
        cpc: "0.26 تومان",
        cr: "2.2%",
        revenue: "780 تومان"
    },
    {
        campaign: "تبلیغات کریمس",
        clicks: "4.1%",
        deliveredRate: "97%",
        impressions: 14500,
        cpc: "0.27 تومان",
        cr: "2.0%",
        revenue: "760 تومان"
    },
    {
        campaign: "حراج میانه سال",
        clicks: "4.9%",
        deliveredRate: "98%",
        impressions: 16500,
        cpc: "0.23 تومان",
        cr: "2.3%",
        revenue: "850 تومان"
    }
];
class TableManager {
    constructor(tableId, options = {}) {
        // Core elements
        this.tableContainer = document.getElementById(tableId);
        if (!this.tableContainer) throw new Error(`جدولی با شناسه "${tableId}" یافت نشد.`);

        // Configuration options
        this.options = {
            itemsPerPage: options.itemsPerPage || 5,
            searchInputId: options.searchInputId || 'searchInput',
            paginationId: options.paginationId || 'pagination',
            exportBtnId: options.exportBtnId || 'exportBtn',
            showingResultsId: options.showingResultsId || 'showingResults',
            ...options
        };

        // State
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;

        // Initialize components
        this.searchInput = document.getElementById(this.options.searchInputId);
        this.paginationContainer = document.getElementById(this.options.paginationId);
        this.exportBtn = document.getElementById(this.options.exportBtnId);
        this.showingResults = document.getElementById(this.options.showingResultsId);

        // Bind methods
        this.initEventListeners();
    }

    // Set data and initialize table
    setData(data) {
        this.data = data;
        this.filteredData = [...data];
        this.renderTable();
        this.updatePagination();
        this.updateResultsInfo();
    }

    // Initialize event listeners
    initEventListeners() {
        // Search functionality
        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => {
                this.handleSearch(this.searchInput.value);
            });
        }

        // Export functionality
        if (this.exportBtn) {
            this.exportBtn.addEventListener('click', () => {
                this.exportToCSV();
            });
        }
    }

    // Handle search functionality
    handleSearch(query) {
        if (!query) {
            this.filteredData = [...this.data];
        } else {
            const searchTerm = query.toLowerCase();
            this.filteredData = this.data.filter(item => {
                return Object.values(item).some(value =>
                    String(value).toLowerCase().includes(searchTerm)
                );
            });
        }

        // Reset to first page and update
        this.currentPage = 1;
        this.renderTable();
        this.updatePagination();
        this.updateResultsInfo();
    }

    // Render table with current data
    renderTable() {
        // Clear existing table content except headers
        const tableBody = this.tableContainer.querySelector('tbody');
        const headerRow = tableBody.querySelector('tr:first-child');
        tableBody.innerHTML = '';
        tableBody.appendChild(headerRow);

        // Calculate pagination
        const startIndex = (this.currentPage - 1) * this.options.itemsPerPage;
        const endIndex = startIndex + this.options.itemsPerPage;
        const currentPageData = this.filteredData.slice(startIndex, endIndex);

        // If no data to display
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
                    </div>
                </td>
            `;
            tableBody.appendChild(noDataRow);
            return;
        }

        // Render rows
        currentPageData.forEach(item => {
            const row = document.createElement('tr');

            Object.values(item).forEach(value => {
                const cell = document.createElement('td');
                cell.textContent = value;
                row.appendChild(cell);
            });

            tableBody.appendChild(row);
        });
    }

    // Update pagination controls
    updatePagination() {
        if (!this.paginationContainer) return;

        const totalPages = Math.ceil(this.filteredData.length / this.options.itemsPerPage);
        this.paginationContainer.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#!';
        prevLink.innerHTML = '<i data-lucide="chevron-right" class="size-4"></i> قبلی';
        prevLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.goToPage(this.currentPage - 1);
            }
        });
        prevLi.appendChild(prevLink);
        this.paginationContainer.appendChild(prevLi);

        // Page numbers
        const maxPagesToShow = 3;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

        if (endPage - startPage + 1 < maxPagesToShow) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            const pageLink = document.createElement('a');
            pageLink.className = 'page-link';
            pageLink.href = '#!';
            pageLink.textContent = i;
            pageLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.goToPage(i);
            });
            pageLi.appendChild(pageLink);
            this.paginationContainer.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#!';
        nextLink.innerHTML = 'بعدی <i data-lucide="chevron-left" class="size-4"></i>';
        nextLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < totalPages) {
                this.goToPage(this.currentPage + 1);
            }
        });
        nextLi.appendChild(nextLink);
        this.paginationContainer.appendChild(nextLi);
        createIcons({ icons });
    }

    // Navigate to specific page
    goToPage(pageNumber) {
        this.currentPage = pageNumber;
        this.renderTable();
        this.updatePagination();
        this.updateResultsInfo();
    }

    // Update showing results text
    updateResultsInfo() {
        if (!this.showingResults) return;

        const startIndex = (this.currentPage - 1) * this.options.itemsPerPage + 1;
        const endIndex = Math.min(startIndex + this.options.itemsPerPage - 1, this.filteredData.length);

        this.showingResults.innerHTML = `نمایش <b class="me-1">${startIndex}-${endIndex}</b>از<b class="ms-1">${this.filteredData.length}</b> نتیجه`;
    }

    // Export data to CSV
    exportToCSV() {
        // Get headers from first row
        const headers = Object.keys(this.data[0] || {});

        // Create CSV content
        let csvContent = headers.join(',') + '\n';

        // Add data rows
        this.filteredData.forEach(item => {
            const values = headers.map(header => {
                const value = item[header];
                // Handle values with commas by wrapping in quotes
                return typeof value === 'string' && value.includes(',') ?
                    `"${value}"` : value;
            });
            csvContent += values.join(',') + '\n';
        });

        // Create download link
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'campaign_data.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}
document.addEventListener('DOMContentLoaded', function () {
    // Initialize table manager
    const tableManager = new TableManager('campaignTable', {
        itemsPerPage: 8,
        searchInputId: 'searchInput',
        paginationId: 'pagination',
        exportBtnId: 'exportBtn',
        showingResultsId: 'showingResults'
    });

    // Set data
    tableManager.setData(campaignData);
});
