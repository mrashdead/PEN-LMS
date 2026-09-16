
function setError(id, message) {
    document.getElementById(id).textContent = message;
}

function clearErrors(ids) {
    ids.forEach(id => setError(id, ''));
}

// --- Card Form Validation ---
document.getElementById('cardPayBtn').addEventListener('click', function () {
    const name = document.getElementById('cardHolderNameInput').value.trim();
    const number = document.getElementById('debitCreditCardInput').value.replace(/\s/g, '');
    const expiry = document.getElementById('expiryDateMask').value.trim();
    const cvv = document.getElementById('cvvInput').value.trim();

    clearErrors(['cardHolderNameError', 'cardNumberError', 'expiryError', 'cvvError']);

    let valid = true;

    if (name === '') {
        setError('cardHolderNameError', 'نام دارنده کارت الزامی است.');
        valid = false;
    }

    if (!/^\d{16}$/.test(number)) {
        setError('cardNumberError', 'شماره کارت باید 16 رقمی باشد.');
        valid = false;
    }

    if (!/^\d{2}\/\d{2}$/.test(expiry)) {
        setError('expiryError', 'تاریخ انقضا باید به صورت ماه/سال باشد.');
        valid = false;
    }

    if (!/^\d{3}$/.test(cvv)) {
        setError('cvvError', 'CVV باید 3 رقمی باشد.');
        valid = false;
    }

    if (valid) {
        // Open modal manually
        const successModal = new window.bootstrap.Modal(document.getElementById('paySuccessModal'));
        successModal.show();
    }
});


// --- Bank Transfer Form Validation ---
document.getElementById('bankPayBtn').addEventListener('click', function () {
    const name = document.getElementById('bankHolderNameInput').value.trim();
    const account = document.getElementById('accountNumberInput').value.trim();
    const confirm = document.getElementById('confirmAccountNumber').value.trim();
    const ifsc = document.getElementById('ifscCodeInput').value.trim().toUpperCase();
    const bank = document.getElementById('bankNameInput').value.trim();

    clearErrors(['bankNameError', 'accountNumberError', 'confirmAccountError', 'ifscError', 'bankInputError']);

    let valid = true;

    if (name === '') {
        setError('bankNameError', 'نام صاحب حساب بانکی الزامی است.');
        valid = false;
    }

    if (!/^\d{9,18}$/.test(account)) {
        setError('accountNumberError', 'شماره حساب باید بین 9 تا 18 رقم باشد.');
        valid = false;
    }

    if (account !== confirm) {
        setError('confirmAccountError', 'شماره حساب‌ها مطابقت ندارند.');
        valid = false;
    }

    if (!/^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc)) {
        setError('ifscError', 'کد IFSC نامعتبر است.');
        valid = false;
    }

    if (bank === '') {
        setError('bankInputError', 'نام بانک الزامی است.');
        valid = false;
    }

    if (valid) {
        // Open modal manually
        const successModal = new window.bootstrap.Modal(document.getElementById('paySuccessModal'));
        successModal.show();
    }
});

// Auto formatting (optional)
document.getElementById('debitCreditCardInput').addEventListener('input', function (e) {
    const v = e.target.value.replace(/\D/g, '').slice(0, 16);
    e.target.value = v.replace(/(.{4})/g, '$1 ').trim();
});

document.getElementById('expiryDateMask').addEventListener('input', function (e) {
    const v = e.target.value.replace(/\D/g, '').slice(0, 4);
    e.target.value = v.length >= 3 ? v.slice(0, 2) + '/' + v.slice(2) : v;
});
