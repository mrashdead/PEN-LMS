document.addEventListener('DOMContentLoaded', function () {

    const wishlistTable = document.getElementById('wishlistTable');

    // Quantity increment/decrement functionality
    wishlistTable.addEventListener('click', function (e) {
        // Handle plus button
        if (e.target.closest('.input-spin-plus')) {
            const input = e.target.closest('.input-spin-group').querySelector('.input-spin');
            input.value = parseInt(input.value) + 1;
            updateSubtotal(e.target.closest('tr'));
        }

        // Handle minus button
        if (e.target.closest('.input-spin-minus')) {
            const input = e.target.closest('.input-spin-group').querySelector('.input-spin');
            if (parseInt(input.value) > 1) {
                input.value = parseInt(input.value) - 1;
                updateSubtotal(e.target.closest('tr'));
            }
        }

        // Handle remove item
        if (e.target.closest('.close-btn')) {
            e.preventDefault();
            if (confirm('آیا از حذف این مورد از لیست علاقه‌مندی‌هایتان مطمئن هستید؟')) {
                e.target.closest('tr').remove();
            }
        }
    });

    // Function to update subtotal when quantity changes
    function updateSubtotal(row) {
        const price = parseFloat(row.querySelector('td:nth-child(2)').textContent);
        const quantity = parseInt(row.querySelector('.input-spin').value);
        const subtotal = price * quantity;
        row.querySelector('td:nth-child(4)').textContent = subtotal.toFixed(2) + " تومان";
    }
});