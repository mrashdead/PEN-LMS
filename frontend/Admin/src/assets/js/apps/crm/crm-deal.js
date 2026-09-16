import { icons, createIcons } from "lucide";

const dealsData = [
    {
        id: 1,
        logo: "assets/images/brands/img-02.png",
        title: "بازبینی استراتژی بازاریابی",
        amount: 12500,
        date: "27 فروردین 1403",
        company: "شرکت مارکت‌بوست",
        description: "بازبینی و به‌روزرسانی استراتژی‌های بازاریابی برای سه‌ماهه دوم.",
        status: {
            expired: true,
            active: true
        }
    },
    {
        id: 2,
        logo: "assets/images/brands/img-03.png",
        title: "رویداد رونمایی محصول",
        amount: 20000,
        date: "22 خرداد 1403",
        company: "شرکت تکنکس",
        description: "برنامه‌ریزی و اجرای رویداد رونمایی برای خط محصولات جدید.",
        status: {
            expired: true,
            active: false
        }
    },
    {
        id: 3,
        logo: "assets/images/brands/img-04.png",
        title: "بازبینی مالی سه‌ماهه",
        amount: 18200,
        date: "8 خرداد 1403",
        company: "شرکت فایننس‌وایز",
        description: "بازبینی عملکرد مالی برای سه‌ماهه اول سال 1403.",
        status: {
            expired: true,
            active: true
        }
    },
    {
        id: 4,
        logo: "assets/images/brands/img-05.png",
        title: "جلسه با مشتری",
        amount: 8500,
        date: "16 خرداد 1403",
        company: "راهکارهای مشتری",
        description: "جلسه با مشتریان بالقوه برای بررسی نیازهای پروژه.",
        status: {
            expired: true,
            active: false
        }
    },
    {
        id: 5,
        logo: "assets/images/brands/img-06.png",
        title: "طراحی مجدد وب‌سایت",
        amount: 14000,
        date: "12 اردیبهشت 1403",
        company: "شرکت وب‌ورکس",
        description: "طراحی مجدد وب‌سایت شرکت برای تجربه بهتر کاربری.",
        status: {
            expired: true,
            active: true
        }
    },
    {
        id: 6,
        logo: "assets/images/brands/img-07.png",
        title: "برنامه آموزش کارکنان",
        amount: 10000,
        date: "12 خرداد 1403",
        company: "تالنت‌هاب",
        description: "توسعه و اجرای برنامه آموزشی جامع برای کارکنان.",
        status: {
            expired: true,
            active: true
        }
    },
    {
        id: 7,
        logo: "assets/images/brands/img-08.png",
        title: "کمپین شبکه‌های اجتماعی",
        amount: 16500,
        date: "21 اردیبهشت 1403",
        company: "شبکه اجتماعی نت",
        description: "راه‌اندازی کمپین هدفمند در شبکه‌های اجتماعی برای افزایش دیده شدن برند.",
        status: {
            expired: true,
            active: false
        }
    },
    {
        id: 8,
        logo: "assets/images/brands/img-09.png",
        title: "بهینه‌سازی زنجیره تأمین",
        amount: 22000,
        date: "12 خرداد 1403",
        company: "لاجی‌تک",
        description: "بهینه‌سازی زنجیره تأمین برای کاهش هزینه‌ها و افزایش کارایی.",
        status: {
            expired: true,
            active: false
        }
    },
    {
        id: 9,
        logo: "assets/images/brands/img-02.png",
        title: "پروژه تحلیل داده‌ها",
        amount: 17500,
        date: "31 خرداد 1403",
        company: "دیتاسمارت آنالیتیکس",
        description: "تحلیل داده‌های مشتریان برای شناسایی روندها و فرصت‌ها.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 10,
        logo: "assets/images/brands/img-03.png",
        title: "توسعه اپلیکیشن موبایل",
        amount: 25000,
        date: "9 مرداد 1403",
        company: "اپ‌جنیوس",
        description: "توسعه یک اپلیکیشن موبایل برای تعامل با مشتریان.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 11,
        logo: "assets/images/brands/img-04.png",
        title: "مهاجرت به فضای ابری",
        amount: 30000,
        date: "25 مرداد 1403",
        company: "راهکارهای کلودتک",
        description: "انتقال زیرساخت شرکت به سرویس‌های مبتنی بر ابر.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 12,
        logo: "assets/images/brands/img-05.png",
        title: "بهینه‌سازی سئو",
        amount: 9500,
        date: "11 تیر 1403",
        company: "مشاوره سرچ‌پرو",
        description: "بهینه‌سازی وب‌سایت برای رتبه‌بندی بهتر در موتورهای جستجو.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 13,
        logo: "assets/images/brands/img-06.png",
        title: "تحلیل بازخورد مشتری",
        amount: 13200,
        date: "1 مرداد 1403",
        company: "فیدبک‌پرو",
        description: "تحلیل بازخورد مشتریان و اعمال بهبودها.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 14,
        logo: "assets/images/brands/img-07.png",
        title: "ممیزی امنیت سایبری",
        amount: 19800,
        date: "20 مرداد 1403",
        company: "سکیورنت تکنولوژیز",
        description: "انجام ممیزی جامع از اقدامات امنیت سایبری.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 15,
        logo: "assets/images/brands/img-08.png",
        title: "استراتژی تولید محتوا",
        amount: 11500,
        date: "4 تیر 1403",
        company: "کانتنت‌وایز مدیا",
        description: "توسعه استراتژی تولید و انتشار محتوا.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 16,
        logo: "assets/images/brands/img-09.png",
        title: "یکپارچه‌سازی سیستم‌های منابع انسانی",
        amount: 15700,
        date: "15 تیر 1403",
        company: "اچ‌آرتک سولوشنز",
        description: "یکپارچه‌سازی سیستم‌های مختلف منابع انسانی برای بهره‌وری بیشتر.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 17,
        logo: "assets/images/brands/img-02.png",
        title: "طرح توسعه کسب‌وکار",
        amount: 29000,
        date: "25 شهریور 1403",
        company: "گرومت‌مکس مشاوره",
        description: "توسعه یک برنامه جامع برای گسترش کسب‌وکار.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 18,
        logo: "assets/images/brands/img-03.png",
        title: "پیش‌بینی مالی",
        amount: 21500,
        date: "11 شهریور 1403",
        company: "فورکست‌پرو فایننس",
        description: "ایجاد پیش‌بینی‌های مالی برای سال مالی پیش‌رو.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 19,
        logo: "assets/images/brands/img-04.png",
        title: "بهینه‌سازی فرآیند جذب مشتری",
        amount: 12800,
        date: "30 مرداد 1403",
        company: "آن‌بوردپرو",
        description: "بهینه‌سازی فرآیند جذب مشتری برای حفظ بهتر آن‌ها.",
        status: {
            expired: false,
            active: true
        }
    },
    {
        id: 20,
        logo: "assets/images/brands/img-05.png",
        title: "سیستم مدیریت فروشندگان",
        amount: 18900,
        date: "20 شهریور 1403",
        company: "وندرتک سیستمز",
        description: "اجرای سیستم جدید مدیریت فروشندگان برای همکاری بهتر.",
        status: {
            expired: false,
            active: true
        }
    }

];

