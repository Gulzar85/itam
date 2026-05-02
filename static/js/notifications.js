/**
 * Notifications-specific JavaScript
 * ITAM - IT Asset Management
 */

// Get CSRF token from cookie
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Get CSRF token for header (Django expects X-CSRFToken)
function getCSRFHeader() {
    return {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
    };
}

// Filter notifications
function applyFilters() {
    const typeFilter = document.getElementById('filterType').value;
    const priorityFilter = document.getElementById('filterPriority').value;
    const readFilter = document.getElementById('filterRead').value;
    
    const params = new URLSearchParams(window.location.search);
    
    if (typeFilter) {
        params.set('type', typeFilter);
    } else {
        params.delete('type');
    }
    
    if (priorityFilter) {
        params.set('priority', priorityFilter);
    } else {
        params.delete('priority');
    }
    
    if (readFilter) {
        params.set('read', readFilter);
    } else {
        params.delete('read');
    }
    
    // Reset to page 1 when filtering
    params.delete('page');
    
    window.location.search = params.toString();
}

// Confirm delete - now handled by Alpine.js in template
// These functions are defined in the template script with Alpine.js integration

// Mark single notification as read - updates DOM without full reload
function markAsRead(notificationId) {
    const el = document.querySelector(`[data-notification-id="${notificationId}"]`);
    if (el) el.style.opacity = '0.5';
    
    fetch(`/notifications/mark-read/${notificationId}/`, {
        method: 'POST',
        headers: getCSRFHeader()
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            if (el) {
                el.classList.remove('border-l-4');
                el.style.borderLeftColor = 'transparent';
                el.style.opacity = '1';
            }
            // Hide the check button
            const btn = el?.querySelector('button[onclick*="markAsRead"]');
            if (btn) btn.style.display = 'none';
            // Update unread count in sidebar
            updateUnreadCount(-1);
        } else {
            if (el) el.style.opacity = '1';
            if (window.showToast) {
                window.showToast('Error marking notification as read', 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (el) el.style.opacity = '1';
        if (window.showToast) {
            window.showToast('An error occurred', 'error');
        }
    });
}

// Mark all notifications as read - updates DOM without full reload
function markAllAsRead() {
    fetch(MARK_ALL_READ_URL, {
        method: 'POST',
        headers: getCSRFHeader()
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update all notification cards
            document.querySelectorAll('[data-notification-id]').forEach(el => {
                el.classList.remove('border-l-4');
                el.style.borderLeftColor = 'transparent';
                const btn = el.querySelector('button[onclick*="markAsRead"]');
                if (btn) btn.style.display = 'none';
            });
            // Reset unread count
            updateUnreadCount(0);
        } else {
            if (window.showToast) {
                window.showToast('Error marking all as read', 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (window.showToast) {
            window.showToast('An error occurred', 'error');
        }
    });
}

// Update unread count in sidebar
function updateUnreadCount(newCount) {
    const badges = document.querySelectorAll('.sidebar-badge');
    badges.forEach(badge => {
        if (newCount <= 0) {
            badge.style.display = 'none';
        } else {
            badge.textContent = newCount;
            badge.style.display = '';
        }
    });
    // Update mark all button
    const markAllBtn = document.querySelector('button[onclick*="markAllAsRead"]');
    if (markAllBtn && newCount <= 0) {
        markAllBtn.closest('.flex').remove();
    }
}

// Export functions for use in other scripts
window.getCSRFToken = getCSRFToken;
window.getCSRFHeader = getCSRFHeader;

// Initialize filter dropdowns if they exist
document.addEventListener('DOMContentLoaded', () => {
    const filterType = document.getElementById('filterType');
    const filterPriority = document.getElementById('filterPriority');
    const filterRead = document.getElementById('filterRead');
    
    if (filterType) {
        filterType.addEventListener('change', applyFilters);
    }
    if (filterPriority) {
        filterPriority.addEventListener('change', applyFilters);
    }
    if (filterRead) {
        filterRead.addEventListener('change', applyFilters);
    }
});
