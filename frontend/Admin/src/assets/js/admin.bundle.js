/*
Template Name: Domiex - Admin & Dashboard Template
Author: Spring Code
Version: 1.0.0
File: admin bundle Js File
*/

import 'simplebar';
import 'simplebar/dist/simplebar.css';
import * as bootstrap from 'bootstrap'

import { createIcons, icons } from 'lucide';

window.bootstrap = bootstrap;

createIcons({ icons });

window.addEventListener('load', () => {
    setTimeout(() => {
        createIcons({ icons });
    }, 0);
});

// Function to handle the follow/unfollow logic
function handleFollowUnfollow(button) {
    const spinner = button.querySelector('.spinner-border');
    spinner.style.display = 'inline-block';

    setTimeout(() => {
        spinner.style.display = 'none';

        const followText = button.querySelector('.follow-text');
        const unfollowText = button.querySelector('.unfollow-text');

        if (followText.style.display === 'none') {
            followText.style.display = 'inline';
            unfollowText.style.display = 'none';
        } else {
            followText.style.display = 'none';
            unfollowText.style.display = 'inline';
        }
    }, 1000);
}

document.querySelectorAll('.follow-btn').forEach((button) => {
    button.addEventListener('click', () => handleFollowUnfollow(button));
});

//Counter number js
document.addEventListener('DOMContentLoaded', function () {
    function animatedCounter(counterElement) {
        const start = parseFloat(counterElement.getAttribute('data-start'));
        const end = parseFloat(counterElement.getAttribute('data-end'));
        const duration = parseFloat(counterElement.getAttribute('data-duration'));

        let current = start;
        const difference = end - start;
        const startTime = performance.now();

        function updateCounter() {
            const currentTime = performance.now();
            const elapsedTime = currentTime - startTime;

            const progress = Math.min(elapsedTime / duration, 1);
            current = start + difference * progress;
            counterElement.textContent = Math.round(current).toLocaleString();

            if (progress < 1)
                requestAnimationFrame(updateCounter);
            else
                counterElement.textContent = end.toLocaleString();
        }
        updateCounter();
    }
    // Initialize the counter animation for all elements with the class "counter"
    const counters = document.querySelectorAll('.counter');
    counters.forEach(counter => {
        animatedCounter(counter);
    });

    // Bootstrap tooltip init
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new window.bootstrap.Tooltip(tooltipTriggerEl))

    // Bootstrap popover init
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new window.bootstrap.Popover(popoverTriggerEl))
});

// current Year footer
function displayCurrentYear() {
    try {
        const currentYear = new Date().getFullYear();
        const footerElement = document.getElementById('currentYearFooter');

        if (footerElement) {
            footerElement.textContent = currentYear;
        }
    } catch (error) {
        console.error('Error in displayCurrentYear:', error);
    }
}

document.addEventListener('DOMContentLoaded', displayCurrentYear);
displayCurrentYear();