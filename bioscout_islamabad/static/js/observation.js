document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const observationForm = document.getElementById('observation-form');
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    const removeImageBtn = document.querySelector('.remove-image');
    const fileNameDisplay = document.querySelector('.file-name');
    const closeModal = document.getElementById('close-modal');
    const addObservationNav = document.getElementById('add-observation-nav');
    const observationModal = document.getElementById('observation-modal');
    const locationMap = document.getElementById('location-map');
    const coordinatesInput = document.getElementById('coordinates');
    const coordinatesDisplay = document.getElementById('coordinates-display');
    
    // Tab Navigation
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const nextButtons = document.querySelectorAll('.btn-next');
    const prevButtons = document.querySelectorAll('.btn-prev');
    const progressFill = document.querySelector('.progress-fill');
    const progressStatus = document.querySelector('.progress-status');
    
    // Initialize map for location selection
    let locationSelectionMap = null;
    let locationMarker = null;
    
    // Tab navigation functions
    function showTab(tabId) {
        // Hide all tabs
        tabContents.forEach(content => content.classList.remove('active'));
        tabButtons.forEach(btn => btn.classList.remove('active'));
        
        // Show the selected tab
        document.getElementById(tabId + '-content').classList.add('active');
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
        
        // Update progress bar
        updateProgress(tabId);
    }
    
    function updateProgress(tabId) {
        let progress = 33; // Default to first tab
        let step = 1;
        
        if (tabId === 'species-details') {
            progress = 66;
            step = 2;
        } else if (tabId === 'location-tab') {
            progress = 100;
            step = 3;
        }
        
        progressFill.style.width = `${progress}%`;
        progressStatus.textContent = `Step ${step} of 3`;
    }
    
    // Initialize location selection map
    function initLocationMap() {
        if (locationMap && !locationSelectionMap) {
            locationSelectionMap = L.map('location-map').setView([33.6844, 73.0479], 12);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(locationSelectionMap);
            
            // Add click handler to set marker
            locationSelectionMap.on('click', function(e) {
                setLocationMarker(e.latlng);
            });
            
            // After map is initialized, invalidate size to ensure proper rendering
            setTimeout(() => {
                locationSelectionMap.invalidateSize();
            }, 100);
        }
    }
    
    function setLocationMarker(latlng) {
        if (locationMarker) {
            locationMarker.setLatLng(latlng);
        } else {
            locationMarker = L.marker(latlng).addTo(locationSelectionMap);
        }
        
        // Update hidden input with coordinates
        coordinatesInput.value = JSON.stringify([latlng.lng, latlng.lat]);
        
        // Display coordinates
        coordinatesDisplay.textContent = `Latitude: ${latlng.lat.toFixed(6)}, Longitude: ${latlng.lng.toFixed(6)}`;
        coordinatesDisplay.classList.add('has-coordinates');
    }
    
    // Event Listeners
    
    // Show image preview when file is selected
    imageInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                imagePreview.classList.remove('hidden');
                fileNameDisplay.textContent = imageInput.files[0].name;
            };
            
            reader.readAsDataURL(this.files[0]);
        }
    });
    
    // Remove image button
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            imagePreview.classList.add('hidden');
            imageInput.value = '';
            fileNameDisplay.textContent = 'No file selected';
        });
    }
    
    // Tab button clicks
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            showTab(tabId);
            
            // Initialize map when switching to location tab
            if (tabId === 'location-tab') {
                initLocationMap();
            }
        });
    });
    
    // Next button clicks
    nextButtons.forEach(button => {
        button.addEventListener('click', function() {
            const nextTabId = this.getAttribute('data-next');
            showTab(nextTabId);
            
            // Initialize map when switching to location tab
            if (nextTabId === 'location-tab') {
                initLocationMap();
            }
        });
    });
    
    // Previous button clicks
    prevButtons.forEach(button => {
        button.addEventListener('click', function() {
            const prevTabId = this.getAttribute('data-prev');
            showTab(prevTabId);
        });
    });
    
    // Open modal when "Add Observation" is clicked
    addObservationNav.addEventListener('click', function() {
        observationModal.classList.remove('hidden');
        
        // If on location tab, initialize map
        if (document.getElementById('location-tab-content').classList.contains('active')) {
            initLocationMap();
        }
    });
    
    // Close modal
    closeModal.addEventListener('click', function() {
        observationModal.classList.add('hidden');
        resetForm();
    });
    
    function resetForm() {
        // Reset form fields
        observationForm.reset();
        imagePreview.classList.add('hidden');
        fileNameDisplay.textContent = 'No file selected';
        
        // Reset location marker and coordinates
        if (locationMarker && locationSelectionMap) {
            locationSelectionMap.removeLayer(locationMarker);
            locationMarker = null;
        }
        coordinatesInput.value = '';
        coordinatesDisplay.textContent = '';
        coordinatesDisplay.classList.remove('has-coordinates');
        
        // Reset to first tab
        showTab('basic-info');
    }
    
    // Form validation and submission
    observationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Basic validation
        const image = imageInput.files[0];
        const location = document.getElementById('location').value;
        
        if (!image) {
            alert('Please upload an image');
            showTab('basic-info');
            return;
        }
        
        if (!location) {
            alert('Please enter a location name');
            showTab('location-tab');
            initLocationMap();
            return;
        }
        
        const formData = new FormData(observationForm);
        
        // Add user ID (in production would be from authentication)
        formData.append('user_id', 'user_' + Date.now());
        
        // If coordinates not set but map clicked, grab them from marker
        if (!formData.get('coordinates') && locationMarker) {
            const latlng = locationMarker.getLatLng();
            formData.set('coordinates', JSON.stringify([latlng.lng, latlng.lat]));
        }
        
        // Show loading state
        const submitBtn = document.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = 'Submitting...';
        submitBtn.disabled = true;
        
        // Submit observation
        fetch('/api/observations', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Reset button state
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
            
            if (data.success) {
                // Close modal and reset form
                observationModal.classList.add('hidden');
                resetForm();
                
                // Show success message
                alert('Observation submitted successfully!');
                
                // Reload observations on map
                if (typeof loadObservations === 'function') {
                    loadObservations();
                }
            } else {
                alert('Error: ' + (data.error || 'Failed to submit observation'));
            }
        })
        .catch(error => {
            // Reset button state
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
            
            console.error('Error submitting observation:', error);
            alert('Error submitting observation. Please try again.');
        });
    });
}); 