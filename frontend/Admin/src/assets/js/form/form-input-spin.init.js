class InputSpinner {
    constructor(container) {
        this.container = container;
        this.input = container.querySelector('.input-spin');
        this.decrementBtn = container.querySelector('.input-spin-minus');
        this.incrementBtn = container.querySelector('.input-spin-plus');

        this.init();
    }

    init() {
        this.decrementBtn.addEventListener('click', () => this.decrement());
        this.incrementBtn.addEventListener('click', () => this.increment());
    }

    decrement() {
        let currentValue = parseInt(this.input.value, 10);
        if (currentValue > 0) {
            this.input.value = currentValue - 1;
        }
    }

    increment() {
        let currentValue = parseInt(this.input.value, 10);
        this.input.value = currentValue + 1;
    }
}

// Initialize spinners for all .input-spin-group elements
document.querySelectorAll('.input-spin-group').forEach(container => {
    new InputSpinner(container);
});