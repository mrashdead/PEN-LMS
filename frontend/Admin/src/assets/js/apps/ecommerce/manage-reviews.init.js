import { createIcons, icons } from "lucide";


// Get the rating elements and emoji elements
const ratingElements = [
    document.getElementById('rating-1'),
    document.getElementById('rating-2'),
    document.getElementById('rating-3'),
    document.getElementById('rating-4'),
    document.getElementById('rating-5')
];

const emojiElements = [
    document.getElementById('emoji-1'),
    document.getElementById('emoji-2'),
    document.getElementById('emoji-3'),
    document.getElementById('emoji-4'),
    document.getElementById('emoji-5')
];

const ratingInput = document.getElementById('rating-input');

let currentActive = 0;

// Function to update the rating display
function updateRating(selectedIndex) {
    selectedIndex = Math.max(0, Math.min(4, selectedIndex));

    currentActive = selectedIndex;

    ratingElements.forEach((rating, index) => {
        if (index <= selectedIndex) {
            rating.classList.remove('bg-body-tertiary');
            rating.classList.add('bg-warning');
        } else {
            rating.classList.remove('bg-warning');
            rating.classList.add('bg-body-tertiary');
        }
    });

    emojiElements.forEach(emoji => {
        emoji.classList.add('d-none');
    });

    emojiElements[selectedIndex].classList.remove('d-none');

    // Update the rating input value
    ratingInput.value = selectedIndex + 1;
}

// Add click event listeners to the rating elements
ratingElements.forEach((rating, index) => {
    rating.addEventListener('click', () => {
        updateRating(index);
    });
});

// Add click event listeners to the emoji elements (NEW CODE)
emojiElements.forEach((emoji, index) => {
    emoji.addEventListener('click', () => {
        updateRating(index);
    });
});

// Add event listeners to the rating input
ratingInput.addEventListener('change', function () {
    let value = parseInt(this.value);

    if (isNaN(value)) value = 1;
    value = Math.max(1, Math.min(5, value));
    this.value = value;

    updateRating(value - 1);
});

ratingInput.addEventListener('input', function () {
    let value = parseInt(this.value) || 0;
    value = Math.max(0, Math.min(5, value));
    if (value >= 1 && value <= 5)
        updateRating(value - 1);
});

// Initialize
updateRating(0);


const reviews = [
    {
        name: "جان دو",
        date: "4 خرداد 1403",
        location: "نیویورک",
        image: "assets/images/avatar/user-1.png",
        rating: 4.5,
        title: "کیفیت کد",
        message: "این واقعاً یک حرکت خوب بود که این را به عنوان بخشی از پروژه‌ ما اضافه کردیم. نظرات بسیار خوبی از کسب‌وکار در مورد طراحی و تجربه کاربری داشتیم. نصب بدون مشکلات وابستگی یا بسته‌های منسوخ و در کل بسیار خوب بود."
    },
    {
        name: "جین اسمیت",
        date: "2 خرداد 1403",
        location: "لس آنجلس",
        image: "assets/images/avatar/user-2.png",
        rating: 5,
        title: "کیفیت مستندات",
        message: "محصول عالی! تمام انتظارات من را برآورده کرد. به هر کسی که به دنبال کیفیت است، توصیه می‌کنم."
    },
    {
        name: "مایکل براون",
        date: "31 اردیبهشت 1403",
        location: "شیکاگو",
        image: "assets/images/avatar/user-3.png",
        rating: 3.5,
        title: "کیفیت طراحی",
        message: "محصول معمولی است اما پتانسیل بهبود دارد. نصب به‌راحتی انجام شد، اما برخی ویژگی‌ها کمی ناامیدکننده بودند."
    },
    {
        name: "امیلی دیویس",
        date: "29 اردیبهشت 1403",
        location: "هیوستون",
        image: "assets/images/avatar/user-4.png",
        rating: 2,
        title: "انعطاف‌پذیری",
        message: "از محصول خیلی راضی نیستم. نتوانست انتظارات من را برآورده کند و در حین نصب مشکلاتی داشت."
    },
    {
        name: "کریس ویلسون",
        date: "26 اردیبهشت 1403",
        location: "فینکس",
        image: "assets/images/avatar/user-5.png",
        rating: 4,
        title: "کیفیت کد",
        message: "محصول به طور کلی خوب است، اما چند باگ وجود دارد که نیاز به رسیدگی دارند. پشتیبانی مشتری در حل برخی مسائل مفید بود."
    },
    {
        name: "سارا لی",
        date: "23 اردیبهشت 1403",
        location: "سان فرانسیسکو",
        image: "assets/images/avatar/user-6.png",
        rating: 4.5,
        title: "قابلیت سفارشی‌سازی",
        message: "محصول عالی با ویژگی‌های فوق‌العاده. رابط کاربری بسیار شهودی و آسان برای استفاده است."
    },
    {
        name: "دیوید جانسون",
        date: "21 اردیبهشت 1403",
        location: "میامی",
        image: "assets/images/avatar/user-7.png",
        rating: 3.5,
        title: "کیفیت کد",
        message: "محصول متوسط است. طبق انتظار عمل می‌کند اما برخی ویژگی‌های پیشرفته‌ای که رقبا ارائه می‌دهند وجود ندارد."
    },
    {
        name: "نانسی آدامز",
        date: "19 اردیبهشت 1403",
        location: "سیاتل",
        image: "assets/images/avatar/user-8.png",
        rating: 4.5,
        title: "کیفیت طراحی",
        message: "در ابتدا مشکلاتی با محصول داشت، اما پشتیبانی مشتری توانست کمک کند تا آنها را حل کنیم. با این حال، به خوبی که امیدوار بودم، نیست."
    },
    {
        name: "پل وایت",
        date: "16 اردیبهشت 1403",
        location: "بوستون",
        image: "assets/images/avatar/user-9.png",
        rating: 3.5,
        title: "موجود بودن ویژگی‌ها",
        message: "محصول به هیچ وجه نتوانست انتظارات من را برآورده کند. نصب دشوار بود و باگ‌های زیادی داشت."
    },
    {
        name: "لیزا گرین",
        date: "14 اردیبهشت 1403",
        location: "دنور",
        image: "assets/images/avatar/user-10.png",
        rating: 5,
        title: "کیفیت طراحی",
        message: "محصول فوق‌العاده‌ای است! تمام ویژگی‌هایی که نیاز دارم را دارد و بدون نقص کار می‌کند."
    },
    {
        name: "جیمز کلارک",
        date: "12 اردیبهشت 1403",
        location: "آتلانتا",
        image: "assets/images/avatar/user-11.png",
        rating: 5,
        title: "موجود بودن ویژگی‌ها",
        message: "به طور کلی، از محصول راضی‌ام. عملکرد خوبی دارد و دامنه خوبی از ویژگی‌ها را داراست."
    },
    {
        name: "پاتریشیا مارتینز",
        date: "9 اردیبهشت 1403",
        location: "دالاس",
        image: "assets/images/avatar/user-12.png",
        rating: 4.5,
        title: "انعطاف‌پذیری",
        message: "محصول خوب است اما می‌تواند به بهبودهایی نیاز داشته باشد. رابط کاربری می‌تواند کاربرپسندتر باشد."
    },
    {
        name: "چارلز براون",
        date: "5 اردیبهشت 1403",
        location: "اورلاندو",
        image: "assets/images/avatar/user-13.png",
        rating: 1,
        title: "کیفیت کد",
        message: "امیدهای زیادی به این محصول داشتم، اما نتوانست طبق انتظار عمل کند. مشکلات زیادی داشت که کار کردن با آن را دشوار می‌کرد."
    },
    {
        name: "مری جانسون",
        date: "3 اردیبهشت 1403",
        location: "فیلادلفیا",
        image: "assets/images/avatar/user-14.png",
        rating: 4,
        title: "موجود بودن ویژگی‌ها",
        message: "به طور کلی، محصول خوبی است. اکثر ویژگی‌هایی که نیاز دارم را دارد و خوب کار می‌کند."
    },
    {
        name: "ریچارد ویلسون",
        date: "1 اردیبهشت 1403",
        location: "سن دیگو",
        image: "assets/images/avatar/user-15.png",
        rating: 3.5,
        title: "کیفیت طراحی",
        message: "محصول خوبی است، اما طراحی می‌تواند مدرن‌تر باشد. کمی قدیمی است."
    },
    {
        name: "کارن تیلور",
        date: "30 فروردین 1403",
        location: "لاس وگاس",
        image: "assets/images/avatar/user-16.png",
        rating: 2.5,
        title: "انعطاف‌پذیری",
        message: "چندان انعطاف‌پذیر نیست. سفارشی‌سازی آن طبق نیازهای ما دشوار است."
    },
    {
        name: "دانیل توماس",
        date: "27 فروردین 1403",
        location: "آستین",
        image: "assets/images/avatar/user-17.png",
        rating: 4,
        title: "کیفیت مستندات",
        message: "مستندات خوبی دارد. به ما کمک کرد تا محصول را بهتر درک کنیم."
    },
    {
        name: "باربارا هرناندز",
        date: "24 فروردین 1403",
        location: "سن آنتونیو",
        image: "assets/images/avatar/user-18.png",
        rating: 3,
        title: "موجود بودن ویژگی‌ها",
        message: "برخی از ویژگی‌هایی که انتظار داشتیم وجود ندارد. به گزینه‌های سفارشی‌سازی بیشتری نیاز دارد."
    },
    {
        name: "متیو مارتینز",
        date: "22 فروردین 1403",
        location: "شارلوت",
        image: "assets/images/avatar/user-19.png",
        rating: 4.5,
        title: "انعطاف‌پذیری",
        message: "محصولی بسیار انعطاف‌پذیر. توانستیم آن را طبق نیازهای خود سفارشی کنیم."
    },
    {
        name: "آماندا یانگ",
        date: "20 فروردین 1403",
        location: "سن خوزه",
        image: "assets/images/avatar/user-20.png",
        rating: 5,
        title: "کیفیت کد",
        message: "کیفیت کد عالی. به خوبی ساختار یافته و آسان برای نگهداری است."
    },
    {
        name: "رابرت لوپز",
        date: "17 فروردین 1403",
        location: "ایندیاناپولیس",
        image: "assets/images/avatar/user-21.png",
        rating: 3,
        title: "کیفیت مستندات",
        message: "مستندات می‌تواند بهبود یابد. جزئیات و مثال‌های بیشتری نیاز دارد."
    },
    {
        name: "دوروتی گونزالز",
        date: "15 فروردین 1403",
        location: "جکسون‌ویل",
        image: "assets/images/avatar/user-22.png",
        rating: 4.5,
        title: "کیفیت طراحی",
        message: "طراحی عالی! از نظر بصری جذاب و آسان برای ناوبری است."
    },
    {
        name: "جوزف پریز",
        date: "13 فروردین 1403",
        location: "سان فرانسیسکو",
        image: "assets/images/avatar/user-23.png",
        rating: 4,
        title: "انعطاف‌پذیری",
        message: "به اندازه کافی انعطاف‌پذیر برای نیازهای ما. توانستیم آن را برای سازگار کردن با جریان کاری خود سفارشی کنیم."
    },
    {
        name: "دونا فلورس",
        date: "10 فروردین 1403",
        location: "کلمبوس",
        image: "assets/images/avatar/user-24.png",
        rating: 2,
        title: "موجود بودن ویژگی‌ها",
        message: "برخی از ویژگی‌های مهمی که در جستجوی آنها بودیم، وجود ندارد. ناامیدکننده است."
    },
    {
        name: "کنت اسکات",
        date: "8 فروردین 1403",
        location: "فورت وورث",
        image: "assets/images/avatar/user-25.png",
        rating: 4.5,
        title: "کیفیت طراحی",
        message: "طراحی بی‌نظیر! تمیز، مدرن و شهودی است."
    },
    {
        name: "جنیفر کینگ",
        date: "5 فروردین 1403",
        location: "ممفیس",
        image: "assets/images/avatar/user-26.png",
        rating: 3,
        title: "موجود بودن ویژگی‌ها",
        message: "مجموعه ویژگی‌های متوسط. نیازهای پایه ما را برآورده می‌کند، اما فاقد عملکردهای پیشرفته است."
    },
    {
        name: "جرالد هرناندز",
        date: "3 فروردین 1403",
        location: "بالتیمور",
        image: "assets/images/avatar/user-27.png",
        rating: 4,
        title: "کیفیت مستندات",
        message: "مستندات خوبی دارد. به ما کمک کرد تا به سرعت با محصول شروع کنیم."
    },
    {
        name: "مگان سانچز",
        date: "1 فروردین 1403",
        location: "واشنگتن",
        image: "assets/images/avatar/user-28.png",
        rating: 4.5,
        title: "کیفیت کد",
        message: "کدبیس با کیفیت بالا. به خوبی نوشته شده و آسان برای درک است."
    }
];

const perPage = 10;
let currentPage = 1;
const searchInput = document.getElementById("searchReviewInput");
let deleteItemUsername = null;
let editingReviewIndex = null;

function renderStars(rating) {
    let html = '';
    for (let i = 1; i <= 5; i++) {
        if (rating >= i) {
            html += `<i class="ri-star-fill text-warning"></i>`;
        } else if (rating >= i - 0.5) {
            html += `<i class="ri-star-half-fill text-warning"></i>`;
        } else {
            html += `<i class="ri-star-line text-warning"></i>`;
        }
    }
    return html;
}

function renderTable() {
    const filtered = getFilteredReviews();
    const start = (currentPage - 1) * perPage;
    const end = start + perPage;
    const items = filtered.slice(start, end);

    const tbody = document.getElementById("reviewTableBody");

    if (items.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="3" class="text-center py-4">
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
                  <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0
                    l-4.331-4.331"></path>
                  <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912"></path>
                  <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round" stroke-miterlimit="10" stroke-width="3" d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814"></path>
                </svg>
                <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                <p class="text-muted mb-0">ما نتوانستیم هیچ نقدی مطابق با جستجوی شما پیدا کنیم.</p>
              </div>
            </td>
          </tr>
        `;
    } else {
        tbody.innerHTML = items.map((r, index) => `
          <tr class="gap-2">
            <td class="align-top whitespace-nowrap text-nowrap">
              <div class="d-flex align-items-center gap-3 flex-nowrap">
                <img src="${r.image}" alt="" class="rounded-2 flex-shrink-0 size-16" loading="lazy">
                <div class="overflow-hidden flex-grow-1">
                  <h6 class="mb-1"><a href="#!" class="link link-custom">${r.name}</a></h6>
                  <p class="mb-1 fs-sm text-truncate">${r.date}</p>
                  <p class="fs-sm text-muted">مکان: <span>${r.location}</span></p>
                </div>
              </div>
            </td>
            <td class="text-wrap">
              <div class="w-350px">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <div class="text-warning d-flex align-items-center">
                    ${renderStars(r.rating)}
                  </div>
                  <h6 class="mb-0">(${r.rating})</h6>
                </div>
                <h6 class="mb-1 lh-base">${r.title}</h6>
                <p class="text-muted">${r.message}</p>
              </div>
            </td>
            <td class="align-top text-nowrap">
              <div class="d-flex align-items-center justify-content-end gap-3 flex-wrap">
                <button class="btn btn-light flex-shrink-0">پیام مستقیم</button>
                <div class="dropdown">
                  <button class="btn btn-primary btn-icon" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                    <i class="ri-more-2-fill"></i>
                  </button>
                  <ul class="dropdown-menu dropdown-menu-end">
                    <li><a href="#addReviewModal" class="dropdown-item edit-review-btn" data-bs-toggle="modal" data-index="${index}"><i class="align-middle me-2 ri-pencil-line"></i> ویرایش</a></li>
                    <li><a href="#deleteModal" class="dropdown-item delete-review-btn" data-bs-toggle="modal" data-username="${r.name}"><i class="align-middle me-2 ri-delete-bin-line"></i> حذف</a></li>
                  </ul>
                </div>
              </div>
            </td>
          </tr>
        `).join('');
    }

    document.getElementById("paginationSummary").innerHTML =
        `نمایش <b>${filtered.length ? start + 1 : 0}</b>-<b>${Math.min(end, filtered.length)}</b> از <b>${filtered.length}</b> نتیجه`;
}


function renderPagination() {
    const filtered = getFilteredReviews();
    const totalPages = Math.ceil(filtered.length / perPage);
    const container = document.getElementById("paginationControls");
    container.innerHTML = '';

    const prev = document.createElement("li");
    prev.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prev.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i>قبلی</a>`;
    prev.onclick = () => changePage(currentPage - 1);
    container.appendChild(prev);

    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement("li");
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
        li.onclick = () => changePage(i);
        container.appendChild(li);
    }

    const next = document.createElement("li");
    next.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    next.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
    next.onclick = () => changePage(currentPage + 1);
    container.appendChild(next);
    createIcons({ icons });
}

function changePage(page) {
    const totalPages = Math.ceil(reviews.length / perPage);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
    renderPagination();
}

function updateSummaryStats() {
    const totalReviews = reviews.length;
    const totalRating = reviews.reduce((sum, r) => sum + r.rating, 0);
    const avgRating = totalReviews ? (totalRating / totalReviews).toFixed(1) : "0";

    // Set total reviews count
    document.getElementById("totalReviewCount").textContent = totalReviews;

    // Fake growth percent (optional: replace with real logic if needed)
    const growthPercent = 100;
    const growthBadge = document.getElementById("reviewGrowthBadge");
    growthBadge.textContent = `${growthPercent}%`;
    growthBadge.classList.toggle("bg-success-subtle", growthPercent >= 0);
    growthBadge.classList.toggle("bg-danger-subtle", growthPercent < 0);
    growthBadge.classList.toggle("text-success", growthPercent >= 0);
    growthBadge.classList.toggle("text-danger", growthPercent < 0);

    // Set average rating
    document.getElementById("averageRating").textContent = avgRating;

    // Render average stars
    const avgStarsContainer = document.getElementById("averageStars");
    avgStarsContainer.innerHTML = renderStars(parseFloat(avgRating));
}

function updateStarBreakdown() {
    const starCounts = [0, 0, 0, 0, 0]; // Index 0 = 1 star, Index 4 = 5 stars

    reviews.forEach(r => {
        const rounded = Math.round(r.rating);
        if (rounded >= 1 && rounded <= 5) {
            starCounts[rounded - 1]++;
        }
    });

    const total = starCounts.reduce((a, b) => a + b, 0);
    const container = document.getElementById("starBreakdown");
    container.innerHTML = "";

    const barColors = ["bg-danger", "bg-info", "bg-warning", "bg-pink", "bg-success"]; // 1 to 5 stars

    for (let i = 4; i >= 0; i--) {
        const count = starCounts[i];
        const percent = total ? (count / total * 100).toFixed(0) : 0;
        const colorClass = barColors[i] || "bg-warning";

        const row = document.createElement("div");
        row.className = "d-flex align-items-center gap-2 mt-1";
        row.innerHTML = `
        <p class="flex-shrink-0"><i class="text-warning ri-star-fill"></i> ${i + 1}</p>
        <div class="progress progress-1" role="progressbar" style="height: 8px; width: ${percent}%;" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100">
          <div class="progress-bar w-100 ${colorClass}"></div>
        </div>
        <h6 class="mb-0">${count}</h6>
      `;
        container.appendChild(row);
    }
}

function getFilteredReviews() {
    const term = searchInput.value.trim().toLowerCase();
    if (!term) return reviews;
    return reviews.filter(r =>
        r.name.toLowerCase().includes(term) ||
        r.date.toLowerCase().includes(term) ||
        r.location.toLowerCase().includes(term) ||
        r.title.toLowerCase().includes(term) ||
        r.message.toLowerCase().includes(term)
    );
}

searchInput.addEventListener("input", () => {
    currentPage = 1; // reset to first page
    renderTable();
    renderPagination();
});

document.getElementById('addReviewBtn').addEventListener('click', function () {
    const name = document.getElementById('userNameInput').value.trim();
    const date = document.getElementById('createDateInput').value.trim();
    const location = document.getElementById('locationInput').value.trim();
    const title = document.getElementById('titleInput').value.trim();
    const message = document.getElementById('writeReviewInput').value.trim();
    const rating = parseFloat(document.getElementById('rating-input').value);
    const showAlert = (message) => {
        const alertContainer = document.querySelector('#addReviewModal #alertContainer');
        alertContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <span>${message}</span>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
    };
    if (!name || !date || !location || !title || !message || isNaN(rating)) {
        showAlert("لطفا همه فیلدها را به درستی پر کنید!");
        return;
    }


    const reviewData = {
        name,
        date,
        location,
        title,
        message,
        rating,
    };

    // Remember the current page before making changes
    const currentPageBeforeEdit = currentPage;

    if (editingReviewIndex !== null && editingReviewIndex >= 0 && editingReviewIndex < reviews.length) {
        // Keep existing image for edited review
        reviewData.image = reviews[editingReviewIndex].image;
        reviews[editingReviewIndex] = reviewData;

        // For edits, maintain the current page
        // (Do not reset to page 1)
    } else {
        // Use default image for new review
        reviewData.image = "assets/images/avatar/user-no.png";
        reviews.unshift(reviewData);

        // Only for new reviews, reset to page 1
        currentPage = 1;
    }

    // Reset edit index
    editingReviewIndex = null;

    // Update UI
    renderTable();
    renderPagination();
    updateSummaryStats();
    updateStarBreakdown();

    // Close modal
    const modalEl = document.getElementById('addReviewModal');
    const modalInstance = window.bootstrap.Modal.getInstance(modalEl);
    if (modalInstance) {
        modalInstance.hide();
    }

    // Reset form
    document.querySelector('form').reset();
    updateRating(0);
    document.querySelector('#addReviewModal h6').textContent = "افزودن نقد و بررسی";
    document.getElementById('addReviewBtn').textContent = "افزودن نقد و بررسی";
});

