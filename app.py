from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
from datetime import datetime
from redis_client import RedisClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'redis-pubsub-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global Redis client instance
redis_client = RedisClient()

# Message history storage (in-memory)
message_history = []


def on_redis_message(channel: str, data):
    """Callback function when Redis message is received"""
    message_entry = {
        'timestamp': datetime.now().isoformat(),
        'channel': channel,
        'data': data,
        'type': 'received'
    }
    message_history.append(message_entry)
    # Keep only last 100 messages
    if len(message_history) > 100:
        message_history.pop(0)
    
    # Emit to all connected clients
    socketio.emit('redis_message', message_entry)


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connection_status', {'connected': True})
    # Send current connection status
    emit('redis_connection_status', {
        'connected': redis_client.is_connected(),
        'channels': list(redis_client.subscribed_channels)
    })
    # Send message history
    emit('message_history', message_history[-50:])  # Last 50 messages


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass


@socketio.on('redis_connect')
def handle_redis_connect(data):
    """Handle Redis connection request"""
    host = data.get('host', 'localhost')
    port = int(data.get('port', 6379))
    password = data.get('password', '')
    db = int(data.get('db', 0))
    
    success, message = redis_client.connect(host, port, password, db)
    
    emit('redis_connection_result', {
        'success': success,
        'message': message,
        'connected': redis_client.is_connected()
    })


@socketio.on('redis_disconnect')
def handle_redis_disconnect():
    """Handle Redis disconnection request"""
    redis_client.disconnect()
    emit('redis_connection_result', {
        'success': True,
        'message': 'Disconnected from Redis',
        'connected': False
    })
    socketio.emit('redis_connection_status', {
        'connected': False,
        'channels': []
    })


@socketio.on('redis_publish')
def handle_redis_publish(data):
    """Handle publish message request"""
    channel = data.get('channel', '')
    message = data.get('message', {})
    
    if not channel:
        emit('publish_result', {
            'success': False,
            'message': 'Channel name is required'
        })
        return
    
    # Validate JSON message
    if isinstance(message, str):
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            emit('publish_result', {
                'success': False,
                'message': 'Invalid JSON format'
            })
            return
    
    success, result_message = redis_client.publish(channel, message)
    
    if success:
        # Add to history
        message_entry = {
            'timestamp': datetime.now().isoformat(),
            'channel': channel,
            'data': message,
            'type': 'sent'
        }
        message_history.append(message_entry)
        if len(message_history) > 100:
            message_history.pop(0)
        
        # Emit to all clients
        socketio.emit('redis_message', message_entry)
    
    emit('publish_result', {
        'success': success,
        'message': result_message
    })


@socketio.on('redis_subscribe')
def handle_redis_subscribe(data):
    """Handle subscribe to channel request"""
    channel = data.get('channel', '')
    
    if not channel:
        emit('subscribe_result', {
            'success': False,
            'message': 'Channel name is required'
        })
        return
    
    success, result_message = redis_client.subscribe(channel, on_redis_message)
    
    emit('subscribe_result', {
        'success': success,
        'message': result_message,
        'channel': channel
    })
    
    # Update all clients with current subscription status
    socketio.emit('redis_connection_status', {
        'connected': redis_client.is_connected(),
        'channels': list(redis_client.subscribed_channels)
    })


@socketio.on('redis_unsubscribe')
def handle_redis_unsubscribe(data):
    """Handle unsubscribe from channel request"""
    channel = data.get('channel', '')
    
    if not channel:
        emit('unsubscribe_result', {
            'success': False,
            'message': 'Channel name is required'
        })
        return
    
    success, result_message = redis_client.unsubscribe(channel)
    
    emit('unsubscribe_result', {
        'success': success,
        'message': result_message,
        'channel': channel
    })
    
    # Update all clients with current subscription status
    socketio.emit('redis_connection_status', {
        'connected': redis_client.is_connected(),
        'channels': list(redis_client.subscribed_channels)
    })


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

