// scroll navbar class add
document.addEventListener('DOMContentLoaded', function () {
    const navbar = document.querySelector('#navbarEcommerce');
    const scrollThreshold = 100;

    function handleNavbarScroll() {
        if (window.scrollY > scrollThreshold)
            navbar.classList.add('scroll-sticky');
        else
            navbar.classList.remove('scroll-sticky');
    }

    let isScrolling;
    window.addEventListener('scroll', function () {
        window.clearTimeout(isScrolling);
        isScrolling = setTimeout(handleNavbarScroll, 50);
    }, false);

    handleNavbarScroll();
});

//dark mode toggle
document.addEventListener("DOMContentLoaded", function () {
    var toggleButton = document.getElementById("theme-toggle-btn");
    var moonIcon = document.getElementById("moon-icon");
    var sunIcon = document.getElementById("sun-icon");

    var savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);

    moonIcon.style.display = (savedTheme === 'light') ? 'block' : 'none';
    sunIcon.style.display = (savedTheme === 'dark') ? 'block' : 'none';

    toggleButton.addEventListener("click", function () {
        var currentTheme = document.documentElement.getAttribute('data-bs-theme');
        var newTheme = (currentTheme === 'dark') ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        moonIcon.style.display = (newTheme === 'light') ? 'block' : 'none';
        sunIcon.style.display = (newTheme === 'dark') ? 'block' : 'none';
    });
});

//product grid
document.addEventListener('DOMContentLoaded', function () {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', function () {
            // Remove active class from all links
            navLinks.forEach(nav => nav.classList.remove('active'));

            // Add active class to the clicked link
            this.classList.add('active');
        });
    });

    const filterButtons = document.querySelectorAll('#filterTabs .nav-link');

    filterButtons.forEach(button => {
        button.addEventListener('click', function () {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            const filterCategory = this.id.replace('Products', '').toLowerCase();
            filterProducts(filterCategory);
        });
    });

    function filterProducts(category) {
        const productColumns = document.querySelectorAll('.row.g-8 > [data-category]');

        productColumns.forEach(column => {
            if (category === 'all') {
                column.style.display = 'block';
            } else {
                const productCategory = column.getAttribute('data-category');
                column.style.display = productCategory === category ? 'block' : 'none';
            }

            const currentLayout = document.querySelector('.product-toolbar a.active').id;
            updateColumnLayout(currentLayout);
        });
    }

    const layoutButtons = document.querySelectorAll('.product-toolbar a');

    layoutButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();

            layoutButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            updateColumnLayout(this.id);
        });
    });

    function updateColumnLayout(layoutId) {
        const productColumns = document.querySelectorAll('.row.g-8 > [data-category]');

        productColumns.forEach(column => {
            column.classList.remove('col-xxl-3', 'col-xxl-4');

            if (layoutId === 'columnsFour')
                column.classList.add('col-xxl-3');
            else if (layoutId === 'columnsThree')
                column.classList.add('col-xxl-4');
        });
    }

    filterProducts('all');
    updateColumnLayout('columnsFour');
});


//before after Images
const sic = new SlickImageCompare('#beforeAfterImages');