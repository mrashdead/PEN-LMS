
import { createIcons, icons } from 'lucide';
import Swiper from 'swiper/bundle';
import 'swiper/css/bundle';


//product Swiper
var swiper = new Swiper(".productSlider", {
    loop: true,
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
    autoplay: {
        delay: 2500,
        disableOnInteraction: false,
    },
});

//preview Images Swiper
var swiper = new Swiper(".previewImages", {
    loop: true,
    pagination: {
        el: ".swiper-pagination",
        type: "fraction",
    },
    autoplay: {
        delay: 2500,
        disableOnInteraction: false,
    },
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
});

//Product Size
document.addEventListener('DOMContentLoaded', function () {
    const sizeLinks = document.querySelectorAll('.product-size a');

    sizeLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();

            sizeLinks.forEach(el => {
                el.classList.remove('active', 'text-success');
                el.classList.add('text-muted');
            });

            this.classList.add('active', 'text-success');
            this.classList.remove('text-muted');
        });
    });
});

//rating emoji modal
document.addEventListener('DOMContentLoaded', function () {
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
        ratingInput.value = selectedIndex + 1;
    }

    ratingElements.forEach((rating, index) => {
        rating.addEventListener('click', () => {
            updateRating(index);
        });
    });

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
});


const reviews = [
    {
        name: "کریم باقری",
        date: "5 اردیبهشت 1403",
        location: "تبریز",
        image: "assets/images/avatar/user-1.png",
        rating: 4.5,
        title: "کیفیت پارچه",
        message: "اضافه کردن این مورد به عنوان بخشی از پروژه‌مان واقعاً حرکت خوبی بود، نظرات بسیار خوبی از طرف بخش طراحی و تجربه کاربری دریافت کردیم. بدون هیچ مشکل وابستگی یا بسته‌های منسوخ‌شده نصب شد و در کل واقعاً خوب بود."
    },
    {
        name: "نصرت کریمی",
        date: "3 اردیبهشت 1403",
        location: "تهران",
        image: "assets/images/avatar/user-2.png",
        rating: 5,
        title: "کیفیت و جنس کار عالی",
        message: "محصول عالی! فراتر از تمام انتظاراتم بود. به هر کسی که به دنبال کیفیت است، اکیداً توصیه می‌کنم."
    },
    {
        name: "محمدرضا هدایتی",
        date: "1 اردیبهشت 1403",
        location: "شیراز",
        image: "assets/images/avatar/user-3.png",
        rating: 3.5,
        title: "کیفیت طراحی",
        message: "این محصول مناسب است اما جای پیشرفت دارد، اما برخی از ویژگی‌ها کمی ناامیدکننده بودند."
    },
    {
        name: "حدیث میرامینی",
        date: "30 فروردین 1403",
        location: "تهران",
        image: "assets/images/avatar/user-4.png",
        rating: 2,
        title: "انعطاف‌پذیری",
        message: "از محصول خیلی راضی نیستم. انتظارات من را برآورده نکرد و هنگام استفاده چندین مشکل داشت."
    },
    {
        name: "علی مصطفی‌زاده",
        date: "27 فروردین 1403",
        location: "اصفهان",
        image: "assets/images/avatar/user-5.png",
        rating: 4,
        title: "کیفیت خوب پارچه",
        message: "در کل محصول خوبی است، اما چند اشکال وجود دارد که باید برطرف شوند. پشتیبانی مشتری در حل برخی از مشکلات مفید بود."
    },
    {
        name: "سارا شریفی‌نیا",
        date: "24 فروردین 1403",
        location: "کهگیلویه و بویراحمد",
        image: "assets/images/avatar/user-6.png",
        rating: 4.5,
        title: "تنوع رنگ",
        message: "محصول عالی با ویژگی‌های عالی. رابط کاربری بسیار کاربرپسند است"
    },
    {
        name: "بهرام رادان",
        date: "22 فروردین 1403",
        location: "تهران",
        image: "assets/images/avatar/user-7.png",
        rating: 3.5,
        title: "جنس پارچه",
        message: "این محصول در حد متوسط ​​است. همانطور که انتظار می‌رود کار می‌کند اما فاقد برخی از ویژگی‌های پیشرفته‌ای است که رقبا ارائه می‌دهند."
    },
    {
        name: "گوهر خیراندیش",
        date: "20 فروردین 1403",
        location: "بندر عباس",
        image: "assets/images/avatar/user-8.png",
        rating: 4.5,
        title: "طراحی لباس",
        message: "در ابتدا با محصول مشکلاتی داشتم، اما پشتیبانی مشتری توانست به حل آنها کمک کند. با این حال، آنقدر که امیدوار بودم بی‌نقص نیست."
    },
    {
        name: "جمشید نجات",
        date: "17 فروردین 1403",
        location: "تهران",
        image: "assets/images/avatar/user-9.png",
        rating: 3.5,
        title: "امکان تغییر اندازه",
        message: "محصول به هیچ وجه انتظارات من را برآورده نکرد."
    },
    {
        name: "مهدی یراحی",
        date: "14 خرداد 1403",
        location: "یزد",
        image: "assets/images/avatar/user-10.png",
        rating: 5,
        title: "طراحی لباس",
        message: "محصولی فوق‌العاده عالی! این محصول تمام ویژگی‌هایی را که نیاز دارم دارد و به طور بی‌نقص کار می‌کند."
    },
    {
        name: "لیلا حاتمی",
        date: "21 خرداد 1403",
        location: "تهران",
        image: "assets/images/avatar/user-11.png",
        rating: 5,
        title: "موجود بودن ویژگی ها",
        message: "به‌طور کلی، از محصول راضی هستم. به خوبی عمل می‌کند و دارای مجموعه‌ای خوب از ویژگی‌ها است."
    },
    {
        name: "محسن چاووشی",
        date: "8 تیر 1403",
        location: "مشهد",
        image: "assets/images/avatar/user-12.png",
        rating: 4.5,
        title: "انعطاف پذیری",
        message: "محصول خوب است اما می‌تواند برخی از بهبودها را ببیند. رابط کاربری باید بیشتر کاربرپسند باشد."
    },
    {
        name: "چارلز براون",
        date: "6 اردیبهشت 1403",
        location: "اورلاندو",
        image: "assets/images/avatar/user-13.png",
        rating: 1,
        title: "جنس پارچه",
        message: "من امیدهای زیادی برای این محصول داشتم، اما نتوانست به انتظارات من پاسخ دهد. چندین مشکل وجود داشت که کار با آن را دشوار کرد."
    },
    {
        name: "مری جانسون",
        date: "3 اردیبهشت 1403",
        location: "فیلادلفیا",
        image: "assets/images/avatar/user-14.png",
        rating: 4,
        title: "موجود بودن ویژگی ها",
        message: "به‌طور کلی، یک محصول خوب. اکثر ویژگی‌هایی که نیاز دارم را دارد و به خوبی عمل می‌کند."
    },
    {
        name: "ریچارد ویلسون",
        date: "1 اردیبهشت 1403",
        location: "سن دیگو",
        image: "assets/images/avatar/user-15.png",
        rating: 3.5,
        title: "طراحی لباس",
        message: "محصول معقولی است، اما طراحی می‌تواند مدرن‌تر باشد. کمی قدیمی است."
    },
    {
        name: "علی مصفا",
        date: "28 تیر 1403",
        location: "تهران",
        image: "assets/images/avatar/user-16.png",
        rating: 2.5,
        title: "انعطاف پذیری",
        message: "خیلی انعطاف‌پذیر نیست. سفارشی‌سازی مطابق اندازه مودر نظر ما دشوار است."
    },
    {
        name: "دانیل حکیمی",
        date: "26 بهمن 1402",
        location: "آستین",
        image: "assets/images/avatar/user-17.png",
        rating: 4,
        title: "کیفیت پشتیبانی",
        message: "پشتیبانی خوبی دارد. به ما کمک کرد تا محصول را بهتر درک کنیم."
    },
    {
        name: "باربارا کریمی",
        date: "23 بهمن 1402",
        location: "سن آنتونیو",
        image: "assets/images/avatar/user-18.png",
        rating: 3,
        title: "موجود بودن ویژگی ها",
        message: "برخی از ویژگی‌هایی که انتظار داشتیم را ندارد. نیاز به گزینه‌های سفارشی‌سازی بیشتری دارد."
    },
    {
        name: "میثم مرودستی",
        date: "21 خرداد 1403",
        location: "اسلامشهر",
        image: "assets/images/avatar/user-19.png",
        rating: 4.5,
        title: "انعطاف پذیری",
        message: "محصول بسیار انعطاف‌پذیری است. ما توانستیم آن را مطابق نیازهای خود سفارشی‌سازی کنیم."
    },
    {
        name: "ثریا قاسمی",
        date: "19 بهمن 1402",
        location: "سبزه‌وار",
        image: "assets/images/avatar/user-20.png",
        rating: 5,
        title: "جنس پارچه",
        message: "کیفیت پارچه عالی است. به خوبی دوخته شده و نگهداری آن آسان است."
    },
    {
        name: "رابرت لوپز",
        date: "17 فروردین 1403",
        location: "ایندیاناپولیس",
        image: "assets/images/avatar/user-21.png",
        rating: 3,
        title: "کیفیت مستندات",
        message: "مستندات نیاز به بهبود دارد. برخی جزئیات و مثال‌ها را کم دارد."
    },
    {
        name: "دوروتی آزبورتک",
        date: "15 فروردین 1403",
        location: "تهران",
        image: "assets/images/avatar/user-22.png",
        rating: 4.5,
        title: "طراحی لباس",
        message: "طراحی عالی! از نظر بصری جذاب و آسان برای پوشش است."
    },
    {
        name: "پرویز پرستویی",
        date: "21 بهمن 1402",
        location: "کاشان",
        image: "assets/images/avatar/user-23.png",
        rating: 4,
        title: "انعطاف پذیری",
        message: "به اندازه کافی انعطاف‌پذیر برای نیازهای ما. توانستیم آن را مطابق با جریان کار خود سفارشی‌سازی کنیم."
    },
    {
        name: "دونا فلورس",
        date: "10 اسفند 1402",
        location: "کلمبوس",
        image: "assets/images/avatar/user-24.png",
        rating: 2,
        title: "موجود بودن ویژگی ها",
        message: "برخی از ویژگی‌های مهمی که دنبالشان بودیم را کم دارد. ناامیدکننده است."
    },
    {
        name: "کنت اسکات",
        date: "7 بهمن 1402",
        location: "فورت وورث",
        image: "assets/images/avatar/user-25.png",
        rating: 4.5,
        title: "طراحی لباس",
        message: "طراحی بی‌نظیر است! تمیز، مدرن و شهودی است."
    },
    {
        name: "جنیفر کینگ",
        date: "4 بهمن 1402",
        location: "ممفیس",
        image: "assets/images/avatar/user-26.png",
        rating: 3,
        title: "موجود بودن ویژگی ها",
        message: "مجموعه ویژگی‌های متوسط. نیازهای اساسی ما را برآورده می‌کند اما قابلیت‌های پیشرفته را کم دارد."
    },
    {
        name: "جرالد هرناندز",
        date: "2 بهمن 1402",
        location: "بالتیمور",
        image: "assets/images/avatar/user-27.png",
        rating: 4,
        title: "کیفیت پشتیبانی",
        message: "پشتیبانی خوبی دارد. به ما کمک کرد تا به سرعت با محصول شروع کنیم."
    },
    {
        name: "مگان سانچز",
        date: "30 دی 1402",
        location: "واشنگتن",
        image: "assets/images/avatar/user-28.png",
        rating: 4.5,
        title: "جنس پارچه",
        message: "جنس پارچه با کیفیت بالا. به خوبی دوخته شده و طرح آن ریباست است."
    }
];

class ProductOverview {
    constructor(options = {}) {
        // Default configuration
        this.config = {
            perPage: options.perPage || 8,
            reviewsData: options.reviewsData || [],
            reviewTableBody: options.reviewTableBody || "reviewTableBody",
            paginationSummary: options.paginationSummary || "paginationSummary",
            paginationControls: options.paginationControls || "paginationControls",
            addReviewModal: options.addReviewModal || "addReviewModal",
            addReviewBtn: options.addReviewBtn || "addReviewBtn",
            confirmDeleteBtn: options.confirmDeleteBtn || "confirmDeleteBtn",
            deleteModal: options.deleteModal || "deleteModal"
        };

        // State management
        this.state = {
            currentPage: 1,
            deleteItemUsername: null,
            editingReviewIndex: null,
            totalPages: Math.ceil(this.config.reviewsData.length / this.config.perPage)
        };

        // Initialize
        this.init();
    }

    init() {
        this.renderTable();
        this.renderPagination();
        this.attachEventListeners();
    }

    // Render star ratings
    renderStars(rating) {
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

    // Render reviews table
    renderTable() {
        const start = (this.state.currentPage - 1) * this.config.perPage;
        const end = Math.min(start + this.config.perPage, this.config.reviewsData.length);
        const displayedReviews = this.config.reviewsData.slice(start, end);

        const tbody = document.getElementById(this.config.reviewTableBody);
        if (!tbody) return;

        tbody.innerHTML = displayedReviews.map((review, localIndex) => {
            // Calculate the actual index in the full reviews array
            const globalIndex = start + localIndex;

            return `
          <tr class="gap-2">
            <td class="align-top text-nowrap">
              <div class="d-flex align-items-center gap-3 flex-nowrap">
                <img src="${review.image}" alt="" class="rounded-2 flex-shrink-0 size-16" loading="lazy">
                <div class="overflow-hidden flex-grow-1">
                  <h6 class="mb-1"><a href="#!" class="link link-custom">${review.name}</a></h6>
                  <p class="mb-1 fs-sm text-truncate">${review.date}</p>
                  <p class="fs-sm text-muted">مکان: <span>${review.location}</span></p>
                </div>
              </div>
            </td>
            <td class="whitespace-nowrap">
              <div class="w-350px">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <div class="text-warning d-flex align-items-center">
                    ${this.renderStars(review.rating)}
                  </div>
                  <h6 class="mb-0">(${review.rating})</h6>
                </div>
                <h6 class="mb-1 lh-base">${review.title}</h6>
                <p class="text-muted">${review.message}</p>
              </div>
            </td>
            <td class="align-top text-nowrap">
              <div class="d-flex align-items-center justify-content-end gap-3">
                <button class="btn btn-light flex-shrink-0">پیام مستقیم</button>
                <div class="dropdown">
                  <button class="btn btn-primary btn-icon" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                    <i class="ri-more-2-fill"></i>
                  </button>
                  <ul class="dropdown-menu dropdown-menu-end">
                    <li><a href="#${this.config.addReviewModal}" class="dropdown-item edit-review-btn" data-bs-toggle="modal" data-global-index="${globalIndex}"><i class="align-middle me-2 ri-pencil-line"></i> ویرایش</a></li>
                    <li><a href="#${this.config.deleteModal}" class="dropdown-item delete-review-btn" data-bs-toggle="modal" data-username="${review.name}"><i class="align-middle me-2 ri-delete-bin-line"></i> حذف</a></li>
                  </ul>
                </div>
              </div>
            </td>
          </tr>
        `;
        }).join('');

        // Update pagination summary
        const summaryEl = document.getElementById(this.config.paginationSummary);
        if (summaryEl) {
            summaryEl.innerHTML = `نمایش <b>${start + 1}</b>-<b>${end}</b> از <b>${this.config.reviewsData.length}</b> نتیجه`;
        }
    }

    // Render pagination controls
    renderPagination() {
        this.state.totalPages = Math.ceil(this.config.reviewsData.length / this.config.perPage);
        const container = document.getElementById(this.config.paginationControls);
        if (!container) return;

        container.innerHTML = '';

        // Previous button
        const prev = document.createElement("li");
        prev.className = `page-item ${this.state.currentPage === 1 ? 'disabled' : ''}`;
        prev.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i>قبلی</a>`;
        prev.addEventListener('click', (e) => {
            e.preventDefault();
            this.changePage(this.state.currentPage - 1);
        });
        container.appendChild(prev);

        // Page numbers
        for (let i = 1; i <= this.state.totalPages; i++) {
            const li = document.createElement("li");
            li.className = `page-item ${i === this.state.currentPage ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
            li.addEventListener('click', (e) => {
                e.preventDefault();
                this.changePage(i);
            });
            container.appendChild(li);
        }

        // Next button
        const next = document.createElement("li");
        next.className = `page-item ${this.state.currentPage === this.state.totalPages ? 'disabled' : ''}`;
        next.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        next.addEventListener('click', (e) => {
            e.preventDefault();
            this.changePage(this.state.currentPage + 1);
        });
        container.appendChild(next);

        createIcons({ icons });
    }

    // Change page
    changePage(page) {
        if (page < 1 || page > this.state.totalPages) return;
        this.state.currentPage = page;
        this.renderTable();
        this.renderPagination();
    }

    // Add or update review
    addOrUpdateReview() {
        const name = document.getElementById('userNameInput').value.trim();
        const date = document.getElementById('createDateInput').value.trim();
        const location = document.getElementById('locationInput').value.trim();
        const title = document.getElementById('titleInput').value.trim();
        const message = document.getElementById('writeReviewInput').value.trim();
        const rating = parseFloat(document.getElementById('rating-input').value);
        const showAlert = (message) => {
            const alertContainer = document.querySelector('form #reviewDiv');
            alertContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <span>${message}</span>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
        };
        if (!name || !date || !location || !title || !message || isNaN(rating)) {
            showAlert("لطفا همه فیلدها را به درستی پر کنید!");
            return false;
        }

        const reviewData = {
            name,
            date,
            location,
            title,
            message,
            rating,
        };

        if (this.state.editingReviewIndex !== null) {
            // Keep existing image for edited review
            reviewData.image = this.config.reviewsData[this.state.editingReviewIndex].image;
            this.config.reviewsData[this.state.editingReviewIndex] = reviewData;
        } else {
            // Use default image for new review
            reviewData.image = "assets/images/avatar/user-no.png";
            this.config.reviewsData.unshift(reviewData);
        }

        // Reset page to first page after adding new review
        if (this.state.editingReviewIndex === null) {
            this.state.currentPage = 1;
        }

        this.renderTable();
        this.renderPagination();
        this.resetForm();
        return true;
    }

    // Reset form
    resetForm() {
        const form = document.querySelector('form');
        if (form) form.reset();

        this.state.editingReviewIndex = null;

        const modalTitle = document.querySelector(`#${this.config.addReviewModal} h6`);
        if (modalTitle) modalTitle.textContent = "افزودن نقد و بررسی";

        const addBtn = document.getElementById(this.config.addReviewBtn);
        if (addBtn) addBtn.textContent = "افزودن نقد و بررسی";
    }

    // Delete review
    deleteReview() {
        if (!this.state.deleteItemUsername) return false;

        const index = this.config.reviewsData.findIndex(
            review => review.name === this.state.deleteItemUsername
        );

        if (index !== -1) {
            this.config.reviewsData.splice(index, 1);
            this.state.deleteItemUsername = null;

            // Update current page if needed
            const maxPage = Math.ceil(this.config.reviewsData.length / this.config.perPage);
            if (this.state.currentPage > maxPage) {
                this.state.currentPage = Math.max(1, maxPage);
            }

            this.renderTable();
            this.renderPagination();
            return true;
        }

        return false;
    }

    // Attach event listeners
    attachEventListeners() {
        // Add review button
        const addReviewBtn = document.getElementById(this.config.addReviewBtn);
        if (addReviewBtn) {
            addReviewBtn.addEventListener('click', () => {
                const success = this.addOrUpdateReview();
                if (success) {
                    // Close modal
                    const modalEl = document.getElementById(this.config.addReviewModal);
                    const modalInstance = window.bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                }
            });
        }

        // Confirm delete button
        const confirmDeleteBtn = document.getElementById(this.config.confirmDeleteBtn);
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => {
                const success = this.deleteReview();
                if (success) {
                    // Close modal
                    const modalEl = document.getElementById(this.config.deleteModal);
                    const modalInstance = window.bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                }
            });
        }

        // Edit button click delegation
        document.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-review-btn');
            if (editBtn) {
                const globalIndex = parseInt(editBtn.getAttribute('data-global-index'));
                if (!isNaN(globalIndex) && this.config.reviewsData[globalIndex]) {
                    this.editReview(globalIndex);
                }
            }

            const deleteBtn = e.target.closest('.delete-review-btn');
            if (deleteBtn) {
                this.state.deleteItemUsername = deleteBtn.getAttribute('data-username');
            }
        });

        // Reset modal on hide
        const addReviewModal = document.getElementById(this.config.addReviewModal);
        if (addReviewModal) {
            addReviewModal.addEventListener('hidden.bs.modal', () => {
                this.resetForm();
            });
        }
    }

    // Edit review
    editReview(index) {
        const review = this.config.reviewsData[index];
        if (!review) return;

        this.state.editingReviewIndex = index;

        // Pre-fill modal
        document.getElementById('userNameInput').value = review.name;
        document.getElementById('createDateInput').value = review.date;
        document.getElementById('locationInput').value = review.location;
        document.getElementById('titleInput').value = review.title;
        document.getElementById('writeReviewInput').value = review.message;
        document.getElementById('rating-input').value = review.rating;

        // Update visual rating in the UI - trigger rating update
        if (typeof updateRating === 'function') {
            updateRating(Math.floor(review.rating) - 1);
        }

        // Update modal title/button
        const modalTitle = document.querySelector(`#${this.config.addReviewModal} h6`);
        if (modalTitle) modalTitle.textContent = "ویرایش نقد و بررسی";

        const addBtn = document.getElementById(this.config.addReviewBtn);
        if (addBtn) addBtn.textContent = "ذخیره تغییرات";
    }
}

// Usage example:
document.addEventListener('DOMContentLoaded', function () {
    // Initialize product overview
    const productOverview = new ProductOverview({
        reviewsData: reviews, // Assuming reviews is defined globally
        perPage: 8
    });

    // Make it globally accessible if needed
    window.productOverview = productOverview;
});
