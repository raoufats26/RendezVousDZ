// RendezVousDZ - Main JavaScript File with Real-Time Support

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initAnimations();
    initFormValidation();
    initPasswordToggle();
    initQueueUpdates();
    initNotifications();
    initThemeEffects();
    initRealtimeQueue(); // 🔥 NEW: Real-time queue updates
});

// 🔥 REAL-TIME QUEUE UPDATES
function initRealtimeQueue() {
    console.log('🚀 initRealtimeQueue() called');
    
    // Check if we're on a page that needs real-time updates
    const businessId = getBusinessIdFromPage();
    console.log('🔍 Business ID detected:', businessId);
    
    if (!businessId) {
        console.log('❌ No business ID found, skipping real-time');
        return; // Not on a queue page
    }
    
    console.log('📡 Loading Socket.IO library...');
    // Load Socket.IO client library
    const script = document.createElement('script');
    script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
    script.onload = function() {
        console.log('✅ Socket.IO library loaded');
        connectToRealtimeQueue(businessId);
    };
    script.onerror = function() {
        console.error('❌ Failed to load Socket.IO library');
    };
    document.head.appendChild(script);
}

function getBusinessIdFromPage() {
    // Dashboard page
    const publicLinkBtn = document.querySelector('a[href^="/b/"]');
    if (publicLinkBtn) {
        const match = publicLinkBtn.getAttribute('href').match(/\/b\/(\d+)/);
        return match ? match[1] : null;
    }
    
    // Public booking page
    const currentPath = window.location.pathname;
    const match = currentPath.match(/\/b\/(\d+)/);
    return match ? match[1] : null;
}

function connectToRealtimeQueue(businessId) {
    console.log('🔌 Connecting to SocketIO for business:', businessId);
    
    // Connect to SocketIO server
    const socket = io();
    
    // Join the business-specific room
    socket.on('connect', function() {
        console.log('🔥 Real-time connected - Socket ID:', socket.id);
        console.log('📤 Emitting join event for business:', businessId);
        socket.emit('join', { business_id: businessId });
    });
    
    // Listen for queue updates
    socket.on('queue_updated', function(data) {
        console.log('📊 Queue updated EVENT RECEIVED:', data);
        console.log('🔍 Comparing business IDs:', data.business_id, '==', businessId);
        
        if (data.business_id == businessId) {
            console.log('✅ Business ID matches! Updating display...');
            updateQueueDisplay(data);
        } else {
            console.log('❌ Business ID mismatch - ignoring update');
        }
    });
    
    socket.on('disconnect', function() {
        console.log('❌ Real-time disconnected');
    });
    
    socket.on('joined', function(data) {
        console.log('✅ Successfully joined room:', data.room);
    });
}

function updateQueueDisplay(data) {
    console.log('🎨 updateQueueDisplay() called with data:', data);
    
    // Update stats
    const currentCountEl = document.querySelector('.stat-value');
    console.log('📊 Current count element:', currentCountEl);
    if (currentCountEl && currentCountEl.textContent !== data.current_count.toString()) {
        console.log('✏️ Updating current count from', currentCountEl.textContent, 'to', data.current_count);
        currentCountEl.textContent = data.current_count;
        animateElement(currentCountEl);
    }
    
    // Update remaining slots
    const remainingSlots = data.max_clients - data.current_count;
    const statCards = document.querySelectorAll('.stat-card');
    console.log('📊 Stat cards found:', statCards.length);
    if (statCards.length >= 3) {
        const remainingEl = statCards[2].querySelector('.stat-value');
        if (remainingEl) {
            console.log('✏️ Updating remaining slots to', remainingSlots);
            remainingEl.textContent = remainingSlots;
            remainingEl.style.color = data.queue_full ? 'var(--error)' : 'var(--success)';
            animateElement(remainingEl);
        }
    }
    
    // Update queue count badge
    const queueCountEl = document.querySelector('.queue-count');
    console.log('🏷️ Queue count badge:', queueCountEl);
    if (queueCountEl) {
        console.log('✏️ Updating queue count badge to', `${data.current_count}/${data.max_clients}`);
        queueCountEl.textContent = `${data.current_count}/${data.max_clients}`;
        animateElement(queueCountEl);
    }
    
    // Update queue full alert
    const queueFullAlert = document.querySelector('[style*="rgba(239, 68, 68"]');
    if (data.queue_full && !queueFullAlert && window.location.pathname.includes('/dashboard')) {
        console.log('⚠️ Adding queue full alert');
        const statsGrid = document.querySelector('.stats-grid');
        if (statsGrid) {
            const alert = document.createElement('div');
            alert.style.cssText = 'background: rgba(239, 68, 68, 0.1); border: 2px solid var(--error); border-radius: var(--radius-lg); padding: var(--space-lg); margin-bottom: var(--space-xl); text-align: center;';
            alert.innerHTML = `<p style="color: var(--error); font-weight: 700; font-size: 1.125rem; margin: 0;">⚠️ Queue Full - Daily limit reached (${data.max_clients}/${data.max_clients})</p>`;
            statsGrid.after(alert);
        }
    } else if (!data.queue_full && queueFullAlert) {
        console.log('✅ Removing queue full alert');
        queueFullAlert.remove();
    }
    
    // Update queue list (DASHBOARD ONLY)
    if (window.location.pathname.includes('/dashboard')) {
        console.log('📋 Updating queue list with', data.queue_entries.length, 'entries');
        updateQueueList(data.queue_entries);
    }
    
    // Update public booking page counter
    if (window.location.pathname.includes('/b/')) {
        console.log('🌐 Updating public booking page');
        const queueStatus = document.querySelector('[style*="background: var(--light-gray)"]');
        if (queueStatus) {
            const statusText = queueStatus.querySelector('p strong');
            if (statusText) {
                statusText.textContent = `${data.current_count}/${data.max_clients}`;
            }
        }
        
        // Disable form if queue is full
        const submitBtn = document.querySelector('button[type="submit"]');
        const inputs = document.querySelectorAll('input[name="client_name"], input[name="client_phone"]');
        
        if (data.queue_full) {
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Queue Full';
            }
            inputs.forEach(input => input.disabled = true);
        } else {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Join Queue';
            }
            inputs.forEach(input => input.disabled = false);
        }
    }
    
    console.log('✅ updateQueueDisplay() completed');
}

function updateQueueList(entries) {
    const queueList = document.querySelector('.queue-list');
    const emptyState = document.querySelector('.empty-state');
    
    if (!entries || entries.length === 0) {
        // Show empty state
        if (queueList) {
            queueList.style.display = 'none';
        }
        if (!emptyState) {
            const queueSection = document.querySelector('.queue-section');
            if (queueSection) {
                const empty = document.createElement('div');
                empty.className = 'empty-state';
                empty.innerHTML = `
                    <div class="empty-state-icon">📋</div>
                    <h4>No clients in queue</h4>
                    <p>Add a client above to get started</p>
                `;
                queueSection.appendChild(empty);
            }
        }
        return;
    }
    
    // Hide empty state
    if (emptyState) {
        emptyState.style.display = 'none';
    }
    
    if (!queueList) {
        return;
    }
    
    queueList.style.display = 'block';
    
    // Build new queue HTML
    let queueHTML = '';
    entries.forEach((entry, index) => {
        queueHTML += `
            <div class="queue-item" style="animation: slideInLeft 0.4s ease-out both;">
                <div class="queue-number">#${index + 1}</div>
                
                <div class="queue-details">
                    <div class="queue-name">${escapeHtml(entry.client_name)}</div>
                    <div class="queue-meta">
                        <span class="queue-status status-${entry.status}">
                            ${capitalizeFirst(entry.status)}
                        </span>
                        ${entry.client_phone ? `<span class="queue-time">📞 ${escapeHtml(entry.client_phone)}</span>` : ''}
                    </div>
                </div>
                
                <div class="queue-actions">
                    ${entry.status === 'waiting' ? `
                        <a href="/mark-done/${entry.id}" class="btn btn-success">Mark Done</a>
                        <a href="/mark-skipped/${entry.id}" class="btn btn-ghost">Skip</a>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    queueList.innerHTML = queueHTML;
    animateElement(queueList);
}

function animateElement(element) {
    element.style.animation = 'none';
    setTimeout(() => {
        element.style.animation = 'pulse 0.3s ease-in-out';
    }, 10);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

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
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
`;
document.head.appendChild(style);
