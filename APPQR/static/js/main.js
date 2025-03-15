// GeoPet Main JavaScript

// Get current location with better error handling
function getCurrentLocation(callback) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const accuracy = position.coords.accuracy;
                callback(lat, lng, accuracy);
            },
            (error) => {
                console.error("Error getting location:", error);
                
                let errorMsg = "No se pudo obtener tu ubicación.";
                
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorMsg = "Permiso de ubicación denegado. Por favor, activa la ubicación en tu dispositivo.";
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMsg = "La información de ubicación no está disponible en este momento.";
                        break;
                    case error.TIMEOUT:
                        errorMsg = "Se agotó el tiempo de espera para obtener la ubicación.";
                        break;
                    case error.UNKNOWN_ERROR:
                        errorMsg = "Ocurrió un error desconocido al obtener la ubicación.";
                        break;
                }
                
                // Default values for Mexico City (as a fallback)
                callback(19.4326, -99.1332, 1000);
                
                // Show error message in a more user-friendly way if possible
                const locationAlert = document.getElementById('location-alert');
                if (locationAlert) {
                    locationAlert.textContent = errorMsg;
                    locationAlert.style.display = 'block';
                } else {
                    console.warn(errorMsg); // Usar console.warn en lugar de alert para no interrumpir el flujo
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 15000, // Aumentado a 15 segundos para dispositivos más lentos
                maximumAge: 60000 // Permitir caché de ubicación de 1 minuto para mejor rendimiento
            }
        );
    } else {
        console.error("Geolocation is not supported by this browser.");
        callback(19.4326, -99.1332, 1000); // Default to Mexico City
        alert("Tu navegador no soporta geolocalización. Por favor ingresa tu ubicación manualmente.");
    }
}

// Fill location inputs with current location
function fillLocationInputs() {
    const latInput = document.getElementById('latitude');
    const lngInput = document.getElementById('longitude');
    
    if (latInput && lngInput) {
        // Show loading indicator if available
        const locationLoading = document.getElementById('location-loading');
        if (locationLoading) locationLoading.style.display = 'block';
        
        getCurrentLocation((lat, lng, accuracy) => {
            latInput.value = lat.toFixed(7);
            lngInput.value = lng.toFixed(7);
            
            // Hide loading indicator
            if (locationLoading) locationLoading.style.display = 'none';
            
            // If we're on the map page, update the map
            if (typeof updateMap === 'function') {
                updateMap(lat, lng);
            }
            
            // Update location display
            updateLocationDisplay();
        });
    }
}

// Update location value display
function updateLocationDisplay() {
    const latInput = document.getElementById('latitude');
    const lngInput = document.getElementById('longitude');
    const latDisplay = document.getElementById('lat-display');
    const lngDisplay = document.getElementById('lng-display');
    
    if (latInput && latDisplay) {
        latDisplay.textContent = latInput.value;
    }
    
    if (lngInput && lngDisplay) {
        lngDisplay.textContent = lngInput.value;
    }
}

// Initialize form elements
function initForms() {
    // Get location button
    const getLocationBtn = document.getElementById('get-location');
    if (getLocationBtn) {
        getLocationBtn.addEventListener('click', fillLocationInputs);
    }
    
    // Location inputs
    const latInput = document.getElementById('latitude');
    const lngInput = document.getElementById('longitude');
    
    if (latInput && lngInput) {
        // Update display when inputs change
        latInput.addEventListener('input', updateLocationDisplay);
        lngInput.addEventListener('input', updateLocationDisplay);
    }
    
    // Initialize location on page load if needed
    const autoLocationPages = ['generate_qr', 'scan_qr', 'map_view'];
    const currentPage = document.body.dataset.page;
    
    if (autoLocationPages.includes(currentPage)) {
        fillLocationInputs();
    }
}

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initForms();
    
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Add page transition effect
    document.body.classList.add('page-loaded');
}); 