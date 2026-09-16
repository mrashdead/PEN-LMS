// scroll navbar class add
document.addEventListener('DOMContentLoaded', function () {
    const navbar = document.querySelector('#navbarInvoice');
    const scrollThreshold = 50;

    function handleNavbarScroll() {
        if (window.scrollY > scrollThreshold)
            navbar.classList.add('scroll-sticky');
        else
            navbar.classList.remove('scroll-sticky');
    }

    let isScrolling;
    window.addEventListener('scroll', function () {
        window.clearTimeout(isScrolling);
        isScrolling = setTimeout(handleNavbarScroll, 30);
    }, false);

    handleNavbarScroll();
});
const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

navLinks.forEach(link => {
    link.addEventListener('click', function () {
        // Remove active from all
        navLinks.forEach(nav => nav.classList.remove('active'));
        // Add active to clicked
        this.classList.add('active');
    });
});
//dark mode toggle
document.addEventListener("DOMContentLoaded", function () {
    var toggleButton = document.getElementById("theme-toggle-btn");
    var moonIcon = document.getElementById("moon-icon");
    var sunIcon = document.getElementById("sun-icon");

    var savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);

    moonIcon.style.display = (savedTheme === 'light') ? 'block' : 'none';
    sunIcon.style.display = (savedTheme === 'dark') ? 'block' : 'none';

    toggleButton.addEventListener("click", function () {
        var currentTheme = document.documentElement.getAttribute('data-bs-theme');
        var newTheme = (currentTheme === 'dark') ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        moonIcon.style.display = (newTheme === 'light') ? 'block' : 'none';
        sunIcon.style.display = (newTheme === 'dark') ? 'block' : 'none';
    });
});

import ApexCharts from '../../libs/apexcharts/apexcharts.esm.js'

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
        // Check if the element exists before trying to render the chart
        const chartElement = document.querySelector("#" + chart[0].id);
        if (!chartElement) {
            console.warn(`عنصر نمودار با شناسه "${chart[0].id}" پیدا نشد، و رندر شدن را متوقف می‌کند.`);
            return; // Skip this chart
        }

        const jsonData = JSON.parse(JSON.stringify(chart[0].data));
        const data = replaceCSSVariables(structuredClone(jsonData));
        if (chart[0].chart)
            chart[0].chart.destroy();

        var chart2 = new ApexCharts(chartElement, data);
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

// Make sure to initialize charts only after DOM content is loaded
document.addEventListener('DOMContentLoaded', function () {
    //Basic Charts
    var options = {
        series: [
            {
                name: "نام مجموعه",
                data: [10, 41, 35, 51, 49, 62, 69, 91, 148]
            }
        ],
        chart: {
            defaultLocale: "en",
            height: 350,
            type: "line",
            fontFamily: "Vazir, sans-serif",
            zoom: {
                enabled: true
            },
            toolbar: {
                show: false,
            }
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth'
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
            labels: {
                style: {
                    fontFamily: "Vazir",
                }
            }
        },
        tooltip: {
            style: {
                fontFamily: "Vazir"
            },
            x: {
                show: true
            },
            y: {
                formatter: function (val) {
                    // Fix the reference to formatCurrency
                    return val.toString(); // Replace with proper formatting if needed
                }
            }
        },
        grid: {
            strokeDashArray: 2,
            padding: {
                top: 0,
                right: 0,
                bottom: 0,
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
        responsive: [
            {
                breakpoint: 768,
                options: {
                xaxis: {
                    labels: {
                    rotate: -45,
                    rotateAlways: true,
                    hideOverlappingLabels: true,
                    style: {
                        fontSize: '10px'
                    }
                    }
                }
                }
            }
        ],
        colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-danger", "--dx-secondary"],
    };

    // Check if the element exists before adding to allCharts
    if (document.getElementById('basicLineChart')) {
        allCharts.push([{ 'id': 'basicLineChart', 'data': options }]);
        updateAllCharts();
    } else {
        console.warn('عنصری با شناسه "basicLineChart" در DOM یافت نشد.');
    }
});
