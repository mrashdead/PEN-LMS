import ApexCharts from '../../libs/apexcharts/apexcharts.esm.js'
import { createIcons, icons } from 'lucide';
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

//Course Activities
var options = {
    series: [44, 55],
    chart: {
        height: 180,
        type: "donut",
    },
    legend: {
        show: true,
        position: 'bottom',
    },
    labels: ["انجام شده", "در حال انجام"],
    tooltip: {
    style: {
            fontFamily: 'Vazir'
        }
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
    fill: {
        type: 'gradient',
    },
    colors: ["--dx-border-color", "--dx-primary"]
};

allCharts.push([{ 'id': 'courseActivitiesChart', 'data': options }]);

//Students charts
var options = {
    series: [
        {
            data: [
                {
                    x: '1397',
                    y: [241, 100]
                },
                {
                    x: '1398',
                    y: [150, 41]
                },
                {
                    x: '1399',
                    y: [210, 100]
                },
                {
                    x: '1400',
                    y: [200, 10]
                },
                {
                    x: '1401',
                    y: [100, 10]
                },
                {
                    x: '1402',
                    y: [190, 120]
                },
                {
                    x: '1403',
                    y: [154, 241]
                }
            ]
        }
    ],
    chart: {
        height: 272,
        type: "rangeBar",
        zoom: {
            enabled: false
        }
    },
    plotOptions: {
        bar: {
            isDumbbell: true,
            columnWidth: 3,
            dumbbellColors: [["--dx-primary", "--dx-pink"]]
        }
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    legend: {
        show: true,
        showForSingleSeries: true,
        position: 'top',
        horizontalAlign: 'center',
        customLegendItems: ['دانش آموزان تازه', 'دانش آموزان فارغ التحصیل'],
    },
    fill: {
        type: 'gradient',
        gradient: {
            type: 'vertical',
            gradientToColors: ["--dx-primary"],
            inverseColors: true,
            stops: [0, 100]
        }
    },
    grid: {
        padding: {
            bottom: -10,
            right: 0
        },
        xaxis: {
            lines: {
                show: true
            }
        },
        yaxis: {
            lines: {
                show: false
            }
        }
    },
    xaxis: {
        tickPlacement: 'on'
    },
    colors: ["--dx-pink", "--dx-primary"]
};

allCharts.push([{ 'id': 'totalStudentsChart', 'data': options }]);

updateAllCharts();

//holiday swiper
var swiper = new Swiper(".holiday-swiper", {
    spaceBetween: 24,
    grabCursor: true,
    slidesPerView: 1,
    loop: true,
    autoplay: {
        delay: 2500,
        disableOnInteraction: false,
    },
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
});

//date widget
class DateWidgetManager {
    constructor(containerSelector, currentDateSelector) {
        this.container = document.querySelector(containerSelector);
        this.scrollContainer = this.container.querySelector('.d-flex');
        this.dateWidgetItems = this.container.querySelectorAll('.date-widget-item');
        this.activeDate = this.container.querySelector('.date-widget-item.active');
        this.currentDateElement = document.querySelector(currentDateSelector);
        this.today = new Date();
        this.currentDay = this.today.getDate();
        this.init();
    }

    init() {
        this.displayCurrentDate();
        this.scrollToActiveDate();
        this.highlightToday();
        this.addEventListeners();
    }

    displayCurrentDate() {
        // Format and display the current date in the header
        const options = {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };

        const formattedDate = new Intl.DateTimeFormat('fa-IR', options).format(this.today);
        this.currentDateElement.textContent = formattedDate;
    }

    highlightToday() {
        // Find and highlight today's date item
        this.dateWidgetItems.forEach(item => {
            const dayNumber = parseInt(item.textContent);

            if (dayNumber === this.currentDay) {
                item.classList.add('active');
            }
        });
    }

    scrollToActiveDate() {
        if (!this.activeDate) return;

        // We need to wait for the DOM to be fully rendered
        setTimeout(() => {
            // Calculate the scroll position
            const containerRect = this.container.getBoundingClientRect();
            const activeDateRect = this.activeDate.getBoundingClientRect();

            // Calculate the scroll position to center the active date
            const scrollLeftPosition = (activeDateRect.left + activeDateRect.width / 2) -
                (containerRect.left + containerRect.width / 2);

            // Apply scroll
            this.container.scrollLeft = scrollLeftPosition;
        }, 100);
    }

    addEventListeners() {
        // Add click event listeners to date items
        this.dateWidgetItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();

                // Remove active class and styling from all items
                this.dateWidgetItems.forEach(dateItem => {
                    dateItem.classList.remove('active');
                    dateItem.style.backgroundColor = '';
                    dateItem.style.color = '';
                });

                item.classList.add('active');

                const selectedDay = parseInt(item.textContent);
                const selectedDate = new Date(this.today.getFullYear(), this.today.getMonth(), selectedDay);

                const options = {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                };

                const formattedDate = selectedDate.toLocaleDateString('fa-IR', options);
                this.currentDateElement.textContent = formattedDate;
            });
        });
    }
}

