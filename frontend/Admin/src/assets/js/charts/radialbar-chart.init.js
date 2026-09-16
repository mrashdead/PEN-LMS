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
    series: [70],
    chart: {
        height: 300,
        type: "radialBar",
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    labels: ['فوتبال'],
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'basicRadialbarChart', 'data': options }]);

//Multiple
var options = {
    series: [44, 55, 67, 83],
    chart: {
        height: 300,
        type: "radialBar",
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                name: {
                    fontSize: '22px',
                },
                value: {
                    fontSize: '16px',
                },
                total: {
                    show: true,
                    label: 'کل',
                    formatter: function (w) {
                        // By default this function returns the average of all series. The below is just an example to show the use of custom formatter function
                        return 249
                    }
                }
            }
        }
    },
    labels: ['سیب', 'نارنگی', 'موز', 'توت'],
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary"],
};

allCharts.push([{ 'id': 'multipleRadialbarChart', 'data': options }]);

//Custom Angle Circle
var options = {
    series: [76, 67, 61, 90],
    chart: {
        height: 300,
        type: "radialBar",
    },
    plotOptions: {
        radialBar: {
            offsetY: 0,
            startAngle: 0,
            endAngle: 270,
            hollow: {
                margin: 5,
                size: '30%',
                background: 'transparent',
                image: undefined,
            },
            dataLabels: {
                name: {
                    show: false,
                },
                value: {
                    show: false,
                }
            }
        }
    },
    legend: {
        show: true,
        floating: true,
        fontSize: '16px',
        position: 'left',
        offsetX: 160,
        offsetY: 15,
        labels: {
            useSeriesColors: true,
        },
        markers: {
            size: 0
        },
        formatter: function (seriesName, opts) {
            return seriesName + ":  " + opts.w.globals.series[opts.seriesIndex]
        },
        itemMargin: {
            vertical: 3
        }
    },
    responsive: [{
        breakpoint: 480,
        options: {
            legend: {
                show: false
            }
        }
    }],
    labels: ['ویمیو', 'مسنجر', 'فیسبوک', 'لینکدین'],
    colors: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary"],
};

allCharts.push([{ 'id': 'customAngleRadialbarChart', 'data': options }]);

//Gradient
var options = {
    series: [75],
    chart: {
        height: 300,
        type: "radialBar",
        toolbar: {
            show: true
        }
    },
    plotOptions: {
        radialBar: {
            startAngle: -135,
            endAngle: 225,
            hollow: {
                margin: 0,
                size: '70%',
                image: undefined,
                imageOffsetX: 0,
                imageOffsetY: 0,
                position: 'front',
            },
            track: {
                strokeWidth: '67%',
                margin: 0, // margin is in pixels
            },

            dataLabels: {
                show: true,
                name: {
                    offsetY: -10,
                    show: true,
                    fontSize: '17px'
                },
                value: {
                    formatter: function (val) {
                        return parseInt(val);
                    },
                    fontSize: '36px',
                    show: true,
                }
            }
        }
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'dark',
            type: 'horizontal',
            shadeIntensity: 0.5,
            gradientToColors: ['--dx-success'],
            inverseColors: true,
            opacityFrom: 1,
            opacityTo: 1,
            stops: [0, 100]
        }
    },
    stroke: {
        lineCap: 'round'
    },
    labels: ['درصد'],
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'gradientRadialbarChart', 'data': options }]);

//Radial bars with Image
var options = {
    series: [67],
    chart: {
        height: 300,
        type: "radialBar"
    },
    plotOptions: {
        radialBar: {
            hollow: {
                margin: 15,
                size: '70%',
                image: 'assets/images/avatar/user-17.png',
                imageWidth: 64,
                imageHeight: 64,
                imageClipped: false
            },
            dataLabels: {
                name: {
                    show: false,
                },
                value: {
                    show: true,
                    offsetY: 70,
                    fontSize: '22px'
                }
            }
        }
    },
    fill: {
        type: 'image',
        image: {
            src: ['assets/images/gallery/img-01.jpg'],
        }
    },
    stroke: {
        lineCap: 'round'
    },
    labels: ['نوسان'],
};

allCharts.push([{ 'id': 'imageRadialbarChart', 'data': options }]);

//Stroked Gauge
var options = {
    series: [75],
    chart: {
        height: 300,
        type: "radialBar",
        offsetY: -10
    },
    plotOptions: {
        radialBar: {
            startAngle: -135,
            endAngle: 135,
            dataLabels: {
                name: {
                    fontSize: '16px',
                    color: undefined,
                    offsetY: 120
                },
                value: {
                    offsetY: 76,
                    fontSize: '22px',
                    color: undefined,
                    formatter: function (val) {
                        return val + "%";
                    }
                }
            }
        }
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'dark',
            shadeIntensity: 0.15,
            inverseColors: false,
            opacityFrom: 1,
            opacityTo: 1,
            stops: [0, 50, 65, 91]
        },
    },
    stroke: {
        dashArray: 4
    },
    labels: ['نسبت میانه'],
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'strokedGaugeRadialbarChart', 'data': options }]);

//Semi Circle Gauge
var options = {
    series: [76],
    chart: {
        height: 300,
        type: "radialBar",
        offsetY: -20,
        sparkline: {
            enabled: true
        }
    },
    plotOptions: {
        radialBar: {
            startAngle: -90,
            endAngle: 90,
            track: {
                strokeWidth: '97%',
                margin: 5, // margin is in pixels
            },
            dataLabels: {
                name: {
                    show: false
                },
                value: {
                    offsetY: -2,
                    fontSize: '22px'
                }
            }
        }
    },
    grid: {
        padding: {
            top: -10
        }
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'light',
            shadeIntensity: 0.4,
            inverseColors: false,
            opacityFrom: 1,
            opacityTo: 1,
            stops: [0, 50, 53, 91]
        },
    },
    labels: ['نتایج میانگین'],
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'semiGaugeRadialbarChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });