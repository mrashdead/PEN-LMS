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

//Basic Chart
var options = {
    series: [{
        name: 'سری اول',
        data: [80, 50, 30, 40, 100, 20],
    }],
    chart: {
        height: 370,
        type: "radar",
    },
    title: {
        text: 'Basic Radar Chart'
    },
    xaxis: {
        categories: ['ژانویه', 'فوریه', 'مارس', 'آوریل', 'مه', 'ژوئن'],
        labels: {
            style: {
                fontFamily: 'Vazir, sans-serif'
            }
        }
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'basicRadarChart', 'data': options }]);

//Radar – Multiple Series Chart
var options = {
    series: [{
        name: 'سری اول',
        data: [80, 50, 30, 40, 100, 20],
    }, {
        name: 'سری دوم',
        data: [20, 30, 40, 80, 20, 80],
    }, {
        name: 'سری سوم',
        data: [44, 76, 78, 13, 43, 10],
    }],
    chart: {
        height: 370,
        type: 'radar',
        dropShadow: {
            enabled: true,
            blur: 1,
            left: 1,
            top: 1
        }
    },
    title: {
        text: 'Radar Chart - Multi Series'
    },
    stroke: {
        width: 2
    },
    fill: {
        opacity: 0.1
    },
    markers: {
        size: 0
    },
    xaxis: {
        categories: ['2011', '2012', '2013', '2014', '2015', '2016'],
    },
    colors: ["--dx-primary", "--dx-warning", "--dx-success"],
};

allCharts.push([{ 'id': 'multipleRadarChart', 'data': options }]);

//Radar with Polygon-fill Chart
var options = {
    series: [{
        name: 'سری اول',
        data: [20, 100, 40, 30, 50, 80, 33],
    }],
    chart: {
        height: 330,
        type: 'radar',
        dropShadow: {
            enabled: true,
            blur: 1,
            left: 1,
            top: 1
        }
    },
    dataLabels: {
        enabled: true
    },
    plotOptions: {
        radar: {
            size: 140,
            polygons: {
                fill: {
                    colors: ['--dx-tertiary-bg', '--dx-secondary-bg']
                }
            }
        }
    },
    title: {
        text: 'Radar with Polygon Fill'
    },
    markers: {
        size: 4,
        colors: ['#fff'],
        strokeColor: '#FF4560',
        strokeWidth: 2,
    },
    tooltip: {
        y: {
            formatter: function (val) {
                return val
            }
        }
    },
    xaxis: {
        categories: ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه'],
        labels: {
            style: {
                fontFamily: 'Vazir, sans-serif'
            }
        }
    },
    yaxis: {
        tickAmount: 7,
        labels: {
            formatter: function (val, i) {
                if (i % 2 === 0) {
                    return val
                } else {
                    return ''
                }
            }
        }
    },
    colors: ["--dx-danger"],
};

allCharts.push([{ 'id': 'polygonRadarChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });