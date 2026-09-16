import { createIcons, icons } from "lucide";


document.addEventListener('DOMContentLoaded', () => {
    if (window.VirtualSelect && document.getElementById('sortBySelect')) {
        VirtualSelect.init({
            ele: "#sortBySelect",
            options: [
                { label: "همه", value: "All" },
                { label: "تازه‌ترین", value: "Newest" },
                { label: "قدیمی‌ترین", value: "Oldest" },
                { label: "محبوب‌ترین", value: "Popular Book" },
                { label: "پر فروش ترین", value: "Best Sales" },
            ],
        });
    }
});

const books = [
    {
        title: "سرود قو",
        author: "دیوید گران",
        image: "assets/images/school/book/img-01.jpg",
        rating: 5,
        reviews: 98,
        price: 47.99,
    },
    {
        title: "شرط‌بندی: داستانی از کشتی‌شکستگی، شورش و قتل",
        author: "الین هیلدربراند",
        image: "assets/images/school/book/img-02.jpg",
        rating: 5,
        reviews: 147,
        price: 29.99,
    },
    {
        title: "باشگاه جمعه عصر: خاطرات خانوادگی",
        author: "گریفین دان",
        image: "assets/images/school/book/img-03.jpg",
        rating: 4.5,
        reviews: 213,
        price: 30,
    },
    {
        title: "نه در عشق",
        author: "علی هیزلوود",
        image: "assets/images/school/book/img-04.jpg",
        rating: 4.5,
        reviews: 97,
        price: 17.99,
    },
    {
        title: "این تابستان متفاوت خواهد بود",
        author: "کارلی فورتون",
        image: "assets/images/school/book/img-05.jpg",
        rating: 4.5,
        reviews: 179,
        price: 21,
    },
    {
        title: "بی‌باک",
        author: "لورِن رابرتز",
        image: "assets/images/school/book/img-06.jpg",
        rating: 4.5,
        reviews: 236,
        price: 39.99,
    },
    {
        title: "شب‌ها و آخر هفته‌ها: یک رمان",
        author: "اوئیسین مک‌کنا",
        image: "assets/images/school/book/img-07.jpg",
        rating: 4.5,
        reviews: 46,
        price: 21.49,
    },
    {
        title: "یک پنجره تاریک",
        author: "ریچل گیلیگ",
        image: "assets/images/school/book/img-08.jpg",
        rating: 4.5,
        reviews: 74,
        price: 49.99,
    },
    {
        title: "دو تاج پیچیده",
        author: "ریچل گیلیگ",
        image: "assets/images/school/book/img-09.jpg",
        rating: 4.5,
        reviews: 39,
        price: 17.49,
    },
    {
        title: "تمام رنگ‌های تاریکی",
        author: "کریس ویتاکر",
        image: "assets/images/school/book/img-10.jpg",
        rating: 4.5,
        reviews: 798,
        price: 33.49,
    },
    {
        title: "سحرشده",
        author: "امیلی مک‌اینتایر",
        image: "assets/images/school/book/img-11.jpg",
        rating: 4.5,
        reviews: 465,
        price: 14.67,
    },
    {
        title: "عمل خلاق: راهی برای بودن",
        author: "ریک روبین",
        image: "assets/images/school/book/img-12.jpg",
        rating: 4.5,
        reviews: 341,
        price: 25.32,
    },
    {
        title: "بیمار ساکت",
        author: "الکس مایکلیدس",
        image: "assets/images/school/book/img-01.jpg",
        rating: 4.5,
        reviews: 287,
        price: 22.99,
    },
    {
        title: "جایی که خرچنگ‌ها می‌خوانند",
        author: "دلیا اونز",
        image: "assets/images/school/book/img-02.jpg",
        rating: 5,
        reviews: 312,
        price: 19.99,
    },
    {
        title: "کتابخانه نیمه‌شب",
        author: "مت هایگ",
        image: "assets/images/school/book/img-03.jpg",
        rating: 4.5,
        reviews: 198,
        price: 18.50,
    },
    {
        title: "پروژه هیل مری",
        author: "اندی ویر",
        image: "assets/images/school/book/img-04.jpg",
        rating: 5,
        reviews: 267,
        price: 24.99,
    },
    {
        title: "چهار باد",
        author: "کریستین هانا",
        image: "assets/images/school/book/img-05.jpg",
        rating: 4.5,
        reviews: 187,
        price: 21.99,
    },
    {
        title: "زندگی نامرئی آدی لارو",
        author: "وی.ای. شواب",
        image: "assets/images/school/book/img-06.jpg",
        rating: 4.5,
        reviews: 210,
        price: 23.49,
    },
    {
        title: "کلارا و خورشید",
        author: "کازوو ایشیگورو",
        image: "assets/images/school/book/img-07.jpg",
        rating: 4.5,
        reviews: 176,
        price: 20.99,
    },
    {
        title: "نیمی که ناپدید شد",
        author: "بریت بنت",
        image: "assets/images/school/book/img-08.jpg",
        rating: 5,
        reviews: 231,
        price: 19.50,
    },
    {
        title: "همنت",
        author: "مگی اوفارل",
        image: "assets/images/school/book/img-09.jpg",
        rating: 4.5,
        reviews: 154,
        price: 22.49,
    },
    {
        title: "گوتیک مکزیکی",
        author: "سیلویا مورنو-گارسیا",
        image: "assets/images/school/book/img-10.jpg",
        rating: 4,
        reviews: 189,
        price: 18.99,
    },
    {
        title: "فهرست مهمانان",
        author: "لوسی فولی",
        image: "assets/images/school/book/img-11.jpg",
        rating: 4,
        reviews: 203,
        price: 17.99,
    },
    {
        title: "سیرس",
        author: "مدلین میلر",
        image: "assets/images/school/book/img-12.jpg",
        rating: 5,
        reviews: 267,
        price: 21.50,
    },
    {
        title: "فشار",
        author: "اشلی آدرِین",
        image: "assets/images/school/book/img-01.jpg",
        rating: 4,
        reviews: 143,
        price: 19.99,
    },
    {
        title: "آخرین چیزی که به من گفت",
        author: "لورا دیو",
        image: "assets/images/school/book/img-02.jpg",
        rating: 4.5,
        reviews: 178,
        price: 23.99,
    },
    {
        title: "کاخ کاغذی",
        author: "میراندا کوولی هلر",
        image: "assets/images/school/book/img-03.jpg",
        rating: 4,
        reviews: 156,
        price: 20.99,
    }
];

