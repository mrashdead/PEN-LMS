document.addEventListener('DOMContentLoaded', () => {
    // Cache DOM elements
    const steps = {
        step1: document.getElementById('step1'),
        step2: document.getElementById('step2'),
        step3: document.getElementById('step3'),
        step4: document.getElementById('step4'),
    };

    const progressBars = {
        progressBar1: document.getElementById('progress-bar'),
        progressBar2: document.getElementById('progress-bar2'),
        progressBar3: document.getElementById('progress-bar3'),
    };

    const buttons = {
        nextStep1: document.getElementById('nextStep1'),
        prevStep1: document.getElementById('prevStep1'),
        nextStep2: document.getElementById('nextStep2'),
        prevStep2: document.getElementById('prevStep2'),
        completeStep: document.getElementById('completeStep'),
        backHome: document.getElementById('backHome'),
        passwordToggle: document.getElementById('passwordToggle'),
    };

    const inputs = {
        firstName: document.getElementById('firstName'),
        email: document.getElementById('email'),
        password: document.getElementById('passwordInput'),
        profession: document.getElementById('profession'),
        gender: document.getElementsByName('gender'),
        fileInput: document.getElementById('fileInput'),
    };

    const errors = {
        firstNameError: document.getElementById('firstNameError'),
        emailError: document.getElementById('emailError'),
        genderError: document.getElementById('genderError'),
        professionError: document.getElementById('professionError'),
        imageError: document.getElementById('imageError'),
        passwordError: document.getElementById('passwordError'),
    };

    const profileImage = document.getElementById('profile-image');

    // Navigation functions
    const navigate = (fromStep, toStep, progressUpdate) => {
        fromStep.classList.add('d-none');
        toStep.classList.remove('d-none');
        if (progressUpdate) progressUpdate();
    };

    const updateProgress = (progressBar, width) => {
        if(progressBar)
            progressBar.style.width = width;
    };

    // Validation functions
    const validateStep1 = () => {
        let valid = true;
        if (inputs.firstName.value.trim() === '') {
            errors.firstNameError.textContent = 'نام و نام خانوادگی الزامی است.';
            valid = false;
        } else {
            errors.firstNameError.textContent = '';
        }

        if (inputs.email.value.trim() === '') {
            errors.emailError.textContent = 'ایمیل الزامی است.';
            valid = false;
        } else {
            errors.emailError.textContent = '';
        }

        return valid;
    };

    const validateStep2 = () => {
        const inputPassword = inputs.password.value.trim();
        const passwordErrors = {
            lowerCaseLetter: document.getElementById('lowerCaseLetterError'),
            upperCaseLetter: document.getElementById('upperCaseLetterError'),
            number: document.getElementById('numberError'),
            specialCharacter: document.getElementById('specialCharacterError'),
            length: document.getElementById('lengthError'),
        };

        // Reset error messages and styles
        errors.passwordError.textContent = '';
        Object.values(passwordErrors).forEach((errorElement) => {
            errorElement.classList.remove('text-danger', 'text-success');
        });

        // Validation rules
        const rules = [
            {
                condition: inputPassword === '',
                message: 'رمز عبور الزامی است.',
            },
            {
                condition: !/[a-z]/.test(inputPassword),
                message: 'رمز عبور باید حداقل شامل یک حرف کوچک باشد.',
                errorElement: passwordErrors.lowerCaseLetter,
            },
            {
                condition: !/[A-Z]/.test(inputPassword),
                message: 'رمز عبور باید حداقل شامل یک حرف بزرگ باشد.',
                errorElement: passwordErrors.upperCaseLetter,
            },
            {
                condition: !/[0-9]/.test(inputPassword),
                message: 'رمز عبور باید حداقل شامل یک عدد باشد.',
                errorElement: passwordErrors.number,
            },
            {
                condition: !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(inputPassword),
                message: 'رمز عبور باید حداقل شامل یک کاراکتر خاص باشد.',
                errorElement: passwordErrors.specialCharacter,
            },
            {
                condition: inputPassword.length < 8,
                message: 'رمز عبور باید حداقل 8 کاراکتر داشته باشد.',
                errorElement: passwordErrors.length,
            },
        ];

        // Check each rule
        let isPass = true;
        for (const rule of rules) {
            if (rule.condition) {
                errors.passwordError.textContent = rule.message;
                if (rule.errorElement) {
                    isPass = false;
                    rule.errorElement.classList.add('text-danger');
                }
            } else if (rule.errorElement) {
                rule.errorElement.classList.add('text-success');
            }
        }

        // If all rules pass
        return isPass;
    };

    const validateStep3 = () => {
        let valid = true;
        const genderSelected = Array.from(inputs.gender).some((gender) => gender.checked);
        if (!genderSelected) {
            errors.genderError.textContent = 'لطفا جنسیت خود را انتخاب کنید.';
            valid = false;
        } else {
            errors.genderError.textContent = '';
        }

        if (inputs.profession.value.trim() === '') {
            errors.professionError.textContent = 'حرفه الزامی است.';
            valid = false;
        } else {
            errors.professionError.textContent = '';
        }

        return valid;
    };

    // Event listeners
    buttons.nextStep1.addEventListener('click', () => {
        if (validateStep1()) {
            navigate(steps.step1, steps.step2, () => {
                updateProgress(progressBars.progressBar1, '66%');
                updateProgress(progressBars.progressBar2, '66%');
            });
        }
    });

    buttons.nextStep2.addEventListener('click', () => {
        if (validateStep2()) {
            navigate(steps.step2, steps.step3, () => {
                updateProgress(progressBars.progressBar2, '100%');
                updateProgress(progressBars.progressBar3, '100%');
            });
        }
    });

    buttons.prevStep1.addEventListener('click', () => {
        navigate(steps.step2, steps.step1, () => {
            updateProgress(progressBars.progressBar1, '33%');
            updateProgress(progressBars.progressBar2, '66%');
        });
    });

    buttons.prevStep2.addEventListener('click', () => {
        navigate(steps.step3, steps.step2, () => {
            updateProgress(progressBars.progressBar2, '66%');
            updateProgress(progressBars.progressBar3, '100%');
        });
    });

    buttons.completeStep.addEventListener('click', () => {
        if (validateStep3()) {
            navigate(steps.step3, steps.step4);
        }
    });

    buttons.backHome.addEventListener('click', () => {
        window.location.href = '/index.html'; // Navigate to home page
    });

    passwordToggle.addEventListener('click', () => {
        const passwordInput = inputs.password;
        passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordToggle.firstElementChild.classList.toggle('d-none');
        passwordToggle.lastElementChild.classList.toggle('d-none');
    });

    // File upload validation
    inputs.fileInput.addEventListener('change', () => {
        const file = inputs.fileInput.files[0];
        errors.imageError.textContent = '';

        if (!file) {
            errors.imageError.textContent = 'لطفا یک تصویر پروفایل بارگذاری کنید.';
            return;
        }

        const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            errors.imageError.textContent = 'فقط فایل‌های JPEG، PNG و GIF مجاز هستند.';
            return;
        }

        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            errors.imageError.textContent = 'فایل خیلی بزرگ است. حداکثر حجم مجاز 5Mb است.';
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            profileImage.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
});