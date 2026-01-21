// Initialize map centered on Islamabad
let map = L.map('map').setView([33.6844, 73.0479], 11);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Store markers for filtering
let markers = [];
let markerLayer = L.layerGroup().addTo(map);

// Expose map to global scope for query.js to access
window.map = map;
window.markerLayer = markerLayer;
window.markers = markers;

// Custom icons for different species types
const markerIcons = {
    bird: L.divIcon({
        className: 'custom-marker marker-bird',
        html: '<span>B</span>',
        iconSize: [30, 30]
    }),
    mammal: L.divIcon({
        className: 'custom-marker marker-mammal',
        html: '<span>M</span>',
        iconSize: [30, 30]
    }),
    reptile: L.divIcon({
        className: 'custom-marker marker-reptile',
        html: '<span>R</span>',
        iconSize: [30, 30]
    }),
    fish: L.divIcon({
        className: 'custom-marker marker-fish',
        html: '<span>F</span>',
        iconSize: [30, 30]
    }),
    amphibian: L.divIcon({
        className: 'custom-marker marker-amphibian',
        html: '<span>A</span>',
        iconSize: [30, 30]
    }),
    plant: L.divIcon({
        className: 'custom-marker marker-plant',
        html: '<span>P</span>',
        iconSize: [30, 30]
    }),
    tree: L.divIcon({
        className: 'custom-marker marker-tree',
        html: '<span>T</span>',
        iconSize: [30, 30]
    }),
    default: L.divIcon({
        className: 'custom-marker',
        html: '<span>•</span>',
        iconSize: [30, 30]
    })
};

// Expose markerIcons to global scope for query.js
window.markerIcons = markerIcons;

// Function to determine species type
function getSpeciesType(speciesName) {
    // This is a simplified logic - in production would use a more comprehensive classification
    speciesName = speciesName.toLowerCase();
    
    if (speciesName.includes('bird') || speciesName.includes('duck') || 
        speciesName.includes('eagle') || speciesName.includes('vulture') ||
        speciesName.includes('griffon') || speciesName.includes('owl') || 
        speciesName.includes('treepie')) {
        return 'bird';
    } else if (speciesName.includes('deer') || speciesName.includes('leopard') || 
               speciesName.includes('fox') || speciesName.includes('jackal') || 
               speciesName.includes('boar') || speciesName.includes('monkey') ||
               speciesName.includes('bear') || speciesName.includes('pangolin') ||
               speciesName.includes('mongoose') || speciesName.includes('marten') || 
               speciesName.includes('flying fox')) {
        return 'mammal';
    } else if (speciesName.includes('snake') || speciesName.includes('cobra') || 
               speciesName.includes('viper') || speciesName.includes('lizard')) {
        return 'reptile';
    } else if (speciesName.includes('fish') || speciesName.includes('carp')) {
        return 'fish';
    } else if (speciesName.includes('frog') || speciesName.includes('toad') ||
              speciesName.includes('amphibian')) {
        return 'amphibian';
    } else if (speciesName.includes('pine') || speciesName.includes('cedar') || 
              speciesName.includes('oak') || speciesName.includes('himalayan') ||
              speciesName.includes('mulberry') || speciesName.includes('date palm') ||
              speciesName.includes('neem') || speciesName.includes('shisham')) {
        return 'tree';
    } else if (speciesName.includes('flower') || speciesName.includes('herb') || 
              speciesName.includes('plant') || speciesName.includes('shrub') ||
              speciesName.includes('amaltas') || speciesName.includes('botanical') || 
              speciesName.includes('tulsi') || speciesName.includes('bottle brush')) {
        return 'plant';
    }
    
    return 'default';
}

// Expose getSpeciesType to global scope for query.js
window.getSpeciesType = getSpeciesType;

// Load initial observations
function loadObservations() {
    console.log("Loading all observations...");
    fetch('/api/observations')
        .then(response => response.json())
        .then(data => {
            // Clear existing markers
            markerLayer.clearLayers();
            markers = [];
            
            // Add markers for each observation with coordinates
            data.observations.forEach(observation => {
                if (observation.coordinates && observation.coordinates.length === 2) {
                    addObservationMarker(observation);
                }
            });
            
            // Create and add filter controls
            createFilterControls();
        })
        .catch(error => console.error('Error loading observations:', error));
}

