import Swal from 'sweetalert2/dist/sweetalert2.js'


//Add Member Select
VirtualSelect.init({
    ele: "#addMemberSelect",
    options: [
        { label: "آئولی آهوکاس", value: "Auli Ahokas" },
        { label: "سیرپا کولکا", value: "Sirpa Kolkka" },
        { label: "لینا لین", value: "Leena Laine" },
        { label: "ریستو ساراسته", value: "Risto Saraste" },
        { label: "میکو ویرتانن", value: "Mikko Virtanen" },
        { label: "توولا نیمینن", value: "Tuula Nieminen" },
        { label: "رزا لینچ", value: "Rosa Lynch" },
        { label: "مگان اسنو", value: "Megan Snow" },
        { label: "جسیکا پری", value: "Jessica Perry" },
        { label: "جولی لاوسون", value: "Julie Lawson" },
        { label: "فیونا اسمیت", value: "Fiona Smith" },
        { label: "لیندا استاکی", value: "Linda Stucky" },
    ],
    search: true,
    allowNewOption: true,
    showValueAsTags: true,
    multiple: true,
});

const chatData = [
    {
        id: 1,
        name: "توسعه‌دهندگان Shopify",
        message: "سلام، حالت چطوره؟",
        time: "11:48 صبح",
        img: "assets/images/brands/img-08.png",
        badge: 2,
        active: true
    },
    {
        id: 2,
        name: "تیم رسانه اجتماعی",
        message: "سلام، حالت چطوره؟",
        time: "08:14 صبح",
        img: "assets/images/brands/img-12.png",
        badge: 2,
        active: false
    },
    {
        id: 3,
        name: "اختلال در استقرار",
        message: "سلام، حالت چطوره؟",
        time: "04:00 عصر",
        img: "assets/images/brands/img-02.png",
        badge: null,
        active: false
    },
    {
        id: 4,
        name: "تیم فول استک",
        message: "سلام، حالت چطوره؟",
        time: "05:14 عصر",
        img: "assets/images/brands/img-22.png",
        badge: null,
        active: false
    },
    {
        id: 5,
        name: "انتقام‌جویان UI/UX",
        message: "سلام، حالت چطوره؟",
        time: "11:57 صبح",
        img: "assets/images/brands/img-01.png",
        badge: null,
        active: false
    }
];

const chatList = document.getElementById("chatList");

chatData.forEach(chat => {
    const badge = chat.badge ? `<span class="badge bg-danger-subtle text-danger">${chat.badge}</span>` : '';
    const activeClass = chat.active ? "active" : "";

    chatList.innerHTML += `
      <li id="chat-${chat.id}">
        <a href="#!" class="chat-list-item ${activeClass}">
          <div class="position-relative size-10 bg-body-secondary flex-shrink-0 rounded-circle p-2">
            <img src="${chat.img}" alt="" class="img-fluid rounded-circle">
          </div>
          <div class="flex-grow-1 overflow-hidden">
            <h6 class="mb-0">${chat.name}</h6>
            <p class="fs-12 text-muted text-truncate">${chat.message}</p>
          </div>
          <div class="flex-shrink-0 text-end">
            <p class="mb-1 fs-12 text-muted">${chat.time}</p>
            ${badge}
          </div>
        </a>
      </li>
    `;
});

const chatItems = document.querySelectorAll(".chat-list-item");

chatItems.forEach(item => {
    item.addEventListener("click", (e) => {
        // Remove active class from all items
        chatItems.forEach(chat => chat.classList.remove("active"));

        // Add active class to the clicked item
        item.classList.add("active");

        // Get the selected chat id
        const selectedId = item.closest("li").id.split("-")[1];

        // Update chatData active status
        chatData.forEach(chat => {
            chat.active = chat.id == selectedId;
        });
    });
});


const saveGroupBtn = document.getElementById("saveGroupBtn");
const groupNameInput = document.getElementById("locationInput");

saveGroupBtn.addEventListener("click", () => {
    const groupName = groupNameInput.value.trim();

    if (groupName !== "") {
        const newChat = {
            id: chatData.length + 1,
            name: groupName,
            message: "گروه ایجاد شد",
            time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            img: "assets/images/brands/img-27.png", // Default group image
            badge: null,
            active: false
        };

        // Unshift new chat to array (add to top)
        chatData.unshift(newChat);

        // Prepend new chat to the list
        const chatItem = `
        <li id="chat-${newChat.id}">
          <a href="#!" class="chat-list-item">
            <div class="position-relative size-10 bg-body-secondary flex-shrink-0 rounded-circle p-2">
              <img src="${newChat.img}" alt="" class="img-fluid rounded-circle">
            </div>
            <div class="flex-grow-1 overflow-hidden">
              <h6 class="mb-0">${newChat.name}</h6>
              <p class="fs-12 text-muted text-truncate">${newChat.message}</p>
            </div>
            <div class="flex-shrink-0 text-end">
              <p class="mb-1 fs-12 text-muted">${newChat.time}</p>
            </div>
          </a>
        </li>
      `;

        // Add to top of the list
        chatList.insertAdjacentHTML("afterbegin", chatItem);

        // Reset input field
        groupNameInput.value = "";

        // Close modal
        const modal = window.bootstrap.Modal.getInstance(document.querySelector(".modal"));
        // modal.hide();
    } else {
        alert("لطفا نام گروه را وارد کنید");
    }
});


const searchInput = document.getElementById("searchChat");
const noResult = document.getElementById("noResult");

searchInput.addEventListener("keyup", () => {
    const searchText = searchInput.value.toLowerCase();
    const chatItems = document.querySelectorAll("#chatList li");
    let found = false;

    chatItems.forEach(item => {
        const name = item.querySelector("h6").textContent.toLowerCase();

        if (name.includes(searchText)) {
            item.style.display = "block"; // Show matched item
            found = true;
        } else {
            item.style.display = "none"; // Hide unmatched item
        }
    });

    // Show "No Result" if nothing is found
    if (found)
        noResult.classList.add("d-none");
    else
        noResult.classList.remove("d-none");
});
const chatHeaderName = document.querySelector(".avatar img");
const chatHeaderTitle = document.querySelector(".avatar").nextElementSibling.querySelector("a");
const chatProfileImage = document.querySelector(".text-center img");
const chatProfileName = document.querySelector(".text-center h6");

chatList.addEventListener("click", (e) => {
    const chatItem = e.target.closest(".chat-list-item");
    if (!chatItem) return;

    const imageSrc = chatItem.querySelector("img").src;
    const groupName = chatItem.querySelector("h6").textContent;

    // Header Image and Name
    chatHeaderName.src = imageSrc;
    chatHeaderTitle.textContent = groupName;

    // Profile Image and Name
    chatProfileImage.src = imageSrc;
    chatProfileName.textContent = groupName;
});


const messages = [
    {
        id: 1,
        name: "User 15",
        message: "سلام به اعضای تیم، امیدوارم حال همگی خوب باشه. بیاید یه مرور خیلی سریع داشته باشیم. امروز چه خبر؟",
        time: "امروز, 09:59 صبح",
        avatar: "assets/images/avatar/user-15.png",
        position: "left" // left message
    },
    {
        id: 2,
        name: "شما",
        message: "صبح بخیر! دارم روی طراحی قالب جدید کار می‌کنم. تقریباً کار صفحه اصلی تموم شده. بعدش می‌رم سراغ صفحات محصول. اگه کسی وقت داره می‌تونم از نظراتش در مورد هیرو سکشن استفاده کنم.",
        time: "امروز, 10:00 صبح",
        avatar: "assets/images/avatar/user-17.png",
        position: "right" // right message
    },
    {
        id: 3,
        name: "User 11",
        message: "سلام به همه. دارم یه مشکلی رو توی فرآیند پرداخت حل می‌کنم. انگار یه مشکلی توی یکپارچه‌سازی درگاه پرداخت هست. شما رو در جریان می‌ذارم.",
        time: "امروز, 10:11 صبح",
        avatar: "assets/images/avatar/user-11.png",
        position: "left"
    },
    {
        id: 4,
        name: "User 19",
        message: "سلام تیم! من دارم روی یکپارچه‌سازی سیستم بررسی شخص ثالث کار می‌کنم. یه مشکل کوچیک با محدودیت‌های API دارم، اما دارم حلش می‌کنم. باید تا آخر امروز درستش کنم.",
        time: "امروز, 10:30 صبح",
        avatar: "assets/images/avatar/user-19.png",
        position: "left"
    },
    {
        id: 5,
        name: "User 4",
        message: "سلام تیم. من در حال آزمایش به‌روزرسانی‌های اخیر روی سرور مرحله‌بندی هستم. چند اشکال جزئی در روند ثبت‌نام کاربر پیدا کردم. جیمی، جزئیات را به‌زودی با تو به اشتراک خواهم گذاشت.",
        time: "امروز, 10:30 صبح",
        avatar: "assets/images/avatar/user-4.png",
        position: "left"
    },
    {
        id: 6,
        name: "User 20",
        message: "ممنون سارا. کیسی، وقتی شروع به کار روی صفحات محصول کردم، بهت خبر میدم. ماکت‌هات خیلی خوب به نظر می‌رسن!",
        time: "امروز, 10:30 صبح",
        avatar: "assets/images/avatar/user-20.png",
        position: "left"
    },
    {
        id: 7,
        name: "User 17",
        message: "البته سارا. شاید وقتی کار ادغام درگاه پرداخت تمام شد، به یک جفت چشم دیگر برای بررسی روند پرداخت نیاز داشته باشم.",
        time: "امروز, 10:30 صبح",
        avatar: "assets/images/avatar/user-17.png",
        position: "right"
    }
];

const chatBody = document.querySelector(".d-flex.flex-column.gap-5");
const input = document.querySelector(".form-control");
const sendBtn = document.querySelector(".btn-active-primary");

function loadMessages() {
    chatBody.innerHTML = ""; // Clear previous messages

    messages.forEach(msg => {
        let chatHtml = `
      <div class="d-flex align-items-end gap-2 ${msg.position === "right" ? "ms-auto" : ""} max-w-xl" data-id="${msg.id}">
        ${msg.position === "left" ? `
          <div class="position-relative size-8 flex-shrink-0 avatar">
            <img src="${msg.avatar}" alt="" class="img-fluid rounded-circle">
            <span class="status-indicator bg-success size-2-5"></span>
          </div>` : ""}

        <div class="flex-grow-1">
          <div class="d-flex align-items-end gap-2">
            <div class="flex-grow-1">
              <p class="text-muted mb-1 fs-12 ${msg.position === "right" ? "text-end" : ""}">${msg.time}</p>
              <div class="px-4 py-10px bg-light text-body ${msg.position === "right" ? "rounded-top-3 rounded-start-3" : "rounded-top-3 rounded-end-3"}">
                ${msg.message}
              </div>
            </div>
            <div class="dropdown">
            <button class="btn btn-link text-muted p-0" type="button" aria-label="Dropdown" data-bs-toggle="dropdown" aria-expanded="true">
                <i class="ri-more-2-fill"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
                <li>
                    <a href="#!" class="dropdown-item">
                        <i class="ri-reply-line me-1"></i>
                        <span>پاسخ به</span>
                    </a>
                </li>
                <li class="delete-msg" data-id="${msg.id}">
                    <a href="#!" class="dropdown-item">
                        <i class="ri-delete-bin-line me-1"></i>
                        <span>حذف</span>
                    </a>
                </li>
            </ul>
        </div>
          </div>
        </div>

        ${msg.position === "right" ? `
          <div class="position-relative size-8 flex-shrink-0 avatar">
            <img src="${msg.avatar}" alt="" class="img-fluid rounded-circle">
            <span class="status-indicator bg-success size-2-5"></span>
          </div>` : ""}
      </div>
    `;
        chatBody.innerHTML += chatHtml;
    });

    // Add delete click event after rendering messages
    document.querySelectorAll(".delete-msg").forEach(btn => {
        btn.addEventListener("click", function () {
            const msgId = parseInt(this.dataset.id);
            deleteMessage(msgId);
        });
    });
}

// Function to delete a message
function deleteMessage(id) {
    messages.splice(messages.findIndex(msg => msg.id === id), 1);
    loadMessages();
}

// Function to send a message
function sendMessage() {
    let message = messageInput.value.trim();
    if (message !== "") {
        let newMsg = {
            id: messages.length + 1,
            sender: "شما",
            avatar: "assets/images/avatar/user-17.png",
            message: message,
            time: "امروز, " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            position: "right"
        };

        // Push Message in Array
        messages.push(newMsg);

        loadMessages();
        scrollToBottom();
        // Scroll to Bottom
        chatBody.scrollTop = chatBody.scrollHeight;

        // Clear Input
        messageInput.value = "";

        // Focus Input
        messageInput.focus();
    }
}

// Event listener for send button
sendBtn.onclick = sendMessage;



let chatsBox = document.querySelector(".chat-messages");
function scrollToBottom() {
    setTimeout(() => {
        const lastMessage = chatsBox.lastElementChild;
        if (lastMessage) {
            lastMessage.scrollIntoView({ behavior: "smooth", block: "end" });
        }
    }, 200);
}

messageInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        sendMessage();
        event.preventDefault();  // Prevent new line when Enter is pressed
    }
});

//Claer all chat messages
//Clear all chat messages
document.addEventListener("click", function (e) {
    const target = e.target.closest(".dropdown-item");

    if (!target) return; // If no target, exit

    if (target.innerText.includes("Clear Chat")) {
        Swal.fire({
            title: "آیا مطمئن هستید؟",
            text: "شما می‌خواهید تمام پیام‌های چت را پاک کنید!",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#3085d6",
            cancelButtonColor: "#d33",
            confirmButtonText: "بله، پاکش کن",
        }).then((result) => {
            if (result.isConfirmed) {
                // Clear the chat box
                chatBody.innerHTML = "";

                // Clear messages array properly (maintain the reference)
                messages.splice(0, messages.length);

                scrollToBottom();
                Swal.fire({
                    title: "پاک شد!",
                    text: "تمام پیام‌های چت پاک شده‌اند.",
                    icon: "success",
                    timer: 1500,
                    showConfirmButton: false,
                });
            }
        });
    }
});

loadMessages();

window.onload = function () {
    scrollToBottom();
};
