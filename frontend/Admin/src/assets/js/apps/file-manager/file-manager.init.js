import * as echarts from 'echarts';

// ====== Theme and Chart Handling ======
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

        var dom = document.getElementById(chart[0].id);

        if (!dom) {
            return;
        }

        // Dispose of the existing chart if it exists to prevent memory leaks
        if (chart[0].chart) {
            chart[0].chart.dispose();
        }

        // Create a new chart instance
        var chartInstance = echarts.init(dom);
        chart[0].chart = chartInstance;

        if (data && typeof data === 'object') {
            chartInstance.setOption(data);
        }
    });
}

function renderCharts(val) {
    // Clear any pending timeouts to prevent race conditions
    if (window.chartUpdateTimeout) {
        clearTimeout(window.chartUpdateTimeout);
    }

    // Use a timeout to ensure the DOM has been updated with new theme values
    window.chartUpdateTimeout = setTimeout(() => {
        updateAllCharts(val);
    }, 50); // Slight delay to ensure CSS variables have updated
}

// ====== Theme Event Listeners ======
document.addEventListener('DOMContentLoaded', function () {
    // Event listeners for radio buttons
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

    // Dark mode button event listener
    const darkModeButton = document.getElementById('darkModeButton');
    if (darkModeButton) {
        darkModeButton.addEventListener('click', function () {
            // Get the current theme or determine it from the document
            const currentTheme = document.documentElement.getAttribute('data-colors') ||
                document.documentElement.getAttribute('data-bs-theme');

            // Toggle between 'dark' and 'light' themes
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';

            // Update the theme attribute on the document
            document.documentElement.setAttribute('data-bs-theme', newTheme);

            // Update charts with the new theme
            renderCharts(newTheme);
        });
    }
});

// ====== Chart Configuration ======
// Basic Gauge Chart
var gaugeChartOption = {
    series: [
        {
            type: 'gauge',
            axisLine: {
                lineStyle: {
                    width: 20,
                    color: [
                        [0.3, '--dx-info'],
                        [0.7, '--dx-primary'],
                        [1, '--dx-danger']
                    ]
                }
            },
            pointer: {
                itemStyle: {
                    color: 'auto'
                }
            },
            grid: {
                top: '0%',
                left: '0%',
                right: '0%',
                bottom: '0%',
                containLabel: true
            },
            axisTick: {
                distance: -20,
                length: 8,
                lineStyle: {
                    color: '--dx-secondary-bg',
                    width: 2
                }
            },
            splitLine: {
                distance: -30,
                length: 30,
                lineStyle: {
                    color: '--dx-secondary-bg',
                    width: 4
                }
            },
            axisLabel: {
                color: 'inherit',
                distance: 25,
                fontSize: 12
            },
            detail: {
                valueAnimation: true,
                formatter: '{value} GB',
                fontSize: 16,
                color: 'inherit'
            },
            data: [
                {
                    value: 80
                }
            ]
        }
    ],
    grid: {
        top: '5%',
        left: '6%',
        right: '0%',
        bottom: '8%',
    }
};

allCharts.push([{ 'id': 'basicBarChart', 'data': gaugeChartOption }]);

// ====== Folder Management ======
const folders = [
    { id: 1, name: "مستندات من", details: "154 فایل" },
    { id: 2, name: "تصاویر", details: "547 تصویر" },
    { id: 3, name: "فایل قالب‌های طراحی", details: "364 فایل" },
    { id: 4, name: "دیگر فایل‌ها", details: "21 پوشه" }
];

let folderIdCounter = 5; // Start from 5 since 1-4 are already used
let folderToDelete = null;

let currentEditFolder = null; // Global variable to track which folder is being edited

function initFolderManagement() {
    const folderContainer = document.getElementById("folder-container");
    const folderCount = document.getElementById("folder-count");
    const folderNameInput = document.getElementById("folderNameInput");
    const addFolderBtn = document.querySelector('#createFolderModal .btn.btn-primary');
    const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
    const searchInput = document.getElementById("searchFileInput");
    const modalTitleElement = document.querySelector('#createFolderModal .modal-header h6');
    const createFolderModal = document.getElementById('createFolderModal');

    // Set initial folder count
    folderCount.textContent = folders.length;

    // Render initial folders
    folders.forEach(folder => {
        renderFolder(folder.id, folder.name, folder.details, folderContainer);
    });

    // Event listener for opening folder modal (both create and edit modes)
    createFolderModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;

        // Check if this is an edit operation
        if (button && button.classList.contains('edit-folder-btn')) {
            // Change modal title and button text for edit mode
            modalTitleElement.textContent = 'ویرایش پوشه';
            addFolderBtn.textContent = 'آپدیت پوشه';

            // Get folder data
            const folderCard = button.closest('.card');
            const folderName = folderCard.querySelector('h6 a').textContent;

            // Set the input value to current folder name
            folderNameInput.value = folderName;

            // Store reference to the folder being edited
            currentEditFolder = folderCard;
        } else {
            // Reset to create mode
            modalTitleElement.textContent = 'ایجاد پوشه';
            addFolderBtn.textContent = 'افزودن پوشه';
            folderNameInput.value = '';
            currentEditFolder = null;
        }
    });

    // Create/Edit folder functionality
    addFolderBtn.addEventListener("click", () => {
        const folderName = folderNameInput.value.trim();
        if (folderName === "") {
            alert("لطفاً نام پوشه را وارد نمایید.");
            return;
        }

        if (currentEditFolder) {
            // Update existing folder
            currentEditFolder.querySelector('h6 a').textContent = folderName;
            currentEditFolder = null;
        } else {
            // Create new folder
            renderFolder(folderIdCounter++, folderName, "0 فایل", folderContainer);
        }

        folderNameInput.value = "";

        // Close modal using Bootstrap's modal hide
        const modal = window.bootstrap.Modal.getInstance(document.getElementById("createFolderModal"));
        modal.hide();
    });

    // Click event delegation for folder container
    folderContainer.addEventListener("click", function (e) {
        // Handle delete button click
        if (e.target.closest("[data-bs-target='#deleteModal']")) {
            const card = e.target.closest(".col-md-6");
            folderToDelete = card;
        }
    });

    confirmDeleteBtn.addEventListener("click", () => {
        if (folderToDelete) {
            folderToDelete.remove();
            updateFolderCount(folderContainer, folderCount);
            folderToDelete = null;
        }
    });

    // Search functionality
    searchInput.addEventListener("input", () => {
        const query = searchInput.value.toLowerCase();
        const folderElements = folderContainer.querySelectorAll(".col-md-6");

        folderElements.forEach(folder => {
            const folderName = folder.querySelector("h6 a").textContent.toLowerCase();
            const match = folderName.includes(query);
            folder.style.display = match ? "" : "none";
        });

        // Update count based on visible folders
        const visibleFolders = [...folderElements].filter(folder => folder.style.display !== "none");
        folderCount.textContent = visibleFolders.length;
    });
}

function renderFolder(id, name, details, container) {
    const col = document.createElement("div");
    col.className = "col-md-6 col-xxl-3";

    col.innerHTML = `
    <div class="card">
      <div class="card-body">
        <div class="dropdown float-end">
          <a href="#!" class="link link-custom-primary" type="button" id="folderDropdownMenuButton${id}" aria-label="Toggle dropdown" data-bs-toggle="dropdown" aria-expanded="false">
            <i class="ri-more-2-fill"></i>
          </a>
          <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="folderDropdownMenuButton${id}">
            <li>
              <a href="#!" class="dropdown-item edit-folder-btn" data-bs-toggle="modal" data-bs-target="#createFolderModal">
                باز کردن پوشه
              </a>
            </li>
            <li>
              <a href="#!" class="dropdown-item" data-bs-toggle="modal" data-bs-target="#deleteModal">
                حذف
              </a>
            </li>
          </ul>
        </div>
        <img src="assets/images/file-manager/icons/folder.png" loading="lazy" alt="">
        <div class="mt-4">
          <h6 class="mb-1"><a href="#!" class="text-reset">${name}</a></h6>
          <p class="fs-sm text-muted">${details}</p>
        </div>
      </div>
    </div>
  `;

    container.appendChild(col);
    updateFolderCount(container, document.getElementById("folder-count"));
}

function updateFolderCount(container, countElement) {
    countElement.textContent = container.children.length;
}

// ====== Initialize Application ======
document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts
    updateAllCharts();

    // Initialize folder management
    initFolderManagement();

    // Handle window resize for responsive charts
    window.addEventListener('resize', () => {
        if (window.resizeTimeout) {
            clearTimeout(window.resizeTimeout);
        }
        window.resizeTimeout = setTimeout(() => {
            updateAllCharts();
        }, 250); // Debounce resize events
    });
});