/**
 * Base JavaScript extracted from base.html
 * ITAM - IT Asset Management System
 */

// Initialize Lucide icons ONCE
function initLucide() {
    if (window.lucide && !window.lucideInitialized) {
        lucide.createIcons();
        window.lucideInitialized = true;
    }
}

// Re-init only for newly added dynamic content
function initNewIcons(container = document) {
    if (window.lucide) {
        const icons = container.querySelectorAll ? container.querySelectorAll('[data-lucide]') : [container];
        icons.forEach(el => {
            if (!el.classList.contains('lucide')) {
                lucide.createIcons({ nodes: [el] });
            }
        });
    }
}

// Setup notifications toast auto-dismiss
function setupNotifications() {
    $(document).ready(function() {
        setTimeout(() => {
            $('.notification-toast').fadeOut('slow', function() {
                $(this).remove();
            });
        }, 4000);
    });
}

// Show toast notification with consistent theme
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer') || document.body;
    const toast = document.createElement('div');
    
    // Consistent theme: primary color border, white background
    toast.className = `fixed bottom-5 right-5 z-[60] bg-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-4 border-l-4 animate-bounce-in notification-toast ${
        type === 'success' ? 'border-green-500' : 'border-red-500'
    }`;
    
    // Icon based on type
    const icon = type === 'success' ? 'check-circle' : 'alert-circle';
    const iconColor = type === 'success' ? 'text-green-500' : 'text-red-500';
    const title = type === 'success' ? 'Success' : 'Error';
    
    const iconWrapper = document.createElement('div');
    iconWrapper.className = iconColor;
    const iconElement = document.createElement('i');
    iconElement.setAttribute('data-lucide', icon);
    iconElement.className = 'w-6 h-6';
    iconWrapper.appendChild(iconElement);

    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'flex flex-col';
    const titleElement = document.createElement('span');
    titleElement.className = 'text-xs font-black uppercase tracking-wider';
    titleElement.style.color = 'var(--primary-color)';
    titleElement.textContent = title;
    const messageElement = document.createElement('span');
    messageElement.className = 'font-medium text-gray-800';
    messageElement.textContent = String(message);
    contentWrapper.appendChild(titleElement);
    contentWrapper.appendChild(messageElement);

    const closeButton = document.createElement('button');
    closeButton.className = 'ml-auto text-gray-400 hover:text-gray-600';
    closeButton.addEventListener('click', () => toast.remove());
    const closeIcon = document.createElement('i');
    closeIcon.setAttribute('data-lucide', 'x');
    closeIcon.className = 'w-4 h-4';
    closeButton.appendChild(closeIcon);

    toast.appendChild(iconWrapper);
    toast.appendChild(contentWrapper);
    toast.appendChild(closeButton);
    
    toastContainer.appendChild(toast);
    
    // Only init icons for the newly added toast
    initNewIcons(toast);
    
    setTimeout(() => {
        if (toast && toast.parentElement) {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Alt + 1 = Dashboard
    if (e.altKey && e.key === '1') {
        window.location.href = '/';
    }
    // Alt + 2 = New Request
    if (e.altKey && e.key === '2') {
        window.location.href = '/requests/new/';
    }
    // Alt + 3 = Equipment
    if (e.altKey && e.key === '3') {
        window.location.href = '/inventory/equipment/';
    }
});

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    setupNotifications();

    // Add skip navigation link if not exists
    if (!document.querySelector('.skip-to-content')) {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-to-content';
        skipLink.textContent = 'Skip to main content';
        document.body.prepend(skipLink);
    }

    // Initialize Lucid icons after DOM ready (uses flag to prevent duplicates)
    initLucide();
});

// Re-initialize icons when Alpine.js is ready
document.addEventListener('alpine:initialized', () => {
    initLucide();
});

// ESC key handler for modals
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // Close all modals
        document.querySelectorAll('[id$="Modal"]').forEach(modal => {
            if (!modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        });
    }
});

// Export functions for use in other scripts
window.initLucide = initLucide;
window.showToast = showToast;
