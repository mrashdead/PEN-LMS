//basic Table
new gridjs.Grid({
    className: {
        table: 'text-nowrap',
    },
    columns: ["نام", "ایمیل", "شماره تلفن"],
    data: [
        ["جان", "john@example.com", "(353) 01 222 3333"],
        ["مارک", "mark@gmail.com", "(01) 22 888 4444"],
        ["ایلان", "eoin@gmail.com", "0097 22 654 00033"],
        ["سارا", "sarahcdd@gmail.com", "+322 876 1233"],
        ["افشین", "afshin@mail.com", "(353) 22 87 8356"]
    ]
}).render(document.getElementById("basicTable"));

//sorting Table
new gridjs.Grid({
    columns: ["نام", "ایمیل", "شماره تلفن"],
    className: {
        table: 'text-nowrap',
    },
    sort: true,
    data: [
        ["جان", "john@example.com", "(353) 01 222 3333"],
        ["مارک", "mark@gmail.com", "(01) 22 888 4444"],
        ["ایلان", "eoin@gmail.com", "0097 22 654 00033"],
        ["سارا", "sarahcdd@gmail.com", "+322 876 1233"],
        ["افشین", "afshin@mail.com", "(353) 22 87 8356"]
    ]
}).render(document.getElementById("sortingTable"));

//pagination Table
new gridjs.Grid({
    columns: ["نام", "ایمیل", "شماره تلفن"],
    className: {
        table: 'text-nowrap',
    },
    sort: true,
    "data": [
        ["جان", "john@example.com", "(353) 01 222 3333"],
        ["مارک", "mark@gmail.com", "(01) 22 888 4444"],
        ["ایلان", "eoin@gmail.com", "0097 22 654 00033"],
        ["سارا", "sarahcdd@gmail.com", "+322 876 1233"],
        ["افشین", "afshin@mail.com", "(353) 22 87 8356"],
        ["آلیس", "alice@yahoo.com", "(44) 07123 456789"],
        ["باب", "bob@outlook.com", "+1 234 567 8901"],
        ["چارلی", "charlie@hotmail.com", "(416) 555-1234"],
        ["دیوید", "david@domain.com", "(234) 555-4567"],
        ["حوا", "eve@work.com", "+44 20 7946 0958"],
        ["فرانک", "frank@gmail.com", "(123) 456 7890"],
        ["گریس", "grace@domain.com", "+34 912 345 678"],
        ["هانا", "hannah@company.com", "(541) 555 0099"],
        ["ایرنه", "irene@service.com", "+39 06 693 8380"],
        ["جک", "jack@example.com", "(777) 555-9876"],
        ["کلی", "kelly@company.net", "+49 170 6543210"],
        ["لئو", "leo@domain.org", "(555) 667 1234"],
        ["میا", "mia@demo.com", "+61 2 9876 4321"],
        ["نینا", "nina@sample.com", "(818) 555-7654"],
        ["اسکار", "oscar@website.com", "+1 323 123 4567"],
        ["پاول", "paul@company.org", "(905) 555-8888"]
    ],
    pagination: {
        limit: 8
    },
}).render(document.getElementById("paginationTable"));


//search Table
new gridjs.Grid({
    columns: ["نام", "ایمیل", "شماره تلفن"],
    className: {
        table: 'text-nowrap',
    },
    search: {
        selector: (cell, rowIndex, cellIndex) => cellIndex === 0 ? cell.firstName : cell
    },
    "data": [
        ["جان", "john@example.com", "(353) 01 222 3333"],
        ["مارک", "mark@gmail.com", "(01) 22 888 4444"],
        ["ایلان", "eoin@gmail.com", "0097 22 654 00033"],
        ["سارا", "sarahcdd@gmail.com", "+322 876 1233"],
        ["افشین", "afshin@mail.com", "(353) 22 87 8356"],
        ["آلیس", "alice@yahoo.com", "(44) 07123 456789"],
        ["باب", "bob@outlook.com", "+1 234 567 8901"],
        ["چارلی", "charlie@hotmail.com", "(416) 555-1234"],
        ["دیوید", "david@domain.com", "(234) 555-4567"],
        ["حوا", "eve@work.com", "+44 20 7946 0958"],
        ["فرانک", "frank@gmail.com", "(123) 456 7890"],
        ["گریس", "grace@domain.com", "+34 912 345 678"],
        ["هانا", "hannah@company.com", "(541) 555 0099"],
        ["ایرنه", "irene@service.com", "+39 06 693 8380"],
        ["جک", "jack@example.com", "(777) 555-9876"],
        ["کلی", "kelly@company.net", "+49 170 6543210"],
        ["لئو", "leo@domain.org", "(555) 667 1234"],
        ["میا", "mia@demo.com", "+61 2 9876 4321"],
        ["نینا", "nina@sample.com", "(818) 555-7654"],
        ["اسکار", "oscar@website.com", "+1 323 123 4567"],
        ["پاول", "paul@company.org", "(905) 555-8888"]
    ],
    pagination: {
        limit: 8
    },
}).render(document.getElementById("searchTable"));

