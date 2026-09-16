
const chatListItems = document.querySelectorAll('.chat-list-item');
let chatsBox = document.querySelector(".chat-messages");
const originalRenderChatWindow = renderChatWindow;
let activeUser = 'سارا جوادی';
const messageForm = document.querySelector('#messageForm');
const messageInput = messageForm.querySelector('input[type="text"]');
const sendButton = messageForm.querySelector('.btn-active-primary');
const dropdownMenu = messageForm.querySelector('.dropdown-menu');
const searchInput = document.getElementById("chatSearch");
const chatItems = document.querySelectorAll(".chat-list-item");
const chatData = {
'سارا جوادی': {
    avatar: 'assets/images/avatar/user-13.png',
    lastSeen: '2 ساعت پیش',
    messages: [
        {
            sender: 'سارا جوادی',
            avatar: 'assets/images/avatar/user-13.png',
            time: 'امروز، 09:59 صبح',
            content: 'ما به یک وب‌سایت جدید نیاز داریم که کاربران بتوانند حساب ایجاد کنند، محصولات را مرور کنند و خرید انجام دهند. می‌توانید یک جدول زمانی تقریبی و برآورد هزینه ارائه دهید؟',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'امروز، 10:00 صبح',
            content: 'حتماً، می‌توانیم کمک کنیم. برای ارائه برآورد دقیق، به جزئیات بیشتری درباره ویژگی‌هایی که می‌خواهید نیاز داریم. بیایید این هفته یک تماس برنامه‌ریزی کنیم تا موارد خاص مانند نوع محصولات، روش‌های پرداخت و ترجیحات طراحی را بررسی کنیم.',
            isMe: true
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'امروز، 10:15 صبح',
            content: 'فهمیدم. بررسی می‌کنم و به‌زودی به شما اطلاع می‌دهم. <a href="#!" class="link-danger">#bug</a>',
            isMe: true
        },
        {
            sender: 'سارا جوادی',
            avatar: 'assets/images/avatar/user-13.png',
            time: 'امروز، 10:11 صبح',
            content: 'سلام <a href="#!" class="link-primary">@Shopia</a>، می‌توانید ویژگی جستجوی جدید را تا جمعه اضافه کنید؟ جزئیات در کانال #features موجود است. ممنون! <a href="#!" class="link-primary">#task</a>',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'امروز، 10:12 صبح',
            content: 'حتماً، امروز شروع می‌کنم. درباره پیشرفت کار به شما اطلاع می‌دهم. <a href="#!" class="link-primary">#task154</a>',
            isMe: true
        },
        {
            sender: 'سارا جوادی',
            avatar: 'assets/images/avatar/user-13.png',
            time: 'امروز، 02:39 بعد از ظهر',
            content: 'سلام Shopia، مشکلی در نمایش موبایل صفحه اصلی وجود دارد. تصاویر درست مقیاس‌بندی نمی‌شوند. آیا کسی می‌تواند بررسی کند؟ <a href="#!" class="link-danger">#bug</a>',
            isMe: false,
            images: ['assets/images/gallery/img-01.jpg', 'assets/images/gallery/img-05.jpg']
        }
    ]
},
'دیوید جانسون': {
    avatar: 'assets/images/avatar/user-11.png',
    lastSeen: '1 ساعت پیش',
    messages: [
        {
            sender: 'دیوید جانسون',
            avatar: 'assets/images/avatar/user-11.png',
            time: 'امروز، 08:30 صبح',
            content: 'یه سری تصویر جذاب برات فرستادم',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'امروز، 08:45 صبح',
            content: 'ممنون از اشتراک‌گذاری! خیلی خوب هستند. آیا اجازه داریم از آن‌ها در پروژه خود استفاده کنیم؟',
            isMe: true
        },
        {
            sender: 'دیوید جانسون',
            avatar: 'assets/images/avatar/user-11.png',
            time: 'امروز، 09:00 صبح',
            content: 'حتماً، می‌توانید از آن‌ها استفاده کنید. نسخه‌های با کیفیت بالا را هم به زودی می‌فرستم.',
            isMe: false
        }
    ]
},
'اندرو گیلبرت': {
    avatar: 'assets/images/avatar/user-18.png',
    lastSeen: '3 ساعت پیش',
    messages: [
        {
            sender: 'اندرو گیلبرت',
            avatar: 'assets/images/avatar/user-18.png',
            time: 'دیروز، 03:15 بعد از ظهر',
            content: 'از ابزارهایی مثل Trello، Asana یا Jira برای مدیریت وظایف و پیگیری پیشرفت استفاده کنید.',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'دیروز، 03:30 بعد از ظهر',
            content: 'ممنون بابت پیشنهاد! بررسی‌شان می‌کنم.',
            isMe: true
        },
        {
            sender: 'اندرو گیلبرت',
            avatar: 'assets/images/avatar/user-18.png',
            time: 'دیروز، 04:00 بعد از ظهر',
            content: 'اگر برای راه‌اندازی آن‌ها به کمکی نیاز داشتی، اطلاع بده.',
            isMe: false
        }
    ]
},
'تایرون دربی': {
    avatar: 'assets/images/avatar/user-20.png',
    lastSeen: '30 دقیقه پیش',
    messages: [
        {
            sender: 'تایرون دربی',
            avatar: 'assets/images/avatar/user-20.png',
            time: 'دیروز، 04:30 بعد از ظهر',
            content: 'مرور منظم و بهبود روش‌های ارتباطی بر اساس بازخورد تیم و نیازهای پروژه.',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'دیروز، 04:45 بعد از ظهر',
            content: 'این یک نکته عالی است. مطمئن می‌شوم بازخورد تیم را جمع‌آوری کنم.',
            isMe: true
        },
        {
            sender: 'تایرون دربی',
            avatar: 'assets/images/avatar/user-20.png',
            time: 'دیروز، 05:00 بعد از ظهر',
            content: 'خوبه. اگر به قالب یا نمونه‌ای برای جلسات بازخورد نیاز داشتی، به من بگو.',
            isMe: false
        }
    ]
},
'سوزان لایلز': {
    avatar: '',
    initials: 'SL',
    lastSeen: '45 دقیقه پیش',
    messages: [
        {
            sender: 'سوزان لایلز',
            avatar: '',
            initials: 'SL',
            time: 'دیروز، 05:15 بعد از ظهر',
            content: 'برنامه‌ریزی برای چک‌این‌های منظم جهت رفع موانع و هماهنگی همه افراد.',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'دیروز، 05:30 بعد از ظهر',
            content: 'این را برای هفته آینده تنظیم می‌کنم.',
            isMe: true
        },
        {
            sender: 'سوزان لایلز',
            avatar: '',
            initials: 'SL',
            time: 'دیروز، 06:00 بعد از ظهر',
            content: 'عالی! اگر برای سازماندهی جلسه کمکی خواستی، به من اطلاع بده.',
            isMe: false
        }
    ]
},
'جاش دویل': {
    avatar: '',
    initials: 'JD',
    lastSeen: '15 دقیقه پیش',
    messages: [
        {
            sender: 'جاش دویل',
            avatar: '',
            initials: 'JD',
            time: 'دیروز، 06:00 بعد از ظهر',
            content: 'سؤال دیگری نیست.',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'دیروز، 06:30 بعد از ظهر',
            content: 'خوبه، اگر مورد دیگری به ذهن‌ت رسید، با خیال راحت اطلاع بده.',
            isMe: true
        },
        {
            sender: 'جاش دویل',
            avatar: '',
            initials: 'JD',
            time: 'دیروز، 07:00 بعد از ظهر',
            content: 'حتماً، ممنون!',
            isMe: false
        }
    ]
},
'نیکلاس هوپ': {
    avatar: 'assets/images/avatar/user-3.png',
    lastSeen: '1 ساعت پیش',
    messages: [
        {
            sender: 'نیکلاس هوپ',
            avatar: 'assets/images/avatar/user-3.png',
            time: 'امروز، 11:30 صبح',
            content: 'مطمئناً، می‌توانم در این زمینه کمک کنم. بعد از این جلسه یک تماس کوتاه برای رفع مشکل داشته باشیم.',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'امروز، 12:00 ظهر',
            content: 'ممنون، برای تماس آماده خواهم بود.',
            isMe: true
        },
        {
            sender: 'نیکلاس هوپ',
            avatar: 'assets/images/avatar/user-3.png',
            time: 'امروز، 12:30 ظهر',
            content: 'پس بیایید شروع کنیم. من هم اکنون در دسترس هستم.',
            isMe: false
        }
    ]
},
'لوئیز برایان': {
    avatar: '',
    initials: 'LB',
    lastSeen: '2 ساعت پیش',
    messages: [
        {
            sender: 'لوئیز برایان',
            avatar: '',
            initials: 'LB',
            time: 'امروز، 12:15 ظهر',
            content: 'به زودی صورتجلسه و اقدامات جلسه را به اشتراک می‌گذارم.',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'امروز، 12:45 ظهر',
            content: 'ممنون! بعد از اشتراک‌گذاری آن‌ها را بررسی می‌کنم.',
            isMe: true
        },
        {
            sender: 'لوئیز برایان',
            avatar: '',
            initials: 'LB',
            time: 'امروز، 01:00 بعد از ظهر',
            content: 'آن‌ها را ارسال کردم، اگر سؤالی داشتی به من اطلاع بده.',
            isMe: false
        }
    ]
},
'سیرکا هاکولا': {
    avatar: 'assets/images/avatar/user-6.png',
    lastSeen: '3 ساعت پیش',
    messages: [
        {
            sender: 'سیرکا هاکولا',
            avatar: 'assets/images/avatar/user-6.png',
            time: 'امروز، 01:00 بعد از ظهر',
            content: 'هفته آینده دوباره برای چک‌این منظم ملاقات کنیم. هفته‌ی پرباری داشته باشید!',
            isMe: false
        },
        {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: 'امروز، 01:30 بعد از ظهر',
            content: 'ممنون، شما هم هفته خوبی داشته باشید!',
            isMe: true
        },
        {
            sender: 'سیرکا هاکولا',
            avatar: 'assets/images/avatar/user-6.png',
            time: 'امروز، 02:00 بعد از ظهر',
            content: 'منتظر جلسه بعدی هستم. به زودی صحبت می‌کنیم!',
            isMe: false
        }
    ]
}
};
function renderChatWindow(username) {
    chatListItems.forEach(item => {
        const itemUsername = item.querySelector('h6').textContent;
        if (itemUsername === username) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    const userData = chatData[username] || chatData['سارا جوادی'];
    const chatHeader = document.querySelector('.chat-toolbar');
    const avatarImg = chatHeader.querySelector('img');
    if (userData.avatar) {
        avatarImg.src = userData.avatar;
        avatarImg.style.display = 'block';
        const initialsElement = chatHeader.querySelector('.initials');
        if (initialsElement) {
            initialsElement.style.display = 'none';
        }
    } else if (userData.initials) {
        avatarImg.style.display = 'none';
        const initialsElement = chatHeader.querySelector('.initials');
        if (initialsElement) {
            initialsElement.textContent = userData.initials;
            initialsElement.style.display = 'block';
        } else {
            const initialsSpan = document.createElement('span');
            initialsSpan.className = 'initials fw-semibold';
            initialsSpan.textContent = userData.initials;
            avatarImg.parentNode.appendChild(initialsSpan);
        }
    }
    chatHeader.querySelector('h6 a').textContent = username;
    chatHeader.querySelector('p').textContent = `آخرین بازدید ${userData.lastSeen}`;
    const chatBody = document.querySelector('#chat-messages');
    chatBody.innerHTML = '';
    userData.messages.forEach((message, index) => {
        let messageHTML = '';
        const messageId = `msg-${index}`;
        if (message.isMe) {
            messageHTML = `
                <div  id="${messageId}" class="d-flex align-items-end gap-2 ms-auto max-w-xl">
                  <div class="flex-grow-1 mb-3">
                    <div class="d-flex align-items-end gap-2">
                      <div class="flex-grow-1">
                        <p class="text-muted mb-1 fs-12 text-end">${message.time}</p>
                        <div class="px-4 py-10px bg-light-subtle text-body rounded-top-3 rounded-start-3">${message.content}</div>
                      </div>
                      <div class="dropdown">
                        <button class="btn btn-link text-muted p-0" type="button" data-bs-toggle="dropdown" aria-expanded="true" title="dropdown-button">
                          <i class="ri-more-2-fill text-muted"></i>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end shadow-sm">
                          <li>
                            <a href="#!" class="dropdown-item">
                              <i class="ri-reply-line me-1"></i>
                              <span>پاسخ به</span>
                            </a>
                          </li>
                          <li>
                            <a href="#!" class="dropdown-item delete-message" data-id="${messageId}">
                              <i class="ri-delete-bin-line me-1"></i>
                              <span>حذف</span>
                            </a>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  <div class="position-relative size-8 flex-shrink-0 d-flex justify-content-center align-items-center">
                    <img src="${message.avatar}" alt="" class="img-fluid rounded-circle">
                    <span class="status-indicator position-absolute bottom-0 end-0 bg-success border border-2 border-light-subtle rounded-circle size-2-5"></span>
                  </div>
                </div>
              `;
        } else {
            let imageGallery = '';
            if (message.images && message.images.length > 0) {
                imageGallery = `
                  <div class="row g-2">
                    ${message.images.map((img, index) => `
                      <div class="col-3">
                        <a href="#!" title="Gallery Image ${index + 1}">
                          <img src="${img}" alt="Image ${index + 1}" class="img-fluid rounded">
                        </a>
                      </div>
                    `).join('')}
                    ${message.images.length > 2 ? `
                      <div class="col-3">
                        <a href="#!" title="Gallery Image 3" class="p-3 bg-light-subtle d-flex align-items-center justify-content-center link-body-emphasis text-body rounded h-100">
                          <h6 class="mb-0">${message.images.length - 2}+</h6>
                        </a>
                      </div>
                    ` : ''}
                  </div>
                `;
            }
            let userAvatarHTML = '';
            if (message.avatar) {
                userAvatarHTML = `<img src="${message.avatar}" alt="" class="img-fluid rounded-circle">`;
            } else if (message.initials) {
                userAvatarHTML = `<span class="fw-semibold">${message.initials}</span>`;
            }
            messageHTML = `
                <div  id="${messageId}"class="d-flex align-items-end gap-2 max-w-xl">
                  <div class="position-relative size-8 flex-shrink-0 d-flex justify-content-center align-items-center">
                    ${userAvatarHTML}
                    <span class="status-indicator position-absolute bottom-0 end-0 bg-success border border-2 border-light-subtle rounded-circle size-2-5"></span>
                  </div>
                  <div class="flex-grow-1 mb-3">
                    <div class="d-flex align-items-end gap-2 ${imageGallery ? 'mb-3' : ''}">
                      <div class="flex-grow-1">
                        <p class="text-muted mb-1 fs-12">${message.time}</p>
                        <div class="px-4 py-10px bg-light-subtle text-body rounded-top-3 rounded-end-3">
                          ${message.content}
                        </div>
                      </div>
                      <div class="dropdown">
                        <button class="btn btn-link text-muted p-0" type="button" data-bs-toggle="dropdown" aria-expanded="true" title="dropdown-button">
                          <i class="ri-more-2-fill text-muted"></i>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end shadow-sm">
                          <li>
                            <a href="#!" class="dropdown-item">
                              <i class="ri-reply-line me-1"></i>
                              <span>پاسخ به</span>
                            </a>
                          </li>
                          <li>
                            <a href="#!" class="dropdown-item delete-message" data-id="${messageId}">
                                <i class="ri-delete-bin-line me-1"></i>
                                <span>حذف</span>
                            </a>
                          </li>
                        </ul>
                      </div>
                    </div>
                    ${imageGallery}
                  </div>
                </div>
              `;
        }
        chatBody.innerHTML += messageHTML;
    });
    const chatSection = document.querySelector('.chat-height');
    chatSection.scrollTop = chatSection.scrollHeight;
    const activeListItem = document.querySelector(`.chat-list-item.active .badge`);
    if (activeListItem) {
        activeListItem.style.display = 'none';
    }
    activeUser = username;
    // Update the delete-message functionality
    chatBody.querySelectorAll('.delete-message').forEach(deleteBtn => {
        deleteBtn.addEventListener('click', function (e) {
            e.preventDefault();
            const messageId = this.getAttribute('data-id');
            const messageIndex = parseInt(messageId.split('-')[1]);

            // Remove the message from the chatData object
            if (chatData[activeUser] && chatData[activeUser].messages && messageIndex >= 0) {
                chatData[activeUser].messages.splice(messageIndex, 1);
            }

            // Re-render the chat window to reflect the updated data
            renderChatWindow(activeUser);
        });
    });
}
chatListItems.forEach(item => {
    item.addEventListener('click', function (e) {
        e.preventDefault();
        const username = this.querySelector('h6').textContent;
        renderChatWindow(username);
    });
});
renderChatWindow(activeUser);
function sendMessage() {
    const messageContent = messageInput.value.trim();
    if (messageContent) {
        const newMessage = {
            sender: 'من',
            avatar: 'assets/images/avatar/user-17.png',
            time: formatCurrentTime(),
            content: messageContent,
            isMe: true
        };
        chatData[activeUser].messages.push(newMessage);
        renderChatWindow(activeUser);
        scrollToBottom();
        messageInput.value = '';
    }
}
function scrollToBottom() {
    setTimeout(() => {
        if (chatsBox && chatsBox.lastElementChild) {
            chatsBox.lastElementChild.scrollIntoView({ behavior: "smooth", block: "end" });
        } else {
            chatsBox = document.querySelector('#chat-messages');
            if (chatsBox && chatsBox.lastElementChild) {
                chatsBox.lastElementChild.scrollIntoView({ behavior: "smooth", block: "end" });
            }
        }
    }, 200);
}
if (sendButton) {
    sendButton.addEventListener('click', function (e) {
        e.preventDefault();
        sendMessage();
    });
}
if (messageInput) {
    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
}
if (dropdownMenu) {
    const clearChatButton = dropdownMenu.querySelector('a:first-child');
    if (clearChatButton) {
        clearChatButton.addEventListener('click', function (e) {
            e.preventDefault();
            chatData[activeUser].messages = [];
            renderChatWindow(activeUser);
        });
    }
}
function formatCurrentTime() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'بعد از ظهر' : 'صبح';
    const formattedHours = (hours % 12) || 12;
    return `امروز, ${formattedHours}:${minutes} ${ampm}`;
}
document.getElementById('callModal').addEventListener('show.bs.modal', function (event) {
    const userData = chatData[activeUser] || chatData['سارا جوادی'];
    const modalImageContainer = this.querySelector('#callAvatar');
    const modalImage = modalImageContainer.querySelector('img');
    const modalUsername = this.querySelector('.modal-body h6');
    const existingInitials = modalImageContainer.querySelector('.initials');
    if (existingInitials) {
        existingInitials.remove();
    }
    if (userData.avatar && userData.avatar !== '') {
        modalImage.src = userData.avatar;
        modalImage.style.display = 'block';
    } else {
        modalImage.style.display = 'none';
        const initialsElement = document.createElement('span');
        initialsElement.className = 'initials fw-semibold d-flex justify-content-center align-items-center size-10 rounded-circle bg-light-subtle';
        initialsElement.textContent = userData.initials || '';
        initialsElement.style.display = 'flex';
        modalImageContainer.appendChild(initialsElement);
    }
    modalUsername.textContent = activeUser;
});
renderChatWindow = function (username) {
    originalRenderChatWindow(username);
    activeUser = username;
};
function addNewChatUser(username, avatar) {
    if (!chatData[username]) {
        chatData[username] = {
            avatar: avatar || '',
            lastSeen: 'حالا',
            messages: []
        };
        if (!avatar) {
            const nameParts = username.split(' ');
            let initials = '';
            if (nameParts.length >= 2) {
                initials = nameParts[0].charAt(0) + nameParts[1].charAt(0);
            } else {
                initials = nameParts[0].charAt(0);
            }
            chatData[username].initials = initials;
        }
        const chatList = document.querySelector('#chatList');
        if (!chatList) {
            console.error('Chat list element not found');
            return;
        }
        const newChatItem = document.createElement('li');
        newChatItem.id = 'chat-list-item';
        if (avatar) {
            newChatItem.innerHTML = `
          <a href="#!" class="chat-list-item">
            <div class="position-relative size-10 bg-light flex-shrink-0 rounded-circle avatar">
              <img src="${avatar}" alt="" class="img-fluid rounded-circle">
              <span class="status-indicator bg-success rounded-circle size-2-5"></span>
            </div>
            <div class="flex-grow-1 overflow-hidden">
              <h6 class="mb-0 fw-bold">${username}</h6>
              <p class="fs-12 text-muted text-truncate">شروع یک گفتگو</p>
            </div>
            <div class="fs-11 text-body-secondary">حالا</div>
            <span class="badge bg-danger rounded-circle position-absolute top-0 end-0 d-none">0</span>
          </a>
        `;
        }
        newChatItem.addEventListener('click', function (e) {
            e.preventDefault();
            renderChatWindow(username);
        });
        chatList.appendChild(newChatItem);
        const modal = document.getElementById('addNewChatModals');
        const bsModal = window.bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
        renderChatWindow(username);
        return true;
    } else {
        renderChatWindow(username);
        const modal = document.getElementById('addNewChatModals');
        const bsModal = window.bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
        return true;
    }
}
document.querySelectorAll('.toggle-mic').forEach(button => {
    button.addEventListener('click', () => {
        const micOffIcon = button.querySelector('.mic-off-icon');
        const micOnIcon = button.querySelector('.mic-on-icon');

        micOffIcon.classList.toggle('d-none');
        micOnIcon.classList.toggle('d-none');
    });
});
document.addEventListener('DOMContentLoaded', function () {
    const addNewChatModal = document.getElementById('addNewChatModals');
    if (addNewChatModal) {
        const sendButtons = addNewChatModal.querySelectorAll('.btn.btn-xs.btn-light');
        sendButtons.forEach(button => {
            button.addEventListener('click', function (e) {
                e.preventDefault();
                const listItem = this.closest('li');
                if (!listItem) return;
                const username = listItem.querySelector('h6').textContent;
                const avatarImg = listItem.querySelector('img');
                const avatar = avatarImg ? avatarImg.getAttribute('src') : '';
                const success = addNewChatUser(username, avatar);
                if (!success) {
                    console.error('Failed to add new chat user');
                }
            });
        });
    }
    const searchInput = document.querySelector('#addNewChatModals input[type="text"]');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase();
            const contactItems = document.querySelectorAll('#addNewChatModals li');
            contactItems.forEach(item => {
                const username = item.querySelector('h6').textContent.toLowerCase();
                if (username.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});
searchInput.addEventListener("input", function () {
    const query = this.value.toLowerCase();
    const noResultElement = document.getElementById("noResult");
    let resultsFound = false;

    chatItems.forEach(item => {
        const name = item.querySelector("h6").textContent.toLowerCase();
        const message = item.querySelector("p").textContent.toLowerCase();

        if (name.includes(query) || message.includes(query)) {
            item.closest("li").style.display = "";
            resultsFound = true;
        } else {
            item.closest("li").style.display = "none";
        }
    });

    // Toggle visibility of the "no results" message
    if (!resultsFound && query !== '') {
        noResultElement.classList.remove("d-none");
    } else {
        noResultElement.classList.add("d-none");
    }
});
const addNewChatSearchInput = document.querySelector('#addNewChatModals input[type="text"]');
if (addNewChatSearchInput) {
    addNewChatSearchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        const contactItems = document.querySelectorAll('#addNewChatModals li');
        let contactsFound = false;

        contactItems.forEach(item => {
            const username = item.querySelector('h6').textContent.toLowerCase();
            if (username.includes(searchTerm)) {
                item.style.display = '';
                contactsFound = true;
            } else {
                item.style.display = 'none';
            }
        });

        // If we had a "no results" element for the modal, we would toggle it here
        const modalNoResult = document.querySelector('#addNewChatModals .no-result');
        if (modalNoResult) {
            if (!contactsFound && searchTerm !== '') {
                modalNoResult.classList.remove('d-none');
            } else {
                modalNoResult.classList.add('d-none');
            }
        }
    });
}

renderChatWindow(activeUser);
window.onload = function () {
    scrollToBottom();
};