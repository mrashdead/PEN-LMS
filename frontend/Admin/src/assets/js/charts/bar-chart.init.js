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

//basic bar Chart
var options = {
    series: [{
        data: [400, 430, 448, 470, 540, 580, 690, 1100, 1200, 1380]
    }],
    chart: {
        type: 'bar',
        height: 360
    },
    plotOptions: {
        bar: {
            borderRadius: 4,
            borderRadiusApplication: 'end',
            horizontal: true,
        }
    },
    dataLabels: {
        enabled: false
    },
    grid: {
        padding: {
            right: 0
        }
    },
    colors: ["--dx-primary"],
    xaxis: {
        categories: ['کره جنوبی', 'کانادا', 'انگلستان', 'هلند', 'ایتالیا', 'فرانسه', 'ژاپن',
            'آمریکا', 'چین', 'آلمان'
        ],
    }
};

allCharts.push([{ 'id': 'basicBarChart', 'data': options }]);

//Grouped bar Chart
var options = {
    series: [{
        data: [44, 55, 41, 64, 22, 43, 21]
    }, {
        data: [53, 32, 33, 52, 13, 44, 32]
    }],
    chart: {
        type: 'bar',
        height: 360
    },
    plotOptions: {
        bar: {
            horizontal: true,
            dataLabels: {
                position: 'top',
            },
        }
    },
    dataLabels: {
        enabled: true,
        offsetX: -6,
        style: {
            fontSize: '12px',
            colors: ['#fff']
        }
    },
    stroke: {
        show: true,
        width: 1,
        colors: ['#fff']
    },
    tooltip: {
        shared: true,
        intersect: false
    },
    colors: ["--dx-primary", "--dx-info"],
    xaxis: {
        categories: [2001, 2002, 2003, 2004, 2005, 2006, 2007],
    },
};

allCharts.push([{ 'id': 'groupedBarChart', 'data': options }]);

//Stacked bar Chart
var options = {
    series: [{
        name: 'پری دریایی',
        data: [44, 55, 41, 37, 22, 43, 21]
    }, {
        name: 'گوساله ضربه زننده',
        data: [53, 32, 33, 52, 13, 43, 32]
    }, {
        name: 'تصویر تانک',
        data: [12, 17, 11, 9, 15, 11, 20]
    }, {
        name: 'سطل مهربانی',
        data: [9, 7, 5, 8, 6, 9, 4]
    }, {
        name: 'تولد دوباره',
        data: [25, 12, 19, 32, 25, 24, 10]
    }],
    chart: {
        height: 300,
        type: "bar",
        stacked: true,
    },
    plotOptions: {
        bar: {
            horizontal: true,
            dataLabels: {
                total: {
                    enabled: true,
                    offsetX: 0,
                    style: {
                        fontSize: '13px',
                        fontWeight: 900
                    }
                }
            }
        },
    },
    stroke: {
        width: 1,
        colors: ['#fff']
    },
    title: {
        text: 'فروش کتاب‌های داستانی'
    },
    xaxis: {
        categories: [2018, 2019, 2020, 2021, 2022, 2023, 2024],
        labels: {
            formatter: function (val) {
                return val + "K"
            }
        }
    },
    yaxis: {
        title: {
            text: undefined
        },
    },
    tooltip: {
        y: {
            formatter: function (val) {
                return val + "K"
            }
        }
    },
    fill: {
        opacity: 1
    },
    legend: {
        position: 'top',
        horizontalAlign: 'left',
        offsetX: 40
    },
    grid: {
        padding: {
            right: 0,
            bottom: -10,
        },
    },
    colors: ["--dx-primary", "--dx-success", "--dx-danger", "--dx-secondary", "--dx-info"],
};

allCharts.push([{ 'id': 'stackedBarChart', 'data': options }]);

