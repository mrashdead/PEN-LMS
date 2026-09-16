//basic table
var table = new Tabulator("#basicTable", {
    height: "311px",
    layout: "fitDataStretch",
    resizableColumnFit: true,
    data: [
        { id: 1, name: "علی صبوری", age: 12, gender: "مرد", height: 95, col: "قرمز", dob: "14/05/2010" },
        { id: 2, name: "مریم کاویانی", age: 42, gender: "زن", height: 142, col: "آبی", dob: "30/07/1954" },
        { id: 3, name: "جمشید مشایخی", age: 35, gender: "مرد", height: 176, col: "سبز", dob: "04/11/1982" },
        { id: 4, name: "اما واتسون", age: 32, gender: "زن", height: 165, col: "بنفش", dob: "15/04/1990" },
        { id: 5, name: "مهران مدیری", age: 28, gender: "مرد", height: 180, col: "نارنجی", dob: "22/09/1995" },
        { id: 6, name: "ثریا قاسمی", age: 24, gender: "زن", height: 160, col: "صورتی", dob: "10/12/1999" },
        { id: 7, name: "جمشید هاشم‌پور", age: 40, gender: "مرد", height: 175, col: "قهوه‌ای", dob: "05/03/1983" },
        { id: 8, name: "سارا شریفی", age: 29, gender: "زن", height: 168, col: "فیروزه‌ای", dob: "18/07/1994" },
        { id: 9, name: "فیروز کریمی", age: 45, gender: "مرد", height: 182, col: "خاکستری", dob: "12/11/1978" },
        { id: 10, name: "الیکا عبدالرزاقی", age: 31, gender: "زن", height: 170, col: "سرخابی", dob: "25/02/1992" },
    ],
    columns: [
        { title: "نام", field: "name", width: 280, resizable: true },
        { title: "جنسیت", field: "gender", width: 280, resizable: true },
        { title: "قد", field: "height", width: 280, resizable: true },
        { title: "رنگ مورد علاقه", field: "col", width: 280, resizable: true },
        { title: "تاریخ تولد", field: "dob", width: 240, resizable: true },
    ],
});

//pagination with table
var table = new Tabulator("#paginationSortingTable", {
    layout: "fitDataStretch",
    pagination: "local",
    paginationSize: 6,
    paginationSizeSelector: [3, 6, 8, 10],
    movableColumns: true,
    paginationCounter: "rows",
    data: [
        { id: 1, name: "علی صبوری", age: 12, gender: "مرد", height: 95, col: "قرمز", dob: "14/05/2010" },
        { id: 2, name: "مریم کاویانی", age: 42, gender: "زن", height: 142, col: "آبی", dob: "30/07/1954" },
        { id: 3, name: "جمشید مشایخی", age: 35, gender: "مرد", height: 176, col: "سبز", dob: "04/11/1982" },
        { id: 4, name: "اما واتسون", age: 32, gender: "زن", height: 165, col: "بنفش", dob: "15/04/1990" },
        { id: 5, name: "مهران مدیری", age: 28, gender: "مرد", height: 180, col: "نارنجی", dob: "22/09/1995" },
        { id: 6, name: "ثریا قاسمی", age: 24, gender: "زن", height: 160, col: "صورتی", dob: "10/12/1999" },
        { id: 7, name: "جمشید هاشم‌پور", age: 40, gender: "مرد", height: 175, col: "قهوه‌ای", dob: "05/03/1983" },
        { id: 8, name: "سارا شریفی", age: 29, gender: "زن", height: 168, col: "فیروزه‌ای", dob: "18/07/1994" },
        { id: 9, name: "فیروز کریمی", age: 45, gender: "مرد", height: 182, col: "خاکستری", dob: "12/11/1978" },
        { id: 10, name: "الیکا عبدالرزاقی", age: 31, gender: "زن", height: 170, col: "سرخابی", dob: "25/02/1992" },
    ],
    columns: [
        { title: "نام", width: 280, field: "name" },
        { title: "جنسیت", width: 280, field: "gender" },
        { title: "قد", width: 280, field: "height" },
        { title: "رنگ مورد علاقه", width: 280, field: "col" },
        { title: "تاریخ تولد", width: 240, field: "dob", },
    ],
});

//Nested Data Trees
var tableDataNested = [
    {
        name: "باب مارلی", location: "انگلیس", gender: "مرد", col: "قرمز", dob: "14/04/1984", _children: [
            { name: "مریم امیرجلالی", location: "آلمان", gender: "زن", col: "آبی", dob: "14/05/1982" },
            { name: "کریستین امانپور", location: "فرانسه", gender: "زن", col: "سبز", dob: "22/05/1982" },
            {
                name: "برندون کوپر", location: "آمریکا", gender: "مرد", col: "نارنجی", dob: "01/08/1980", _children: [
                    { name: "مارگو رابی", location: "کانادا", gender: "زن", col: "زرد", dob: "31/01/1999" },
                    { name: "فرانک سیناترا", location: "روسیه", gender: "مرد", col: "قرمز", dob: "12/05/1966" },
                ]
            },
        ]
    },
    { name: "جیمی نیوهارت", location: "هندوستان", gender: "مرد", col: "سبز", dob: "14/05/1985" },
    {
        name: "گما جین", location: "چین", gender: "زن", col: "قرمز", dob: "22/05/1982", _children: [
            { name: "املیا کلارک", location: "کره جنوبی", gender: "زن", col: "طلایی", dob: "11/11/1970" },
        ]
    },
    { name: "جان نیومون", location: "ژاپن", gender: "مرد", col: "قرمز", dob: "22/03/1998" },
];

var table = new Tabulator("#nestingDateTreesTable", {
    layout: "fitDataStretch",
    data: tableDataNested,
    dataTree: true,
    dataTreeStartExpanded: true,
    columns: [
        { title: "نام", field: "name", width: 280, responsive: 0 }, //never hide this column
        { title: "مکان", field: "location", width: 280, },
        { title: "جنسیت", field: "gender", width: 280, responsive: 2 }, //hide this column first
        { title: "رنگ مورد علاقه", field: "col", width: 280, },
        { title: "تاریخ تولد", field: "dob", width: 240, hozAlign: "center", sorter: "dob" },
    ],
});

//Create Data Editor
var dateEditor = function (cell, onRendered, success, cancel) {
    //cell - the cell component for the editable cell
    //onRendered - function to call when the editor has been rendered
    //success - function to call to pass the successfully updated value to Tabulator
    //cancel - function to call to abort the edit and return to a normal cell

    //create and style input
    var cellValue = luxon.DateTime.fromFormat(cell.getValue(), "dd/MM/yyyy").toFormat("yyyy-MM-dd"),
        input = document.createElement("input");

    input.setAttribute("type", "date");

    input.style.padding = "4px";
    input.style.width = "100%";
    input.style.boxSizing = "border-box";

    input.value = cellValue;

    onRendered(function () {
        input.focus();
        input.style.height = "100%";
    });

    function onChange() {
        if (input.value != cellValue) {
            success(luxon.DateTime.fromFormat(input.value, "yyyy-MM-dd").toFormat("dd/MM/yyyy"));
        } else {
            cancel();
        }
    }

    //submit new value on blur or change
    input.addEventListener("blur", onChange);

    //submit new value on enter
    input.addEventListener("keydown", function (e) {
        if (e.keyCode == 13) {
            onChange();
        }

        if (e.keyCode == 27) {
            cancel();
        }
    });

    return input;
};


//Build Tabulator
var table = new Tabulator("#example-table", {
    height: "311px",
    layout: "fitDataStretch",
    data: [
        { id: 1, name: "علی صبوری", location: "چین", age: 12, gender: "مرد", height: 95, col: "قرمز", dob: "14/05/2010" },
        { id: 2, name: "مریم کاویانی", location: "آمریکا", age: 42, gender: "زن", height: 142, col: "آبی", dob: "30/07/1954" },
        { id: 3, name: "جمشید مشایخی", location: "مکزیک", age: 35, gender: "مرد", height: 176, col: "سبز", dob: "04/11/1982" },
        { id: 4, name: "اما واتسون", location: "برزیل", age: 32, gender: "زن", height: 165, col: "بنفش", dob: "15/04/1990" },
        { id: 5, name: "مهران مدیری", location: "روسیه", age: 28, gender: "مرد", height: 180, col: "نارنجی", dob: "22/09/1995" },
        { id: 6, name: "ثریا قاسمی", location: "اندونزی", age: 24, gender: "زن", height: 160, col: "صورتی", dob: "10/12/1999" },
        { id: 7, name: "جمشید هاشم‌پور", location: "ترکیه", age: 40, gender: "مرد", height: 175, col: "قهوه‌ای", dob: "05/03/1983" },
        { id: 8, name: "سارا شریفی", location: "فیلیپین", age: 29, gender: "زن", height: 168, col: "فیروزه‌ای", dob: "18/07/1994" },
        { id: 9, name: "فیروز کریمی", location: "چین", age: 45, gender: "مرد", height: 182, col: "خاکستری", dob: "12/11/1978" },
        { id: 10, name: "الیکا عبدالرزاقی", location: "برزیل", age: 31, gender: "زن", height: 170, col: "سرخابی", dob: "25/02/1992" },
    ],
    columns: [
        { title: "نام", field: "name", width: 280, editor: "input" },
        { title: "مکان", field: "location", width: 280, editor: "list", editorParams: { autocomplete: "true", allowEmpty: true, listOnEmpty: true, valuesLookup: true } },
        { title: "جنسیت", field: "gender", editor: "list", editorParams: { values: { "مرد": "مرد", "زن": "زن", "دیگری": "دیگری" } } },
        {
            title: "امتیاز",
            field: "rating",
            formatter: function (cell, formatterParams, onRendered) {
                var value = cell.getValue();
                var stars = "";
                for (var i = 1; i <= 5; i++) {
                    var starClass = i <= value ? "ri-star-fill active" : "ri-star-line";
                    stars += `<span class="${starClass}" data-rating="${i}" style="cursor: pointer; color: ${i <= value ? 'var(--dx-warning)' : 'var(--dx-secondary-color)'}; margin-right: 5px;"></span>`;
                }
                return stars;
            },
            cellClick: function (e, cell) {
                var rating = e.target.getAttribute("data-rating");
                if (rating) {
                    cell.setValue(rating); // Update the rating value
                }
            },
            hozAlign: "center",
            width: 280,
            editor: true,
        },
        { title: "تاریخ تولد", field: "dob", width: 280, hozAlign: "center", sorter: "date", width: 140, editor: dateEditor },
        { title: "امتیاز رانندگی", field: "car", width: 280, hozAlign: "center", editor: true, formatter: "tickCross" },
    ],
});