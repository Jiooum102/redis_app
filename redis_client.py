import redis
import json
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscribed_channels = set()
        self.message_callback: Optional[Callable] = None
        self.listener_thread: Optional[threading.Thread] = None
        self.is_listening = False

    def connect(self, host: str, port: int, password: str, db: int = 0) -> tuple[bool, str]:
        """Connect to Redis server"""
        try:
            self.disconnect()
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                password=password if password else None,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            return True, "Connected successfully"
        except redis.ConnectionError as e:
            return False, f"Connection failed: {str(e)}"
        except redis.AuthenticationError as e:
            return False, f"Authentication failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def disconnect(self):
        """Disconnect from Redis and stop listening"""
        self.stop_listening()
        if self.pubsub:
            try:
                self.pubsub.close()
            except:
                pass
            self.pubsub = None
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
            self.redis_client = None
        self.subscribed_channels.clear()

    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False

    def publish(self, channel: str, message: dict) -> tuple[bool, str]:
        """Publish a JSON message to a Redis channel"""
        if not self.is_connected():
            return False, "Not connected to Redis"
        
        try:
            message_str = json.dumps(message)
            self.redis_client.publish(channel, message_str)
            return True, "Message published successfully"
        except Exception as e:
            return False, f"Publish failed: {str(e)}"

    def subscribe(self, channel: str, callback: Callable) -> tuple[bool, str]:
        """Subscribe to a Redis channel"""
        if not self.is_connected():
            return False, "Not connected to Redis"
        
        if channel in self.subscribed_channels:
            return True, f"Already subscribed to {channel}"
        
        try:
            if not self.pubsub:
                self.pubsub = self.redis_client.pubsub()
            
            self.pubsub.subscribe(channel)
            self.subscribed_channels.add(channel)
            self.message_callback = callback
            
            if not self.is_listening:
                self.start_listening()
            
            return True, f"Subscribed to {channel}"
        except Exception as e:
            return False, f"Subscribe failed: {str(e)}"

    def unsubscribe(self, channel: str) -> tuple[bool, str]:
        """Unsubscribe from a Redis channel"""
        if channel not in self.subscribed_channels:
            return True, f"Not subscribed to {channel}"
        
        try:
            if self.pubsub:
                self.pubsub.unsubscribe(channel)
            self.subscribed_channels.discard(channel)
            
            if len(self.subscribed_channels) == 0:
                self.stop_listening()
            
            return True, f"Unsubscribed from {channel}"
        except Exception as e:
            return False, f"Unsubscribe failed: {str(e)}"

    def start_listening(self):
        """Start listening thread for pub/sub messages"""
        if self.is_listening or not self.pubsub:
            return
        
        self.is_listening = True
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()

    def stop_listening(self):
        """Stop listening thread"""
        self.is_listening = False
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1)

    def _listen(self):
        """Internal method to listen for messages"""
        try:
            logger.info('Started listening for Redis pub/sub messages')
            for message in self.pubsub.listen():
                if not self.is_listening:
                    break
                
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        logger.debug(f'Received message on channel {message["channel"]}: {data}')
                        if self.message_callback:
                            self.message_callback(message['channel'], data)
                    except json.JSONDecodeError:
                        # If message is not JSON, send as string
                        logger.debug(f'Received non-JSON message on channel {message["channel"]}: {message["data"]}')
                        if self.message_callback:
                            self.message_callback(message['channel'], message['data'])
        except Exception as e:
            logger.error(f'Error in Redis pub/sub listener: {e}')
            if self.message_callback:
                self.message_callback('_error', {'error': str(e)})
        finally:
            logger.info('Stopped listening for Redis pub/sub messages')

