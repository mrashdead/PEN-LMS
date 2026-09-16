// scroll navbar class add
document.addEventListener('DOMContentLoaded', function () {
    const navbar = document.querySelector('#navbarSchool');
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
const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

navLinks.forEach(link => {
    link.addEventListener('click', function () {
        // Remove active class from all nav-links
        navLinks.forEach(nav => nav.classList.remove('active'));
        // Add active class to the clicked nav-link
        this.classList.add('active');
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

//simple parallax
import SimpleParallax from "simple-parallax-js/vanilla";

var image = document.getElementsByClassName('thumbnail');
new SimpleParallax(image, {
    delay: .8,
    spaceBetween: 30,
    transition: 'cubic-bezier(0,0,0,1)',
    overflow: true,
});

//swiper
import Swiper from 'swiper/bundle';
import 'swiper/css/bundle';
var swiper = new Swiper(".review-swiper", {
    loop: true,
    spaceBetween: 30,
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
    autoplay: {
        delay: 2000,
        disableOnInteraction: false,
    },
});