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

//ads revenue Charts
var options = {
    series: [{
        name: 'درآمد کل',
        data: [31, 77, 44, 31, 63, 94, 109]
    }],
    labels: ['مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
    chart: {
        defaultLocale: "en",
        height: 140,
        type: "line",
        zoom: {
            enabled: false
        },
        toolbar: {
            show: false,
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 3,
        curve: 'smooth',
        dashArray: [10]
    },
    legend: {
        tooltipHoverFormatter: function (val, opts) {
            return val + ' - <strong>' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + '</strong>'
        }
    },
    markers: {
        size: 0,
        hover: {
            sizeOffset: 5
        }
    },
    grid: {
        borderColor: ["--dx-border-color"],
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
            left: 7
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
    yaxis: {
        show: false,
    },
    colors: ["--dx-danger"],

};

allCharts.push([{ 'id': 'adsRevenueChart', 'data': options }]);

//Sales Revenue Charts
var options = {
    series: [{
        name: 'درآمد کل',
        data: [31, 40, 28, 51, 42, 119, 100]
    }],
    labels: ['مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
    chart: {
        defaultLocale: "en",
        height: 140,
        type: "line",
        zoom: {
            enabled: false
        },
        toolbar: {
            show: false,
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 3,
        curve: 'smooth',
        dashArray: [10]
    },
    legend: {
        tooltipHoverFormatter: function (val, opts) {
            return val + ' - <strong>' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + '</strong>';
        }
    },
    markers: {
        size: 0,
        hover: {
            sizeOffset: 5
        }
    },
    grid: {
        borderColor: ['--dx-border-color'],
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
            left: 7
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
    yaxis: {
        show: false,
    },
    colors: ["--dx-primary"],

};

allCharts.push([{ 'id': 'salesRevenueChart', 'data': options }]);

//ads revenue Charts
var options = {
    series: [{
        name: 'درآمد کل',
        data: [31, 77, 44, 31, 63, 94, 109]
    }],
    labels: ['مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد', 'اردیبهشت', 'فروردین'],
    chart: {
        defaultLocale: "en",
        height: 140,
        type: "line",
        zoom: {
            enabled: false
        },
        toolbar: {
            show: false,
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 3,
        curve: 'smooth',
        dashArray: [10]
    },
    legend: {
        tooltipHoverFormatter: function (val, opts) {
            return val + ' - <strong>' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + '</strong>'
        }
    },
    markers: {
        size: 0,
        hover: {
            sizeOffset: 5
        }
    },
    grid: {
        borderColor: ["--dx-border-color"],
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
            left: 7
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
    yaxis: {
        show: false,
    },
    colors: ["--dx-danger"],

};

allCharts.push([{ 'id': 'adsRevenueChart2', 'data': options }]);

//Total Sales Charts
var options = {
    series: [{
        name: 'تورم',
        data: [2.3, 3.1, 4.0, 10.1, 4.0, 3.6, 3.2, 2.3, 1.4, 1.3, 1.9, 2.8]
    }],
    yaxis: {
        show: false,
    },
    chart: {
        height: 268,
        type: "bar",
        toolbar: { show: false },
    },
    plotOptions: {
        bar: {
            columnWidth: '60%',
            borderRadius: 5,
            dataLabels: { position: 'top' },
        }
    },
    dataLabels: { enabled: false },
    xaxis: {
        categories: ["اسفند", "بهمن", "دی", "آذر", "آبان", "مهر", "شهریور", "مرداد", "تیر", "خرداد", "اردیبهشت", "فروردین"],
        axisBorder: { show: false },
        axisTicks: { show: false },
    },
    yaxis: {
        axisBorder: { show: false },
        axisTicks: { show: false },
        labels: {
            show: true,
            formatter: function (val) {
                return val + "%";
            }
        }
    },
    grid: {
        xaxis: { lines: { show: false } },
        yaxis: { lines: { show: false } },
        padding: { top: -10, right: 1, bottom: 0, left: 0 },
    },
    grid: {
        padding: {
            right: 0,
            top: 0,
            bottom: -10,
            left: 0
        }
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'totalSalesChart', 'data': options }]);

//Total View Performance Charts
var options = {
    series: [48, 98],
    chart: {
        height: 190,
        type: "donut",
    },
    dataLabels: {
        enabled: false
    },
    plotOptions: {
        pie: {
            startAngle: -90,
            endAngle: 90,
            offsetY: 20,
        },
    },
    legend: {
        show: false
    },
    grid: {
        padding: {
            top: -20,
            bottom: -80
        }
    },
    colors: ["--dx-primary", "--dx-pink"],
};

allCharts.push([{ 'id': 'totalViewPerformanceChart', 'data': options }]);

updateAllCharts();