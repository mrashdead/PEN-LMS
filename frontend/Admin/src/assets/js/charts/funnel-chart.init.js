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

//Funnel Chart
var options = {
    series: [
        {
            name: "سری قیف",
            data: [1380, 1100, 990, 880, 740, 548, 330, 200],
        },
    ],
    chart: {
        height: 300,
        type: "bar",
    },
    plotOptions: {
        bar: {
            borderRadius: 0,
            horizontal: true,
            barHeight: '80%',
            isFunnel: true,
        },
    },
    dataLabels: {
        enabled: true,
        formatter: function (val, opt) {
            return opt.w.globals.labels[opt.dataPointIndex] + ':  ' + val
        },
        dropShadow: {
            enabled: true,
        },
    },
    title: {
        text: 'قیف استخدام',
        align: 'middle',
    },
    xaxis: {
        categories: [
            'منبع‌یابی شده',
            'غربالگری شده',
            'ارزیابی شده',
            'مصاحبه HR',
            'فنی',
            'تأیید',
            'پیشنهاد شده',
            'استخدام شده',
        ],
    },
    legend: {
        show: false,
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

allCharts.push([{ 'id': 'funnelChart', 'data': options }]);

//Pyramid Chart
var options = {
    series: [
        {
            name: "",
            data: [200, 330, 548, 740, 880, 990, 1100, 1380],
        },
    ],
    chart: {
        height: 300,
        type: 'bar',
        animations: {
            speed: 500
        }
    },
    plotOptions: {
        bar: {
            borderRadius: 0,
            horizontal: true,
            distributed: true,
            barHeight: '80%',
            isFunnel: true,
        },
    },
    colors: [
        '--dx-primary',
        '--dx-success',
        '--dx-info',
        '--dx-danger',
        '--dx-warning',
        '--dx-orange',
        '--dx-secondary',
        '--dx-pink',
    ],
    dataLabels: {
        enabled: true,
        formatter: function (val, opt) {
            return opt.w.globals.labels[opt.dataPointIndex]
        },
        dropShadow: {
            enabled: true,
        },
    },
    title: {
        text: 'Pyramid چارت',
        align: 'middle',
    },
    xaxis: {
        categories: ['شیرینی', 'غذاهای فرآوری شده', 'چربی‌های سالم', 'گوشت', 'لوبیا و حبوبات', 'لبنیات', 'میوه و سبزیجات', 'غلات'],
    },
    legend: {
        show: false,
    },
    grid: {
        padding: {
            top: 0,
            right: 0,
            bottom: 0,
        },
    },
};

allCharts.push([{ 'id': 'pyramidChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });