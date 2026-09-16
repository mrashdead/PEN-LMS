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
            data: [
                {
                    x: 'کدنویسی',
                    y: [
                        new Date('2019-03-02').getTime(),
                        new Date('2019-03-04').getTime()
                    ]
                },
                {
                    x: 'تست',
                    y: [
                        new Date('2019-03-04').getTime(),
                        new Date('2019-03-08').getTime()
                    ]
                },
                {
                    x: 'اعتبارسنجی',
                    y: [
                        new Date('2019-03-08').getTime(),
                        new Date('2019-03-12').getTime()
                    ]
                },
                {
                    x: 'دیپلوی کردن',
                    y: [
                        new Date('2019-03-12').getTime(),
                        new Date('2019-03-18').getTime()
                    ]
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "rangeBar",
    },
    plotOptions: {
        bar: {
            horizontal: true
        }
    },
    xaxis: {
        type: 'datetime'
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-warning", "--dx-danger"],
};

allCharts.push([{ 'id': 'basicChart', 'data': options }]);

//Advanced Chart
var options = {
    series: [
        {
            name: 'باب',
            data: [
                {
                    x: 'طراحی',
                    y: [
                        new Date('2019-03-05').getTime(),
                        new Date('2019-03-08').getTime()
                    ]
                },
                {
                    x: 'کدنویسی',
                    y: [
                        new Date('2019-03-02').getTime(),
                        new Date('2019-03-05').getTime()
                    ]
                },
                {
                    x: 'کدنویسی',
                    y: [
                        new Date('2019-03-05').getTime(),
                        new Date('2019-03-07').getTime()
                    ]
                },
                {
                    x: 'تست',
                    y: [
                        new Date('2019-03-03').getTime(),
                        new Date('2019-03-09').getTime()
                    ]
                },
                {
                    x: 'تست',
                    y: [
                        new Date('2019-03-08').getTime(),
                        new Date('2019-03-11').getTime()
                    ]
                },
                {
                    x: 'اعتبارسنجی',
                    y: [
                        new Date('2019-03-11').getTime(),
                        new Date('2019-03-16').getTime()
                    ]
                },
                {
                    x: 'طراحی',
                    y: [
                        new Date('2019-03-01').getTime(),
                        new Date('2019-03-03').getTime()
                    ],
                }
            ]
        },
        {
            name: 'جویی',
            data: [
                {
                    x: 'طراحی',
                    y: [
                        new Date('2019-03-02').getTime(),
                        new Date('2019-03-05').getTime()
                    ]
                },
                {
                    x: 'تست',
                    y: [
                        new Date('2019-03-06').getTime(),
                        new Date('2019-03-16').getTime()
                    ],
                    goals: [
                        {
                            name: 'Break',
                            value: new Date('2019-03-10').getTime(),
                            strokeColor: '#CD2F2A'
                        }
                    ]
                },
                {
                    x: 'کدنویسی',
                    y: [
                        new Date('2019-03-03').getTime(),
                        new Date('2019-03-07').getTime()
                    ]
                },
                {
                    x: 'دیپلوی کردن',
                    y: [
                        new Date('2019-03-20').getTime(),
                        new Date('2019-03-22').getTime()
                    ]
                },
                {
                    x: 'طراحی',
                    y: [
                        new Date('2019-03-10').getTime(),
                        new Date('2019-03-16').getTime()
                    ]
                }
            ]
        },
        {
            name: 'دن',
            data: [
                {
                    x: 'کدنویسی',
                    y: [
                        new Date('2019-03-10').getTime(),
                        new Date('2019-03-17').getTime()
                    ]
                },
                {
                    x: 'اعتبارسنجی',
                    y: [
                        new Date('2019-03-05').getTime(),
                        new Date('2019-03-09').getTime()
                    ],
                    goals: [
                        {
                            name: 'Break',
                            value: new Date('2019-03-07').getTime(),
                            strokeColor: '#CD2F2A'
                        }
                    ]
                },
            ]
        }
    ],
    chart: {
        height: 300,
        type: "rangeBar",
    },
    plotOptions: {
        bar: {
            horizontal: true,
            barHeight: '80%'
        }
    },
    xaxis: {
        type: 'datetime'
    },
    stroke: {
        width: 1
    },
    fill: {
        type: 'solid',
        opacity: 0.6
    },
    legend: {
        position: 'top',
        horizontalAlign: 'left'
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-warning", "--dx-danger"],
};

allCharts.push([{ 'id': 'advancedTimelineChart', 'data': options }]);

//Multiple series – Group rows Chart
var options = {
    series: [
        // George Washington
        {
            name: 'جورج واشنگتن',
            data: [
                {
                    x: 'رئیس جمهور',
                    y: [
                        new Date(1789, 3, 30).getTime(),
                        new Date(1797, 2, 4).getTime()
                    ]
                },
            ]
        },
        // John Adams
        {
            name: 'جان آدامز',
            data: [
                {
                    x: 'رئیس جمهور',
                    y: [
                        new Date(1797, 2, 4).getTime(),
                        new Date(1801, 2, 4).getTime()
                    ]
                },
                {
                    x: 'معاون رئیس جمهور',
                    y: [
                        new Date(1789, 3, 21).getTime(),
                        new Date(1797, 2, 4).getTime()
                    ]
                }
            ]
        },
        // Thomas Jefferson
        {
            name: 'توماس جفرسون',
            data: [
                {
                    x: 'رئیس جمهور',
                    y: [
                        new Date(1801, 2, 4).getTime(),
                        new Date(1809, 2, 4).getTime()
                    ]
                },
                {
                    x: 'معاون رئیس جمهور',
                    y: [
                        new Date(1797, 2, 4).getTime(),
                        new Date(1801, 2, 4).getTime()
                    ]
                },
                {
                    x: 'وزیر امور خارجه',
                    y: [
                        new Date(1790, 2, 22).getTime(),
                        new Date(1793, 11, 31).getTime()
                    ]
                }
            ]
        },
        // Aaron Burr
        {
            name: 'آرون بِر',
            data: [
                {
                    x: 'معاون رئیس جمهور',
                    y: [
                        new Date(1801, 2, 4).getTime(),
                        new Date(1805, 2, 4).getTime()
                    ]
                }
            ]
        },
        // George Clinton
        {
            name: 'جورج کلینتون',
            data: [
                {
                    x: 'معاون رئیس جمهور',
                    y: [
                        new Date(1805, 2, 4).getTime(),
                        new Date(1812, 3, 20).getTime()
                    ]
                }
            ]
        },
        // John Jay
        {
            name: 'جان جی',
            data: [
                {
                    x: 'وزیر امور خارجه',
                    y: [
                        new Date(1789, 8, 25).getTime(),
                        new Date(1790, 2, 22).getTime()
                    ]
                }
            ]
        },
        // Edmund Randolph
        {
            name: 'ادموند راندولف',
            data: [
                {
                    x: 'وزیر امور خارجه',
                    y: [
                        new Date(1794, 0, 2).getTime(),
                        new Date(1795, 7, 20).getTime()
                    ]
                }
            ]
        },
        // Timothy Pickering
        {
            name: 'تیموتی پیکرینگ',
            data: [
                {
                    x: 'وزیر امور خارجه',
                    y: [
                        new Date(1795, 7, 20).getTime(),
                        new Date(1800, 4, 12).getTime()
                    ]
                }
            ]
        },
        // Charles Lee
        {
            name: 'چارلز لی',
            data: [
                {
                    x: 'وزیر امور خارجه',
                    y: [
                        new Date(1800, 4, 13).getTime(),
                        new Date(1800, 5, 5).getTime()
                    ]
                }
            ]
        },
        // John Marshall
        {
            name: 'جان مارشال',
            data: [
                {
                    x: 'وزیر امور خارجه',
                    y: [
                        new Date(1800, 5, 13).getTime(),
                        new Date(1801, 2, 4).getTime()
                    ]
                }
            ]
        },
        // Levi Lincoln
        {
            name: 'لوی لینکلن',
            data: [
                {
                    x: 'وزیر امور خارجه',
                    y: [
                        new Date(1801, 2, 5).getTime(),
                        new Date(1801, 4, 1).getTime()
                    ]
                }
            ]
        },
        // James Madison
        {
            name: 'جیمز مدیسون',
            data: [
                {
                    x: 'وزیر امور خارجه',
                    y: [
                        new Date(1801, 4, 2).getTime(),
                        new Date(1809, 2, 3).getTime()
                    ]
                }
            ]
        },
    ],
    chart: {
        height: 300,
        type: "rangeBar",
    },
    plotOptions: {
        bar: {
            horizontal: true,
            barHeight: '50%',
            rangeBarGroupRows: true
        }
    },
    colors: [
        "#008FFB", "#00E396", "#FEB019", "#FF4560", "#775DD0",
        "#3F51B5", "#546E7A", "#D4526E", "#8D5B4C", "#F86624",
        "#D7263D", "#1B998B", "#2E294E", "#F46036", "#E2C044"
    ],
    fill: {
        type: 'solid'
    },
    xaxis: {
        type: 'datetime'
    },
    legend: {
        position: 'right'
    },
    tooltip: {
        custom: function (opts) {
            const fromYear = new Date(opts.y1).getFullYear()
            const toYear = new Date(opts.y2).getFullYear()
            const values = opts.ctx.rangeBar.getTooltipValues(opts)

            return (
                '<div class="apexcharts-tooltip-rangebar">' +
                '<div> <span class="series-name" style="color: ' +
                values.color +
                '">' +
                (values.seriesName ? values.seriesName : '') +
                '</span></div>' +
                '<div> <span class="category">' +
                values.ylabel +
                ' </span> <span class="value start-value">' +
                fromYear +
                '</span> <span class="separator">-</span> <span class="value end-value">' +
                toYear +
                '</span></div>' +
                '</div>'
            )
        }
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-warning", "--dx-danger"],
};

allCharts.push([{ 'id': 'multipleGroupTimelineChart', 'data': options }]);

//Dumbbell Chart (Horizontal) Chart
var options = {
    series: [
        {
            data: [
                {
                    x: 'اوپراتورها',
                    y: [2800, 4500]
                },
                {
                    x: 'موفقیت مشتری',
                    y: [3200, 4100]
                },
                {
                    x: 'مهندسی',
                    y: [2950, 7800]
                },
                {
                    x: 'مارکتینگ',
                    y: [3000, 4600]
                },
                {
                    x: 'محصول',
                    y: [3500, 4100]
                },
                {
                    x: 'علم داده',
                    y: [4500, 6500]
                },
                {
                    x: 'فروش',
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
            horizontal: true,
            isDumbbell: true,
            dumbbellColors: ["--dx-primary", "--dx-danger", "--dx-danger"],
        }
    },
    title: {
        text: 'Paygap Disparity'
    },
    legend: {
        show: true,
        showForSingleSeries: true,
        position: 'top',
        horizontalAlign: 'left',
        customLegendItems: ['زن', 'مرد']
    },
    fill: {
        type: 'gradient',
        gradient: {
            gradientToColors: ['#36BDCB'],
            inverseColors: false,
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
        },
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary", "--dx-warning", "--dx-danger"],
};

allCharts.push([{ 'id': 'dumbbellTimelineChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });