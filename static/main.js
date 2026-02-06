// RendezVousDZ - Main JavaScript File

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initAnimations();
    initFormValidation();
    initPasswordToggle();
    initQueueUpdates();
    initNotifications();
    initThemeEffects();
});

// Animation Initialization
function initAnimations() {
    // Add staggered fade-in animations to elements
    const animatedElements = document.querySelectorAll('.animate-fadeIn');
    animatedElements.forEach((element, index) => {
        element.style.animationDelay = `${index * 0.1}s`;
    });

    // Parallax effect for floating shapes
    const shapes = document.querySelectorAll('.floating-shape');
    if (shapes.length > 0) {
        window.addEventListener('mousemove', (e) => {
            const mouseX = e.clientX / window.innerWidth;
            const mouseY = e.clientY / window.innerHeight;
            
            shapes.forEach((shape, index) => {
                const speed = (index + 1) * 10;
                const x = (mouseX - 0.5) * speed;
                const y = (mouseY - 0.5) * speed;
                shape.style.transform = `translate(${x}px, ${y}px)`;
            });
        });
    }
}

// Form Validation
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const submitButton = form.querySelector('button[type="submit"]');
        
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!validateInput(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                return false;
            }
            
            // Add loading state to button
            if (submitButton) {
                submitButton.classList.add('btn-loading');
                submitButton.disabled = true;
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateInput(this);
            });
            
            input.addEventListener('input', function() {
                removeError(this);
            });
        });
    });
}

function validateInput(input) {
    const value = input.value.trim();
    const type = input.type;
    
    removeError(input);
    
    if (input.required && !value) {
        showError(input, 'This field is required');
        return false;
    }
    
    if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showError(input, 'Please enter a valid email address');
            return false;
        }
    }
    
    if (type === 'password' && value) {
        if (value.length < 6) {
            showError(input, 'Password must be at least 6 characters');
            return false;
        }
    }
    
    return true;
}

function showError(input, message) {
    input.classList.add('input-error');
    input.style.borderColor = 'var(--error)';
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.style.cssText = `
        color: var(--error);
        font-size: 0.875rem;
        margin-top: 0.25rem;
        font-weight: 500;
    `;
    errorElement.textContent = message;
    
    const parent = input.parentElement;
    const existingError = parent.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    parent.appendChild(errorElement);
}

function removeError(input) {
    input.classList.remove('input-error');
    input.style.borderColor = '';
    
    const parent = input.parentElement;
    const errorElement = parent.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
}

// Password Toggle Functionality
function initPasswordToggle() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        const wrapper = input.parentElement;
        
        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'password-toggle';
        toggleBtn.innerHTML = '👁️';
        toggleBtn.setAttribute('aria-label', 'Toggle password visibility');
        
        wrapper.style.position = 'relative';
        wrapper.appendChild(toggleBtn);
        
        toggleBtn.addEventListener('click', function() {
            const type = input.type === 'password' ? 'text' : 'password';
            input.type = type;
            this.innerHTML = type === 'password' ? '👁️' : '🙈';
        });
    });
}

// Queue Updates (for dashboard)
function initQueueUpdates() {
    const queueItems = document.querySelectorAll('.queue-item');
    
    queueItems.forEach((item, index) => {
        // Add entrance animation
        item.style.animation = `slideInLeft 0.4s ease-out ${index * 0.1}s both`;
        
        // Update timestamps
        const timeElement = item.querySelector('.queue-time');
        if (timeElement) {
            updateTimestamp(timeElement);
            setInterval(() => updateTimestamp(timeElement), 60000); // Update every minute
        }
    });
    
    // Auto-refresh queue every 30 seconds
    const queueList = document.querySelector('.queue-list');
    if (queueList && window.location.pathname.includes('dashboard')) {
        setInterval(() => {
            // Add subtle pulse to indicate update
            queueList.style.opacity = '0.7';
            setTimeout(() => {
                queueList.style.opacity = '1';
            }, 200);
        }, 30000);
    }
}

function updateTimestamp(element) {
    const timestamp = element.dataset.timestamp;
    if (timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000 / 60); // minutes
        
        if (diff < 1) {
            element.textContent = 'Just now';
        } else if (diff < 60) {
            element.textContent = `${diff} min ago`;
        } else {
            const hours = Math.floor(diff / 60);
            element.textContent = `${hours} hour${hours > 1 ? 's' : ''} ago`;
        }
    }
}

// Notification System
function initNotifications() {
    // Check for success/error messages in URL params
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const error = urlParams.get('error');
    
    if (success) {
        showNotification(success, 'success');
    }
    
    if (error) {
        showNotification(error, 'error');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--white);
        padding: 1rem 1.5rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-xl);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        max-width: 400px;
        animation: slideInRight 0.3s ease-out;
        border-left: 4px solid ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--info)'};
    `;
    
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    notification.innerHTML = `
        <span style="font-size: 1.5rem;">${icon}</span>
        <span style="font-weight: 500; color: var(--dark-gray);">${message}</span>
        <button onclick="this.parentElement.remove()" style="
            background: none;
            border: none;
            color: var(--mid-gray);
            cursor: pointer;
            padding: 0.25rem;
            font-size: 1.25rem;
            margin-left: auto;
        ">×</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Theme Effects
function initThemeEffects() {
    // Add dynamic gradient effect to buttons
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary');
    
    buttons.forEach(button => {
        button.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            this.style.setProperty('--mouse-x', `${x}px`);
            this.style.setProperty('--mouse-y', `${y}px`);
        });
    });
    
    // Smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Queue Management Functions
function joinQueue(name) {
    if (!name || name.trim() === '') {
        showNotification('Please enter a name', 'error');
        return false;
    }
    
    showNotification('Joining queue...', 'info');
    return true;
}

function markAsDone(queueNumber) {
    if (confirm(`Mark customer #${queueNumber} as done?`)) {
        showNotification(`Customer #${queueNumber} marked as done`, 'success');
        return true;
    }
    return false;
}

// Export functions for use in HTML
window.RendezVousDZ = {
    joinQueue,
    markAsDone,
    showNotification
};

// Add custom animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);