// Create filter controls for the map
function createFilterControls() {
    // Check if we've already added filters
    if (document.querySelector('.filter-controls')) return;
    
    // Create filter container
    const filterContainer = document.createElement('div');
    filterContainer.className = 'filter-controls';
    
    // Add category selector
    const categorySelector = document.createElement('div');
    categorySelector.className = 'category-selector';
    
    const categoryLabel = document.createElement('div');
    categoryLabel.className = 'filter-section-title';
    categoryLabel.textContent = 'Category:';
    categorySelector.appendChild(categoryLabel);
    
    const categoryOptions = ['all', 'plants', 'animals'];
    const categoryButtons = document.createElement('div');
    categoryButtons.className = 'filter-button-group';
    
    categoryOptions.forEach(option => {
        const button = document.createElement('button');
        button.className = 'category-button';
        button.dataset.category = option;
        button.textContent = option.charAt(0).toUpperCase() + option.slice(1);
        
        if (option === 'all') {
            button.classList.add('active');
        }
        
        button.addEventListener('click', () => {
            // Remove active class from all category buttons
            document.querySelectorAll('.category-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Load observations for selected category
            loadObservationsByCategory(option);
        });
        
        categoryButtons.appendChild(button);
    });
    
    categorySelector.appendChild(categoryButtons);
    filterContainer.appendChild(categorySelector);
    
    // Add type filter section
    const typeFilterSection = document.createElement('div');
    typeFilterSection.className = 'type-filter-section';
    
    const filterTitle = document.createElement('div');
    filterTitle.className = 'filter-section-title';
    filterTitle.textContent = 'Filter By Type:';
    typeFilterSection.appendChild(filterTitle);
    
    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'filter-button-group';
    
    // Add filter buttons (dependent on selected category)
    updateTypeFilterButtons(buttonContainer, 'all');
    
    typeFilterSection.appendChild(buttonContainer);
    filterContainer.appendChild(typeFilterSection);
    
    // Add to map
    document.querySelector('.map-container').appendChild(filterContainer);
    
    // Make the filter controls draggable
    makeDraggable(filterContainer);
}

// Make an element draggable
function makeDraggable(element) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    
    // Mouse events
    element.addEventListener('mousedown', dragMouseDown);
    
    // Touch events
    element.addEventListener('touchstart', dragTouchStart, { passive: false });
    
    function dragMouseDown(e) {
        e.preventDefault();
        // Get the mouse cursor position at startup
        pos3 = e.clientX;
        pos4 = e.clientY;
        
        element.classList.add('dragging');
        
        // Call functions on mouse move and mouse up
        document.addEventListener('mousemove', elementDrag);
        document.addEventListener('mouseup', closeDragElement);
    }
    
    function dragTouchStart(e) {
        e.preventDefault();
        // Get the touch position
        const touch = e.touches[0];
        pos3 = touch.clientX;
        pos4 = touch.clientY;
        
        element.classList.add('dragging');
        
        // Call functions on touch move and touch end
        document.addEventListener('touchmove', elementTouchDrag, { passive: false });
        document.addEventListener('touchend', closeTouchDragElement);
    }
    
    function elementDrag(e) {
        e.preventDefault();
        // Calculate the new cursor position
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        
        updateElementPosition();
    }
    
    function elementTouchDrag(e) {
        e.preventDefault();
        // Calculate the new touch position
        const touch = e.touches[0];
        pos1 = pos3 - touch.clientX;
        pos2 = pos4 - touch.clientY;
        pos3 = touch.clientX;
        pos4 = touch.clientY;
        
        updateElementPosition();
    }
    
    function updateElementPosition() {
        // Set the element's new position
        const newTop = element.offsetTop - pos2;
        const newLeft = element.offsetLeft - pos1;
        
        // Keep the element within the map container boundaries
        const container = document.querySelector('.map-container');
        const maxLeft = container.clientWidth - element.offsetWidth;
        const maxTop = container.clientHeight - element.offsetHeight;
        
        element.style.top = Math.max(0, Math.min(newTop, maxTop)) + 'px';
        element.style.left = Math.max(0, Math.min(newLeft, maxLeft)) + 'px';
    }
    
    function closeDragElement() {
        // Stop moving when mouse button is released
        element.classList.remove('dragging');
        document.removeEventListener('mousemove', elementDrag);
        document.removeEventListener('mouseup', closeDragElement);
    }
    
    function closeTouchDragElement() {
        // Stop moving when touch ends
        element.classList.remove('dragging');
        document.removeEventListener('touchmove', elementTouchDrag);
        document.removeEventListener('touchend', closeTouchDragElement);
    }
}

// Load observations by category (all, plants, animals)
function loadObservationsByCategory(category) {
    console.log(`Loading observations by category: ${category}`);
    const apiEndpoint = category === 'all' 
        ? '/api/observations' 
        : `/api/observations?category=${category.slice(0, -1)}`; // Remove 's' at the end
    
    fetch(apiEndpoint)
        .then(response => response.json())
        .then(data => {
            // Clear existing markers
            markerLayer.clearLayers();
            markers = [];
            
            // Add markers for each observation with coordinates
            data.observations.forEach(observation => {
                if (observation.coordinates && observation.coordinates.length === 2) {
                    addObservationMarker(observation);
                }
            });
            
            // Update type filter buttons based on selected category
            const buttonContainer = document.querySelector('.filter-button-group:last-child');
            updateTypeFilterButtons(buttonContainer, category);
            
            // Reset to "All" type filter
            filterMarkers(null);
            
            // Fit map to bounds if markers exist
            if (markers.length > 0) {
                const group = L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
            }
        })
        .catch(error => console.error(`Error loading ${category} observations:`, error));
}

// Update type filter buttons based on selected category
function updateTypeFilterButtons(container, category) {
    // Clear existing buttons
    container.innerHTML = '';
    
    // Define button types based on category
    let types = ['all'];
    
    if (category === 'all' || category === 'animals') {
        types = types.concat(['mammal', 'bird', 'reptile', 'amphibian', 'fish']);
    }
    
    if (category === 'all' || category === 'plants') {
        types = types.concat(['tree', 'plant']);
    }
    
    // Add buttons
    types.forEach(type => {
        const button = document.createElement('button');
        button.className = 'filter-button';
        button.dataset.type = type;
        button.textContent = type === 'all' ? 'All Types' : type.charAt(0).toUpperCase() + type.slice(1);
        
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            document.querySelectorAll('.filter-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Apply filter
            filterMarkers(type === 'all' ? null : type);
        });
        
        // Set 'All' as active by default
        if (type === 'all') {
            button.classList.add('active');
        }
        
        container.appendChild(button);
    });
}

// Add marker for a single observation
function addObservationMarker(observation) {
    const type = getSpeciesType(observation.species_name || '');
    const icon = markerIcons[type] || markerIcons.default;
    
    const marker = L.marker(
        [observation.coordinates[1], observation.coordinates[0]], 
        { icon: icon }
    ).bindPopup(createPopupContent(observation));
    
    marker.properties = observation;
    marker.properties.type = type; // Store type for filtering
    markers.push(marker);
    markerLayer.addLayer(marker);
}

// Create popup content for observation marker
function createPopupContent(observation) {
    let content = `
        <div class="popup-content">
            <h3>${observation.species_name || 'Unknown Species'}</h3>
            <p><strong>Location:</strong> ${observation.location || 'Unknown Location'}</p>
            <p><strong>Date:</strong> ${new Date(observation.date_observed).toLocaleDateString()}</p>
    `;
    
    if (observation.image_url) {
        content += `<img src="${observation.image_url}" class="popup-image" alt="${observation.species_name}">`;
    }
    
    if (observation.notes) {
        content += `<p><strong>Notes:</strong> ${observation.notes}</p>`;
    }
    
    // Add type label
    const type = getSpeciesType(observation.species_name || '');
    content += `<p><strong>Type:</strong> <span style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; color: white; background-color: #2e7d32;">${type.charAt(0).toUpperCase() + type.slice(1)}</span></p>`;
    
    // Add button to query RAG about this species
    content += `
        <button style="background-color: #2e7d32; color: white; border: none; padding: 8px 12px; margin-top: 10px; border-radius: 4px; cursor: pointer; width: 100%;" 
                onclick="window.submitQuery('Tell me about ${observation.species_name}')">
            Learn more about this species
        </button>
    `;
    
    content += '</div>';
    
    return content;
}

