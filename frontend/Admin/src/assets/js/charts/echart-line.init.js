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

//basic line
var option;
option = {
    textStyle: {
        fontFamily: "Vazir",
        fontWeight: 400
    },
    xAxis: {
        type: 'category',
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        },
        axisLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        }
    },
    legend: {
        textStyle: {
            color: ["--dx-body-color"],
            fontFamily: "Vazir",
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
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    series: [
        {
            data: [150, 230, 224, 218, 135, 147, 260],
            type: 'line',
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        }
    ],
    tooltip: {
        textStyle: {
            fontFamily: "Vazir",
            fontWeight: 400
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

allCharts.push([{ 'id': 'basicLineChart', 'data': option }]);

//smooth line
var option;
option = {
    textStyle: {
        fontFamily: "Vazir",
        fontWeight: 400
    },
    xAxis: {
        type: 'category',
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        },
        axisLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        }
    },
    legend: {
        textStyle: {
            color: ["--dx-body-color"],
            fontFamily: "Vazir",
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
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    series: [
        {
            data: [820, 932, 901, 934, 1290, 1330, 1320],
            type: 'line',
            smooth: true,
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        }
    ],
    tooltip: {
        textStyle: {
            fontFamily: "Vazir",
            fontWeight: 400
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

allCharts.push([{ 'id': 'smoothLineChart', 'data': option }]);

//Stacked Line Chart
var option;
option = {
    textStyle: {
        fontFamily: "Vazir",
        fontWeight: 400
    },
    series: [
        {
            name: 'ایمیل',
            type: 'line',
            stack: 'Total',
            data: [120, 132, 101, 134, 90, 230, 210],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        },
        {
            name: 'تبلیغات اتحادیه',
            type: 'line',
            stack: 'Total',
            data: [220, 182, 191, 234, 290, 330, 310],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        },
        {
            name: 'تبلیغات ویدئویی',
            type: 'line',
            stack: 'Total',
            data: [150, 232, 201, 154, 190, 330, 410],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        },
        {
            name: 'دایرکت',
            type: 'line',
            stack: 'Total',
            data: [320, 332, 301, 334, 390, 330, 320],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        },
        {
            name: 'موتور جستجو',
            type: 'line',
            stack: 'Total',
            data: [820, 932, 901, 934, 1290, 1330, 1320],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        }
    ],
    tooltip: {
        trigger: 'axis',
        textStyle: {
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        },
        axisLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        }
    },
    legend: {
        data: ['Email', 'Union Ads', 'Video Ads', 'Direct', 'Search Engine'],
        textStyle: {
            color: ["--dx-body-color"],
            fontFamily: "Vazir",
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
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    toolbox: {
        show: false
    },
    color: ["--dx-primary", "--dx-secondary", "--dx-success", "--dx-danger", "--dx-warning"],
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    }
};

allCharts.push([{ 'id': 'stackedLineChart', 'data': option }]);

//Line Y Category
var option;
option = {
    textStyle: {
        fontFamily: "Vazir",
        fontWeight: 400
    },
    legend: {
        data: ['رابطه ارتفاع (کیلومتر) و دما (°C)'],
        textStyle: {
            color: ["--dx-body-color"],
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    tooltip: {
        trigger: 'axis',
        formatter: 'در ارتفاع {b} کیلومتر<br/>دما: {c} درجه سانتی‌گراد',
        textStyle: {
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    xAxis: {
        type: 'value',
        axisLabel: {
            formatter: '{value} °C',
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        },
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        }
    },
    yAxis: {
        type: 'category',
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        axisLabel: {
            formatter: '{value} km',
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        },
        axisLine: {
            onZero: false,
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        boundaryGap: false,
        data: ['0', '10', '20', '30', '40', '50', '60', '70', '80']
    },
    axisLine: {
        lineStyle: {
            color: ["--dx-border-color"]
        }
    },
    toolbox: {
        show: false
    },
    series: [
        {
            name: 'ارتفاع (کیلومتر) در مقابل دما (درجه سانتیگراد)',
            type: 'line',
            symbolSize: 10,
            symbol: 'circle',
            smooth: true,
            lineStyle: {
                width: 3,
                shadowColor: 'rgba(0,0,0,0.3)',
                shadowBlur: 10,
                shadowOffsetY: 8
            },
            data: [15, -50, -56.5, -46.5, -22.1, -2.5, -27.7, -55.7, -76.5],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        }
    ],
    color: ["--dx-primary"],
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    }
};

allCharts.push([{ 'id': 'categoryLineChart', 'data': option }]);

//Line Step
var option;
option = {
    textStyle: {
        fontFamily: "Vazir",
        fontWeight: 400
    },
    series: [
        {
            name: 'شروع مرحله',
            type: 'line',
            step: 'start',
            data: [120, 132, 101, 134, 90, 230, 210],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        },
        {
            name: 'مرحله میانی',
            type: 'line',
            step: 'middle',
            data: [220, 282, 201, 234, 290, 430, 410],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        },
        {
            name: 'پایان مرحله',
            type: 'line',
            step: 'end',
            data: [450, 432, 401, 454, 590, 530, 510],
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        }
    ],
    title: {
        text: 'Step Line',
        textStyle: {
            color: ["--dx-body-color"],
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    tooltip: {
        trigger: 'axis',
        textStyle: {
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    legend: {
        data: ['Step Start', 'Step Middle', 'Step End'],
        textStyle: {
            color: ["--dx-body-color"],
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    toolbox: {
        show: false
    },
    xAxis: {
        type: 'category',
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        },
        axisLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
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
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    color: ["--dx-primary", "--dx-indigo", "--dx-pink"],
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    }
};

allCharts.push([{ 'id': 'stepLineChart', 'data': option }]);

//Line Style
var option;
option = {
    textStyle: {
        fontFamily: "Vazir",
        fontWeight: 400
    },
    series: [
        {
            data: [120, 200, 150, 80, 70, 110, 130],
            type: 'line',
            symbol: 'triangle',
            symbolSize: 20,
            lineStyle: {
                color: "--dx-border-color",
                width: 4,
                type: 'dashed'
            },
            itemStyle: {
                borderWidth: 3,
                borderColor: '#EE6666',
                color: 'yellow'
            },
            label: {
                fontFamily: "Vazir",
                fontWeight: 400
            }
        }
    ],
    legend: {
        textStyle: {
            color: ["--dx-body-color"],
            fontFamily: "Vazir",
            fontWeight: 400
        }
    },
    toolbox: {
        show: false
    },
    xAxis: {
        type: 'category',
        data: ['جمعه', 'پنجشنبه', 'چهارشنبه', 'سه‌شنبه', 'دوشنبه', 'یکشنبه', 'شنبه'],
        splitLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
        },
        axisLabel: {
            color: "--dx-secondary-color",
            fontFamily: "Vazir",
            fontWeight: 400
        },
        axisLine: {
            lineStyle: {
                color: ["--dx-border-color"]
            }
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
            fontFamily: "Vazir",
            fontWeight: 400
        },
    },
    color: ["--dx-primary", "--dx-indigo", "--dx-pink"],
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    },
    tooltip: {
        textStyle: {
            fontFamily: "Vazir",
            fontWeight: 400
        }
    }
};

allCharts.push([{ 'id': 'styleLineChart', 'data': option }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });