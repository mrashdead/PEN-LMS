//sampleSelect
VirtualSelect.init({
    ele: "#sampleSelect",
    options: [
        { label: "همه", value: "All" },
        { label: "پرداخت شده", value: "Paid" },
        { label: "پرداخت نشده", value: "Unpaid" },
        { label: "در انتظار", value: "Pending" },
        { label: "معوقه", value: "Overdue" },
    ],
});

import ApexCharts from '../../../libs/apexcharts/apexcharts.esm.js'
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

document.getElementById('darkModeButton')?.addEventListener('click', function () {
    setTimeout(() => {
        updateAllCharts();
    }, 0);
});

//expense chart
var options = {
    series: [16, 8, 12, 9],
    labels: ['پرداخت شده', 'پرداخت نشده', 'در انتظار', 'معوقه'],
    chart: {
        height: 110,
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
    plotOptions: {
        pie: {
            expandOnClick: true,
            donut: {
                size: '60%',
            }
        }
    },
    legend: {
        offsetY: -10,
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                height: 200
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-success", "--dx-info", "--dx-warning", "--dx-danger"]
};

allCharts.push([{ 'id': 'invoiceStatusChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });

document.addEventListener('DOMContentLoaded', function () {
    // DOM elements
    const invoiceCards = Array.from(document.querySelectorAll('.invoice-card'));
    const paginationInfo = document.querySelector('.pagination-courting-info');
    const paginationContainer = document.querySelector('.pagination');
    const sampleSelect = document.getElementById('sampleSelect');

    // Mapping between values and Persian labels
    const statusMapping = {
        'Paid': 'پرداخت شده',
        'Unpaid': 'پرداخت نشده',
        'Pending': 'در انتظار',
        'Overdue': 'معوقه'
    };

    sampleSelect?.addEventListener('change', function (event) {
        currentFilter = event.target.value; // Use value instead of label
        currentPage = 1; // Reset to first page when filter changes

        // Filter cards
        if (currentFilter === 'All') {
            filteredCards = [...invoiceCards];
        } else {
            filteredCards = invoiceCards.filter(card => {
                const statusBadge = card.querySelector('.badge');
                const cardStatus = statusBadge.textContent.trim();
                return cardStatus === statusMapping[currentFilter];
            });
        }

        // Update UI
        updatePaginationInfo();
        renderCards();
        setupPagination();

    });

    // Pagination variables
    const cardsPerPage = 8;
    let currentPage = 1;
    let currentFilter = 'All Cards';
    let filteredCards = [...invoiceCards];

    // Initialize
    updatePaginationInfo();
    renderCards();
    setupPagination();

    // Render cards for current page
    function renderCards() {
        // Hide all cards first
        invoiceCards.forEach(card => card.style.display = 'none');

        // Calculate start and end index
        const startIndex = (currentPage - 1) * cardsPerPage;
        const endIndex = Math.min(startIndex + cardsPerPage, filteredCards.length);

        // Show cards for current page
        for (let i = startIndex; i < endIndex; i++) {
            if (filteredCards[i]) {
                filteredCards[i].style.display = 'block';
            }
        }
    }

    // Update pagination info text
    function updatePaginationInfo() {
        if (paginationInfo) {
            const start = Math.min((currentPage - 1) * cardsPerPage + 1, filteredCards.length);
            const end = Math.min(currentPage * cardsPerPage, filteredCards.length);
            paginationInfo.innerHTML = `نمایش <b class="me-1">${start}-${end}</b>از<b class="ms-1">${filteredCards.length}</b> نتیجه`;
        }
    }

    // Setup pagination buttons
    function setupPagination() {
        const totalPages = Math.ceil(filteredCards.length / cardsPerPage);

        // Clear existing pagination
        paginationContainer.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = 'page-item' + (currentPage === 1 ? ' disabled' : '');
        prevLi.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        prevLi.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderCards();
                updatePaginationInfo();
                setupPagination();
            }
        });
        paginationContainer.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = 'page-item' + (i === currentPage ? ' active' : '');
            pageLi.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
            pageLi.addEventListener('click', () => {
                currentPage = i;
                renderCards();
                updatePaginationInfo();
                setupPagination();
            });
            paginationContainer.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = 'page-item' + (currentPage === totalPages ? ' disabled' : '');
        nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        nextLi.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                renderCards();
                updatePaginationInfo();
                setupPagination();
            }
        });
        paginationContainer.appendChild(nextLi);
        createIcons({ icons });
    }

    function init() {
        updatePaginationInfo();
        renderCards();
        setupPagination();
    }

    init();
});