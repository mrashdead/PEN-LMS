import ApexCharts from '../../libs/apexcharts/apexcharts.esm.js';
import { createIcons, icons } from 'lucide';
//Table
class TableManager {
    constructor(tableId, data, itemsPerPage = 8) {
        this.tableId = tableId;
        this.data = data;
        this.itemsPerPage = itemsPerPage;
        this.currentPage = 1;
        this.tableElement = document.getElementById(tableId);
        this.totalPages = Math.ceil(this.data.length / this.itemsPerPage);

        this.init();
    }

    init() {
        this.renderTable();
        this.setupPagination();
        this.updatePaginationInfo();
    }

    renderTable() {
        // Clear existing table body
        const tbody = this.tableElement.querySelector('tbody');
        tbody.innerHTML = '';

        // Calculate start and end index for current page
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.data.length);

        // Render table rows for current page
        for (let i = startIndex; i < endIndex; i++) {
            const item = this.data[i];
            const row = document.createElement('tr');

            // Product Code column
            let cell = document.createElement('td');
            cell.textContent = item.productCode;
            row.appendChild(cell);

            // Item column with link
            cell = document.createElement('td');
            const link = document.createElement('a');
            link.href = "apps-ecommerce-product-overview.html";
            link.className = "text-body";
            link.textContent = item.item;
            cell.appendChild(link);
            row.appendChild(cell);

            // Quantity column
            cell = document.createElement('td');
            cell.textContent = item.qtyLeft;
            row.appendChild(cell);

            // Status column with badge
            cell = document.createElement('td');
            const badge = document.createElement('span');

            if (item.qtyLeft === 0) {
                badge.className = "badge bg-danger-subtle text-danger border border-danger-subtle";
                badge.textContent = "ناموجود";
            } else if (item.qtyLeft < 150) {
                badge.className = "badge bg-warning-subtle text-warning border border-warning-subtle";
                badge.textContent = "موجودی کم";
            } else {
                badge.className = "badge bg-secondary-subtle text-secondary border border-secondary-subtle";
                badge.textContent = "موجود در انبار";
            }

            cell.appendChild(badge);
            row.appendChild(cell);

            // Price column
            cell = document.createElement('td');
            cell.textContent = item.price;
            row.appendChild(cell);

            tbody.appendChild(row);
        }
    }

    setupPagination() {
        const paginationElement = document.getElementById('pagination');
        paginationElement.innerHTML = '';

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
        paginationElement.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= this.totalPages; i++) {
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
            paginationElement.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}`;

        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#!';
        nextLink.innerHTML = 'بعدی <i data-lucide="chevron-left" class="size-4"></i>';

        nextLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < this.totalPages) {
                this.goToPage(this.currentPage + 1);
            }
        });

        nextLi.appendChild(nextLink);
        paginationElement.appendChild(nextLi);
        createIcons({ icons });
    }

    updatePaginationInfo() {
        const infoElement = document.getElementById('pagination-info');
        const startItem = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endItem = Math.min(startItem + this.itemsPerPage - 1, this.data.length);

        infoElement.innerHTML = `نمایش <b class="me-1">${startItem}-${endItem}</b> از<b class="ms-1">${this.data.length}</b> نتیجه`;
    }

    goToPage(page) {
        this.currentPage = page;
        this.renderTable();
        this.setupPagination();
        this.updatePaginationInfo();
    }
}

// Sample data in JSON format
const productData = [
    {
        productCode: "PEP-1478",
        item: "تاپ لوله‌ای طرح رافل بلوز",
        qtyLeft: 145,
        price: "14,000 تومان"
    },
    {
        productCode: "PEP-1479",
        item: "ساعت آویزدار طلایی رنگ",
        qtyLeft: 569,
        price: "20,000 تومان"
    },
    {
        productCode: "PEP-1480",
        item: "لباس ژاکت کشباف",
        qtyLeft: 541,
        price: "22,490 تومان"
    },
    {
        productCode: "PEP-1481",
        item: "لباس آستین‌دار",
        qtyLeft: 126,
        price: "31,780 تومان"
    },
    {
        productCode: "PEP-1482",
        item: "کفش زرد زنانه",
        qtyLeft: 0,
        price: "50,000 تومان"
    },
    {
        productCode: "PEP-1483",
        item: "کلاه حصیری مدل کلاه کابوی",
        qtyLeft: 571,
        price: "50,000 تومان"
    },
    {
        productCode: "PEP-1484",
        item: "کفش بسکتبال اسنیکرز نایک",
        qtyLeft: 0,
        price: "50,000 تومان"
    },
    {
        productCode: "PEP-1485",
        item: "تی‌شرت مدرن و فشن",
        qtyLeft: 321,
        price: "30,000 تومان"
    },
    {
        productCode: "PEP-1486",
        item: "ژاکت جین",
        qtyLeft: 250,
        price: "60,000 تومان"
    },
    {
        productCode: "PEP-1487",
        item: "کیف پول چرمی",
        qtyLeft: 89,
        price: "25,000 تومان"
    },
    {
        productCode: "PEP-1488",
        item: "عینک آفتابی",
        qtyLeft: 120,
        price: "16,000 تومان"
    },
    {
        productCode: "PEP-1489",
        item: "کوله پشتی کنواس",
        qtyLeft: 203,
        price: "40,000 تومان"
    }
];

// Initialize table when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Create a new TableManager instance
    const tableManager = new TableManager('product-table', productData, 8);
});
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

//expense chart
var options = {
    series: [44, 55, 41, 17, 15],
    chart: {
        height: 75,
        type: "donut",
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    dataLabels: {
        enabled: false
    },
    legend: {
        show: false,
        position: 'bottom'
    },
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-danger", "--dx-secondary"],
    grid: {
        padding: {
            top: -6,
            right: 0,
            bottom: -10,
            left: 0
        },
    }
};

allCharts.push([{ 'id': 'expenseChart', 'data': options }]);

//Product Sales chart
var options = {
    series: [{
        name: 'سود فروش',
        data: [44, 55, 57, 56, 61, 58, 63, 60, 66]
    }, {
        name: 'درآمد',
        data: [76, 85, 101, 98, 87, 105, 91, 114, 94]
    }],
    chart: {
        height: 280,
        type: "bar",
        toolbar: {
            show: false,
        }
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: '55%',
            borderRadius: [10],
        },
    },
    states: {
        hover: {
            filter: {
                type: 'none',
            }
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        show: true,
        width: 2,
        lineCap: 'round',
        colors: ['transparent']
    },
    colors: ["--dx-danger", "--dx-primary"],
    xaxis: {
        categories: ['آذر', 'آبان', 'مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین' ],
    },
    yaxis: {
        title: {
            text: '(میلیون) تومان',
            style: { fontFamily: 'Vazir' }
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
    }
};

allCharts.push([{ 'id': 'productSalesChart', 'data': options }]);

//Net Profit Chart
var options = {
    series: [
        {
            name: 'سود',
            data: [5, 4, 7, 2, 8, 6, 3]
        }],
    chart: {
        height: 130,
        type: "bar",
        toolbar: {
            show: false,
        },
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        bar: {
            horizontal: false,
            endingShape: 'rounded'
        },
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    colors: ["--dx-primary"],
    grid: {
        padding: {
            top: 0,
            right: -10,
            bottom: 0,
            left: -10
        }
    },
    stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
    },
};

allCharts.push([{ 'id': 'netProfitChart', 'data': options }]);

//Traffic Chart
var options = {
    series: [{
        name: 'فروش',
        data: [0.4, 0.65, 0.76, 0.88, 1.5, 2.1, 2.9, 3.8, 3.9, 4.2, 4, 4.3, 4.1, 4.2, 4.5,
            3.9, 3.5
        ]
    },
    {
        name: 'بازدید',
        data: [-0.8, -1.05, -1.06, -1.18, -1.4, -2.2, -2.85, -3.7, -3.96, -4.22, -4.3, -4.4,
        -4.1, -4, -4.1, -3.4, -3.1
        ]
    }
    ],
    chart: {
        height: 320,
        type: "bar",
        stacked: true,
        toolbar: {
            show: false,
        }
    },
    colors: ["--dx-primary", "--dx-success"],
    plotOptions: {
        bar: {
            horizontal: true,
            barHeight: '80%',
        },
    },
    dataLabels: {
        enabled: false
    },
    grid: {
        strokeDashArray: 2,
        xaxis: {
            lines: {
                show: false
            }
        },
        yaxis: {
            lines: {
                show: true
            }
        },
        padding: {
            top: -20,
            bottom: 0,
        },
        row: {
            opacity: 0
        },
    },
    yaxis: {
        min: -5,
        max: 5,
    },
    states: {
        hover: {
            filter: {
                type: 'none',
            }
        },
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        },
        shared: false,
        x: {
            formatter: function (val) {
                return val
            }
        },
        y: {
            formatter: function (val) {
                return Math.abs(val) + "%"
            }
        }
    },
    xaxis: {
        categories: ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'],
        labels: {
            formatter: function (val) {
                return Math.abs(Math.round(val)) + "%"
            }
        }
    },
};

allCharts.push([{ 'id': 'trafficChart', 'data': options }]);

updateAllCharts();

//Top Location Map
const markersMap = new jsVectorMap({
    selector: "#topLocationMap",
    map: "world",
    markers: [{
        name: "برزیل",
        coords: [-14.235, -51.9253]
    },
    {
        name: "روسیه",
        coords: [61.524, 105.3188]
    },
    {
        name: "چین",
        coords: [35.8617, 104.1954]
    }],
    labels: {
        markers: {
            render: (marker) => marker.name
        }
    },
    selectedMarkers: [1],
});

