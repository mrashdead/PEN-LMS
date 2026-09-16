function showMailBox(event) {
    event.preventDefault();

    const mailSection = document.getElementById('mailSection');
    mailSection.style.display = 'block';

    mailSection.scrollIntoView({ behavior: 'smooth' });
}

function hideMailBox(event) {
    event.preventDefault();

    const mailSection = document.getElementById('mailSection');
    mailSection.style.display = 'none';
}

const emails = [
    {
        id: "checkMail1",
        img: "assets/images/avatar/user-11.png",
        initials: null,
        name: "آرماند نوتو",
        email: "armand@domiex.com",
        subject: "گزارش - پروژه‌های دومیکس",
        message: "لطفاً وضعیت پروژه را در فایل PDF پیوست شده مشاهده کنید. پروژه خوب پیش می‌رود و مطمئن هستیم که به موقع تکمیل خواهد شد.",
        date: "15 شهریور، 01:22 صبح",
        type: ["Inbox", "Starred", "Sent"],
        badges: ["صندوق ورودی", "جلسات تیم", "توسعه‌دهندگان"],
    },
    {
        id: "checkMail2",
        img: "assets/images/avatar/user-13.png",
        initials: null,
        name: "شری شنون",
        email: "sherry@domiex.com",
        subject: "سال نو مبارک، شاپیا",
        message: "متشکرم شاپیا، که همیشه به اشتراک‌های ما اعتماد دارید. به عنوان قدردانی، این کد تخفیف را می‌توانید در اپلیکیشن ما استفاده کنید.",
        date: "14 مرداد، 11:05 صبح",
        badges: ["توسعه‌دهندگان", "صندوق ورودی"],
        type: ["Drafts", "Inbox"]
    },
    {
        id: "checkMail4",
        img: null,
        initials: "BS",
        name: "باربارا ساتن",
        email: "barbara@domiex.com",
        subject: "یک مشترک جدید دارید",
        badges: ["عکاس", "صندوق ورودی"],
        message: "سلام! شما یک مشترک جدید در کانالتان دارید",
        date: "10 مرداد، 10:58 صبح",
        type: ["spam", "Inbox"]
    },
    {
        id: "checkMail5",
        img: null,
        initials: "MD",
        name: "مارک دنیلز",
        email: "mark@domiex.com",
        subject: "مهلت مهم پروژه",
        badges: ["اپلیکیشن", "صندوق ورودی"],
        message: "سلام تیم، می‌خواستم یادآوری کنم که مهلت پروژه بازاریابی نزدیک است. بیایید مطمئن شویم همه چیز آماده و تا جمعه ارسال شده باشد.",
        date: "07 مرداد، 04:22 بعدازظهر",
        type: ["Inbox", "Important", "spam"]
    },
    {
        id: "checkMail6",
        img: null,
        initials: "JA",
        name: "جیمز اندرسون",
        email: "james@domiex.com",
        subject: "پیشنهاد ویژه فقط برای شما!",
        badges: ["اپلیکیشن", "صندوق ورودی"],
        message: "سلام! ما یک پیشنهاد انحصاری برای مشترکان داریم. روی لینک زیر کلیک کنید تا تخفیف خود را دریافت کرده و از ویژگی‌های پریمیوم با نصف قیمت استفاده کنید.",
        date: "01 مرداد، 08:22 صبح",
        type: ["Inbox", "Spam"]
    },
    {
        id: "checkMail7",
        img: null,
        initials: "AR",
        name: "الکس راس",
        email: "alex@domiex.com",
        subject: "جلسه به زمان دیگری موکول شد",
        message: "سلام تیم، به دلیل شرایط پیش‌بینی نشده، جلسه تیم که برای فردا برنامه‌ریزی شده بود به دوشنبه آینده ساعت 10 صبح منتقل شد.",
        date: "23 تیر، 03:14 بعدازظهر",
        badges: ["توسعه‌دهندگان", "صندوق ورودی"],
        type: ["Inbox", "Trash"]
    },
    {
        id: "checkMail8",
        img: "assets/images/avatar/user-16.png",
        initials: null,
        name: "دارلین بلک",
        email: "darlene@domiex.com",
        subject: "حساب شما مسدود شده است",
        message: "متأسفیم که اطلاع دهیم حساب شما به دلیل فعالیت مشکوک مسدود شده است. لطفاً برای راهنمایی بیشتر با پشتیبانی تماس بگیرید.",
        date: "17 تیر، 12:11 بعدازظهر",
        badges: ["توسعه‌دهندگان", "صندوق ورودی"],
        type: ["Inbox", "Trash"]
    },
    {
        id: "checkMail9",
        img: "assets/images/avatar/user-3.png",
        initials: null,
        name: "لئونارد گارسیا",
        email: "leonard@domiex.com",
        badges: ["توسعه‌دهندگان", "صندوق ورودی"],
        subject: "خبرنامه هفتگی - نسخه تیر",
        message: "به خبرنامه تیر ما خوش آمدید! این ماه، جدیدترین به‌روزرسانی‌ها، ویژگی‌های جدید و نکات برجسته جامعه را پوشش می‌دهیم.",
        date: "14 تیر، 07:04 بعدازظهر",
        type: ["Scheduled", "Inbox"]
    },
    {
        id: "checkMail10",
        img: "assets/images/avatar/user-4.png",
        initials: null,
        name: "جسی رویز",
        email: "jesse@domiex.com",
        badges: ["جلسات تیم", "مهم"],
        subject: "پیش‌نویس‌های کمپین بازاریابی جدید",
        message: "سلام تیم، پیش‌نویس‌های اولیه کمپین بازاریابی جدید را پیوست کرده‌ام. لطفاً بررسی کرده و تا پایان روز جمعه بازخورد دهید.",
        date: "11 تیر، 04:51 صبح",
        type: ["Drafts", "Inbox"]
    },
    {
        id: "checkMail11",
        img: null,
        initials: "AR",
        name: "آنیتا رودریگز",
        email: "anita@domiex.com",
        subject: "تأیید رزرو جلسه عکاسی",
        badges: ["توسعه‌دهندگان", "صندوق ورودی"],
        message: "آنیتا عزیز، جلسه عکاسی شما برای شنبه ساعت 3 بعدازظهر تأیید شد. لطفاً 15 دقیقه زودتر حضور داشته باشید و تمام وسایل لازم را همراه بیاورید.",
        date: "04 تیر، 10:31 صبح",
        type: ["Starred", "Inbox"]
    }
];


const typetyles = {
    Inbox: "bg-body-tertiary text-muted border",
    "Team Meetings": "bg-danger-subtle text-danger border border-danger-subtle",
    Developers: "bg-warning-subtle text-warning border border-warning-subtle",
    Application: "bg-success-subtle text-success border border-success-subtle",
    Important: "bg-success-subtle text-success border border-success-subtle",
    spam: "bg-danger-subtle text-danger border border-danger-subtle",
    Trash: "bg-danger-subtle text-danger border border-danger-subtle",
    Marketing: "bg-danger-subtle text-danger border border-danger-subtle",
    Drafts: "bg-body-tertiary text-muted border",
    Photographer: "bg-info-subtle text-info border border-info-subtle"
};

const badgeKeyMap = {
    "توسعه‌دهندگان": "Developers",
    "صندوق ورودی": "Inbox",
    "اپلیکیشن": "Application",
    "مهم": "Important",
    "اسپم": "spam",
    "زباله": "Trash",
    "جلسات تیم": "Team Meetings",
    "پیش‌نویس": "Drafts",
    "عکاس": "Photographer",
};

function renderEmails(list = emails) {
    const container = document.getElementById("mailbox-list");
    container.innerHTML = ""; // Clear list first
    document.getElementById("message-count").textContent = `${list.length} پیام`;

    list.forEach(email => {
        const avatar = email.img
            ? `<img src="${email.img}" loading="lazy" alt="${email.name}" class="rounded-circle size-10">`
            : email.initials;

        const type = (email.type || [])
            .map(tag => `<span class="badge ${typetyles[tag] || ''}">${tag}</span>`)
            .join("");

        // Generate badges HTML from email.badges
        const badges = (email.badges || [])
            .map(badge => {
                const key = badgeKeyMap[badge];
                const classes = key ? (typetyles[key] || '') : 'bg-body-tertiary text-muted border';
                return `<span class="badge ${classes}">${badge}</span>`;
            })
            .join("");

        const html = `
            <div class="mailbox-list-item d-flex gap-3 p-5" data-id="${email.id}" style="cursor: pointer;">
              <div class="form-check check-primary flex-shrink-0 align-self-start mt-3">
              <input class="form-check-input" type="checkbox" id="${email.id}">
              <label class="form-check-label d-none" for="${email.id}">Check ${email.name}</label>
            </div>
            <div class="avatar text-danger rounded-circle size-10 bg-danger-subtle flex-shrink-0">${avatar}</div>
            <div class="overflow-hidden flex-grow-1">
              <p class="float-end fs-sm">${email.date}</p>
              <h6 class="mb-1">${email.name}</h6>
              <a href="#!" class="link link-custom-primary">${email.email}</a>
              <a href="#!" class="d-block mt-3 text-body">
                <h6 class="mb-1">${email.subject}</h6>
                <p class="text-truncate">${email.message}</p>
              </a>
              <div class="d-flex justify-content-end gap-2 mt-2">${badges}</div>
            </div>
          </div>
        `;

        container.insertAdjacentHTML("beforeend", html);
    });
}

const selectAllCheckbox = document.getElementById("allCheckMail");
const deleteBtn = document.getElementById("deleteBtn");

selectAllCheckbox.addEventListener("change", function () {
    const emailCheckboxes = document.querySelectorAll('#mailbox-list input[type="checkbox"]');

    emailCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });

    toggleDeleteBtn();
});

document.addEventListener("change", function (e) {
    if (e.target.matches('#mailbox-list input[type="checkbox"]')) {
        const emailCheckboxes = document.querySelectorAll('#mailbox-list input[type="checkbox"]');
        const checkedCount = [...emailCheckboxes].filter(cb => cb.checked).length;

        selectAllCheckbox.checked = (checkedCount === emailCheckboxes.length);
        toggleDeleteBtn();
    }
});

function toggleDeleteBtn() {
    const anyChecked = [...document.querySelectorAll('#mailbox-list input[type="checkbox"]')]
        .some(cb => cb.checked);

    if (anyChecked) {
        deleteBtn.classList.remove("d-none");
    } else {
        deleteBtn.classList.add("d-none");
    }
}

document.getElementById("searchResults").addEventListener("input", function () {
    const keyword = this.value.toLowerCase().trim();
    const filteredEmails = emails.filter(email =>
        email.name.toLowerCase().includes(keyword) ||
        email.email.toLowerCase().includes(keyword) ||
        email.subject.toLowerCase().includes(keyword) ||
        email.message.toLowerCase().includes(keyword)
    );

    renderEmails(filteredEmails);
    selectAllCheckbox.checked = false;
});

let currentEmailId = null;

function renderEmailContent(email) {
    currentEmailId = email.id;

    const senderName = document.querySelector('#mailOverview .card-body h6');
    const subjectLine = document.querySelector('#mailOverview .mt-5 h6');
    const messageBody = document.querySelector('#mailOverview .mt-5 .d-flex.flex-column p');
    const avatarContainer = document.querySelector('#mailOverview .avatar');
    const timestamp = document.querySelector('#mailOverview .fs-12.text-muted');

    if (senderName) senderName.textContent = email.name;
    if (subjectLine) subjectLine.textContent = email.subject;
    if (messageBody) messageBody.textContent = email.message;
    if (timestamp) timestamp.textContent = email.date;

    if (avatarContainer) {
        if (email.img) {
            avatarContainer.innerHTML = `<img src="${email.img}" loading="lazy" alt="${email.name}" class="rounded-circle size-10">`;
            avatarContainer.className = 'avatar text-danger rounded-circle bg-danger-subtle shrink-0 size-10';
        } else if (email.initials) {
            avatarContainer.innerHTML = email.initials;
            avatarContainer.className = 'avatar text-center d-flex align-items-center justify-content-center rounded-circle size-10 bg-primary-subtle text-primary shrink-0';
        }
    }

    const toEmailInput = document.getElementById('toEmailInput');
    if (toEmailInput) {
        toEmailInput.value = email.email;
    }
}

document.getElementById("mailbox-list").addEventListener("click", function (e) {
    const mailItem = e.target.closest('.mailbox-list-item');
    if (mailItem) {
        if (!e.target.closest('.form-check')) {
            e.preventDefault();
            const mailId = mailItem.dataset.id;
            const email = emails.find(email => email.id == mailId);
            if (email) {
                const mailOverview = document.getElementById("mailOverview");
                mailOverview.style.display = "";
                document.querySelector('.mailbox-wrapper').classList.add('show');
                renderEmailContent(email);
            }
        }
    }
});

document.querySelector('#mailOverview .card-header a').addEventListener('click', function (e) {
    e.preventDefault();
    const mailOverview = document.getElementById("mailOverview");
    mailOverview.style.display = "none";
    document.querySelector('.mailbox-wrapper').classList.remove('show');
    currentEmailId = null;
});

// Function to check and apply responsive styles
function applyResponsiveStyles() {
    const mailboxList = document.querySelector('.mailbox-list');
    const mailboxCard = mailboxList ? mailboxList.closest('.card.flex-grow-1') : null;

    if (mailboxCard) {
        if (window.innerWidth < 1024) {
            mailboxCard.style.display = 'block';
        } else {
            mailboxCard.style.display = '';
        }
    }
}

// Apply styles on page load
document.addEventListener('DOMContentLoaded', function () {
    applyResponsiveStyles();
});

// Apply styles when window is resized
window.addEventListener('resize', function () {
    applyResponsiveStyles();
});

// Modify the email click handler to show the email list on smaller screens
document.getElementById("mailbox-list").addEventListener("click", function (e) {
    const mailItem = e.target.closest('.mailbox-list-item');
    if (mailItem) {
        if (!e.target.closest('.form-check')) {
            e.preventDefault();
            const mailId = mailItem.dataset.id;
            const email = emails.find(email => email.id == mailId);
            if (email) {
                const mailOverview = document.getElementById("mailOverview");
                mailOverview.style.display = "";
                document.querySelector('.mailbox-wrapper').classList.add('show');
                renderEmailContent(email);

                // Hide the mailbox list on screens smaller than 1024px
                if (window.innerWidth < 1024) {
                    const mailboxCard = mailItem.closest('.card.flex-grow-1');
                    if (mailboxCard) {
                        mailboxCard.style.display = 'none';
                    }
                }
            }
        }
    }
});

// Modify the back button to show the email list again on smaller screens
document.querySelector('#mailOverview .card-header a').addEventListener('click', function (e) {
    e.preventDefault();
    const mailOverview = document.getElementById("mailOverview");
    mailOverview.style.display = "none";
    document.querySelector('.mailbox-wrapper').classList.remove('show');
    currentEmailId = null;

    // Show the mailbox list again on screens smaller than 1024px
    if (window.innerWidth < 1024) {
        const mailboxList = document.querySelector('.mailbox-list');
        const mailboxCard = mailboxList ? mailboxList.closest('.card.flex-grow-1') : null;
        if (mailboxCard) {
            mailboxCard.style.display = '';
        }
    }
});

const categoryMap = {
    'صندوق ورودی': 'Inbox',
    'زباله‌دان': 'Trash',
    'اسپم': 'Spam',
    'مهم': 'Important',
    'پیش‌نویس‌ها': 'Drafts',
    'ارسال‌شده': 'Sent',
    'نشان‌دار': 'Starred',
    'برنامه‌ریزی‌شده': 'Scheduled',

    // fallback for English Version
    'Inbox': 'Inbox',
    'Trash': 'Trash'
};

// Modifying the delete button handler to check if we're in trash view
document.getElementById("deleteBtn").addEventListener("click", function (e) {
    e.preventDefault();

    const activeCategory = document.querySelector('.inbox-message-list li a.active');
    const activeCategoryText = activeCategory
        ? activeCategory.textContent.trim().split('\n')[0].trim()
        : 'Inbox';

    const filterCategory =
        categoryMap[activeCategoryText] || activeCategoryText;

    const isTrashView = filterCategory === 'Trash';

    const emailCheckboxes = document.querySelectorAll('#mailbox-list input[type="checkbox"]');
    const mailboxWrapper = document.querySelector('.mailbox-wrapper');
    const isMailViewOpen = mailboxWrapper.classList.contains('show');
    const emailsToRemove = [];

    emailCheckboxes.forEach(checkbox => {
        if (!checkbox.checked) return;

        const mailboxItem = checkbox.closest('.mailbox-list-item');
        if (!mailboxItem) return;

        const emailId = mailboxItem.dataset.id;
        const emailIndex = emails.findIndex(email => email.id === emailId);

        if (emailIndex === -1) return;

        if (isTrashView) {
            emailsToRemove.push(emailIndex);
        } else {
            const email = emails[emailIndex];
            email.type = ['Trash']; // ✅ تمیزتر و امن‌تر
        }
    });

    if (isTrashView && emailsToRemove.length) {
        emailsToRemove.sort((a, b) => b - a);
        emailsToRemove.forEach(index => emails.splice(index, 1));
    }

    const visibleEmails = emails.filter(email =>
        email.type.includes(filterCategory)
    );

    renderEmails(visibleEmails);

    document.getElementById("allCheckMail").checked = false;
    document.getElementById("deleteBtn").classList.add("d-none");

    if (isMailViewOpen && visibleEmails.length) {
        const firstEmail = visibleEmails[0];
        document.getElementById("mailOverview").style.display = "";
        renderEmailContent(firstEmail);
        currentEmailId = firstEmail.id;
    } else {
        document.getElementById("mailOverview").style.display = "none";
        mailboxWrapper.classList.remove('show');
    }
});

// Modify the single email delete button to also completely delete from trash
document.getElementById('deleteButton').addEventListener('click', function () {
    if (!currentEmailId) return;

        const activeCategory = document.querySelector('.inbox-message-list li a.active');
        const activeCategoryText = activeCategory ? activeCategory.textContent.trim().split('\n')[0].trim() : 'Inbox';

        const filterCategory =
            categoryMap[activeCategoryText] || activeCategoryText;

                const isTrashView = filterCategory === 'Trash';

                const emailIndex = emails.findIndex(email => email.id === currentEmailId);

                if (emailIndex === -1) return;

                if (isTrashView) {
                    // ✅ permanently delete
                    emails.splice(emailIndex, 1);
                } else {
                    // ✅ move to trash (cleaner + safer)
                    emails[emailIndex].type = ['Trash'];
                }
                const visibleEmails = emails.filter(email =>
                    email.type.includes(filterCategory)
                );

            renderEmails(visibleEmails);
            
            const mailOverview = document.getElementById("mailOverview");
            mailOverview.style.display = "none";
            document.querySelector('.mailbox-wrapper').classList.remove('show');
            currentEmailId = null;

            if (window.innerWidth < 1024) {
                const mailboxList = document.querySelector('.mailbox-list');
                const mailboxCard = mailboxList?.closest('.card.flex-grow-1');
                if (mailboxCard) {
                    mailboxCard.style.display = 'block';
        }
    }
});

const sidebarMenuItems = document.querySelectorAll('.inbox-message-list li a');

sidebarMenuItems.forEach(item => {
    item.addEventListener('click', function (e) {
        e.preventDefault();

        sidebarMenuItems.forEach(menuItem => {
            menuItem.classList.remove('active');
        });
        this.classList.add('active');

        // متن خام دسته (فارسی یا انگلیسی)
        const rawCategoryText = this.textContent.trim().split('\n')[0].trim();

        // نرمال‌سازی به کلید انگلیسی دیتا
        const categoryText = categoryMap[rawCategoryText] || rawCategoryText;

        let filteredEmails;

        switch (categoryText) {
            case 'Inbox':
                filteredEmails = emails.filter(email => email.type.includes('Inbox'));
                break;
            case 'Starred':
                filteredEmails = emails.filter(email => email.type.includes('Starred'));
                break;
            case 'Sent':
                filteredEmails = emails.filter(email => email.type.includes('Sent'));
                break;
            case 'Drafts':
                filteredEmails = emails.filter(email => email.type.includes('Drafts'));
                break;
            case 'Spam':
                filteredEmails = emails.filter(email => email.type.includes('spam'));
                break;
            case 'Trash':
                filteredEmails = emails.filter(email => email.type.includes('Trash'));
                break;
            case 'Important':
                filteredEmails = emails.filter(email => email.type.includes('Important'));
                break;
            case 'Scheduled':
                filteredEmails = emails.filter(email => email.type.includes('Scheduled'));
                break;
            default:
                filteredEmails = emails;
        }

        renderEmails(filteredEmails);
        document.getElementById('allCheckMail').checked = false;
        document.getElementById('deleteBtn').classList.add('d-none');

        const mailOverview = document.getElementById('mailOverview');
        if (mailOverview.style.display !== 'none') {
            mailOverview.style.display = 'none';
            document.querySelector('.mailbox-wrapper').classList.remove('show');
        }
    });
});

const mailboxSidebarToggle = document.getElementById('mailboxSidebarToggle');
const mailboxWrapper = document.querySelector('.mailbox-left');

function createBackdrop() {
    let backdrop = document.querySelector('.offcanvas-backdrop');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.className = 'offcanvas-backdrop';
        document.body.appendChild(backdrop);
    }
    return backdrop;
}

mailboxSidebarToggle.addEventListener('click', function () {
    if (mailboxWrapper.style.display === 'block') {
        mailboxWrapper.style.display = '';

        const backdrop = document.querySelector('.offcanvas-backdrop');
        if (backdrop) {
            backdrop.style.display = 'none';
        }
    } else {
        mailboxWrapper.style.display = 'block';

        const backdrop = createBackdrop();
        backdrop.style.display = 'block';

        backdrop.addEventListener('click', function () {
            mailboxWrapper.style.display = '';
            backdrop.style.display = 'none';
        });
    }
});

document.addEventListener('click', function (e) {
    const backdrop = document.querySelector('.offcanvas-backdrop');
    if (e.target === backdrop) {
        mailboxWrapper.style.display = '';
        backdrop.style.display = 'none';
    }
});

renderEmails();