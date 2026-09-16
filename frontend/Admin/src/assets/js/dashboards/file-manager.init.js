import ApexCharts from '../../libs/apexcharts/apexcharts.esm.js'
import Swiper from 'swiper/bundle';
import 'swiper/css/bundle';

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

//Analytics Chart
var options = {
    series: [{
        name: 'مجموع گیگابایت',
        data: [44, 55, 41, 67, 22]
    }],
    chart: {
        height: 290,
        type: 'bar',
        toolbar: {
            show: false,
        }
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
    grid: {
        padding: {
            right: -12,
            top: -18,
            bottom: -8,
            left: 0
        }
    },
    xaxis: {
        labels: {
            rotate: -45
        },
        categories: ['دراپ باکس', 'کلاود', 'مگا', 'گوگل', 'درایو'],
        tickPlacement: 'on'
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'light',
            type: "horizontal",
            shadeIntensity: 0.25,
            gradientToColors: undefined,
            inverseColors: ["--dx-primary"],
            opacityFrom: 0.85,
            opacityTo: 0.85,
            stops: [50, 0, 100]
        },
    },
    yaxis: {
        labels: {
            offsetX: -8,
        }
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'analyticsChart', 'data': options }]);

//Overview Storage Chart
var options = {
    series: [44, 55, 41, 17, 15],
    chart: {
        height: 252,
        type: "donut",
    },
    plotOptions: {
        pie: {
            startAngle: -90,
            endAngle: 90,
            offsetY: 5
        }
    },
    grid: {
        padding: {
            bottom: -80
        }
    },
    stroke: {
        width: 0,
    },
    fill: {
        type: 'gradient',
    },
    labels: ["مستندات", "تصاویر", "ویدئوها", "صداها", "سایر"],
    legend: {
        position: 'bottom'
    },
    tooltip: {
    style: {
            fontFamily: 'Vazir'
        }
    },
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary", "--dx-danger"],
};

allCharts.push([{ 'id': 'overviewStorageChart', 'data': options }]);

updateAllCharts();

//my favorite slider
var swiper = new Swiper(".favorites-swiper", {
    spaceBetween: 24,
    grabCursor: true,
    slidesPerView: 1,
    loop: true,
    autoplay: {
        delay: 2500,
        disableOnInteraction: false,
    },
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
});

/**
 * TableManager - A class to manage table data and search functionality
 */
class TableManager {
    constructor(tableId, searchInputId, data) {
        this.tableElement = document.getElementById(tableId);
        this.searchInput = document.getElementById(searchInputId);
        this.data = data;
        this.init();
    }

    init() {
        // Render the initial table
        this.renderTable(this.data);

        // Add event listener for search input
        this.searchInput.addEventListener('input', () => {
            this.handleSearch();
        });
    }

    /**
     * Filter data based on search term
     */
    handleSearch() {
        const searchTerm = this.searchInput.value.toLowerCase().trim();

        if (!searchTerm) {
            this.renderTable(this.data);
            return;
        }

        const filteredData = this.data.filter(item => {
            return (
                item.name.toLowerCase().includes(searchTerm) ||
                item.type.toLowerCase().includes(searchTerm) ||
                item.size.toLowerCase().includes(searchTerm) ||
                item.date.toLowerCase().includes(searchTerm)
            );
        });

        this.renderTable(filteredData);
    }

    /**
     * Render table with the provided data
     */
    renderTable(data) {
        const tbody = this.tableElement.querySelector('tbody');
        tbody.innerHTML = '';

        if (data.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
         <td colspan="6" class="text-center py-4">
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
                </td>
        `;
            tbody.appendChild(emptyRow);
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
          <td>
            <div class="d-flex gap-3 align-items-center">
              <img src="assets/images/file-manager/icons/${item.icon}" loading="lazy" alt="" class="size-8">
              <a href="#!" class="text-body">
                <h6 class="mb-0">${item.name}</h6>
              </a>
            </div>
          </td>
          <td>${item.type}</td>
          <td>${item.size}</td>
          <td>${item.date}</td>
          <td>
            <div class="d-flex gap-3">
              <a class="link link-custom-primary" href="#!" aria-label="overview"><i class="ri-edit-2-line"></i></a>
              <a class="link link-custom-primary" href="#!" aria-label="edit"><i class="ri-download-2-line"></i></a>
              <a href="#!" class="link link-custom-danger" aria-label="delete"><i class="ri-delete-bin-6-line"></i></a>
            </div>
          </td>
        `;
            tbody.appendChild(row);
        });
    }
}

// Sample data that would come from your backend or a JSON file
const tableData = [
    {
        name: "پروژه انیمیشن",
        type: "مستندات",
        size: "24 MB",
        date: "31 تیر 1403",
        icon: "document.png"
    },
    {
        name: "طراحی رابط کاربری",
        type: "تصویر",
        size: "154 MB",
        date: "8 خرداد 1403",
        icon: "picture.png"
    },
    {
        name: "آموزش مدیریت",
        type: "ویدئو",
        size: "149 MB",
        date: "13 بهمن 1402",
        icon: "video.png"
    },
    {
        name: "هویت برند",
        type: "AI",
        size: "17 MB",
        date: "22 بهمن 1402",
        icon: "ai-file-format.png"
    },
    {
        name: "رزومه",
        type: "PDF",
        size: "11 MB",
        date: "30 اردیبهشت 1402",
        icon: "pdf.png"
    }
];

// Initialize the TableManager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const tableManager = new TableManager('fileTable', 'searchInput', tableData);
});