document.addEventListener('DOMContentLoaded', () => {
    // Pagination settings
    const itemsPerPage = 8;
    let currentPage = 1;
    let filteredData = [...dealsData];
    let totalPages = Math.ceil(dealsData.length / itemsPerPage);
    const searchInput = document.getElementById('searchDealInput');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }
    // Initial render
    renderDeals(currentPage);
    renderPagination(currentPage, totalPages);

    /**
     * Handle search input
     * @param {Event} e - Input event
     */
    function handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase().trim();

        if (searchTerm === '') {
            filteredData = [...dealsData];
        } else {
            filteredData = dealsData.filter(deal => {
                return (
                    deal.title.toLowerCase().includes(searchTerm) ||
                    deal.company.toLowerCase().includes(searchTerm) ||
                    deal.description.toLowerCase().includes(searchTerm) ||
                    deal.date.toLowerCase().includes(searchTerm) ||
                    deal.amount.toString().includes(searchTerm)
                );
            });
        }

        // Reset to first page and update view
        currentPage = 1;
        totalPages = Math.ceil(filteredData.length / itemsPerPage);
        renderDeals(currentPage);
        renderPagination(currentPage, totalPages);
    }

    /**
     * Render deals based on the current page
     * @param {number} page - Current page number
     */
    function renderDeals(page) {
        const startIndex = (page - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, filteredData.length);
        const currentDeals = filteredData.slice(startIndex, endIndex);

        const gridContainer = document.querySelector('#gridView .row:not(:last-child)');
        gridContainer.innerHTML = '';

        if (currentDeals.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'col-12 text-center py-5';
            noResults.innerHTML = `
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
                <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0l-4.331-4.331"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
              </svg>
              <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
              <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
            </div>
          `;
            gridContainer.appendChild(noResults);
        } else {
            currentDeals.forEach(deal => {
                const dealCard = createDealCard(deal);
                gridContainer.appendChild(dealCard);
            });
        }

        // Update showing results text
        const resultsText = document.querySelector('#pagination-courting-info');
        if (filteredData.length > 0) {
            resultsText.innerHTML = `نمایش <b class="me-1">${startIndex + 1}-${endIndex}</b>از<b class="ms-1">${filteredData.length}</b> نتیجه`;
        } else {
            resultsText.innerHTML = `نمایش <b class="me-1">0</b>از<b class="ms-1">0</b> نتیجه`;
        }
    }
    /**
      * Create a deal card element
      * @param {Object} deal - Deal data object
      * @returns {HTMLElement} Deal card element
      */
    function createDealCard(deal) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-xxl-3';

        col.innerHTML = `
      <div class="card">
        <div class="card-body">
          <div class="d-flex align-items-center gap-3 mb-4">
            <div class="size-12 rounded border avatar">
              <img src="${deal.logo}" loading="lazy" alt="" class="size-7">
            </div>
            <div class="flex-grow-1">
              <h6 class="mb-1"><a href="#!" class="text-reset">${deal.title}</a></h6>
              <p class="text-muted"><span>${deal.amount.toLocaleString()} دلار</span><span>- <span>${deal.date}</span></span></p>
            </div>
          </div>
          <p class="fw-medium mb-1">${deal.company}</p>
          <p class="text-muted">${deal.description}</p>
          <div class="d-flex align-items-center gap-2 flex-wrap my-4">
            ${deal.status.expired ? '<span class="badge bg-pink-subtle text-pink border border-pink-subtle">منقضی شده</span>' : ''}
            ${deal.status.active ?
                '<span class="badge bg-success-subtle text-success border border-success-subtle">فعال</span>' :
                '<span class="badge bg-light-subtle text-muted border border-light-subtle">غیر فعال</span>'}
          </div>
          <div class="d-flex gap-2 align-items-center flex-wrap">
            <button class="btn btn-dashed-warning" data-bs-toggle="modal" data-bs-target="#messageModal"><i class="ri-message-2-line me-1"></i>پیام</button>
            <button class="btn btn-dashed-primary" data-bs-toggle="modal" data-bs-target="#callModal2"><i class="ri-phone-line me-1"></i>تماس</button>
            <button class="btn btn-light btn-icon"><i data-lucide="trash" class="size-4"></i></button>
          </div>
        </div>
      </div>
    `;

        return col;
    }

    /**
     * Render pagination controls
     * @param {number} currentPage - Current active page
     * @param {number} totalPages - Total number of pages
     */

    /**
     * Render pagination controls
     * @param {number} currentPage - Current active page
     * @param {number} totalPages - Total number of pages
     */
    function renderPagination(currentPage, totalPages) {
        const paginationContainer = document.querySelector('.pagination');
        paginationContainer.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        paginationContainer.appendChild(prevLi);

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${currentPage === i ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#!" data-page="${i}">${i}</a>`;
            paginationContainer.appendChild(pageLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        paginationContainer.appendChild(nextLi);

        // Add event listeners to page links
        const pageLinks = paginationContainer.querySelectorAll('.page-link');
        pageLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();

                if (link.textContent.includes('قبلی') && currentPage > 1) {
                    changePage(currentPage - 1);
                } else if (link.textContent.includes('بعدی') && currentPage < totalPages) {
                    changePage(currentPage + 1);
                } else if (link.dataset.page) {
                    changePage(parseInt(link.dataset.page));
                }
            });
        });

        createIcons({ icons });
    }

    /**
   * Change the current page
   * @param {number} page - Page number to change to
   */
    function changePage(page) {
        currentPage = page;
        renderDeals(currentPage);
        renderPagination(currentPage, totalPages);
    }
});