// Filter markers based on species type
function filterMarkers(type) {
    markerLayer.clearLayers();
    let visibleMarkers = [];
    
    markers.forEach(marker => {
        if (!type || marker.properties.type === type) {
            markerLayer.addLayer(marker);
            visibleMarkers.push(marker);
        }
    });
    
    // Fit map to bounds if markers are filtered
    if (visibleMarkers.length > 0 && type) {
        const group = L.featureGroup(visibleMarkers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Initialize map for location selection in the modal
let locationMap = null;
let locationMarker = null;

function initLocationMap() {
    if (locationMap) return;
    
    // Create map for location selection
    locationMap = L.map('location-map').setView([33.6844, 73.0479], 11);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(locationMap);
    
    // Add click event for location selection
    locationMap.on('click', function(e) {
        if (locationMarker) {
            locationMap.removeLayer(locationMarker);
        }
        
        locationMarker = L.marker(e.latlng).addTo(locationMap);
        
        // Store coordinates in hidden field
        document.getElementById('coordinates').value = JSON.stringify([e.latlng.lng, e.latlng.lat]);
    });
}

// Event delegation for dynamically created popup buttons
document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('ask-about-species')) {
        const speciesName = e.target.dataset.species;
        if (speciesName) {
            // Use the query.js function to ask about this species
            if (window.submitQuery) {
                window.submitQuery(`Tell me about ${speciesName} in Islamabad`);
            }
        }
    }
});

// Function to filter observations by species for the query system
window.filterObservationsBySpecies = function(species) {
    console.log(`Filtering observations by species: ${species}`);
    fetch(`/api/observations?species=${species}`)
        .then(response => response.json())
        .then(data => {
            // Clear existing markers
            markerLayer.clearLayers();
            markers = [];
            
            // Add markers for each observation with coordinates
            data.observations.forEach(observation => {
                if (observation.coordinates && observation.coordinates.length === 2) {
                    addObservationMarker(observation);
                }
            });
            
            // Fit map to bounds if markers exist
            if (markers.length > 0) {
                const group = L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
                
                // Flash the markers to make the transition more visible
                flashMarkers();
            }
        })
        .catch(error => console.error(`Error filtering by species ${species}:`, error));
};

// Function to filter observations by category for the query system
window.filterObservationsByCategory = function(category) {
    console.log(`Filtering observations by category: ${category}`);
    fetch(`/api/observations?category=${category}`)
        .then(response => response.json())
        .then(data => {
            // Clear existing markers
            markerLayer.clearLayers();
            markers = [];
            
            // Add markers for each observation with coordinates
            data.observations.forEach(observation => {
                if (observation.coordinates && observation.coordinates.length === 2) {
                    addObservationMarker(observation);
                }
            });
            
            // Fit map to bounds if markers exist
            if (markers.length > 0) {
                const group = L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
                
                // Flash the markers to make the transition more visible
                flashMarkers();
            }
        })
        .catch(error => console.error(`Error filtering by category ${category}:`, error));
};

// Function to flash markers to make transitions more visible
function flashMarkers() {
    // Add a flash class to all markers
    document.querySelectorAll('.custom-marker').forEach(marker => {
        marker.classList.add('marker-flash');
        setTimeout(() => {
            marker.classList.remove('marker-flash');
        }, 1000);
    });
}

// Load observations when page loads
document.addEventListener('DOMContentLoaded', loadObservations);

// Initialize modal maps when modal opens
document.getElementById('add-observation-nav').addEventListener('click', function() {
    document.getElementById('observation-modal').classList.remove('hidden');
    setTimeout(initLocationMap, 300); // Delay to ensure container is visible
}); 