import { icons, createIcons } from "lucide";

// Leave management data and functionality
document.addEventListener('DOMContentLoaded', function () {
    // Leave data in JSON format
    const leaveData = [
        {
            id: "PEA-15015",
            leaveType: "تعطیلات",
            startDate: "26 خرداد 1403",
            endDate: "1 تیر 1403",
            days: 7,
            reason: "تعطیلات خانوادگی",
            approvedBy: "",
            requestDate: "23 خرداد 1403",
            approvedDate: "25 خرداد 1403",
            status: "pending"
        },
        {
            id: "PEA-15016",
            leaveType: "مرخصی استعلاجی",
            startDate: "20 تیر 1403",
            endDate: "24 تیر 1403",
            days: 5,
            reason: "دلایل پزشکی",
            approvedBy: "HR",
            requestDate: "18 تیر 1403",
            approvedDate: "19 تیر 1403",
            status: "approved"
        },
        {
            id: "PEA-15017",
            leaveType: "شخصی",
            startDate: "11 مرداد 1403",
            endDate: "13 مرداد 1403",
            days: 3,
            reason: "دلایل شخصی",
            approvedBy: "مدیر",
            requestDate: "21 تیر 1403",
            approvedDate: "9 مرداد 1403",
            status: "approved"
        },
        {
            id: "PEA-15018",
            leaveType: "تعطیلات",
            startDate: "30 مرداد 1403",
            endDate: "6 شهریور 1403",
            days: 8,
            reason: "سفر",
            approvedBy: "",
            requestDate: "25 مرداد 1403",
            approvedDate: "28 مرداد 1403",
            status: "pending"
        },
        {
            id: "PEA-15019",
            leaveType: "مرخصی زایمان",
            startDate: "15 شهریور 1403",
            endDate: "15 شهریور 1403",
            days: 1,
            reason: "تولد مادر",
            approvedBy: "HR",
            requestDate: "11 شهریور 1403",
            approvedDate: "13 شهریور 1403",
            status: "approved"
        },
        {
            id: "PEA-15020",
            leaveType: "مرخصی استعلاجی",
            startDate: "22 شهریور 1403",
            endDate: "26 شهریور 1403",
            days: 5,
            reason: "بهبودی پس از جراحی",
            approvedBy: "",
            requestDate: "20 شهریور 1403",
            approvedDate: "11 شهریور 1403",
            status: "pending"
        },
        {
            id: "PEA-15021",
            leaveType: "تعطیلات",
            startDate: "10 مهر 1403",
            endDate: "19 مهر 1403",
            days: 10,
            reason: "ماه عسل",
            approvedBy: "مدیر",
            requestDate: "4 مهر 1403",
            approvedDate: "7 مهر 1403",
            status: "approved"
        },
        {
            id: "PEA-15022",
            leaveType: "شخصی",
            startDate: "29 مهر 1403",
            endDate: "1 آبان 1403",
            days: 3,
            reason: "دلایل شخصی",
            approvedBy: "مدیر",
            requestDate: "27 مهر 1403",
            approvedDate: "28 مهر 1403",
            status: "rejected"
        },
        {
            id: "PEA-15023",
            leaveType: "مرخصی استعلاجی",
            startDate: "15 آبان 1403",
            endDate: "17 آبان 1403",
            days: 3,
            reason: "آنفولانزا",
            approvedBy: "HR",
            requestDate: "13 آبان 1403",
            approvedDate: "14 آبان 1403",
            status: "approved"
        },
        {
            id: "PEA-15024",
            leaveType: "تعطیلات",
            startDate: "25 آبان 1403",
            endDate: "2 آذر 1403",
            days: 8,
            reason: "تعطیلات",
            approvedBy: "",
            requestDate: "20 آبان 1403",
            approvedDate: "22 آبان 1403",
            status: "pending"
        },
        {
            id: "PEA-15025",
            leaveType: "شخصی",
            startDate: "15 آذر 1403",
            endDate: "16 آذر 1403",
            days: 2,
            reason: "دلایل شخصی",
            approvedBy: "مدیر",
            requestDate: "11 آذر 1403",
            approvedDate: "13 آذر 1403",
            status: "approved"
        },
    ];

    // Variables to control pagination
    let currentPage = 1;
    const itemsPerPage = 10;
    let totalPages = Math.ceil(leaveData.length / itemsPerPage);
    let filteredData = [...leaveData];

    // Sorting state
    let currentSortColumn = 'id';
    let currentSortOrder = 'asc';

    // Initialize the table on page load
    setupSortableHeaders();
    renderTable(filteredData, currentPage);
    setupPagination();
    initializeStatusSelect();
    setupDateRange();
    setupSearchFilter();
    setupFilterButton();

    // Function to set up sortable column headers
    function setupSortableHeaders() {
        const tableHeaders = document.querySelectorAll('thead th');

        // Add sort indicators and click handlers to sortable columns
        tableHeaders.forEach(header => {
            // Skip the last column (Actions)
            if (header.textContent.trim() === 'Actions') return;

            // Get the column name from the header text
            const columnName = header.textContent.trim().toLowerCase().replace(/\s+/g, '');

            // Make the header clickable for sorting
            header.style.cursor = 'pointer';
            header.classList.add('sortable');

            // Add sort indicators (initially hidden)
            const sortIndicator = document.createElement('span');
            sortIndicator.className = 'sort-indicator ms-2';
            sortIndicator.innerHTML = '<i data-lucide="arrow-up" class="size-3 d-none"></i><i data-lucide="arrow-down" class="size-3 d-none"></i>';
            header.appendChild(sortIndicator);

            // Add click event to sort the table
            header.addEventListener('click', function () {
                const column = columnNameToProperty(header.textContent.trim());

                // Toggle sort order if clicking the same column
                if (currentSortColumn === column) {
                    currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSortColumn = column;
                    currentSortOrder = 'asc';
                }

                // Sort the data
                sortData(column, currentSortOrder);

                // Update sort indicators
                updateSortIndicators(header);

                // Reset to first page when sorting changes
                currentPage = 1;

                // Re-render the table with sorted data
                renderTable(filteredData, currentPage);
                setupPagination();
            });
        });

        // Initialize the sort indicators
        createIcons({ icons });
    }

    // Function to update sort indicators on column headers
    function updateSortIndicators(activeHeader) {
        const tableHeaders = document.querySelectorAll('thead th.sortable');

        tableHeaders.forEach(header => {
            // Get the arrow icons
            const upArrow = header.querySelector('[data-lucide="arrow-up"]');
            const downArrow = header.querySelector('[data-lucide="arrow-down"]');

            if (header === activeHeader) {
                // Show the appropriate arrow for the active header
                if (currentSortOrder === 'asc') {
                    upArrow.classList.remove('d-none');
                    downArrow.classList.add('d-none');
                } else {
                    upArrow.classList.add('d-none');
                    downArrow.classList.remove('d-none');
                }
            } else {
                // Hide arrows for inactive headers
                upArrow.classList.add('d-none');
                downArrow.classList.add('d-none');
            }
        });
    }

    // Function to convert column header text to data property
    function columnNameToProperty(headerText) {
        // Map header text to data property names
        const columnMap = {
            'ID': 'id',
            'Leave Type': 'leaveType',
            'Start Date': 'startDate',
            'End Date': 'endDate',
            'Days': 'days',
            'Reason': 'reason',
            'Approved By': 'approvedBy',
            'Request Date': 'requestDate',
            'Approved Date': 'approvedDate',
            'Status': 'status'
        };

        return columnMap[headerText] || headerText.toLowerCase();
    }

    // Function to sort the data
    function sortData(column, order) {
        filteredData.sort((a, b) => {
            let valueA = a[column];
            let valueB = b[column];

            // Special handling for dates
            if (column === 'startDate' || column === 'endDate' || column === 'requestDate' || column === 'approvedDate') {
                valueA = parseDateString(valueA);
                valueB = parseDateString(valueB);
            }

            // Special handling for numeric values
            if (column === 'days') {
                valueA = parseInt(valueA, 10);
                valueB = parseInt(valueB, 10);
                return order === 'asc' ? valueA - valueB : valueB - valueA;
            }

            // Default string comparison
            if (valueA < valueB) return order === 'asc' ? -1 : 1;
            if (valueA > valueB) return order === 'asc' ? 1 : -1;
            return 0;
        });
    }

    // Function to parse date strings (format: "DD Month, YYYY")
    function parseDateString(dateStr) {
        if (!dateStr) return new Date(0); // Handle empty dates

        const parts = dateStr.split(' ');
        if (parts.length < 3) return new Date(0); // Invalid format

        const day = parseInt(parts[0], 10);
        const month = parts[1].replace(',', '');
        const year = parseInt(parts[2], 10);

        const monthNames = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ];

        const monthIndex = monthNames.findIndex(m => month.startsWith(m));
        return new Date(year, monthIndex, day);
    }

    // Function to render the table with data
    function renderTable(data, page) {
        const tableBody = document.querySelector('tbody');
        tableBody.innerHTML = '';

        // Set status badge class based on leave status
        const statusTextMap = {
            approved: "تأیید شده",
            pending: "در حال بررسی",
            rejected: "رد شده"
        };

        const statusClassMap = {
            approved: "bg-success-subtle text-success border border-success-subtle",
            pending: "bg-warning-subtle text-warning border border-warning-subtle",
            rejected: "bg-danger-subtle text-danger border border-danger-subtle"
        };

        // Check if there are no results to display
        if (data.length === 0) {
            const noDataRow = document.createElement('tr');
            noDataRow.innerHTML = `
                <td colspan="11" class="text-center py-4">
                    <div class="d-flex flex-column align-items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" class="mx-auto size-12" viewBox="0 0 48 48">
                            <linearGradient id="SVGID_1" x1="34.598" x2="15.982" y1="15.982" y2="34.598" gradientUnits="userSpaceOnUse">
                                <stop offset="0" stop-color="#60e8fe"></stop>
                                <stop offset=".033" stop-color="#6ae9fe"></stop>
                                <stop offset=".197" stop-color="#97f0fe"></stop>
                                <stop offset=".362" stop-color="#bdf5ff"></stop>
                                <stop offset=".525" stop-color="#dafaff"></stop>
                                <stop offset=".687" stop-color="#eefdff"></stop>
                                <stop offset=".846" stop-color="#fbfeff"></stop>
                                <stop offset="1" stop-color="#ffffff"></stop>
                            </linearGradient>
                            <path fill="url(#SVGID_1)" d="M40.036,33.826L31.68,25.6c0.847-1.739,1.335-3.684,1.335-5.748
                                c0-7.27-5.894-13.164-13.164-13.164S6.688,12.582,6.688,19.852c0,7.27,5.894,13.164,13.164,13.164
                                c2.056,0,3.995-0.485,5.728-1.326l3.914,4.015l4.331,4.331c1.715,1.715,4.496,1.715,6.211,0
                                C41.751,38.321,41.751,35.541,40.036,33.826z">
                            </path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round"
                                stroke-miterlimit="10" stroke-width="3"
                                d="M31.95,25.739l8.086,8.086c1.715,1.715,1.715,4.496,0,6.211l0,0c-1.715,1.715-4.496,1.715-6.211,0l-4.331-4.331">
                            </path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round"
                                stroke-miterlimit="10" stroke-width="3"
                                d="M7.525,24.511c-1.771-4.694-0.767-10.196,3.011-13.975c3.847-3.847,9.48-4.817,14.228-2.912">
                            </path>
                            <path fill="none" stroke="#10cfe3" stroke-linecap="round" stroke-linejoin="round"
                                stroke-miterlimit="10" stroke-width="3"
                                d="M30.856,12.603c3.376,5.114,2.814,12.063-1.688,16.565c-4.858,4.858-12.565,5.129-17.741,0.814">
                            </path>
                        </svg>
                        <p class="mt-2 text-center text-gray-500 dark:text-dark-500">هیچ رکورد منطبقی یافت نشد</p>
                        <p class="text-muted mb-0">ما نتوانستیم هیچ دسته‌بندی مطابق با جستجوی شما پیدا کنیم.</p>
                    </div>
                </td>
            `;
            tableBody.appendChild(noDataRow);

            // Hide pagination when no results
            document.querySelector('#paginationResult').style.display = 'none';
            return;
        } else {
            // Show pagination when results exist
            document.querySelector('#paginationResult').style.display = 'flex';
        }

        const startIndex = (page - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, data.length);
        const paginatedData = data.slice(startIndex, endIndex);

        paginatedData.forEach(leave => {
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${leave.id}</td>
                <td>${leave.leaveType}</td>
                <td>${leave.startDate}</td>
                <td>${leave.endDate}</td>
                <td>${leave.days}</td>
                <td>${leave.reason}</td>
                <td>${leave.approvedBy}</td>
                <td>${leave.requestDate}</td>
                <td>${leave.approvedDate}</td>
                <td>
                    <span class="badge ${statusClassMap[leave.status]}">
                        ${statusTextMap[leave.status]}
                    </span>
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn btn-light size-8 btn-icon edit-btn" data-id="${leave.id}"><i class="ri-pencil-line"></i></button>
                        <button class="btn btn-sub-success size-8 btn-icon approve-btn" data-id="${leave.id}"><i class="ri-check-line"></i></button>
                        <button class="btn btn-sub-danger size-8 btn-icon reject-btn" data-id="${leave.id}"><i class="ri-close-line"></i></button>
                    </div>
                </td>
            `;

            tableBody.appendChild(row);
        });

        // Update the pagination display
        updatePaginationDisplay(data);

        // Set up event listeners for action buttons
        setupActionButtons();
    }

    // Function to update the pagination display
    function updatePaginationDisplay(data) {
        const totalItems = data.length;
        const startItem = totalItems > 0 ? ((currentPage - 1) * itemsPerPage) + 1 : 0;
        const endItem = Math.min(currentPage * itemsPerPage, totalItems);

        document.querySelector('#showingResults p').innerHTML = `نمایش <b class="me-1">${startItem}-${endItem}</b>از<b class="ms-1">${totalItems}</b> نتیجه`;
    }

    // Function to set up pagination controls
    function setupPagination() {
        totalPages = Math.max(1, Math.ceil(filteredData.length / itemsPerPage));

        // Ensure current page is within valid range
        if (currentPage > totalPages) {
            currentPage = totalPages;
        }

        const paginationContainer = document.querySelector('.pagination');
        paginationContainer.innerHTML = '';

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#!"><i data-lucide="chevron-right" class="size-4"></i> قبلی</a>`;
        paginationContainer.appendChild(prevLi);

        prevLi.addEventListener('click', function () {
            if (currentPage > 1) {
                currentPage--;
                renderTable(filteredData, currentPage);
                setupPagination();
            }
        });

        // Page numbers
        for (let i = 1; i <= Math.min(totalPages, 3); i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${currentPage === i ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#!">${i}</a>`;
            paginationContainer.appendChild(pageLi);

            pageLi.addEventListener('click', function () {
                currentPage = i;
                renderTable(filteredData, currentPage);
                setupPagination();
            });
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#!">بعدی <i data-lucide="chevron-left" class="size-4"></i></a>`;
        paginationContainer.appendChild(nextLi);

        nextLi.addEventListener('click', function () {
            if (currentPage < totalPages) {
                currentPage++;
                renderTable(filteredData, currentPage);
                setupPagination();
            }
        });

        createIcons({ icons });
    }

    // Function to initialize status select dropdown
    function initializeStatusSelect() {
        const statusSelect = document.getElementById('statusSelect');
        statusSelect.innerHTML = `
            <select class="form-select" id="statusFilter">
                <option value="">همه وضعیت‌ها</option>
                <option value="approved">تایید شده</option>
                <option value="pending">در حال بررسی</option>
                <option value="rejected">رد شده</option>
            </select>
        `;

        document.getElementById('statusFilter').addEventListener('change', applyFilters);
    }

    // Function to set up date range picker
    function setupDateRange() {
        const dateRangeInput = document.querySelector('input[placeholder="انتخاب محدوده داده"]');

        // Simple date range picker initialization (replace with actual date picker library in production)
        dateRangeInput.addEventListener('click', function () {
            // For demonstration, just toggle a data-active attribute
            if (this.getAttribute('data-active') === 'true') {
                this.setAttribute('data-active', 'false');
            } else {
                this.setAttribute('data-active', 'true');
                // In a real implementation, this would open a date range picker
            }
        });
    }

    // Function to set up search functionality
    function setupSearchFilter() {
        const searchInput = document.getElementById('searchLeaveInput');

        searchInput.addEventListener('input', function () {
            applyFilters();
        });
    }

    // Function to set up filter button
    function setupFilterButton() {
        const filterButton = document.querySelector('#filterNow');

        filterButton.addEventListener('click', function () {
            applyFilters();
        });
    }

    // Function to apply all filters
    function applyFilters() {
        const searchTerm = document.getElementById('searchLeaveInput').value;
        const statusFilter = document.getElementById('statusFilter').value;

        filteredData = leaveData.filter(leave => {
            // Search filter
            const matchesSearch =
                leave.id.includes(searchTerm) ||
                leave.leaveType.includes(searchTerm) ||
                leave.reason.includes(searchTerm);

            // Status filter
            const matchesStatus = statusFilter === '' || leave.status === statusFilter;

            return matchesSearch && matchesStatus;
        });

        // Reset to first page when filters change
        currentPage = 1;

        // Apply any existing sort
        if (currentSortColumn) {
            sortData(currentSortColumn, currentSortOrder);
        }

        // Update the table and pagination
        renderTable(filteredData, currentPage);
        setupPagination();
    }

    // Function to set up action buttons
    function setupActionButtons() {
        // Approve buttons
        document.querySelectorAll('.approve-btn').forEach(button => {
            button.addEventListener('click', function () {
                const leaveId = this.getAttribute('data-id');
                const leaveIndex = leaveData.findIndex(leave => leave.id === leaveId);

                if (leaveIndex !== -1) {
                    leaveData[leaveIndex].status = 'approved';
                    leaveData[leaveIndex].approvedBy = 'جمشید بهاری‌فر';
                    leaveData[leaveIndex].approvedDate = new Date().toLocaleDateString('fa-IR', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric'
                    });

                    // Update filteredData as well if the item exists there
                    const filteredIndex = filteredData.findIndex(leave => leave.id === leaveId);
                    if (filteredIndex !== -1) {
                        filteredData[filteredIndex] = { ...leaveData[leaveIndex] };
                    }

                    // Re-render the table to show the updated status
                    renderTable(filteredData, currentPage);
                    setupPagination();
                }
            });
        });

        // Reject buttons
        document.querySelectorAll('.reject-btn').forEach(button => {
            button.addEventListener('click', function () {
                const leaveId = this.getAttribute('data-id');
                const leaveIndex = leaveData.findIndex(leave => leave.id === leaveId);

                if (leaveIndex !== -1) {
                    leaveData[leaveIndex].status = 'rejected';

                    // Update filteredData as well if the item exists there
                    const filteredIndex = filteredData.findIndex(leave => leave.id === leaveId);
                    if (filteredIndex !== -1) {
                        filteredData[filteredIndex] = { ...leaveData[leaveIndex] };
                    }

                    // Re-render the table to show the updated status
                    renderTable(filteredData, currentPage);
                    setupPagination();
                }
            });
        });
    }

    // Add function for testing "no records found" scenario
    window.testNoRecordsFound = function () {
        document.getElementById('searchLeaveInput').value = "nonexistentrecord";
        applyFilters();
    };
});