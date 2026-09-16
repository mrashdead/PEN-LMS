let map;
let geoMap, infoWindow;

function initMap() {

	// ---------------------------------------------------------- basic map ----------------------------------------
	map = new google.maps.Map(document.getElementById("map"), {
		center: { lat: -31.397, lng: 125.644 },
		zoom: 6,
	});
	// ---------------------------------------------------------- geolocation map ----------------------------------------
	geoMap = new google.maps.Map(document.getElementById("geolocation"), {
		center: { lat: -34.397, lng: 150.644 },
		zoom: 6,
	});
	infoWindow = new google.maps.InfoWindow();
	const locationButton = document.createElement("button");

	locationButton.textContent = "Pan to Current Location";
	locationButton.classList.add("custom-map-control-button");
	geoMap.controls[google.maps.ControlPosition.TOP_CENTER].push(locationButton);
	locationButton.addEventListener("click", () => {
		// Try HTML5 geolocation.
		if (navigator.geolocation) {
			navigator.geolocation.getCurrentPosition(
				(position) => {
					const pos = {
						lat: position.coords.latitude,
						lng: position.coords.longitude,
					};

					infoWindow.setPosition(pos);
					infoWindow.setContent("Location found.");
					infoWindow.open(geoMap);
					geoMap.setCenter(pos);
				},
				() => {
					handleLocationError(true, infoWindow, geoMap.getCenter());
				}
			);
		} else {
			// Browser doesn't support Geolocation
			handleLocationError(false, infoWindow, geoMap.getCenter());
		}
	});


	// ---------------------------------------------------------- lat lang map ----------------------------------------
	const langMap = new google.maps.Map(document.getElementById("latlang-map"), {
		zoom: 4,
		center: { lat: -25.363882, lng: 131.044922 },
		mapId: "DEMO_MAP_ID",
	});
	const bounds = {
		north: -25.363882,
		south: -31.203405,
		east: 131.044922,
		west: 125.244141,
	};

	langMap.fitBounds(bounds);

	const secretMessages = ["This", "is", "the", "secret", "message"];
	const lngSpan = bounds.east - bounds.west;
	const latSpan = bounds.north - bounds.south;

	for (let i = 0; i < secretMessages.length; ++i) {
		const marker = new google.maps.Marker({
			// The below line is equivalent to writing:
			position: {
				lat: bounds.south + latSpan * Math.random(),
				lng: bounds.west + lngSpan * Math.random(),
			},
			map: langMap,
		});

		attachSecretMessage(marker, secretMessages[i]);
	}



	const origin = { lat: -33.871, lng: 151.197 };
	const eventMap = new google.maps.Map(document.getElementById("event-map"), {
		zoom: 18,
		center: origin,
	});

	new ClickEventHandler(eventMap, origin);
}

function isIconMouseEvent(e) {
	return "placeId" in e;
}

class ClickEventHandler {
	origin;
	eventMap;
	directionsService;
	directionsRenderer;
	placesService;
	infoWindow;
	infoWindowContent;
	constructor(eventMap, origin) {
		this.origin = origin;
		this.eventMap = eventMap;
		this.directionsService = new google.maps.DirectionsService();
		this.directionsRenderer = new google.maps.DirectionsRenderer();
		this.directionsRenderer.setMap(map);
		this.placesService = new google.maps.places.PlacesService(eventMap);
		this.infoWindow = new google.maps.InfoWindow();
		this.infoWindowContent = document.getElementById("infowindow-content");
		this.infoWindow.setContent(this.infoWindowContent);
		// Listen for clicks on the map.
		this.eventMap.addListener("click", this.handleClick.bind(this));
	}
	handleClick(event) {
		// If the event has a placeId, use it.
		if (isIconMouseEvent(event)) {
			// Calling e.stop() on the event prevents the default info window from
			// showing.
			// If you call stop here when there is no placeId you will prevent some
			// other map click event handlers from receiving the event.
			event.stop();
			if (event.placeId) {
				this.calculateAndDisplayRoute(event.placeId);
				this.getPlaceInformation(event.placeId);
			}
		}
	}
	calculateAndDisplayRoute(placeId) {
		const me = this;
		this.directionsService
			.route({
				origin: this.origin,
				destination: { placeId: placeId },
				travelMode: google.maps.TravelMode.WALKING,
			})
			.then((response) => {
				me.directionsRenderer.setDirections(response);
			})
			.catch((e) => window.alert("Directions request failed due to " + status));
	}
	getPlaceInformation(placeId) {
		const me = this;
		this.placesService.getDetails({ placeId: placeId }, (place, status) => {
			if (
				status === "OK" &&
				place &&
				place.geometry &&
				place.geometry.location
			) {
				me.infoWindow.close();
				me.infoWindow.setPosition(place.geometry.location);
				me.infoWindowContent.children["place-icon"].src = place.icon;
				me.infoWindowContent.children["place-name"].textContent = place.name;
				me.infoWindowContent.children["place-id"].textContent = place.place_id;
				me.infoWindowContent.children["place-address"].textContent =
					place.formatted_address;
				me.infoWindow.open(me.map);
			}
		});
	}
}
// Attaches an info window to a marker with the provided message. When the
// marker is clicked, the info window will open with the secret message.
function attachSecretMessage(marker, secretMessage) {
	const infoWindow = new google.maps.InfoWindow({
		content: secretMessage,
	});
	marker.addListener("click", () => {
		infoWindow.open(marker.map, marker);
	});
}
function handleLocationError(browserHasGeolocation, infoWindow, pos) {
	infoWindow.setPosition(pos);
	infoWindow.setContent(
		browserHasGeolocation
			? "Error: The Geolocation service failed."
			: "Error: Your browser doesn't support geolocation."
	);
	infoWindow.open(geoMap);
}
window.initMap = initMap;