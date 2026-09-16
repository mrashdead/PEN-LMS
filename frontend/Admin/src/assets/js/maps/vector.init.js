function vectorMap() {
  document.getElementById("basicMap").innerHTML = '';
  const map = new jsVectorMap({
    selector: "#basicMap",
    map: "world",
    onRegionTipShow: function (e, el, code) {
      // Customize tooltip content based on the region code
      const tooltipContent = regionsData[code] || el.data('name');
      el.html(tooltipContent);
    },
  });
}

vectorMap();
window.addEventListener('resize', vectorMap);

// Markers
function handleResizeMarker() {
  document.getElementById("markersMap").innerHTML = '';
  const markersMap = new jsVectorMap({
    selector: "#markersMap",

    map: "world",
    markers: [{ coords: [-14.235, -51.9253] }, { coords: [35.8617, 104.1954] }],
    selectedMarkers: [0],
  });
}

handleResizeMarker();
window.addEventListener('resize', handleResizeMarker);

//Image Marker
function imageMarkersMapFun() {
  document.getElementById("imageMarkersMap").innerHTML = '';
  const imageMarkersMap = new jsVectorMap({
    selector: "#imageMarkersMap",
    map: "world",
    markers: [
      {
        name: "Egypt",
        coords: [26.8206, 30.8025],
        style: {
          initial: {
            image: "assets/images/others/pin.png", // Add a marker image for this particular marker.
          }
        }
      },
      {
        name: "United States",
        coords: [37.0902, -95.7129],
        style: {
          initial: {
            image: "assets/images/others/pin.png", // Add a marker image for this particular marker.
          }
        }
      },
      {
        name: "United Kingdom",
        coords: [55.3781, 3.436],
        style: {
          initial: {
            image: "assets/images/others/pin.png", // Add a marker image for this particular marker.
          }
        }
      },
    ],
  });
}

imageMarkersMapFun();
window.addEventListener('resize', imageMarkersMapFun);

// line style
function lineMapFun() {
  document.getElementById("lineStyleMap").innerHTML = '';
  const lineMap = new jsVectorMap({
    selector: "#lineStyleMap",
    map: "world",
    lineStyle: {
      stroke: "#676767",
      strokeWidth: 1.5,
      fill: "#ff5566",
      fillOpacity: 1,
      strokeDasharray: "6 3 6", // OR: [6, 2, 6]
      animation: true, // Enables animation
    },
    markers: [
      {
        name: "Brazil",
        coords: [-14.235, -51.9253], // Brazil coordinates
        style: { fill: "red" },
      },
      {
        name: "Greenland",
        coords: [71.7069, -42.6043],
        style: { fill: "green" },
      },
      {
        name: "Egypt",
        coords: [26.8206, 30.8025],
        style: { fill: "blue" },
      },
      {
        name: "United States",
        coords: [37.0902, -95.7129],
        style: { fill: "purple" },
      },
      {
        name: "Norway",
        coords: [60.472, 8.4689],
        style: { fill: "yellow" },
      },
    ],
  });

  // Avoid this in the future versions.
  lineMap.addLines([
    { from: "Brazil", to: "Greenland" },
    { from: "Greenland", to: "Egypt" },
    { from: "Egypt", to: "United States" },
    { from: "United States", to: "Norway" },
    { from: "Norway", to: "Brazil" },
  ]);
  // tooltip map
}

lineMapFun();
window.addEventListener('resize', lineMapFun);

function tooltipFun() {
  document.getElementById("tooltipMap").innerHTML = '';
  const tooltip = new jsVectorMap({
    selector: "#tooltipMap",
    map: "world",
    onRegionTooltipShow(event, tooltip, code) {
      tooltip.text(
        `<h6 class="mb-2">${tooltip.text()} - کشور</h6>` +
        `<p class="text-xs">با اسپرینگ کد تجربه کاربری بهتری داشته باشید.</p>`,
        true // Enables HTML
      );
    },
  });
}

tooltipFun();
window.addEventListener('resize', tooltipFun);

// data series
function dataSeriesFun() {
  document.getElementById("dataSeriesMap").innerHTML = '';
  const dataSeries = new jsVectorMap({
    selector: "#dataSeriesMap",
    map: "world",
    // Notice: you should declare a list of markers to apply series configuration.
    markers: [
      { coords: [61, 105] },
      { coords: [72, -42] },
      { coords: [56, -106] },
      { coords: [31.5, 34.8] },
      { coords: [-14.235, -51.9253] },
      { coords: [35.8617, 104.1954] },
    ],
    series: {
      markers: [
        {
          attribute: "fill",
          legend: {
            title: "چیزی (نشانگر)",
          },
          scale: {
            mScale1: "#ffc371",
            mScale2: "#c79efd",
          },
          values: {
            // Notice: the key must be a number of the marker.
            0: "mScale1",
            1: "mScale2",
            2: "mScale2",
          },
        },
      ],
    },
  });
}

dataSeriesFun();
window.addEventListener('resize', dataSeriesFun);

// user location
function userLocationMapFun() {
  document.getElementById("userLocationMap").innerHTML = '';
  const userLocationMap = new jsVectorMap({
    selector: '#userLocationMap',
    map: 'world',
    onRegionTipShow: function (e, el, code) {
      const regionName = el.html();
      el.html(regionName); // Show region name on hover
    },
    async onLoaded(map) {
      // Fetch location data from ipinfo.io
      const response = await fetch('https://ipinfo.io/geo');
      const data = await response.json();

      // Store location data for later use
      const city = data.city;
      const country = data.country; // Country code (e.g., 'IN')
      const ip = data.ip;

      // "Find My Location" button event listener
      const button = document.querySelector('#request-location');
      button.addEventListener('click', async () => {
        // Clear previous markers if needed
        map.removeMarkers();

        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(async (position) => {
            // Get user's coordinates
            const coords = [position.coords.latitude, position.coords.longitude];
            // Format the name as '• City-CountryCode(IP)'
            const locationName = `• ${city}-${country}(${ip})`;
            // Add marker for user's location with the formatted name
            map.addMarkers({
              coords: coords,
              name: locationName // Use the formatted location name directly with the marker
            });
          }, (error) => {
            console.error('Error getting location: ', error);
            alert('بازیابی موقعیت مکانی شما امکان‌پذیر نیست.');
          });
        } else {
          alert('موقعیت جغرافیایی توسط این مرورگر پشتیبانی نمی‌شود.');
        }
      });
      // "Clear Location" button event listener
      document.querySelector('#clear-location').addEventListener('click', () => {
        map.removeMarkers(); // Clear all markers
      });
    }
  });
}

userLocationMapFun();
window.addEventListener('resize', userLocationMapFun);