// Top Score
class StudentResultsManager {
    constructor(tableContainerId, paginationId, resultsInfoId, pageSize = 5) {
        this.tableContainer = document.getElementById(tableContainerId);
        this.paginationContainer = document.getElementById(paginationId);
        this.resultsInfoElement = document.getElementById(resultsInfoId);
        this.pageSize = pageSize;
        this.currentPage = 1;
        this.data = [];
        this.filteredData = [];
        this.totalItems = 0;

        this.initializeData();
    }

    initializeData() {
        // Set the student results data
        this.data = STUDENT_RESULTS_DATA;
        this.filteredData = [...this.data];
        this.totalItems = this.data.length;

        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    renderTable() {
        // Calculate start and end indices for current page
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = Math.min(startIndex + this.pageSize, this.filteredData.length);

        const currentPageData = this.filteredData.slice(startIndex, endIndex);

        // Create table structure
        let tableHtml = `
      <div class="table-responsive">
        <table class="table table-borderless text-nowrap mb-0">
          <thead>
            <tr>
              <th>نام دانش آموز</th>
              <th>امتیاز</th>
              <th>تاریخ</th>
              <th>سطح</th>
              <th>وضعیت</th>
            </tr>
          </thead>
          <tbody>
      `;

        // Add rows for current page
        currentPageData.forEach(student => {
            const statusClass = student.status === 'پاس' ?
                'bg-success-subtle border border-success-subtle text-success' :
                'bg-danger-subtle border border-danger-subtle text-danger';

            tableHtml += `
          <tr>
            <td>${student.name}</td>
            <td>${student.score}</td>
            <td>${student.date}</td>
            <td>${student.grade}</td>
            <td><span class="badge ${statusClass}">${student.status}</span></td>
          </tr>
        `;
        });

        tableHtml += `
          </tbody>
        </table>
      </div>
      `;

        this.tableContainer.innerHTML = tableHtml;
    }

    renderPagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.pageSize);

        let paginationHtml = `
        <ul class="pagination justify-content-center justify-content-md-end mb-0">
          <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#!" data-page="prev">
              <i data-lucide="chevron-right" class="size-4"></i> قبلی
            </a>
          </li>
      `;

        // Generate page numbers
        for (let i = 1; i <= totalPages; i++) {
            paginationHtml += `
          <li class="page-item ${this.currentPage === i ? 'active' : ''}">
            <a class="page-link" href="#!" data-page="${i}">${i}</a>
          </li>
        `;
        }

        paginationHtml += `
          <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#!" data-page="next">
              بعدی <i data-lucide="chevron-left" class="size-4"></i>
            </a>
          </li>
        </ul>
      `;

        this.paginationContainer.innerHTML = paginationHtml;

