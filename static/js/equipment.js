/**
 * Equipment-specific JavaScript
 * ITAM - IT Asset Management
 */

// Bulk selection
function toggleBulkActionBar() {
    const checkboxes = document.querySelectorAll('.equipment-checkbox:checked');
    const bar = document.getElementById('bulkActionBar');
    
    if (checkboxes.length > 0) {
        bar.classList.remove('hidden');
        document.getElementById('selectedCount').textContent = checkboxes.length;
    } else {
        bar.classList.add('hidden');
    }
}

// Select all checkbox
function toggleSelectAll() {
    const selectAll = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.equipment-checkbox');
    
    checkboxes.forEach(cb => {
        cb.checked = selectAll.checked;
    });
    
    toggleBulkActionBar();
}

// Bulk action
function bulkAction(action) {
    const checkboxes = document.querySelectorAll('.equipment-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => cb.value);
    
    if (ids.length === 0) return;
    
    openConfirmModal(
        `Confirm ${action.replace('_', ' ')}`,
        `This will ${action.replace('_', ' ')} ${ids.length} item(s). Continue?`,
        () => {
            showLoading();
            const bulkActionUrl = window.ITAM_CONFIG?.bulkActionUrl || '/inventory/equipment/bulk-action/';
            fetch(bulkActionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': window.ITAM_CONFIG?.csrfToken || ''
                },
                body: `action=${action}&equipment_ids=${ids.join('&equipment_ids=')}`
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.status === 'success') {
                    showToast(data.message);
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showToast(data.message || 'Error', 'error');
                }
            })
            .catch(error => {
                hideLoading();
                showToast('An error occurred', 'error');
            });
        }
    );
}

// QR Code Search
function startQRScan() {
    document.getElementById('qrModal').classList.remove('hidden');
    document.getElementById('qrSearchInput').focus();
    
    // ESC key support
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeQRModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

function closeQRModal() {
    document.getElementById('qrModal').classList.add('hidden');
    document.getElementById('qrSearchInput').value = '';
}

function submitQRSearch() {
    const searchValue = document.getElementById('qrSearchInput').value.trim();
    if (searchValue) {
        const searchInput = document.querySelector('input[name="search"]');
        searchInput.value = searchValue;
        closeQRModal();
        searchInput.closest('form').submit();
    }
}

// Enter key to submit QR search
document.addEventListener('DOMContentLoaded', () => {
    const qrInput = document.getElementById('qrSearchInput');
    if (qrInput) {
        qrInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                submitQRSearch();
            }
        });
    }
    
    // Initialize checkboxes if they exist
    const checkboxes = document.querySelectorAll('.equipment-checkbox');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', toggleBulkActionBar);
    });
});
