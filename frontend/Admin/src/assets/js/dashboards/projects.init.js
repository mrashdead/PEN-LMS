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

//Project Status Chart
var options = {
    series: [{
        name: 'درآمد',
        data: [67, 48, 85, 51, 93, 109, 116]
    }],
    chart: {
        defaultLocale: "en",
        height: 115,
        type: "area",
        sparkline: { enabled: !0 },
        zoom: {
            enabled: false
        },
    },
    dataLabels: {
        enabled: false
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    stroke: {
        width: 3,
        curve: 'smooth',
        dashArray: 2
    },
    legend: {
        tooltipHoverFormatter: function (val, opts) {
            return val + ' - <strong>' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + '</strong>'
        }
    },
    markers: {
        size: 0,
        hover: {
            sizeOffset: 6
        }
    },
    labels: ['آذر', 'آبان', 'مهر', 'شهریور', 'مرداد', 'تیر', 'خرداد'],
    yaxis: {
        title: {
            text: 'Growth',
        },
        labels: {
            formatter: function (y) {
                return "$" + y.toFixed(0) + "k";
            }
        }
    },
    grid: {
        padding: {
            top: -20,
            right: 0,
            bottom: 0,
        },
    },
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'projectStatusChart', 'data': options }]);

//Daily Working Reports
var options = {
    series: [55, 33, 46],
    chart: {
        height: 210,
        type: "donut",
        dropShadow: {
            enabled: true,
            color: '#111',
            top: -1,
            left: 3,
            blur: 3,
            opacity: 0.2
        }
    },
    stroke: {
        width: 0,
    },
    plotOptions: {
        pie: {
            donut: {
                labels: {
                    show: false,
                }
            }
        }
    },
    labels: ["بعد از ظهر", "عصر", "صبح"],
    dataLabels: {
        enabled: false,
    },
    tooltip: {
        style: {
            fontFamily: 'Vazir'
        }
    },
    fill: {
        type: 'pattern',
        pattern: {
            style: 'squares',
        },
    },
    states: {
        hover: {
            filter: 'none'
        }
    },
    theme: {
        palette: 'palette2'
    },
    legend: {
        show: false
    },
    colors: ["--dx-primary", "--dx-secondary", "--dx-success"],
};

allCharts.push([{ 'id': 'dailyWorkingReportsChart', 'data': options }]);

//my task 1
var options = {
    series: [32],
    chart: {
        height: 60,
        width: 50,
        type: 'radialBar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                show: false
            },
            hollow: {
                size: '20%',
            }
        },
    },
    labels: ['Progress'],
    colors: ["--dx-primary"],
};

allCharts.push([{ 'id': 'myTask1Chart', 'data': options }]);

//my task 2
var options = {
    series: [45],
    chart: {
        height: 60,
        width: 50,
        type: 'radialBar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                show: false
            },
            hollow: {
                size: '20%',
            }
        },
    },
    labels: ['Progress'],
    colors: ["--dx-success"],
};

allCharts.push([{ 'id': 'myTask2Chart', 'data': options }]);

//my task 3
var options = {
    series: [79],
    chart: {
        height: 60,
        width: 50,
        type: 'radialBar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                show: false
            },
            hollow: {
                size: '20%',
            }
        },
    },
    labels: ['Progress'],
    colors: ["--dx-danger"],
};

allCharts.push([{ 'id': 'myTask3Chart', 'data': options }]);

//my task 4
var options = {
    series: [100],
    chart: {
        height: 60,
        width: 50,
        type: 'radialBar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                show: false
            },
            hollow: {
                size: '20%',
            }
        },
    },
    labels: ['Progress'],
    colors: ["--dx-warning"],
};

allCharts.push([{ 'id': 'myTask4Chart', 'data': options }]);

//my task 5
var options = {
    series: [87],
    chart: {
        height: 60,
        width: 50,
        type: 'radialBar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                show: false
            },
            hollow: {
                size: '20%',
            }
        },
    },
    labels: ['Progress'],
    colors: ["--dx-secondary"],
};

allCharts.push([{ 'id': 'myTask5Chart', 'data': options }]);

//my task 6
var options = {
    series: [26],
    chart: {
        height: 60,
        width: 50,
        type: 'radialBar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                show: false
            },
            hollow: {
                size: '20%',
            }
        },
    },
    labels: ['Progress'],
    colors: ["--dx-orange"],
};

allCharts.push([{ 'id': 'myTask6Chart', 'data': options }]);

//my task 7
var options = {
    series: [49],
    chart: {
        height: 60,
        width: 50,
        type: 'radialBar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                show: false
            },
            hollow: {
                size: '20%',
            }
        },
    },
    labels: ['Progress'],
    colors: ["--dx-info"],
};

allCharts.push([{ 'id': 'myTask7Chart', 'data': options }]);

//my task 8
var options = {
    series: [73],
    chart: {
        height: 60,
        width: 50,
        type: 'radialBar',
        sparkline: { enabled: !0 },
    },
    plotOptions: {
        radialBar: {
            hollow: {
                size: '70%',
            }
        },
    },
    plotOptions: {
        radialBar: {
            dataLabels: {
                show: false
            },
            hollow: {
                size: '20%',
            }
        },
    },
    labels: ['Progress'],
    colors: ["--dx-pink"],
};

allCharts.push([{ 'id': 'myTask8Chart', 'data': options }]);

updateAllCharts();

/**
 * TodoListManager - A class to manage todo list functionality
 */
class TodoListManager {
    constructor(containerSelector, defaultSelectedIndexes = []) {
        this.container = document.querySelector(containerSelector);
        this.defaultSelectedIndexes = defaultSelectedIndexes;
        this.tasks = [];
        this.init();
    }

    init() {
        // Extract tasks from the DOM
        this.extractTasksFromDOM();

        // Set default selected tasks
        this.setDefaultSelectedTasks();

        // Add event listeners to checkboxes
        this.addEventListeners();
    }

    extractTasksFromDOM() {
        // Find all task items in the container
        const taskItems = this.container.querySelectorAll('.task-list-item');

        taskItems.forEach((taskItem, index) => {
            const checkbox = taskItem.querySelector('.form-check-input');
            const label = taskItem.querySelector('.form-check-label');

            this.tasks.push({
                id: checkbox.id,
                text: label.textContent.trim(),
                completed: checkbox.checked,
                index: index
            });
        });
    }

    setDefaultSelectedTasks() {
        // Select default tasks
        this.defaultSelectedIndexes.forEach(index => {
            if (index < this.tasks.length) {
                const taskId = this.tasks[index].id;
                const checkbox = document.getElementById(taskId);
                if (checkbox) {
                    checkbox.checked = true;
                    this.tasks[index].completed = true;
                }
            }
        });
    }

    addEventListeners() {
        // Add change event listeners to all checkboxes
        this.tasks.forEach(task => {
            const checkbox = document.getElementById(task.id);
            if (checkbox) {
                checkbox.addEventListener('change', (e) => {
                    this.updateTaskStatus(task.id, e.target.checked);
                });
            }
        });
    }

    updateTaskStatus(taskId, isCompleted) {
        // Update task status in our data structure
        const taskIndex = this.tasks.findIndex(task => task.id === taskId);
        if (taskIndex !== -1) {
            this.tasks[taskIndex].completed = isCompleted;
            console.log(`Task "${this.tasks[taskIndex].text}" is now ${isCompleted ? 'completed' : 'pending'}`);
        }
    }

    // Get all tasks
    getAllTasks() {
        return this.tasks;
    }

    // Get completed tasks
    getCompletedTasks() {
        return this.tasks.filter(task => task.completed);
    }

    // Get pending tasks
    getPendingTasks() {
        return this.tasks.filter(task => !task.completed);
    }
}

// Initialize the TodoListManager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Select the first and second tasks by default (indexes 0 and 1)
    const todoManager = new TodoListManager('.task-list', [2, 6]);
});