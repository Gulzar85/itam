/**
 * Base JavaScript extracted from base.html
 * ITAM - IT Asset Management System
 */

// Initialize Lucide icons
function initLucide() {
    if (window.lucide) {
        lucide.createIcons();
    }
}

// Setup notifications toast auto-dismiss
function setupNotifications() {
    $(document).ready(function() {
        initLucide();
        setTimeout(() => {
            $('.notification-toast').fadeOut('slow', function() {
                $(this).remove();
            });
        }, 4000);
    });

    // Re-initialize with Alpine.js
    document.addEventListener('alpine:initialized', () => {
        initLucide();
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
    
    toast.innerHTML = `
        <div class="${iconColor}">
            <i data-lucide="${icon}" class="w-6 h-6"></i>
        </div>
        <div class="flex flex-col">
            <span class="text-xs font-black uppercase tracking-wider" style="color: var(--primary-color)">
                ${title}
            </span>
            <span class="font-medium text-gray-800">${message}</span>
        </div>
        <button onclick="this.parentElement.remove()" class="ml-auto text-gray-400 hover:text-gray-600">
            <i data-lucide="x" class="w-4 h-4"></i>
        </button>
    `;
    
    toastContainer.appendChild(toast);
    
    if (window.lucide) {
        lucide.createIcons();
    }
    
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
