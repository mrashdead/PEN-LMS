class ProgressCircle {
    constructor(element) {
        this.element = element;
        this.value = parseInt(element.getAttribute('data-value')) || 0;
        this.size = parseInt(element.getAttribute('data-size')) || 100;
        this.color = element.getAttribute('data-color') || '#0d6efd';
        this.text = element.getAttribute('data-text');
        this.strokeWidth = element.hasAttribute('data-stroke-width') 
            ? parseInt(element.getAttribute('data-stroke-width')) 
            : 6;
        this.bgStrokeWidth = element.hasAttribute('data-bg-stroke-width')
            ? parseInt(element.getAttribute('data-bg-stroke-width'))
            : this.strokeWidth; // Defaults to same as stroke-width
        this.bgColor = element.getAttribute('data-bg-color') || '#eee';
        
        this.init();
        this.animate();
    }
    
    init() {
        const radius = (this.size / 2) - (Math.max(this.strokeWidth, this.bgStrokeWidth) / 2);
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (this.value / 100) * circumference;
        
        this.element.style.width = `${this.size}px`;
        this.element.style.height = `${this.size}px`;
        
        this.element.innerHTML = `
            <svg width="${this.size}" height="${this.size}" viewBox="0 0 ${this.size} ${this.size}">
                ${this.bgStrokeWidth > 0 ? 
                    `<circle class="progress-bg" 
                        cx="${this.size/2}" 
                        cy="${this.size/2}" 
                        r="${radius}" 
                        stroke="${this.bgColor}" 
                        stroke-width="${this.bgStrokeWidth}"/>` 
                    : ''}
                <circle class="progress-fill" 
                        cx="${this.size/2}" 
                        cy="${this.size/2}" 
                        r="${radius}" 
                        stroke="${this.color}" 
                        stroke-width="${this.strokeWidth}" 
                        stroke-dasharray="${circumference}" 
                        stroke-dashoffset="${circumference}"/>
            </svg>
            <div class="progress-text">
                <div class="progress-text-inner">
                    <div class="animate-count">0%</div>
                    ${this.text ? `<div class="small">${this.text}</div>` : ''}
                </div>
            </div>
        `;
        
        this.fillElement = this.element.querySelector('.progress-fill');
        this.countElement = this.element.querySelector('.animate-count');
        this.radius = radius;
        this.circumference = circumference;
        this.offset = offset;
    }
    
    animate() {
        setTimeout(() => {
            this.fillElement.style.strokeDashoffset = this.offset;
            
            let start = 0;
            const end = this.value;
            const duration = 1000;
            const increment = end / (duration / 16);
            
            const timer = setInterval(() => {
                start += increment;
                if (start >= end) {
                    start = end;
                    clearInterval(timer);
                }
                this.countElement.textContent = Math.round(start) + '%';
            }, 16);
        }, 100);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.progress-circle').forEach(element => {
        new ProgressCircle(element);
    });
});