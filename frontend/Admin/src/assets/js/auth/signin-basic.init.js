document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const emailInput = document.getElementById('emailInput');
    const passwordInput = document.getElementById('passwordInput');
    const successAlert = document.querySelector('.alert-success');
    const errorAlert = document.querySelector('.alert-danger');

    const eyeIconContainer = document.getElementById('passwordShowIcon');
    eyeIconContainer.addEventListener('click', function () {
        const eyeOffIcon = eyeIconContainer.querySelector('[data-lucide="eye-off"]');
        const eyeIcon = eyeIconContainer.querySelector('[data-lucide="eye"]');
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            eyeOffIcon.classList.add('d-none');
            eyeIcon.classList.remove('d-none');
        } else {
            passwordInput.type = 'password';
            eyeOffIcon.classList.remove('d-none');
            eyeIcon.classList.add('d-none');
        }
    });

    // Form submission
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if (!validateEmail(email)) {
            showErrorAlert('لطفا یک ایمیل معتبر وارد کنید.');
            return;
        }

        if (!validatePassword(password)) {
            showErrorAlert('طول پسورد باید حداقل 8 کرکتر باشد.');
            return;
        }

        showSuccessAlert('شما با موفقیت وارد شدید! در حال هدایت ...');
        setTimeout(() => {
            window.location.href = 'index.html'; // Redirect to index.html
        }, 2000);
    });

    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    function validatePassword(password) {
        return password.length >= 8;
    }

    function showSuccessAlert(message) {
        successAlert.querySelector('span').textContent = message;
        successAlert.classList.remove('d-none');
        errorAlert.classList.add('d-none');
    }

    function showErrorAlert(message) {
        errorAlert.querySelector('span').textContent = message;
        errorAlert.classList.remove('d-none');
        successAlert.classList.add('d-none');
    }
});