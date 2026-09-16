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

//Simple Pie Chart
var options = {
    series: [44, 55, 13, 43, 22],
    chart: {
        height: 300,
        type: "pie",
    },
    labels: ['Team A', 'Team B', 'Team C', 'Team D', 'Team E'],
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: '100%'
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary", "--dx-danger"],
};

allCharts.push([{ 'id': 'simplePieChart', 'data': options }]);

//Simple Donut Chart
var options = {
    series: [44, 55, 41, 17, 15],
    chart: {
        height: 300,
        type: "donut",
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: '100%'
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary", "--dx-danger"],
};

allCharts.push([{ 'id': 'simpleDonutChart', 'data': options }]);

//Update Donut
var updateDonutChartOptions = {
    series: [44, 55, 13, 33],
    chart: {
        height: 250,
        type: 'donut',
    },
    dataLabels: {
        enabled: false
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: '100%'
            },
            legend: {
                show: true
            }
        }
    }],
    legend: {
        position: 'right',
        offsetY: 0,
        height: 230,
    },
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-danger"],
};

allCharts.push([{ 'id': 'updateDonutChart', 'data': updateDonutChartOptions }]);

//Monochrome Pie Chart
var options = {
    series: [25, 15, 44, 55, 41, 17],
    chart: {
        height: 340,
        type: "pie",
    },
    labels: ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"],
    theme: {
        monochrome: {
            enabled: true
        }
    },
    plotOptions: {
        pie: {
            dataLabels: {
                offset: -5
            }
        }
    },
    title: {
        text: "Monochrome Pie"
    },
    dataLabels: {
        formatter(val, opts) {
            const name = opts.w.globals.labels[opts.seriesIndex]
            return [name, val.toFixed(1) + '%']
        }
    },
    legend: {
        show: false
    },
};

allCharts.push([{ 'id': 'monochromePieChart', 'data': options }]);

//Gradient Donut Chart
var options = {
    series: [44, 55, 41, 17, 15],
    chart: {
        height: 300,
        type: "donut",
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
    legend: {
        formatter: function (val, opts) {
            return val + " - " + opts.w.globals.series[opts.seriesIndex]
        }
    },
    title: {
        text: 'Gradient Donut with custom Start-angle'
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: '100%'
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-danger", "--dx-secondary"],
};

allCharts.push([{ 'id': 'gradientDonutChart', 'data': options }]);

//Semi Donut Chart
var options = {
    series: [44, 55, 41, 17, 15],
    chart: {
        height: 300,
        type: "donut",
    },
    plotOptions: {
        pie: {
            startAngle: -90,
            endAngle: 90,
            offsetY: 10
        }
    },
    grid: {
        padding: {
            bottom: -80
        }
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: '100%'
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary", "--dx-danger"],
};

allCharts.push([{ 'id': 'semiDonutChart', 'data': options }]);

//Donut with Pattern Chart
var options = {
    series: [44, 55, 41, 17, 15],
    chart: {
        height: 300,
        type: "donut",
        dropShadow: {
            enabled: true,
            color: '#111',
            top: -1,
            left: 3,
            blur: 3,
            opacity: 0.2
        }
    },
    stroke: {
        width: 0,
    },
    plotOptions: {
        pie: {
            donut: {
                labels: {
                    show: true,
                    total: {
                        showAlways: true,
                        show: true
                    }
                }
            }
        }
    },
    labels: ["کمدی", "اکشن", "علمی - تخیلی", "درام", "ترسناک"],
    dataLabels: {
        dropShadow: {
            blur: 3,
            opacity: 0.8
        }
    },
    fill: {
        type: 'pattern',
        opacity: 1,
        pattern: {
            enabled: true,
            style: ['verticalLines', 'squares', 'horizontalLines', 'circles', 'slantedLines'],
        },
    },
    states: {
        hover: {
            filter: 'none'
        }
    },
    theme: {
        palette: 'palette2'
    },
    title: {
        text: "Favourite Movie Type"
    },
    responsive: [{
        breakpoint: 480,
        options: {
            chart: {
                width: '100%'
            },
            legend: {
                position: 'bottom'
            }
        }
    }],
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary", "--dx-danger"],
};

allCharts.push([{ 'id': 'patternDonutChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });

const flattened = allCharts.flat();
const updateDonutChart = flattened.find(item => item.id === 'updateDonutChart');

document.querySelector("#randomize").addEventListener("click", function () {
    updateDonutChart.chart.updateSeries(randomize())
})

document.querySelector("#add").addEventListener("click", function () {
    updateDonutChart.chart.updateSeries(appendData())
})

document.querySelector("#remove").addEventListener("click", function () {
    updateDonutChart.chart.updateSeries(removeData())
})

document.querySelector("#reset").addEventListener("click", function () {
    updateDonutChart.chart.updateSeries(reset())
})

function appendData() {
    var arr = updateDonutChart.chart.w.globals.series.slice()
    arr.push(Math.floor(Math.random() * (100 - 1 + 1)) + 1)
    return arr;
}

function removeData() {
    var arr = updateDonutChart.chart.w.globals.series.slice()
    arr.pop()
    return arr;
}

function randomize() {
    return updateDonutChart.chart.w.globals.series.map(function () {
        return Math.floor(Math.random() * (100 - 1 + 1)) + 1
    })
}

function reset() {
    return updateDonutChartOptions.series
}