// Socket.IO connection
const socket = io();

// State management
let isRedisConnected = false;
let subscribedChannels = new Set();
let messageCount = 0;

// DOM elements
const connectionStatus = document.getElementById('connectionStatus');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const redisConnectionForm = document.getElementById('redisConnectionForm');
const connectBtn = document.getElementById('connectBtn');
const disconnectBtn = document.getElementById('disconnectBtn');
const connectionMessage = document.getElementById('connectionMessage');
const subscribeChannel = document.getElementById('subscribeChannel');
const subscribeBtn = document.getElementById('subscribeBtn');
const subscribedChannelsDiv = document.getElementById('subscribedChannels');
const subscribeMessage = document.getElementById('subscribeMessage');
const publishForm = document.getElementById('publishForm');
const channelSelector = document.getElementById('channelSelector');
const publishChannel = document.getElementById('publishChannel');
const jsonFieldsContainer = document.getElementById('jsonFieldsContainer');
const addFieldBtn = document.getElementById('addFieldBtn');
const publishResultMessage = document.getElementById('publishResultMessage');
const publishBtn = document.getElementById('publishBtn');
const messagesContainer = document.getElementById('messagesContainer');
const messageCountSpan = document.getElementById('messageCount');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateConnectionStatus(false);
});

socket.on('connection_status', (data) => {
    console.log('Connection status:', data);
});

socket.on('redis_connection_status', (data) => {
    isRedisConnected = data.connected;
    subscribedChannels = new Set(data.channels || []);
    updateConnectionStatus(data.connected);
    updateSubscribedChannels();
    updateButtonStates();
    updateChannelSelector();
});

socket.on('redis_connection_result', (data) => {
    isRedisConnected = data.connected;
    updateConnectionStatus(data.connected);
    showMessage(connectionMessage, data.message, data.success);
    updateButtonStates();
    updateChannelSelector();
});

socket.on('subscribe_result', (data) => {
    if (data.success) {
        subscribedChannels.add(data.channel);
        updateSubscribedChannels();
        subscribeChannel.value = '';
    }
    showMessage(subscribeMessage, data.message, data.success);
});

socket.on('unsubscribe_result', (data) => {
    if (data.success) {
        subscribedChannels.delete(data.channel);
        updateSubscribedChannels();
    }
    showMessage(subscribeMessage, data.message, data.success);
});

socket.on('publish_result', (data) => {
    showMessage(publishResultMessage, data.message, data.success);
});

socket.on('redis_message', (message) => {
    addMessageToDisplay(message);
});

socket.on('message_history', (messages) => {
    messagesContainer.innerHTML = '';
    messageCount = 0;
    messages.forEach(msg => {
        addMessageToDisplay(msg);
    });
});

// Form handlers
redisConnectionForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(redisConnectionForm);
    const connectionData = {
        host: formData.get('host'),
        port: parseInt(formData.get('port')),
        password: formData.get('password'),
        db: parseInt(formData.get('db')) || 0
    };
    
    socket.emit('redis_connect', connectionData);
});

disconnectBtn.addEventListener('click', () => {
    socket.emit('redis_disconnect');
});

subscribeBtn.addEventListener('click', () => {
    const channel = subscribeChannel.value.trim();
    if (channel) {
        socket.emit('redis_subscribe', { channel });
    }
});

publishForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const channel = publishChannel.value.trim();
    
    if (!channel) {
        showMessage(publishResultMessage, 'Channel name is required', false);
        return;
    }
    
    // Build JSON object from form fields
    const message = buildJsonFromFields();
    
    if (Object.keys(message).length === 0) {
        showMessage(publishResultMessage, 'At least one field is required', false);
        return;
    }
    
    // Cache the form data
    cacheFormData(channel, message);
    
    socket.emit('redis_publish', { channel, message });
    
    // Clear channel but keep form fields for easy editing
    publishChannel.value = '';
});

clearHistoryBtn.addEventListener('click', () => {
    messagesContainer.innerHTML = '<p class="empty-message">No messages yet. Connect to Redis and start publishing or subscribing.</p>';
    messageCount = 0;
    updateMessageCount();
});

channelSelector.addEventListener('change', (e) => {
    if (e.target.value) {
        const selectedChannel = e.target.value;
        publishChannel.value = selectedChannel;
        
        // Load cached data for this channel
        loadCachedFormDataForChannel(selectedChannel);
        
        // Reset selector to placeholder after selection
        e.target.value = '';
    }
});

addFieldBtn.addEventListener('click', () => {
    addJsonField();
});

// Auto-save form data as user types
jsonFieldsContainer.addEventListener('input', () => {
    const channel = publishChannel.value.trim();
    if (channel) {
        const message = buildJsonFromFields();
        cacheFormData(channel, message);
    }
});

publishChannel.addEventListener('input', () => {
    const channel = publishChannel.value.trim();
    if (channel) {
        const message = buildJsonFromFields();
        cacheFormData(channel, message);
    }
});

// Load cached data on page load and initialize form
window.addEventListener('load', () => {
    // Ensure at least one field exists
    const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
    if (rows.length === 0) {
        addJsonField();
    } else {
        updateRemoveButtons();
    }
    // Load cached data (will override if exists)
    loadCachedFormData();
});

// Helper functions
function updateConnectionStatus(connected) {
    if (connected) {
        statusIndicator.classList.add('connected');
        statusText.textContent = 'Connected to Redis';
    } else {
        statusIndicator.classList.remove('connected');
        statusText.textContent = 'Not Connected';
    }
}

function updateButtonStates() {
    connectBtn.disabled = isRedisConnected;
    disconnectBtn.disabled = !isRedisConnected;
    subscribeBtn.disabled = !isRedisConnected;
    publishBtn.disabled = !isRedisConnected;
    addFieldBtn.disabled = !isRedisConnected;
    updateChannelSelector();
}

function updateSubscribedChannels() {
    if (subscribedChannels.size === 0) {
        subscribedChannelsDiv.innerHTML = '<p>No active subscriptions</p>';
    } else {
        subscribedChannelsDiv.innerHTML = '';
        subscribedChannels.forEach(channel => {
            const tag = document.createElement('span');
            tag.className = 'channel-tag';
            tag.innerHTML = `
                ${channel}
                <button class="remove-btn" onclick="unsubscribeChannel('${channel}')">×</button>
            `;
            subscribedChannelsDiv.appendChild(tag);
        });
    }
    updateChannelSelector();
}

function updateChannelSelector() {
    // Clear existing options except the first one
    channelSelector.innerHTML = '<option value="">Select from subscribed channels...</option>';
    
    // Enable/disable based on connection and available channels
    if (!isRedisConnected || subscribedChannels.size === 0) {
        channelSelector.disabled = true;
        return;
    }
    
    channelSelector.disabled = false;
    
    // Add subscribed channels as options
    subscribedChannels.forEach(channel => {
        const option = document.createElement('option');
        option.value = channel;
        option.textContent = channel;
        channelSelector.appendChild(option);
    });
}

function unsubscribeChannel(channel) {
    socket.emit('redis_unsubscribe', { channel });
}

function showMessage(element, message, isSuccess) {
    element.textContent = message;
    element.className = 'message ' + (isSuccess ? 'success' : 'error');
    setTimeout(() => {
        element.className = 'message';
        element.textContent = '';
    }, 5000);
}

function addMessageToDisplay(message) {
    if (messagesContainer.querySelector('.empty-message')) {
        messagesContainer.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-item ${message.type}`;
    
    const timestamp = new Date(message.timestamp).toLocaleString();
    const messageType = message.type === 'sent' ? 'SENT' : 'RECEIVED';
    
    let formattedData;
    try {
        formattedData = JSON.stringify(message.data, null, 2);
    } catch (e) {
        formattedData = String(message.data);
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <div>
                <span class="message-type ${message.type}">${messageType}</span>
                <span class="message-channel">#${message.channel}</span>
            </div>
            <span class="message-timestamp">${timestamp}</span>
        </div>
        <div class="message-content">${escapeHtml(formattedData)}</div>
    `;
    
    messagesContainer.insertBefore(messageDiv, messagesContainer.firstChild);
    messageCount++;
    updateMessageCount();
    
    // Keep only last 100 messages in DOM
    while (messagesContainer.children.length > 100) {
        messagesContainer.removeChild(messagesContainer.lastChild);
    }
}

function updateMessageCount() {
    messageCountSpan.textContent = `${messageCount} message${messageCount !== 1 ? 's' : ''}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make unsubscribeChannel available globally for onclick handler
window.unsubscribeChannel = unsubscribeChannel;

// JSON Form Field Management
function addJsonField(key = '', value = '') {
    const fieldRow = document.createElement('div');
    fieldRow.className = 'json-field-row';
    fieldRow.innerHTML = `
        <input type="text" class="json-key" placeholder="Key" value="${escapeHtml(key)}" />
        <input type="text" class="json-value" placeholder="Value" value="${escapeHtml(value)}" />
        <button type="button" class="remove-field-btn" onclick="removeJsonField(this)">×</button>
    `;
    jsonFieldsContainer.appendChild(fieldRow);
    updateRemoveButtons();
}

function removeJsonField(button) {
    const fieldRow = button.closest('.json-field-row');
    if (fieldRow) {
        fieldRow.remove();
        updateRemoveButtons();
        // Auto-save after removal
        const channel = publishChannel.value.trim();
        if (channel) {
            const message = buildJsonFromFields();
            cacheFormData(channel, message);
        }
    }
}

function updateRemoveButtons() {
    const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
    rows.forEach(row => {
        const removeBtn = row.querySelector('.remove-field-btn');
        if (removeBtn) {
            // Disable remove button if only one field remains
            removeBtn.disabled = rows.length <= 1;
        }
    });
}

function buildJsonFromFields() {
    const message = {};
    const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
    
    rows.forEach(row => {
        const keyInput = row.querySelector('.json-key');
        const valueInput = row.querySelector('.json-value');
        
        if (keyInput && valueInput) {
            const key = keyInput.value.trim();
            const value = valueInput.value.trim();
            
            if (key) {
                // Try to parse value as JSON, if fails use as string
                let parsedValue = value;
                if (value) {
                    // Try to detect if it's a number, boolean, or JSON
                    if (value === 'true') {
                        parsedValue = true;
                    } else if (value === 'false') {
                        parsedValue = false;
                    } else if (value === 'null') {
                        parsedValue = null;
                    } else if (!isNaN(value) && value !== '') {
                        // Check if it's a number
                        parsedValue = Number(value);
                    } else if (value.startsWith('{') || value.startsWith('[')) {
                        // Try to parse as JSON
                        try {
                            parsedValue = JSON.parse(value);
                        } catch (e) {
                            // Keep as string if parsing fails
                            parsedValue = value;
                        }
                    }
                }
                message[key] = parsedValue;
            }
        }
    });
    
    return message;
}

function cacheFormData(channel, message) {
    if (!channel) return;
    
    try {
        const cacheKey = 'redis_pubsub_form_cache';
        let cache = {};
        
        // Load existing cache
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
            try {
                cache = JSON.parse(cached);
            } catch (e) {
                cache = {};
            }
        }
        
        // Store form fields structure
        const fields = [];
        const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
        rows.forEach(row => {
            const keyInput = row.querySelector('.json-key');
            const valueInput = row.querySelector('.json-value');
            if (keyInput && valueInput) {
                fields.push({
                    key: keyInput.value.trim(),
                    value: valueInput.value.trim()
                });
            }
        });
        
        // Store both the message and the form structure
        cache[channel] = {
            message: message,
            fields: fields,
            timestamp: new Date().toISOString()
        };
        
        localStorage.setItem(cacheKey, JSON.stringify(cache));
    } catch (e) {
        console.error('Failed to cache form data:', e);
    }
}

function loadCachedFormDataForChannel(channel) {
    try {
        const cacheKey = 'redis_pubsub_form_cache';
        const cached = localStorage.getItem(cacheKey);
        
        if (!cached) {
            // No cache, ensure at least one field exists
            const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
            if (rows.length === 0) {
                addJsonField();
            }
            return;
        }
        
        const cache = JSON.parse(cached);
        
        if (channel && cache[channel]) {
            const data = cache[channel];
            
            // Clear existing fields
            jsonFieldsContainer.innerHTML = '';
            
            // Restore fields
            if (data.fields && data.fields.length > 0) {
                data.fields.forEach(field => {
                    addJsonField(field.key, field.value);
                });
            } else {
                // If no fields structure, create one field
                addJsonField();
            }
        } else {
            // No cache for this channel, ensure at least one field exists
            const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
            if (rows.length === 0) {
                addJsonField();
            }
        }
    } catch (e) {
        console.error('Failed to load cached form data:', e);
        // Ensure at least one field exists
        const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
        if (rows.length === 0) {
            addJsonField();
        }
    }
}

function loadCachedFormData() {
    try {
        const cacheKey = 'redis_pubsub_form_cache';
        const cached = localStorage.getItem(cacheKey);
        
        if (!cached) {
            // No cache, ensure at least one field exists
            const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
            if (rows.length === 0) {
                addJsonField();
            }
            return;
        }
        
        const cache = JSON.parse(cached);
        
        // Find the most recently used channel
        let latestChannel = null;
        let latestTimestamp = null;
        
        for (const [channel, data] of Object.entries(cache)) {
            if (data.timestamp && (!latestTimestamp || data.timestamp > latestTimestamp)) {
                latestTimestamp = data.timestamp;
                latestChannel = channel;
            }
        }
        
        if (latestChannel && cache[latestChannel]) {
            const data = cache[latestChannel];
            
            // Restore channel
            publishChannel.value = latestChannel;
            
            // Load fields for this channel
            loadCachedFormDataForChannel(latestChannel);
        } else {
            // No cache, ensure at least one field exists
            const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
            if (rows.length === 0) {
                addJsonField();
            }
        }
    } catch (e) {
        console.error('Failed to load cached form data:', e);
        // Ensure at least one field exists
        const rows = jsonFieldsContainer.querySelectorAll('.json-field-row');
        if (rows.length === 0) {
            addJsonField();
        }
    }
}

// Make removeJsonField available globally for onclick handler
window.removeJsonField = removeJsonField;

