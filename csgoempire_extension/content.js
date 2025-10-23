
// Content script to monitor WebSocket connections
console.log('CSGOEmpire WebSocket Monitor loaded');

// Override WebSocket constructor to capture connections
const originalWebSocket = window.WebSocket;

window.WebSocket = function(url, protocols) {
    console.log('WebSocket connection detected:', url);
    
    // Check if it's CSGOEmpire WebSocket
    if (url.includes('trade.csgoempire.com') || url.includes('roulette.csgoempire.com')) {
        console.log('CSGOEmpire WebSocket detected:', url);
        
        // Extract token from URL
        const tokenMatch = url.match(/token=([^&]+)/);
        const uidMatch = url.match(/uid=(\d+)/);
        
        if (tokenMatch && uidMatch) {
            const token = tokenMatch[1];
            const uid = uidMatch[1];
            
            console.log('Token extracted:', token.substring(0, 50) + '...');
            console.log('UID:', uid);
            
            // Send to background script
            chrome.runtime.sendMessage({
                type: 'websocket_detected',
                url: url,
                token: token,
                uid: uid
            });
        }
    }
    
    // Create the actual WebSocket
    const ws = new originalWebSocket(url, protocols);
    
    // Monitor messages
    const originalOnMessage = ws.onmessage;
    ws.onmessage = function(event) {
        console.log('WebSocket message received:', event.data);
        
        // Send message data to background script
        chrome.runtime.sendMessage({
            type: 'websocket_message',
            data: event.data,
            url: url
        });
        
        // Call original handler
        if (originalOnMessage) {
            originalOnMessage.call(this, event);
        }
    };
    
    return ws;
};

// Also monitor fetch requests for WebSocket upgrades
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    if (typeof url === 'string' && url.includes('csgoempire.com')) {
        console.log('Fetch request to CSGOEmpire:', url);
    }
    return originalFetch.apply(this, args);
};
