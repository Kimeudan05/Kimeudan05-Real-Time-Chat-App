// static/js/chat_websocket.js
class ChatWebSocket {
    constructor(roomId, userId) {
        this.roomId = roomId;
        this.userId = userId;
        this.socket = null;
        this.typingTimeout = null;
        this.typingUsers = new Set();
        this.messageCallbacks = [];
        this.typingCallbacks = [];
        this.statusCallbacks = [];
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/chat/${this.roomId}/`;

        this.socket = new WebSocket(url);

        this.socket.onopen = (e) => {
            console.log('Chat WebSocket connected');
            this.onOpen(e);
        };

        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleMessage(data);
        };

        this.socket.onclose = (e) => {
            console.log('Chat WebSocket disconnected, reconnecting...');
            this.onClose(e);
            setTimeout(() => this.connect(), 3000);
        };

        this.socket.onerror = (err) => {
            console.error('Chat WebSocket error:', err);
            this.onError(err);
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }

    sendMessage(content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'message',
                message: content,
                sender_id: this.userId,
            }));
        }
    }

    sendTypingIndicator(isTyping) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'typing',
                is_typing: isTyping,
            }));
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'message':
                this.messageCallbacks.forEach(callback => callback(data));
                break;
            case 'typing':
                this.typingCallbacks.forEach(callback => callback(data));
                break;
            case 'user_status':
                this.statusCallbacks.forEach(callback => callback(data));
                break;
        }
    }

    onMessage(callback) {
        this.messageCallbacks.push(callback);
    }

    onTyping(callback) {
        this.typingCallbacks.push(callback);
    }

    onStatusChange(callback) {
        this.statusCallbacks.push(callback);
    }

    onOpen(callback) {
        if (callback) callback();
    }

    onClose(callback) {
        if (callback) callback();
    }

    onError(callback) {
        if (callback) callback();
    }

    // Utility method to detect typing
    setupTypingDetection(inputElement, delay = 1000) {
        inputElement.addEventListener('input', () => {
            if (this.typingTimeout) {
                clearTimeout(this.typingTimeout);
            }

            this.sendTypingIndicator(true);

            this.typingTimeout = setTimeout(() => {
                this.sendTypingIndicator(false);
            }, delay);
        });
    }
}

class OnlineStatusSocket {
    constructor() {
        this.socket = null;
        this.callbacks = [];
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/online/`;

        this.socket = new WebSocket(url);

        this.socket.onopen = (e) => {
            console.log('Online status WebSocket connected');
        };

        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.callbacks.forEach(callback => callback(data));
        };

        this.socket.onclose = (e) => {
            console.log('Online status WebSocket disconnected, reconnecting...');
            setTimeout(() => this.connect(), 3000);
        };

        this.socket.onerror = (err) => {
            console.error('Online status WebSocket error:', err);
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }

    onStatusChange(callback) {
        this.callbacks.push(callback);
    }
}