document.addEventListener('DOMContentLoaded', () => {
    // Pagination settings
    const itemsPerPage = 8;
    let currentPage = 1;
    let filteredData = [...dealsData];
    let totalPages = Math.ceil(dealsData.length / itemsPerPage);
    const searchInput = document.getElementById('searchDealInput');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }

    // View toggling
    const gridViewTab = document.getElementById('grid-view-tab');
    const listViewTab = document.getElementById('list-view-tab');
    let currentView = 'grid'; // Default view

    if (gridViewTab && listViewTab) {
        gridViewTab.addEventListener('click', () => {
            currentView = 'grid';
            renderDeals(currentPage);
            renderPagination(currentPage, totalPages);
        });

        listViewTab.addEventListener('click', () => {
            currentView = 'list';
            renderDeals(currentPage);
            renderPagination(currentPage, totalPages);
        });
    }

    // Initial render
    renderDeals(currentPage);
    renderPagination(currentPage, totalPages);

    /**
     * Handle search input
     * @param {Event} e - Input event
     */
    function handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase().trim();

        if (searchTerm === '') {
            filteredData = [...dealsData];
        } else {
            filteredData = dealsData.filter(deal => {
                return (
                    deal.title.toLowerCase().includes(searchTerm) ||
                    deal.company.toLowerCase().includes(searchTerm) ||
                    deal.description.toLowerCase().includes(searchTerm) ||
                    deal.date.toLowerCase().includes(searchTerm) ||
                    deal.amount.toString().includes(searchTerm)
                );
            });
        }

        // Reset to first page and update view
        currentPage = 1;
        totalPages = Math.ceil(filteredData.length / itemsPerPage);
        renderDeals(currentPage);
        renderPagination(currentPage, totalPages);
    }

    /**
     * Render deals based on the current page and view
     * @param {number} page - Current page number
     */
    function renderDeals(page) {
        const startIndex = (page - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, filteredData.length);
        const currentDeals = filteredData.slice(startIndex, endIndex);

        if (currentView === 'grid') {
            renderGridView(currentDeals, startIndex, endIndex);
        } else {
            renderListView(currentDeals, startIndex, endIndex);
        }
    }

    /**
     * Render grid view
     * @param {Array} deals - Array of deals to display
     * @param {number} startIndex - Start index of current page
     * @param {number} endIndex - End index of current page
     */
    function renderGridView(deals, startIndex, endIndex) {
        const gridContainer = document.querySelector('#gridView .row:not(:last-child)');
        if (!gridContainer) return;

        gridContainer.innerHTML = '';

        if (deals.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'col-12 text-center py-5';
            noResults.innerHTML = `
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
                <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0l-4.331-4.331"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
              </svg>
              <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
              <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
            </div>
          `;

            gridContainer.appendChild(noResults);
        } else {
            deals.forEach(deal => {
                const dealCard = createDealCard(deal);
                gridContainer.appendChild(dealCard);
            });
        }

        // Update showing results text
        updateResultsText(startIndex, endIndex);
    }

    /**
     * Render list view
     * @param {Array} deals - Array of deals to display
     * @param {number} startIndex - Start index of current page
     * @param {number} endIndex - End index of current page
     */
    function renderListView(deals, startIndex, endIndex) {
        const listContainer = document.querySelector('#listView .row:not(:last-child)');
        if (!listContainer) return;

        listContainer.innerHTML = '';

        if (deals.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'col-12 text-center py-5';
            noResults.innerHTML = `
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
                <path fill="url(#SVGID_1__h35ynqzIJzH4_gr1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748c0-7.27-5.894-13.164-13.164-13.164S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331c1.715,1.715,4.496,1.715,6.211,0C41.751,38.321,41.751,35.541,40.036,33.826z"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0l-4.331-4.331"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
              </svg>
              <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
              <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
            </div>
          `;

            listContainer.appendChild(noResults);
        } else {
            deals.forEach(deal => {
                const dealRow = createDealRow(deal);
                listContainer.appendChild(dealRow);
            });
        }

        // Update showing results text
        updateResultsText(startIndex, endIndex);
    }

    /**
     * Create a deal card element for grid view
     * @param {Object} deal - Deal data object
     * @returns {HTMLElement} Deal card element
     */
    function createDealCard(deal) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-xxl-3';

        col.innerHTML = `
      <div class="card">
        <div class="card-body">
          <div class="d-flex align-items-center gap-3 mb-4">
            <div class="size-12 rounded border avatar">
              <img src="${deal.logo}" loading="lazy" alt="" class="size-7">
            </div>
            <div class="flex-grow-1">
              <h6 class="mb-1"><a href="#!" class="text-reset">${deal.title}</a></h6>
              <p class="text-muted"><span>${deal.amount.toLocaleString()} دلار</span><span>- <span>${deal.date}</span></span></p>
            </div>
          </div>
          <p class="fw-medium mb-1">${deal.company}</p>
          <p class="text-muted">${deal.description}</p>
          <div class="d-flex align-items-center gap-2 flex-wrap my-4">
            ${deal.status.expired ? '<span class="badge bg-pink-subtle text-pink border border-pink-subtle">منقضی شده</span>' : ''}
            ${deal.status.active ?
                '<span class="badge bg-success-subtle text-success border border-success-subtle">فعال</span>' :
                '<span class="badge bg-light-subtle text-muted border border-light-subtle">غیر فعال</span>'}
          </div>
          <div class="d-flex gap-2 align-items-center flex-wrap">
            <button class="btn btn-dashed-warning" data-bs-toggle="modal" data-bs-target="#messageModal"><i class="ri-message-2-line me-1"></i>پیام</button>
            <button class="btn btn-dashed-primary" data-bs-toggle="modal" data-bs-target="#callModal2"><i class="ri-phone-line me-1"></i>تماس</button>
            <button class="btn btn-light btn-icon"><i data-lucide="trash" class="size-4"></i></button>
          </div>
        </div>
      </div>
    `;

        return col;
    }

    /**
     * Create a deal row element for list view
     * @param {Object} deal - Deal data object
     * @returns {HTMLElement} Deal row element
     */
    function createDealRow(deal) {
        const col = document.createElement('div');
        col.className = 'col-12';

        col.innerHTML = `
      <div class="card">
        <div class="card-body d-flex flex-column flex-md-row justify-content-between gap-2 gap-md-5 text-nowrap">
          <div class="d-flex align-items-center gap-3">
            <div class="size-12 rounded border avatar">
              <img src="${deal.logo}" loading="lazy" alt="" class="size-7">
            </div>
            <div class="flex-grow-1">
              <h6 class="mb-1"><a href="#!" class="text-reset">${deal.title}</a></h6>
              <p class="text-muted">${deal.amount.toLocaleString()} دلار</p>
            </div>
          </div>
          <p class="min-w-28 text-truncate text-muted">${deal.date}</p>
          <p class="min-w-28 text-truncate text-muted">${deal.company}</p>
          <div class="d-flex gap-2 w-28">
            ${deal.status.expired ? '<div><span class="badge bg-pink-subtle text-pink border border-pink-subtle">منقضی شده</span></div>' : ''}
            ${deal.status.active ?
                '<div><span class="badge bg-success-subtle text-success border border-success-subtle">فعال</span></div>' :
                '<div><span class="badge bg-light-subtle text-muted border border-light-subtle">غیر فعال</span></div>'}
          </div>
          <div class="d-flex gap-2 align-items-center flex-wrap">
            <button class="btn btn-dashed-warning" data-bs-toggle="modal" data-bs-target="#messageModal"><i class="ri-message-2-line me-1"></i>پیام</button>
            <button class="btn btn-dashed-primary" data-bs-toggle="modal" data-bs-target="#callModal2"><i class="ri-phone-line me-1"></i>تماس</button>
            <button class="btn btn-light btn-icon"><i data-lucide="trash" class="size-4"></i></button>
          </div>
        </div>
      </div>
    `;

        return col;
    }

    /**
     * Update the results text showing current page info
     * @param {number} startIndex - Start index of current page
     * @param {number} endIndex - End index of current page
     */
    function updateResultsText(startIndex, endIndex) {
        const resultsTexts = document.querySelectorAll('.text-muted.text-center.text-md-start.mb-0');
        resultsTexts.forEach(resultsText => {
            if (filteredData.length > 0) {
                resultsText.innerHTML = `نمایش <b class="me-1">${startIndex + 1}-${endIndex}</b>از<b class="ms-1">${filteredData.length}</b> نتیجه`;
            } else {
                resultsText.innerHTML = `نمایش <b class="me-1">0</b>از<b class="ms-1">0</b> نتیجه`;
            }
        });
    }

    /**
     * Render pagination controls
     * @param {number} currentPage - Current active page
     * @param {number} totalPages - Total number of pages
     */
    function renderPagination(currentPage, totalPages) {
        const paginationContainers = document.querySelectorAll('.pagination');

        paginationContainers.forEach(paginationContainer => {
            paginationContainer.innerHTML = '';

            // Previous button
            const prevLi = document.createElement('li');
            prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
            prevLi.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
            paginationContainer.appendChild(prevLi);

            // Page numbers
            for (let i = 1; i <= totalPages; i++) {
                const pageLi = document.createElement('li');
                pageLi.className = `page-item ${currentPage === i ? 'active' : ''}`;
                pageLi.innerHTML = `<a class="page-link" href="#!" data-page="${i}">${i}</a>`;
                paginationContainer.appendChild(pageLi);
            }

            // Next button
            const nextLi = document.createElement('li');
            nextLi.className = `page-item ${currentPage === totalPages || totalPages === 0 ? 'disabled' : ''}`;
            nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
            paginationContainer.appendChild(nextLi);

            // Add event listeners to page links
            const pageLinks = paginationContainer.querySelectorAll('.page-link');
            pageLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();

                    if (link.textContent.includes('قبلی') && currentPage > 1) {
                        changePage(currentPage - 1);
                    } else if (link.textContent.includes('بعدی') && currentPage < totalPages) {
                        changePage(currentPage + 1);
                    } else if (link.dataset.page) {
                        changePage(parseInt(link.dataset.page));
                    }
                });
            });
        });

        createIcons({ icons });
    }

    /**
     * Change the current page
     * @param {number} page - Page number to change to
     */
    function changePage(page) {
        currentPage = page;
        renderDeals(currentPage);
        renderPagination(currentPage, totalPages);
    }
});