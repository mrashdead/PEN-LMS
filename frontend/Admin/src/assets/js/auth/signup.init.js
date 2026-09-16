document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const firstNameInput = document.getElementById('firstNameInput');
    const lastNameInput = document.getElementById('lastNameInput');
    const usernameInput = document.getElementById('usernameInput');
    const emailInput = document.getElementById('emailInput');
    const passwordInput = document.getElementById('passwordInput');
    const confirmPasswordInput = document.getElementById('confirmPasswordInput');
    const rememberMeCheckbox = document.getElementById('rememberMe');
    const successAlert = document.querySelector('.alert-success');
    const errorAlert = document.querySelector('.alert-danger');

    document.body.addEventListener('click', function (event) {
        if (event.target.closest('#passwordShowIcon')) {
            const iconContainer = event.target.closest('#passwordShowIcon');
            const passwordField = iconContainer.closest('.password').querySelector('input[type="password"], input[type="text"]');
            const eyeOffIcon = iconContainer.querySelector('[data-lucide="eye-off"]');
            const eyeIcon = iconContainer.querySelector('[data-lucide="eye"]');

            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                eyeOffIcon.classList.add('d-none');
                eyeIcon.classList.remove('d-none');
            } else {
                passwordField.type = 'password';
                eyeOffIcon.classList.remove('d-none');
                eyeIcon.classList.add('d-none');
            }
        }
    });

    // Form submission
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        successAlert.classList.add('d-none');
        errorAlert.classList.add('d-none');

        const firstName = firstNameInput.value.trim();
        const lastName = lastNameInput.value.trim();
        const username = usernameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();

        // Validate form
        if (!firstName || !username || !email || !password || !confirmPassword) {
            showErrorAlert('لطفا تمام فیلدهای ضروری را پر کنید.');
            return;
        }

        if (!validateEmail(email)) {
            showErrorAlert('لطفا یک آدرس ایمیل معتبر وارد کنید.');
            return;
        }

        if (password !== confirmPassword) {
            showErrorAlert('رمزهای عبور مطابقت ندارند.');
            return;
        }

        if (password.length < 8) {
            showErrorAlert('رمز عبور باید حداقل 8 کاراکتر داشته باشد.');
            return;
        }

        if (!rememberMeCheckbox.checked) {
            showErrorAlert('شما باید با شرایط و ضوابط موافقت کنید.');
            return;
        }

        showSuccessAlert('شما با موفقیت ثبت نام کردید!');
        setTimeout(() => {
            window.location.href = 'index.html'; // Redirect to index.html
        }, 2000);
    });

    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    function showSuccessAlert(message) {
        successAlert.querySelector('span').textContent = message;
        successAlert.classList.remove('d-none');
        successAlert.classList.add('show');

        setTimeout(() => {
            successAlert.classList.remove('show');
            successAlert.classList.add('d-none');
        }, 5000);
    }

    function showErrorAlert(message) {
        errorAlert.querySelector('span').textContent = message;
        errorAlert.classList.remove('d-none');
        errorAlert.classList.add('show');

        setTimeout(() => {
            errorAlert.classList.remove('show');
            errorAlert.classList.add('d-none');
        }, 5000);
    }
});