        // Add event listeners to pagination links
        const paginationLinks = this.paginationContainer.querySelectorAll('.page-link');
        paginationLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const pageAction = link.getAttribute('data-page');

                if (pageAction === 'قبلی' && this.currentPage > 1)
                    this.goToPage(this.currentPage - 1);
                else if (pageAction === 'بعدی' && this.currentPage < totalPages)
                    this.goToPage(this.currentPage + 1);
                else if (!isNaN(parseInt(pageAction)))
                    this.goToPage(parseInt(pageAction));
            });
        });
        createIcons({ icons });
    }

    updateResultsInfo() {
        const startIndex = (this.currentPage - 1) * this.pageSize + 1;
        const endIndex = Math.min(startIndex + this.pageSize - 1, this.filteredData.length);

        this.resultsInfoElement.innerHTML = `
        نمایش <b class="me-1">${startIndex}-${endIndex}</b> از <b class="ms-1">${this.filteredData.length}</b> نتیجه
      `;
    }

    goToPage(pageNumber) {
        this.currentPage = pageNumber;
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }

    search(searchTerm) {
        if (!searchTerm.trim()) {
            this.filteredData = [...this.data];
        } else {
            const term = searchTerm.toLowerCase().trim();
            this.filteredData = this.data.filter(student => {
                return (
                    student.name.toLowerCase().includes(term) ||
                    student.score.toLowerCase().includes(term) ||
                    student.date.toLowerCase().includes(term) ||
                    student.grade.toLowerCase().includes(term) ||
                    student.status.toLowerCase().includes(term)
                );
            });
        }

        this.currentPage = 1;
        this.renderTable();
        this.renderPagination();
        this.updateResultsInfo();
    }
}

// Student results data in JSON format
const STUDENT_RESULTS_DATA = [
    {
        "name": "دوروتی دیلی",
        "score": "498/600",
        "date": "22 دی 1402",
        "grade": "A",
        "status": "پاس"
    },
    {
        "name": "سیلویا هوور",
        "score": "140/600",
        "date": "22 دی 1402",
        "grade": "D",
        "status": "مردود"
    },
    {
        "name": "جوناتان دیویس",
        "score": "450/600",
        "date": "22 دی 1402",
        "grade": "A",
        "status": "پاس"
    },
    {
        "name": "مارتا استوارت",
        "score": "320/600",
        "date": "22 دی 1402",
        "grade": "B",
        "status": "پاس"
    },
    {
        "name": "هارولد فینچ",
        "score": "275/600",
        "date": "22 دی 1402",
        "grade": "C",
        "status": "پاس"
    },
    {
        "name": "جان اسمیت",
        "score": "510/600",
        "date": "25 دی 1402",
        "grade": "A",
        "status": "پاس"
    },
    {
        "name": "اما ویلسون",
        "score": "180/600",
        "date": "25 دی 1402",
        "grade": "D",
        "status": "مردود"
    },
    {
        "name": "مایکل براون",
        "score": "350/600",
        "date": "27 دی 1402",
        "grade": "B",
        "status": "پاس"
    },
    {
        "name": "اولیویا تیلور",
        "score": "420/600",
        "date": "28 دی 1402",
        "grade": "A",
        "status": "پاس"
    },
    {
        "name": "جیمز اندرسون",
        "score": "290/600",
        "date": "29 دی 1402",
        "grade": "C",
        "status": "پاس"
    },
    {
        "name": "سوفیا مارتینز",
        "score": "130/600",
        "date": "30 دی 1402",
        "grade": "D",
        "status": "مردود"
    },
    {
        "name": "ویلیام جانسون",
        "score": "460/600",
        "date": "2 بهمن 1402",
        "grade": "A",
        "status": "پاس"
    }
];

// Initialize the StudentResultsManager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const tableManager = new StudentResultsManager('resultsTable', 'pagination', 'showingResults');
    const dateManager = new DateWidgetManager('section[data-simplebar]', '#current-date');

    // Optional: Add search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            tableManager.search(e.target.value);
        });
    }
});