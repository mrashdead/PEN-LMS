import "vanilla-tilt/dist/vanilla-tilt";

document.addEventListener("DOMContentLoaded", function() {
    // Set the target date to 15th December 2028
    const targetDate = new Date("December 15, 2028 00:00:00").getTime();

    function startCountdown() {
        const interval = setInterval(function() {
            const now = new Date().getTime();
            const distance = targetDate - now;

            // If the countdown is over, stop it
            if (distance < 0) {
                clearInterval(interval);
                document.getElementById("comingSoonCountDown").innerHTML = "<h3>رویداد شروع شد!</h3>";
                return;
            }

            // Calculate days, hours, minutes, and seconds
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            // Update the displayed values
            document.getElementById("days").textContent = String(days).padStart(2, '0');
            document.getElementById("hours").textContent = String(hours).padStart(2, '0');
            document.getElementById("minutes").textContent = String(minutes).padStart(2, '0');
            document.getElementById("seconds").textContent = String(seconds).padStart(2, '0');
        }, 1000);
    }

    startCountdown();
});