//category Select
VirtualSelect.init({
    ele: "#categorySelect",
    options: [
        { label: "مد", value: "Fashion" },
        { label: "میوه‌ها", value: "fruits" },
        { label: "کفش", value: "Footwear" },
        { label: "کیف", value: "Bags" },
        { label: "ساعت", value: "Watch" },
    ],
    categorySelect: true,
    allowNewOption: true,
});

//Brand Select
VirtualSelect.init({
    ele: "#brandTypeSelect",
    options: [
        { label: "گوچی", value: "Gucci" },
        { label: "رولکس", value: "Rolex" },
        { label: "کالوین کلین", value: "Calvin Klein" },
        { label: "زارا", value: "Zara" },
        { label: "نایک", value: "Nike" },
        { label: "آدیداس", value: "Adidas" },
    ],
    brandTypeSelect: true,
    allowNewOption: true,
});

//Size Select
VirtualSelect.init({
    ele: "#sizeSelect",
    options: [
        { label: "XS", value: "XS" },
        { label: "S", value: "S" },
        { label: "M", value: "M" },
        { label: "L", value: "L" },
        { label: "XL", value: "XL" },
        { label: "2XL", value: "2XL" },
    ],
    multiple: true,
    showValueAsTags: true,
});

//Color select
VirtualSelect.init({
    ele: "#colorsSelect",
    options: [
        { label: "آبی", value: "Blue" },
        { label: "سبز", value: "Green" },
        { label: "زرد", value: "Yellow" },
        { label: "آسمانی", value: "Sky" },
        { label: "قرمز", value: "Red" },
        { label: "صورتی", value: "Pink" },
        { label: "خاکستری", value: "Gray" },
        { label: "بنفش", value: "Purple" },
    ],
    multiple: true,
});

import Swiper from 'swiper/bundle';
import 'swiper/css/bundle';

//Product Slider Swiper
var swiper = new Swiper(".productSlider", {
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
});

//Product Size 
document.addEventListener('DOMContentLoaded', function() {
    const sizeLinks = document.querySelectorAll('.product-size a');
    
    sizeLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            sizeLinks.forEach(el => {
                el.classList.remove('active', 'text-success');
                el.classList.add('text-muted');
            });
            
            this.classList.add('active', 'text-success');
            this.classList.remove('text-muted');
        });
    });
});

//Pricing & Sale 
document.addEventListener('DOMContentLoaded', function() {
    const priceInput = document.getElementById('priceInput');
    const discountInput = document.getElementById('discountInput');
    const sellingPriceInput = document.getElementById('sellingPrice');
    
    function sanitizeInput(input) {
        return input.replace(/[^0-9.]/g, '');
    }
    
    function calculateSellingPrice() {
        const price = parseFloat(priceInput.value) || 0;
        const discount = parseFloat(discountInput.value) || 0;
        
        if (discount > 100) {
            discountInput.value = 100;
            return calculateSellingPrice();
        }
        
        const sellingPrice = price * (1 - discount / 100);
        sellingPriceInput.value = sellingPrice.toFixed(2);
    }
    
    priceInput.addEventListener('input', function() {
        this.value = sanitizeInput(this.value);
        calculateSellingPrice();
    });
    
    discountInput.addEventListener('input', function() {
        this.value = sanitizeInput(this.value);
        calculateSellingPrice();
    });
    
    // Initial
    calculateSellingPrice();
});