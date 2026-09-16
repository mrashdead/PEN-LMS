import { createIcons,icons } from "lucide";

VirtualSelect.init({
  ele: '#sample-select',
  options: [
    { label: 'همه', value: '1' },
    { label: 'ماه قبل', value: '2' },
    { label: 'این ماه', value: '3' },
    { label: 'هفته قبل', value: '4' },
    { label: 'سال قبل', value: '5' },
    { label: 'امسال', value: '6' },
  ],
  selectedValue: 0
});
// User data extracted from HTML
const userData = [
  {
    id: 1,
    name: "ویکتور پرولو",
    role: "طراح وب",
    avatar: "assets/images/avatar/user-11.png",
    tasks: 15,
    earning: "8,500 تومان"
  },
  {
    id: 2,
    name: "سابین آیکل",
    role: "توسعه‌دهنده ASP.Net",
    avatar: "assets/images/avatar/user-13.png",
    tasks: 4,
    earning: "4,987 تومان"
  },
  {
    id: 3,
    name: "دیانا هوبر",
    role: "توسعه‌دهنده React",
    avatar: "assets/images/avatar/user-15.png",
    tasks: 19,
    earning: "9,065 تومان"
  },
  {
    id: 4,
    name: "رابرت فورستر",
    role: "توسعه‌دهنده Laravel",
    avatar: "assets/images/avatar/user-14.png",
    tasks: 8,
    earning: "11,000 تومان"
  },
  {
    id: 5,
    name: "امیلی کلارک",
    role: "طراح UI/UX",
    avatar: "assets/images/avatar/user-16.png",
    tasks: 22,
    earning: "7,250 تومان"
  },
  {
    id: 6,
    name: "جیمز اسمیت",
    role: "توسعه‌دهنده Java",
    avatar: "assets/images/avatar/user-17.png",
    tasks: 10,
    earning: "10,500 تومان"
  },
  {
    id: 7,
    name: "اولیویا براون",
    role: "توسعه‌دهنده PHP",
    avatar: "assets/images/avatar/user-18.png",
    tasks: 13,
    earning: "6,800 تومان"
  },
  {
    id: 8,
    name: "لیام جانسون",
    role: "توسعه‌دهنده Python",
    avatar: "assets/images/avatar/user-19.png",
    tasks: 7,
    earning: "9,200 تومان"
  },
  {
    id: 9,
    name: "اما ویلسون",
    role: "توسعه‌دهنده فرانت‌اند",
    avatar: "assets/images/avatar/user-12.png",
    tasks: 12,
    earning: "7,800 تومان"
  },
  {
    id: 10,
    name: "نوآ گارسیا",
    role: "توسعه‌دهنده فول‌استک",
    avatar: "assets/images/avatar/user-20.png",
    tasks: 16,
    earning: "12,400 تومان"
  },
  {
    id: 11,
    name: "سوفیا مارتینز",
    role: "مهندس DevOps",
    avatar: "assets/images/avatar/user-21.png",
    tasks: 9,
    earning: "10,200 تومان"
  },
  {
    id: 12,
    name: "بنجامین رودریگز",
    role: "توسعه‌دهنده بک‌اند",
    avatar: "assets/images/avatar/user-22.png",
    tasks: 14,
    earning: "9,800 تومان"
  },
  {
    id: 13,
    name: "ایزابلا لوپز",
    role: "توسعه‌دهنده موبایل",
    avatar: "assets/images/avatar/user-23.png",
    tasks: 6,
    earning: "8,700 تومان"
  },
  {
    id: 14,
    name: "ویلیام لی",
    role: "دانشمند داده",
    avatar: "assets/images/avatar/user-24.png",
    tasks: 11,
    earning: "13,500 تومان"
  },
  {
    id: 15,
    name: "میا گونزالس",
    role: "مهندس تضمین کیفیت (QA)",
    avatar: "assets/images/avatar/user-25.png",
    tasks: 18,
    earning: "8,200 تومان"
  },
  {
    id: 16,
    name: "الکساندر هرناندز",
    role: "مدیر سیستم",
    avatar: "assets/images/avatar/user-26.png",
    tasks: 5,
    earning: "11,300 تومان"
  },
  {
    id: 17,
    name: "شارلوت پرز",
    role: "معمار رایانش ابری",
    avatar: "assets/images/avatar/user-27.png",
    tasks: 20,
    earning: "14,500 تومان"
  },
  {
    id: 18,
    name: "دنیل ترنر",
    role: "مهندس امنیت",
    avatar: "assets/images/avatar/user-28.png",
    tasks: 7,
    earning: "12,000 تومان"
  },
  {
    id: 19,
    name: "آملیا فیلیپس",
    role: "پژوهشگر UX",
    avatar: "assets/images/avatar/user-29.png",
    tasks: 12,
    earning: "9,400 تومان"
  },
  {
    id: 20,
    name: "هنری کمپبل",
    role: "لید فنی",
    avatar: "assets/images/avatar/user-30.png",
    tasks: 25,
    earning: "15,200 تومان"
  },
  {
    id: 21,
    name: "الیزابت بیکر",
    role: "مدیر محصول",
    avatar: "assets/images/avatar/user-31.png",
    tasks: 17,
    earning: "13,800 تومان"
  },
  {
    id: 22,
    name: "مایکل استوارت",
    role: "مدیر ارشد فناوری (CTO)",
    avatar: "assets/images/avatar/user-32.png",
    tasks: 8,
    earning: "18,500 تومان"
  },
  {
    id: 23,
    name: "اولین موریس",
    role: "مهندس هوش مصنوعی",
    avatar: "assets/images/avatar/user-33.png",
    tasks: 14,
    earning: "13,200 تومان"
  },
  {
    id: 24,
    name: "جوزف راجرز",
    role: "توسعه‌دهنده بلاک‌چین",
    avatar: "assets/images/avatar/user-34.png",
    tasks: 9,
    earning: "14,800 تومان"
  },
  {
    id: 25,
    name: "اسکارلت رید",
    role: "معمار نرم‌افزار",
    avatar: "assets/images/avatar/user-35.png",
    tasks: 21,
    earning: "16,700 تومان"
  },
  {
    id: 26,
    name: "توماس کوک",
    role: "توسعه‌دهنده بازی",
    avatar: "assets/images/avatar/user-36.png",
    tasks: 16,
    earning: "11,900 تومان"
  },
  {
    id: 27,
    name: "گریس مورگان",
    role: "مدیر پایگاه داده",
    avatar: "assets/images/avatar/user-37.png",
    tasks: 10,
    earning: "10,600 تومان"
  },
  {
    id: 28,
    name: "ساموئل پارکر",
    role: "مهندس شبکه",
    avatar: "assets/images/avatar/user-38.png",
    tasks: 7,
    earning: "12,300 تومان"
  },
  {
    id: 29,
    name: "کلویی کوپر",
    role: "تحلیل‌گر کسب‌وکار",
    avatar: "assets/images/avatar/user-39.png",
    tasks: 15,
    earning: "9,700 تومان"
  },
  {
    id: 30,
    name: "جک پیترسون",
    role: "مدیر ارشد اطلاعات (CIO)",
    avatar: "assets/images/avatar/user-40.png",
    tasks: 6,
    earning: "17,800 تومان"
  },
  {
    id: 31,
    name: "زویی گری",
    role: "مهندس یادگیری ماشین",
    avatar: "assets/images/avatar/user-41.png",
    tasks: 11,
    earning: "13,400 تومان"
  },
  {
    id: 32,
    name: "لوک جیمز",
    role: "نویسنده فنی",
    avatar: "assets/images/avatar/user-42.png",
    tasks: 8,
    earning: "8,900 تومان"
  },
  {
    id: 33,
    name: "لیلی آدامز",
    role: "مدیر پروژه",
    avatar: "assets/images/avatar/user-43.png",
    tasks: 19,
    earning: "12,700 تومان"
  }
];

