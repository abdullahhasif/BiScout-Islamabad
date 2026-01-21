// Global function to submit queries from elsewhere (like map markers)
window.submitQuery = function(query) {
    const queryInput = document.getElementById('query-input');
    if (queryInput) {
        queryInput.value = query;
        // Find and click the submit button
        const submitButton = document.querySelector('#query-form button');
        if (submitButton) {
            submitButton.click();
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    const queryForm = document.getElementById('query-form');
    const queryInput = document.getElementById('query-input');
    const queryResults = document.getElementById('query-results');
    const resultsContent = document.getElementById('results-content');
    const closeResults = document.getElementById('close-results');
    
    // Click event for example tags
    document.querySelectorAll('.example-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            const query = this.getAttribute('data-query');
            queryInput.value = query;
            queryForm.dispatchEvent(new Event('submit'));
        });
    });
    
    // Handle query submission
    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;
        
        // Show loading indicator
        resultsContent.innerHTML = '<p>Processing your query...</p>';
        queryResults.classList.remove('hidden');
        
        // Check for direct map filter commands in natural language
        const mapFilterQuery = parseMapFilterQuery(query);
        if (mapFilterQuery) {
            console.log("Detected map filter query:", mapFilterQuery);
            // Directly filter the map based on the query
            filterMapByQuery(mapFilterQuery);
            
            // Show a simplified response
            const targetType = mapFilterQuery.species || mapFilterQuery.type || mapFilterQuery.category || 'all';
            const response = `Showing ${targetType} observations on the map.`;
            displaySimpleResponse(query, response);
            return;
        }
        
        // Submit query to API for normal RAG processing
        fetch('/api/queries', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        })
        .then(response => response.json())
        .then(data => {
            // Display response
            displayQueryResults(data, query);
            
            // Update map with observations if available
            if (data.observations && data.observations.length > 0) {
                updateMapWithQueryResults(data.observations);
            } else {
                // If no specific observations returned, try to extract filter from query
                const extractedFilter = extractFilterFromQuery(query);
                if (extractedFilter) {
                    console.log("Extracted filter from query:", extractedFilter);
                    fetchAndFilterObservations(extractedFilter);
                }
            }
        })
        .catch(error => {
            console.error('Error processing query:', error);
            resultsContent.innerHTML = '<p>Error processing your query. Please try again.</p>';
            
            // Even on error, try to see if we can extract a filter
            const extractedFilter = extractFilterFromQuery(query);
            if (extractedFilter) {
                fetchAndFilterObservations(extractedFilter);
            }
        });
    });
    
    // Close results panel
    closeResults.addEventListener('click', function() {
        queryResults.classList.add('hidden');
        // Reset map to show all observations
        if (window.loadObservations) {
            loadObservations();
        }
    });
    
    // Parse query to determine if it's a direct map filter command
    function parseMapFilterQuery(query) {
        query = query.toLowerCase();
        
        // Match patterns like "show me all plants" or "display birds on map"
        const showPatterns = [
            /show\s+(?:me\s+)?(?:all\s+)?(.+?)(?:\s+on\s+(?:the\s+)?map)?$/i,
            /display\s+(?:all\s+)?(.+?)(?:\s+on\s+(?:the\s+)?map)?$/i,
            /find\s+(?:all\s+)?(.+?)(?:\s+on\s+(?:the\s+)?map)?$/i,
            /where\s+(?:are\s+)(?:the\s+)?(.+?)(?:\s+on\s+(?:the\s+)?map)?$/i,
            /map\s+(?:of\s+)?(.+?)$/i,
            /locate\s+(?:all\s+)?(.+?)(?:\s+on\s+(?:the\s+)?map)?$/i
        ];
        
        for (const pattern of showPatterns) {
            const match = query.match(pattern);
            if (match) {
                const target = match[1].trim();
                
                // Check for category filters (plants/animals)
                if (target === 'plants' || target === 'plant') {
                    return { category: 'plant' };
                } else if (target === 'animals' || target === 'animal') {
                    return { category: 'animal' };
                }
                
                // Check for type filters
                const types = ['mammal', 'bird', 'reptile', 'fish', 'amphibian', 'tree'];
                const pluralTypeMappings = {
                    'mammals': 'mammal',
                    'birds': 'bird', 
                    'reptiles': 'reptile',
                    'fishes': 'fish',
                    'amphibians': 'amphibian',
                    'trees': 'tree'
                };
                
                if (types.includes(target)) {
                    return { type: target };
                }
                
                // Handle plural forms
                if (pluralTypeMappings[target]) {
                    return { type: pluralTypeMappings[target] };
                }
                
                // Check for specific species from our data
                const knownSpecies = [
                    'chir pine', 'blue pine', 'himalayan cedar', 'amaltas', 'paper mulberry',
                    'wild date palm', 'neem', 'bottle brush', 'shisham', 'tulsi',
                    'leopard', 'barking deer', 'pangolin', 'mallard duck', 'cobra',
                    'griffon', 'fox', 'bear', 'boar', 'jackal', 'mongoose', 'marten',
                    'owlet', 'treepie', 'flying fox'
                ];
                
                // Exact match with known species
                if (knownSpecies.includes(target)) {
                    return { species: target };
                }
                
                // Check for partial matches with known species
                for (const species of knownSpecies) {
                    if (species.includes(target) || target.includes(species)) {
                        return { species: species };
                    }
                }
                
                // If it's not a category or type, it might be a specific species
                return { species: target };
            }
        }
        
        return null;
    }
    
    // Extract filter information from a general query
    function extractFilterFromQuery(query) {
        query = query.toLowerCase();
        
        // Try to match specific species first - these have higher priority
        const knownSpecies = [
            'chir pine', 'blue pine', 'himalayan cedar', 'amaltas', 'paper mulberry',
            'wild date palm', 'neem', 'bottle brush', 'shisham', 'tulsi',
            'leopard', 'barking deer', 'pangolin', 'mallard', 'duck', 'cobra',
            'griffon', 'fox', 'bear', 'boar', 'jackal', 'mongoose', 'marten',
            'owlet', 'treepie', 'flying fox'
        ];
        
        // Look for exact species names in the query
        for (const species of knownSpecies) {
            if (query.includes(species)) {
                return { species: species };
            }
        }
        
        // Check for category keywords
        if (query.includes('plant') || query.includes('tree') || query.includes('flora')) {
            return { category: 'plant' };
        } else if (query.includes('animal') || query.includes('mammal') || 
                  query.includes('bird') || query.includes('reptile') || 
                  query.includes('wildlife') || query.includes('fauna')) {
            return { category: 'animal' };
        }
        
        // Check for type keywords
        const typeKeywords = {
            'mammal': ['mammal', 'fox', 'bear', 'deer', 'leopard'],
            'bird': ['bird', 'duck', 'eagle', 'owl', 'vulture'],
            'reptile': ['reptile', 'snake', 'cobra', 'lizard'],
            'fish': ['fish'],
            'amphibian': ['amphibian', 'frog', 'toad'],
            'tree': ['pine', 'cedar', 'oak', 'neem']
        };
        
        for (const [type, keywords] of Object.entries(typeKeywords)) {
            if (keywords.some(keyword => query.includes(keyword))) {
                return { type: type };
            }
        }
        
        // Look for single-word species references
        const words = query.split(/\s+/);
        for (const word of words) {
            if (word.length > 3 && !['what', 'where', 'when', 'how', 'about', 'tell', 'show', 'find', 'many', 'much', 'there', 'they', 'their', 'these', 'those', 'some', 'most', 'more'].includes(word)) {
                // Check if this word is part of a known species name
                for (const species of knownSpecies) {
                    if (species.includes(word)) {
                        return { species: species };
                    }
                }
                return { species: word };
            }
        }
        
        return null;
    }
    
    // Fetch and filter observations based on extracted filter
    function fetchAndFilterObservations(filter) {
        let endpoint = '/api/observations';
        const params = [];
        
        if (filter.category) {
            params.push(`category=${filter.category}`);
        }
        
        if (filter.type) {
            params.push(`type=${filter.type}`);
        }
        
        if (filter.species) {
            params.push(`species=${filter.species}`);
        }
        
        if (params.length > 0) {
            endpoint += '?' + params.join('&');
        }
        
        console.log("Fetching observations with endpoint:", endpoint);
        
        fetch(endpoint)
            .then(response => response.json())
            .then(data => {
                if (data.observations && data.observations.length > 0) {
                    console.log(`Found ${data.observations.length} matching observations`);
                    // Filter map to show these observations
                    showFilteredObservationsOnMap(data.observations);
                    
                    // Update results content
                    const filterType = filter.species || filter.type || filter.category || 'matching';
                    const message = `Found ${data.observations.length} ${filterType} observations on the map.`;
                    const currentContent = resultsContent.innerHTML;
                    
                    if (currentContent.includes('Processing')) {
                        resultsContent.innerHTML = `<p>${message}</p>`;
                    } else {
                        resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid #2e7d32;"><p>${message}</p></div>`;
                    }
                } else {
                    console.log("No matching observations found");
                    if (resultsContent.innerHTML.includes('Processing')) {
                        resultsContent.innerHTML = `<p>No matching observations found for "${filter.species || filter.type || filter.category}".</p>`;
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching observations:', error);
            });
    }
    
    // Filter map directly based on query
    function filterMapByQuery(filter) {
        // Call appropriate map filter function if available
        if (filter.species && window.filterObservationsBySpecies) {
            console.log(`Calling window.filterObservationsBySpecies with: ${filter.species}`);
            window.filterObservationsBySpecies(filter.species);
            
            // Add message to results content
            const filterType = filter.species || '';
            resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid #8BC34A;">
                <p>Showing ${filterType} observations on the map.</p>
            </div>`;
            return;
        }
        
        if (filter.category && window.filterObservationsByCategory) {
            console.log(`Calling window.filterObservationsByCategory with: ${filter.category}`);
            window.filterObservationsByCategory(filter.category);
            
            // Add message to results content
            const filterType = filter.category === 'plant' ? 'plant' : 'animal';
            resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid #8BC34A;">
                <p>Showing all ${filterType} observations on the map.</p>
            </div>`;
            return;
        }
        
        if (filter.type && window.filterObservationsByCategory) {
            // For type filters, we need to fetch all observations and filter on the client side
            console.log(`Filtering by type: ${filter.type}`);
            fetch('/api/observations')
                .then(response => response.json())
                .then(data => {
                    if (data.observations && data.observations.length > 0) {
                        // Filter observations by type
                        const typeObservations = data.observations.filter(obs => {
                            if (window.getSpeciesType) {
                                const obsType = window.getSpeciesType(obs.species_name || '');
                                return obsType === filter.type;
                            }
                            return false;
                        });
                        
                        // If we have matching observations and the showFilteredObservationsOnMap function
                        if (typeObservations.length > 0) {
                            if (window.markerLayer && window.map && window.getSpeciesType && window.markerIcons) {
                                console.log(`Found ${typeObservations.length} observations of type ${filter.type}`);
                                showFilteredObservationsOnMap(typeObservations);
                                
                                // Add message to results content
                                resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid #8BC34A;">
                                    <p>Found ${typeObservations.length} ${filter.type} observations on the map.</p>
                                </div>`;
                            } else {
                                console.error("Required map functions not available");
                                resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #ffebee; border-radius: 4px; border-left: 3px solid #f44336;">
                                    <p>Error: Map interface not available. Please reload the page.</p>
                                </div>`;
                            }
                        } else {
                            console.log("No matching observations found");
                            resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid #ff9800;">
                                <p>No ${filter.type} observations found on the map.</p>
                            </div>`;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching observations:', error);
                    resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #ffebee; border-radius: 4px; border-left: 3px solid #f44336;">
                        <p>Error loading observations. Please try again.</p>
                    </div>`;
                });
            return;
        }
        
        // If no direct functions available, fall back to API endpoint
        console.log("Fallback to API endpoint filtering");
        let endpoint = '/api/observations';
        const params = [];
        
        if (filter.category) {
            params.push(`category=${filter.category}`);
        }
        
        if (filter.type) {
            params.push(`type=${filter.type}`);
        }
        
        if (filter.species) {
            params.push(`species=${filter.species}`);
        }
        
        if (params.length > 0) {
            endpoint += '?' + params.join('&');
        }
        
        console.log("Filtering map with endpoint:", endpoint);
        
        fetch(endpoint)
            .then(response => response.json())
            .then(data => {
                if (data.observations && data.observations.length > 0) {
                    console.log(`Found ${data.observations.length} matching observations`);
                    showFilteredObservationsOnMap(data.observations);
                    
                    // Add message to results content
                    const filterType = filter.species || filter.type || filter.category || '';
                    resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid #8BC34A;">
                        <p>Found ${data.observations.length} ${filterType} observations on the map.</p>
                    </div>`;
                } else {
                    console.log("No matching observations found");
                    resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid #ff9800;">
                        <p>No matching observations found on the map.</p>
                    </div>`;
                }
            })
            .catch(error => {
                console.error('Error fetching observations:', error);
                resultsContent.innerHTML += `<div style="margin-top: 15px; padding: 10px; background-color: #ffebee; border-radius: 4px; border-left: 3px solid #f44336;">
                    <p>Error loading observations. Please try again.</p>
                </div>`;
            });
    }
    
    // Show filtered observations on map
    function showFilteredObservationsOnMap(observations) {
        if (window.markerLayer && window.markerIcons && window.getSpeciesType) {
            // Clear existing markers
            window.markerLayer.clearLayers();
            
            // Add markers for each observation
            observations.forEach(obs => {
                if (obs.coordinates && obs.coordinates.length === 2) {
                    const type = window.getSpeciesType(obs.species_name || '');
                    const icon = window.markerIcons[type] || window.markerIcons.default;
                    
                    const marker = L.marker(
                        [obs.coordinates[1], obs.coordinates[0]], 
                        { icon: icon }
                    );
                    
                    // Create popup content
                    const popupContent = `
                        <div class="popup-content">
                            <h3>${obs.species_name || 'Unknown Species'}</h3>
                            <p><strong>Location:</strong> ${obs.location || 'Unknown Location'}</p>
                            <p><strong>Date:</strong> ${new Date(obs.date_observed).toLocaleDateString()}</p>
                            ${obs.notes ? `<p><strong>Notes:</strong> ${obs.notes}</p>` : ''}
                            <p><strong>Type:</strong> <span style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; color: white; background-color: #2e7d32;">${type.charAt(0).toUpperCase() + type.slice(1)}</span></p>
                            <button style="background-color: #2e7d32; color: white; border: none; padding: 8px 12px; margin-top: 10px; border-radius: 4px; cursor: pointer; width: 100%;" 
                                    onclick="window.submitQuery('Tell me about ${obs.species_name}')">
                                Learn more about this species
                            </button>
                        </div>
                    `;
                    
                    marker.bindPopup(popupContent);
                    marker.properties = obs;
                    marker.properties.type = type;
                    
                    window.markerLayer.addLayer(marker);
                }
            });
            
            // Fit map to bounds if markers exist
            if (window.markerLayer.getLayers().length > 0) {
                const group = L.featureGroup(window.markerLayer.getLayers());
                window.map.fitBounds(group.getBounds().pad(0.1));
            }
        }
    }
    
    // Display a simple response for direct filter queries
    function displaySimpleResponse(query, response) {
        let html = `
            <div style="margin-bottom: 15px; font-style: italic; color: #666; border-left: 3px solid #2e7d32; padding-left: 10px;">
                <strong>Your request:</strong> "${query}"
            </div>
            <div>
                <p>${response}</p>
            </div>
        `;
        
        resultsContent.innerHTML = html;
    }
    
    // Display query results in the panel
    function displayQueryResults(data, originalQuery) {
        let html = '';
        
        // Show what system answered the query (LlamaIndex or simple fallback)
        if (data.using_fallback) {
            html += `<div style="margin-bottom: 10px;">
                <span style="display: inline-block; background-color: #ff9800; color: white; font-size: 12px; padding: 3px 8px; border-radius: 10px;">Simple RAG</span>
            </div>`;
        }
        
        // Show original query
        html += `<div style="margin-bottom: 15px; font-style: italic; color: #666; border-left: 3px solid #2e7d32; padding-left: 10px;">
            <strong>Your question:</strong> "${originalQuery}"
        </div>`;
        
        // Display main response
        html += `<div style="margin-bottom: 15px; line-height: 1.6;">
            <p>${data.response}</p>
        </div>`;
        
        // If there are observations, list them
        if (data.observations && data.observations.length > 0) {
            html += `<div style="margin-top: 15px;">
                <h4>Related Observations (${data.observations.length})</h4>
                <p>Observations have been highlighted on the map.</p>
                <ul style="list-style-type: circle; margin-left: 20px; color: #555; font-size: 14px;">`;
                
            // Show up to 3 observation summaries
            data.observations.slice(0, 3).forEach(obs => {
                if (obs.properties) {
                    html += `<li>${obs.properties.species} at ${obs.properties.location}</li>`;
                }
            });
            
            html += `</ul>
            </div>`;
        } else {
            // Try to extract filter from query if no observations were returned
            const filter = extractFilterFromQuery(originalQuery);
            if (filter) {
                html += `<div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid #2196f3;">
                    <p>Looking for ${filter.species || filter.type || filter.category || ''} observations on the map...</p>
                </div>`;
            }
        }
        
        // List knowledge sources
        if (data.knowledge_sources && data.knowledge_sources.length > 0) {
            html += `<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0;">
                <h4>Information Sources:</h4>
                <ul style="padding-left: 20px; font-size: 13px; color: #666;">`;
                
            data.knowledge_sources.forEach(source => {
                html += `<li>${source}</li>`;
            });
            
            html += `</ul>
            </div>`;
        }
        
        resultsContent.innerHTML = html;
    }
    
    // Update map with query results
    function updateMapWithQueryResults(observations) {
        // Clear existing markers
        if (window.markerLayer) {
            window.markerLayer.clearLayers();
        
            // Add new markers based on query results
            observations.forEach(observation => {
                if (observation.geometry && observation.geometry.coordinates) {
                    const coords = observation.geometry.coordinates;
                    const props = observation.properties;
                    
                    const type = window.getSpeciesType ? window.getSpeciesType(props.species || '') : 'default';
                    const icon = window.markerIcons ? window.markerIcons[type] || window.markerIcons.default : null;
                    
                    const marker = L.marker(
                        [coords[1], coords[0]], 
                        icon ? { icon: icon } : {}
                    ).bindPopup(createObservationPopup(props));
                    
                    marker.properties = props;
                    marker.properties.type = type; // Store type for filtering
                    window.markerLayer.addLayer(marker);
                }
            });
            
            // If there are markers, fit the map to their bounds
            if (window.markerLayer.getLayers().length > 0) {
                const group = L.featureGroup(window.markerLayer.getLayers());
                window.map.fitBounds(group.getBounds().pad(0.1));
            }
        }
    }
    
    // Create popup content for observation from query results
    function createObservationPopup(props) {
        let content = `
            <div class="popup-content">
                <h3>${props.species || 'Unknown Species'}</h3>
                <p><strong>Location:</strong> ${props.location || 'Unknown Location'}</p>
        `;
        
        if (props.date) {
            content += `<p><strong>Date:</strong> ${new Date(props.date).toLocaleDateString()}</p>`;
        }
        
        if (props.notes) {
            content += `<p><strong>Notes:</strong> ${props.notes}</p>`;
        }
        
        // Type label if available
        const type = window.getSpeciesType ? window.getSpeciesType(props.species || '') : null;
        if (type) {
            content += `<p><strong>Type:</strong> <span style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; color: white; background-color: #2e7d32;">${type.charAt(0).toUpperCase() + type.slice(1)}</span></p>`;
        }
        
        // Add button to query RAG about this species
        content += `
            <button style="background-color: #2e7d32; color: white; border: none; padding: 8px 12px; margin-top: 10px; border-radius: 4px; cursor: pointer; width: 100%;" 
                    onclick="window.submitQuery('Tell me about ${props.species}')">
                Learn more about this species
            </button>
        `;
        
        content += '</div>';
        
        return content;
    }
}); 