// Fix the edit button click handler
document.addEventListener('click', function (e) {
    const btn = e.target.closest('.edit-review-btn');
    if (!btn) return;

    // Get the index from the data attribute
    const displayIndex = parseInt(btn.getAttribute('data-index'));

    // Convert the display index to the actual index in the reviews array
    const filtered = getFilteredReviews();
    const startIndex = (currentPage - 1) * perPage;
    const actualReview = filtered[startIndex + displayIndex];

    // Find the index in the original reviews array
    const originalIndex = reviews.findIndex(r =>
        r.name === actualReview.name &&
        r.date === actualReview.date &&
        r.message === actualReview.message
    );

    if (originalIndex === -1) return;
    editingReviewIndex = originalIndex;

    // Pre-fill modal with review data
    document.getElementById('userNameInput').value = actualReview.name;
    document.getElementById('createDateInput').value = actualReview.date;
    document.getElementById('locationInput').value = actualReview.location;
    document.getElementById('titleInput').value = actualReview.title;
    document.getElementById('writeReviewInput').value = actualReview.message;

    // Handle decimal ratings properly
    const rating = actualReview.rating;
    document.getElementById('rating-input').value = rating;
    updateRating(Math.ceil(rating) - 1);

    // Update modal title/button
    document.querySelector('#addReviewModal h6').textContent = "ویرایش نقد و بررسی";
    document.getElementById('addReviewBtn').textContent = "ذخیره تغییرات";
});


document.getElementById('addReviewModal').addEventListener('hidden.bs.modal', function () {
    editingReviewIndex = null;
    document.querySelector('form').reset();
    updateRating(0);
    document.querySelector('#addReviewModal h6').textContent = "افزودن نقد و بررسی";
    document.getElementById('addReviewBtn').textContent = "افزودن نقد و بررسی";
});

// Attach event listeners to all delete buttons
document.addEventListener('click', function (e) {
    if (e.target.closest('.delete-review-btn')) {
        const btn = e.target.closest('.delete-review-btn');
        deleteItemUsername = btn.getAttribute('data-username');
    }
});

// Confirm delete logic
document.getElementById('confirmDeleteBtn').addEventListener('click', function () {
    if (!deleteItemUsername) return;
    // Find and remove from the array
    for (let i = 0; i < reviews.length; i++) {
        if (reviews[i].name === deleteItemUsername) {
            reviews.splice(i, 1);
            break;
        }
    }

    // Reset and rerender
    deleteItemUsername = null;
    currentPage = 1;

    renderTable();
    renderPagination();
    updateSummaryStats();
    updateStarBreakdown();

    // Close modal (Bootstrap way)
    const modalEl = document.getElementById('deleteModal');
    const modal = window.bootstrap.Modal.getInstance(modalEl);
    modal.hide();
});

// Init
renderTable();
renderPagination();
updateSummaryStats();
updateStarBreakdown();

