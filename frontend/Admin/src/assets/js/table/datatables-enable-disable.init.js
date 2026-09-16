document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        const thElements = document.querySelectorAll('th .dt-column-order');
        thElements.forEach(function (th) {
            th.classList.remove('dt-column-order');
        });
        const dtLengthElement = document.getElementById('dt-length-0');
        const dtSearchElement = document.getElementById('dt-search-0');
        if (dtLengthElement) {
            dtLengthElement.classList.remove('form-select-sm');
        }
        if (dtSearchElement) {
            dtSearchElement.classList.remove('form-control-sm');
        }
    }, 100);
    const table = new DataTable('#enableDisableTable', {
        select: false,
        info: false,
        ordering: false,
        paging: false
    });
});
