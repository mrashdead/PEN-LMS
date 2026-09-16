import Swiper from 'swiper/bundle';
import 'swiper/css/bundle';

var swiper = new Swiper("#basicSwiper", {
    loop: true,
    spaceBetween: 0,
});

var swiper = new Swiper("#paginationSwiper", {
    pagination: {
        el: ".swiper-pagination",
        dynamicBullets: true,
    },
});

var swiper = new Swiper("#simplepaginationSwiper", {
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
});
var swiper = new Swiper("#verticalSwiper", {
    direction: "vertical",
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
});

var swiper = new Swiper("#grabSwiper", {
    slidesPerView: 4,
    centeredSlides: true,
    spaceBetween: 20,
    grabCursor: true,
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
    breakpoints: {
        375: {
            slidesPerView: 1.5,
            spaceBetween: 20
        },
        557: {
            slidesPerView: 2,
            spaceBetween: 20
        },
        1024: {
            slidesPerView: 3,
            spaceBetween: 20
        },
        1200: {
            slidesPerView: 4,
            spaceBetween: 20
        }
    }
});

var swiper = new Swiper("#slidesSwiper", {
    slidesPerView: 3,
    spaceBetween: 20,
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
    breakpoints: {
        375: {
            slidesPerView: 1.5,
            spaceBetween: 20
        },
        557: {
            slidesPerView: 2,
            spaceBetween: 20
        },
        1024: {
            slidesPerView: 3,
            spaceBetween: 20
        }
    }
});