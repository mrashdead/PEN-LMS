var slider = document.getElementById('slider');

noUiSlider.create(slider, {
    start: [20, 80],
    connect: true,
    range: {
        'min': 0,
        'max': 100
    }
});

var valuesSlider = document.getElementById('values-slider');
var valuesForSlider = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32]; // 16 values

var format = {
    to: function (value) {
        return valuesForSlider[Math.round(value)];
    },
    from: function (value) {
        return valuesForSlider.indexOf(Number(value));
    }
};

noUiSlider.create(valuesSlider, {
    start: [8, 24],
    // A linear range from 0 to 15 (16 values)
    range: { min: 0, max: valuesForSlider.length - 1 },
    // steps of 1
    step: 1,
    tooltips: true,
    format: format,
    pips: { mode: 'steps', format: format },
});

valuesSlider.noUiSlider.set(['7', '28']);

var arbitraryValuesSlider = document.getElementById('arbitrary-values-slider');
var arbitraryValuesForSlider = ['128MB', '256MB', '1GB', '8GB', '16GB', '32GB'];

var format = {
    to: function (value) {
        return arbitraryValuesForSlider[Math.round(value)];
    },
    from: function (value) {
        return arbitraryValuesForSlider.indexOf(value);
    }
};

noUiSlider.create(arbitraryValuesSlider, {
    // start values are parsed by 'format'
    start: ['1GB', '16GB'],
    range: { min: 0, max: arbitraryValuesForSlider.length - 1 },
    step: 1,
    tooltips: true,
    format: format,
    pips: { mode: 'steps', format: format, density: 50 },
});

// Initialize the slider
var slider = document.getElementById('color-slider');

// Create the noUiSlider
noUiSlider.create(slider, {
    start: [4000, 8000, 12000, 16000],
    connect: [false, true, true, true, true],
    range: {
        min: [2000],
        max: [20000]
    }
});

// Get the connect elements and apply colors
var connectElements = slider.querySelectorAll('.noUi-connect');
var colorClasses = ['c-1-color', 'c-2-color', 'c-3-color', 'c-4-color', 'c-5-color'];

for (var i = 0; i < connectElements.length; i++) {
    connectElements[i].classList.add(colorClasses[i]);
}

// slider toggle

var toggleSlider = document.getElementById('slider-toggle');

noUiSlider.create(toggleSlider, {
    orientation: "vertical",
    start: 0,
    range: {
        'min': [0, 1],
        'max': 1
    },
    format: wNumb({
        decimals: 0
    })
});

toggleSlider.noUiSlider.on('update', function (values, handle) {
    if (values[handle] === '1') {
        toggleSlider.classList.add('off');
    } else {
        toggleSlider.classList.remove('off');
    }
});

// soft limit
var softSlider = document.getElementById('soft');

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

softSlider.noUiSlider.on('change', function (values, handle) {
    if (values[handle] < 20) {
        softSlider.noUiSlider.set(20);
    } else if (values[handle] > 80) {
        softSlider.noUiSlider.set(80);
    }
});

// overlapping tooltip

var overlappingTooltipSlider = document.getElementById("overlapping-tooltip");
noUiSlider.create(overlappingTooltipSlider, {
    start: [20, 32, 50, 70, 80, 90],
    connect: true,
    tooltips: [false, true, true, true, true, true],
    range: { min: 0, max: 100 }
});

function mergeTooltips(slider, threshold, separator) {

    var textIsRtl = getComputedStyle(slider).direction === 'rtl';
    var isRtl = slider.noUiSlider.options.direction === 'rtl';
    var isVertical = slider.noUiSlider.options.orientation === 'vertical';
    var tooltips = slider.noUiSlider.getTooltips();
    var origins = slider.noUiSlider.getOrigins();

    // Move tooltips into the origin element. The default stylesheet handles this.
    tooltips.forEach(function (tooltip, index) {
        if (tooltip) {
            origins[index].appendChild(tooltip);
        }
    });

    slider.noUiSlider.on('update', function (values, handle, unencoded, tap, positions) {
        var pools = [[]];
        var poolPositions = [[]];
        var poolValues = [[]];
        var atPool = 0;

        // Assign the first tooltip to the first pool, if the tooltip is configured
        if (tooltips[0]) {
            pools[0][0] = 0;
            poolPositions[0][0] = positions[0];
            poolValues[0][0] = values[0];
        }
        for (var i = 1; i < positions.length; i++) {
            if (!tooltips[i] || (positions[i] - positions[i - 1]) > threshold) {
                atPool++;
                pools[atPool] = [];
                poolValues[atPool] = [];
                poolPositions[atPool] = [];
            }
            if (tooltips[i]) {
                pools[atPool].push(i);
                poolValues[atPool].push(values[i]);
                poolPositions[atPool].push(positions[i]);
            }
        }
        pools.forEach(function (pool, poolIndex) {
            var handlesInPool = pool.length;
            for (var j = 0; j < handlesInPool; j++) {
                var handleNumber = pool[j];
                if (j === handlesInPool - 1) {
                    var offset = 0;
                    poolPositions[poolIndex].forEach(function (value) {
                        offset += 1000 - value;
                    });
                    var direction = isVertical ? 'bottom' : 'right';
                    var last = isRtl ? 0 : handlesInPool - 1;
                    var lastOffset = 1000 - poolPositions[poolIndex][last];
                    offset = (textIsRtl && !isVertical ? 100 : 0) + (offset / handlesInPool) - lastOffset;
                    // Center this tooltip over the affected handles
                    tooltips[handleNumber].innerHTML = poolValues[poolIndex].join(separator);
                    tooltips[handleNumber].style.display = 'block';
                    tooltips[handleNumber].style[direction] = offset + '%';
                } else // Hide this tooltip
                    tooltips[handleNumber].style.display = 'none';
            }
        });
    });
}

// color picker

var resultElement = document.getElementById('result');
var sliders = document.querySelectorAll('.sliders');
var colors = [0, 0, 0];

sliders.forEach(function (slider, index) {

    noUiSlider.create(slider, {
        start: 127,
        connect: [true, false],
        orientation: "vertical",
        range: {
            'min': 0,
            'max': 255
        },
        format: wNumb({
            decimals: 0
        })
    });

    // Bind the color changing function to the update event.
    slider.noUiSlider.on('update', function () {

        colors[index] = slider.noUiSlider.get();

        var color = 'rgb(' + colors.join(',') + ')';

        resultElement.style.background = color;
        resultElement.style.color = color;
    });
});