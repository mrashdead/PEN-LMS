document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('.pattern-input');
    const verifyButton = document.getElementById('verifyButton');
    const successAlert = document.getElementById('successAlert');
    const errorAlert = document.getElementById('errorAlert');

    // Restrict input to numeric values only
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            // Remove non-numeric characters
            input.value = input.value.replace(/\D/g, '');

            // Auto-focus the next input if a digit is entered
            if (input.value.length === 1 && input.nextElementSibling) {
                input.nextElementSibling.focus();
            }
        });

        // Handle backspace to move focus to the previous input
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && input.value.length === 0 && input.previousElementSibling) {
                input.previousElementSibling.focus();
            }
        });
    });

    // Validate OTP
    verifyButton.addEventListener('click', () => {
        let otp = '';
        inputs.forEach(input => {
            otp += input.value;
        });

        if (otp.length === 6) {
            // Valid OTP
            successAlert.classList.remove('d-none'); // Show success alert
            errorAlert.classList.add('d-none'); // Hide error alert

            // Redirect after 2 seconds
            setTimeout(() => {
                window.location.href = 'auth-reset-password-basic.html';
            }, 2000);
        } else {
            // Invalid OTP
            errorAlert.classList.remove('d-none'); // Show error alert
            successAlert.classList.add('d-none'); // Hide success alert
        }
    });
});