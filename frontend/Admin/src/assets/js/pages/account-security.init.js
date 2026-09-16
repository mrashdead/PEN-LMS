
document.addEventListener('DOMContentLoaded', function () {
    const inputsFirstModal = document.querySelectorAll('#googleAuthenticationModal .pattern-input');
    const verifyButton = document.getElementById('verifyButton');

    function moveToNextInput(currentInput, nextInput) {
        if (currentInput.value.length === 1 && nextInput) {
            nextInput.focus();
        }
    }

    function moveToPreviousInput(currentInput, previousInput) {
        if (currentInput.value.length === 0 && previousInput) {
            previousInput.focus();
        }
    }

    inputsFirstModal.forEach((input, index) => {
        input.addEventListener('input', function () {
            if (this.value.match(/\d/)) {
                moveToNextInput(this, inputsFirstModal[index + 1]);
            } else {
                this.value = '';
            }
        });

        input.addEventListener('keydown', function (e) {
            if (e.key === 'Backspace' && this.value.length === 0) {
                moveToPreviousInput(this, inputsFirstModal[index - 1]);
            }
        });
    });

    // Verify OTP on button
    verifyButton.addEventListener('click', function () {
        let otp = '';
        let isValid = true;

        inputsFirstModal.forEach(input => {
            if (input.value.match(/\d/)) {
                otp += input.value;
            } else {
                isValid = false;
            }
        });

        if (isValid && otp.length === 6) {
            // Close the first modal
            const firstModal = window.bootstrap.Modal.getInstance(document.getElementById('googleAuthenticationModal'));
            firstModal.hide();

            // Open the second modal
            const secondModal = new window.bootstrap.Modal(document.getElementById('googleAuthenticationModal2'));
            secondModal.show();
        } else {
            alert('لطفا تمام فیلدها را با اعداد معتبر پر کنید.');
        }
    });

    window.validateInput = function (input, event) {
        if (!input.value.match(/\d/)) {
            input.value = '';
        } else {
            const nextInput = input.nextElementSibling;
            if (nextInput) {
                nextInput.focus();
            }
        }
    };
});

//reset form 
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('passwordResetForm');
    const updatePasswordAlert = document.getElementById('updatePasswordAlert');

    // Toggle password
    const togglePassword = (icon) => {
        const input = icon.closest('.password').querySelector('input');
        const eyeOffIcon = icon.closest('.password').querySelector('[data-lucide="eye-off"]');
        const eyeIcon = icon.closest('.password').querySelector('[data-lucide="eye"]');

        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);

        eyeOffIcon.classList.toggle('d-none', type === 'text');
        eyeOffIcon.classList.toggle('d-block', type === 'password');
        eyeIcon.classList.toggle('d-none', type === 'password');
        eyeIcon.classList.toggle('d-block', type === 'text');
    };

    document.querySelectorAll('#button-addon1, #button-addon2, #button-addon3').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.closest('.password').querySelector('input');
            const eyeOffIcon = toggle.querySelector('[data-lucide="eye-off"]');
            const eyeIcon = toggle.querySelector('[data-lucide="eye"]');

            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);

            eyeOffIcon.classList.toggle('d-none', type === 'text');
            eyeIcon.classList.toggle('d-none', type === 'password');
        });
    });

    // Form validation and submission
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        let isValid = true;

        // Helper function to show errors
        const showError = (input, errorElement, message) => {
            input.classList.add('is-invalid');
            errorElement.textContent = message;
            errorElement.classList.add('d-block');
            isValid = false;
        };

        // Helper function to clear errors
        const clearError = (input, errorElement) => {
            input.classList.remove('is-invalid');
            errorElement.textContent = '';
            errorElement.classList.remove('d-block');
        };

        // Validate current password
        const currentPasswordInput = document.getElementById('currentPasswordInput');
        const currentPasswordError = document.getElementById('currentPasswordError');
        if (currentPasswordInput.value.trim() === '')
            showError(currentPasswordInput, currentPasswordError, 'رمز عبور فعلی الزامی است.');
        else
            clearError(currentPasswordInput, currentPasswordError);

        // Validate new password
        const newPasswordInput = document.getElementById('newPasswordInput');
        const newPasswordError = document.getElementById('newPasswordError');
        if (newPasswordInput.value.trim() === '')
            showError(newPasswordInput, newPasswordError, 'رمز عبور جدید الزامی است.');
        else if (newPasswordInput.value.length < 8)
            showError(newPasswordInput, newPasswordError, 'رمز عبور جدید باید حداقل ۸ کاراکتر داشته باشد.');
        else
            clearError(newPasswordInput, newPasswordError);

        // Validate confirm password
        const confirmPasswordInput = document.getElementById('confirmPasswordInput');
        const confirmPasswordError = document.getElementById('confirmPasswordError');
        if (confirmPasswordInput.value.trim() === '')
            showError(confirmPasswordInput, confirmPasswordError, 'لطفا رمز عبور جدید خود را تأیید کنید.');
        else if (confirmPasswordInput.value !== newPasswordInput.value)
            showError(confirmPasswordInput, confirmPasswordError, 'رمزهای عبور مطابقت ندارند.');
        else
            clearError(confirmPasswordInput, confirmPasswordError);

        if (isValid) {
            form.reset();

            // Show success alert
            updatePasswordAlert.innerHTML = `
                <div class="alert alert-success alert-dismissible mb-5 fade show" role="alert">
                    <span>رمز عبور با موفقیت به‌روزرسانی شد!</span>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;

            setTimeout(() => {
                const alert = updatePasswordAlert.querySelector('.alert');
                if (alert) alert.remove();
            }, 5000);
        }
    });
});

