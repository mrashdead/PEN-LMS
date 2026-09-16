
//Sort By select
// Initialize VirtualSelect for sorting
document.addEventListener('DOMContentLoaded', function () {
    // Sort By select
    VirtualSelect.init({
        ele: "#sortBySelect",
        options: [
            { label: "همه", value: "All" },
            { label: "چهار گزینه‌ای", value: "MCQ" },
            { label: "تشریحی", value: "Q & A" },
            { label: "سخت", value: "Hard" },
            { label: "عادی", value: "Normal" },
            { label: "متوسط", value: "Medium" },
        ]
    });

    // Add event listener after initialization
    document.querySelector('#sortBySelect').addEventListener('change', function () {
        // Get the value directly from the element
        const sortValue = this.value;
        if (window.tableManager) {
            window.tableManager.filterQuestions(sortValue);
        }
    });
});

//Item Type select
VirtualSelect.init({
    ele: "#itemTypeSelect",
    options: [
        { label: "چهار گزینه‌ای", value: "MCQ" },
        { label: "تشریحی", value: "Q & A" },
    ],
});

//Difficult Level select
VirtualSelect.init({
    ele: "#difficultLevelSelect",
    options: [
        { label: "عادی", value: "Normal" },
        { label: "متوسط", value: "Medium" },
        { label: "سخت", value: "Hard" },
    ],
});

//Status select
VirtualSelect.init({
    ele: "#statusSelect",
    options: [
        { label: "تازه", value: "New" },
        { label: "قدیمی", value: "Old" }
    ],
});

// Filter based on the selected value
const difficultyMap = {
    Easy: "ساده",
    Medium: "متوسط",
    Hard: "سخت",
    Normal: "عادی"
};

const typeMap = {
    "Q & A": "تشریحی",
    "MCQ": "چهار گزینه‌ای"
};

const statusMap = {
    "New": "تازه",
    "Old": "قدیمی"
};

class TableManager {
    constructor() {
        this.questions = [];
        this.filteredQuestions = [];
        this.modals = {};
        this.currentId = 0;
        this.initializeModals();
        this.initializeEventListeners();
        this.initializeBulkActions();
        this.loadSampleData();
        window.tableManager = this;
    }
    /**
     * Initialize bulk selection and deletion functionality
     */
    initializeBulkActions() {
        const bulkDeleteBtn = document.querySelector('.btn-danger.btn-icon');
        if (!bulkDeleteBtn) {
            console.warn("Bulk delete button not found");
            return;
        }

        // Function to handle checkbox state changes
        const updateBulkActionVisibility = () => {
            const checkedBoxes = document.querySelectorAll('input[id^="checkData"]:checked');
            if (checkedBoxes.length > 0) {
                bulkDeleteBtn.classList.remove('d-none');
            } else {
                bulkDeleteBtn.classList.add('d-none');
            }
        };

        // Add click event to the bulk delete button
        bulkDeleteBtn.addEventListener('click', () => {
            const checkedBoxes = document.querySelectorAll('input[id^="checkData"]:checked');
            if (checkedBoxes.length === 0) return;

            // Show confirmation modal
            const deleteIdElement = document.getElementById('deleteQuestionId');
            if (deleteIdElement) {
                deleteIdElement.value = 'bulk'; // Special value for bulk delete

                // Update modal text to indicate multiple deletion
                const modalBodyText = document.querySelector('#deleteModal .modal-body p');
                if (modalBodyText) {
                    modalBodyText.textContent = `آیا مطمئن هستید که قصد دارید سؤالات انتخاب شده ${checkedBoxes.length} را حذف کنید؟`;
                }

                if (this.modals.deleteModal) {
                    this.modals.deleteModal.show();
                }
            }
        });

        // Monitor checkbox changes using event delegation
        document.addEventListener('change', (e) => {
            if (e.target.id === 'allCheckData' || e.target.id.startsWith('checkData')) {
                updateBulkActionVisibility();
            }
        });

        // Modify the confirmDeleteBtn handler to handle bulk deletion
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            // Remove existing event listeners
            const newConfirmBtn = confirmDeleteBtn.cloneNode(true);
            confirmDeleteBtn.parentNode.replaceChild(newConfirmBtn, confirmDeleteBtn);

            // Add new event listener
            newConfirmBtn.addEventListener('click', () => {
                const deleteIdElement = document.getElementById('deleteQuestionId');
                if (!deleteIdElement) return;

                const id = deleteIdElement.value;

                if (id === 'bulk') {
                    // Handle bulk delete
                    const checkedBoxes = document.querySelectorAll('input[id^="checkData"]:checked');
                    const idsToDelete = Array.from(checkedBoxes).map(checkbox => {
                        // Extract ID from the checkbox ID (format: checkData{id})
                        return parseInt(checkbox.id.replace('checkData', ''));
                    });

                    // Delete all selected questions
                    this.questions = this.questions.filter(q => !idsToDelete.includes(q.id));

                    // Reset the allCheckData checkbox
                    const allCheckData = document.getElementById('allCheckData');
                    if (allCheckData) {
                        allCheckData.checked = false;
                    }

                    // Hide the bulk delete button
                    const bulkDeleteBtn = document.querySelector('.btn-danger.btn-icon');
                    if (bulkDeleteBtn) {
                        bulkDeleteBtn.classList.add('d-none');
                    }

                    // Reset modal text
                    const modalBodyText = document.querySelector('#deleteModal .modal-body p');
                    if (modalBodyText) {
                        modalBodyText.textContent = 'آیا از حذف این سؤال مطمئن هستید؟';
                    }
                } else {
                    // Handle single delete
                    this.deleteQuestion(parseInt(id));
                }

                // Update filtered questions and render table
                this.applyCurrentFilters();
                this.renderTable();

                if (this.modals.deleteModal) {
                    this.modals.deleteModal.hide();
                }
            });
        }
    }

    /**
     * Initialize Bootstrap modals
     */
    initializeModals() {
        const modalElements = [
            'addQuestionModal',
            'overviewQuestionModal',
            'deleteModal'
        ];

        modalElements.forEach(id => {
            const modalElement = document.getElementById(id);
            if (modalElement) {
                this.modals[id] = new window.bootstrap.Modal(modalElement);

                // Reset form when modal is hidden
                if (id === 'addQuestionModal') {
                    modalElement.addEventListener('hidden.bs.modal', () => {
                        const form = document.getElementById('questionForm');
                        if (form) form.reset();

                        const questionId = document.getElementById('questionId');
                        if (questionId) questionId.value = '';

                        const modalTitle = document.getElementById('modalTitle');
                        if (modalTitle) modalTitle.textContent = 'افزودن سؤال';

                        const saveBtn = document.getElementById('saveQuestionBtn');
                        if (saveBtn) saveBtn.textContent = 'افزودن سؤال';
                    });
                }
            } else {
                console.warn(`Modal element with ID '${id}' not found in the DOM`);
            }
        });
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Create/Edit question button
        const createQuestionBtn = document.getElementById('createQuestionBtn');
        if (createQuestionBtn) {
            createQuestionBtn.addEventListener('click', () => {
                if (this.modals.addQuestionModal) {
                    this.modals.addQuestionModal.show();
                }
            });
        }

        // Form submission
        const questionForm = document.getElementById('questionForm');
        if (questionForm) {
            questionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveQuestion();
            });
        }

        // Search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchQuestions(e.target.value);
            });
        }

        const searchButton = document.getElementById('searchButton');
        if (searchButton) {
            searchButton.addEventListener('click', () => {
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    this.searchQuestions(searchInput.value);
                }
            });
        }

        // Sort functionality
        const sortBySelect = document.getElementById('sortBySelect');
        if (sortBySelect) {
            sortBySelect.addEventListener('change', (e) => {
                this.sortQuestions(e.target.value);
            });
        }

        // MCQ checkbox toggle
        const notAMcqCheck = document.getElementById('notAMcqCheck');
        if (notAMcqCheck) {
            notAMcqCheck.addEventListener('change', (e) => {
                const optionsContainer = document.getElementById('optionsContainer');
                if (optionsContainer) {
                    optionsContainer.style.display = e.target.checked ? 'none' : 'block';
                }

                // Update item type accordingly
                const itemTypeSelect = document.getElementById('itemTypeSelect');
                if (itemTypeSelect) {
                    itemTypeSelect.value = e.target.checked ? 'Q & A' : 'MCQ';
                }
            });
        }

        // Delete confirmation
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => {
                const deleteIdElement = document.getElementById('deleteQuestionId');
                if (deleteIdElement) {
                    const id = deleteIdElement.value;
                    this.deleteQuestion(parseInt(id));

                    if (this.modals.deleteModal) {
                        this.modals.deleteModal.hide();
                    }
                }
            });
        }

        // Select all checkbox
        const allCheckData = document.getElementById('allCheckData');
        if (allCheckData) {
            allCheckData.addEventListener('change', (e) => {
                const checkboxes = document.querySelectorAll('input[id^="checkData"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
            });
        }
    }

    /**
     * Load sample data
     */
    loadSampleData() {
        const sampleQuestions = [
            {
                id: 1,
                text: "عامل مهم سیستم اطلاعات مدیریت چیست؟",
                options: ["دیتا", "سیستم", "فرآیند", "همه موارد بالا"],
                type: "MCQ",
                difficulty: "Hard",
                status: "New"
            },
            {
                id: 2,
                text: "نمودار جریان داده، جزء اساسی سیستم …………… است.",
                options: ["مفهومی", "منطقی", "فیزیکی", "ترتیبی"],
                type: "MCQ",
                difficulty: "Hard",
                status: "New"
            },
            {
                id: 3,
                text: "یک ویژگی مطلوب ماژول چیست؟",
                options: ["استقلال", "انسجام کم", "اتصال زیاد", "چند منظوره"],
                type: "MCQ",
                difficulty: "Hard",
                status: "New"
            },
            {
                id: 4,
                text: "کدام یک از نمودارهای UML زیر دارای نمای ایستا است؟",
                options: ["نمودار همکاری", "نمودار مورد-کاربر", "نمودار وضعیت", "نمودار فعالیت"],
                type: "MCQ",
                difficulty: "Medium",
                status: "Old"
            },
            {
                id: 5,
                text: "شکل کامل HTML چیست؟",
                options: ["Hyper text markup language", "Hyphenation text markup language", "Hyphenation test marking language", "Hyper text marking language"],
                type: "MCQ",
                difficulty: "Hard",
                status: "New"
            },
            {
                id: 6,
                text: "آیا رابط کاربری/تجربه کاربری شغل خوبی است؟",
                options: [],
                type: "Q & A",
                difficulty: "Normal",
                status: "Old"
            }, {
                id: 7,
                text: "کدام یک از موارد زیر جزو انواع نگهداری نرم‌افزار نیست؟",
                options: ["اصلاحی", "تطبیقی", "پیشگیرانه", "انتخابی"],
                type: "MCQ",
                difficulty: "Medium",
                status: "New"
            },
            {
                id: 8,
                text: "کدام زبان عمدتاً برای برنامه‌نویسی هوش مصنوعی استفاده می‌شود؟",
                options: ["Python", "C++", "Java", "Pascal"],
                type: "MCQ",
                difficulty: "Hard",
                status: "New"
            },
            {
                id: 9,
                text: "متدولوژی چابک چیست؟",
                options: [],
                type: "Q & A",
                difficulty: "Normal",
                status: "Old"
            }
        ];

        this.questions = sampleQuestions;
        this.currentId = this.questions.length;
        this.filteredQuestions = [...this.questions];
        this.renderTable();
    }
    filterQuestions(filterValue) {
        // Reset to show all questions
        if (!filterValue || filterValue === 'All') {
            this.filteredQuestions = [...this.questions];
            this.renderTable();
            return;
        }

        this.filteredQuestions = this.questions.filter(question => {
            return question.difficulty === filterValue || 
                question.type === filterValue || 
                question.status === filterValue;
        });

        this.renderTable();
    }

    /**
     * Render table with questions
     */
    renderTable() {
        const tbody = document.getElementById('questionsTableBody');
        if (!tbody) {
            console.warn("Table body element not found");
            return;
        }

        tbody.innerHTML = '';
        const questionsToRender = this.filteredQuestions;

        if (questionsToRender.length === 0) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td colspan="7" class="text-center py-4">
                    <div class="d-flex flex-column align-items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" class="mx-auto size-12" viewBox="0 0 48 48">
                            <linearGradient id="SVGID_1__h35ynqzIJzH4_gr1" x1="34.598" x2="15.982" y1="15.982" y2="34.598" gradientUnits="userSpaceOnUse">
                                <stop offset="0" stop-color="#60e8fe"></stop>
                                <stop offset=".033" stop-color="#6ae9fe"></stop>
                                <stop offset=".197" stop-color="#97f0fe"></stop>
                                <stop offset=".362" stop-color="#bdf5ff"></stop>
                                <stop offset=".525" stop-color="#dafaff"></stop>
                                <stop offset=".687" stop-color="#eefdff"></stop>
                                <stop offset=".846" stop-color="#fbfeff"></stop>
                                <stop offset="1" stop-color="#fff"></stop>
                            </linearGradient>
                            <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164
                            S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331
                            c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3"
                            d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0
                            l-4.331-4.331"></path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3"
                            d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3"
                            d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                        </svg>
                        <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                        <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
            return;
        }

        questionsToRender.forEach((question, index) => {
            const tr = document.createElement('tr');

            // Checkbox column
            const tdCheckbox = document.createElement('td');
            tdCheckbox.innerHTML = `
                <div class="form-check check-primary">
                    <input class="form-check-input" type="checkbox" id="checkData${question.id}" aria-label="checkData${question.id}">
                </div>
            `;

            // Question column
            const tdQuestion = document.createElement('td');
            tdQuestion.innerHTML = `
                <a data-bs-toggle="collapse" href="#collapseQuestion${question.id}" class="text-reset fw-semibold">${question.text}</a>
                <div class="collapse" id="collapseQuestion${question.id}">
                    ${this.renderOptions(question)}
                </div>
            `;

            // Options column
            const tdOptions = document.createElement('td');
            tdOptions.innerHTML = `<a href="#collapseQuestion${question.id}" data-bs-toggle="collapse" class="text-dark link link-custom-primary">نمایش همه</a>`;

            // Type column
            const tdType = document.createElement('td');
            tdType.textContent = typeMap[question.type] || question.type;

            // Difficulty column
            const tdDifficulty = document.createElement('td');
            tdDifficulty.textContent = difficultyMap[question.difficulty] || question.difficulty;

            // Status column
            const tdStatus = document.createElement('td');
            const persianStatus = statusMap[question.status] || question.status;
            const statusClass = question.status === 'New' ?
                'badge bg-success-subtle text-success border border-success-subtle' :
                'badge bg-light-subtle text-dark border border-dark-subtle';
            tdStatus.innerHTML = `<span class="${statusClass}">${persianStatus}</span>`;

            // Action column
            const tdAction = document.createElement('td');
            tdAction.innerHTML = `
                <div class="dropdown">
                    <button class="btn btn-link text-dark p-0" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="dropdown-button">
                        <i class="ri-more-2-fill"></i>
                    </button>
                    <ul class="dropdown-menu">
                        <li>
                            <a href="#!" class="px-4 py-1 lh-lg d-flex gap-2 align-items-center link link-custom-primary overview-btn" data-id="${question.id}">
                                <i class="ri-eye-line"></i>
                                <span>نمای کلی</span>
                            </a>
                        </li>
                        <li>
                            <a href="#!" class="px-4 py-1 lh-lg d-flex gap-2 align-items-center link link-custom-primary edit-btn" data-id="${question.id}">
                                <i class="ri-pencil-line"></i>
                                ویرایش
                            </a>
                        </li>
                        <li>
                            <a href="#!" class="px-4 py-1 lh-lg d-flex gap-2 align-items-center link link-custom-danger delete-btn" data-id="${question.id}">
                                <i class="ri-delete-bin-line"></i>
                                <span>حذف</span>
                            </a>
                        </li>
                    </ul>
                </div>
            `;

            tr.appendChild(tdCheckbox);
            tr.appendChild(tdQuestion);
            tr.appendChild(tdOptions);
            tr.appendChild(tdType);
            tr.appendChild(tdDifficulty);
            tr.appendChild(tdStatus);
            tr.appendChild(tdAction);

            tbody.appendChild(tr);
        });

        // Add event listeners for action buttons
        this.addActionButtonListeners();
    }


    /**
     * Render options for a question
     */
    renderOptions(question) {
        if (question.type === 'MCQ') {
            let optionsHtml = '';
            const letters = ['الف', 'ب', 'ج', 'د'];

            question.options.forEach((option, index) => {
                optionsHtml += `
                    <div class="form-check radio-primary d-flex align-items-center gap-2 exam-question-check ps-0 ${index === 0 ? 'mt-3' : 'mt-2'}">
                        <input class="form-check-input d-none" type="radio" name="questionCheck${question.id}" id="questionMcq${question.id}${index}">
                        <label class="form-check-label size-10 d-flex align-items-center justify-content-center border rounded-2 text-center flex-shrink-0" for="questionMcq${question.id}${index}">
                            ${letters[index]}
                        </label>
                        <label for="questionMcq${question.id}${index}" class="h-10 form-control flex-grow-1 cursor-pointer">
                            ${option}
                        </label>
                    </div>
                `;
            });

            return optionsHtml;
        } else {
            return `
                <div class="mt-3">
                    <label for="qaInput${question.id}" class="form-label d-none">${question.text}</label>
                    <textarea class="form-control" id="qaInput${question.id}" rows="3" placeholder="پاسخ خود را بنویسید ..."></textarea>
                </div>
            `;
        }
    }

    /**
     * Add event listeners to action buttons
     */
    addActionButtonListeners() {
        // Overview buttons
        document.querySelectorAll('.overview-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const questionId = parseInt(btn.getAttribute('data-id'));
                this.showOverview(questionId);
            });
        });

        // Edit buttons
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const questionId = parseInt(btn.getAttribute('data-id'));
                this.editQuestion(questionId);
            });
        });

        // Delete buttons
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const questionId = parseInt(btn.getAttribute('data-id'));
                const deleteIdElement = document.getElementById('deleteQuestionId');
                if (deleteIdElement) {
                    deleteIdElement.value = questionId;

                    // Reset modal text to single delete
                    const modalBodyText = document.querySelector('#deleteModal .modal-body p');
                    if (modalBodyText) {
                        modalBodyText.textContent = 'آیا از حذف این سؤال مطمئن هستید؟';
                    }

                    if (this.modals.deleteModal) {
                        this.modals.deleteModal.show();
                    }
                }
            });
        });

        // Add click listeners for checkboxes to update state
        document.querySelectorAll('input[id^="checkData"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const checkedBoxes = document.querySelectorAll('input[id^="checkData"]:checked');
                const bulkDeleteBtn = document.querySelector('.btn-danger.btn-icon');

                if (bulkDeleteBtn) {
                    if (checkedBoxes.length > 0) {
                        bulkDeleteBtn.classList.remove('d-none');
                    } else {
                        bulkDeleteBtn.classList.add('d-none');
                    }
                }
            });
        });
    }

    /**
     * Show question overview
     */
    showOverview(id) {
        const question = this.questions.find(q => q.id === id);
        if (!question) return;

        const questionTextElement = document.getElementById('overviewQuestionText');
        if (!questionTextElement) {
            console.warn("Overview question text element not found");
            return;
        }

        questionTextElement.textContent = `سؤال ${id}. ${question.text}`;

        const optionContainer = document.getElementById('overviewOptionContainer');
        if (!optionContainer) {
            console.warn("Overview option container not found");
            return;
        }

        optionContainer.innerHTML = '';

        if (question.type === 'MCQ') {
            const letters = ['A', 'B', 'C', 'D'];
            question.options.forEach((option, index) => {
                optionContainer.innerHTML += `
                    <div class="form-check radio-primary d-flex align-items-center gap-2 exam-question-check ps-0 ${index === 0 ? 'mt-3' : 'mt-2'}">
                        <input class="form-check-input d-none" type="radio" name="questionCheck" id="questionMcqModal${index + 1}">
                        <label class="form-check-label size-10 d-flex align-items-center justify-content-center border rounded-2 text-center flex-shrink-0" for="questionMcqModal${index + 1}">
                            ${letters[index]}
                        </label>
                        <label for="questionMcqModal${index + 1}" class="h-10 form-control flex-grow-1 cursor-pointer">
                            ${option}
                        </label>
                    </div>
                `;
            });
        } else {
            optionContainer.innerHTML = `
                <div class="mt-3">
                    <textarea class="form-control" rows="3" placeholder="پاسخ خود را بنویسید ..."></textarea>
                </div>
            `;
        }

        if (this.modals.overviewQuestionModal) {
            this.modals.overviewQuestionModal.show();
        }
    }

    /**
     * Edit question
     */
    editQuestion(id) {
        const question = this.questions.find(q => q.id === id);
        if (!question) return;

        const questionIdElement = document.getElementById('questionId');
        const questionTextElement = document.getElementById('questionText');
        const notAMcqCheck = document.getElementById('notAMcqCheck');
        const optionsContainer = document.getElementById('optionsContainer');
        const itemTypeSelect = document.getElementById('itemTypeSelect');
        const difficultySelect = document.getElementById('difficultLevelSelect');
        const statusSelect = document.getElementById('statusSelect');
        const modalTitle = document.getElementById('modalTitle');
        const saveBtn = document.getElementById('saveQuestionBtn');

        if (questionIdElement) questionIdElement.value = question.id;
        if (questionTextElement) questionTextElement.value = question.text;

        if (question.type === 'MCQ') {
            if (notAMcqCheck) notAMcqCheck.checked = false;
            if (optionsContainer) optionsContainer.style.display = 'block';

            for (let i = 0; i < 4; i++) {
                const optionElement = document.getElementById(`option${i + 1}`);
                if (optionElement) optionElement.value = question.options[i] || '';
            }
        } else {
            if (notAMcqCheck) notAMcqCheck.checked = true;
            if (optionsContainer) optionsContainer.style.display = 'none';
        }

        if (itemTypeSelect) itemTypeSelect.value = question.type;
        if (difficultySelect) difficultySelect.value = question.difficulty;
        if (statusSelect) statusSelect.value = question.status;

        if (modalTitle) modalTitle.textContent = 'ویرایش سؤال';
        if (saveBtn) saveBtn.textContent = 'آپدیت سؤال';

        if (this.modals.addQuestionModal) {
            this.modals.addQuestionModal.show();
        }
    }

    /**
     * Save new question or update existing one
     */
    saveQuestion() {
        const questionIdElement = document.getElementById('questionId');
        const questionTextElement = document.getElementById('questionText');
        const notAMcqCheck = document.getElementById('notAMcqCheck');

        if (!questionIdElement || !questionTextElement || !notAMcqCheck) {
            console.warn("Required form elements not found");
            return;
        }

        const id = questionIdElement.value;
        const text = questionTextElement.value.trim();
        const isMcq = !notAMcqCheck.checked;

        // Validate form
        if (!text) {
            alert('لطفا سؤال را وارد کنید');
            return;
        }

        let options = [];
        if (isMcq) {
            const option1 = document.getElementById('option1');
            const option2 = document.getElementById('option2');
            const option3 = document.getElementById('option3');
            const option4 = document.getElementById('option4');

            if (!option1 || !option2 || !option3 || !option4) {
                console.warn("Option elements not found");
                return;
            }

            options = [
                option1.value.trim(),
                option2.value.trim(),
                option3.value.trim(),
                option4.value.trim()
            ];

            // Validate options for MCQ
            if (options.some(opt => !opt)) {
                alert('لطفا همه گزینه‌ها را پر کنید');
                return;
            }
        }

        const itemTypeSelect = document.getElementById('itemTypeSelect');
        const difficultySelect = document.getElementById('difficultLevelSelect');
        const statusSelect = document.getElementById('statusSelect');

        if (!itemTypeSelect || !difficultySelect || !statusSelect) {
            console.warn("Select elements not found");
            return;
        }

        const type = itemTypeSelect.value;
        const difficulty = difficultySelect.value;
        const status = statusSelect.value;

        // Validate selects
        if (!type || !difficulty || !status) {
            alert('لطفا همه فیلدهای الزامی را انتخاب کنید');
            return;
        }

        const question = {
            text,
            options,
            type,
            difficulty,
            status
        };

        if (id) {
            // Update existing question
            question.id = parseInt(id);
            const index = this.questions.findIndex(q => q.id === question.id);
            if (index !== -1) {
                this.questions[index] = question;
            }
        } else {
            // Add new question
            this.currentId++;
            question.id = this.currentId;
            this.questions.unshift(question);
        }
        this.applyCurrentFilters();
        this.renderTable();

        if (this.modals.addQuestionModal) {
            this.modals.addQuestionModal.hide();
        }
    }

    /**
     * Delete question
     */
    deleteQuestion(id) {
        this.questions = this.questions.filter(q => q.id !== id);
        // Update filteredQuestions to match current filter state
        this.applyCurrentFilters();
        this.renderTable();
    }
    applyCurrentFilters() {
        // Get current filter value from select
        const sortBySelect = document.querySelector('#sortBySelect');
        const filterValue = sortBySelect ? sortBySelect.value : 'همه';

        if (!filterValue || filterValue === 'همه') {
            this.filteredQuestions = [...this.questions];
            return;
        }

        // Re-apply current filter
        this.filteredQuestions = this.questions.filter(question => {
            if (filterValue === 'چهار گزینه‌ای' || filterValue === 'تشریحی') {
                return question.type === filterValue;
            } else if (filterValue === 'سخت' || filterValue === 'متوسط' || filterValue === 'عادی') {
                return question.difficulty === filterValue;
            }
            return false;
        });
    }

    /**
     * Search questions
     */
    searchQuestions(query) {
        if (!query || query.trim() === '') {
            // Reset to show all questions based on current filter
            this.applyCurrentFilters();
            this.renderTable();
            return;
        }

        query = query.toLowerCase().trim();

        // Start with currently filtered questions rather than all questions
        // This preserves any active filters from sortBySelect
        const baseQuestions = this.filteredQuestions.length > 0 ?
            this.filteredQuestions : [...this.questions];

        const searchResults = baseQuestions.filter(q => {
            return (
                q.text.toLowerCase().includes(query) ||
                q.type.toLowerCase().includes(query) ||
                q.difficulty.toLowerCase().includes(query) ||
                q.status.toLowerCase().includes(query) ||
                (q.options && q.options.some(opt => opt.toLowerCase().includes(query)))
            );
        });

        // Temporarily store the filtered results
        const previousFiltered = this.filteredQuestions;
        this.filteredQuestions = searchResults;
        this.renderTable();

        // If search is cleared, we need to restore the previous filter state
        if (searchResults.length === 0 || query === '') {
            this.filteredQuestions = previousFiltered;
        }
    }

    /**
     * Render filtered questions
     */
    renderFilteredQuestions(filteredQuestions) {
        this.filteredQuestions = filteredQuestions;
        this.renderTable();
    }

    /**
     * Sort questions
     */
    sortQuestions(sortBy) {
        if (!sortBy) {
            this.renderTable();
            return;
        }

        const [field, direction] = sortBy.split('-');
        const sortedQuestions = [...this.questions];

        sortedQuestions.sort((a, b) => {
            let comparison = 0;

            switch (field) {
                case 'difficulty':
                    const difficultyOrder = { 'Easy': 1, 'Normal': 2, 'Medium': 3, 'Hard': 4 };
                    comparison = difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
                    break;

                case 'type':
                    comparison = a.type.localeCompare(b.type);
                    break;

                case 'status':
                    comparison = a.status === 'New' ? -1 : 1;
                    break;

                default:
                    return 0;
            }

            return direction === 'desc' ? -comparison : comparison;
        });

        this.renderFilteredQuestions(sortedQuestions);
    }
}

// Initialize the table manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        const tableManager = new TableManager();
    } catch (error) {
        console.error("Error initializing TableManager:", error);
    }
    const sortBySelect = document.getElementById('sortBySelect');
    if (sortBySelect) {
        sortBySelect.addEventListener('change', function () {
            const selectElement = document.querySelector('#sortBySelect');
            if (selectElement) {
                const selectedValue = selectElement.value;
                window.tableManager.filterQuestions(selectedValue);
            }
        });
    }
});