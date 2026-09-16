// Key Moments functionality
let seconds = 0;
let timerInterval;

function formatTime(totalSeconds) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;

    return [
        hours.toString().padStart(2, '0'),
        minutes.toString().padStart(2, '0'),
        secs.toString().padStart(2, '0')
    ].join(':');
}

function updateTimer() {
    seconds++;
    document.getElementById('videoCallTime').textContent = formatTime(seconds);
}
timerInterval = setInterval(updateTimer, 1000);

// Pin functionality
document.getElementById('addPin').addEventListener('click', function () {
    const noteText = document.getElementById('newPinText').value.trim();
    const currentTime = formatTime(seconds);

    if (noteText) {
        const keyMomentsContainer = document.getElementById('keyMoments');

        const newPin = document.createElement('a');
        newPin.href = '#!';
        newPin.className = 'd-flex gap-3 align-items-center text-muted';

        const timeElement = document.createElement('p');
        timeElement.className = 'w-28';
        timeElement.textContent = currentTime;

        const textElement = document.createElement('p');
        textElement.textContent = noteText;

        newPin.appendChild(timeElement);
        newPin.appendChild(textElement);

        keyMomentsContainer.appendChild(newPin);

        document.getElementById('newPinText').value = '';
        newPin.scrollIntoView({ behavior: 'smooth' });
    }
});

document.getElementById('newPinText').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        document.getElementById('addPin').click();
    }
});