// Configuration constants
const CONFIG = Object.freeze({
    booksPerPage: 12,
    defaultPage: 1
});

// Cache DOM elements and create state management
const DOM = {};
let state = {
    currentPage: CONFIG.defaultPage,
    searchQuery: '',
    filteredBooks: [...books],
    totalPages: Math.ceil(books.length / CONFIG.booksPerPage)
};

// Performance optimized star icon generator with template caching
const starIconCache = new Map();
function getStarIcons(rating) {
    // Check cache first
    if (starIconCache.has(rating)) {
        return starIconCache.get(rating);
    }

    const fullStars = Math.floor(rating);
    const hasHalf = rating % 1 !== 0;
    const stars = [];

    for (let i = 0; i < fullStars; i++) {
        stars.push('<i class="ri-star-fill"></i>');
    }

    if (hasHalf) {
        stars.push('<i class="ri-star-half-fill"></i>');
    }

    const result = stars.join('');
    starIconCache.set(rating, result); // Cache the result
    return result;
}

// Create book card using template literals for better performance
function createBookCard(book, index) {
    return `
      <div class="col-12 col-md-6 col-xl-4 col-xxl-3">
        <div class="card">
          <div class="d-flex align-items-center gap-3 card-body">
            <img src="${book.image}" loading="lazy" alt="${book.title}" class="h-40 rounded-3 cursor-pointer book-thumbnail" data-book-index="${index}">
            <div class="overflow-hidden flex-grow-1">
              <h6 class="mb-1 text-truncate lh-base"><a href="#!" class="link link-custom book-link" data-book-index="${index}">${book.title}</a></h6>
              <p class="mb-2 text-muted">نوشته <a href="#!" class="link link-custom-success">${book.author}</a></p>
              <div class="text-warning d-flex gap-1 mb-2">
                ${getStarIcons(book.rating)}
                <span class="text-dark-emphasis"> (${book.reviews})</span>
              </div>
              <h5 class="mb-2 fs-lg lh-base">${book.price.toFixed(2)} تومان</h5>
              <button type="button" class="w-100 btn btn-sub-danger">تهیه کنید</button>
            </div>
          </div>
        </div>
      </div>
    `;
}

// Batch DOM updates with DocumentFragment for better performance
function renderBooks() {
    const container = DOM.bookList;
    if (!container) return;

    // Filter books based on search
    const searchQuery = DOM.searchInput?.value?.trim().toLowerCase() || '';
    state.searchQuery = searchQuery;

    // Use memoization for filtered books when the search query hasn't changed
    if (state.searchQuery !== state.lastSearchQuery) {
        state.filteredBooks = searchQuery ?
            books.filter(book =>
                book.title.toLowerCase().includes(searchQuery) ||
                book.author.toLowerCase().includes(searchQuery)
            ) : [...books];

        state.lastSearchQuery = searchQuery;
        state.totalPages = Math.ceil(state.filteredBooks.length / CONFIG.booksPerPage);
        state.currentPage = 1; // Reset to first page on new search
    }

    const startIndex = (state.currentPage - 1) * CONFIG.booksPerPage;
    const endIndex = Math.min(startIndex + CONFIG.booksPerPage, state.filteredBooks.length);
    const booksToDisplay = state.filteredBooks.slice(startIndex, endIndex);

    // Use DocumentFragment for better performance
    const fragment = document.createDocumentFragment();
    const tempDiv = document.createElement('div');

    const cardsHTML = booksToDisplay.map((book, i) =>
        createBookCard(book, books.indexOf(book))
    ).join('');

    tempDiv.innerHTML = cardsHTML;

    while (tempDiv.firstChild) {
        fragment.appendChild(tempDiv.firstChild);
    }

    // Clear and update container in one operation
    container.innerHTML = '';
    if (booksToDisplay.length === 0) {
        container.innerHTML = `
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
        const fragment = document.createDocumentFragment();
        const tempDiv = document.createElement('div');

        const cardsHTML = booksToDisplay.map((book, i) =>
            createBookCard(book, books.indexOf(book))
        ).join('');

        tempDiv.innerHTML = cardsHTML;

        while (tempDiv.firstChild) {
            fragment.appendChild(tempDiv.firstChild);
        }

        container.appendChild(fragment);
    }

    // Use event delegation instead of multiple event listeners
    container.removeEventListener('click', handleBookClick);
    container.addEventListener('click', handleBookClick);

    updatePaginationInfo();
    updatePaginationButtons();
}

// Event delegation handler for book clicks
function handleBookClick(e) {
    const target = e.target.closest('[data-book-index]');
    if (target) {
        const bookIndex = parseInt(target.getAttribute('data-book-index'), 10);
        if (!isNaN(bookIndex) && books[bookIndex]) {
            updateBookModal(books[bookIndex]);

            // Get the modal element and initialize/show it with Bootstrap
            const modal = DOM.bookModal;
            if (modal && window.bootstrap) {
                const bsModal = new window.bootstrap.Modal(modal);
                bsModal.show();
            }
        }
    }
}

// Update pagination info
function updatePaginationInfo() {
    const { paginationInfo } = DOM;
    if (!paginationInfo) return;

    const totalItems = state.filteredBooks.length;
    const startItem = totalItems === 0 ? 0 : (state.currentPage - 1) * CONFIG.booksPerPage + 1;
    const endItem = Math.min(state.currentPage * CONFIG.booksPerPage, totalItems);

    paginationInfo.innerHTML = `
        <p class="text-muted text-center text-md-start mb-3 mb-md-0">
            نمایش <b class="me-1">${startItem}-${endItem}</b> از <b class="ms-1">${totalItems}</b> نتیجه
        </p>
    `;
}

// Update pagination buttons
function updatePaginationButtons() {
    const { pagination } = DOM;
    if (!pagination) return;

    const prevButton = pagination.querySelector('.page-item:first-child');
    const nextButton = pagination.querySelector('.page-item:last-child');
    if (!prevButton || !nextButton) return;

    const previousHTML = pagination.innerHTML;
    let paginationHTML = '';

    // Calculate page range
    let startPage = Math.max(1, state.currentPage - 2);
    let endPage = Math.min(state.totalPages, startPage + 4);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    // Build new pagination
    paginationHTML += `
        <li class="page-item ${state.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#!" data-nav="prev"><i data-lucide="chevron-right" class="size-4"></i>قبلی</a>
        </li>
    `;

    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === state.currentPage ? 'active' : ''}">
                <a class="page-link" href="#!" data-page="${i}">${i}</a>
            </li>
        `;
    }

    paginationHTML += `
        <li class="page-item ${state.currentPage === state.totalPages || state.totalPages === 0 ? 'disabled' : ''}">
            <a class="page-link" href="#!" data-nav="next">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>
        </li>
    `;

    // Only update if changed
    if (paginationHTML !== previousHTML) {
        pagination.innerHTML = paginationHTML;

        // Re-bind event listener
        pagination.removeEventListener('click', handlePaginationClick);
        pagination.addEventListener('click', handlePaginationClick);
    }
    createIcons({ icons });
}

// Handle pagination clicks
function handlePaginationClick(e) {
    e.preventDefault();
    const link = e.target.closest('.page-link');
    if (!link) return;

    const { nav, page } = link.dataset;

    if (nav === 'prev' && state.currentPage > 1) {
        state.currentPage--;
        renderBooks();
    } else if (nav === 'next' && state.currentPage < state.totalPages) {
        state.currentPage++;
        renderBooks();
    } else if (page) {
        const pageNum = parseInt(page, 10);
        if (pageNum && pageNum !== state.currentPage) {
            state.currentPage = pageNum;
            renderBooks();
        }
    }
}


// Update book modal with memoization
let lastDisplayedBook = null;
function updateBookModal(book) {
    const modal = DOM.bookModal;
    if (!modal) return;

    // Skip update if same book is already displayed
    if (lastDisplayedBook === book) return;
    lastDisplayedBook = book;

    const modalImg = modal.querySelector('#bookOverviewContent img');
    if (modalImg) modalImg.src = book.image;

    const starsContainer = modal.querySelector('.text-warning');
    if (starsContainer) {
        let starsHTML = getStarIcons(book.rating);
        starsHTML += `<span class="text-dark-emphasis"> (${book.reviews})</span>`;
        starsContainer.innerHTML = starsHTML;
    }

    const titleElement = modal.querySelector('#bookOverviewContent h6 a');
    if (titleElement) titleElement.textContent = book.title;

    const authorElement = modal.querySelector('#bookOverviewContent p.text-muted a');
    if (authorElement) authorElement.textContent = book.author;

    const priceElement = modal.querySelector('#bookOverviewContent h5');
    if (priceElement) priceElement.textContent = `${book.price.toFixed(2)} تومان`;
}

// Image validation helper
function validateImage(file) {
    return new Promise((resolve, reject) => {
        if (!file) {
            reject('فایلی انتخاب نشده است');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                if (img.width <= 105 && img.height <= 160) {
                    resolve({ valid: true, dataUrl: e.target.result });
                } else {
                    reject(`ابعاد تصویر (${img.width}x${img.height}) بزرگ تر از حداکثر اندازه  105x160 پیکسل می‌باشد`);
                }
            };
            img.onerror = () => reject('فایل تصویری نامعتبر');
            img.src = e.target.result;
        };
        reader.onerror = () => reject('خطا در خواندن فایل');
        reader.readAsDataURL(file);
    });
}

// Initialize all event listeners and cache DOM elements
function initApp() {
    // Cache DOM elements for better performance
    DOM.bookList = document.getElementById('bookList');
    DOM.searchInput = document.getElementById('searchInput');
    DOM.pagination = document.querySelector('.pagination');
    DOM.paginationInfo = document.querySelector('.pagination-info');
    DOM.bookModal = document.getElementById('bookOverviewModal');
    DOM.addBookModal = document.getElementById('addBookModal');
    DOM.imageInput = DOM.addBookModal?.querySelector('input[type="file"]');
    DOM.imagePreview = document.getElementById('imagePreview');
    DOM.imagePlaceholder = document.getElementById('imagePlaceholder');
    DOM.imageError = document.getElementById('imageError');
    DOM.addBookForm = DOM.addBookModal?.querySelector('#addBookForm');
    DOM.alertContainer = DOM.addBookModal?.querySelector('.alert-book-modal');

    // Set up search with debounce
    if (DOM.searchInput) {
        let searchTimer;
        DOM.searchInput.addEventListener('input', () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                state.currentPage = 1; // Reset to first page on search
                renderBooks();
            }, 300);
        });
    }

    if (DOM.imageInput) {
        DOM.imageInput.addEventListener('change', async function () {
            try {
                if (this.files && this.files[0]) {
                    const result = await validateImage(this.files[0]);

                    DOM.imagePreview.src = result.dataUrl;
                    DOM.imagePreview.classList.remove('d-none');
                    DOM.imagePlaceholder.classList.add('d-none');
                    DOM.imageError.classList.add('d-none');

                    if (DOM.alertContainer) {
                        DOM.alertContainer.innerHTML = '';
                    }
                }
            } catch (error) {
                DOM.imagePreview.classList.add('d-none');
                DOM.imagePlaceholder.classList.remove('d-none');
                DOM.imageError.classList.remove('d-none');

                showAlert(error);
                this.value = '';
            }
        });
    }

    // Set up add book form handler
    if (DOM.addBookForm) {
        DOM.addBookForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const titleInput = document.getElementById('bookTitleInput');
            const authorInput = document.getElementById('writerNameInput');
            const priceInput = document.getElementById('priceInput');

            const title = titleInput.value.trim();
            const author = authorInput.value.trim();
            const priceRaw = priceInput.value.trim().replace('تومان', '');
            const price = parseFloat(priceRaw);
            const imageFile = DOM.imageInput.files[0];

            let isValid = true;

            // Form validation
            if (!title) {
                titleInput.classList.add('is-invalid');
                isValid = false;
            }

            if (!author) {
                authorInput.classList.add('is-invalid');
                isValid = false;
            }

            if (isNaN(price) || price <= 0) {
                priceInput.classList.add('is-invalid');
                isValid = false;
            }

            if (!imageFile) {
                DOM.imageError.classList.remove('d-none');
                isValid = false;
            }

            if (!isValid) return;

            // Add new book to the collection
            const newBook = {
                title: title,
                author: author,
                image: imageFile ? URL.createObjectURL(imageFile) : "assets/images/school/book/img-01.jpg",
                rating: 5,
                reviews: 0,
                price: price
            };

            // Add to start of books array
            books.unshift(newBook);

            // Reset form and state
            this.reset();
            DOM.imagePreview.classList.add('d-none');
            DOM.imagePlaceholder.classList.remove('d-none');

            state.currentPage = 1;
            state.lastSearchQuery = null;
            renderBooks();

            // Hide modal
            if (DOM.addBookModal && window.bootstrap) {
                const modal = window.bootstrap.Modal.getInstance(DOM.addBookModal);
                if (modal) modal.hide();
            }
        });

        // Clear validation errors on input
        const formInputs = DOM.addBookForm.querySelectorAll('input');
        formInputs.forEach(input => {
            input.addEventListener('input', function () {
                this.classList.remove('is-invalid');
                if (this.type === 'file')
                    DOM.imageError.classList.add('d-none');
            });
        });
    }

    // Show alert helper
    function showAlert(message) {
        if (!DOM.alertContainer) return;

        DOM.alertContainer.innerHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
          <span>${message}</span>
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      `;
    }
    renderBooks();
}

// Initialize the application when DOM is fully loaded
document.addEventListener('DOMContentLoaded', initApp);