// Pagination settings
let currentPage = 1;
const itemsPerPage = 8; // Show 8 users per page
const totalUsers = userData.length;
const totalPages = Math.ceil(totalUsers / itemsPerPage);

// DOM elements (to be initialized when DOM is ready)
let userContainer;
let paginationContainer;
let userCountInfo;

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  // Get DOM elements
  userContainer = document.querySelector('#userList');
  paginationContainer = document.querySelector('.pagination');
  userCountInfo = document.querySelector('#showingResults');

  // Update the total user count in the header
  const userCountHeader = document.querySelector('#userCountHeader');
  if (userCountHeader) {
    userCountHeader.textContent = `کاربران (${totalUsers})`;
  }

  // Initial render
  renderUsers();
  renderPagination();
  updateUserCountInfo();
});

// Function to render users based on current page
function renderUsers() {
  if (!userContainer) return;

  // Clear existing content
  userContainer.innerHTML = '';

  // Calculate start and end indices for current page
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalUsers);

  // Get current page data
  const currentPageData = userData.slice(startIndex, endIndex);

  // Generate HTML for each user
  currentPageData.forEach(user => {
    const userCard = document.createElement('div');
    userCard.className = 'col';
    userCard.innerHTML = `
          <div class="card text-center">
              <div class="card-body">
                  <img src="${user.avatar}" loading="lazy" alt="${user.name}" class="mx-auto mb-4 rounded-circle size-14">
                  <h6 class="mb-1"><a href="pages-user.html" class="text-reset">${user.name}</a></h6>
                  <p class="text-muted">${user.role}</p>
                  <div class="row gx-4 mt-4">
                      <div class="col-6">
                          <div class="p-3 border border-dashed rounded">
                              <h6 class="mb-0">${user.tasks}</h6>
                              <p class="text-muted">وظایف</p>
                          </div>
                      </div>
                      <div class="col-6">
                          <div class="p-3 border border-dashed rounded">
                              <h6 class="mb-0">${user.earning}</h6>
                              <p class="text-muted">درآمد</p>
                          </div>
                      </div>
                  </div>
              </div>
          </div>
      `;
    userContainer.appendChild(userCard);
  });
}

// Function to render pagination controls
function renderPagination() {
  if (!paginationContainer) return;

  paginationContainer.innerHTML = '';

  // Previous button
  const prevLi = document.createElement('li');
  prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
  prevLi.innerHTML = `<a class="page-link" href="#!" onclick="changePage(${currentPage - 1})"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
  paginationContainer.appendChild(prevLi);

  // Page numbers
  // Show max 5 page numbers with current page in the middle when possible
  const maxVisiblePages = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
  let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

  // Adjust start page if we're near the end
  if (endPage - startPage + 1 < maxVisiblePages) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
    const pageLi = document.createElement('li');
    pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
    pageLi.innerHTML = `<a class="page-link" href="#!" onclick="changePage(${i})">${i}</a>`;
    paginationContainer.appendChild(pageLi);
  }

  // Next button
  const nextLi = document.createElement('li');
  nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
  nextLi.innerHTML = `<a class="page-link" href="#!" onclick="changePage(${currentPage + 1})">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
  paginationContainer.appendChild(nextLi);

  createIcons({ icons });
}

// Function to update the user count information text
function updateUserCountInfo() {
  if (!userCountInfo) return;

  const startIndex = (currentPage - 1) * itemsPerPage + 1;
  const endIndex = Math.min(currentPage * itemsPerPage, totalUsers);

  userCountInfo.innerHTML = `نمایش <b class="me-1">${startIndex}-${endIndex}</b> از <b class="ms-1">${totalUsers}</b> نتیجه`;
}

// Function to change page
function changePage(newPage) {
  if (newPage < 1 || newPage > totalPages || newPage === currentPage) {
    return;
  }

  currentPage = newPage;
  renderUsers();
  renderPagination();
  updateUserCountInfo();

  // Scroll to top of user container
  if (userContainer) {
    userContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Function to initialize sample select dropdown if needed
function initializeSampleSelect() {
  const sampleSelectContainer = document.getElementById('sample-select');
  if (!sampleSelectContainer) return;

  // Example implementation for the sample selector (you can customize this)
  sampleSelectContainer.innerHTML = `
      <select class="form-select" onchange="filterUsers(this.value)">
          <option value="all" selected>همه کاربران</option>
          <option value="developer">توسعه‌دهندگان</option>
          <option value="designer">طراحان</option>
          <option value="manager">مدیران</option>
      </select>
  `;
}

// Example function to filter users by role type
function filterUsers(filterType) {
  // Reset to first page when filtering
  currentPage = 1;

  if (filterType === 'all') {
    // No filtering needed
    renderUsers();
    renderPagination();
    updateUserCountInfo();
    return;
  }

  // Apply filter based on role keywords
  const filteredData = userData.filter(user => {
    const role = user.role.toLowerCase();

    switch (filterType) {
      case 'developer':
        return role.includes('developer') ||
          role.includes('engineer') ||
          role.includes('programmer') ||
          role.includes('coder');
      case 'designer':
        return role.includes('designer') ||
          role.includes('ux') ||
          role.includes('ui');
      case 'manager':
        return role.includes('manager') ||
          role.includes('lead') ||
          role.includes('cto') ||
          role.includes('cio');
      default:
        return true;
    }
  });

  // Temporary replace userData with filtered set
  const originalData = [...userData];
  userData.length = 0;
  userData.push(...filteredData);

  // Render with filtered data
  renderUsers();
  renderPagination();
  updateUserCountInfo();

  // Restore original data
  userData.length = 0;
  userData.push(...originalData);
}

// Export functions and data for potential external use
window.userData = userData;
window.changePage = changePage;
window.filterUsers = filterUsers; 