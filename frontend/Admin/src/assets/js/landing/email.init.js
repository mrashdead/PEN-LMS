// scroll navbar class add
document.addEventListener('DOMContentLoaded', function () {
    const navbar = document.querySelector('#navbarEmail');
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
// Select all nav links
const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

// Click event
navLinks.forEach(link => {
    link.addEventListener('click', function () {
        navLinks.forEach(nav => nav.classList.remove('active'));
        this.classList.add('active');
    });
});

// Scroll event
window.addEventListener('scroll', function () {
    let scrollPos = window.scrollY + 100; // adjust "100" if needed

    navLinks.forEach(link => {
        const section = document.querySelector(link.getAttribute('href'));
        if (section) {
            if (scrollPos >= section.offsetTop && scrollPos < section.offsetTop + section.offsetHeight) {
                navLinks.forEach(nav => nav.classList.remove('active'));
                link.classList.add('active');
            }
        }
    });
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