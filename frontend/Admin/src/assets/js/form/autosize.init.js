// Get references to the textarea and character count element
const textarea = document.getElementById('message');
const charCount = document.getElementById('charCount');

function autoResize() {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function updateCharCount() {
    const currentLength = textarea.value.length;
    charCount.textContent = currentLength;
}

// Add event listeners
textarea.addEventListener('input', () => {
    autoResize();
    updateCharCount();
});
