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
    }, 50);
    const table = new DataTable('#basicTable', {
        select: false,
        columnDefs: [{
            visible: false,
            searchable: false
        }]
    });
});

var groupColumn = 2;
var table = $('#basicTable').DataTable({
    columnDefs: [{ visible: false, targets: groupColumn }],
    order: [[groupColumn, 'asc']],
    displayLength: 25,
    drawCallback: function (settings) {
        var api = this.api();
        var rows = api.rows({ page: 'current' }).nodes();
        var last = null;
 
        api.column(groupColumn, { page: 'current' })
            .data()
            .each(function (group, i) {
                if (last !== group) {
                    $(rows)
                        .eq(i)
                        .before(
                            '<tr class="group bg-light"><td colspan="5">' +
                                group +
                                '</td></tr>'
                        );
 
                    last = group;
                }
            });
    }
});
 
// Order by the grouping
$('#example tbody').on('click', 'tr.group', function () {
    var currentOrder = table.order()[0];
    if (currentOrder[0] === groupColumn && currentOrder[1] === 'asc') {
        table.order([groupColumn, 'desc']).draw();
    }
    else {
        table.order([groupColumn, 'asc']).draw();
    }
});