//Stacked bar 100 Chart
var options = {
    series: [{
        name: 'پری دریایی',
        data: [44, 55, 41, 37, 22, 43, 21]
    }, {
        name: 'گوساله ضربه زننده',
        data: [53, 32, 33, 52, 13, 43, 32]
    }, {
        name: 'تصویر تانک',
        data: [12, 17, 11, 9, 15, 11, 20]
    }, {
        name: 'سطل مهربانی',
        data: [9, 7, 5, 8, 6, 9, 4]
    }, {
        name: 'تولد دوباره',
        data: [25, 12, 19, 32, 25, 24, 10]
    }],
    chart: {
        height: 300,
        type: "bar",
        stacked: true,
        stackType: '100%'
    },
    plotOptions: {
        bar: {
            horizontal: true,
        },
    },
    stroke: {
        width: 1,
        colors: ['#fff']
    },
    title: {
        text: '100% Stacked Bar'
    },
    xaxis: {
        categories: [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    },
    tooltip: {
        y: {
            formatter: function (val) {
                return val + "K"
            }
        }
    },
    fill: {
        opacity: 1

    },
    legend: {
        position: 'top',
        horizontalAlign: 'left',
        offsetX: 40
    },
    grid: {
        padding: {
            right: 0,
            bottom: -10,
        },
    },
    colors: ["--dx-primary", "--dx-orange", "--dx-success", "--dx-secondary", "--dx-info"],
};

allCharts.push([{ 'id': 'stackedBar100Chart', 'data': options }]);

//Grouped Stacked Bars Chart
var options = {
    series: [
        {
            name: 'بودجه سه ماه اول',
            group: 'budget',
            data: [44000, 55000, 41000, 67000, 22000]
        },
        {
            name: 'سه ماهه اول واقعی',
            group: 'actual',
            data: [48000, 50000, 40000, 65000, 25000]
        },
        {
            name: 'بودجه سه ماه دوم',
            group: 'budget',
            data: [13000, 36000, 20000, 8000, 13000]
        },
        {
            name: 'سه ماهه دوم واقعی',
            group: 'actual',
            data: [20000, 40000, 25000, 10000, 12000]
        }
    ],
    chart: {
        height: 300,
        type: "bar",
        stacked: true,
    },
    stroke: {
        width: 1,
        colors: ['#fff']
    },
    dataLabels: {
        formatter: (val) => {
            return val / 1000 + 'K'
        }
    },
    plotOptions: {
        bar: {
            horizontal: true
        }
    },
    xaxis: {
        categories: [
            'تبلیغات آنلاین',
            'آموزش فروش',
            'تبلیغات چاپی',
            'کاتالوگ‌ها',
            'جلسات'
        ],
        labels: {
            formatter: (val) => {
                return val / 1000 + 'K'
            }
        }
    },
    fill: {
        opacity: 1,
    },
    legend: {
        position: 'top',
        horizontalAlign: 'left'
    },
    grid: {
        padding: {
            right: 0,
            bottom: -10,
        },
    },
    colors: ["--dx-primary", "--dx-success", "--dx-primary-border-subtle", "--dx-success-border-subtle",],
};

allCharts.push([{ 'id': 'groupedStackedBarChart', 'data': options }]);

//Bar with Negative Values Bars Chart
var options = {
    series: [{
        name: 'مردان',
        data: [0.4, 0.65, 0.76, 0.88, 1.5, 2.1, 2.9, 3.8, 3.9, 4.2, 4, 4.3, 4.1, 4.2, 4.5,
            3.9, 3.5, 3
        ]
    },
    {
        name: 'زنان',
        data: [-0.8, -1.05, -1.06, -1.18, -1.4, -2.2, -2.85, -3.7, -3.96, -4.22, -4.3, -4.4,
        -4.1, -4, -4.1, -3.4, -3.1, -2.8
        ]
    }],
    chart: {
        height: 300,
        type: "bar",
        stacked: true,
    },
    plotOptions: {
        bar: {
            horizontal: true,
            barHeight: '80%',
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 1,
        colors: ["#fff"]
    },

    grid: {
        xaxis: {
            lines: {
                show: false
            }
        }
    },
    yaxis: {
        min: -5,
        max: 5,
    },
    tooltip: {
        shared: false,
        x: {
            formatter: function (val) {
                return val
            }
        },
        y: {
            formatter: function (val) {
                return Math.abs(val) + "%"
            }
        }
    },
    title: {
        text: 'هرم جمعیتی موریس در سال 2011'
    },
    xaxis: {
        categories: ['85+', '80-84', '75-79', '70-74', '65-69', '60-64', '55-59', '50-54',
            '45-49', '40-44', '35-39', '30-34', '25-29', '20-24', '15-19', '10-14', '5-9',
            '0-4'
        ],
        title: {
            text: 'درصد'
        },
        labels: {
            formatter: function (val) {
                return Math.abs(Math.round(val)) + "%"
            }
        }
    },
    grid: {
        padding: {
            right: 0,
            bottom: -10,
        },
    },
    colors: ["--dx-info", "--dx-secondary"],
};

allCharts.push([{ 'id': 'negativeValueBarChart', 'data': options }]);

//Bar with Markers Chart
var options = {
    series: [
        {
            name: 'واقعی',
            data: [
                {
                    x: '2011',
                    y: 12,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 14,
                            strokeWidth: 2,
                            strokeDashArray: 2,
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2012',
                    y: 44,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 54,
                            strokeWidth: 5,
                            strokeHeight: 10,
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2013',
                    y: 54,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 52,
                            strokeWidth: 10,
                            strokeHeight: 0,
                            strokeLineCap: 'round',
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2014',
                    y: 66,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 61,
                            strokeWidth: 10,
                            strokeHeight: 0,
                            strokeLineCap: 'round',
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2015',
                    y: 81,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 66,
                            strokeWidth: 10,
                            strokeHeight: 0,
                            strokeLineCap: 'round',
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2016',
                    y: 67,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 70,
                            strokeWidth: 5,
                            strokeHeight: 10,
                            strokeColor: '#775DD0'
                        }
                    ]
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "bar",
    },
    plotOptions: {
        bar: {
            horizontal: true,
        }
    },
    dataLabels: {
        formatter: function (val, opt) {
            const goals =
                opt.w.config.series[opt.seriesIndex].data[opt.dataPointIndex]
                    .goals

            if (goals && goals.length) {
                return `${val} / ${goals[0].value}`
            }
            return val
        }
    },
    legend: {
        show: true,
        showForSingleSeries: true,
        customLegendItems: ['واقعی', 'مورد انتظار'],
        markers: {
            fillColors: ['--dx-primary', '--dx-secondary']
        }
    },
    grid: {
        padding: {
            right: 0,
            bottom: -10,
        },
    },
    colors: ["--dx-primary", "--dx-secondary"],
};

allCharts.push([{ 'id': 'markersBarChart', 'data': options }]);

//Reversed Bar Chart
var options = {
    series: [{
        data: [400, 430, 448, 470, 540, 580, 690]
    }],
    chart: {
        height: 300,
        type: "bar",
    },
    annotations: {
        xaxis: [{
            x: 500,
            borderColor: '--dx-border-color',
            label: {
                borderColor: '--dx-border-color',
                style: {
                    color: '--dx-white',
                    background: '--dx-success',
                },
                text: 'X حاشیه نویسی',
            }
        }],
        yaxis: [{
            y: 'جولای',
            y2: 'سپتامبر',
            label: {
                borderColor: '--dx-border-color',
                style: {
                    color: '--dx-body-color',
                    background: '--dx-secondary-bg',
                },
                text: 'Y حاشیه نویسی'
            }
        }]
    },
    plotOptions: {
        bar: {
            horizontal: true,
        }
    },
    dataLabels: {
        enabled: true
    },
    xaxis: {
        categories: ['ژوئن', 'جولای', 'آگوست', 'سپتامبر', 'اکتبر', 'نوامبر', 'دسامبر'],
    },
    grid: {
        xaxis: {
            lines: {
                show: true
            }
        }
    },
    yaxis: {
        reversed: true,
        axisTicks: {
            show: true
        }
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'reversedBarChart', 'data': options }]);

//Patterned Bar Chart
var options = {
    series: [{
        name: 'پری دریایی',
        data: [44, 55, 41, 37, 22, 43, 21]
    }, {
        name: 'گوساله ضربه زننده',
        data: [53, 32, 33, 52, 13, 43, 32]
    }, {
        name: 'تصویر تانک',
        data: [12, 17, 11, 9, 15, 11, 20]
    }, {
        name: 'سطل مهربانی',
        data: [9, 7, 5, 8, 6, 9, 4]
    }],
    chart: {
        height: 300,
        type: "bar",
        stacked: true,
        dropShadow: {
            enabled: true,
            blur: 1,
            opacity: 0.25
        }
    },
    plotOptions: {
        bar: {
            horizontal: true,
            barHeight: '60%',
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 2,
    },
    title: {
        text: 'مقایسه کتاب‌های پرفروش'
    },
    xaxis: {
        categories: [2008, 2009, 2010, 2011, 2012, 2013, 2014],
    },
    yaxis: {
        title: {
            text: undefined
        },
    },
    tooltip: {
        shared: false,
        y: {
            formatter: function (val) {
                return val + "K"
            }
        }
    },
    fill: {
        type: 'pattern',
        opacity: 1,
        pattern: {
            style: ['circles', 'slantedLines', 'verticalLines', 'horizontalLines'], // string or array of strings

        }
    },
    states: {
        hover: {
            filter: 'none'
        }
    },
    legend: {
        position: 'right',
        offsetY: 40
    },
    colors: ["--dx-primary", "--dx-success", "--dx-danger", "--dx-secondary"],
};

allCharts.push([{ 'id': 'patternedBarChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });