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

//basic chart
var option;
option = {
  textStyle: {
    fontFamily: "Vazir",
    fontWeight: 400
  },
  tooltip: {
    trigger: 'item',
    textStyle: {
      fontFamily: "Vazir",
      fontWeight: 400
    }
  },
  legend: {
    orient: 'vertical',
    left: 'left',
    textStyle: {
      color: "--dx-secondary-color",
      fontFamily: "Vazir",
      fontWeight: 400
    }
  },
  color: ["--dx-primary", "--dx-success", "--dx-warning", "--dx-secondary", "--dx-orange"],
  series: [
    {
      name: 'دسترسی از',
      type: 'pie',
      radius: '50%',
      label: {
        fontFamily: "Vazir",
        fontWeight: 400
      },
      emphasis: {
        label: {
          fontFamily: "Vazir",
          fontWeight: 400
        }
      },
      data: [
        { value: 1048, name: 'موتور جستجو' },
        { value: 735, name: 'دایرکت' },
        { value: 580, name: 'ایمیل' },
        { value: 484, name: 'تبلیغات اتحادیه' },
        { value: 300, name: 'تبلیغات ویدئویی' }
      ],
    }
  ]
};

allCharts.push([{ 'id': 'basicPieChart', 'data': option }]);

//Doughnut Chart with Rounded Corner
option = {
  textStyle: {
    fontFamily: "Vazir",
    fontWeight: 400
  },
  tooltip: {
    trigger: 'item',
    textStyle: {
      fontFamily: "Vazir",
      fontWeight: 400
    }
  },
  legend: {
    top: '5%',
    left: 'center',
    textStyle: {
      color: "--dx-body-color",
      fontFamily: "Vazir",
      fontWeight: 400
    }
  },
  series: [
    {
      name: 'دسترسی از',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: "--dx-secondary-bg",
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center',
        fontFamily: "Vazir",
        fontWeight: 400
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold',
          fontFamily: "Vazir"
        }
      },
      labelLine: {
        show: false
      },
      color: ["--dx-primary-border-subtle", "--dx-success-border-subtle", "--dx-pink-border-subtle", "--dx-secondary-border-subtle", "--dx-orange-border-subtle"],
      data: [
        { value: 1048, name: 'موتور جستجو' },
        { value: 735, name: 'دایرکت' },
        { value: 580, name: 'ایمیل' },
        { value: 484, name: 'تبلیغات اتحادیه' },
        { value: 300, name: 'تبلیغات ویدئویی' }
      ]
    }
  ]
};

allCharts.push([{ 'id': 'doughnutRoundedPieChart', 'data': option }]);

//Doughnut Chart
option = {
  textStyle: {
    fontFamily: "Vazir",
    fontWeight: 400
  },
  tooltip: {
    trigger: 'item',
    textStyle: {
      fontFamily: "Vazir",
      fontWeight: 400
    }
  },
  legend: {
    top: '5%',
    left: 'center',
    textStyle: {
      color: "--dx-body-color",
      fontFamily: "Vazir",
      fontWeight: 400
    }
  },
  series: [
    {
      name: 'دسترسی از',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      label: {
        show: false,
        position: 'center',
        fontFamily: "Vazir",
        fontWeight: 400
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold',
          fontFamily: "Vazir"
        }
      },
      labelLine: {
        show: false
      },
      data: [
        { value: 1048, name: 'موتور جستجو' },
        { value: 735, name: 'دایرکت' },
        { value: 580, name: 'ایمیل' },
        { value: 484, name: 'تبلیغات اتحادیه' },
        { value: 300, name: 'تبلیغات ویدئویی' }
      ]
    }
  ]
};

allCharts.push([{ 'id': 'doughnutPieChart', 'data': option }]);

//Half Doughnut Chart
option = {
  textStyle: {
    fontFamily: "Vazir",
    fontWeight: 400
  },
  tooltip: {
    trigger: 'item',
    textStyle: {
      fontFamily: "Vazir",
      fontWeight: 400
    }
  },
  legend: {
    top: '5%',
    left: 'center',
    textStyle: {
      color: "--dx-body-color",
      fontFamily: "Vazir",
      fontWeight: 400
    }
  },
  series: [
    {
      name: 'دسترسی از',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '70%'],
      // adjust the start and end angle
      startAngle: 180,
      endAngle: 360,
      label: {
        fontFamily: "Vazir",
        fontWeight: 400
      },
      emphasis: {
        label: {
          fontFamily: "Vazir",
          fontWeight: 400
        }
      },
      data: [
        { value: 1048, name: 'موتور جستجو' },
        { value: 735, name: 'دایرکت' },
        { value: 580, name: 'ایمیل' },
        { value: 484, name: 'تبلیغات اتحادیه' },
        { value: 300, name: 'تبلیغات ویدئویی' }
      ]
    }
  ]
};

allCharts.push([{ 'id': 'halfDouglasNutChart', 'data': option }]);

function makeChartsResponsive() {
  allCharts.forEach(chartData => {
    const chartDom = document.getElementById(chartData[0].id);
    if (chartDom) {
      // Make chart container responsive
      chartDom.style.width = '100%';
      chartDom.style.height = '100%';
      chartDom.style.minHeight = '300px';

      // Apply responsive legend to all charts
      if (chartData[0].data && chartData[0].data.legend) {
        // For smaller screens
        if (window.innerWidth < 768) {
          chartData[0].data.legend.orient = 'horizontal';
          chartData[0].data.legend.left = 'center';
          chartData[0].data.legend.top = '0%';
          chartData[0].data.legend.itemGap = 10;
          chartData[0].data.legend.textStyle = {
            ...chartData[0].data.legend.textStyle,
            fontSize: 12
          };
        } else {
          // For larger screens - restore original settings if needed
          if (chartData[0].id.includes('doughnut') || chartData[0].id.includes('halfDouglas')) {
            chartData[0].data.legend.top = '5%';
            chartData[0].data.legend.left = 'center';
          }
        }
      }
    }
  });

  // Update all charts with new configurations
  updateAllCharts();
}

// Call this function on page load and window resize
window.addEventListener('DOMContentLoaded', makeChartsResponsive);
window.addEventListener('resize', () => {
  setTimeout(makeChartsResponsive, 0);
});

window.addEventListener('DOMContentLoaded', () => {
  updateAllCharts();
});

window.addEventListener('resize', () => { setTimeout(() => { updateAllCharts(); }, 0) });