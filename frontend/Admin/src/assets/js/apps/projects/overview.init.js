import ApexCharts from '../../../libs/apexcharts/apexcharts.esm.js'

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

//Working Hours Charts
var options = {
    series: [{
        name: 'ساعت', 
        data: [4, 3, 10, 9, 29, 19, 22, 9, 12, 7, 19, 5, 13, 9, 16, 2, 7, 8], 
    }],
    chart: {
        type: 'line',  
        height: 300,  
        zoom: { enabled: true },
        dropShadow: {
            enabled: true,
            top: 0,
            left: 0,
            blur: 3,
            color: '#000',
            opacity: 0.15
        }
    },
    stroke: {
        width: 5,  
        curve: 'smooth'
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    xaxis: {
        categories: [
            '1/11/1403', '2/11/1403', '3/11/1403', '4/11/1403', '5/11/1403', 
            '6/11/1403', '7/11/1403', '8/11/1403', '9/11/1403', '10/11/1403', 
            '11/11/1403', '12/11/1403', '1/11/1404', '2/11/1404', '3/11/1404', 
            '4/11/1404', '5/11/1404', '6/11/1404'
        ],
        tickAmount: 10
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'dark',
            gradientToColors: ["--dx-primary"], 
            type: 'horizontal',
            opacityFrom: 1, 
            opacityTo: 1, 
            stops: [0, 100, 100, 100]
        },
    },
    colors: ["--dx-secondary"],
    grid: {
        padding: {
            top: 0,
            right: 5,
            bottom: 0,
        },
        yaxis: {
            lines: {
                show: false 
            }
        },
    }
};

allCharts.push([{ 'id': 'workingHoursChart', 'data': options }]);

//Column with Data Labels Chart
var options = {
    series: [{
        name: 'کل وظایف',
        data: [3, 4, 8, 2, 6, 10, 8]
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
        offsetY: -20,
        style: {
            fontSize: '12px',
            colors: ["#304758"]
        }
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    xaxis: {
        categories: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
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
            show: true,
        }
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: -10,
        },
    },
    colors: ["--dx-primary"]
};

allCharts.push([{ 'id': 'taskActivitiesChart', 'data': options }]);

updateAllCharts();