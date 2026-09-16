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
                    x: 'دهلی نو',
                    y: 218
                },
                {
                    x: 'کلکته',
                    y: 149
                },
                {
                    x: 'بمبئی',
                    y: 184
                },
                {
                    x: 'احمد آباد',
                    y: 55
                },
                {
                    x: 'بنگلور',
                    y: 84
                },
                {
                    x: 'پونا',
                    y: 31
                },
                {
                    x: 'چونای',
                    y: 70
                },
                {
                    x: 'جیپور',
                    y: 30
                },
                {
                    x: 'سورات',
                    y: 44
                },
                {
                    x: 'حیدر آباد',
                    y: 68
                },
                {
                    x: 'لاک نو',
                    y: 28
                },
                {
                    x: 'ایندور',
                    y: 19
                },
                {
                    x: 'کانپور',
                    y: 29
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "treemap",
    },
    legend: {
        show: false
    },
    title: {
        text: 'Basic Treemap'
    },
    colors: ["--dx-primary", "--dx-warning", "--dx-danger"],
};

allCharts.push([{ 'id': 'basicTreemapChart', 'data': options }]);


//Treemap Multiple Series
var options = {
    series: [
        {
            name: 'دسکتاپ',
            data: [
                {
                    x: 'ABC',
                    y: 10
                },
                {
                    x: 'DEF',
                    y: 60
                },
                {
                    x: 'XYZ',
                    y: 41
                }
            ]
        },
        {
            name: 'موبایل',
            data: [
                {
                    x: 'ABCD',
                    y: 10
                },
                {
                    x: 'DEFG',
                    y: 20
                },
                {
                    x: 'WXYZ',
                    y: 51
                },
                {
                    x: 'PQR',
                    y: 30
                },
                {
                    x: 'MNO',
                    y: 20
                },
                {
                    x: 'CDE',
                    y: 30
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "treemap",
    },
    legend: {
        show: false
    },
    title: {
        text: 'Multi-dimensional Treemap',
        align: 'center'
    },
    colors: ["--dx-primary", "--dx-success"],
};

allCharts.push([{ 'id': 'multipleTreemapChart', 'data': options }]);

//Color Range
var options = {
    series: [
        {
            data: [
                {
                    x: 'INTC',
                    y: 1.2
                },
                {
                    x: 'GS',
                    y: 0.4
                },
                {
                    x: 'CVX',
                    y: -1.4
                },
                {
                    x: 'GE',
                    y: 2.7
                },
                {
                    x: 'CAT',
                    y: -0.3
                },
                {
                    x: 'RTX',
                    y: 5.1
                },
                {
                    x: 'CSCO',
                    y: -2.3
                },
                {
                    x: 'JNJ',
                    y: 2.1
                },
                {
                    x: 'PG',
                    y: 0.3
                },
                {
                    x: 'TRV',
                    y: 0.12
                },
                {
                    x: 'MMM',
                    y: -2.31
                },
                {
                    x: 'NKE',
                    y: 3.98
                },
                {
                    x: 'IYT',
                    y: 1.67
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "treemap",
    },
    legend: {
        show: false
    },
    title: {
        text: 'Treemap with Color scale'
    },
    dataLabels: {
        enabled: true,
        style: {
            fontSize: '12px',
        },
        formatter: function (text, op) {
            return [text, op.value]
        },
        offsetY: -4
    },
    plotOptions: {
        treemap: {
            enableShades: true,
            shadeIntensity: 0.5,
            reverseNegativeShade: true,
            colorScale: {
                ranges: [
                    {
                        from: -6,
                        to: 0,
                        color: '--dx-success'
                    },
                    {
                        from: 0.001,
                        to: 6,
                        color: '--dx-danger'
                    }
                ]
            }
        }
    },
};

allCharts.push([{ 'id': 'colorRangeTreemapChart', 'data': options }]);

//Distributed
var options = {
    series: [
        {
            data: [
                {
                    x: 'دهلی نو',
                    y: 218
                },
                {
                    x: 'کلکته',
                    y: 149
                },
                {
                    x: 'بمبئی',
                    y: 184
                },
                {
                    x: 'احمد آباد',
                    y: 55
                },
                {
                    x: 'بنگلور',
                    y: 84
                },
                {
                    x: 'پونا',
                    y: 31
                },
                {
                    x: 'چونای',
                    y: 70
                },
                {
                    x: 'جیپور',
                    y: 30
                },
                {
                    x: 'سورات',
                    y: 44
                },
                {
                    x: 'حیدر آباد',
                    y: 68
                },
                {
                    x: 'لاک نو',
                    y: 28
                },
                {
                    x: 'ایندور',
                    y: 19
                },
                {
                    x: 'کانپور',
                    y: 29
                }
            ]
        }
    ],
    chart: {
        height: 300,
        type: "treemap",
    },
    legend: {
        show: false
    },
    title: {
        text: 'Distributed Treemap (different color for each cell)',
        align: 'center'
    },
    plotOptions: {
        treemap: {
            distributed: true,
            enableShades: false
        }
    },
    colors: ["--dx-primary", "--dx-warning", "--dx-success", "--dx-secondary", "--dx-info"],
};

allCharts.push([{ 'id': 'distributedTreemapChart', 'data': options }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });