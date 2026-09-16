var softSlider = document.getElementById('withdrawPrice');

noUiSlider.create(softSlider, {
    start: 50,
    range: {
        min: 0,
        max: 100
    },
    pips: {
        mode: 'values',
        values: [20, 80],
        density: 4
    }
});

import IMask from 'imask';

// Get the input element
const accountNumberInput = document.getElementById('accountNumberInput');

// Create the mask
const mask = IMask(accountNumberInput, {
    mask: '0000 0000 0000 0000 000',
    placeholderChar: '_',
    lazy: false,  // Always show the mask pattern
    blocks: {
        '0': {
            mask: IMask.MaskedRange,
            from: 0,
            to: 9
        }
    }
});
