import ApexSankey from 'apexsankey';

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
        var chart2 = new ApexSankey(document.getElementById(chart[0].id), data);
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

//basic Chart
const data = {
    nodes: [
    {
        id: 'Oil',
        title: 'نفت',
    },
    {
        id: 'Natural Gas',
        title: 'گاز طبیعی',
    },
    {
        id: 'Coal',
        title: 'زغال‌سنگ',
    },
    {
        id: 'Fossil Fuels',
        title: 'سوخت‌های فسیلی',
    },
    {
        id: 'Electricity',
        title: 'برق',
    },
    {
        id: 'Energy',
        title: 'انرژی',
    },
    ],
    edges: [
        {
            source: 'Oil',
            target: 'Fossil Fuels',
            value: 15,
        },
        {
            source: 'Natural Gas',
            target: 'Fossil Fuels',
            value: 20,
        },
        {
            source: 'Coal',
            target: 'Fossil Fuels',
            value: 25,
        },
        {
            source: 'Coal',
            target: 'Electricity',
            value: 25,
        },
        {
            source: 'Fossil Fuels',
            target: 'Energy',
            value: 60,
        },
        {
            source: 'Electricity',
            target: 'Energy',
            value: 25,
        },
    ],
};
const graphOptions = {
    nodeWidth: 20,
    fontWeight: '500',
    fontSize: '10px',
    height: '200px',
    enableToolbar: true,
    fontColor: '--dx-body-color',
    tooltipBGColor: '--dx-secondary-bg',
    tooltipBorderColor: '--dx-border-color',
    canvasStyle: 'border: 1px solid var(--dx-border-color); background: var(--dx-secondary-bg);',
};

allCharts.push([{ 'id': 'basicSankey', 'data': graphOptions, renderData: data }]);

const data2 = {
    nodes: [
    { id: 'Applications', title: 'درخواست‌ها' },
    { id: 'Accepted', title: 'پذیرفته‌شده' },
    { id: 'Rejected', title: 'ردشده' },
    { id: 'In Progress', title: 'در حال بررسی' },

    { id: 'Software Engineering', title: 'مهندسی نرم‌افزار' },
    { id: 'Data Science', title: 'علم داده' },
    { id: 'Marketing', title: 'بازاریابی' },
    { id: 'Sales', title: 'فروش' },
    { id: 'HR', title: 'منابع انسانی' },
    { id: 'Finance', title: 'مالی' },

    { id: 'Internship', title: 'کارآموزی' },
    { id: 'Junior', title: 'جونیور' },
    { id: 'Mid-level', title: 'سطح متوسط' },
    { id: 'Senior', title: 'سینیور' },
    { id: 'Entry Level', title: 'سطح ورودی' },
    { id: 'Full-time', title: 'تمام‌وقت' },
    { id: 'Part-time', title: 'پاره‌وقت' },
    ],
    edges: [
        { source: 'Applications', target: 'Accepted', value: 10 },
        { source: 'Applications', target: 'Rejected', value: 15 },
        { source: 'Applications', target: 'In Progress', value: 10 },

        { source: 'Accepted', target: 'Software Engineering', value: 4 },
        { source: 'Accepted', target: 'Data Science', value: 2 },
        { source: 'Accepted', target: 'Marketing', value: 1 },
        { source: 'Accepted', target: 'Sales', value: 1 },
        { source: 'Accepted', target: 'HR', value: 1 },
        { source: 'Accepted', target: 'Finance', value: 1 },
        { source: 'Rejected', target: 'Software Engineering', value: 5 },
        { source: 'Rejected', target: 'Data Science', value: 3 },
        { source: 'Rejected', target: 'Marketing', value: 2 },
        { source: 'Rejected', target: 'Sales', value: 2 },
        { source: 'Rejected', target: 'HR', value: 2 },
        { source: 'Rejected', target: 'Finance', value: 1 },
        { source: 'In Progress', target: 'Software Engineering', value: 3 },
        { source: 'In Progress', target: 'Data Science', value: 2 },
        { source: 'In Progress', target: 'Marketing', value: 2 },
        { source: 'In Progress', target: 'Sales', value: 1 },
        { source: 'In Progress', target: 'HR', value: 1 },
        { source: 'In Progress', target: 'Finance', value: 1 },
        { source: 'Software Engineering', target: 'Internship', value: 1 },
        { source: 'Software Engineering', target: 'Junior', value: 1 },
        { source: 'Software Engineering', target: 'Mid-level', value: 1 },
        { source: 'Software Engineering', target: 'Senior', value: 1 },
        { source: 'Software Engineering', target: 'Entry Level', value: 1 },
        { source: 'Data Science', target: 'Internship', value: 1 },
        { source: 'Data Science', target: 'Junior', value: 1 },
        { source: 'Data Science', target: 'Mid-level', value: 1 },
        { source: 'Data Science', target: 'Senior', value: 1 },
        { source: 'Data Science', target: 'Entry Level', value: 1 },
        { source: 'Marketing', target: 'Internship', value: 1 },
        { source: 'Marketing', target: 'Junior', value: 1 },
        { source: 'Marketing', target: 'Mid-level', value: 1 },
        { source: 'Marketing', target: 'Senior', value: 1 },
        { source: 'Marketing', target: 'Entry Level', value: 1 },
        { source: 'Sales', target: 'Internship', value: 1 },
        { source: 'Sales', target: 'Junior', value: 1 },
        { source: 'Sales', target: 'Mid-level', value: 1 },
        { source: 'Sales', target: 'Senior', value: 1 },
        { source: 'Sales', target: 'Entry Level', value: 1 },
        { source: 'HR', target: 'Internship', value: 1 },
        { source: 'HR', target: 'Junior', value: 1 },
        { source: 'HR', target: 'Mid-level', value: 1 },
        { source: 'HR', target: 'Senior', value: 1 },
        { source: 'HR', target: 'Entry Level', value: 1 },
        { source: 'Finance', target: 'Internship', value: 1 },
        { source: 'Finance', target: 'Junior', value: 1 },
        { source: 'Finance', target: 'Mid-level', value: 1 },
        { source: 'Finance', target: 'Senior', value: 1 },
        { source: 'Finance', target: 'Entry Level', value: 1 },
        { source: 'Internship', target: 'Full-time', value: 1 },
        { source: 'Internship', target: 'Part-time', value: 1 },
        { source: 'Junior', target: 'Full-time', value: 1 },
        { source: 'Junior', target: 'Part-time', value: 1 },
        { source: 'Mid-level', target: 'Full-time', value: 1 },
        { source: 'Mid-level', target: 'Part-time', value: 1 },
        { source: 'Senior', target: 'Full-time', value: 1 },
        { source: 'Senior', target: 'Part-time', value: 1 },
        { source: 'Entry Level', target: 'Full-time', value: 1 },
        { source: 'Entry Level', target: 'Part-time', value: 1 },
    ],
};
const graphOptions2 = {
    height: '250px',
    fontSize: '10px',
    fontWeight: '500',
    nodeWidth: 5,
    nodeBorderWidth: 2,
    nodeBorderColor: '--dx-border-color',
    edgeGradientFill: false,
    fontColor: '--dx-body-color',
    tooltipBGColor: '--dx-secondary-bg',
    tooltipBorderColor: '--dx-border-color',
    canvasStyle: 'border: 1px solid var(--dx-border-color); background: var(--dx-secondary-bg);',
};

allCharts.push([{ 'id': 'nodeCustomization', 'data': graphOptions2, renderData: data2 }]);

// edge charts
const data3 = {
    nodes: [
    { id: 'England', title: 'انگلستان' },
    { id: 'Wales', title: 'ولز' },

    { id: 'Level 4', title: 'سطح 4' },
    { id: 'Level 3', title: 'سطح 3' },
    { id: 'Level 2', title: 'سطح 2' },
    { id: 'Level 1 and entry level', title: 'سطح 1 و ورودی' },
    { id: 'No qualifications', title: 'فاقد مدرک' },
    { id: 'Other', title: 'سایر' },

    { id: 'Wholesale & retail', title: 'عمده‌فروشی و خرده‌فروشی' },
    { id: 'Health & social work', title: 'بهداشت و خدمات اجتماعی' },
    { id: 'Education', title: 'آموزش' },
    { id: 'Construction', title: 'ساخت‌وساز' },
    { id: 'Manufacturing', title: 'تولید' },
    { id: 'Transport & storage', title: 'حمل‌ونقل و انبارداری' },
    { id: 'Finance & insurance', title: 'مالی و بیمه' },
    ],
    edges: [
        { source: 'England', target: 'Level 4', value: 13 },
        { source: 'England', target: 'Level 3', value: 8 },
        { source: 'England', target: 'Level 2', value: 8 },
        { source: 'England', target: 'Level 1 and entry level', value: 6 },
        { source: 'England', target: 'No qualifications', value: 3 },
        // { source: 'England', target: 'Other', value: 4 },
        { source: 'Wales', target: 'Level 4', value: 7 },
        { source: 'Wales', target: 'Level 3', value: 8 },
        { source: 'Wales', target: 'Level 2', value: 4 },
        { source: 'Wales', target: 'Level 1 and entry level', value: 5 },
        { source: 'Wales', target: 'No qualifications', value: 5 },
        // { source: 'Wales', target: 'Other', value: 3 },
        { source: 'Level 4', target: 'Wholesale & retail', value: 4 },
        { source: 'Level 4', target: 'Health & social work', value: 3 },
        { source: 'Level 4', target: 'Education', value: 2 },
        { source: 'Level 4', target: 'Construction', value: 1 },
        { source: 'Level 4', target: 'Manufacturing', value: 2 },
        { source: 'Level 4', target: 'Other', value: 3 },
        { source: 'Level 4', target: 'Transport & storage', value: 2 },
        { source: 'Level 4', target: 'Finance & insurance', value: 3 },

        { source: 'Level 3', target: 'Wholesale & retail', value: 3 },
        { source: 'Level 3', target: 'Health & social work', value: 2 },
        { source: 'Level 3', target: 'Education', value: 1 },
        { source: 'Level 3', target: 'Construction', value: 2 },
        { source: 'Level 3', target: 'Manufacturing', value: 1 },
        { source: 'Level 3', target: 'Other', value: 3 },
        { source: 'Level 3', target: 'Transport & storage', value: 2 },
        { source: 'Level 3', target: 'Finance & insurance', value: 2 },

        { source: 'Level 2', target: 'Wholesale & retail', value: 2 },
        { source: 'Level 2', target: 'Health & social work', value: 1 },
        { source: 'Level 2', target: 'Education', value: 2 },
        { source: 'Level 2', target: 'Construction', value: 1 },
        { source: 'Level 2', target: 'Manufacturing', value: 2 },
        { source: 'Level 2', target: 'Other', value: 2 },
        { source: 'Level 2', target: 'Transport & storage', value: 1 },
        { source: 'Level 2', target: 'Finance & insurance', value: 1 },

        { source: 'Level 1 and entry level', target: 'Wholesale & retail', value: 1 },
        { source: 'Level 1 and entry level', target: 'Health & social work', value: 2 },
        { source: 'Level 1 and entry level', target: 'Education', value: 1 },
        { source: 'Level 1 and entry level', target: 'Construction', value: 2 },
        { source: 'Level 1 and entry level', target: 'Manufacturing', value: 1 },
        { source: 'Level 1 and entry level', target: 'Other', value: 2 },
        { source: 'Level 1 and entry level', target: 'Transport & storage', value: 1 },
        { source: 'Level 1 and entry level', target: 'Finance & insurance', value: 1 },

        { source: 'No qualifications', target: 'Wholesale & retail', value: 1 },
        { source: 'No qualifications', target: 'Health & social work', value: 1 },
        { source: 'No qualifications', target: 'Education', value: 1 },
        { source: 'No qualifications', target: 'Construction', value: 1 },
        { source: 'No qualifications', target: 'Manufacturing', value: 1 },
        { source: 'No qualifications', target: 'Other', value: 1 },
        { source: 'No qualifications', target: 'Transport & storage', value: 1 },
        { source: 'No qualifications', target: 'Finance & insurance', value: 1 },
        // { source: 'Other', target: 'Wholesale & retail', value: 1 },
        // { source: 'Other', target: 'Health & social work', value: 1 },
        // { source: 'Other', target: 'Education', value: 1 },
        // { source: 'Other', target: 'Construction', value: 1 },
        // { source: 'Other', target: 'Manufacturing', value: 1 },
        // // { source: 'Other', target: 'Other', value: 1 },
        // { source: 'Other', target: 'Transport & storage', value: 1 },
        // { source: 'Other', target: 'Finance & insurance', value: 1 }
    ],
};
const graphOptions3 = {
    nodeWidth: 20,
    fontSize: '10px',
    height: '100%',
    fontWeight: '500',
    edgeOpacity: 0.2,
    fontColor: '--dx-body-color',
    tooltipBGColor: '--dx-secondary-bg',
    tooltipBorderColor: '--dx-border-color',
    canvasStyle: 'border: 1px solid var(--dx-border-color); background: var(--dx-secondary-bg);',
};

allCharts.push([{ 'id': 'edgeCustomization', 'data': graphOptions3, renderData: data3 }]);

const data4 = {
    nodes: [
        { id: 'Berlin', title: 'برلین' },
        { id: 'Job Applications', title: 'درخواست‌های شغلی' },
        { id: 'Barcelona', title: 'بارسلونا' },
        { id: 'Madrid', title: 'مادرید' },
        { id: 'Amsterdam', title: 'آمستردام' },
        { id: 'Paris', title: 'پاریس' },
        { id: 'London', title: 'لندن' },
        { id: 'Munich', title: 'مونیخ' },
        { id: 'Brussels', title: 'بروکسل' },
        { id: 'Dubai', title: 'دوبی' },
        { id: 'Dublin', title: 'دوبلین' },
        { id: 'Other Cities', title: 'دیگر شهر ها' },
        { id: 'No Response', title: 'بدون پاسخ' },
        { id: 'Responded', title: 'پاسخ داده شد' },
        { id: 'Rejected', title: 'رد شده' },
        { id: 'Interviewed', title: 'مصاحبه شده' },
        { id: 'No Offer', title: 'بدون پیشنهاد' },
        { id: 'Declined Offer', title: 'پیشنهاد رد شده' },
        { id: 'Accepted Offer', title: 'پیشنهاد پذیرفته شده' },
    ],
    edges: [
    {
        source: 'Berlin',
        target: 'Job Applications',
        value: 102,
        color: '#dddddd',
    },
    {
        source: 'Barcelona',
        target: 'Job Applications',
        value: 39,
        color: '#dddddd',
    },
    {
        source: 'Madrid',
        target: 'Job Applications',
        value: 35,
        color: '#dddddd',
    },
    {
        source: 'Amsterdam',
        target: 'Job Applications',
        value: 15,
        color: '#dddddd',
    },
    {
        source: 'Paris',
        target: 'Job Applications',
        value: 14,
        color: '#dddddd',
    },
    {
        source: 'London',
        target: 'Job Applications',
        value: 6,
        color: '#dddddd',
    },
    {
        source: 'Munich',
        target: 'Job Applications',
        value: 5,
        color: '#dddddd',
    },
    {
        source: 'Brussels',
        target: 'Job Applications',
        value: 4,
        color: '#dddddd',
    },
    {
        source: 'Dubai',
        target: 'Job Applications',
        value: 3,
        color: '#dddddd',
    },
    {
        source: 'Dublin',
        target: 'Job Applications',
        value: 3,
        color: '#dddddd',
    },
    {
        source: 'Other Cities',
        target: 'Job Applications',
        value: 12,
        color: '#dddddd',
    },
    {
        source: 'Job Applications',
        target: 'No Response',
        value: 189,
        color: '#dddddd',
    },
    {
        source: 'Job Applications',
        target: 'Responded',
        value: 49,
        color: 'orange',
    },
    {
        source: 'Responded',
        target: 'Rejected',
        value: 38,
        color: '#dddddd',
    },
    {
        source: 'Responded',
        target: 'Interviewed',
        value: 11,
        color: 'orange',
    },
    {
        source: 'Interviewed',
        target: 'No Offer',
        value: 8,
        color: '#dddddd',
    },
    {
        source: 'Interviewed',
        target: 'Offer Rejected',
        value: 2,
        color: '#dddddd',
    },
    {
        source: 'Interviewed',
        target: 'Offer Accepted',
        value: 1,
        color: 'orange',
    },
    ],
    options: {
        order: [
            [
                ['Berlin', 'Barcelona', 'Madrid', 'Amsterdam', 'Paris', 'London'],
                ['Munich', 'Brussels', 'Dubai', 'Dublin', 'Other Cities'],
            ],
            [['Job Applications']],
            [['Responded'], ['No Response']],
            [['Interviewed'], ['Rejected']],
            [['Offer Accepted', 'Offer Rejected', 'No Offer'], []],
        ],
    },
};
const graphOptions4 = {
    nodeWidth: 10,
    fontSize: '10px',
    height: '100%',
    fontFamily: '"Vazir", Satisfy, "cursive"',
    fontWeight: '500',
    fontColor: '--dx-orange',
    tooltipBGColor: '--dx-secondary-bg',
    tooltipBorderColor: '--dx-border-color',
    canvasStyle: 'border: 1px solid var(--dx-border-color); background: var(--dx-secondary-bg);',
};

allCharts.push([{ 'id': 'fontOptions', 'data': graphOptions4, renderData: data4 }]);

window.addEventListener('DOMContentLoaded', () => {
    updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });
