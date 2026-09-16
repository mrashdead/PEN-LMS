class ChatBot {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.chatBox = this.container.querySelector('.chat-box');
        this.userInput = this.container.querySelector('.user-input');
        this.sendButton = this.container.querySelector('.send-button');

        // Initialize the chatbot
        this.init();
    }

    init() {
        // Display the default bot message when the page loads
        this.appendMessage("سلام! حالت چطوره؟", 'bot');
        this.appendMessage("من خوبم، ممنون ", 'user');
        this.appendMessage("سلام به شما! چطور می‌تونم کمک کنم؟", 'bot');
        this.appendMessage("دومیکس چیه؟", 'bot');
        this.appendMessage("آیا فایل فیگما هم شامل میشه؟", 'bot');
        this.appendMessage("آیا با Next 15 و TS و JS همراه هستش؟", 'bot');
        this.appendMessage("آیا نسخه Next شامل حال App Router هم میشه؟", 'bot');

        // Add event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') this.sendMessage();
        });

        // Debounce input events (optional, if needed)
        this.userInput.addEventListener('input', this.debounce(() => {
            console.log('User is typing...');
        }, 300));
    }

    sendMessage() {
        const userInput = this.userInput.value.trim(); // Trim input
        if (userInput === "") return; // Do not send empty messages

        // Append user message to chat box
        this.appendMessage(userInput, 'user');

        // Simulate bot response
        setTimeout(() => {
            const botResponse = this.getBotResponse(userInput);
            this.appendMessage(botResponse, 'bot');
        }, 1000);

        // Clear input field
        this.userInput.value = '';
    }

    appendMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('d-flex', 'align-items-end');

        if (sender === 'user') {
            messageElement.classList.add('justify-content-end');
            messageElement.innerHTML = `
                <div class="px-3 py-2 bg-primary text-white rounded-top-2 rounded-start-2 me-2">
                    <span class="fw-medium fs-sm">${message}</span>
                </div>
                <div class="flex-shrink-0">
                    <img src="assets/images/avatar/user-2.png" alt="" class="rounded-circle img-fluid size-6" loading="lazy">
                </div>
            `;
        } else {
            messageElement.innerHTML = `
                <div class="flex-shrink-0">
                    <img src="assets/images/others/bot.png" alt="" class="rounded-circle img-fluid size-6" loading="lazy">
                </div>
                <div class="px-3 py-2 bg-light-subtle rounded-top-2 rounded-end-2 ms-2">
                    <span class="fw-medium fs-sm">${message}</span>
                </div>
            `;
        }

        // Append message to chat box
        this.chatBox.appendChild(messageElement);
        this.scrollToBottom();
    }

    scrollToBottom() {
        if (this.chatBox) {
            if (this.chatBox.closest('.simplebar-content-wrapper'))
                this.chatBox.closest('.simplebar-content-wrapper').scrollTop = this.chatBox.scrollHeight; // Smooth scroll
        }
    }

    getBotResponse(userInput) {
        const responses = {
            "hello": "Hello! How can I assist you today?",
            "سلام": "سلام به شما! چطور می‌تونم کمک کنم؟",
            "howareyou": "I'm just a bot, but I'm functioning perfectly! How can I help you?",
            "whatisyourname": "I'm Domiex ChatBot, your virtual assistant.",
            "whatcanyoudo": "I can help answer your questions, provide information, and assist with tasks. Just ask!",
            "ممنون": "خواهش می‌کنم! روز خوبی داشته باشید.",
            "متشکرم": "خواهش می‌کنم! هر چیز دیگری نیاز داشتید به من خبر بده.",
            "یه جوک بگو": "چرا دانشمندان به اتم‌ها اعتماد ندارند؟ چون آنها همه چیز را تشکیل می‌دهند!",
            "چه کسی تو رو ساخته": "من توسط تیمی از توسعه‌دهندگان برای کمک به شما ایجاد شده‌ام.",
            "دومیکس چیه؟": "دومیکس پلتفرمی است که برای ارائه راه‌حل‌ها و خدمات نوآورانه طراحی شده است.",
            "default": "مطمئن نیستم چطور به این سوال پاسخ بدهم. می‌توانی سوال دیگری بپرسی؟",
            "آیا فایل فیگما هم شامل میشه": "بله، فایل فیگما هم شامل فایل‌های پروژه می‌شود.",
            "آیا فایل فیگما هم شامل میشه؟": "بله، فایل فیگما هم شامل فایل‌های پروژه می‌شود.",
            "آیا نسخه Next.js هم با JS در دسترس هست هم با TS": "بله، با Next 15 و با TypeScript و JavaScript نیز ساخته شده است.",
            "آیا نسخه Next.js هم با JS در دسترس هست هم با TS؟": "بله، با Next 15 و با TypeScript و JavaScript نیز ساخته شده است.",
            "آیا Next.js از App Router پشتیبانی میکنه": "بله، نسخه Next.js از App Router پشتیبانی می‌کند.",
            "آیا Next.js از App Router پشتیبانی میکنه؟": "بله، نسخه Next.js از App Router پشتیبانی می‌کند.",
            "آیا نسخه Next شامل حال App Router هم میشه": "بله، نسخه Next.js از App Router پشتیبانی می‌کند.",
            "آیا نسخه Next شامل حال App Router هم میشه؟": "بله، نسخه Next.js از App Router پشتیبانی می‌کند.",
        };

        // Normalized spaces from the user input for Persian language
        const normalizedInput = userInput.trim().replace(/\s+/g, ' ');
        return responses[normalizedInput] || responses['default'];
    }

    // Debounce function to limit the rate of function execution
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }
}

// Initialize multiple chatbots
document.addEventListener('DOMContentLoaded', function () {
    const chatbot1 = new ChatBot('chatbot1');
    const chatbot2 = new ChatBot('chatbot2');
    const chatbot3 = new ChatBot('chatbot3');
    const chatbot4 = new ChatBot('chatbot4');
});