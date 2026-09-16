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

//Invitation Chart
var options = {
    series: [87],
    chart: {
        height: 250,
        type: "radialBar",
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '60%',
            },
            dataLabels: {
                show: true,
                name: {
                    fontWeight: '600'
                },
            }
        },
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'dark',
            gradientToColors: ['--dx-pink'],
            type: 'horizontal',
            opacityFrom: 1,
            opacityTo: 1,
            stops: [0, 100],
        },
    },
    stroke: {
        lineCap: 'round'
    },
    labels: ['دعوت‌های پذیرفته'],
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'invitationChart', 'data': options }]);

//Ticket sale Charts
var options = {
    series: [{ name: "فروش بلیط", data: [10, 41, 35, 51, 49, 62, 69] }],
    chart: {
        defaultLocale: "en",
        height: 180,
        type: "line",
        zoom: {
            enabled: true
        },
        toolbar: {
            show: false
        }
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        show: true,
        curve: 'monotoneCubic',
        lineCap: 'butt',
        width: 3,
        dashArray: 0,
    },
    xaxis: {
        categories: ["هفته 7","هفته 6","هفته 5","هفته 4","هفته 3","هفته 2","هفته 1"]
    },
    yaxis: {
        show: false,
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        },
        x: {
            show: true
        },
    },
    grid: {
        padding: {
            top: -10,
            right: 0,
            bottom: 0,
        },
        xaxis: {
            lines: {
                show: false
            }
        },
        yaxis: {
            lines: {
                show: false
            }
        },
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'ticketSaleChart', 'data': options }]);

updateAllCharts();