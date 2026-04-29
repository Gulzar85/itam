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

// Mark single notification as read
function markAsRead(notificationId) {
    fetch(`/notifications/mark-read/${notificationId}/`, {
        method: 'POST',
        headers: getCSRFHeader()
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            if (window.showToast) {
                window.showToast('Error marking notification as read', 'error');
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

// Mark all notifications as read
function markAllAsRead() {
    fetch(MARK_ALL_READ_URL, {
        method: 'POST',
        headers: getCSRFHeader()
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
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
