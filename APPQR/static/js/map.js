// Map functionality for GeoPet
let map;
let markerBlue; // Current device position marker
let markerRed;  // QR code position marker
let routeLayer;

// Improved marker icons with custom colors
function createMarkerIcon(color, pulsating = false) {
    const className = pulsating ? 'custom-div-icon pulsating' : 'custom-div-icon';
    
    return L.divIcon({
        className: className,
        html: `<div style="background-color:${color}; width:20px; height:20px; border-radius:50%; border:2px solid white;"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
}

// Initialize the map
function initMap(defaultLat, defaultLng) {
    // Create map
    map = L.map('map', {
        zoomControl: false,
        attributionControl: false
    }).setView([defaultLat, defaultLng], 15);
    
    // Add zoom control to bottom right
    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Add the blue marker for current position
    markerBlue = L.marker([defaultLat, defaultLng], {
        icon: createMarkerIcon('#4e73df', true),
        zIndexOffset: 1000
    }).addTo(map)
        .bindPopup('Tu ubicación actual')
        .openPopup();
    
    // Add custom attribution
    L.control.attribution({
        position: 'bottomleft'
    }).addAttribution('GeoPet &copy; 2025').addTo(map);
    
    // Add click event to the map
    map.on('click', function(e) {
        document.getElementById('latitude').value = e.latlng.lat.toFixed(7);
        document.getElementById('longitude').value = e.latlng.lng.toFixed(7);
        updateLocationDisplay();
        
        // If we're in "current location" mode, update the marker
        markerBlue.setLatLng(e.latlng);
        
        // If there's a QR location, draw route
        if (markerRed) {
            const qrLatLng = markerRed.getLatLng();
            drawRoute(e.latlng.lat, e.latlng.lng, qrLatLng.lat, qrLatLng.lng);
        }
    });
}

// Update the map with new coordinates
function updateMap(lat, lng, qrLat = null, qrLng = null) {
    // Make sure coordinates are valid numbers
    lat = parseFloat(lat);
    lng = parseFloat(lng);
    
    if (isNaN(lat) || isNaN(lng)) {
        console.error("Invalid coordinates:", lat, lng);
        return;
    }
    
    // Make sure map is initialized
    if (!map) {
        initMap(lat, lng);
        return;
    }
    
    // Update blue marker (current location)
    markerBlue.setLatLng([lat, lng]);
    
    // Get QR coordinates from data attributes if not provided
    if (qrLat === null || qrLng === null) {
        const mapContainer = document.getElementById('map');
        if (mapContainer) {
            const dataQrLat = parseFloat(mapContainer.dataset.qrLat);
            const dataQrLng = parseFloat(mapContainer.dataset.qrLng);
            
            if (!isNaN(dataQrLat) && !isNaN(dataQrLng)) {
                qrLat = dataQrLat;
                qrLng = dataQrLng;
            }
        }
    }
    
    // Set map view to show all markers
    if (qrLat !== null && qrLng !== null && !isNaN(qrLat) && !isNaN(qrLng)) {
        // Show the red marker for QR location
        if (!markerRed) {
            // Create marker if it doesn't exist yet
            markerRed = L.marker([qrLat, qrLng], {
                icon: createMarkerIcon('#e74a3b')
            }).addTo(map)
                .bindPopup('Ubicación del código QR');
        } else {
            // Update existing marker
            markerRed.setLatLng([qrLat, qrLng]);
        }
        
        // Draw route between points
        drawRoute(lat, lng, qrLat, qrLng);
        
        // Create bounds to fit both markers
        const bounds = L.latLngBounds([
            [lat, lng],
            [qrLat, qrLng]
        ]);
        
        // Fit map to bounds with padding
        map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 16
        });
    } else {
        // Set view to current location
        map.setView([lat, lng], 15);
    }
    
    // Update info panel if it exists
    updateInfoPanel(lat, lng, qrLat, qrLng);
}

// Manual coordinates search
function searchLocation() {
    const lat = parseFloat(document.getElementById('latitude').value);
    const lng = parseFloat(document.getElementById('longitude').value);
    
    if (isNaN(lat) || isNaN(lng)) {
        alert('Por favor ingrese coordenadas válidas');
        return;
    }
    
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
        alert('Coordenadas fuera de rango. Latitud: -90 a 90, Longitud: -180 a 180');
        return;
    }
    
    // Update the map
    updateMap(lat, lng);
}

// Calculate distance between two points
function calculateDistance(lat1, lon1, lat2, lon2) {
    // Haversine formula to calculate distance between two points on Earth
    const R = 6371; // Radius of the Earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c; // Distance in km
    
    return distance;
}

// Draw route between two points
function drawRoute(lat1, lng1, lat2, lng2) {
    // Remove any existing route
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }
    
    // Remove any existing distance labels
    document.querySelectorAll('.distance-label').forEach(el => {
        if (el._leaflet_id) {
            map.removeLayer(el);
        }
    });
    
    // Create a red dashed line
    const routeCoordinates = [
        [lat1, lng1],
        [lat2, lng2]
    ];
    
    routeLayer = L.polyline(routeCoordinates, {
        color: '#e74a3b',
        weight: 4,
        opacity: 0.7,
        dashArray: '10, 10'
    }).addTo(map);
    
    // Calculate distance
    const distance = calculateDistance(lat1, lng1, lat2, lng2);
    
    // Add distance label
    const midPoint = [
        (lat1 + lat2) / 2,
        (lng1 + lng2) / 2
    ];
    
    // Add distance label on the map
    L.marker(midPoint, {
        icon: L.divIcon({
            className: 'distance-label',
            html: `<div style="background: rgba(0,0,0,0.6); color: white; padding: 5px; border-radius: 5px; font-size: 12px;">${distance.toFixed(2)} km</div>`,
            iconSize: [80, 20],
            iconAnchor: [40, 10]
        })
    }).addTo(map);
    
    // Update distance info in panel if exists
    const distanceInfo = document.getElementById('distance-info');
    if (distanceInfo) {
        distanceInfo.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-route me-2"></i>
                <strong>Distancia:</strong> ${distance.toFixed(2)} km
            </div>
        `;
    }
}

// Update information panel
function updateInfoPanel(lat, lng, qrLat, qrLng) {
    const userLocationInfo = document.getElementById('user-location-info');
    const qrLocationInfo = document.getElementById('qr-location-info');
    
    if (userLocationInfo) {
        userLocationInfo.innerHTML = `
            <p><span class="marker-blue"></span> <strong>Tu ubicación actual:</strong><br>
            Latitud: ${lat.toFixed(7)}, Longitud: ${lng.toFixed(7)}</p>
        `;
    }
    
    if (qrLocationInfo && qrLat && qrLng) {
        qrLocationInfo.innerHTML = `
            <p><span class="marker-red"></span> <strong>Ubicación del código QR:</strong><br>
            Latitud: ${qrLat.toFixed(7)}, Longitud: ${qrLng.toFixed(7)}</p>
        `;
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Get map container
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        return; // Not on the map page
    }
    
    // Add pulsating effect for markers
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }
        .pulsating div {
            animation: pulse 1.5s infinite;
        }
    `;
    document.head.appendChild(style);
    
    // Get search button
    const searchBtn = document.getElementById('search-location');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchLocation);
    }
    
    // Get default coordinates from the page
    const defaultLat = parseFloat(mapContainer.dataset.lat || 0);
    const defaultLng = parseFloat(mapContainer.dataset.lng || 0);
    const qrLat = parseFloat(mapContainer.dataset.qrLat || null);
    const qrLng = parseFloat(mapContainer.dataset.qrLng || null);
    const scannerLat = parseFloat(mapContainer.dataset.scannerLat || null);
    const scannerLng = parseFloat(mapContainer.dataset.scannerLng || null);
    
    // Use scanner location if available, otherwise get current location
    if (!isNaN(scannerLat) && !isNaN(scannerLng)) {
        // Use scanner location from data attributes
        initMap(scannerLat, scannerLng);
        
        // Update form fields
        document.getElementById('latitude').value = scannerLat.toFixed(7);
        document.getElementById('longitude').value = scannerLng.toFixed(7);
        updateLocationDisplay();
        
        // If we have QR coordinates, show both
        if (!isNaN(qrLat) && !isNaN(qrLng)) {
            updateMap(scannerLat, scannerLng, qrLat, qrLng);
        }
    } else {
        // Get current location
        getCurrentLocation((lat, lng) => {
            // Initialize map with current location
            initMap(lat, lng);
            
            // Update form fields
            document.getElementById('latitude').value = lat.toFixed(7);
            document.getElementById('longitude').value = lng.toFixed(7);
            updateLocationDisplay();
            
            // If we have QR coordinates, show both
            if (!isNaN(qrLat) && !isNaN(qrLng)) {
                updateMap(lat, lng, qrLat, qrLng);
            }
        });
    }
}); 