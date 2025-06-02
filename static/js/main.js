// Main JavaScript for TripAI Flask Application

// Global variables
let currentTrip = null;
let isGeneratingTrip = false;

// Utility Functions
function showAlert(message, type = 'info', duration = 5000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.dynamic-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show dynamic-alert`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '80px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Loading overlay
function showLoadingOverlay(message = 'Processing...') {
    const existingOverlay = document.getElementById('loadingOverlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>${message}</p>
        </div>
    `;
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        color: white;
        text-align: center;
    `;
    
    document.body.appendChild(overlay);
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Trip Planning Functions
function initTripPlanner() {
    const tripForm = document.getElementById('tripPlannerForm');
    if (!tripForm) return;
    
    tripForm.addEventListener('submit', handleTripSubmission);
    
    // Initialize date pickers
    initDatePickers();
    
    // Initialize location autocomplete
    initLocationAutocomplete();
    
    // Initialize budget slider
    initBudgetSlider();
}

function handleTripSubmission(e) {
    e.preventDefault();
    
    if (isGeneratingTrip) {
        showAlert('Please wait while we generate your current trip plan', 'warning');
        return;
    }
    
    if (!validateTripForm()) {
        return;
    }
    
    const formData = new FormData(e.target);
    generateTripPlan(formData);
}

function validateTripForm() {
    const startLocation = document.getElementById('start_location').value.trim();
    const destination = document.getElementById('destination').value.trim();
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const budget = document.getElementById('budget').value;
    
    if (!startLocation) {
        showAlert('Please enter your starting location', 'error');
        return false;
    }
    
    if (!destination) {
        showAlert('Please enter your destination', 'error');
        return false;
    }
    
    if (!startDate) {
        showAlert('Please select a start date', 'error');
        return false;
    }
    
    if (!endDate) {
        showAlert('Please select an end date', 'error');
        return false;
    }
    
    // Validate dates
    const start = new Date(startDate);
    const end = new Date(endDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (start < today) {
        showAlert('Start date cannot be in the past', 'error');
        return false;
    }
    
    if (end <= start) {
        showAlert('End date must be after start date', 'error');
        return false;
    }
    
    if (!budget || budget < 1000) {
        showAlert('Please enter a valid budget (minimum ₹1,000)', 'error');
        return false;
    }
    
    return true;
}

async function generateTripPlan(formData) {
    isGeneratingTrip = true;
    
    try {
        showLoadingOverlay('Generating your personalized trip plan...');
        
        const response = await fetch('/generate_trip', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        hideLoadingOverlay();
        
        if (data.success) {
            showAlert('Trip plan generated successfully!', 'success');
            
            // Store current trip data
            currentTrip = data.trip;
            
            // Redirect to results page or update current page
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                displayTripResults(data.trip);
            }
        } else {
            showAlert(data.message || 'Failed to generate trip plan', 'error');
        }
    } catch (error) {
        hideLoadingOverlay();
        console.error('Error generating trip:', error);
        showAlert('Network error. Please check your connection and try again.', 'error');
    } finally {
        isGeneratingTrip = false;
    }
}

function displayTripResults(trip) {
    const resultsContainer = document.getElementById('tripResults');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h3><i class="fas fa-map-marked-alt"></i> ${trip.title}</h3>
                <p class="mb-0">${trip.start_location} → ${trip.destination}</p>
            </div>
            <div class="card-body">
                <div class="trip-details mb-4">
                    <div class="row">
                        <div class="col-md-3">
                            <strong>Duration:</strong> ${trip.duration} days
                        </div>
                        <div class="col-md-3">
                            <strong>Dates:</strong> ${trip.start_date} to ${trip.end_date}
                        </div>
                        <div class="col-md-3">
                            <strong>Budget:</strong> ₹${trip.budget.amount.toLocaleString()}
                        </div>
                        <div class="col-md-3">
                            <strong>Status:</strong> <span class="badge bg-success">${trip.status}</span>
                        </div>
                    </div>
                </div>
                
                <div class="trip-plan">
                    <h4>Your Itinerary</h4>
                    <div class="trip-content">
                        ${formatTripPlan(trip.trip_plan)}
                    </div>
                </div>
                
                <div class="trip-actions mt-4">
                    <button class="btn btn-primary me-2" onclick="downloadTripPDF('${trip.trip_id}')">
                        <i class="fas fa-download"></i> Download PDF
                    </button>
                    <button class="btn btn-outline-secondary me-2" onclick="shareTrip('${trip.trip_id}')">
                        <i class="fas fa-share"></i> Share Trip
                    </button>
                    <button class="btn btn-outline-success" onclick="saveTrip('${trip.trip_id}')">
                        <i class="fas fa-save"></i> Save Trip
                    </button>
                </div>
            </div>
        </div>
    `;
}

function formatTripPlan(planText) {
    // Convert the trip plan text to formatted HTML
    return planText
        .split('\n')
        .map(line => {
            if (line.trim().startsWith('Day ')) {
                return `<h5 class="mt-3 mb-2 text-primary">${line.trim()}</h5>`;
            } else if (line.trim().startsWith('- ')) {
                return `<p class="mb-1"><i class="fas fa-circle text-muted me-2" style="font-size: 0.5em;"></i>${line.trim().substring(2)}</p>`;
            } else if (line.trim()) {
                return `<p class="mb-2">${line.trim()}</p>`;
            }
            return '';
        })
        .join('');
}

// Date picker initialization
function initDatePickers() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        startDateInput.min = today;
        endDateInput.min = today;
        
        startDateInput.addEventListener('change', function() {
            const startDate = new Date(this.value);
            const nextDay = new Date(startDate);
            nextDay.setDate(nextDay.getDate() + 1);
            
            endDateInput.min = nextDay.toISOString().split('T')[0];
            
            if (endDateInput.value && new Date(endDateInput.value) <= startDate) {
                endDateInput.value = nextDay.toISOString().split('T')[0];
            }
        });
    }
}

// Location autocomplete (basic implementation)
function initLocationAutocomplete() {
    const locationInputs = document.querySelectorAll('#start_location, #destination');
    
    locationInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Here you could implement Google Places API or other location services
            // For now, just basic validation
            if (this.value.length < 2) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });
}

// Budget slider
function initBudgetSlider() {
    const budgetInput = document.getElementById('budget');
    const budgetDisplay = document.getElementById('budgetDisplay');
    
    if (budgetInput && budgetDisplay) {
        budgetInput.addEventListener('input', function() {
            budgetDisplay.textContent = `₹${parseInt(this.value).toLocaleString()}`;
        });
    }
}

// Trip actions
async function downloadTripPDF(tripId) {
    try {
        showLoadingOverlay('Generating PDF...');
        
        const response = await fetch(`/download_trip_pdf/${tripId}`, {
            method: 'GET'
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `trip-plan-${tripId}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showAlert('PDF downloaded successfully!', 'success');
        } else {
            throw new Error('Failed to download PDF');
        }
    } catch (error) {
        console.error('Error downloading PDF:', error);
        showAlert('Failed to download PDF. Please try again.', 'error');
    } finally {
        hideLoadingOverlay();
    }
}

function shareTrip(tripId) {
    if (navigator.share) {
        navigator.share({
            title: 'My Trip Plan - TripAI',
            text: 'Check out my awesome trip plan generated by TripAI!',
            url: `${window.location.origin}/trip/${tripId}`
        });
    } else {
        // Fallback: copy to clipboard
        const url = `${window.location.origin}/trip/${tripId}`;
        navigator.clipboard.writeText(url).then(() => {
            showAlert('Trip link copied to clipboard!', 'success');
        }).catch(() => {
            showAlert('Unable to copy link. Please share manually.', 'error');
        });
    }
}

async function saveTrip(tripId) {
    try {
        const response = await fetch(`/save_trip/${tripId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Trip saved successfully!', 'success');
        } else {
            showAlert(data.message || 'Failed to save trip', 'error');
        }
    } catch (error) {
        console.error('Error saving trip:', error);
        showAlert('Failed to save trip. Please try again.', 'error');
    }
}

// Dashboard functions
function initDashboard() {
    loadRecentTrips();
    loadTripStats();
}

async function loadRecentTrips() {
    const tripsContainer = document.getElementById('recentTrips');
    if (!tripsContainer) return;
    
    try {
        const response = await fetch('/api/recent_trips');
        const data = await response.json();
        
        if (data.success && data.trips.length > 0) {
            tripsContainer.innerHTML = data.trips.map(trip => `
                <div class="col-md-4 mb-3">
                    <div class="card trip-card">
                        <div class="card-body">
                            <h6 class="card-title">${trip.title}</h6>
                            <p class="card-text small text-muted">
                                ${trip.start_location} → ${trip.destination}<br>
                                ${trip.start_date} to ${trip.end_date}
                            </p>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="badge bg-primary">₹${trip.budget.amount.toLocaleString()}</span>
                                <div class="btn-group btn-group-sm">
                                    <button class="btn btn-outline-primary btn-sm" onclick="viewTrip('${trip.trip_id}')">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn btn-outline-secondary btn-sm" onclick="downloadTripPDF('${trip.trip_id}')">
                                        <i class="fas fa-download"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            tripsContainer.innerHTML = `
                <div class="col-12">
                    <div class="text-center py-4">
                        <i class="fas fa-suitcase fa-3x text-muted mb-3"></i>
                        <h5>No trips yet</h5>
                        <p class="text-muted">Start planning your first adventure!</p>
                        <a href="/trip_planner" class="btn btn-primary">Plan New Trip</a>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading recent trips:', error);
        tripsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-warning">
                    Failed to load recent trips. Please refresh the page.
                </div>
            </div>
        `;
    }
}

async function loadTripStats() {
    const statsContainer = document.getElementById('tripStats');
    if (!statsContainer) return;
    
    try {
        const response = await fetch('/api/trip_stats');
        const data = await response.json();
        
        if (data.success) {
            statsContainer.innerHTML = `
                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-card">
                            <i class="fas fa-map-marker-alt"></i>
                            <h3>${data.stats.total_trips}</h3>
                            <p>Total Trips</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <i class="fas fa-globe"></i>
                            <h3>${data.stats.countries_visited}</h3>
                            <p>Countries</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <i class="fas fa-calendar"></i>
                            <h3>${data.stats.total_days}</h3>
                            <p>Travel Days</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <i class="fas fa-rupee-sign"></i>
                            <h3>₹${data.stats.total_budget.toLocaleString()}</h3>
                            <p>Total Budget</p>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading trip stats:', error);
    }
}

function viewTrip(tripId) {
    window.location.href = `/trip/${tripId}`;
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize based on current page
    const currentPage = window.location.pathname;
    
    if (currentPage.includes('trip_planner')) {
        initTripPlanner();
    } else if (currentPage.includes('dashboard')) {
        initDashboard();
    }
    
    // Initialize common features
    initNavbar();
    initTooltips();
});

// Navbar enhancements
function initNavbar() {
    // Add active class to current page link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Initialize Bootstrap tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showAlert('An unexpected error occurred. Please refresh the page.', 'error');
});

// Export functions for use in other scripts
window.TripAI = {
    showAlert,
    downloadTripPDF,
    shareTrip,
    saveTrip,
    viewTrip
};