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

//Simple Chart
function generateData(baseval, count, yrange) {
    var i = 0;
    var series = [];
    while (i < count) {
        var x = Math.floor(Math.random() * (750 - 1 + 1)) + 1;;
        var y = Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;
        var z = Math.floor(Math.random() * (75 - 15 + 1)) + 15;

        series.push([x, y, z]);
        baseval += 86400000;
        i++;
    }
    return series;
}
var options = {
    series: [{
        name: 'Bubble1',
        data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
            min: 10,
            max: 60
        })
    },
    {
        name: 'Bubble2',
        data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
            min: 10,
            max: 60
        })
    },
    {
        name: 'Bubble3',
        data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
            min: 10,
            max: 60
        })
    },
    {
        name: 'Bubble4',
        data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
            min: 10,
            max: 60
        })
    }],
    chart: {
        height: 300,
        type: "bubble",
    },
    dataLabels: {
        enabled: false
    },
    fill: {
        opacity: 0.8
    },
    colors: ["--dx-primary", "--dx-success", "--dx-danger", "--dx-warning"],
    title: {
        text: 'Simple Bubble Chart'
    },
    xaxis: {
        tickAmount: 12,
        type: 'category',
    },
    yaxis: {
        max: 70
    }
};

allCharts.push([{ 'id': 'simpleBubbleChart', 'data': options }]);

//3D Bubble
var options = {
    series: [{
        name: 'Product1',
        data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
            min: 10,
            max: 60
        })
    },
    {
        name: 'Product2',
        data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
            min: 10,
            max: 60
        })
    },
    {
        name: 'Product3',
        data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
            min: 10,
            max: 60
        })
    },
    {
        name: 'Product4',
        data: generateData(new Date('11 Feb 2017 GMT').getTime(), 20, {
            min: 10,
            max: 60
        })
    }],
    chart: {
        height: 300,
        type: "bubble",
    },
    dataLabels: {
        enabled: false
    },
    fill: {
        type: 'gradient',
    },
    title: {
        text: '3D Bubble Chart'
    },
    xaxis: {
        tickAmount: 12,
        type: 'datetime',
        labels: {
            rotate: 0,
        }
    },
    yaxis: {
        max: 70
    },
    theme: {
        palette: 'palette2'
    },
    colors: ["--dx-primary", "--dx-success", "--dx-danger", "--dx-warning"],
};

allCharts.push([{ 'id': 'dbubbleChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });