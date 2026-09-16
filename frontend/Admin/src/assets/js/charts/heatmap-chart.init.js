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
function generateData(count, yrange) {
    var i = 0;
    var series = [];
    while (i < count) {
        var x = (i + 1).toString();
        var y = Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

        series.push({
            x: x,
            y: y
        });
        i++;
    }
    return series;
}
var options = {
    series: [{
        name: 'Metric1',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric2',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric3',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric4',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric5',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric6',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric7',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric8',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric9',
        data: generateData(18, {
            min: 0,
            max: 90
        })
    }
    ],
    chart: {
        height: 300,
        type: "heatmap",
    },
    dataLabels: {
        enabled: false
    },
    title: {
        text: 'HeatMap Chart (Single color)'
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

allCharts.push([{ 'id': 'basicHatmapChart', 'data': options }]);

//Multiple Colors Chart
var options = {
    series: [{
        name: 'PE1',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE2',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE3',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE4',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE5',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE6',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE7',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE8',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE9',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE10',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE11',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE12',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE13',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE14',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'PE15',
        data: generateData(8, {
            min: 0,
            max: 90
        })
    }
    ],
    chart: {
        height: 300,
        type: "heatmap",
    },
    dataLabels: {
        enabled: false
    },
    xaxis: {
        type: 'category',
        categories: ['10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '01:00', '01:30']
    },
    title: {
        text: 'HeatMap Chart (Different color shades for each series)'
    },
    grid: {
        padding: {
            right: 20
        }
    },
    colors: ["--dx-primary", "--dx-success", "--dx-pink", "--dx-info", "--dx-indigo", "--dx-secondary", "--dx-warning"],
};

allCharts.push([{ 'id': 'multiColorHatmapChart', 'data': options }]);

//Multiple Colors Flipped
var options = {
    series: [{
        name: 'Jan',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    },
    {
        name: 'Feb',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    },
    {
        name: 'Mar',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    },
    {
        name: 'Apr',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    },
    {
        name: 'May',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    },
    {
        name: 'Jun',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    },
    {
        name: 'Jul',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    },
    {
        name: 'Aug',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    },
    {
        name: 'Sep',
        data: generateData(20, {
            min: -30,
            max: 55
        })
    }
    ],
    chart: {
        height: 300,
        type: "heatmap",
    },
    dataLabels: {
        enabled: false
    },
    plotOptions: {
        heatmap: {
            colorScale: {
                inverse: true
            }
        }
    },
    xaxis: {
        type: 'category',
        categories: ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16', 'P17', 'P18', 'P19', 'P20']
    },
    title: {
        text: 'Color Scales flipped Vertically'
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-success", "--dx-pink", "--dx-info", "--dx-indigo", "--dx-secondary", "--dx-warning"],
};

allCharts.push([{ 'id': 'multiColorFlippedHatmapChart', 'data': options }]);

//Rounded
var options = {
    series: [{
        name: 'Metric1',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric2',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric3',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric4',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric5',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric6',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric7',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric8',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    },
    {
        name: 'Metric8',
        data: generateData(20, {
            min: 0,
            max: 90
        })
    }
    ],
    chart: {
        height: 300,
        type: "heatmap",
    },
    stroke: {
        width: 0
    },
    plotOptions: {
        heatmap: {
            radius: 30,
            enableShades: false,
            colorScale: {
                ranges: [{
                    from: 0,
                    to: 50,
                    color: '--dx-primary'
                },
                {
                    from: 51,
                    to: 100,
                    color: '--dx-success'
                },
                ],
            },
        }
    },
    dataLabels: {
        enabled: true,
        style: {
            colors: ['#fff']
        }
    },
    xaxis: {
        type: 'category',
    },
    title: {
        text: 'Rounded (Range without Shades)'
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    }
};

allCharts.push([{ 'id': 'roundedHatmapChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });