// Get the timer element
const timerElement = document.getElementById('timeToLeftPage');

// Set the initial time in seconds (5 minutes = 300 seconds)
let timeLeft = 300;

// Update the timer every second
const countdown = setInterval(function () {
    // Calculate minutes and seconds
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;

    // Display the time in MM:SS format
    timerElement.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

    // Decrease the time left
    timeLeft--;

    // If time runs out, redirect to index.html
    if (timeLeft < 0) {
        clearInterval(countdown);
        window.location.href = 'apps-ecommerce-products-list.html';
    }
}, 1000);

const products = [
    {
        id: 1,
        category: "مد",
        title: "لباس ژاکت کشباف",
        image: "assets/images/products/img-04.png",
        price: 22.12,
        originalPrice: 29.49,
        discount: 25,
        quantity: 1,
        selectedSize: "S",
        selectedColor: "bg-primary",
        colors: ["bg-primary", "bg-dark", "bg-pink", "bg-success", "bg-danger"],
        sizes: ["S", "M", "L", "XL", "2XL"]
    },
    {
        id: 2,
        category: "کفش",
        title: "کفش‌های ورزشی مردانه مشکی",
        image: "assets/images/products/img-03.png",
        price: 71.56,
        quantity: 2,
        selectedSize: "6",
        selectedColor: "bg-dark",
        colors: ["bg-dark", "bg-pink"],
        sizes: ["6", "7", "8", "9", "10"]
    },
    {
        id: 3,
        category: "مد",
        title: "کاپشن هودی طرح‌دار آستین بلند",
        image: "assets/images/products/img-09.png",
        price: 44.49,
        quantity: 1,
        selectedSize: "X",
        selectedColor: "bg-primary",
        colors: ["bg-primary"],
        sizes: ["X", "L", "XL"]
    }
];

function renderCart() {
    const container = document.getElementById("cartProductList");
    container.innerHTML = "";

    products.forEach(product => {
        const colorHTML = product.colors.map(c => (
            `<a href="#!" class="avatar rounded-circle size-5 chart-icon-ring-primary ${c} outline-offset-0 color-option ${product.selectedColor === c ? 'border border-dark' : ''}" data-id="${product.id}" data-color="${c}"></a>`
        )).join("");

        const sizeHTML = product.sizes.map(s => (
            `<a href="#!" class="fw-medium size-option ${product.selectedSize === s ? "text-success" : "text-muted"}" data-id="${product.id}" data-size="${s}">${s}</a>`
        )).join("");

        const totalPrice = (product.price * product.quantity).toFixed(2);

        const card = document.createElement("div");
        card.className = "card mb-4";
        card.setAttribute("data-id", product.id);

        card.innerHTML = `
        <div class="card-body">
          <button type="button" class="btn-close position-absolute top-0 end-0 mt-4 me-4 remove-item"></button>
          <div class="row g-5">
            <div class="col-lg-3">
            <div class="bg-light-subtle rounded-2">
                <img src="${product.image}" loading="lazy" alt="Product Image" class="img-fluid">
            </div>
            </div>
            <div class="col-lg-9">
              <span class="badge bg-light-subtle border border-dark-subtle text-dark">${product.category}</span>
              <h6 class="mt-2 mb-3"><a href="#!" class="text-body">${product.title}</a></h6>
              <div class="row g-5">
                <div class="col">
                  <h6 class="mb-0 lh-base">انتخاب رنگ</h6>
                  <div class="d-flex gap-3 align-items-center mt-2 flex-grow-1">${colorHTML}</div>
                </div>
                <div class="col">
                  <h6 class="mb-0 lh-base">انتخاب اندازه</h6>
                  <div class="d-flex gap-2 mt-3">${sizeHTML}</div>
                </div>
              </div>
              <h5 class="d-flex align-items-center gap-2 mt-4">
                <span class="fs-lg price-display">${totalPrice} تومان</span>
                ${product.originalPrice ? `
                  <p class="text-muted text-decoration-line-through fw-normal fs-sm">${product.originalPrice} تومان</p>
                  <span class="badge bg-danger-subtle border border-danger-subtle text-danger">${product.discount}%</span>` : ""
            }
              </h5>
              <div class="mt-5">
                <div class="input-spin-group input-borderless p-1 border rounded">
                  <button type="button" class="input-spin-minus btn bg-primary-subtle text-primary px-2 border-0 size-8 d-flex justify-content-center align-items-center" data-id="${product.id}"><i data-lucide="minus" class="size-4"></i></button>
                  <input type="text" class="input-spin form-control text-center border-0 h-8 quantity-display" readonly value="${product.quantity}">
                  <button type="button" class="input-spin-plus btn bg-primary-subtle text-primary px-2 border-0 size-8 d-flex justify-content-center align-items-center" data-id="${product.id}"><i data-lucide="plus" class="size-4"></i></button>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
        container.appendChild(card);
    });

    attachEvents();
}

function attachEvents() {
    document.querySelectorAll(".input-spin-minus").forEach(btn => {
        btn.addEventListener("click", () => {
            const id = +btn.dataset.id;
            const product = products.find(p => p.id === id);
            if (product.quantity > 1) {
                product.quantity--;

                const card = btn.closest(".card");
                card.querySelector(".quantity-display").value = product.quantity;
                card.querySelector(".price-display").textContent = `${(product.price * product.quantity).toFixed(2)} تومان`;

                updateSummary();
            }
        });
    });

    document.querySelectorAll(".input-spin-plus").forEach(btn => {
        btn.addEventListener("click", () => {
            const id = +btn.dataset.id;
            const product = products.find(p => p.id === id);
            product.quantity++;

            const card = btn.closest(".card");
            card.querySelector(".quantity-display").value = product.quantity;
            card.querySelector(".price-display").textContent = `${(product.price * product.quantity).toFixed(2)} تومان`;

            updateSummary();
        });
    });

    document.querySelectorAll(".remove-item").forEach(btn => {
        btn.addEventListener("click", () => {
            const card = btn.closest(".card");
            const id = +card.dataset.id;
            const index = products.findIndex(p => p.id === id);
            if (index !== -1) {
                products.splice(index, 1);
                card.remove();
                updateSummary();
            }

        });
    });

    document.querySelectorAll(".size-option").forEach(link => {
        link.addEventListener("click", () => {
            const id = +link.dataset.id;
            const size = link.dataset.size;
            const product = products.find(p => p.id === id);
            product.selectedSize = size;

            // Only update styling, no re-render
            const card = link.closest(".card");
            card.querySelectorAll(".size-option").forEach(el => {
                el.classList.remove("text-success");
                el.classList.add("text-muted");
            });
            link.classList.add("text-success");
            link.classList.remove("text-muted");
        });
    });

    document.querySelectorAll(".color-option").forEach(link => {
        link.addEventListener("click", () => {
            const id = +link.dataset.id;
            const color = link.dataset.color;
            const product = products.find(p => p.id === id);
            product.selectedColor = color;

            // Only update styling, no re-render
            const card = link.closest(".card");
            card.querySelectorAll(".color-option").forEach(el => {
                el.classList.remove("border", "border-dark");
            });
            link.classList.add("border", "border-dark");
        });
    });
}

function updateSummary() {
    const subtotal = products.reduce((sum, p) => sum + p.price * p.quantity, 0);
    const vat = subtotal * 0.06;
    const discount = subtotal * 0.10; // assuming 10% discount
    const shipping = 35;
    const total = subtotal + vat + shipping - discount;

    document.getElementById("subtotal").textContent = subtotal.toFixed(2);
    document.getElementById("vat").textContent = vat.toFixed(2);
    document.getElementById("discount").textContent = discount.toFixed(2);
    document.getElementById("shipping").textContent = shipping.toFixed(2);
    document.getElementById("total").textContent = total.toFixed(2);
}


document.addEventListener("DOMContentLoaded", () => {
    renderCart();
    updateSummary(); 
});
