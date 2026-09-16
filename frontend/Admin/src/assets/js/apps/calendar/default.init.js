
document.addEventListener('DOMContentLoaded', function () {
    var currentYear = new Date().getFullYear();
    var currentMonth = new Date().getMonth();

    // Fix the typo in the Festival Function button
    var festivalButton = document.querySelector('.btn-info .fc-event-mai');
    if (festivalButton) {
        festivalButton.textContent = 'مراسم جشنواره';
        festivalButton.className = 'fc-event-main fs-13';
    }

    // Initialize the external events with Draggable from FullCalendar
    var containerEl = document.getElementById('external-events');
    new FullCalendar.Draggable(containerEl, {
        itemSelector: '.draggable-event',
        eventData: function (eventEl) {
            // Safely get the title element
            var titleEl = eventEl.querySelector('.fc-event-main');
            if (!titleEl) {
                console.error('Event title element not found');
                return { title: 'Untitled Event' }; // Fallback title
            }

            // Determine the event color class based on the button class
            var colorClass = 'bg-secondary'; // Default color
            if (eventEl.classList.contains('btn-primary')) colorClass = 'bg-primary';
            if (eventEl.classList.contains('btn-success')) colorClass = 'bg-success';
            if (eventEl.classList.contains('btn-info')) colorClass = 'bg-info';

            return {
                title: titleEl.textContent,
                backgroundColor: colorClass.replace('bg-', ''),
                className: colorClass + ' text-white p-2 rounded-2'
            };
        }
    });

    // Initialize the calendar
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        timeZone: 'local',
        locale: 'fa',
        direction: 'rtl',
        firstDay: 6,
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'امروز',
            month: 'ماه',
            week: 'هفته',
            day: 'روز'
        },
        allDayText: 'تمام روز',
        buttonHints: {
        today: 'رفتن به امروز',
        month: 'نمایش ماه',
        week: 'نمایش هفته',
        day: 'نمایش روز',
        prev: 'قبلی',
        next: 'بعدی'
        },
        events: [
            { id: '1', title: 'جلسه', start: new Date(currentYear, currentMonth, 1), backgroundColor: 'success', className: 'bg-success text-white p-2 rounded-2', extendedProps: { location: "تهران", guests: [] } },
            { id: '2', title: 'آپدیت هفتگی', start: new Date(currentYear, currentMonth, 7), backgroundColor: 'primary', className: 'bg-primary text-white p-2 rounded-2', extendedProps: { location: "تهران", guests: [] } },
            { id: '3', title: 'شام خانوادگی', start: new Date(currentYear, currentMonth, 14), backgroundColor: 'secondary', className: 'bg-secondary text-white p-2 rounded-2', extendedProps: { location: "تهران", guests: [] } },
            { id: '4', title: 'تجدید دیدار مدرسه', start: new Date(currentYear, currentMonth, 10), backgroundColor: 'info', className: 'bg-info text-white p-2 rounded-2', extendedProps: { location: "تهران", guests: [] } },
            { id: '5', title: 'تور تعطیلات', start: new Date(currentYear, currentMonth, 14), backgroundColor: 'success', className: 'bg-success text-white p-2 rounded-2', extendedProps: { location: "تهران", guests: [] } },
            { id: '6', title: 'جلسه', start: new Date(currentYear, currentMonth, 23), backgroundColor: 'success', className: 'bg-success text-white p-2 rounded-2', extendedProps: { location: "تهران", guests: [] } },
            { id: '7', title: 'مشاوره ازدواج', start: new Date(currentYear, currentMonth, 18), backgroundColor: 'secondary', className: 'bg-secondary text-white p-2 rounded-2', extendedProps: { location: "تهران", guests: [] } }
        ],
        editable: true,
        droppable: true,
        eventContent: function (info) {
            const containerEl = document.createElement('div');
            containerEl.classList.add('overflow-hidden');
            const titleEl = document.createElement('div');
            titleEl.classList.add('fc-event-title', 'text-truncate', 'text-white', 'fs-sm');
            titleEl.innerText = info.event.title;
            containerEl.appendChild(titleEl);
            return { domNodes: [containerEl] };
        },
        dateClick: function (info) {
            resetEventForm();
            var modal = new window.bootstrap.Modal(document.getElementById('addEventModal'));
            document.getElementById('eventDateInput').value = info.dateStr;
            document.getElementById('endEventDateInput').value = info.dateStr;
            document.getElementById('modalTitle').textContent = 'افزودن رویداد';
            document.getElementById('submitEventBtn').textContent = 'ایجاد رویداد';
            // Clear any existing event ID
            document.getElementById('eventForm').removeAttribute('data-event-id');
            modal.show();
        },
        eventClick: function (info) {
            // First reset the form to clear any previous data
            resetEventForm();

            // Open modal for editing
            var modal = new window.bootstrap.Modal(document.getElementById('addEventModal'));

            // Set modal title
            document.getElementById('modalTitle').textContent = 'ویرایش رویداد';
            document.getElementById('submitEventBtn').textContent = 'آپدیت رویداد';

            // Get event data
            const event = info.event;

            // Fill form with event data
            document.getElementById('eventNameInput').value = event.title;

            // Format the date for input element (YYYY-MM-DD)
            const startDate = event.start ? formatDateForInput(event.start) : '';
            document.getElementById('eventDateInput').value = startDate;

            const endDate = event.end ? formatDateForInput(event.end) : startDate;
            document.getElementById('endEventDateInput').value = endDate;

            // Set time if it's not an all-day event
            if (!event.allDay && event.start) {
                const hours = event.start.getHours().toString().padStart(2, '0');
                const minutes = event.start.getMinutes().toString().padStart(2, '0');
                document.getElementById('eventTimeInput').value = `${hours}:${minutes}`;
            } else {
                document.getElementById('eventTimeInput').value = '';
            }

            // Set location
            document.getElementById('locationInput').value = event.extendedProps?.location || '';

            // Set event ID as data attribute for form submission
            document.getElementById('eventForm').setAttribute('data-event-id', event.id);

            // Display guests if any
            displayGuests(event.extendedProps?.guests || []);

            modal.show();
        },
        drop: function (info) {
        }
    });

    calendar.render();

    // Helper function to format date for input
    function formatDateForInput(date) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    // Function to reset form
    function resetEventForm() {
        document.getElementById('eventForm').reset();
        document.getElementById('guestList').innerHTML = '';
    }

    // Function to display guests in the modal
    function displayGuests(guests) {
        const guestListEl = document.getElementById('guestList');
        guestListEl.innerHTML = '';

        if (guests && guests.length > 0) {
            guests.forEach(guest => {
                const guestEl = createGuestElement(guest.email, guest.avatarId);
                guestListEl.appendChild(guestEl);
            });
        }
    }

    // Function to create a guest element
    function createGuestElement(email, avatarId) {
        const guestDiv = document.createElement('div');
        guestDiv.className = 'position-relative rounded-circle size-9';
        guestDiv.setAttribute('data-email', email);

        const img = document.createElement('img');
        img.src = `assets/images/avatar/user-${avatarId}.png`;
        img.alt = email;
        img.className = 'size-9 rounded-circle';

        const removeLink = document.createElement('a');
        removeLink.href = '#!';
        removeLink.className = 'position-absolute d-inline-flex align-items-center justify-content-center text-white bg-dark fs-13 border-2 rounded-circle size-4 top-0 end-0 me-n1 mt-n1';
        removeLink.innerHTML = '<i class="text-xs ri-close-line"></i>';

        // Add event listener to remove guest
        removeLink.addEventListener('click', function (e) {
            e.preventDefault();
            guestDiv.remove();
        });

        guestDiv.appendChild(img);
        guestDiv.appendChild(removeLink);

        return guestDiv;
    }

    // Add guest button handler
    document.getElementById('addGuestBtn').addEventListener('click', function () {
        const guestInput = document.getElementById('guestInput');
        const email = guestInput.value.trim();

        if (email && isValidEmail(email)) {
            // Generate random avatar ID (1-30)
            const avatarId = Math.floor(Math.random() * 30) + 1;

            // Create and add guest element
            const guestEl = createGuestElement(email, avatarId);
            document.getElementById('guestList').appendChild(guestEl);

            // Clear input
            guestInput.value = '';
        } else {
            // Show validation error
            alert('لطفا یک آدرس ایمیل معتبر وارد کنید');
        }
    });

    // Validate email function
    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // Handle form submission for new/edited events
    document.getElementById('eventForm').addEventListener('submit', function (e) {
        e.preventDefault();

        // Get form values
        const eventName = document.getElementById('eventNameInput').value;
        const eventDate = document.getElementById('eventDateInput').value;
        const endDate = document.getElementById('endEventDateInput').value;
        const eventTime = document.getElementById('eventTimeInput').value;
        const location = document.getElementById('locationInput').value;

        // Get event ID (if editing)
        const eventId = this.getAttribute('data-event-id');

        // Get selected color
        let color = 'primary'; // Default value
        if (typeof VirtualSelect !== 'undefined') {
            const colorValue = document.querySelector('#ColorSelect').querySelector('.vscomp-value-tag');
            if (colorValue) {
                color = colorValue.getAttribute('data-value') || 'primary';
            }
        }

        // Create start and end dates
        let startDate = new Date(eventDate);
        let endDate_ = new Date(endDate || eventDate);

        if (eventTime) {
            const [hours, minutes] = eventTime.split(':');
            startDate.setHours(parseInt(hours), parseInt(minutes));
            endDate_.setHours(parseInt(hours), parseInt(minutes));
        }

        // Collect guests
        const guestElements = document.getElementById('guestList').querySelectorAll('[data-email]');
        const guests = Array.from(guestElements).map(el => {
            const email = el.getAttribute('data-email');
            const imgSrc = el.querySelector('img').src;
            const avatarId = imgSrc.match(/user-(\d+)\.png/) ? parseInt(imgSrc.match(/user-(\d+)\.png/)[1]) : 1;
            return { email, avatarId };
        });

        // Create event data object
        const eventData = {
            title: eventName,
            start: startDate,
            end: endDate_,
            allDay: !eventTime,
            // backgroundColor: color,
            className: 'bg-' + color + ' text-white p-2 rounded-2',
            extendedProps: {
                location: location,
                guests: guests
            }
        };

        // Add event to calendar or update existing event
        if (eventName) {
            if (eventId) {
                // Update existing event
                const existingEvent = calendar.getEventById(eventId);
                if (existingEvent) {
                    // Remove the existing event first
                    existingEvent.remove();
                }
                // Keep the same ID for the updated event
                eventData.id = eventId;
            } else {
                // Generate a new unique ID for new events
                eventData.id = 'رویداد-' + new Date().getTime();
            }

            // Add the event to the calendar
            calendar.addEvent(eventData);

            // Close modal and reset form
            const modal = window.bootstrap.Modal.getInstance(document.getElementById('addEventModal'));
            modal.hide();
            resetEventForm();
        }
    });

    // Add event button handler
    document.getElementById('newEvent').addEventListener('click', function () {
        // Set default date to today
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('eventDateInput').value = today;
        document.getElementById('endEventDateInput').value = today;

        // Reset form and set modal title
        resetEventForm();
        document.getElementById('modalTitle').textContent = 'افزودن رویداد';
        document.getElementById('submitEventBtn').textContent = 'ایجاد رویداد';
        document.getElementById('eventForm').removeAttribute('data-event-id');
    });

    // Initialize the VirtualSelect for color selection if available
    if (typeof VirtualSelect !== 'undefined') {
        VirtualSelect.init({
            ele: "#ColorSelect",
            options: [
                { label: "آبی", value: "primary" },
                { label: "سبز", value: "success" },
                { label: "بنفش", value: "secondary" },
                { label: "فیروزه‌ای", value: "info" }
            ],
            search: false,
            defaultValue: "primary"
        });
    } else {
        console.error('VirtualSelect is not loaded');

        // Fallback to a standard select element if VirtualSelect is not available
        const colorSelectContainer = document.getElementById('ColorSelect');
        if (colorSelectContainer) {
            const selectEl = document.createElement('select');
            selectEl.className = 'form-select';
            selectEl.id = 'ColorSelectFallback';

            const options = [
                { label: "آبی", value: "primary" },
                { label: "سبز", value: "success" },
                { label: "بنفش", value: "secondary" },
                { label: "فیروزه‌ای", value: "info" }
            ];

            options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.label;
                selectEl.appendChild(option);
            });

            colorSelectContainer.parentNode.replaceChild(selectEl, colorSelectContainer);
        }
    }
});