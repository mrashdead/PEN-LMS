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

//basic Chart
var options = {
    series: [
        {
            name: 'دمای هوای نیویورک',
            data: [
                {
                    x: 'ژانویه',
                    y: [-2, 4]
                },
                {
                    x: 'فوریه',
                    y: [-1, 6]
                },
                {
                    x: 'مارس',
                    y: [3, 10]
                },
                {
                    x: 'آوریل',
                    y: [8, 16]
                },
                {
                    x: 'مه',
                    y: [13, 22]
                },
                {
                    x: 'ژوئن',
                    y: [18, 26]
                },
                {
                    x: 'جولای',
                    y: [21, 29]
                },
                {
                    x: 'آگوست',
                    y: [21, 28]
                },
                {
                    x: 'سپتامبر',
                    y: [17, 24]
                },
                {
                    x: 'اکتبر',
                    y: [11, 18]
                },
                {
                    x: 'نوامبر',
                    y: [6, 12]
                },
                {
                    x: 'دسامبر',
                    y: [1, 7]
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "rangeArea",
    },
    stroke: {
        curve: 'straight'
    },
    markers: {
        hover: {
            sizeOffset: 5
        }
    },
    dataLabels: {
        enabled: false
    },
    yaxis: {
        labels: {
            formatter: (val) => {
                return val + '°C'
            }
        }
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'rangeBasicChart', 'data': options }]);

//Combo Chart
var options = {
    series: [
        {
            type: 'rangeArea',
            name: 'B محدوده تیم',

            data: [
                {
                    x: 'ژانویه',
                    y: [1100, 1900]
                },
                {
                    x: 'فوریه',
                    y: [1200, 1800]
                },
                {
                    x: 'مارس',
                    y: [900, 2900]
                },
                {
                    x: 'آوریل',
                    y: [1400, 2700]
                },
                {
                    x: 'مه',
                    y: [2600, 3900]
                },
                {
                    x: 'ژوئن',
                    y: [500, 1700]
                },
                {
                    x: 'جولای',
                    y: [1900, 2300]
                },
                {
                    x: 'آگوست',
                    y: [1000, 1500]
                }
            ]
        },

        {
            type: 'rangeArea',
            name: 'A محدوده تیم',
            data: [
                {
                    x: 'ژانویه',
                    y: [3100, 3400]
                },
                {
                    x: 'فوریه',
                    y: [4200, 5200]
                },
                {
                    x: 'مارس',
                    y: [3900, 4900]
                },
                {
                    x: 'آوریل',
                    y: [3400, 3900]
                },
                {
                    x: 'مه',
                    y: [5100, 5900]
                },
                {
                    x: 'ژوئن',
                    y: [5400, 6700]
                },
                {
                    x: 'جولای',
                    y: [4300, 4600]
                },
                {
                    x: 'آگوست',
                    y: [2100, 2900]
                }
            ]
        },

        {
            type: 'line',
            name: 'B میانه تیم',
            data: [
                {
                    x: 'ژانویه',
                    y: 1500
                },
                {
                    x: 'فوریه',
                    y: 1700
                },
                {
                    x: 'مارس',
                    y: 1900
                },
                {
                    x: 'آوریل',
                    y: 2200
                },
                {
                    x: 'مه',
                    y: 3000
                },
                {
                    x: 'ژوئن',
                    y: 1000
                },
                {
                    x: 'جولای',
                    y: 2100
                },
                {
                    x: 'آگوست',
                    y: 1200
                },
                {
                    x: 'سپتامبر',
                    y: 1800
                },
                {
                    x: 'اکتبر',
                    y: 2000
                }
            ]
        },
        {
            type: 'line',
            name: 'A میانه تیم',
            data: [
                {
                    x: 'ژانویه',
                    y: 3300
                },
                {
                    x: 'فوریه',
                    y: 4900
                },
                {
                    x: 'مارس',
                    y: 4300
                },
                {
                    x: 'آوریل',
                    y: 3700
                },
                {
                    x: 'مه',
                    y: 5500
                },
                {
                    x: 'ژوئن',
                    y: 5900
                },
                {
                    x: 'جولای',
                    y: 4500
                },
                {
                    x: 'آگوست',
                    y: 2400
                },
                {
                    x: 'سپتامبر',
                    y: 2100
                },
                {
                    x: 'اکتبر',
                    y: 1500
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: 'rangeArea',
        animations: {
            speed: 500
        }
    },
    dataLabels: {
        enabled: false
    },
    fill: {
        opacity: [0.24, 0.24, 1, 1]
    },
    forecastDataPoints: {
        count: 2
    },
    stroke: {
        curve: 'straight',
        width: [0, 0, 2, 2]
    },
    legend: {
        show: true,
        customLegendItems: ['B تیم', 'A تیم'],
        inverseOrder: true
    },
    markers: {
        hover: {
            sizeOffset: 5
        }
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-danger"],
};

allCharts.push([{ 'id': 'rangeComboChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });