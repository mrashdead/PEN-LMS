//Multiple select
VirtualSelect.init({
    ele: '#keywordsSelect',
    options: [
        { label: 'کمک', value: 'Help' },
        { label: 'طراحی', value: 'Design' },
        { label: 'شخصی‌سازی', value: 'Customize' },
        { label: 'توسعه', value: 'Development' },
    ],
    multiple: true,
});

//assigned To select
VirtualSelect.init({
    ele: '#assignedToSelect',
    options: [
        { label: 'پاتریک شولتز', value: '1' },
        { label: 'مارگارت مان', value: '2' },
        { label: 'جوانه موری', value: '3' },
        { label: 'سینتیا جاستیس', value: '4' },
        { label: 'جان منسون', value: '5' },
        { label: 'مارک ولچ', value: '6' },
        { label: 'ویرجینیا داوسون', value: '7' },
    ],
    multiple: true,
});

document.addEventListener('DOMContentLoaded', function () {
    // Initialize both tab systems
    initializeSidebarTabs();
    initializeTicketTabs();
    initializeSearchFunctionality();
    initializeTicketButtons();
});

// Function to handle the sidebar tabs
function initializeSidebarTabs() {
    const sidebarTabs = document.querySelectorAll('#helpCenterTabs .nav-link');

    // Sample data for each category
        const categoryData = {
        'gettingStarted': [
            { id: '001', title: 'چگونه با پلتفرم ما شروع کنم؟', content: 'برای شروع، تنها کافیست یک حساب کاربری ایجاد کرده و راهنمای شروع به کار را دنبال کنید.', author: 'مدیر سیستم', avatar: 'assets/images/avatar/user-1.png', tags: ['شروع کار', 'راهنما', 'تنظیمات'], status: 'بسته شده' },
            { id: '002', title: 'الزامات سیستم چیست؟', content: 'پلتفرم ما با تمامی مرورگرهای مدرن کار می‌کند. ما گوگل کروم، فایرفاکس یا اج را برای بهترین تجربه توصیه می‌کنیم.', author: 'پشتیبانی فنی', avatar: 'assets/images/avatar/user-2.png', tags: ['الزامات', 'تنظیمات', 'فنی'], status: 'فعال' },
            { id: '003', title: 'چگونه رمز عبور خود را بازنشانی کنم؟', content: 'شما می‌توانید با کلیک بر روی لینک "رمز عبور را فراموش کرده‌ام" در صفحه ورود، رمز عبور خود را بازنشانی کنید.', author: 'تیم پشتیبانی', avatar: 'assets/images/avatar/user-3.png', tags: ['حساب کاربری', 'رمز عبور', 'امنیت'], status: 'حذف شده' },
            { id: '004', title: 'آیا می‌توانم از پلتفرم در دستگاه‌های موبایل استفاده کنم؟', content: 'بله، پلتفرم ما به طور کامل پاسخگو است و در تمامی دستگاه‌های موبایل و تبلت‌ها کار می‌کند.', author: 'تیم محصول', avatar: 'assets/images/avatar/user-4.png', tags: ['موبایل', 'پاسخگو', 'دستگاه‌ها'], status: 'فعال' },
            { id: '005', title: 'چگونه با پشتیبانی مشتری تماس بگیرم؟', content: 'شما می‌توانید از طریق دکمه "کمک" یا با ارسال ایمیل به support@example.com با تیم پشتیبانی مشتریان تماس بگیرید.', author: 'تیم خدمات مشتری', avatar: 'assets/images/avatar/user-5.png', tags: ['پشتیبانی', 'تماس', 'کمک'], status: 'بسته شده' }
        ],
        'accountWithCard': [
            { id: '006', title: 'چگونه یک روش پرداخت اضافه کنم؟', content: 'برای اضافه کردن یک روش پرداخت، به تنظیمات حساب کاربری خود بروید و "روش‌های پرداخت" را انتخاب کنید.', author: 'تیم صورتحساب', avatar: 'assets/images/avatar/user-6.png', tags: ['پرداخت', 'صورتحساب', 'حساب کاربری'], status: 'بسته شده' },
            { id: '007', title: 'آیا اطلاعات پرداخت من امن است؟', content: 'بله، ما از رمزنگاری استاندارد صنعتی برای محافظت از اطلاعات پرداخت شما استفاده می‌کنیم.', author: 'تیم امنیت', avatar: 'assets/images/avatar/user-7.png', tags: ['امنیت', 'پرداخت', 'محافظت'], status: 'فعال' },
            { id: '008', title: 'چگونه جزئیات کارت خود را به‌روزرسانی کنم؟', content: 'شما می‌توانید جزئیات کارت خود را در بخش "روش‌های پرداخت" تنظیمات حساب کاربری خود به‌روزرسانی کنید.', author: 'پشتیبانی صورتحساب', avatar: 'assets/images/avatar/user-8.png', tags: ['به‌روزرسانی', 'پرداخت', 'کارت'], status: 'فعال' }
        ],
        'licensesPolicy': [
            { id: '009', title: 'چه نوع مجوزهایی ارائه می‌دهید؟', content: 'ما مجوزهای شخصی، تجاری و شرکتی با ویژگی‌ها و قیمت‌های مختلف ارائه می‌دهیم.', author: 'مدیر مجوزها', avatar: 'assets/images/avatar/user-9.png', tags: ['مجوز', 'انواع', 'گزینه‌ها'], status: 'حذف شده' },
            { id: '010', title: 'آیا می‌توانم مجوز خود را به کاربر دیگری منتقل کنم؟', content: 'مجوزهای تجاری و شرکتی اجازه انتقال مجوز را می‌دهند. برای همکاری با پشتیبانی تماس بگیرید.', author: 'تیم مدیر', avatar: 'assets/images/avatar/user-10.png', tags: ['انتقال', 'مجوز', 'سیاست'], status: 'فعال' }
        ],
        'customizeTemplates': [
            { id: '011', title: 'چگونه الگوهای پیش‌فرض را سفارشی‌سازی کنم؟', content: 'شما می‌توانید الگوها را با رفتن به بخش "الگوها" و کلیک بر روی "سفارشی‌سازی" سفارشی‌سازی کنید.', author: 'تیم طراحی', avatar: 'assets/images/avatar/user-11.png', tags: ['الگوها', 'سفارشی‌سازی', 'طراحی'], status: 'حذف شده' },
            { id: '012', title: 'آیا می‌توانم الگوهای سفارشی خود را ذخیره کنم؟', content: 'بله، شما می‌توانید الگوهای سفارشی خود را برای استفاده در آینده با کلیک بر روی "ذخیره الگو" ذخیره کنید.', author: 'مدیر محصول', avatar: 'assets/images/avatar/user-12.png', tags: ['ذخیره', 'الگوها', 'سفارشی'], status: 'فعال' }
        ],
        'customizeLayouts': [
            { id: '013', title: 'چگونه طراحی داشبورد خود را تغییر دهم؟', content: 'شما می‌توانید طراحی داشبورد خود را در بخش "طراحی" تنظیمات حساب کاربری خود تغییر دهید.', author: 'طراح UX', avatar: 'assets/images/avatar/user-13.png', tags: ['طراحی', 'داشبورد', 'سفارشی‌سازی'], status: 'فعال' },
            { id: '014', title: 'آیا طرح‌های از پیش تنظیم شده موجود است؟', content: 'بله، ما چندین طرح از پیش تنظیم شده ارائه می‌دهیم که می‌توانید از آن‌ها در بخش "طراحی" انتخاب کنید.', author: 'تیم UI', avatar: 'assets/images/avatar/user-14.png', tags: ['طرح‌های از پیش تنظیم شده', 'طراحی', 'گزینه‌ها'], status: 'حذف شده' }
        ]
    };

    sidebarTabs.forEach(tab => {
        tab.addEventListener('click', function (e) {
            e.preventDefault();

            // Remove active class from all tabs
            sidebarTabs.forEach(t => t.classList.remove('active'));

            // Add active class to clicked tab
            this.classList.add('active');

            // Get the id of the clicked tab
            const tabId = this.id;

            // Generate and display tickets for the selected category
            displayCategoryTickets(tabId, categoryData[tabId] || []);
        });
    });

    // Display initial tickets for the active tab (Getting Started)
    const activeTabId = document.querySelector('#helpCenterTabs .nav-link.active').id;
    displayCategoryTickets(activeTabId, categoryData[activeTabId] || []);
}

function displayCategoryTickets(categoryId, tickets) {
    const ticketListContainer = document.querySelector('.ticket-list-wrapper .d-flex.flex-column');

    // Clear existing tickets
    ticketListContainer.innerHTML = '';

    // Add new tickets
    tickets.forEach(ticket => {
        const ticketHTML = `
            <div class="card mb-0 mt-3" data-status="${ticket.status}">
                <div class="card-body">
                    <div class="d-flex align-items-center gap-5 mb-4">
                        <h6 class="flex-grow-1 mb-0">
                            <a href="#!" class="text-reset ticket-btn" data-ticket-id="${ticket.id}">#2023-${ticket.id} تیکت</a>
                        </h6>
                        <div class="d-flex align-items-center gap-4">
                            <p class="fs-sm text-muted">${getRandomTime()}</p>
                            <div class="dropdown">
                                <a href="#!" class="link link-custom-primary" id="dropdownTicketId${ticket.id}" data-bs-toggle="dropdown" aria-expanded="false" aria-label="dropdown-button">
                                    <i class="ri-more-2-fill"></i>
                                </a>
                                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="dropdownTicketId${ticket.id}">
                                    <li>
                                        <a href="#!" class="dropdown-item">پاسخ به وظیفه</a>
                                    </li>
                                    <li>
                                        <a href="#!" class="dropdown-item">جزئیات بیشتر</a>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <h6 class="mb-1"><a href="#!" class="text-reset ticket-btn" data-ticket-id="${ticket.id}">${ticket.title}</a></h6>
                    <p class="text-muted line-clamp-2">${ticket.content}</p>
                    <div class="d-flex flex-wrap align-items-center gap-4 mt-5">
                        <div class="d-flex align-items-center gap-2 flex-grow-1">
                            <img src="${ticket.avatar}" loading="lazy" alt="user" class="rounded-circle size-8">
                            <h6 class="mb-0">${ticket.author}</h6>
                        </div>
                        <div class="flex-shrink-0 d-flex gap-2">
                            ${ticket.tags.map(tag => `<a href="#!" class="link link-custom-primary">${tag}</a>`).join('')}
                        </div>
                        <div class="flex-shrink-0">
                            <a href="#!" class="link link-custom-primary">
                                <i class="ri-chat-3-line align-middle size-5 me-1"></i> <span>${Math.floor(Math.random() * 5) + 1}</span>
                            </a>
                        </div>
                        <div class="flex-shrink-0 ms-2">
                            <span class="badge ${getStatusBadgeClass(ticket.status)}">${ticket.status}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        ticketListContainer.innerHTML += ticketHTML;
    });

    // Re-initialize ticket buttons after updating the DOM
    initializeTicketButtons();

    // Make the category data globally accessible for filtering
    window.categoryData = window.categoryData || {};
    window.categoryData[categoryId] = tickets;

    // Apply current filter if any is active
    const activeTab = document.querySelector('.nav-underline .nav-link.active');
    if (activeTab) {
        filterTickets(activeTab.id);
    }
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'فعال':
            return 'bg-success text-white';
        case 'بسته شده':
            return 'bg-secondary text-white';
        case 'حذف شده':
            return 'bg-danger text-white';
        default:
            return 'bg-info text-white';
    }
}


// Helper function to generate random time
function getRandomTime() {
    const hours = Math.floor(Math.random() * 12) + 1;
    const minutes = Math.floor(Math.random() * 60);
    const ampm = Math.random() > 0.5 ? 'صبح' : 'بعد از ظهر';
    return `${hours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
}

// Function to handle the ticket tabs
function initializeTicketTabs() {
    const ticketTabs = document.querySelectorAll('.nav-underline .nav-link');

    ticketTabs.forEach(tab => {
        tab.addEventListener('click', function () {
            // Remove active class from all tabs
            ticketTabs.forEach(t => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });

            // Add active class to clicked tab
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');

            // Filter tickets based on the selected tab
            const tabId = this.id;
            filterTickets(tabId);
        });
    });
}

function filterTickets(tabId) {
    // Map tab IDs to ticket status
    const statusMap = {
        'allTickets-tab': 'همه',
        'active-tab': 'فعال',
        'closed-tab': 'بسته شده',
        'delete-tab': 'حذف شده'
    };

    const filterStatus = statusMap[tabId];
    const ticketCards = document.querySelectorAll('.ticket-list-wrapper .card');

    // Loop through all ticket cards
    ticketCards.forEach(card => {
        const ticketStatus = card.getAttribute('data-status');

        const ticketTitle = card.querySelector('h6.mb-1 a').textContent;
        const ticketId = card.querySelector('.ticket-btn').getAttribute('data-ticket-id');

        let status = '';
        for (const category in window.categoryData) {
            const ticket = window.categoryData[category].find(t => t.id === ticketId);
            if (ticket) {
                status = ticket.status;
                break;
            }
        }

        // Show/hide based on filter selection
        if (filterStatus === 'همه' || status === filterStatus) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });

    // Update total count (if you have a count element)
    updateTicketCount();
}

// Helper function to update the visible ticket count
function updateTicketCount() {
    const visibleTickets = document.querySelectorAll('.ticket-list-wrapper .card[style="display: ;"], .ticket-list-wrapper .card:not([style*="display: none"])');
    const countElement = document.querySelector('.ticket-count');

    if (countElement) {
        countElement.textContent = `${visibleTickets.length} tickets`;
    }
}

// Function to handle the search functionality
function initializeSearchFunctionality() {
    const searchInput = document.getElementById('searchInput');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase();
            searchTickets(searchTerm);
        });
    }
}

function searchTickets(searchTerm) {
    const ticketCards = document.querySelectorAll('.ticket-list-wrapper .card');

    ticketCards.forEach(card => {
        const title = card.querySelector('h6.mb-1 a').textContent.toLowerCase();
        const content = card.querySelector('p.text-muted').textContent.toLowerCase();

        if (title.includes(searchTerm) || content.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Function to handle ticket view buttons
function initializeTicketButtons() {
    const ticketButtons = document.querySelectorAll('.ticket-btn');
    const ticketList = document.getElementById('ticketList');
    const ticketContent = document.getElementById('ticketContent');
    const closeButton = document.querySelector('.close-btn');

    ticketButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();

            // Get ticket ID for potential API calls in a real application
            const ticketId = this.getAttribute('data-ticket-id') || '0001';

            // Hide ticket list, show ticket content
            ticketList.classList.add('d-none');
            ticketContent.classList.remove('d-none');
        });
    });

    if (closeButton) {
        closeButton.addEventListener('click', function (e) {
            e.preventDefault();

            // Hide ticket content, show ticket list
            ticketContent.classList.add('d-none');
            ticketList.classList.remove('d-none');
        });
    }
}
