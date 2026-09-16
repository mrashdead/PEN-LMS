document.getElementById('wordInput').addEventListener('input', function () {
    const text = this.value.trim();
    const words = text.split(/\s+/).filter(word => word.length > 0);
    const chars = text.replace(/\s+/g, '').length;

    document.getElementById('wordCount').textContent = words.length;
    document.getElementById('charCount').textContent = chars;
});
