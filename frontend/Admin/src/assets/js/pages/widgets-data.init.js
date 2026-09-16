document.addEventListener('DOMContentLoaded', function () {
    const table = document.querySelector('table');
    const headers = table.querySelectorAll('th');
    const tbody = table.querySelector('tbody');

    headers.forEach((header, index) => {
        // Skip the first column (Product) from sorting as it contains complex content
        if (index > 0) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                sortTable(index, header);
            });
        }
    });

    function sortTable(column, header) {
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isAscending = header.getAttribute('data-sort') === 'asc';

        // Remove sort indicators from all headers
        headers.forEach(h => {
            h.querySelector('.sort-indicator')?.remove();
            h.removeAttribute('data-sort');
        });

        // Add sort indicator
        const indicator = document.createElement('i');
        indicator.className = `sort-indicator ms-1 ri ${isAscending ? 'ri-arrow-up-long-fill' : 'ri-arrow-down-long-fill'}`;
        header.appendChild(indicator);

        // Toggle sort direction
        header.setAttribute('data-sort', isAscending ? 'desc' : 'asc');

        rows.sort((a, b) => {
            const aCell = a.cells[column].textContent.trim();
            const bCell = b.cells[column].textContent.trim();

            // Handle numeric values (Sales, Price, Stock, Revenue)
            if ([1, 2, 3, 4].includes(column)) {
                const aValue = parseFloat(aCell.replace(/[^0-9.-]/g, ''));
                const bValue = parseFloat(bCell.replace(/[^0-9.-]/g, ''));
                return isAscending ? aValue - bValue : bValue - aValue;
            }
            // Handle rating (column 5)
            else if (column === 5) {
                const aValue = parseFloat(aCell);
                const bValue = parseFloat(bCell);
                return isAscending ? aValue - bValue : bValue - aValue;
            }

            // Default to string comparison (shouldn't happen as we skip column 0)
            return isAscending
                ? aCell.localeCompare(bCell)
                : bCell.localeCompare(aCell);
        });

        // Rebuild the table
        rows.forEach(row => tbody.appendChild(row));
    }
});