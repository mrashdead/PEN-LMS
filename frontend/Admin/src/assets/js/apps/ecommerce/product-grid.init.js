import { icons, createIcons } from "lucide";


//Filter Category & Color checkbox functionality
document.addEventListener('DOMContentLoaded', function () {
    // Initialize
    hideExtraCheckboxes();
    updateFilterCounts();

    // Listen for checkbox changes
    document.querySelectorAll('.form-check-input').forEach(checkbox => {
        checkbox.addEventListener('change', updateFilterCounts);
    });

    // "Show More/Less" button functionality
    document.querySelectorAll('.show-more').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            toggleCheckboxVisibility(this);
        });
    });
});

// Hide checkboxes
function hideExtraCheckboxes() {
    document.querySelectorAll('.product-filter').forEach(section => {
        const checkboxes = section.querySelectorAll('.form-check');
        checkboxes.forEach((checkbox, index) => {
            if (index >= 5) // Show only first 3 by default
                checkbox.style.display = 'none';
        });
    });
}

// Toggle visibility
function toggleCheckboxVisibility(link) {
    const container = link.closest('.product-filter');
    const checkboxes = container.querySelectorAll('.form-check');
    const isShowingMore = link.textContent.includes('بیشتر');

    checkboxes.forEach((checkbox, index) => {
        if (index >= 5)
            checkbox.style.display = isShowingMore ? 'block' : 'none';
    });

    if (isShowingMore)
        link.innerHTML = 'نمایش کمتر <i data-lucide="chevron-up" class="size-4"></i>';
    else
        link.innerHTML = 'نمایش بیشتر <i data-lucide="chevron-down" class="size-4"></i>';
}

function updateFilterCounts() {
    document.querySelectorAll('.product-filter').forEach(section => {
        const heading = section.querySelector('h6');
        const checkboxes = section.querySelectorAll('.form-check-input:checked');
        const category = heading.textContent.split('(')[0].trim();
        heading.textContent = `${category} (${checkboxes.length})`;
    });
}

//price
var arbitraryValuesSlider = document.getElementById('arbitrary-values-slider');
var arbitraryValuesForSlider = ['0', '50 تومان', '100 تومان', '500'];

var format = {
    to: function (value) {
        return arbitraryValuesForSlider[Math.round(value)];
    },
    from: function (value) {
        return arbitraryValuesForSlider.indexOf(value);
    }
};

noUiSlider.create(arbitraryValuesSlider, {
    // start values are parsed by 'format'
    start: ['50 تومان', '100 تومان'],
    range: { min: 0, max: arbitraryValuesForSlider.length - 1 },
    step: 1,
    tooltips: true,
    format: format,
    pips: { mode: 'steps', format: format, density: 50 },
});

class TableManager {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            itemsPerPage: options.itemsPerPage || 8,
            pageButtonCount: options.pageButtonCount || 3,
            ...options
        };
        this.currentPage = 1;
        this.data = [];
        this.filteredData = [];
        this.modalId = 'deleteModal';
        this.setupModal();
        this.deleteItemId = null;
    }

    // Set data and initialize the table
    setData(data) {
        this.data = data;
        this.filteredData = [...data];
        this.render();
        return this;
    }

    // Create delete confirmation modal
    setupModal() {
        if (!document.getElementById(this.modalId)) {
            const modalHTML = `
          <div class="modal fade" id="${this.modalId}" tabindex="-1" aria-labelledby="${this.modalId}Label" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered modal-xs">
              <div class="modal-content p-7 text-center">
                <div class="size-14 bg-danger-subtle rounded-circle avatar mx-auto mb-4">
                  <i data-lucide="trash-2" class="size-6 text-danger"></i>
                </div>
                <h5 class="mb-4 lh-base">آیا از حذف این محصول مطمئن هستید؟</h5>
                <div class="d-flex justify-content-center align-items-center gap-2">
                  <button class="btn btn-danger" id="confirmDelete">حذف</button>
                  <button class="btn btn-link link-primary text-dark" data-bs-dismiss="modal">لفو</button>
                </div>
              </div>
            </div>
          </div>
        `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);

            document.getElementById('confirmDelete').addEventListener('click', () => {
                if (this.deleteItemId !== null) {
                    this.removeItem(this.deleteItemId);
                    this.deleteItemId = null;
                    this.hideModal();
                }
            });
        }
    }

    // Show modal and set item to delete
    showDeleteModal(id) {
        this.deleteItemId = id;
        const modal = document.getElementById(this.modalId);
        const modalInstance = new window.bootstrap.Modal(modal);
        modalInstance.show();
    }

    // Hide the modal
    hideModal() {
        const modal = document.getElementById(this.modalId);
        const modalInstance = window.bootstrap.Modal.getInstance(modal);
        modalInstance.hide();
    }

    // Remove an item from the data
    removeItem(id) {
        this.data = this.data.filter(item => item.id !== id);
        this.filteredData = this.filteredData.filter(item => item.id !== id);

        // If current page is empty after deletion but not the first page, go back one page
        const totalPages = Math.ceil(this.filteredData.length / this.options.itemsPerPage);
        if (this.currentPage > totalPages && this.currentPage > 1) {
            this.currentPage = totalPages;
        }

        this.render();
    }
    // Generate the HTML for products grid
    generateProductsHtml() {
        const startIndex = (this.currentPage - 1) * this.options.itemsPerPage;
        const endIndex = startIndex + this.options.itemsPerPage;
        const currentItems = this.filteredData.slice(startIndex, endIndex);

        if (currentItems.length === 0) {
            return '<div class="col-12 text-center"><p>هیچ محصولی یافت نشد</p></div>';
        }

        return currentItems.map(item => `
        <div class="col-md-6 col-lg-4 col-xl-3">
          <div class="card card-hover-animate">
            <div class="p-2 card-body">
              <div class="position-relative p-5 bg-${item.bgColor}-subtle">
                <div class="dropdown position-absolute top-0 end-0 mt-2 me-2">
                  <a href="#!" class="link link-custom-danger avatar rounded-circle bg-body-secondary size-10" aria-label="More Action" id="moreDropdown${item.id}" data-bs-toggle="dropdown" aria-expanded="false">
                    <i class="ri-more-2-fill"></i>
                  </a>
                  <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="moreDropdown${item.id}">
                    <li><a class="dropdown-item" href="apps-ecommerce-product-overview.html"><i class="align-middle me-1 ri-eye-line"></i> نمای کلی</a></li>
                    <li><a class="dropdown-item" href="apps-ecommerce-create-products.html"><i class="align-middle me-1 ri-pencil-line"></i> ویرایش</a></li>
                    <li><a class="dropdown-item delete-btn" href="#" data-id="${item.id}"><i class="align-middle me-1 ri-delete-bin-6-line"></i> حذف</a></li>
                  </ul>
                </div>
                <img src="${item.image}" loading="lazy" alt="${item.title}" class="img-fluid">
              </div>
              <div class="p-1 mt-2">
                <h5 class="mb-2 lh-base fs-lg">${item.price}</h5>
                <h6 class="mb-1"><a href="apps-ecommerce-product-overview.html" class="text-reset">${item.title}</a></h6>
                <p class="text-muted">${item.category}</p>
                <div class="d-flex gap-2 mt-3">
                  <a href="apps-ecommerce-shop-cart.html" class="w-100 btn btn-primary">افزودن به سبد</a>
                  <a href="#!" class="btn btn-light btn-icon flex-shrink-0" aria-label="favorite">
                    <i class="fs-lg ri-heart-line"></i>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      `).join('');
    }

    // Generate pagination HTML
    generatePaginationHtml() {
        const totalItems = this.filteredData.length;
        const totalPages = Math.ceil(totalItems / this.options.itemsPerPage);

        if (totalPages <= 1) {
            return '';
        }

        let paginationHtml = `
        <div class="row align-items-center g-3 mb-5">
          <div class="col-md-6">
            <p class="text-muted text-center text-md-start mb-0">
              نمایش <b class="me-1">${(this.currentPage - 1) * this.options.itemsPerPage + 1}-${Math.min(this.currentPage * this.options.itemsPerPage, totalItems)}</b>
              از<b class="ms-1">${totalItems}</b> نتیجه
            </p>
          </div>
          <div class="col-md-6">
            <nav aria-label="Page navigation">
              <ul class="pagination justify-content-center justify-content-md-end mb-0">
                <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                  <a class="page-link prev-page" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>
                </li>
      `;

        // Calculate page range to display
        let startPage = Math.max(1, this.currentPage - Math.floor(this.options.pageButtonCount / 2));
        let endPage = Math.min(totalPages, startPage + this.options.pageButtonCount - 1);

        // Adjust if we're near the end
        if (endPage - startPage + 1 < this.options.pageButtonCount) {
            startPage = Math.max(1, endPage - this.options.pageButtonCount + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
          <li class="page-item ${i === this.currentPage ? 'active' : ''}">
            <a class="page-link page-number" data-page="${i}" href="#!">${i}</a>
          </li>
        `;
        }

        paginationHtml += `
                <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                  <a class="page-link next-page" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      `;

        return paginationHtml;
    }

    // Render the table and pagination
    render() {
        if (!this.container) return;

        const productsHtml = this.generateProductsHtml();
        const paginationHtml = this.generatePaginationHtml();

        this.container.innerHTML = `
        <div class="row">
          ${productsHtml}
        </div>
        ${paginationHtml}
      `;

        // Add event listeners
        this.addEventListeners();

        createIcons({ icons });
    }

    // Add event listeners
    addEventListeners() {
        // Pagination event listeners
        const prevBtn = this.container.querySelector('.prev-page');
        const nextBtn = this.container.querySelector('.next-page');
        const pageButtons = this.container.querySelectorAll('.page-number');

        if (prevBtn) {
            prevBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.render();
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const totalPages = Math.ceil(this.filteredData.length / this.options.itemsPerPage);
                if (this.currentPage < totalPages) {
                    this.currentPage++;
                    this.render();
                }
            });
        }

        pageButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page !== this.currentPage) {
                    this.currentPage = page;
                    this.render();
                }
            });
        });

        // Delete button event listeners - FIX APPLIED HERE
        const deleteButtons = this.container.querySelectorAll('.delete-btn');
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                // Fix: Find the closest .delete-btn element from the event target
                // This works even if the icon inside the button was clicked
                const deleteBtn = e.target.closest('.delete-btn');
                if (deleteBtn) {
                    const id = parseInt(deleteBtn.dataset.id);
                    this.showDeleteModal(id);
                }
            });
        });
    }
}

// Sample usage:
document.addEventListener('DOMContentLoaded', function () {
    // Sample product data extracted from the HTML
    const productData = [
        {
            id: 1,
            title: "تاپ لوله‌ای چروک",
            price: "15 تومان",
            category: "مد",
            image: "assets/images/products/img-01.png",
            bgColor: "primary"
        },
        {
            id: 2,
            title: "ساعت مچی رنگ طلایی",
            price: "60 تومان",
            category: "ساعت",
            image: "assets/images/products/img-02.png",
            bgColor: "success"
        },
        {
            id: 3,
            title: "کفش ورزشی سیاه مردانه",
            price: "35 تومان",
            category: "کفش",
            image: "assets/images/products/img-03.png",
            bgColor: "secondary"
        },
        {
            id: 4,
            title: "بلوز بافتنی کراپ",
            price: "30 تومان",
            category: "مد",
            image: "assets/images/products/img-04.png",
            bgColor: "pink"
        },
        {
            id: 5,
            title: "لباس آستین دار",
            price: "22 تومان",
            category: "مد",
            image: "assets/images/products/img-05.png",
            bgColor: "pink"
        },
        {
            id: 6,
            title: "تاپ کراپ توری",
            price: "30 تومان",
            category: "مد",
            image: "assets/images/products/img-06.png",
            bgColor: "light"
        },
        {
            id: 7,
            title: "کفش زنانه زرد",
            price: "37 تومان",
            category: "کفش",
            image: "assets/images/products/img-07.png",
            bgColor: "warning"
        },
        {
            id: 8,
            title: "کیف دستی چرم",
            price: "89 تومان",
            category: "کیف",
            image: "assets/images/products/img-08.png",
            bgColor: "danger"
        },
        {
            id: 9,
            title: "کاپشن هودی طرح Letterman آستین بلند",
            price: "44 تومان",
            category: "مد",
            image: "assets/images/products/img-09.png",
            bgColor: "info"
        },
        {
            id: 10,
            title: "کلاه آفتابی حصیری",
            price: "12 تومان",
            category: "لوازم جانبی",
            image: "assets/images/products/img-10.png",
            bgColor: "orange"
        },
        {
            id: 11,
            title: "کفش کتانی نایک بسکتبال",
            price: "32 تومان",
            category: "کفش",
            image: "assets/images/products/img-11.png",
            bgColor: "success"
        },
        {
            id: 12,
            title: "هدفون بی‌سیم",
            price: "90 تومان",
            category: "الکترونیکی",
            image: "assets/images/products/img-12.png",
            bgColor: "pink"
        },
        {
            id: 13,
            title: "زیرانداز یوگا پریمیوم",
            price: "33 تومان",
            category: "ورزشی",
            image: "assets/images/products/img-13.png",
            bgColor: "pink"
        },
        {
            id: 14,
            title: "بطری آب از جنس استیل ضد زنگ",
            price: "25 تومان",
            category: "اکسسوری‌ها",
            image: "assets/images/products/img-14.png",
            bgColor: "light"
        },
        {
            id: 15,
            title: "پیراهن راحتی مردانه",
            price: "38 تومان",
            category: "مد",
            image: "assets/images/products/img-15.png",
            bgColor: "warning"
        },
        {
            id: 16,
            title: "کیف پول چرمی",
            price: "45 تومان",
            category: "اکسسوری‌ها",
            image: "assets/images/products/img-16.png",
            bgColor: "danger"
        },
        {
            id: 17,
            title: "پاوربانک پرو 20000 میلی‌آمپر ساعت",
            price: "25 تومان",
            category: "الکترونیکی",
            image: "assets/images/products/img-17.png",
            bgColor: "light"
        },
        {
            id: 18,
            title: "توب ورزشی خارق‌العاده",
            price: "50 تومان",
            category: "ورزشی",
            image: "assets/images/products/img-18.png",
            bgColor: "warning"
        },
        {
            id: 19,
            title: "گوشواره‌های حلقه‌ای مینیمال",
            price: "80 تومان",
            category: "جواهرات",
            image: "assets/images/products/img-19.png",
            bgColor: "success"
        },
        {
            id: 20,
            title: "عینک آفتابی طرح‌دار",
            price: "85 تومان",
            category: "اکسسوری‌ها",
            image: "assets/images/products/img-20.png",
            bgColor: "pink"
        }
    ];

    // Instantiate and initialize the table manager
    const productsContainer = document.getElementById('products-container');
    if (productsContainer) {
        const tableManager = new TableManager('products-container', {
            itemsPerPage: 8,
            pageButtonCount: 3
        });

        tableManager.setData(productData);

        // Expose the table manager to the global scope for easier debugging (optional)
        window.tableManager = tableManager;
    }
});