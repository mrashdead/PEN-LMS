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

//basic column Chart
var options = {
    series: [{
        name: 'سود خالص',
        data: [44, 55, 57, 56, 61, 58, 63, 60, 66]
    }, {
        name: 'درآمد',
        data: [76, 85, 101, 98, 87, 105, 91, 114, 94]
    }, {
        name: 'جریان نقدی آزاد',
        data: [35, 41, 36, 26, 45, 48, 52, 53, 41]
    }],
    chart: {
        height: 300,
        type: "bar",
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: '55%',
            endingShape: 'rounded'
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
    },
    xaxis: {
        categories: ['فوریه', 'مارس', 'آوریل', 'مه', 'ژوئن', 'جولای', 'آگوست', 'سپتامبر', 'اکتبر'],
    },
    yaxis: {
        title: {
            text: '(میلیون) تومان'
        }
    },
    fill: {
        opacity: 1
    },
    tooltip: {
        y: {
            formatter: function (val) {
                return "$ " + val + " thousands"
            }
        }
    },
    colors: ["--dx-primary", "--dx-success", "--dx-warning"],
};

allCharts.push([{ 'id': 'basicColumnChart', 'data': options }]);

//Column with Data Labels Chart
var options = {
    series: [{
        name: 'تورم',
        data: [2.3, 3.1, 4.0, 10.1, 4.0, 3.6, 3.2, 2.3, 1.4, 0.8, 0.5, 0.2]
    }],
    chart: {
        height: 300,
        type: "bar",
    },
    plotOptions: {
        bar: {
            borderRadius: 10,
            dataLabels: {
                position: 'top', // top, center, bottom
            },
        }
    },
    dataLabels: {
        enabled: true,
        formatter: function (val) {
            return val + "%";
        },
        offsetY: -20,
        style: {
            fontSize: '12px',
            colors: ["#304758"]
        }
    },

    xaxis: {
        categories: ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن", "جولای", "آگوست", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"],
        position: 'top',
        axisBorder: {
            show: false
        },
        axisTicks: {
            show: false
        },
        crosshairs: {
            fill: {
                type: 'gradient',
                gradient: {
                    colorFrom: '#D8E3F0',
                    colorTo: '#BED1E6',
                    stops: [0, 100],
                    opacityFrom: 0.4,
                    opacityTo: 0.5,
                }
            }
        },
        tooltip: {
            enabled: true,
        }
    },
    yaxis: {
        axisBorder: {
            show: false
        },
        axisTicks: {
            show: false,
        },
        labels: {
            show: false,
            formatter: function (val) {
                return val + "%";
            }
        }

    },
    title: {
        text: 'تورم ماهانه در آرژانتین، 2002',
        floating: true,
        offsetY: 330,
        align: 'center',
        style: {
            color: '--dx-secondary-color'
        }
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'labelColumnChart', 'data': options }]);

//Stacked Columns Chart
var options = {
    series: [{
        name: 'A محصول',
        data: [44, 55, 41, 67, 22, 43]
    }, {
        name: 'B محصول',
        data: [13, 23, 20, 8, 13, 27]
    }, {
        name: 'C محصول',
        data: [11, 17, 15, 15, 21, 14]
    }, {
        name: 'D محصول',
        data: [21, 7, 25, 13, 22, 8]
    }],
    chart: {
        height: 300,
        type: "bar",
        stacked: true,
        toolbar: {
            show: true
        },
        zoom: {
            enabled: true
        }
    },
    responsive: [{
        breakpoint: 480,
        options: {
            legend: {
                position: 'bottom',
                offsetX: -10,
                offsetY: 0
            }
        }
    }],
    plotOptions: {
        bar: {
            horizontal: false,
            borderRadius: 10,
            dataLabels: {
                total: {
                    enabled: true,
                    style: {
                        fontSize: '13px',
                        fontWeight: 900
                    }
                }
            }
        },
    },

    xaxis: {
        categories: ['01/01/2024 GMT', '01/02/2024 GMT', '01/03/2024 GMT', '01/04/2024 GMT', '01/05/2024 GMT', '01/06/2024 GMT'],
        type: 'datetime'
    },
    legend: {
        position: 'right',
        offsetY: 40
    },
    fill: {
        opacity: 1
    },
    colors: ["--dx-primary", "--dx-success", "--dx-danger", "--dx-warning"],
};

allCharts.push([{ 'id': 'stackedColumnChart', 'data': options }]);

//Stacked Columns 100 Chart
var options = {
    series: [{
        name: 'A محصول',
        data: [44, 55, 41, 67, 22, 43, 21, 49]
    }, {
        name: 'B محصول',
        data: [13, 23, 20, 8, 13, 27, 33, 12]
    }, {
        name: 'C محصول',
        data: [11, 17, 15, 15, 21, 14, 15, 13]
    }],
    chart: {
        height: 300,
        type: "bar",
        stacked: true,
        stackType: '100%'
    },
    responsive: [{
        breakpoint: 480,
        options: {
            legend: {
                position: 'bottom',
                offsetX: -10,
                offsetY: 0
            }
        }
    }],
    xaxis: {
        categories: ['2024 Q1', '2024 Q2', '2024 Q3', '2024 Q4', '2025 Q1', '2025 Q2', '2025 Q3', '2025 Q4'],
    },
    fill: {
        opacity: 1
    },
    legend: {
        position: 'right',
        offsetX: 0,
        offsetY: 50
    },
    colors: ["--dx-primary", "--dx-success", "--dx-warning"],
};

allCharts.push([{ 'id': 'stackedColumn100Chart', 'data': options }]);

//Grouped Stacked Columns Chart
var options = {
    series: [
        {
            name: 'بودجه سه ماه اول',
            group: 'budget',
            data: [44000, 55000, 41000, 67000, 22000, 43000]
        },
        {
            name: 'سه ماهه اول واقعی',
            group: 'actual',
            data: [48000, 50000, 40000, 65000, 25000, 40000]
        },
        {
            name: 'بودجه سه ماه دوم',
            group: 'budget',
            data: [13000, 36000, 20000, 8000, 13000, 27000]
        },
        {
            name: 'سه ماهه دوم واقعی',
            group: 'actual',
            data: [20000, 40000, 25000, 10000, 12000, 28000]
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
            horizontal: false
        }
    },
    xaxis: {
        categories: [
            'تبلیغات آنلاین',
            'آموزش فروش',
            'تبلیغات چاپی',
            'کاتالوگ‌ها',
            'جلسات',
            'روابط عمومی'
        ]
    },
    fill: {
        opacity: 1
    },
    yaxis: {
        labels: {
            formatter: (val) => {
                return val / 1000 + 'K'
            }
        }
    },
    legend: {
        position: 'top',
        horizontalAlign: 'left'
    },
    colors: ["--dx-primary", "--dx-success", "--dx-primary-border-subtle", "--dx-success-border-subtle"],
};

allCharts.push([{ 'id': 'groupStackedColumnChart', 'data': options }]);

//Dumbbell Chart
var options = {
    series: [
        {
            data: [
                {
                    x: '2008',
                    y: [2800, 4500]
                },
                {
                    x: '2009',
                    y: [3200, 4100]
                },
                {
                    x: '2010',
                    y: [2950, 7800]
                },
                {
                    x: '2011',
                    y: [3000, 4600]
                },
                {
                    x: '2012',
                    y: [3500, 4100]
                },
                {
                    x: '2013',
                    y: [4500, 6500]
                },
                {
                    x: '2014',
                    y: [4100, 5600]
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "rangeBar",
        zoom: {
            enabled: false
        }
    },
    plotOptions: {
        bar: {
            isDumbbell: true,
            columnWidth: 3,
            dumbbellColors: [["--dx-primary", "--dx-pink"]]
        }
    },
    legend: {
        show: true,
        showForSingleSeries: true,
        position: 'top',
        horizontalAlign: 'left',
        customLegendItems: ['A محصول', 'B محصول']
    },
    fill: {
        type: 'gradient',
        gradient: {
            type: 'vertical',
            gradientToColors: ['--dx-pink'],
            inverseColors: true,
            stops: [0, 100]
        }
    },
    grid: {
        xaxis: {
            lines: {
                show: true
            }
        },
        yaxis: {
            lines: {
                show: false
            }
        }
    },
    xaxis: {
        tickPlacement: 'on'
    },
    colors: ["--dx-primary", "--dx-pink"],
};

allCharts.push([{ 'id': 'dumbbellColumnChart', 'data': options }]);

//Column with Markers Chart
var options = {
    series: [
        {
            name: 'واقعی',
            data: [
                {
                    x: '2011',
                    y: 1292,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 1400,
                            strokeHeight: 5,
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2012',
                    y: 4432,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 5400,
                            strokeHeight: 5,
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2013',
                    y: 5423,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 5200,
                            strokeHeight: 5,
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2014',
                    y: 6653,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 6500,
                            strokeHeight: 5,
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2015',
                    y: 8133,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 6600,
                            strokeHeight: 13,
                            strokeWidth: 0,
                            strokeLineCap: 'round',
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2016',
                    y: 7132,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 7500,
                            strokeHeight: 5,
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2017',
                    y: 7332,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 8700,
                            strokeHeight: 5,
                            strokeColor: '#775DD0'
                        }
                    ]
                },
                {
                    x: '2018',
                    y: 6553,
                    goals: [
                        {
                            name: 'مورد انتظار',
                            value: 7300,
                            strokeHeight: 2,
                            strokeDashArray: 2,
                            strokeColor: '#775DD0'
                        }
                    ]
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: 'bar',
    },
    plotOptions: {
        bar: {
            columnWidth: '60%'
        }
    },
    dataLabels: {
        enabled: false
    },
    legend: {
        show: true,
        showForSingleSeries: true,
        customLegendItems: ['واقعی', 'مورد انتظار'],
        markers: {
            fillColors: ['--dx-primary', '--dx-success']
        }
    },
    colors: ["--dx-primary", "--dx-success"],
};

allCharts.push([{ 'id': 'markersColumnChart', 'data': options }]);

//Column with Group Label Chart
var options = {
    series: [{
        name: "فروش",
        data: [{
            x: '2023/01/01',
            y: 400
        }, {
            x: '2023/04/01',
            y: 430
        }, {
            x: '2023/07/01',
            y: 448
        }, {
            x: '2023/10/01',
            y: 470
        }, {
            x: '2024/01/01',
            y: 540
        }, {
            x: '2024/04/01',
            y: 580
        }, {
            x: '2024/07/01',
            y: 690
        }, {
            x: '2024/10/01',
            y: 690
        }]
    }],
    chart: {
        height: 300,
        type: 'bar',
    },
    xaxis: {
        type: 'category',
        labels: {
            formatter: function (val) {
                return "Q" + dayjs(val).quarter()
            }
        },
        group: {
            style: {
                fontSize: '10px',
                fontWeight: 700
            },
            groups: [
                { title: '2019', cols: 4 },
                { title: '2020', cols: 4 }
            ]
        }
    },
    title: {
        text: 'Grouped Labels on the X-axis',
    },
    tooltip: {
        x: {
            formatter: function (val) {
                return "Q" + dayjs(val).quarter() + " " + dayjs(val).format("YYYY")
            }
        }
    },
    colors: ["--dx-primary"]
};

allCharts.push([{ 'id': 'groupLabelColumnChart', 'data': options }]);

//Column with Rotated Labels Chart
var options = {
    series: [{
        name: 'وعده غذایی',
        data: [44, 55, 41, 67, 22, 43, 21, 33, 45, 31, 87, 65, 35]
    }],
    annotations: {
        points: [{
            x: 'موز',
            seriesIndex: 0,
            label: {
                borderColor: 'var(--dx-secondary)',
                offsetY: 0,
                style: {
                    color: '#fff',
                    background: 'var(--dx-secondary)',
                    fontSize: '12px'
                },
                text: 'موز بسیار مفید است'
            }
        }]
    },
    chart: {
        height: 350,
        type: 'bar',
    },
    plotOptions: {
        bar: {
            borderRadius: 10,
            columnWidth: '35%',
        }
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        width: 2
    },
    xaxis: {
        tickPlacement: 'on',
        labels: {
            rotate: -45,
            rotateAlways: true,
            hideOverlappingLabels: false,
            trim: false,
            maxHeight: 80,
            style: {
                fontSize: '12px'
            }
        },
        categories: [
            'سیب',
            'پرتقال',
            'توت‌فرنگی',
            'آناناس',
            'انبه',
            'موز',
            'شاه‌توت',
            'گلابی',
            'هندوانه',
            'گیلاس',
            'انار',
            'نارنگی',
            'پاپایا'
        ]
    },

    yaxis: {
        title: {
            text: 'وعده غذایی'
        }
    },

    fill: {
        type: 'gradient',
        gradient: {
            shade: 'light',
            type: 'horizontal',
            shadeIntensity: 0.25,
            inverseColors: true,
            opacityFrom: 0.85,
            opacityTo: 0.85,
            stops: [0, 50, 100]
        }
    },

    colors: ['var(--dx-primary)']
};

allCharts.push([{ 'id': 'rotatedLabelColumnChart', 'data': options }]);

//Column with Negative Values Chart
dayjs.extend(window.dayjs_plugin_quarterOfYear)
var options = {
    series: [{
        name: 'جریان نقدی',
        data: [1.45, 5.42, 5.9, -0.42, -12.6, -18.1, -18.2, -14.16, -11.1, -6.09, 0.34, 3.88, 13.07,
            5.8, 2, 7.37, 8.1, 13.57, 15.75, 17.1, 19.8, -27.03, -54.4, -47.2, -43.3, -18.6, -
            48.6, -41.1, -39.6, -37.6, -29.4, -21.4, -2.4
        ]
    }],
    chart: {
        height: 300,
        type: 'bar',
    },
    plotOptions: {
        bar: {
            colors: {
                ranges: [{
                    from: -100,
                    to: -46,
                    color: '--dx-danger'
                }, {
                    from: -45,
                    to: 0,
                    color: '--dx-warning'
                }]
            },
            columnWidth: '80%',
        }
    },
    dataLabels: {
        enabled: false,
    },
    yaxis: {
        title: {
            text: 'رشد',
        },
        labels: {
            formatter: function (y) {
                return y.toFixed(0) + "%";
            }
        }
    },
    xaxis: {
        type: 'datetime',
        categories: ['2011-01-01', '2011-02-01', '2011-03-01', '2011-04-01', '2011-05-01', '2011-06-01',
            '2011-07-01', '2011-08-01', '2011-09-01', '2011-10-01', '2011-11-01', '2011-12-01',
            '2012-01-01', '2012-02-01', '2012-03-01', '2012-04-01', '2012-05-01', '2012-06-01',
            '2012-07-01', '2012-08-01', '2012-09-01', '2012-10-01', '2012-11-01', '2012-12-01',
            '2013-01-01', '2013-02-01', '2013-03-01', '2013-04-01', '2013-05-01', '2013-06-01',
            '2013-07-01', '2013-08-01', '2013-09-01'
        ],
        labels: {
            rotate: -90
        }
    },
    colors: ["--dx-primary"]
};

allCharts.push([{ 'id': 'negativeLabelColumnChart', 'data': options }]);

//Distributed Columns Chart
dayjs.extend(window.dayjs_plugin_quarterOfYear)
var options = {
    series: [{
        data: [21, 22, 10, 28, 16, 21, 13, 30]
    }],
    chart: {
        height: 300,
        type: 'bar',
        events: {
            click: function (chart, w, e) {
                // console.log(chart, w, e)
            }
        }
    },
    plotOptions: {
        bar: {
            columnWidth: '45%',
            distributed: true,
        }
    },
    dataLabels: {
        enabled: false
    },
    legend: {
        show: false
    },
    xaxis: {
        categories: [['جانی', 'دپ'],
        ['جویی', 'اسمیت'],
        ['جیک', 'جینهال'],
            'امبر',
        ['پیتر', 'تیل'],
        ['کریس', 'ایونس'],
        ['دیوید', 'جونز'],
        ['جولیا', 'رابرتز'],
        ],
        labels: {
            style: {
                colors: ["--dx-primary", "--dx-pink", "--dx-info", "--dx-success", "--dx-warning", "--dx-secondary", "--dx-danger", "--dx-orange"],
                fontSize: '12px'
            }
        }
    },
    colors: ["--dx-primary", "--dx-pink", "--dx-info", "--dx-success", "--dx-warning", "--dx-secondary", "--dx-danger", "--dx-orange"]
};

allCharts.push([{ 'id': 'distributedColumnChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });