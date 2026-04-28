/**
 * Notifications-specific JavaScript
 * ITAM - IT Asset Management
 */

let pendingDeleteId = null;

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

// Confirm delete
function confirmDelete(notificationId) {
    pendingDeleteId = notificationId;
    document.getElementById('confirmDeleteModal').classList.remove('hidden');
    if (window.lucide) {
        lucide.createIcons();
    }
}

function closeDeleteModal() {
    document.getElementById('confirmDeleteModal').classList.add('hidden');
    pendingDeleteId = null;
}

function deleteNotification() {
    if (!pendingDeleteId) return;
    const notificationId = pendingDeleteId;
    closeDeleteModal();
    
    fetch(`/notifications/delete/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            if (window.showToast) {
                window.showToast('Error deleting notification', 'error');
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

// Mark single notification as read
function markAsRead(notificationId) {
    fetch(`/notifications/mark-read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
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
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
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

// ESC key support for delete modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeDeleteModal();
    }
});

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
