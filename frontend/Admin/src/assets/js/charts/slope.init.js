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
    series: [
        {
            name: 'آبی',
            data: [
                {
                    x: 'فروردین',
                    y: 43,
                },
                {
                    x: 'اردیبهشت',
                    y: 58,
                },
            ],
        },
        {
            name: 'سبز',
            data: [
                {
                    x: 'فروردین',
                    y: 33,
                },
                {
                    x: 'اردیبهشت',
                    y: 38,
                },
            ],
        },
        {
            name: 'زرد',
            data: [
                {
                    x: 'فروردین',
                    y: 55,
                },
                {
                    x: 'اردیبهشت',
                    y: 21,
                },
            ],
        },
    ],
    chart: {
        height: 300,
        type: "line",
    },
    plotOptions: {
        line: {
            isSlopeChart: true,
        },
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-success", "--dx-warning"],
};

allCharts.push([{ 'id': 'slopeBasicChart', 'data': options }]);

//Multi group Chart
var options = {
    series: [
        {
            name: 'آبی',
            data: [
                {
                    x: 'دسته‌بندی 1',
                    y: 503,
                },
                {
                    x: 'دسته‌بندی 2',
                    y: 580,
                },
                {
                    x: 'دسته‌بندی 3',
                    y: 135,
                },
            ],
        },
        {
            name: 'سبز',
            data: [
                {
                    x: 'دسته‌بندی 1',
                    y: 733,
                },
                {
                    x: 'دسته‌بندی 2',
                    y: 385,
                },
                {
                    x: 'دسته‌بندی 3',
                    y: 715,
                },
            ],
        },
        {
            name: 'نارنجی',
            data: [
                {
                    x: 'دسته‌بندی 1',
                    y: 255,
                },
                {
                    x: 'دسته‌بندی 2',
                    y: 211,
                },
                {
                    x: 'دسته‌بندی 3',
                    y: 441,
                },
            ],
        },
        {
            name: 'قرمز',
            data: [
                {
                    x: 'دسته‌بندی 1',
                    y: 428,
                },
                {
                    x: 'دسته‌بندی 2',
                    y: 749,
                },
                {
                    x: 'دسته‌بندی 3',
                    y: 559,
                },
            ],
        },
    ],
    chart: {
        height: 300,
        type: "line",
    },
    plotOptions: {
        line: {
            isSlopeChart: true,
        },
    },
    tooltip: {
        followCursor: true,
        intersect: false,
        shared: true,
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
    yaxis: {
        show: true,
        labels: {
            show: true,
        },
    },
    xaxis: {
        position: 'bottom',
    },
    legend: {
        show: true,
        position: 'top',
        horizontalAlign: 'left',
    },
    stroke: {
        width: [2, 3, 4, 2],
        dashArray: [0, 0, 5, 2],
        curve: 'smooth',
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-success", "--dx-orange", "--dx-danger"],
};

allCharts.push([{ 'id': 'slopeMultiGroupChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });