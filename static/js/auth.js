// Authentication JavaScript for TripAI Flask Application

// Password visibility toggle
function togglePassword(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const toggleIcon = document.querySelector(`#${fieldId} + .password-toggle i`);
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    } else {
        passwordField.type = 'password';
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    }
}

// Form validation for login
function validateLoginForm() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address', 'error');
        return false;
    }
    
    // Password validation
    if (password.length < 6) {
        showAlert('Password must be at least 6 characters long', 'error');
        return false;
    }
    
    return true;
}

// Form validation for registration
function validateRegisterForm() {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const termsAccepted = document.getElementById('terms').checked;
    
    // Name validation
    if (name.length < 2) {
        showAlert('Name must be at least 2 characters long', 'error');
        return false;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address', 'error');
        return false;
    }
    
    // Password validation
    if (password.length < 8) {
        showAlert('Password must be at least 8 characters long', 'error');
        return false;
    }
    
    // Password strength validation
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
    if (!(hasUpperCase && hasLowerCase && hasNumbers)) {
        showAlert('Password must contain uppercase, lowercase, and numbers', 'error');
        return false;
    }
    
    // Confirm password validation
    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'error');
        return false;
    }
    
    // Terms validation
    if (!termsAccepted) {
        showAlert('Please accept the Terms of Service and Privacy Policy', 'error');
        return false;
    }
    
    return true;
}

// Show alert messages
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show custom-alert`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert alert at the top of the form
    const authCard = document.querySelector('.auth-card');
    authCard.insertBefore(alertDiv, authCard.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv) {
            alertDiv.remove();
        }
    }, 5000);
}

// Loading state management
function setLoadingState(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        const originalText = button.innerHTML;
        button.dataset.originalText = originalText;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
    }
}

// Handle form submissions - FIXED VERSION
function handleFormSubmission(form, validationFunction) {
    const submitButton = form.querySelector('button[type="submit"]');
    
    form.addEventListener('submit', function(e) {
        // Only prevent default if validation fails
        if (!validationFunction()) {
            e.preventDefault();
            return;
        }
        
        // For successful validation, show loading state but allow normal form submission
        setLoadingState(submitButton, true);
        
        // Don't prevent default - let the form submit normally to Flask
        // Flask will handle the redirect after processing
    });
}

// Social login handlers
function initSocialLogin() {
    const googleBtn = document.querySelector('.social-login button:first-child');
    const facebookBtn = document.querySelector('.social-login button:last-child');
    
    if (googleBtn) {
        googleBtn.addEventListener('click', function() {
            showAlert('Google login will be available soon!', 'info');
        });
    }
    
    if (facebookBtn) {
        facebookBtn.addEventListener('click', function() {
            showAlert('Facebook login will be available soon!', 'info');
        });
    }
}

// Real-time email validation
function initEmailValidation() {
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email && !emailRegex.test(email)) {
                this.classList.add('is-invalid');
                showFieldError(this, 'Please enter a valid email address');
            } else {
                this.classList.remove('is-invalid');
                hideFieldError(this);
            }
        });
    }
}

// Show field-specific error
function showFieldError(field, message) {
    hideFieldError(field); // Remove existing error
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

// Hide field-specific error
function hideFieldError(field) {
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form handlers
    const loginForm = document.querySelector('#loginForm, form[action*="login"]');
    const registerForm = document.querySelector('#registerForm, form[action*="register"]');
    
    if (loginForm) {
        handleFormSubmission(loginForm, validateLoginForm);
    }
    
    if (registerForm) {
        handleFormSubmission(registerForm, validateRegisterForm);
    }
    
    // Initialize other features
    initSocialLogin();
    initEmailValidation();
    
    // Add smooth animations
    const authCard = document.querySelector('.auth-card');
    if (authCard) {
        authCard.style.opacity = '0';
        authCard.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            authCard.style.transition = 'all 0.5s ease-out';
            authCard.style.opacity = '1';
            authCard.style.transform = 'translateY(0)';
        }, 100);
    }
});

// Forgot password handler
function handleForgotPassword() {
    const email = document.getElementById('email').value.trim();
    
    if (!email) {
        showAlert('Please enter your email address first', 'error');
        return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address', 'error');
        return;
    }
    
    // Here you would typically send a request to your backend
    showAlert('Password reset instructions have been sent to your email', 'success');
}

// Add event listener for forgot password link
document.addEventListener('DOMContentLoaded', function() {
    const forgotPasswordLink = document.querySelector('.forgot-password');
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', function(e) {
            e.preventDefault();
            handleForgotPassword();
        });
    }
});