import { icons, createIcons } from "lucide";

document.addEventListener('DOMContentLoaded', function () {
    // Get the input field
    const newTaskInput = document.getElementById('newTaskInput');

    // Add event listener for the Enter key
    newTaskInput && newTaskInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && this.value.trim() !== '') {
            addNewTask(this.value.trim());
            this.value = ''; // Clear the input field
        }
    });

    // Add event listeners to existing checkboxes
    document.querySelectorAll('.form-check-input').forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const taskText = this.closest('.to-do-title').querySelector('span');
            if (taskText) {
                if (this.checked) {
                    taskText.classList.add('text-decoration-line-through');
                } else {
                    taskText.classList.remove('text-decoration-line-through');
                }
            }
        });
    });

    // Add event listeners to existing delete buttons
    document.querySelectorAll('.delete-button').forEach(deleteBtn => {
        deleteBtn.addEventListener('click', function (e) {
            e.preventDefault();
            const taskItem = this.closest('.todo-wrapper');
            taskItem && taskItem.remove();
            updateTaskCounts();
        });
    });

    // Add event listeners to existing edit buttons
    document.querySelectorAll('.edit-button').forEach(editBtn => {
        editBtn.addEventListener('click', function (e) {
            e.preventDefault();
            const taskText = this.closest('.d-flex.gap-2').previousElementSibling.querySelector('span');
            if (taskText) {
                const newText = prompt('ویرایش وظیفه:', taskText.textContent);
                if (newText !== null && newText.trim() !== '') {
                    taskText.textContent = newText.trim();
                }
            }
        });
    });

    // Function to add a new task
    function addNewTask(taskText) {
        const todaySection = document.getElementById('todayTasks');
        if (!todaySection) return;

        const taskList = todaySection;

        const newTask = document.createElement('div');
        newTask.className = 'd-flex justify-content-between align-items-center gap-5 mb-2 todo-wrapper';
        newTask.innerHTML = `
            <div class="d-flex align-items-center flex-grow-1 to-do-title">
                <div class="form-check check-primary">
                    <input class="form-check-input" type="checkbox">
                </div>
                <span class="ms-3 text-dark-emphasis">${taskText}</span>
            </div>
            <div class="d-flex gap-2">
                <a href="#!" class="link link-custom-warning edit-button">
                    <i class="ri-pencil-line"></i>
                </a>
                <a href="#!" class="link link-custom-danger delete-button">
                    <i class="ri-close-line"></i>
                </a>
            </div>
        `;

        // Insert the new task at the top of the list
        if (taskList.children.length > 0) {
            taskList.insertBefore(newTask, taskList.children[1]);
        } else {
            taskList.appendChild(newTask);
        }

        // Add event listeners to the new task
        const newCheckbox = newTask.querySelector('.form-check-input');
        newCheckbox && newCheckbox.addEventListener('change', function () {
            const textElement = this.closest('.d-flex.align-items-center').querySelector('span');
            if (textElement) {
                if (this.checked) {
                    textElement.classList.add('text-decoration-line-through');
                } else {
                    textElement.classList.remove('text-decoration-line-through');
                }
            }
        });

        const newDeleteBtn = newTask.querySelector('.link-danger');
        newDeleteBtn && newDeleteBtn.addEventListener('click', function (e) {
            e.preventDefault();
            this.closest('.d-flex.justify-content-between')?.remove();
            updateTaskCounts();
        });

        const newEditBtn = newTask.querySelector('.link-warning');
        newEditBtn && newEditBtn.addEventListener('click', function (e) {
            e.preventDefault();
            const textElement = this.closest('.d-flex.gap-2').previousElementSibling.querySelector('span');
            if (textElement) {
                const newText = prompt('ویرایش وظیفه:', textElement.textContent);
                if (newText !== null && newText.trim() !== '') {
                    textElement.textContent = newText.trim();
                }
            }
        });

        updateTaskCounts();
    }

    // Function to update task counts in headings
    function updateTaskCounts() {
        ['todayTasks', 'yesterdayTasks'].forEach(id => {
            const section = document.getElementById(id);
            if (section) {
                const heading = section.querySelector('h6');
                if (heading) {
                    const tasks = section.querySelectorAll('.task-completed');
                    const count = tasks.length;
                    const currentText = heading.textContent.split(' (')[0];
                    heading.textContent = `${currentText} (${count})`;
                }
            }
        });
    }

    // Initialize task counts
    updateTaskCounts();
});

// Task Management Data
const taskData = [
    {
        taskName: "بررسی‌های امنیتی و انطباق",
        createDate: "16 اردیبهشت 1403",
        assignedTo: ["user-18", "user-20", "user-19"],
        status: "تکمیل شده",
        priority: "بالا"
    },
    {
        taskName: "مدیریت دسترسی کاربران",
        createDate: "20 مرداد 1403",
        assignedTo: ["user-30", "user-29"],
        status: "در انتظار",
        priority: "بالا"
    },
    {
        taskName: "یکپارچه‌سازی داده‌ها",
        createDate: "22 تیر 1403",
        assignedTo: ["user-22", "user-24", "user-15"],
        status: "تکمیل شده",
        priority: "بالا"
    },
    {
        taskName: "مصورسازی داده‌ها",
        createDate: "25 تیر 1403",
        assignedTo: ["user-25", "user-18"],
        status: "در انتظار",
        priority: "بالا"
    },
    {
        taskName: "شناسایی و دسترسی به منابع داده",
        createDate: "26 خرداد 1403",
        assignedTo: ["user-14", "user-16"],
        status: "جدید",
        priority: "بالا"
    },
    {
        taskName: "نگهداری سیستم",
        createDate: "31 خرداد 1403",
        assignedTo: ["user-21", "user-23"],
        status: "جدید",
        priority: "متوسط"
    },
    {
        taskName: "بهینه‌سازی فرانت‌اند",
        createDate: "5 تیر 1403",
        assignedTo: ["user-17"],
        status: "در انتظار",
        priority: "متوسط"
    },
    {
        taskName: "توسعه API بک‌اند",
        createDate: "12 تیر 1403",
        assignedTo: ["user-26", "user-27", "user-28"],
        status: "تکمیل شده",
        priority: "بالا"
    },
    {
        taskName: "تست پذیرش کاربر",
        createDate: "20 مرداد 1403",
        assignedTo: ["user-31", "user-32"],
        status: "جدید",
        priority: "بالا"
    }
];

// DOM Elements
document.addEventListener('DOMContentLoaded', function () {
    const tableBody = document.querySelector('tbody');
    const paginationContainer = document.querySelector('.pagination');
    const resultInfo = document.querySelector('.text-muted.text-center');

    // Pagination Configuration
    const itemsPerPage = 5;
    let currentPage = 1;

    // Initialize
    renderTable();
    setupPagination();
    updateResultInfo();

    // Render Table Function
    function renderTable() {
        // Clear table
        tableBody.innerHTML = '';

        // Calculate start and end index for current page
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, taskData.length);

        // Render rows for current page
        for (let i = startIndex; i < endIndex; i++) {
            const task = taskData[i];

            const row = document.createElement('tr');

            // Task Name Cell
            const taskNameCell = document.createElement('td');
            taskNameCell.textContent = task.taskName;
            row.appendChild(taskNameCell);

            // Create Date Cell
            const createDateCell = document.createElement('td');
            createDateCell.textContent = task.createDate;
            row.appendChild(createDateCell);

            // Assigned To Cell
            const assignedToCell = document.createElement('td');
            const avatarGroup = document.createElement('div');
            avatarGroup.className = 'avatar-group';

            task.assignedTo.forEach(userId => {
                const link = document.createElement('a');
                link.href = '#!';
                link.className = 'avatar-group-item';
                link.title = 'avatar-link';

                const img = document.createElement('img');
                img.src = `assets/images/avatar/${userId}.png`;
                img.loading = 'lazy';
                img.alt = userId;
                img.className = 'size-8';

                link.appendChild(img);
                avatarGroup.appendChild(link);
            });

            assignedToCell.appendChild(avatarGroup);
            row.appendChild(assignedToCell);

            // Status Cell
            const statusCell = document.createElement('td');
            const statusBadge = document.createElement('span');

            let statusClass = '';
            switch (task.status) {
                case 'تکمیل شده':
                    statusClass = 'bg-success-subtle text-success border border-success-subtle';
                    break;
                case 'در انتظار':
                    statusClass = 'bg-warning-subtle text-warning border border-warning-subtle';
                    break;
                default:
                    statusClass = 'bg-secondary-subtle text-secondary border border-secondary-subtle';
            }

            statusBadge.className = `badge ${statusClass}`;
            statusBadge.textContent = task.status;
            statusCell.appendChild(statusBadge);
            row.appendChild(statusCell);

            // Priority Cell
            const priorityCell = document.createElement('td');
            const priorityBadge = document.createElement('span');

            let priorityClass = '';
            switch (task.priority) {
                case 'بالا':
                    priorityClass = 'bg-danger-subtle text-danger border border-danger-subtle';
                    break;
                default:
                    priorityClass = 'bg-info-subtle text-info border border-info-subtle';
            }

            priorityBadge.className = `badge ${priorityClass}`;
            priorityBadge.textContent = task.priority;
            priorityCell.appendChild(priorityBadge);
            row.appendChild(priorityCell);

            // Action Cell
            const actionCell = document.createElement('td');
            actionCell.innerHTML = `
          <div class="dropdown">
              <a href="#!" class="link link-custom-primary" id="actionDropdownMenu${i + 1}" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="action dropdown">
                  <i class="ri-more-2-fill"></i>
              </a>
              <ul class="dropdown-menu" aria-labelledby="actionDropdownMenu${i + 1}">
                  <li><a class="dropdown-item" href="#">وظیفه جدید</a></li>
                  <li><a class="dropdown-item" href="#">ویرایش وظیفه</a></li>
                  <li><a class="dropdown-item" href="#">حذف وظیفه</a></li>
              </ul>
          </div>
        `;
            row.appendChild(actionCell);

            // Add row to table
            tableBody.appendChild(row);
        }
    }

    // Setup Pagination Function
    function setupPagination() {
        // Calculate total pages
        const totalPages = Math.ceil(taskData.length / itemsPerPage);

        // Clear pagination
        paginationContainer.innerHTML = '';

        // Previous Button
        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;

        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#!';
        prevLink.innerHTML = '<i data-lucide="chevron-right" class="size-4"></i> قبلی';

        prevLink.addEventListener('click', function (e) {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                updatePage();
            }
        });

        prevItem.appendChild(prevLink);
        paginationContainer.appendChild(prevItem);

        // Page Numbers
        for (let i = 1; i <= totalPages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${currentPage === i ? 'active' : ''}`;

            const pageLink = document.createElement('a');
            pageLink.className = 'page-link';
            pageLink.href = '#!';
            pageLink.textContent = i;

            pageLink.addEventListener('click', function (e) {
                e.preventDefault();
                currentPage = i;
                updatePage();
            });

            pageItem.appendChild(pageLink);
            paginationContainer.appendChild(pageItem);
        }

        // Next Button
        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;

        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#!';
        nextLink.innerHTML = 'بعدی <i data-lucide="chevron-left" class="size-4"></i>';

        nextLink.addEventListener('click', function (e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                currentPage++;
                updatePage();
            }
        });

        nextItem.appendChild(nextLink);
        paginationContainer.appendChild(nextItem);
        createIcons({ icons });
    }

    // Update Result Info Function
    function updateResultInfo() {
        const startIndex = (currentPage - 1) * itemsPerPage + 1;
        const endIndex = Math.min(currentPage * itemsPerPage, taskData.length);

        resultInfo.innerHTML = `نمایش <b class="me-1">${startIndex}-${endIndex}</b>از<b class="ms-1">${taskData.length}</b> نتیجه`;
    }

    // Update Page Function (calls all render functions)
    function updatePage() {
        renderTable();
        setupPagination();
        updateResultInfo();
    }
});