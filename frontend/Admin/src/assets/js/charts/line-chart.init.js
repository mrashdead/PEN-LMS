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

//Basic Charts
var options = {
    series: [
        {
            name: "نام سری",
            data: [10, 41, 35, 51, 49, 62, 69, 91, 148],
        }
    ],
    chart: {
        defaultLocale: "en",
        height: 300,
        type: "line",
        zoom: {
            enabled: true
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        curve: 'straight'
    },
    grid: {
        row: {
            colors: ['#f3f3f3', 'transparent'], // takes an array which will be repeated on columns
            opacity: 0.5
        },
    },
    xaxis: {
        title: {
            text: "Xaxis"
        },
        categories: [
            "ژانویه",
            "فوریه",
            "مارس",
            "آوریل",
            "مه",
            "ژوئن",
            "جولای",
            "آگوست",
            "سپتامبر",
            "اکتبر",
            "نوامبر",
            "دسامبر"
        ],
    },
    tooltip: {
        x: {
            show: true
        },
        y: {
            formatter: (val) => {
                return this.formatCurrency(val);
            }
        }
    },
    grid: {
        padding: {
            top: 0,
            right: 5,
            bottom: 0,
        },
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'basicLineChart', 'data': options }]);

//Line with Data Labels Charts
var options = {
    series: [
        {
            name: "بالا - 2013",
            data: [28, 29, 33, 36, 32, 32, 33]
        },
        {
            name: "پایین - 2013",
            data: [12, 11, 14, 18, 17, 13, 13]
        }
    ],
    chart: {
        defaultLocale: "en",
        height: 300,
        type: "line",
        dropShadow: {
            enabled: true,
            color: '#000',
            top: 18,
            left: 7,
            blur: 10,
            opacity: 0.2
        },
        toolbar: {
            show: false
        }
    },
    dataLabels: {
        enabled: true,
    },
    stroke: {
        curve: 'smooth'
    },
    grid: {
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
        },
    },
    legend: {
        position: 'top',
        horizontalAlign: 'right',
        floating: true,
        offsetY: -25,
        offsetX: -5
    },
    xaxis: {
        title: {
            text: "ماه"
        },
        categories: ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن", "جولای"]
    },
    yaxis: {
        title: {
            text: 'دما'
        },
        min: 5,
        max: 40
    },
    colors: ["--dx-primary", "--dx-border-color"],
};

allCharts.push([{ 'id': 'labelLineChart', 'data': options }]);

//Zoomable Timeseries Charts
var options = {
    series: [
        {
            name: "XYZ موتورز",
            data: [{
                x: new Date('2024-06-12').getTime(),
                y: 140
            }, {
                x: new Date('2024-06-13').getTime(),
                y: 147
            }, {
                x: new Date('2024-06-14').getTime(),
                y: 150
            }, {
                x: new Date('2024-06-15').getTime(),
                y: 154
            }, {
                x: new Date('2024-06-16').getTime(),
                y: 160
            }, {
                x: new Date('2024-06-17').getTime(),
                y: 165
            }, {
                x: new Date('2024-06-18').getTime(),
                y: 162
            }, {
                x: new Date('2024-06-20').getTime(),
                y: 159
            }, {
                x: new Date('2024-06-21').getTime(),
                y: 164
            }, {
                x: new Date('2024-06-22').getTime(),
                y: 160
            }, {
                x: new Date('2024-06-23').getTime(),
                y: 165
            }, {
                x: new Date('2024-06-24').getTime(),
                y: 169
            }, {
                x: new Date('2024-06-25').getTime(),
                y: 172
            }, {
                x: new Date('2024-06-26').getTime(),
                y: 177
            }, {
                x: new Date('2024-06-27').getTime(),
                y: 173
            }, {
                x: new Date('2024-06-28').getTime(),
                y: 169
            }, {
                x: new Date('2024-06-29').getTime(),
                y: 163
            }, {
                x: new Date('2024-06-30').getTime(),
                y: 158
            }, {
                x: new Date('2024-07-01').getTime(),
                y: 153
            }, {
                x: new Date('2024-07-02').getTime(),
                y: 149
            }, {
                x: new Date('2024-07-03').getTime(),
                y: 144
            }, {
                x: new Date('2024-07-05').getTime(),
                y: 150
            }, {
                x: new Date('2024-07-06').getTime(),
                y: 155
            }, {
                x: new Date('2024-07-07').getTime(),
                y: 159
            }, {
                x: new Date('2024-07-08').getTime(),
                y: 163
            }, {
                x: new Date('2024-07-09').getTime(),
                y: 156
            }, {
                x: new Date('2024-07-11').getTime(),
                y: 151
            }, {
                x: new Date('2024-07-12').getTime(),
                y: 157
            }, {
                x: new Date('2024-07-13').getTime(),
                y: 161
            }, {
                x: new Date('2024-07-14').getTime(),
                y: 150
            }, {
                x: new Date('2024-07-15').getTime(),
                y: 154
            }, {
                x: new Date('2024-07-16').getTime(),
                y: 160
            }, {
                x: new Date('2024-07-17').getTime(),
                y: 165
            }, {
                x: new Date('2024-07-18').getTime(),
                y: 162
            }, {
                x: new Date('2024-07-20').getTime(),
                y: 159
            }, {
                x: new Date('2024-07-21').getTime(),
                y: 164
            }, {
                x: new Date('2024-07-22').getTime(),
                y: 160
            }, {
                x: new Date('2024-07-23').getTime(),
                y: 165
            }, {
                x: new Date('2024-07-24').getTime(),
                y: 169
            }, {
                x: new Date('2024-07-25').getTime(),
                y: 172
            }, {
                x: new Date('2024-07-26').getTime(),
                y: 177
            }, {
                x: new Date('2024-07-27').getTime(),
                y: 173
            }, {
                x: new Date('2024-07-28').getTime(),
                y: 169
            }, {
                x: new Date('2024-07-29').getTime(),
                y: 163
            }, {
                x: new Date('2024-07-30').getTime(),
                y: 162
            }, {
                x: new Date('2024-08-01').getTime(),
                y: 158
            }, {
                x: new Date('2024-08-02').getTime(),
                y: 152
            }, {
                x: new Date('2024-08-03').getTime(),
                y: 147
            }, {
                x: new Date('2024-08-05').getTime(),
                y: 142
            }, {
                x: new Date('2024-08-06').getTime(),
                y: 147
            }, {
                x: new Date('2024-08-07').getTime(),
                y: 151
            }, {
                x: new Date('2024-08-08').getTime(),
                y: 155
            }, {
                x: new Date('2024-08-09').getTime(),
                y: 159
            }, {
                x: new Date('2024-08-11').getTime(),
                y: 162
            }, {
                x: new Date('2024-08-12').getTime(),
                y: 157
            }, {
                x: new Date('2024-08-13').getTime(),
                y: 161
            }, {
                x: new Date('2024-08-14').getTime(),
                y: 166
            }, {
                x: new Date('2024-08-15').getTime(),
                y: 169
            }, {
                x: new Date('2024-08-16').getTime(),
                y: 172
            }, {
                x: new Date('2024-08-17').getTime(),
                y: 177
            }, {
                x: new Date('2024-08-18').getTime(),
                y: 181
            }, {
                x: new Date('2024-08-20').getTime(),
                y: 178
            }, {
                x: new Date('2024-08-21').getTime(),
                y: 173
            }, {
                x: new Date('2024-08-22').getTime(),
                y: 169
            }, {
                x: new Date('2024-08-23').getTime(),
                y: 163
            }, {
                x: new Date('2024-08-24').getTime(),
                y: 159
            }, {
                x: new Date('2024-08-25').getTime(),
                y: 164
            }, {
                x: new Date('2024-08-26').getTime(),
                y: 168
            }, {
                x: new Date('2024-08-27').getTime(),
                y: 172
            }, {
                x: new Date('2024-08-28').getTime(),
                y: 169
            }, {
                x: new Date('2024-08-29').getTime(),
                y: 163
            }, {
                x: new Date('2024-08-30').getTime(),
                y: 162
            }, {
                x: new Date('2024-09-01').getTime(),
                y: 158
            }, {
                x: new Date('2024-09-02').getTime(),
                y: 152
            }, {
                x: new Date('2024-09-03').getTime(),
                y: 147
            }, {
                x: new Date('2024-09-05').getTime(),
                y: 142
            }, {
                x: new Date('2024-09-06').getTime(),
                y: 147
            }, {
                x: new Date('2024-09-07').getTime(),
                y: 151
            }, {
                x: new Date('2024-09-08').getTime(),
                y: 155
            }, {
                x: new Date('2024-09-09').getTime(),
                y: 159
            }, {
                x: new Date('2024-09-11').getTime(),
                y: 162
            }, {
                x: new Date('2024-09-12').getTime(),
                y: 157
            }, {
                x: new Date('2024-09-13').getTime(),
                y: 161
            }, {
                x: new Date('2024-09-14').getTime(),
                y: 166
            }, {
                x: new Date('2024-09-15').getTime(),
                y: 169
            }, {
                x: new Date('2024-09-16').getTime(),
                y: 172
            }, {
                x: new Date('2024-09-17').getTime(),
                y: 177
            }, {
                x: new Date('2024-09-18').getTime(),
                y: 181
            }, {
                x: new Date('2024-09-20').getTime(),
                y: 178
            }, {
                x: new Date('2024-09-21').getTime(),
                y: 173
            }],
        }
    ],
    chart: {
        defaultLocale: "en",
        height: 300,
        type: "area",
        stacked: false,
        zoom: {
            type: 'x',
            enabled: true,
            autoScaleYaxis: true
        },
        toolbar: {
            autoSelected: 'zoom'
        }
    },
    dataLabels: {
        enabled: false
    },
    markers: {
        size: 0,
    },
    title: {
        text: 'حرکت قیمت سهام',
        align: 'left'
    },
    grid: {
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
        },
    },
    fill: {
        type: 'gradient',
        gradient: {
            shadeIntensity: 1,
            inverseColors: false,
            opacityFrom: 0.5,
            opacityTo: 0,
            stops: [0, 90, 100]
        },
    },
    yaxis: {
        labels: {
            formatter: function (val) {
                return (val / 1000000).toFixed(0);
            },
        },
        title: {
            text: 'قیمت'
        },
    },
    xaxis: {
        type: 'datetime',
    },
    tooltip: {
        shared: false,
        y: {
            formatter: function (val) {
                return (val / 1000000).toFixed(0)
            }
        }
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'zoomableLineChart', 'data': options }]);

//stepline Charts
var options = {
    series: [
        {
            data: [34, 44, 54, 21, 12, 43, 33, 23, 66, 66, 58]
        }
    ],
    chart: {
        defaultLocale: "en",
        height: 300,
        type: "line",
        zoom: {
            enabled: true
        },
    },
    stroke: {
        curve: 'stepline',
    },
    dataLabels: {
        enabled: false
    },
    title: {
        text: 'Stepline Chart',
        align: 'left'
    },
    markers: {
        hover: {
            sizeOffset: 4
        }
    },
    grid: {
        padding: {
            top: 0,
            right: 5,
            bottom: 0,
        },
    },
    colors: ["--dx-success"],
};

allCharts.push([{ 'id': 'steplineLineChart', 'data': options }]);

//Gradient Charts
var options = {
    series: [
        {
            name: 'فروش',
            data: [4, 3, 10, 9, 29, 19, 22, 9, 12, 7, 19, 5, 13, 9, 17, 2, 7, 5]
        }
    ],
    chart: {
        height: 300,
        type: "line",
        zoom: {
            enabled: true
        },
    },
    forecastDataPoints: {
        count: 7
    },
    stroke: {
        width: 5,
        curve: 'smooth'
    },
    xaxis: {
        type: 'datetime',
        categories: ['1/11/2000', '2/11/2000', '3/11/2000', '4/11/2000', '5/11/2000', '6/11/2000', '7/11/2000', '8/11/2000', '9/11/2000', '10/11/2000', '11/11/2000', '12/11/2000', '1/11/2001', '2/11/2001', '3/11/2001', '4/11/2001', '5/11/2001', '6/11/2001'],
        tickAmount: 10,
        labels: {
            formatter: function (value, timestamp, opts) {
                return opts.dateFormatter(new Date(timestamp), 'dd MMM')
            }
        }
    },
    title: {
        text: 'پیش‌بینی',
        align: 'left',
        style: {
            fontSize: "16px",
            color: '#666'
        }
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'dark',
            gradientToColors: ['--dx-orange'],
            shadeIntensity: 1,
            type: 'horizontal',
            opacityFrom: 1,
            opacityTo: 1,
            stops: [0, 100, 100, 100]
        },
    },
    yaxis: {
        min: -10,
        max: 40
    },
    grid: {
        padding: {
            top: 0,
            right: 5,
            bottom: 0,
        },
    },
    colors: ["--dx-warning"],
};

allCharts.push([{ 'id': 'gradientLineChart', 'data': options }]);

//Dashed Charts
var options = {
    series: [{
        name: "مدت زمان جلسه",
        data: [45, 52, 38, 24, 33, 26, 21, 20, 6, 8, 15, 10]
    },
    {
        name: "بازدیدهای صفحه",
        data: [35, 41, 62, 42, 13, 18, 29, 37, 36, 51, 32, 35]
    },
    {
        name: 'کل بازدیدها',
        data: [87, 57, 74, 99, 75, 38, 62, 47, 82, 56, 45, 47]
    }
    ],
    chart: {
        defaultLocale: "en",
        height: 300,
        type: "line",
        zoom: {
            enabled: false
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: [5, 7, 5],
        curve: 'straight',
        dashArray: [0, 8, 5]
    },
    title: {
        text: 'آمار صفحه',
        align: 'left'
    },
    legend: {
        tooltipHoverFormatter: function (val, opts) {
            return val + ' - <strong>' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + '</strong>'
        }
    },
    markers: {
        size: 0,
        hover: {
            sizeOffset: 6
        }
    },
    grid: {
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
        },
    },
    tooltip: {
        y: [
            {
                title: {
                    formatter: function (val) {
                        return " (دقیقه)" + val 
                    }
                }
            },
            {
                title: {
                    formatter: function (val) {
                        return " در هر جلسه" + val 
                    }
                }
            },
            {
                title: {
                    formatter: function (val) {
                        return val;
                    }
                }
            }
        ]
    },
    colors: ["--dx-primary", "--dx-success", "--dx-danger"],
};

allCharts.push([{ 'id': 'dashedLineChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });