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
    id: 'ms',
    data: {
        imageURL: 'assets/images/avatar/user-17.png',
        name: 'جمشید بهاری‌فر',
    },
    options: {
        nodeBGColor: '--dx-primary-bg-subtle',
        nodeBGColorHover: '--dx-primary-border-subtle',
    },
    children: [
        {
            id: 'mh',
            data: {
                imageURL: 'https://i.pravatar.cc/300?img=69',
                name: 'مهدی هاشمی',
            },
            options: {
                nodeBGColor: '--dx-secondary-bg-subtle',
                nodeBGColorHover: '--dx-secondary-border-subtle',
            },
            children: [
                {
                    id: 'kb',
                    data: {
                        imageURL: 'https://i.pravatar.cc/300?img=65',
                        name: 'کریم باقری',
                    },
                    options: {
                        nodeBGColor: '--dx-success-bg-subtle',
                        nodeBGColorHover: '--dx-success-border-subtle',
                    }
                },
                {
                    id: 'cr',
                    data: {
                        imageURL: 'https://i.pravatar.cc/300?img=60',
                        name: 'کریس رونالدو',
                    },
                    options: {
                        nodeBGColor: '--dx-warning-bg-subtle',
                        nodeBGColorHover: '--dx-warning-border-subtle',
                    },
                },
            ],
        },
        {
            id: 'cs',
            data: {
                imageURL: 'https://i.pravatar.cc/300?img=59',
                name: 'لیلا حاتمی',
            },
            options: {
                nodeBGColor: '--dx-indigo-bg-subtle',
                nodeBGColorHover: '--dx-indigo-border-subtle',
            },
            children: [
                {
                    id: 'Noah_Chandler',
                    data: {
                        imageURL: 'https://i.pravatar.cc/300?img=57',
                        name: 'نوح چندلر',
                    },
                    options: {
                        nodeBGColor: '--dx-orange-bg-subtle',
                        nodeBGColorHover: '--dx-orange-border-subtle',
                    },
                },
                {
                    id: 'Felix_King',
                    data: {
                        imageURL: 'https://i.pravatar.cc/300?img=52',
                        name: 'فلیکس کینگ',
                    },
                    options: {
                        nodeBGColor: '--dx-pink-bg-subtle',
                        nodeBGColorHover: '--dx-pink-border-subtle',
                    },
                },
            ],
        },
    ],
};

const options = {
    contentKey: 'data',
    width: '100%',
    height: 600,
    nodeWidth: 150,
    nodeHeight: 100,
    fontColor: '--dx-body-color',
    borderColor: '--dx-border-color',
    edgeColor: '--dx-border-color',
    edgeColorHover: '--dx-primary',
    tooltipBorderColor: '--dx-border-color',
    childrenSpacing: 50,
    siblingSpacing: 20,
    direction: 'top',
    nodeTemplate: (content) =>
        `<div class="d-flex gap-3 flex-column justify-content-center align-items-center h-100">
      <img style='width: 50px;height: 50px;border-radius: 50%;' src='${content.imageURL}' alt='' />
      <h6 class="text-reset fs-13">${content.name}</h6>
     </div>`,
    canvasStyle: 'border: 1px solid var(--dx-border-color);background: var(--dx-secondary-bg);',
    enableToolbar: true,
};

allCharts.push([{ 'id': 'topToBottomChart', 'data': options, renderData: data }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });