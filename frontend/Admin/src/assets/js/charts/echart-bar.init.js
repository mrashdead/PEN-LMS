import * as echarts from 'echarts';

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
            chart[0].chart?.dispose();

        var dom = document.getElementById(chart[0].id);
        var chart2 = echarts.init(dom);
        chart[0].chart = chart2;

        if (data && typeof data === 'object') {
            chart2.setOption(data);
        }
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

//basic bar
var option;
option = {
    series: [
        {
            data: [120, 200, 150, 80, 70, 110, 130],
            type: 'bar'
        }
    ],
    xAxis: {
        type: 'category',
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        axisLabel: {
            fontFamily: 'Vazir',
            fontWeight: 400,
            color: "--dx-secondary-color"
        }
    },
    legend: {
        textStyle: {
            fontFamily: 'Vazir',
            fontWeight: 400,
            color: "--dx-body-color"
        }
    },
    yAxis: {
        type: 'value',
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        axisLabel: {
            fontFamily: 'Vazir',
            fontWeight: 400,
            color: "--dx-secondary-color"
        }
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    color: "--dx-primary",
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    },
    textStyle: {
        fontFamily: 'Vazir',
        fontWeight: 400
    }
};

allCharts.push([{ 'id': 'basicBarChart', 'data': option }]);

//Axis Align with Tick
var option;
option = {
    textStyle: {
        fontFamily: "Vazir",
        fontWeight: 400
    },

    series: [
        {
            name: 'دایرکت',
            type: 'bar',
            barWidth: '60%',
            data: [10, 52, 200, 334, 390, 330, 220],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        }
    ],
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow'
        },
        textStyle: {
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    xAxis: {
        type: 'category',
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        axisTick: {
            alignWithLabel: true
        },
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    legend: {
        show: false
    },
    yAxis: {
        type: 'value',
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    color: "--dx-secondary",
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    }
};

allCharts.push([{ 'id': 'axisAlignBarChart', 'data': option }]);

//Bar with Background
var option;
option = {
    textStyle: {
        fontFamily: 'Vazir',
        fontWeight: 400
    },
    series: [
        {
            data: [120, 200, 150, 80, 70, 110, 130],
            type: 'bar',
            showBackground: true,
            backgroundStyle: {
                color: "--dx-success-bg-subtle"
            }
        }
    ],
    xAxis: {
        type: 'category',
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: 'Vazir',
            fontWeight: 400
        }
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow'
        },
        textStyle: {
            fontFamily: 'Vazir'
        }
    },
    legend: {
        textStyle: {
            color: "--dx-body-color",
            fontFamily: 'Vazir',
            fontWeight: 400
        }
    },
    yAxis: {
        type: 'value',
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: 'Vazir',
            fontWeight: 400
        }
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    color: "--dx-success",
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    }
};

allCharts.push([{ 'id': 'backgroundBarChart', 'data': option }]);

//Set Style of Single Bar
var option;
option = {
    textStyle: {
        fontFamily: 'Vazir',
        fontWeight: 400
    },
    series: [
        {
            data: [
                120,
                {
                    value: 200,
                    itemStyle: {
                        color: "--dx-secondary"
                    }
                },
                150,
                80,
                70,
                110,
                130
            ],
            type: 'bar'
        }
    ],
    xAxis: {
        type: 'category',
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: 'Vazir',
            fontWeight: 400
        }
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow'
        },
        textStyle: {
            fontFamily: 'Vazir'
        }
    },
    legend: {
        textStyle: {
            color: "--dx-body-color",
            fontFamily: 'Vazir',
            fontWeight: 400
        }
    },
    yAxis: {
        type: 'value',
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: 'Vazir',
            fontWeight: 400
        }
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    color: "--dx-primary",
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    }
};

allCharts.push([{ 'id': 'singleBarChart', 'data': option }]);

//World Population
var option;
option = {
    textStyle: {
        fontFamily: 'Vazir',
        fontWeight: 400
    },
    series: [
        {
            name: '2024',
            type: 'bar',
            data: [18203, 23489, 29034, 104970, 131744, 630230]
        },
        {
            name: '2025',
            type: 'bar',
            data: [19325, 23438, 31000, 121594, 134141, 681807]
        }
    ],
    title: {
        text: 'جمعیت جهان',
        textStyle: {
            color: "--dx-body-color",
            fontFamily: 'Vazir',
            fontWeight: 700
        }
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow'
        },
        textStyle: {
            fontFamily: 'Vazir'
        }
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow'
        }
    },
    xAxis: {
        type: 'value',
        boundaryGap: [0, 0.01],
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: 'Vazir',
            fontWeight: 400
        }
    },
    yAxis: {
        type: 'category',
        data: ['برزیل', 'اندونزی', 'آمریکا', 'هند', 'چین', 'جهان'],
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: 'Vazir',
            fontWeight: 400
        }
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    color: "--dx-primary",
    grid: {
        top: '12%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    }
};

allCharts.push([{ 'id': 'worldPopulationBarChart', 'data': option }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });