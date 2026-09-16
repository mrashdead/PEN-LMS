import Swal from 'sweetalert2/dist/sweetalert2.js'

//basic Alerts
document.getElementById('basicAlerts').addEventListener('click', function () {
    Swal.fire({
        title: 'سلام!',
        text: 'این یک مثال از SweetAlert2 است.',
        icon: 'success',
        confirmButtonText: 'عالیه',
        customClass: {
            confirmButton: 'btn btn-primary',
        }
    });
});

// toastButton
const ToastAlert = Swal.mixin({
    toast: true,
    position: "top-end",
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
        toast.onmouseenter = Swal.stopTimer;
        toast.onmouseleave = Swal.resumeTimer;
    }
});

document.getElementById('toastAlert').addEventListener('click', function () {
    ToastAlert.fire({
        icon: "success",
        title: "با موفقیت وارد سیستم شدید",
    });
});

// Success Icon
document.getElementById('successButton').addEventListener('click', function () {
    Swal.fire({
        icon: 'success',
        title: 'موفق بود!',
        text: 'عملیات شما با موفقیت انجام شد.',
        customClass: {
            confirmButton: 'btn btn-primary',
        }
    });
});

// Error Icon
document.getElementById('errorButton').addEventListener('click', function () {
    Swal.fire({
        icon: 'error',
        title: 'خطا!',
        text: 'مشکلی پیش آمد.',
        customClass: {
            confirmButton: 'btn btn-primary',
        }
    });
});

// Warning Icon
document.getElementById('warningButton').addEventListener('click', function () {
    Swal.fire({
        icon: 'warning',
        title: 'هشدار!',
        text: 'این اقدام قابل لغو نیست.',
        customClass: {
            confirmButton: 'btn btn-primary',
        }
    });
});

// Info Icon
document.getElementById('infoButton').addEventListener('click', function () {
    Swal.fire({
        icon: 'info',
        title: 'جهت اطلاع!',
        text: 'در اینجا اطلاعاتی برای شما آورده شده است.',
        customClass: {
            confirmButton: 'btn btn-primary',
        }
    });
});

// Question Icon
document.getElementById('questionButton').addEventListener('click', function () {
    Swal.fire({
        icon: 'question',
        title: 'سؤال؟',
        text: 'مطمئنی که می‌خوای ادامه بدی؟',
        customClass: {
            confirmButton: 'btn btn-primary',
        }
    });
});

// Text Input
document.getElementById('textInputButton').addEventListener('click', function () {
    Swal.fire({
        title: 'نام خود را وارد کنید',
        input: 'text',
        inputPlaceholder: 'علی کریمی',
        showCancelButton: true,
        confirmButtonText: 'ارسال',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-danger',
        },
        preConfirm: (input) => {
            if (!input) {
                Swal.showValidationMessage('لطفا نام خود را وارد کنید');
            }
            return input;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'موفق!',
                text: `شما وارد کردید: ${result.value}`,
                icon: 'success',
                confirmButtonText: 'باشه',
                customClass: {
                    confirmButton: 'btn btn-success',
                }
            }).then(() => {
                console.log('Second modal closed');
            });
        }
    });
});

// Email Input
document.getElementById('emailInputButton').addEventListener('click', function () {
    Swal.fire({
        title: 'ایمیل خود را وارد کنید',
        input: 'email',
        inputPlaceholder: 'example@domiex.com',
        showCancelButton: true,
        confirmButtonText: 'ارسال',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-danger',
        },
        preConfirm: (input) => {
            if (!input) {
                Swal.showValidationMessage('لطفا ایمیل خود را وارد کنید');
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input)) {
                Swal.showValidationMessage('لطفا یک آدرس ایمیل معتبر وارد کنید');
            }
            return input;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'موفق!',
                text: `شما وارد کردید: ${result.value}`,
                icon: 'success',
                confirmButtonText: 'باشه',
                customClass: {
                    confirmButton: 'btn btn-success',
                }
            }).then(() => {
                console.log('Second modal closed');
            });
        }
    });
});

// Password Input
document.getElementById('passwordInputButton').addEventListener('click', function () {
    Swal.fire({
        title: 'رمز عبور خود را وارد کنید',
        input: 'password',
        inputPlaceholder: 'رمز عبور',
        showCancelButton: true,
        confirmButtonText: 'ارسال',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-danger',
        },
        preConfirm: (input) => {
            if (!input) {
                Swal.showValidationMessage('لطفا رمز عبور خود را وارد کنید');
            }
            return input;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'موفق!',
                text: 'شما یک رمز عبور وارد کردید.',
                icon: 'success',
                confirmButtonText: 'باشه',
                customClass: {
                    confirmButton: 'btn btn-success',
                }
            });
        }
    });
});

// Number Input
document.getElementById('numberInputButton').addEventListener('click', function () {
    Swal.fire({
        title: 'سن خود را وارد کنید',
        input: 'number',
        inputPlaceholder: '18',
        showCancelButton: true,
        confirmButtonText: 'ارسال',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-danger',
        },
        preConfirm: (input) => {
            if (!input) {
                Swal.showValidationMessage('لطفا سن خود را وارد کنید');
            }
            return input;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'موفق!',
                text: `شما وارد کردید: ${result.value}`,
                icon: 'success',
                confirmButtonText: 'باشه',
                customClass: {
                    confirmButton: 'btn btn-success',
                }
            });
        }
    });
});

// Tel Input
document.getElementById('telInputButton').addEventListener('click', function () {
    Swal.fire({
        title: 'شماره تلفن خود را وارد کنید',
        input: 'tel',
        inputPlaceholder: '+1234567890',
        showCancelButton: true,
        confirmButtonText: 'ارسال',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-danger',
        },
        preConfirm: (input) => {
            if (!input) {
                Swal.showValidationMessage('لطفا شماره تلفن خود را وارد کنید');
            }
            return input;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'موفق!',
                text: `شما وارد کردید: ${result.value}`,
                icon: 'success',
                confirmButtonText: 'باشه',
                customClass: {
                    confirmButton: 'btn btn-success',
                }
            });
        }
    });
});

// Range Input
document.getElementById('rangeInputButton').addEventListener('click', function () {
    Swal.fire({
        title: 'یک مقدار انتخاب کنید',
        input: 'range',
        inputAttributes: {
            min: 0,
            max: 100,
            step: 1,
            class: 'form-range'
        },
        inputValue: 50,
        showCancelButton: true,
        confirmButtonText: 'ارسال',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-danger',
        },
        preConfirm: (input) => {
            return input;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'موفق!',
                text: `شما انتخاب کردید: ${result.value}`,
                icon: 'success',
                confirmButtonText: 'باشه',
                customClass: {
                    confirmButton: 'btn btn-success',
                }
            });
        }
    });
});

// Radio Input
document.getElementById('radioInputButton').addEventListener('click', function () {
    Swal.fire({
        title: 'یک گزینه را انتخاب کنید',
        html:
            '<div class="d-flex align-items-center justify-content-center gap-5 flex-wrap">' +
            '<div class="form-check">' +
            '<input class="form-check-input" type="radio" name="radioOption" id="radioOption1" value="option1">' +
            '<label class="form-check-label" for="radioOption1">گزینه 1</label>' +
            '</div>' +
            '<div class="form-check">' +
            '<input class="form-check-input" type="radio" name="radioOption" id="radioOption2" value="option2">' +
            '<label class="form-check-label" for="radioOption2">گزینه 2</label>' +
            '</div>' +
            '<div class="form-check">' +
            '<input class="form-check-input" type="radio" name="radioOption" id="radioOption3" value="option3">' +
            '<label class="form-check-label" for="radioOption3">گزینه 3</label>' +
            '</div>' +
            '</div>',
        showCancelButton: true,
        confirmButtonText: 'ارسال',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-danger',
        },
        preConfirm: () => {
            const selectedOption = document.querySelector('input[name="radioOption"]:checked');
            if (!selectedOption) {
                Swal.showValidationMessage('لطفا یک گزینه را انتخاب کنید');
            }
            return selectedOption ? selectedOption.value : null;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'ارسال شد!',
                text: `شما انتخاب کردید: ${result.value}`,
                icon: 'success',
                confirmButtonText: 'باشه',
                customClass: {
                    confirmButton: 'btn btn-success',
                }
            });
        }
    });
});