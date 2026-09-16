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
            type: 'boxPlot',
            data: [
                {
                    x: 'Jan 2015',
                    y: [54, 66, 69, 75, 88]
                },
                {
                    x: 'Jan 2016',
                    y: [43, 65, 69, 76, 81]
                },
                {
                    x: 'Jan 2017',
                    y: [31, 39, 45, 51, 59]
                },
                {
                    x: 'Jan 2018',
                    y: [39, 46, 55, 65, 71]
                },
                {
                    x: 'Jan 2019',
                    y: [29, 31, 35, 39, 44]
                },
                {
                    x: 'Jan 2020',
                    y: [41, 49, 58, 61, 67]
                },
                {
                    x: 'Jan 2021',
                    y: [54, 59, 66, 71, 88]
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "boxPlot",
    },
    title: {
        text: 'Basic BoxPlot Chart',
        align: 'left'
    },
    plotOptions: {
        boxPlot: {
            colors: {
                upper: '--dx-primary',
                lower: '--dx-success'
            }
        }
    },
};

allCharts.push([{ 'id': 'boxWhiskerBasicChart', 'data': options }]);

//Boxplot-Scatter Chart
var options = {
    series: [
        {
            name: 'جعبه',
            type: 'boxPlot',
            data: [
                {
                    x: new Date('2017-01-01').getTime(),
                    y: [54, 66, 69, 75, 88]
                },
                {
                    x: new Date('2018-01-01').getTime(),
                    y: [43, 65, 69, 76, 81]
                },
                {
                    x: new Date('2019-01-01').getTime(),
                    y: [31, 39, 45, 51, 59]
                },
                {
                    x: new Date('2020-01-01').getTime(),
                    y: [39, 46, 55, 65, 71]
                },
                {
                    x: new Date('2021-01-01').getTime(),
                    y: [29, 31, 35, 39, 44]
                }
            ]
        },
        {
            name: 'داده‌های پرت',
            type: 'scatter',
            data: [
                {
                    x: new Date('2017-01-01').getTime(),
                    y: 32
                },
                {
                    x: new Date('2018-01-01').getTime(),
                    y: 25
                },
                {
                    x: new Date('2019-01-01').getTime(),
                    y: 64
                },
                {
                    x: new Date('2020-01-01').getTime(),
                    y: 27
                },
                {
                    x: new Date('2020-01-01').getTime(),
                    y: 78
                },
                {
                    x: new Date('2021-01-01').getTime(),
                    y: 15
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "boxPlot",
    },
    colors: ["--dx-primary", "--dx-danger"],
    title: {
        text: 'BoxPlot - Scatter Chart',
        align: 'left'
    },
    xaxis: {
        type: 'datetime',
        tooltip: {
            formatter: function (val) {
                return new Date(val).getFullYear()
            }
        }
    },
    plotOptions: {
        boxPlot: {
            colors: {
                upper: '--dx-primary',
                lower: '--dx-warning'
            }
        }
    },
    tooltip: {
        shared: false,
        intersect: true
    }
};

allCharts.push([{ 'id': 'boxplotScatterChart', 'data': options }]);

//Horizontal BoxPlot Chart
var options = {
    series: [
        {
            data: [
                {
                    x: 'A دسته‌بندی',
                    y: [54, 66, 69, 75, 88]
                },
                {
                    x: 'B دسته‌بندی',
                    y: [43, 65, 69, 76, 81]
                },
                {
                    x: 'C دسته‌بندی',
                    y: [31, 39, 45, 51, 59]
                },
                {
                    x: 'D دسته‌بندی',
                    y: [39, 46, 55, 65, 71]
                },
                {
                    x: 'E دسته‌بندی',
                    y: [29, 31, 35, 39, 44]
                },
                {
                    x: 'F دسته‌بندی',
                    y: [41, 49, 58, 61, 67]
                },
                {
                    x: 'G دسته‌بندی',
                    y: [54, 59, 66, 71, 88]
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "boxPlot",
    },
    title: {
        text: 'Horizontal BoxPlot Chart',
        align: 'left'
    },
    plotOptions: {
        bar: {
            horizontal: true,
            barHeight: '50%'
        },
        boxPlot: {
            colors: {
                upper: '--dx-primary',
                lower: '--dx-info'
            }
        }
    },
};

allCharts.push([{ 'id': 'boxplotHorizontalChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });