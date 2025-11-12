from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from redis_client import RedisClient

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'redis-pubsub-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global Redis client instance
redis_client = RedisClient()

# Message history storage (in-memory)
message_history = []


def on_redis_message(channel: str, data):
    """Callback function when Redis message is received"""
    logger.info(f'Received message on channel {channel}')
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
    logger.info('Client connected')
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
    logger.info('Client disconnected')


@socketio.on('redis_connect')
def handle_redis_connect(data):
    """Handle Redis connection request"""
    host = data.get('host', 'localhost')
    port = int(data.get('port', 6379))
    password = data.get('password', '')
    db = int(data.get('db', 0))
    
    logger.info(f'Attempting to connect to Redis at {host}:{port} (db={db})')
    success, message = redis_client.connect(host, port, password, db)
    
    if success:
        logger.info(f'Successfully connected to Redis at {host}:{port}')
    else:
        logger.warning(f'Failed to connect to Redis at {host}:{port}: {message}')
    
    emit('redis_connection_result', {
        'success': success,
        'message': message,
        'connected': redis_client.is_connected()
    })


@socketio.on('redis_disconnect')
def handle_redis_disconnect():
    """Handle Redis disconnection request"""
    logger.info('Disconnecting from Redis')
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
        logger.warning('Publish attempt without channel name')
        emit('publish_result', {
            'success': False,
            'message': 'Channel name is required'
        })
        return
    
    # Validate JSON message
    if isinstance(message, str):
        try:
            message = json.loads(message)
        except json.JSONDecodeError as e:
            logger.warning(f'Invalid JSON format in publish message: {e}')
            emit('publish_result', {
                'success': False,
                'message': 'Invalid JSON format'
            })
            return
    
    logger.info(f'Publishing message to channel: {channel}')
    success, result_message = redis_client.publish(channel, message)
    
    if success:
        logger.info(f'Message published successfully to channel: {channel}')
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
    else:
        logger.error(f'Failed to publish message to channel {channel}: {result_message}')
    
    emit('publish_result', {
        'success': success,
        'message': result_message
    })


@socketio.on('redis_subscribe')
def handle_redis_subscribe(data):
    """Handle subscribe to channel request"""
    channel = data.get('channel', '')
    
    if not channel:
        logger.warning('Subscribe attempt without channel name')
        emit('subscribe_result', {
            'success': False,
            'message': 'Channel name is required'
        })
        return
    
    logger.info(f'Subscribing to channel: {channel}')
    success, result_message = redis_client.subscribe(channel, on_redis_message)
    
    if success:
        logger.info(f'Successfully subscribed to channel: {channel}')
    else:
        logger.warning(f'Failed to subscribe to channel {channel}: {result_message}')
    
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
        logger.warning('Unsubscribe attempt without channel name')
        emit('unsubscribe_result', {
            'success': False,
            'message': 'Channel name is required'
        })
        return
    
    logger.info(f'Unsubscribing from channel: {channel}')
    success, result_message = redis_client.unsubscribe(channel)
    
    if success:
        logger.info(f'Successfully unsubscribed from channel: {channel}')
    else:
        logger.warning(f'Failed to unsubscribe from channel {channel}: {result_message}')
    
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
    # Get configuration from environment variables
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))
    
    if debug_mode:
        # Development server
        logger.info(f'Starting Flask development server on {host}:{port}')
        socketio.run(app, debug=True, host=host, port=port)
    else:
        # Production mode - use gunicorn instead
        logger.warning('Running in production mode. Use gunicorn for deployment:')
        logger.warning('gunicorn --worker-class gevent --worker-connections 1000 -w 1 --bind 0.0.0.0:5000 app:app')
        logger.info(f'Starting Flask server in production mode on {host}:{port}')
        socketio.run(app, debug=False, host=host, port=port)

