import 'tippy.js/dist/tippy.css';
import 'tippy.js/animations/scale.css';
import 'tippy.js/animations/scale-subtle.css';
import 'tippy.js/animations/shift-away.css';
import 'tippy.js/animations/shift-toward.css';
import 'tippy.js/animations/perspective.css';

tippy('#hover', {
    interactive: true,
    content: 'این یک تولتیپ است',
});
tippy('#click-me', {
    trigger: 'click',
    content: 'این یک تولتیپ است',
});
tippy('#mouseenter', {
    content: 'این یک تولتیپ است',
});
tippy('#follow-cursor', {
    followCursor: true,
    content: 'این یک تولتیپ است',
});
tippy('#cursor-horizontal', {
    followCursor: 'vertical',
    content: 'این یک تولتیپ است',
});
tippy('#cursor-initial', {
    followCursor: 'initial',
    content: 'این یک تولتیپ است',
});

tippy('#arrowless', {
    content: 'این یک تولتیپ است',
    arrow: false,
});

tippy('#no-flip', {
    content: 'این یک تولتیپ است',
    animation: 'no-flip',
    placement: 'left',
});

tippy('#scale', {
    content: 'این یک تولتیپ است',
    animation: 'scale',
});
tippy('#scale-subtle', {
    content: 'این یک تولتیپ است',
    animation: 'scale-subtle',
});
tippy('#scale-extreme', {
    content: 'این یک تولتیپ است',
    animation: 'scale-extreme',
});

tippy('#top', {
    content: 'این یک تولتیپ است',
    placement: 'top',
});
tippy('#top-start', {
    content: 'این یک تولتیپ است',
    placement: 'top-start',
});
tippy('#top-end', {
    content: 'این یک تولتیپ است',
    placement: 'top-end',
});
tippy('#right', {
    content: 'این یک تولتیپ است',
    placement: 'right',
});
tippy('#right-start', {
    content: 'این یک تولتیپ است',
    placement: 'right-start',
});
tippy('#right-end', {
    content: 'این یک تولتیپ است',
    placement: 'right-end',
});
tippy('#bottom', {
    content: 'این یک تولتیپ است',
    placement: 'bottom',
});
tippy('#bottom-start', {
    content: 'این یک تولتیپ است',
    placement: 'bottom-start',
});
tippy('#bottom-end', {
    content: 'این یک تولتیپ است',
    placement: 'bottom-end',
});
tippy('#left', {
    content: 'این یک تولتیپ است',
    placement: 'left',
});
tippy('#left-start', {
    content: 'این یک تولتیپ است',
    placement: 'left-start',
});
tippy('#left-end', {
    content: 'این یک تولتیپ است',
    placement: 'left-end',
});

const messageInput = document.getElementById('message-input');
const messageText = document.getElementById('message-text');
const tooltipBtn = document.getElementById('tooltip-btn');

// Update message text when input changes
messageInput.addEventListener('input', function() {
    messageText.textContent = messageInput.value || 'Hello, world!';
});
tippy(tooltipBtn, {
    content: () => messageText,
    allowHTML: true,
    appendTo: document.body,
});