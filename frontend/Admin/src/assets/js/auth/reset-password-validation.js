document.addEventListener('DOMContentLoaded', function () {
    //DOM elements
    const form = document.querySelector('form');
    const passwordInput = document.getElementById('passwordInput');
    const confirmPasswordInput = document.getElementById('confirmPasswordInput');
    const successAlert = document.querySelector('.alert-success');
    const errorAlert = document.querySelector('.alert-danger');

    function togglePasswordVisibility(passwordField, eyeOffIcon, eyeIcon) {
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

    document.querySelectorAll('.password-show-icon').forEach((iconContainer) => {
        iconContainer.addEventListener('click', function () {
            const passwordField = iconContainer.closest('.position-relative').querySelector('input[type="password"], input[type="text"]');
            const eyeOffIcon = iconContainer.querySelector('[data-lucide="eye-off"]');
            const eyeIcon = iconContainer.querySelector('[data-lucide="eye"]');

            togglePasswordVisibility(passwordField, eyeOffIcon, eyeIcon);
        });
    });

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        successAlert.classList.add('d-none');
        errorAlert.classList.add('d-none');

        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();

        if (!password || !confirmPassword) {
            showErrorAlert('لطفا تمام فیلدها را پر کنید.');
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

        showSuccessAlert('رمز عبور با موفقیت تنظیم شد!');
        setTimeout(() => {
            window.location.href = 'auth-successful-password-basic.html';
        }, 2000);
    });

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