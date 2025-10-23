
// Background script to handle WebSocket data
console.log('CSGOEmpire WebSocket Monitor background script loaded');

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'websocket_detected') {
        console.log('WebSocket detected:', message.url);
        console.log('Token:', message.token.substring(0, 50) + '...');
        console.log('UID:', message.uid);
        
        // Store the token
        chrome.storage.local.set({
            'csgoempire_token': message.token,
            'csgoempire_uid': message.uid,
            'last_updated': Date.now()
        });
        
        // Send to external application (if needed)
        // This could send data to a local server or save to file
    }
    
    if (message.type === 'websocket_message') {
        console.log('WebSocket message:', message.data);
        
        // Store the message
        chrome.storage.local.get(['websocket_messages'], (result) => {
            const messages = result.websocket_messages || [];
            messages.push({
                data: message.data,
                url: message.url,
                timestamp: Date.now()
            });
            
            // Keep only last 100 messages
            if (messages.length > 100) {
                messages.splice(0, messages.length - 100);
            }
            
            chrome.storage.local.set({
                'websocket_messages': messages
            });
        });
    }
});

// Periodically save data to file (if possible)
setInterval(() => {
    chrome.storage.local.get(['websocket_messages'], (result) => {
        if (result.websocket_messages && result.websocket_messages.length > 0) {
            console.log('Saving WebSocket messages to file...');
            // This would need additional permissions to write files
        }
    });
}, 30000); // Every 30 seconds
