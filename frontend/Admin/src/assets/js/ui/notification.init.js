
class ToastManager {
    constructor() {
        this.toasts = new Map(); // Store toast instances
        this.init(); // Initialize the manager
    }

    // Initialize the ToastManager
    init() {
        // Find all buttons with the `data-toast-toggle` attribute
        const toastButtons = document.querySelectorAll('[data-toast-toggle]');

        // Loop through each button and set up the toast
        toastButtons.forEach(button => {
            const toastId = button.getAttribute('data-toast-toggle');
            const toastElement = document.getElementById(toastId);

            if (toastElement) {
                const toast = new window.bootstrap.Toast(toastElement); // Create Bootstrap Toast instance
                this.toasts.set(toastId, toast); // Store the toast instance in the Map

                // Add click event to the button
                button.addEventListener('click', () => {
                    this.showToast(toastId);
                });
            } else {
                console.error(`Toast element not found for ID: ${toastId}`);
            }
        });
    }

    // Show a specific toast by ID
    showToast(toastId) {
        const toast = this.toasts.get(toastId);
        if (toast) {
            toast.show();
        } else {
            console.error(`Toast not found for ID: ${toastId}`);
        }
    }
}

// Initialize the ToastManager
const toastManager = new ToastManager();