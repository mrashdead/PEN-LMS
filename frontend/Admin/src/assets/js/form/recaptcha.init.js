// Form validation and reCAPTCHA check
document.getElementById('contactForm').addEventListener('submit', function (event) {
    event.preventDefault();

    const recaptchaResponse = grecaptcha.getResponse();
    if (recaptchaResponse.length === 0) {
        document.getElementById('recaptchaError').style.display = 'block';
        return;
    } else {
        document.getElementById('recaptchaError').style.display = 'none';
    }

    if (this.checkValidity()) {
        alert('فرم با موفقیت ارسال شد!');
        this.reset();
        grecaptcha.reset(); // Reset reCAPTCHA
    } else {
        event.stopPropagation();
    }

    this.classList.add('was-validated');
});