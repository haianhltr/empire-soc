
// Popup script
document.addEventListener('DOMContentLoaded', () => {
    const statusDiv = document.getElementById('status');
    const exportBtn = document.getElementById('export');
    const clearBtn = document.getElementById('clear');
    
    // Check connection status
    chrome.storage.local.get(['csgoempire_token', 'last_updated'], (result) => {
        if (result.csgoempire_token && result.last_updated) {
            const timeDiff = Date.now() - result.last_updated;
            if (timeDiff < 60000) { // Less than 1 minute
                statusDiv.textContent = 'Connected';
                statusDiv.className = 'status connected';
            } else {
                statusDiv.textContent = 'Token Expired';
                statusDiv.className = 'status disconnected';
            }
        } else {
            statusDiv.textContent = 'Not Connected';
            statusDiv.className = 'status disconnected';
        }
    });
    
    // Export data
    exportBtn.addEventListener('click', () => {
        chrome.storage.local.get(['websocket_messages'], (result) => {
            if (result.websocket_messages) {
                const dataStr = JSON.stringify(result.websocket_messages, null, 2);
                const blob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'csgoempire_websocket_data.json';
                a.click();
                URL.revokeObjectURL(url);
            }
        });
    });
    
    // Clear data
    clearBtn.addEventListener('click', () => {
        chrome.storage.local.clear(() => {
            statusDiv.textContent = 'Data Cleared';
            statusDiv.className = 'status disconnected';
        });
    });
});
