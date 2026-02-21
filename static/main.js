// RendezVousDZ - Main JavaScript
// Global dark mode + logo swap + real-time queue

document.addEventListener('DOMContentLoaded', function() {
    initTheme();           // 🌙 FIRST — before anything renders
    initAnimations();
    initFormValidation();
    initPasswordToggle();
    initQueueUpdates();
    initNotifications();
    initThemeEffects();
    initRealtimeQueue();
});

// ═══════════════════════════════════════════════════════
// 🌙 GLOBAL DARK MODE
// ═══════════════════════════════════════════════════════
const THEME_KEY = 'rvdz_theme';

function initTheme() {
    const saved = localStorage.getItem(THEME_KEY) || 'light';
    _applyTheme(saved);
}

function _applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);

    // Update ALL toggle buttons on the page
    document.querySelectorAll('.theme-toggle').forEach(btn => {
        const lightIcon = btn.querySelector('.theme-icon-light');
        const darkIcon  = btn.querySelector('.theme-icon-dark');
        if (lightIcon) lightIcon.style.display = theme === 'dark' ? 'none'   : '';
        if (darkIcon)  darkIcon.style.display  = theme === 'dark' ? ''       : 'none';
    });

    // Swap logos — works regardless of current src value
    // Strategy: match any logo img and set the correct one
    document.querySelectorAll('img.auth-logo, img.dashboard-logo').forEach(img => {
        img.src = theme === 'dark'
            ? '/static/logo_white.png'
            : '/static/logo_blue.png';
    });

    // Analytics charts rebuild if present
    if (window._chartsBuilt && typeof buildCharts === 'function') {
        setTimeout(buildCharts, 50);
    }
}

// Called by onclick="toggleTheme()" on any button
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    _applyTheme(current === 'dark' ? 'light' : 'dark');
}

window.toggleTheme = toggleTheme;


// ═══════════════════════════════════════════════════════
// 🔥 REAL-TIME QUEUE UPDATES
// ═══════════════════════════════════════════════════════
function initRealtimeQueue() {
    const businessId = getBusinessIdFromPage();
    if (!businessId) return;

    const script  = document.createElement('script');
    script.src    = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
    script.onload = () => connectToRealtimeQueue(businessId);
    script.onerror= () => console.error('❌ Failed to load Socket.IO');
    document.head.appendChild(script);
}

function getBusinessIdFromPage() {
    const btn = document.querySelector('a[href^="/b/"]');
    if (btn) {
        const m = btn.getAttribute('href').match(/\/b\/(\d+)/);
        return m ? m[1] : null;
    }
    const m = window.location.pathname.match(/\/b\/(\d+)/);
    return m ? m[1] : null;
}

function connectToRealtimeQueue(businessId) {
    const socket = io();
    socket.on('connect',       () => socket.emit('join', { business_id: businessId }));
    socket.on('queue_updated', data => { if (data.business_id == businessId) updateQueueDisplay(data); });
    socket.on('disconnect',    () => console.log('❌ Real-time disconnected'));
}

function updateQueueDisplay(data) {
    // Current count stat card
    const currentCountEl = document.querySelector('.stat-value');
    if (currentCountEl && currentCountEl.textContent !== data.current_count.toString()) {
        currentCountEl.textContent = data.current_count;
        animateElement(currentCountEl);
    }

    // Remaining slots
    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length >= 3) {
        const remainingEl = statCards[2].querySelector('.stat-value');
        if (remainingEl) {
            remainingEl.textContent = data.max_clients - data.current_count;
            remainingEl.style.color = data.queue_full ? 'var(--error)' : 'var(--success)';
            animateElement(remainingEl);
        }
    }

    // Queue count badge
    const queueCountEl = document.querySelector('.queue-count');
    if (queueCountEl) {
        queueCountEl.textContent = `${data.current_count}/${data.max_clients}`;
        animateElement(queueCountEl);
    }

    // Queue full alert
    const queueFullAlert = document.querySelector('[data-queue-full-alert]');
    if (data.queue_full && !queueFullAlert && window.location.pathname.includes('/dashboard')) {
        const statsGrid = document.querySelector('.stats-grid');
        if (statsGrid) {
            const alert = document.createElement('div');
            alert.setAttribute('data-queue-full-alert', '1');
            alert.style.cssText = 'background:rgba(239,68,68,0.1);border:2px solid var(--error);border-radius:var(--radius-lg);padding:var(--space-lg);margin-bottom:var(--space-xl);text-align:center;';
            alert.innerHTML = `<p style="color:var(--error);font-weight:700;font-size:1.125rem;margin:0;">⚠️ Queue Full - Daily limit reached (${data.max_clients}/${data.max_clients})</p>`;
            statsGrid.after(alert);
        }
    } else if (!data.queue_full && queueFullAlert) {
        queueFullAlert.remove();
    }

    // Queue list (dashboard only)
    if (window.location.pathname.includes('/dashboard')) {
        updateQueueList(data.queue_entries);
    }

    // Public booking page counter
    if (window.location.pathname.includes('/b/')) {
        const statusStrong = document.querySelector('.queue-status-count');
        if (statusStrong) statusStrong.textContent = `${data.current_count}/${data.max_clients}`;

        const submitBtn = document.querySelector('button[type="submit"]');
        const inputs    = document.querySelectorAll('input[name="client_name"], input[name="client_phone"]');
        if (data.queue_full) {
            if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Queue Full'; }
            inputs.forEach(i => i.disabled = true);
        } else {
            if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Join Queue'; }
            inputs.forEach(i => i.disabled = false);
        }
    }
}

function updateQueueList(entries) {
    const queueList  = document.querySelector('.queue-list');
    const emptyState = document.querySelector('.empty-state');

    if (!entries || entries.length === 0) {
        if (queueList) queueList.style.display = 'none';
        if (!emptyState) {
            const section = document.querySelector('.queue-section');
            if (section) {
                const empty = document.createElement('div');
                empty.className = 'empty-state';
                empty.innerHTML = '<div class="empty-state-icon">📋</div><h4>No clients in queue</h4><p>Add a client above to get started</p>';
                section.appendChild(empty);
            }
        }
        return;
    }

    if (emptyState) emptyState.style.display = 'none';
    if (!queueList) return;
    queueList.style.display = 'flex';

    queueList.innerHTML = entries.map((entry, i) => `
        <div class="queue-item" style="animation:slideInLeft 0.4s ease-out both;">
            <div class="queue-number">#${i + 1}</div>
            <div class="queue-details">
                <div class="queue-name">${escapeHtml(entry.client_name)}</div>
                <div class="queue-meta">
                    <span class="queue-status status-${entry.status}">${capitalizeFirst(entry.status)}</span>
                    ${entry.client_phone ? `<span class="queue-time">📞 ${escapeHtml(entry.client_phone)}</span>` : ''}
                </div>
            </div>
            <div class="queue-actions">
                ${entry.status === 'waiting' ? `
                    <a href="/mark-done/${entry.id}" class="btn btn-success">Mark Done</a>
                    <a href="/mark-skipped/${entry.id}" class="btn btn-ghost">Skip</a>
                ` : ''}
            </div>
        </div>`).join('');
}


// ═══════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════
function initAnimations() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.style.animation = 'fadeIn 0.5s ease-out both';
                observer.unobserve(e.target);
            }
        });
    }, { threshold: 0.1 });
    document.querySelectorAll('.card, .stat-card, .feature-card').forEach(c => observer.observe(c));
}

function animateElement(el) {
    el.style.animation = 'none';
    el.offsetHeight;
    el.style.animation = 'pulse 0.4s ease-out';
}


// ═══════════════════════════════════════════════════════
// FORM VALIDATION
// ═══════════════════════════════════════════════════════
function initFormValidation() {
    document.querySelectorAll('form').forEach(form => {
        form.querySelectorAll('input[required], select[required]').forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('input-error')) validateField(input);
            });
        });
    });
}

function validateField(input) {
    if (!input.value.trim()) { showError(input, `This field is required`); return false; }
    if (input.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value)) {
        showError(input, 'Please enter a valid email address'); return false;
    }
    if (input.type === 'password' && input.value.length < 8) {
        showError(input, 'Password must be at least 8 characters'); return false;
    }
    removeError(input);
    return true;
}

function showError(input, message) {
    input.classList.add('input-error');
    input.style.borderColor = 'var(--error)';
    const parent = input.parentElement;
    const existing = parent.querySelector('.field-error');
    if (existing) existing.remove();
    const err = document.createElement('span');
    err.className = 'field-error';
    err.style.cssText = 'color:var(--error);font-size:0.8rem;margin-top:0.25rem;display:block;';
    err.textContent = message;
    parent.appendChild(err);
}

function removeError(input) {
    input.classList.remove('input-error');
    input.style.borderColor = '';
    const err = input.parentElement.querySelector('.field-error');
    if (err) err.remove();
}


// ═══════════════════════════════════════════════════════
// PASSWORD TOGGLE
// ═══════════════════════════════════════════════════════
function initPasswordToggle() {
    document.querySelectorAll('input[type="password"]').forEach(input => {
        const wrapper = input.parentElement;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'password-toggle';
        btn.innerHTML = '👁️';
        btn.setAttribute('aria-label', 'Toggle password visibility');
        wrapper.style.position = 'relative';
        wrapper.appendChild(btn);
        btn.addEventListener('click', function() {
            input.type = input.type === 'password' ? 'text' : 'password';
            this.innerHTML = input.type === 'password' ? '👁️' : '🙈';
        });
    });
}


// ═══════════════════════════════════════════════════════
// QUEUE ITEM ANIMATIONS
// ═══════════════════════════════════════════════════════
function initQueueUpdates() {
    document.querySelectorAll('.queue-item').forEach((item, i) => {
        item.style.animation = `slideInLeft 0.4s ease-out ${i * 0.1}s both`;
    });
}


// ═══════════════════════════════════════════════════════
// NOTIFICATIONS
// ═══════════════════════════════════════════════════════
function initNotifications() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('success')) showNotification(params.get('success'), 'success');
    if (params.get('error'))   showNotification(params.get('error'),   'error');
}

function showNotification(message, type = 'info') {
    const n = document.createElement('div');
    n.style.cssText = `position:fixed;top:20px;right:20px;background:var(--surface-card);padding:1rem 1.5rem;
        border-radius:var(--radius-lg);box-shadow:var(--shadow-xl);z-index:9999;display:flex;
        align-items:center;gap:0.75rem;max-width:400px;animation:slideInRight 0.3s ease-out;
        border-left:4px solid ${type==='success'?'var(--success)':type==='error'?'var(--error)':'var(--info)'};`;
    const icon = type==='success' ? '✅' : type==='error' ? '❌' : 'ℹ️';
    n.innerHTML = `<span style="font-size:1.5rem;">${icon}</span>
        <span style="font-weight:500;color:var(--text-primary);">${message}</span>
        <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1.25rem;margin-left:auto;">×</button>`;
    document.body.appendChild(n);
    setTimeout(() => {
        n.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => n.remove(), 300);
    }, 5000);
}


// ═══════════════════════════════════════════════════════
// THEME EFFECTS (button hover glow)
// ═══════════════════════════════════════════════════════
function initThemeEffects() {
    document.querySelectorAll('.btn-primary, .btn-secondary').forEach(btn => {
        btn.addEventListener('mousemove', function(e) {
            const r = this.getBoundingClientRect();
            this.style.setProperty('--mouse-x', `${e.clientX - r.left}px`);
            this.style.setProperty('--mouse-y', `${e.clientY - r.top}px`);
        });
    });
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            const t = document.querySelector(this.getAttribute('href'));
            if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth' }); }
        });
    });
}


// ═══════════════════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════════════════
function escapeHtml(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
}

function capitalizeFirst(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

window.RendezVousDZ = { showNotification, toggleTheme };

// Extra keyframes injected at runtime
const _style = document.createElement('style');
_style.textContent = `
    @keyframes slideOutRight { from{opacity:1;transform:translateX(0)} to{opacity:0;transform:translateX(100%)} }
    @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.05)} }
`;
document.head.appendChild(_style);