//Loading Table
new gridjs.Grid({
    columns: ['نام', 'ایمیل', 'شماره تلفن'],
    sort: true,
    search: true,
    className: {
        table: 'text-nowrap',
    },
    pagination: {
        limit: 8
    },
    data: () => {
        return new Promise(resolve => {
            setTimeout(() =>
                resolve([
                    ["جان", "john@example.com", "(353) 01 222 3333"],
                    ["مارک", "mark@gmail.com", "(01) 22 888 4444"],
                    ["ایلان", "eoin@gmail.com", "0097 22 654 00033"],
                    ["سارا", "sarahcdd@gmail.com", "+322 876 1233"],
                    ["افشین", "afshin@mail.com", "(353) 22 87 8356"],
                    ["آلیس", "alice@yahoo.com", "(44) 07123 456789"],
                    ["باب", "bob@outlook.com", "+1 234 567 8901"],
                    ["چارلی", "charlie@hotmail.com", "(416) 555-1234"],
                    ["دیوید", "david@domain.com", "(234) 555-4567"],
                    ["حوا", "eve@work.com", "+44 20 7946 0958"],
                    ["فرانک", "frank@gmail.com", "(123) 456 7890"],
                    ["گریس", "grace@domain.com", "+34 912 345 678"],
                    ["هانا", "hannah@company.com", "(541) 555 0099"],
                    ["ایرنه", "irene@service.com", "+39 06 693 8380"],
                    ["جک", "jack@example.com", "(777) 555-9876"],
                    ["کلی", "kelly@company.net", "+49 170 6543210"],
                    ["لئو", "leo@domain.org", "(555) 667 1234"],
                    ["میا", "mia@demo.com", "+61 2 9876 4321"],
                    ["نینا", "nina@sample.com", "(818) 555-7654"],
                    ["اسکار", "oscar@website.com", "+1 323 123 4567"],
                    ["پاول", "paul@company.org", "(905) 555-8888"]
                ]), 2000);
        });
    }
}).render(document.getElementById("loadingTable"));

//Fixed Header Table
new gridjs.Grid({
    columns: ['نام', 'ایمیل', 'شماره تلفن'],
    sort: true,
    search: true,
    fixedHeader: true,
    height: '400px',
    className: {
        table: 'text-nowrap',
    },

    "data": [
        ["جان", "john@example.com", "(353) 01 222 3333"],
        ["مارک", "mark@gmail.com", "(01) 22 888 4444"],
        ["ایلان", "eoin@gmail.com", "0097 22 654 00033"],
        ["سارا", "sarahcdd@gmail.com", "+322 876 1233"],
        ["افشین", "afshin@mail.com", "(353) 22 87 8356"],
        ["آلیس", "alice@yahoo.com", "(44) 07123 456789"],
        ["باب", "bob@outlook.com", "+1 234 567 8901"],
        ["چارلی", "charlie@hotmail.com", "(416) 555-1234"],
        ["دیوید", "david@domain.com", "(234) 555-4567"],
        ["حوا", "eve@work.com", "+44 20 7946 0958"],
        ["فرانک", "frank@gmail.com", "(123) 456 7890"],
        ["گریس", "grace@domain.com", "+34 912 345 678"],
        ["هانا", "hannah@company.com", "(541) 555 0099"],
        ["ایرنه", "irene@service.com", "+39 06 693 8380"],
        ["جک", "jack@example.com", "(777) 555-9876"],
        ["کلی", "kelly@company.net", "+49 170 6543210"],
        ["لئو", "leo@domain.org", "(555) 667 1234"],
        ["میا", "mia@demo.com", "+61 2 9876 4321"],
        ["نینا", "nina@sample.com", "(818) 555-7654"],
        ["اسکار", "oscar@website.com", "+1 323 123 4567"],
        ["پاول", "paul@company.org", "(905) 555-8888"]
    ],
}).render(document.getElementById("fixedHeaderTable"));