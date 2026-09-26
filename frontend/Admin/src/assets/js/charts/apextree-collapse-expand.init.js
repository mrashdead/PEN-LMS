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
        imageURL: 'assets/images/avatar/user-no.png',
        name: 'جمشید بهاری‌فر',
    },
    options: {
        nodeBGColor: '--dx-primary',
        nodeBGColorHover: '--dx-primary',
        borderColor: '--dx-primary',
        borderColorHover: '--dx-primary',
    },
    children: [
        {
            id: 'mh',
            data: {
                imageURL: 'assets/images/avatar/user-14.png',
                name: 'مهدی هاشمی',
            },
            options: {
                nodeBGColor: '--dx-pink',
                nodeBGColorHover: '--dx-pink',
                borderColor: '--dx-pink',
                borderColorHover: '--dx-pink',
            },
            children: [
                {
                    id: 'kb',
                    data: {
                        imageURL: 'assets/images/avatar/user-11.png',
                        name: 'کریم باقری',
                    },
                    options: {
                        nodeBGColor: '--dx-success',
                        nodeBGColorHover: '--dx-success',
                        borderColor: '--dx-success',
                        borderColorHover: '--dx-success',
                    },
                },
                {
                    id: 'cr',
                    data: {
                        imageURL: 'assets/images/avatar/user-10.png',
                        name: 'کریس رونالدو',
                    },
                    options: {
                        nodeBGColor: '--dx-success',
                        nodeBGColorHover: '--dx-success',
                        borderColor: '--dx-success',
                        borderColorHover: '--dx-success',
                    },
                },
            ],
        },
        {
            id: 'cs',
            data: {
                imageURL: 'assets/images/avatar/user-9.png',
                name: 'لیلا حاتمی',
            },
            options: {
                nodeBGColor: '--dx-danger',
                nodeBGColorHover: '--dx-danger',
                borderColor: '--dx-danger',
                borderColorHover: '--dx-danger',
            },
            children: [
                {
                    id: 'Noah_Chandler',
                    data: {
                        imageURL: 'assets/images/avatar/user-7.png',
                        name: 'نوح چندلر',
                    },
                    options: {
                        nodeBGColor: '--dx-warning',
                        nodeBGColorHover: '--dx-warning',
                        borderColor: '--dx-warning',
                        borderColorHover: '--dx-warning',
                    },
                },
                {
                    id: 'Felix_King',
                    data: {
                        imageURL: 'assets/images/avatar/user-5.png',
                        name: 'فلیکس کینگ',
                    },
                    options: {
                        nodeBGColor: '--dx-warning',
                        nodeBGColorHover: '--dx-warning',
                        borderColor: '--dx-warning',
                        borderColorHover: '--dx-warning',
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
    fontColor: '--dx-white',
    borderColor: '--dx-border-color',
    edgeColor: '--dx-border-color',
    edgeColorHover: '--dx-primary',
    tooltipBorderColor: '--dx-border-color',
    childrenSpacing: 50,
    siblingSpacing: 20,
    direction: 'top',
    enableExpandCollapse: true,
    nodeTemplate: (content) =>
        `<div class="d-flex flex-column justify-content-center align-items-center h-100 px-3 gap-2">
      <img class="rounded-circle size-10 flex-shrink-0" src='${content.imageURL}' alt='${content.name}' />
      <h6 class="mb-0">${content.name}</h6>
     </div>`,
    canvasStyle: 'border: 1px solid var(--dx-border-color);background: var(--dx-secondary-bg);',
    enableToolbar: true,
};

allCharts.push([{ 'id': 'collapseExpandChart', 'data': options, renderData: data }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });
