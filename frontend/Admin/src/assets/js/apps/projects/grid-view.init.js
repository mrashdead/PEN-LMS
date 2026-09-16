import { icons, createIcons } from "lucide";



import user14 from "/assets/images/avatar/user-14.png"
import user17 from "/assets/images/avatar/user-17.png"
import user16 from "/assets/images/avatar/user-16.png"
import user12 from "/assets/images/avatar/user-12.png"
import user18 from "/assets/images/avatar/user-18.png"
import user15 from "/assets/images/avatar/user-15.png"

VirtualSelect.init({
    ele: '#assignedSelect',
    options: [
        { label: "مکس بوکو", value: "Max Boucaut" },
        { label: "ناتاشا تگ", value: "Natasha Tegg" },
        { label: "ایتن زاهل", value: "Ethan Zahel" },
        { label: "رایان فریزر", value: "Ryan Frazer" },
        { label: "جولیان مارکونی", value: "Julian Marconi" },
        { label: "پاپی دالی", value: "Poppy Dalley" }
    ],
    selectedValue: 0,
    multiple: true,
});

VirtualSelect.init({
    ele: "#statusSelect2",
    options: [
        { label: "فعال", value: "Active" },
        { label: "در انتظار", value: "On Hold" },
        { label: "در حال انجام", value: "Pending" },
        { label: "تکمیل شده", value: "Completed" }
    ],
});
VirtualSelect.init({
    ele: "#filterStatusSelect",
    options: [
        { label: "فعال", value: "Active" },
        { label: "در انتظار", value: "On Hold" },
        { label: "در حال انجام", value: "Pending" },
        { label: "تکمیل شده", value: "Completed" }
    ],
});

VirtualSelect.init({
    ele: "#filterSelect",
    options: [
        { label: "هفتگی", value: "Weekly" },
        { label: "ماهانه", value: "Monthly" },
        { label: "سالانه", value: "Yearly" },
    ],
});

// Mappings
const statusMapping = {
    'Active': 'فعال',
    'On Hold': 'در انتظار',
    'Pending': 'در حال انجام',
    'Completed': 'تکمیل شده'
};


class ProjectsGrid {
    constructor() {
        // Main elements
        this.projectsContainer = document.querySelector('#projectsList');
        this.projectCountElement = document.querySelector('#projectCountElement');
        this.searchInput = document.getElementById('searchProjectsInput');
        this.filterTabs = document.querySelectorAll('.project-nav');
        this.paginationContainer = document.querySelector('.pagination');

        // State
        this.projects = [];
        this.filteredProjects = [];
        this.currentFilter = 'همه پروژه‌ها';
        this.currentPage = 1;
        this.itemsPerPage = 8;
        this.totalPages = 0;

        // Initialize
        this.setupEventListeners();
        this.loadProjects();
    }

    setupEventListeners() {
        // Search functionality
        this.searchInput.addEventListener('input', () => this.handleSearch());

        // Filter tabs
        this.filterTabs.forEach(tab => {
            tab.addEventListener('click', (e) => this.handleFilter(e.target.textContent));
        });

        // Add project - clear form and errors when opening modal
        document.querySelector('[data-bs-target="#addProjectModal"]').addEventListener('click', () => {
            document.getElementById('addProjectModalLabel').textContent = 'اضافه کردن پروژه';
            this.clearForm();
            this.clearValidationErrors();
        });

        // Form submission
        document.querySelector('#addProjectModal form').addEventListener('submit', (e) => {
            e.preventDefault();
            const isEdit = document.getElementById('addProjectModalLabel').textContent.includes('Edit') || document.getElementById('addProjectModalLabel').textContent.includes('ویرایش');

            isEdit ? this.updateProject() : this.addProject();
        });

        // Input validation on blur
        const form = document.querySelector('#addProjectModal form');
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                // Clear any existing error for this input
                if (input.classList.contains('is-invalid')) {
                    input.classList.remove('is-invalid');
                    const errorMessage = input.parentNode.querySelector('.error-message');
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                }

                // Check if input is empty
                if (input.value.trim() === '' && input.hasAttribute('required')) {
                    const fieldName = input.getAttribute('placeholder') || input.id;
                    this.addErrorMessage(input, `${fieldName} لازم است.`);
                }

                // For amount field, also validate it's a number
                if (input.id === 'totalAmountInput' && input.value.trim() !== '') {
                    if (isNaN(parseFloat(input.value))) {
                        this.addErrorMessage(input, 'مبلغ کل باید عدد باشد');
                    }
                }
            });
        });

        // Global event delegation for edit and delete
        document.addEventListener('click', (e) => {
            // Edit project
            if (e.target.closest('[data-bs-target="#addProjectModal"]') &&
                e.target.closest('.dropdown-menu')) {
                const projectCard = e.target.closest('.project-card');
                if (projectCard) {
                    this.openEditForm(projectCard.dataset.id);
                    this.clearValidationErrors(); // Clear any validation errors when editing
                }
            }

            // Delete confirmation
            if (e.target.closest('[data-bs-target="#deleteModal"]')) {
                const projectCard = e.target.closest('.project-card');
                if (projectCard) {
                    this.projectToDelete = projectCard.dataset.id;
                }
            }

            // Delete project
            if (e.target.closest('#deleteModal .btn-danger')) {
                this.deleteProject(this.projectToDelete);
            }

            // Pagination
            if (e.target.closest('.page-link') && !e.target.closest('.disabled')) {
                const pageText = e.target.textContent.trim();

                if (pageText === 'قبلی' || pageText.includes('قبلی'))
                    this.goToPage(this.currentPage - 1);
                else if (pageText === 'بعدی' || pageText.includes('بعدی'))
                    this.goToPage(this.currentPage + 1);
                else
                    this.goToPage(parseInt(pageText));
            }
        });
    }
    addErrorMessage(inputElement, message) {
        inputElement.classList.add('is-invalid');

        const errorElement = document.createElement('div');
        errorElement.className = 'invalid-feedback error-message';
        errorElement.textContent = message;

        inputElement.parentNode.appendChild(errorElement);
    }

    clearValidationErrors() {
        const form = document.querySelector('#addProjectModal form');
        const errorElements = form.querySelectorAll('.error-message');
        errorElements.forEach(element => element.remove());

        const invalidFields = form.querySelectorAll('.is-invalid');
        invalidFields.forEach(field => field.classList.remove('is-invalid'));
    }

    loadProjects() {
        this.projects = this.getSampleProjects();
        this.filteredProjects = [...this.projects];
        this.updateTotalPages();
        this.renderProjects();
        this.updateProjectCount();
    }

    getSampleProjects() {
        return [
    {
        id: 1,
        title: 'برنامه چت',
        client: 'جان دو',
        dueDate: '15 خرداد 1403',
        amount: '18,000 تومان',
        progress: 18,
        status: 'Active',
        assigned: ["assets/images/avatar/user-14.png", "assets/images/avatar/user-16.png"],
        image: 'assets/images/brands/img-01.png'
    },
    {
        id: 2,
        title: 'پلتفرم تجارت الکترونیک',
        client: 'سم ویلیامز',
        dueDate: '25 تیر 1403',
        amount: '25,000 تومان',
        progress: 41,
        status: 'On Hold',
        assigned: ["assets/images/avatar/user-17.png", "assets/images/avatar/user-15.png", "assets/images/avatar/user-19.png"],
        image: 'assets/images/brands/img-02.png'
    },
    {
        id: 3,
        title: 'وب‌سایت شرکتی',
        client: 'شرکت ABC',
        dueDate: '30 اردیبهشت 1403',
        amount: '10,000 تومان',
        progress: 75,
        status: 'Pending',
        assigned: ["assets/images/avatar/user-16.png", "assets/images/avatar/user-12.png"],
        image: 'assets/images/brands/img-03.png'
    },
    {
        id: 4,
        title: 'ادغام API',
        client: 'DevHouse',
        dueDate: '5 مرداد 1403',
        amount: '20,000 تومان',
        progress: 60,
        status: 'Pending',
        assigned: ["assets/images/avatar/user-17.png", "assets/images/avatar/user-16.png"],
        image: 'assets/images/brands/img-08.png'
    },
    {
        id: 5,
        title: 'طراحی دوباره برنامه موبایل',
        client: 'Creative Studio',
        dueDate: '10 شهریور 1403',
        amount: '12,500 تومان',
        progress: 35,
        status: 'Active',
        assigned: ["assets/images/avatar/user-15.png", "assets/images/avatar/user-19.png"],
        image: 'assets/images/brands/img-01.png'
    },
    {
        id: 6,
        title: 'داشبورد بازاریابی',
        client: 'MarketGurus',
        dueDate: '1 مهر 1403',
        amount: '30,000 تومان',
        progress: 80,
        status: 'Completed',
        assigned: ["assets/images/avatar/user-12.png", "assets/images/avatar/user-14.png"],
        image: 'assets/images/brands/img-02.png'
    },
    {
        id: 7,
        title: 'مدیریت SaaS',
        client: 'TechNova',
        dueDate: '18 مرداد 1403',
        amount: '22,000 تومان',
        progress: 50,
        status: 'On Hold',
        assigned: ["assets/images/avatar/user-16.png", "assets/images/avatar/user-17.png"],
        image: 'assets/images/brands/img-03.png'
    },
    {
        id: 8,
        title: 'سیستم CRM',
        client: 'BusinessPro',
        dueDate: '5 آذر 1403',
        amount: '40,000 تومان',
        progress: 90,
        status: 'Active',
        assigned: ["assets/images/avatar/user-14.png", "assets/images/avatar/user-15.png"],
        image: 'assets/images/brands/img-08.png'
    },
    {
        id: 9,
        title: 'سازنده پرتفوی',
        client: 'Freelance Hub',
        dueDate: '22 آبان 1403',
        amount: '7,500 تومان',
        progress: 28,
        status: 'Pending',
        assigned: ["assets/images/avatar/user-19.png", "assets/images/avatar/user-12.png"],
        image: 'assets/images/brands/img-01.png'
    },
    {
        id: 10,
        title: 'ردیاب موجودی',
        client: 'RetailChain',
        dueDate: '15 مهر 1403',
        amount: '16,000 تومان',
        progress: 66,
        status: 'Active',
        assigned: ["assets/images/avatar/user-17.png", "assets/images/avatar/user-14.png", "assets/images/avatar/user-16.png"],
        image: 'assets/images/brands/img-02.png'
    },
    {
        id: 11,
        title: 'سیستم مدیریت منابع انسانی',
        client: 'PeopleOps Inc.',
        dueDate: '20 شهریور 1403',
        amount: '19,000 تومان',
        progress: 45,
        status: 'On Hold',
        assigned: ["assets/images/avatar/user-14.png", "assets/images/avatar/user-12.png"],
        image: 'assets/images/brands/img-03.png'
    },
    {
        id: 12,
        title: 'برنامه ردیاب پروژه',
        client: 'BuildSuite',
        dueDate: '12 مرداد 1403',
        amount: '11,500 تومان',
        progress: 55,
        status: 'Active',
        assigned: ["assets/images/avatar/user-15.png", "assets/images/avatar/user-17.png"],
        image: 'assets/images/brands/img-01.png'
    },
    {
        id: 13,
        title: 'ابزار تجزیه و تحلیل',
        client: 'Insight Lab',
        dueDate: '2 آبان 1403',
        amount: '23,000 تومان',
        progress: 33,
        status: 'Pending',
        assigned: ["assets/images/avatar/user-16.png", "assets/images/avatar/user-19.png"],
        image: 'assets/images/brands/img-02.png'
    },
    {
        id: 14,
        title: 'مهاجرت به ابری',
        client: 'SkyNet Solutions',
        dueDate: '28 آذر 1403',
        amount: '45,000 تومان',
        progress: 72,
        status: 'On Hold',
        assigned: ["assets/images/avatar/user-12.png", "assets/images/avatar/user-14.png", "assets/images/avatar/user-17.png"],
        image: 'assets/images/brands/img-08.png'
    },
    {
        id: 15,
        title: 'برنامه زمان‌بندی رسانه‌های اجتماعی',
        client: 'PostPal',
        dueDate: '7 مهر 1403',
        amount: '14,000 تومان',
        progress: 25,
        status: 'Pending',
        assigned: ["assets/images/avatar/user-15.png"],
        image: 'assets/images/brands/img-03.png'
    },
    {
        id: 16,
        title: 'ویدجت چت زنده',
        client: 'QuickTalk',
        dueDate: '13 شهریور 1403',
        amount: '9,500 تومان',
        progress: 64,
        status: 'Active',
        assigned: ["assets/images/avatar/user-16.png", "assets/images/avatar/user-19.png"],
        image: 'assets/images/brands/img-01.png'
    },
    {
        id: 17,
        title: 'موتور رزرو',
        client: 'TravelFox',
        dueDate: '5 دی 1403',
        amount: '32,000 تومان',
        progress: 48,
        status: 'Pending',
        assigned: ["assets/images/avatar/user-14.png", "assets/images/avatar/user-15.png"],
        image: 'assets/images/brands/img-02.png'
    },
    {
        id: 18,
        title: 'پلتفرم یادگیری',
        client: 'EduTrack',
        dueDate: '11 بهمن 1403',
        amount: '38,000 تومان',
        progress: 69,
        status: 'On Hold',
        assigned: ["assets/images/avatar/user-17.png", "assets/images/avatar/user-16.png"],
        image: 'assets/images/brands/img-08.png'
    },
    {
        id: 19,
        title: 'داشبورد IoT',
        client: 'SmartNet',
        dueDate: '24 دی 1403',
        amount: '27,000 تومان',
        progress: 36,
        status: 'Active',
        assigned: ["assets/images/avatar/user-12.png", "assets/images/avatar/user-19.png"],
        image: 'assets/images/brands/img-03.png'
    },
    {
        id: 20,
        title: 'ردیاب پرونده‌های حقوقی',
        client: 'LexTech',
        dueDate: '9 اسفند 1403',
        amount: '21,000 تومان',
        progress: 52,
        status: 'Pending',
        assigned: ["assets/images/avatar/user-14.png", "assets/images/avatar/user-15.png", "assets/images/avatar/user-17.png"],
        image: 'assets/images/brands/img-01.png'
    },
    {
        id: 21,
        title: 'سیستم مدیریت ناوگان',
        client: 'DriveOps',
        dueDate: '18 اردیبهشت 1404',
        amount: '26,000 تومان',
        progress: 39,
        status: 'Active',
        assigned: ["assets/images/avatar/user-17.png", "assets/images/avatar/user-14.png"],
        image: 'assets/images/brands/img-02.png'
    },
    {
        id: 22,
        title: 'پلتفرم صدور بلیت رویداد',
        client: 'TicketVerse',
        dueDate: '6 خرداد 1404',
        amount: '34,000 تومان',
        progress: 71,
        status: 'Completed',
        assigned: ["assets/images/avatar/user-15.png", "assets/images/avatar/user-16.png", "assets/images/avatar/user-12.png"],
        image: 'assets/images/brands/img-08.png'
    },
    {
        id: 23,
        title: 'پورتال املاک',
        client: 'HomeHunt',
        dueDate: '25 تیر 1404',
        amount: '29,000 تومان',
        progress: 44,
        status: 'در حال انتظار',
        assigned: ["assets/images/avatar/user-14.png", "assets/images/avatar/user-19.png"],
        image: 'assets/images/brands/img-03.png'
    },
    {
        id: 24,
        title: 'پشتیبان‌گیری پخش ویدئو',
        client: 'StreamWise',
        dueDate: '9 تیر 1404',
        amount: '50,000 تومان',
        progress: 22,
        status: 'Pending',
        assigned: ["assets/images/avatar/user-17.png", "assets/images/avatar/user-15.png"],
        image: 'assets/images/brands/img-01.png'
    },
    {
        id: 25,
        title: 'API رده‌بندی بازی',
        client: 'PixelPlay',
        dueDate: '3 مرداد 1404',
        amount: '13,500 تومان',
        progress: 58,
        status: 'Active',
        assigned: ["assets/images/avatar/user-12.png"],
        image: 'assets/images/brands/img-02.png'
    },
    {
        id: 26,
        title: 'برنامه ردیاب تناسب اندام',
        client: 'FitWorld',
        dueDate: '17 شهریور 1404',
        amount: '17,000 تومان',
        progress: 63,
        status: 'در حال انتظار',
        assigned: ["assets/images/avatar/user-14.png", "assets/images/avatar/user-16.png"],
        image: 'assets/images/brands/img-03.png'
    },
    {
        id: 27,
        title: 'پورتال دوره‌های آنلاین',
        client: 'SkillBoost',
        dueDate: '21 مهر 1404',
        amount: '42,000 تومان',
        progress: 78,
        status: 'Completed',
        assigned: ["assets/images/avatar/user-19.png", "assets/images/avatar/user-17.png"],
        image: 'assets/images/brands/img-08.png'
    }
        ];
    }

    handleSearch() {
        const query = this.searchInput.value.toLowerCase().trim();

        if (query === '') {
            // Reset to current filter only
            this.applyFilter(this.currentFilter);
        } else {
            // Apply both search and current filter
            if (this.currentFilter === 'همه پروژه‌ها') {
                this.filteredProjects = this.projects.filter(project =>
                    project.title.toLowerCase().includes(query) ||
                    project.client.toLowerCase().includes(query)
                );
            } else {
                this.filteredProjects = this.projects.filter(project =>
                    (project.title.toLowerCase().includes(query) ||
                        project.client.toLowerCase().includes(query)) &&
                    project.status === this.currentFilter
                );
            }
        }

        this.currentPage = 1;
        this.updateTotalPages();
        this.renderProjects();
    }

    handleFilter(filterName) {
        // Update active tab UI
        this.filterTabs.forEach(tab => {
            tab.classList.toggle('active', tab.textContent === filterName);
        });

        this.currentFilter = filterName;
        this.applyFilter(filterName);

        this.currentPage = 1;
        this.updateTotalPages();
        this.renderProjects();
    }

    applyFilter(filterName) {
        // Map Persian filter to English status
        const reverseMapping = {
            'فعال': 'Active',
            'در انتظار': 'On Hold',
            'در حال انجام': 'Pending',
            'تکمیل شده': 'Completed'
        };

        if (filterName === 'همه پروژه‌ها') {
            this.filteredProjects = [...this.projects];
        } else {
            // Convert Persian filter name to English before comparing
            const englishStatus = reverseMapping[filterName] || filterName;
            this.filteredProjects = this.projects.filter(project =>
                project.status === englishStatus
            );
        }

        // Apply search query if exists
        const query = this.searchInput.value.toLowerCase().trim();
        if (query) {
            this.filteredProjects = this.filteredProjects.filter(project =>
                project.title.toLowerCase().includes(query) ||
                project.client.toLowerCase().includes(query)
            );
        }
    }

    updateTotalPages() {
        this.totalPages = Math.ceil(this.filteredProjects.length / this.itemsPerPage);
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.renderProjects();
    }

    renderPagination() {
        if (!this.paginationContainer) return;

        let paginationHTML = `
        <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
          <a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>
        </li>
      `;

        for (let i = 1; i <= this.totalPages; i++) {
            paginationHTML += `
          <li class="page-item ${i === this.currentPage ? 'active' : ''}">
            <a class="page-link" href="#!">${i}</a>
          </li>
        `;
        }

        paginationHTML += `
        <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
          <a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>
        </li>
      `;

        this.paginationContainer.innerHTML = paginationHTML;

        createIcons({ icons });
    }

    updatePaginationInfo() {
        const infoElement = document.querySelector('.pagination-courting-info');
        if (!infoElement) return;

        const start = (this.currentPage - 1) * this.itemsPerPage + 1;
        const end = Math.min(start + this.itemsPerPage - 1, this.filteredProjects.length);
        const total = this.filteredProjects.length;

        infoElement.innerHTML = `نمایش <b class="me-1">${start}-${end}</b> از<b class="ms-1">${total}</b> نتیجه`;
    }

    getStatusBadgeClass(status) {
        switch (status) {
            case 'Active':
                return 'bg-secondary-subtle text-secondary border border-secondary-subtle';
            case 'On Hold':
                return 'bg-orange-subtle text-orange border border-orange-subtle';
            case 'Pending':
                return 'bg-warning-subtle text-warning border border-warning-subtle';
            case 'Completed':
                return 'bg-success-subtle text-success border border-success-subtle';
            default:
                return 'bg-secondary-subtle text-secondary border border-secondary-subtle';
        }
    }
    // Updated renderProjects method with fixed avatar rendering
    renderProjects() {
        if (!this.projectsContainer) return;

        // Calculate pagination slice
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        const paginatedProjects = this.filteredProjects.slice(start, end);

        // Clear current projects
        this.projectsContainer.innerHTML = '';

        if (paginatedProjects.length === 0) {
            this.projectsContainer.innerHTML = `
          <td colspan="6" class="text-center py-4">
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
                                                <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164	S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331	c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                                                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0	l-4.331-4.331"></path>
                                                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                                                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                                            </svg>
                                            <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                        <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                    </div>
                </td>
      `;
        } else {
            paginatedProjects.forEach(project => {
                const projectCard = document.createElement('div');
                projectCard.className = 'col-md-6 col-xxl-3 project-card';
                projectCard.dataset.id = project.id;

                let avatarsHTML = '';
                // Handle both "assigned" (array of paths) and "assignees" (array of objects)
                if (project.assigned && Array.isArray(project.assigned)) {
                    // Handle original data structure (array of paths)
                    project.assigned.forEach(avatarPath => {
                        avatarsHTML += `
            <a href="#!" class="avatar-group-item" aria-label="avatar">
                <img src="${avatarPath}" loading="lazy" alt="avatar" class="size-8">
            </a>
        `;
                    });
                } else if (project.assignees && Array.isArray(project.assignees)) {
                    // Handle new data structure (array of objects with image and name)
                    project.assignees.forEach(assignee => {
                        avatarsHTML += `
            <a href="#!" class="avatar-group-item" aria-label="avatar">
                <img src="${assignee.image}" loading="lazy" alt="${assignee.name}" class="size-8">
            </a>
        `;
                    });
                }

                const persianStatus = statusMapping[project.status] || project.status;

                projectCard.innerHTML = `
          <div class="card">
            <div class="card-body">
              <div class="dropdown float-end">
                <a href="#!" class="link link-custom-primary" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="dropdown-button">
                  <i class="ri-more-fill"></i>
                </a>
                <ul class="dropdown-menu dropdown-menu-end">
                  <li><a href="#!" class="dropdown-item d-flex gap-xl-2 align-items-center"><i class="ri-eye-line"></i><span>نمای کلی</span></a></li>
                  <li data-bs-toggle="modal" data-bs-target="#addProjectModal"><a href="#!" class="dropdown-item d-flex gap-xl-2 align-items-center"><i class="ri-pencil-line"></i>ویرایش</a></li>
                  <li data-bs-toggle="modal" data-bs-target="#deleteModal"><a href="#!" class="dropdown-item d-flex gap-xl-2 align-items-center"><i class="ri-delete-bin-line"></i><span>حذف</span></a></li>
                </ul>
              </div>
              <div class="size-12 border avatar mb-4 rounded">
                <img src="${project.image}" loading="lazy" alt="${project.title}" class="size-8">
              </div>
              <h6 class="mb-1">${project.title}</h6>
              <p class="text-muted">${project.client}</p>
              <div class="row mt-3">
                <div class="col-6 p-2 text-center border-end">
                  <h6 class="mb-1">${project.dueDate}</h6>
                  <p class="text-muted">تاریخ سررسید</p>
                </div>
                <div class="col-6 p-2 text-center">
                  <h6 class="mb-1">${project.amount}</h6>
                  <p class="text-muted">مبلغ کل</p>
                </div>
              </div>
              <div class="mt-5">
                <p class="mb-2 text-muted">پروژه %${project.progress} تکمیل شده است</p>
                <div class="progress progress-1" role="progressbar" aria-label="Project Progress" aria-valuenow="${project.progress}" aria-valuemin="0" aria-valuemax="100">
                  <div class="progress-bar progress-gradient progress-gradient-secondary" style="width: ${project.progress}%"></div>
                </div>
              </div>
              <div class="d-flex align-items-center gap-2 mt-5">
                <p class="me-3">اختصاص داده شده به:</p>
                <div class="avatar-group flex-grow-1">
                  ${avatarsHTML}
                </div>
                <span class="flex-shrink-0 badge ${this.getStatusBadgeClass(project.status)}">${persianStatus}</span>
              </div>
            </div>
          </div>
        `;
                this.projectsContainer.appendChild(projectCard);
            });
        }

        createIcons({ icons });

        this.renderPagination();
        this.updatePaginationInfo();
    }

    generateAssigneeAvatars(assignedAvatars) {
        if (!assignedAvatars || !Array.isArray(assignedAvatars)) {
            return '';
        }

        let avatarsHTML = '';
        assignedAvatars.forEach(avatarPath => {
            avatarsHTML += `
      <a href="#!" class="avatar-group-item" aria-label="avatar">
        <img src="${avatarPath}" loading="lazy" alt="avatar" class="size-8">
      </a>
    `;
        });
        return avatarsHTML;
    }

    clearForm() {
        const form = document.querySelector('#addProjectModal form');
        form.reset();

        // Reset any hidden inputs
        const idInput = form.querySelector('input[name="projectId"]');
        if (idInput) idInput.value = '';

        // Reset progress bar
        const progressBar = form.querySelector('.progress-bar');
        if (progressBar) progressBar.style.width = '0%';

        // Clear any validation errors
        this.clearValidationErrors();
    }

    validateForm() {
        const form = document.querySelector('#addProjectModal form');

        // Get form fields
        const title = form.querySelector('#projectTitleInput').value.trim();
        const client = form.querySelector('#clientName').value.trim();
        const dueDate = form.querySelector('input[placeholder="تاریخ سررسید را انتخاب کنید"]').value.trim();
        const amount = form.querySelector('#totalAmountInput').value.trim();
        const assigneeSelect = document.querySelector("#assignedSelect");
        const statusSelect = form.querySelector('#statusSelect') || form.querySelector('#statusSelect2');

        const assignee = assigneeSelect ? assigneeSelect.value : '';
        const status = statusSelect ? statusSelect.value.trim() : '';

        // Reset previous error messages
        const errorElements = form.querySelectorAll('.error-message');
        errorElements.forEach(element => element.remove());

        const invalidFields = form.querySelectorAll('.is-invalid');
        invalidFields.forEach(field => field.classList.remove('is-invalid'));

        // Validation checks
        let isValid = true;

        // Title validation
        if (!title) {
            this.addErrorMessage(form.querySelector('#projectTitleInput'), 'عنوان پروژه الزامی است');
            isValid = false;
        }

        // Client validation
        if (!client) {
            this.addErrorMessage(form.querySelector('#clientName'), 'نام مشتری الزامی است');
            isValid = false;
        }

        // Due date validation
        if (!dueDate) {
            this.addErrorMessage(form.querySelector('input[placeholder="تاریخ سررسید را انتخاب کنید"]'), 'تاریخ سررسید الزامی است');
            isValid = false;
        }

        // Amount validation
        if (!amount) {
            this.addErrorMessage(form.querySelector('#totalAmountInput'), 'مبلغ کل مورد نیاز است');
            isValid = false;
        } else if (isNaN(parseFloat(amount))) {
            this.addErrorMessage(form.querySelector('#totalAmountInput'), 'مبلغ کل باید عدد باشد');
            isValid = false;
        }

        // Assignee validation
        if (!assignee || (Array.isArray(assignee) && assignee.length === 0)) {
            this.addErrorMessage(assigneeSelect, 'لطفاً حداقل یک نماینده انتخاب کنید');
            isValid = false;
        }

        // Status validation
        if (!status) {
            this.addErrorMessage(statusSelect, 'لطفاً یک وضعیت انتخاب کنید');
            isValid = false;
        }

        return isValid;
    }

    openEditForm(projectId) {
        const project = this.projects.find(p => p.id == projectId);
        if (!project) return;

        document.getElementById('addProjectModalLabel').textContent = 'ویرایش پروژه';
        // document.getElementById('addProjectModalLabel').textContent = 'Edit Project';

        const form = document.querySelector('#addProjectModal form');

        let idInput = form.querySelector('input[name="projectId"]');
        if (!idInput) {
            idInput = document.createElement('input');
            idInput.type = 'hidden';
            idInput.name = 'projectId';
            form.appendChild(idInput);
        }
        idInput.value = project.id;

        // Fill form fields
        form.querySelector('#projectTitleInput').value = project.title;
        form.querySelector('#clientName').value = project.client;
        form.querySelector('input[placeholder="تاریخ سررسید را انتخاب کنید"]').value = project.dueDate;  // Replace AirDatepicker
        form.querySelector('#totalAmountInput').value = project.amount.replace(/[^\d.]/g, '');
        form.querySelector('#progressInput').value = project.progress;

        // Set Virtual Select values
        document.querySelector('#statusSelect2').setValue(project.status);

        // Update progress bar
        const progressBar = form.querySelector('.progress-bar');
        if (progressBar) progressBar.style.width = `${project.progress}%`;
    }

    addProject() {
        // Validate form before proceeding
        if (!this.validateForm()) {
            return; // Stop execution if validation fails
        }

        const form = document.querySelector('#addProjectModal form');
        const title = form.querySelector('#projectTitleInput').value;
        const client = form.querySelector('#clientName').value;
        const dueDate = form.querySelector('input[placeholder="تاریخ سررسید را انتخاب کنید"]').value;
        const amount = form.querySelector('#totalAmountInput').value;
        const progress = parseInt(form.querySelector('#progressInput').value) || 0;

        const assigneeSelect = document.querySelector("#assignedSelect");
        const assignee = assigneeSelect ? assigneeSelect.value : [];
        let assigneesImages = [];

        if (!assignee || assignee.length === 0) {
            assigneesImages = this.projectForm?.assignees || [];
        } else {
            (Array.isArray(assignee) ? assignee : [assignee]).forEach(element => {
                if (element == "Max Boucaut")
                    assigneesImages.push({ image: user14, name: element });
                else if (element == "Poppy Dalley")
                    assigneesImages.push({ image: user17, name: element });
                else if (element == "Ethan Zahel")
                    assigneesImages.push({ image: user16, name: element });
                else if (element == "Julian Marconi")
                    assigneesImages.push({ image: user12, name: element });
                else if (element == "Ryan Frazer")
                    assigneesImages.push({ image: user18, name: element });
                else if (element == "Natasha Tegg")
                    assigneesImages.push({ image: user15, name: element });
            });
        }

        // Get status from select
        const statusSelect = form.querySelector('#statusSelect') || form.querySelector('#statusSelect2');
        const status = statusSelect?.value || 'Active';

        // Get next ID with null check
        const maxId = Math.max(...(this.projects || []).map(p => p.id || 0), 0);

        const newProject = {
            id: maxId + 1,
            title,
            client,
            dueDate,
            amount: (parseFloat(amount) || 0).toLocaleString() + ' تومان',
            progress,
            status,
            assignees: assigneesImages,
            assigneesCount: assigneesImages.length,
            image: `assets/images/brands/img-0${Math.floor(Math.random() * 3) + 1}.png`
        };

        // Initialize projects array if it doesn't exist
        if (!this.projects) {
            this.projects = [];
        }

        this.projects.unshift(newProject);

        // Close modal - Added error handling
        try {
            const modal = window.bootstrap.Modal.getInstance(document.getElementById('addProjectModal'));
            if (modal) modal.hide();
        } catch (error) {
            console.error("Error closing modal:", error);
        }

        // Apply current filter and search with null checks
        if (typeof this.applyFilter === 'function') {
            this.applyFilter(this.currentFilter || 'all');
        }

        if (typeof this.updateTotalPages === 'function') {
            this.updateTotalPages();
        }

        if (typeof this.renderProjects === 'function') {
            this.renderProjects();
        }

        if (typeof this.updateProjectCount === 'function') {
            this.updateProjectCount();
        }
    }

    updateProject() {
        // Validate form before proceeding
        if (!this.validateForm()) {
            return; // Stop execution if validation fails
        }

        const form = document.querySelector('#addProjectModal form');
        const projectIdInput = form.querySelector('input[name="projectId"]');

        if (!projectIdInput) {
            console.error("Project ID input not found");
            return;
        }

        const projectId = parseInt(projectIdInput.value);

        if (isNaN(projectId)) {
            console.error("Invalid project ID");
            return;
        }

        // Initialize projects array if it doesn't exist
        if (!this.projects) {
            console.error("Projects array not initialized");
            return;
        }

        const projectIndex = this.projects.findIndex(p => p.id === projectId);
        if (projectIndex === -1) {
            console.error("Project not found with ID:", projectId);
            return;
        }

        const title = form.querySelector('#projectTitleInput').value;
        const client = form.querySelector('#clientName').value;
        const dueDate = form.querySelector('input[placeholder="تاریخ سررسید را انتخاب کنید"]').value;
        const amount = form.querySelector('#totalAmountInput').value;
        const progress = parseInt(form.querySelector('#progressInput').value) || 0;

        // Handle assignees with better VirtualSelect handling
        const assigneeSelect = document.querySelector("#assignedSelect");
        const assignee = assigneeSelect ? assigneeSelect.value : [];
        let assigneesImages = [];

        if (!assignee || assignee.length === 0) {
            assigneesImages = this.projects[projectIndex].assignees || [];
        } else {
            // Handle both array and single value cases
            (Array.isArray(assignee) ? assignee : [assignee]).forEach(element => {
                if (element == "Max Boucaut")
                    assigneesImages.push({ image: user14, name: element });
                else if (element == "Poppy Dalley")
                    assigneesImages.push({ image: user17, name: element });
                else if (element == "Ethan Zahel")
                    assigneesImages.push({ image: user16, name: element });
                else if (element == "Julian Marconi")
                    assigneesImages.push({ image: user12, name: element });
                else if (element == "Ryan Frazer")
                    assigneesImages.push({ image: user18, name: element });
                else if (element == "Natasha Tegg")
                    assigneesImages.push({ image: user15, name: element });
            });
        }

        // Get status with fallbacks
        const statusSelect = form.querySelector('#statusSelect') || form.querySelector('#statusSelect2');
        const status = statusSelect?.value || this.projects[projectIndex].status || 'Active';

        const { image } = this.projects[projectIndex];

        const updatedProject = {
            id: projectId,
            title,
            client,
            dueDate,
            amount: (parseFloat(amount) || 0).toLocaleString() + ' تومان',
            progress,
            status,
            assignees: assigneesImages,
            assigneesCount: assigneesImages.length,
            image
        };

        this.projects[projectIndex] = updatedProject;

        // Close modal with error handling
        try {
            const modal = window.bootstrap.Modal.getInstance(document.getElementById('addProjectModal'));
            if (modal) modal.hide();
        } catch (error) {
            console.error("Error closing modal:", error);
        }

        // Apply current filter and search with safety checks
        if (typeof this.applyFilter === 'function')
            this.applyFilter(this.currentFilter || 'all');

        if (typeof this.updateTotalPages === 'function')
            this.updateTotalPages();

        if (typeof this.renderProjects === 'function')
            this.renderProjects();
    }

    deleteProject(projectId) {
        projectId = parseInt(projectId);
        this.projects = this.projects.filter(p => p.id !== projectId);

        // Apply current filter and search
        this.applyFilter(this.currentFilter);
        this.updateTotalPages();
        this.renderProjects();
        this.updateProjectCount();
    }

    updateProjectCount() {
        if (this.projectCountElement)
            this.projectCountElement.textContent = this.projects.length;
    }
}

// Progress Bar Functionality for Modal
document.addEventListener('DOMContentLoaded', () => {
    const progressInput = document.getElementById('progressInput');
    const progressBar = document.querySelector('#addProjectModal .progress-bar');

    if (progressInput && progressBar) {
        progressInput.addEventListener('input', function () {
            let value = parseInt(this.value) || 0;
            value = Math.max(0, Math.min(100, value));

            if (value.toString() !== this.value) {
                this.value = value;
            }

            // Update the progress bar width
            progressBar.style.width = `${value}%`;
        });

        // Initialize progress bar
        const initialValue = parseInt(progressInput.value) || 0;
        progressBar.style.width = `${initialValue}%`;
    }
});
document.addEventListener('DOMContentLoaded', () => {
    const projectsGrid = new ProjectsGrid();
});