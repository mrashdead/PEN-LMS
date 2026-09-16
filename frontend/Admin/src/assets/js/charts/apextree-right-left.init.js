import ApexTree from 'apextree'

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
        const jsonRenderData = JSON.parse(JSON.stringify(chart[0].renderData));
        const renderData = replaceCSSVariables(structuredClone(jsonRenderData));

        if (chart[0].chart)
            chart[0].chart.dispose();

        data.nodeTemplate = chart[0].data.nodeTemplate;
        var chart2 = new ApexTree(document.getElementById(chart[0].id), data);
        chart2.render(renderData);
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

const data = {
    id: 'Lucas_Alex',
    data: {
        name: 'لوکاس الکس',
        imageURL: 'assets/images/avatar/user-45.png',
    },
    options: {
        nodeBGColor: '--dx-primary-bg-subtle',
        nodeBGColorHover: '--dx-primary-border-subtle',
    },
    children: [
        {
            id: 'Alex_Lee',
            data: {
                name: 'الکس لی',
                imageURL: 'assets/images/avatar/user-16.png',
            },
            options: {
                nodeBGColor: '--dx-orange-bg-subtle',
                nodeBGColorHover: '--dx-orange-border-subtle',
            },
            children: [
                {
                    id: 'Mia_Patel',
                    data: {
                        name: 'میا پاتل',
                        imageURL: 'assets/images/avatar/user-15.png',
                    },
                    options: {
                        nodeBGColor: '--dx-success-bg-subtle',
                        nodeBGColorHover: '--dx-success-border-subtle',
                    },
                },
                {
                    id: 'Ryan_Clark',
                    data: {
                        name: 'رایان کلارک',
                        imageURL: 'assets/images/avatar/user-14.png',
                    },
                    options: {
                        nodeBGColor: '--dx-success-bg-subtle',
                        nodeBGColorHover: '--dx-success-border-subtle',
                    },
                },
                {
                    id: 'Zoe_Wang',
                    data: {
                        name: 'زویی وانگ',
                        imageURL: 'assets/images/avatar/user-12.png',
                    },
                    options: {
                        nodeBGColor: '--dx-success-bg-subtle',
                        nodeBGColorHover: '--dx-success-border-subtle',
                    },
                },
            ],
        },
        {
            id: 'Leo_Kim',
            data: {
                name: 'لئو کیم',
                imageURL: 'assets/images/avatar/user-11.png',
            },
            options: {
                nodeBGColor: '--dx-orange-bg-subtle',
                nodeBGColorHover: '--dx-orange-border-subtle',
            },
            children: [
                {
                    id: 'Ava_Jones',
                    data: {
                        name: 'آوا جونز',
                        imageURL: 'assets/images/avatar/user-10.png',
                    },
                    options: {
                        nodeBGColor: '--dx-warning-bg-subtle',
                        nodeBGColorHover: '--dx-warning-border-subtle',
                    },
                },
                {
                    id: 'Maya_Gupta',
                    data: {
                        name: 'مایا گوپتا',
                        imageURL: 'assets/images/avatar/user-9.png',
                    },
                    options: {
                        nodeBGColor: '--dx-warning-bg-subtle',
                        nodeBGColorHover: '--dx-warning-border-subtle',
                    },
                },
            ],
        },

        {
            id: 'Lily_Chen',
            data: {
                name: 'لیلی چن',
                imageURL: 'assets/images/avatar/user-8.png',
            },
            options: {
                nodeBGColor: '--dx-orange-bg-subtle',
                nodeBGColorHover: '--dx-orange-border-subtle',
            },
            children: [
                {
                    id: 'Jake_Scott',
                    data: {
                        name: 'جیک اسکات',
                        imageURL: 'assets/images/avatar/user-7.png',
                    },
                    options: {
                        nodeBGColor: '--dx-pink-bg-subtle',
                        nodeBGColorHover: '--dx-pink-border-subtle',
                    },
                },
            ],
        },
        {
            id: 'Max_Ruiz',
            data: {
                name: 'مکس روئیز',
                imageURL: 'assets/images/avatar/user-5.png',
            },
            options: {
                nodeBGColor: '--dx-orange-bg-subtle',
                nodeBGColorHover: '--dx-orange-border-subtle',
            },
        },
    ],
};
const options = {
    contentKey: 'data',
    width: '100%',
    height: 600,
    nodeWidth: 150,
    nodeHeight: 70,
    childrenSpacing: 70,
    siblingSpacing: 30,
    fontColor: '--dx-body-color',
    borderColor: '--dx-border-color',
    edgeColor: '--dx-border-color',
    edgeColorHover: '--dx-primary',
    tooltipBorderColor: '--dx-border-color',
    direction: 'right',
    nodeTemplate: (content) => {
        return `<div class="d-flex flex-row justify-content-center align-items-center h-100 px-3 gap-2">
      <img class="rounded-circle size-10 flex-shrink-0" src='${content.imageURL}' alt='${content.name}'>
      <h6 class="mb-0">${content.name}</h6>
     </div>`;
    },
    canvasStyle: 'border: 1px solid var(--dx-border-color);background: var(--dx-secondary-bg);',
};
allCharts.push([{ 'id': 'rightToLeftChart', 'data': options, renderData: data }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });