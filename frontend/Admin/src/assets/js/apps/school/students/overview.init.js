import Swiper from 'swiper/bundle';
import 'swiper/css/bundle';

var swiper = new Swiper(".achievementsSwiper", {
    loop: true,
    spaceBetween: 0,
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
});

import ApexCharts from '../../../../libs/apexcharts/apexcharts.esm.js'

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

//Test Marks (Subject) Chart
var options = {
    series: [{
        name: "عملکرد",
        data: [69, 78, 49, 63, 54, 87]
    }],
    chart: {
        height: 265,
        type: 'bar',
        toolbar: {
            show: false,
        }
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    plotOptions: {
        bar: {
            columnWidth: '20%',
            distributed: true,
        }
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'dark',
            type: "horizontal",
            shadeIntensity: 0.2,
            inverseColors: true,
            opacityFrom: 1,
            opacityTo: 1,
            stops: [0, 50, 30],
            colorStops: []
        }
    },
    states: {
        normal: {
            filter: {
                type: 'none',
                value: 0,
            }
        },
        hover: {
            filter: {
                type: 'none',
                value: 0,
            }
        },
        active: {
            filter: {
                type: 'none',
                value: 0,
            }
        },
    },
    dataLabels: {
        enabled: false,
        formatter: function (val) {
            return val + "%";
        },
    },
    legend: {
        show: false
    },
    xaxis: {
        categories: [
            ['ریاضیات'],
            ['فیزیک'],
            ['شیمی'],
            ['زیست'],
            ['دینی'],
            ['انگلیسی']
        ],
    },
    grid: {
        padding: {
            top: -20,
            right: 0,
            bottom: 0
        },
    },
    yaxis: {
        labels: {
            formatter: function (val) {
                return val + "%";
            }
        }
    },
    colors: ["--dx-primary", "--dx-secondary", "--dx-info", "--dx-success", "--dx-danger", "--dx-orange"],
    grid: {
        padding: {
            top: -6,
            right: 0,
            bottom: -6,
            left: 0
        },
    }
};

allCharts.push([{ 'id': 'testMarksSubjectChart', 'data': options }]);


// document.addEventListener("alpine:init", () => {
//     Alpine.data("testMarksSubjectApp", () => ({

//         labels: [
//             ['ریاضیات'],
//             ['فیزیک'],
//             ['شیمی'],
//             ['زیست'],
//             ['دینی'],
//             ['انگلیسی']
//         ],
//         init() {
//           this.colorCodes = this.getColorCodes();

//             let testMarksSubjectChart = new ApexCharts(this.$refs.testMarksSubjectChart, this.options);
//             testMarksSubjectChart.render();
//         },
//         get options() {
//             return {
//                 series: this.series,

//                 colors: this.colorCodes,
//             };
//         },
//         getColorCodes() {
//           return ['#90cdff', '#d8b4fe', '#7dd3fc', '#86efac', '#fca5a5', '#fdba74'];
//       }
//     }));
// });

updateAllCharts();