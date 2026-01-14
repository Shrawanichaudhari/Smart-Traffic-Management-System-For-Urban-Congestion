import os
import json
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
import redis.asyncio as redis
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("redis_service")

class RedisPubSubService:
    """
    Service for Redis Pub/Sub communication between ML models and backend.
    Handles subscribing to channels and publishing messages.
    """
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self.pubsub = None
        self.subscribers = {}
        self.running_tasks = []
        self.connected = False
        
    async def connect(self):
        """
        Connect to Redis server and initialize PubSub.
        """
        try:
            self.redis_client = await redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            self.connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """
        Disconnect from Redis and clean up resources.
        """
        try:
            # Cancel all running subscription tasks
            for task in self.running_tasks:
                task.cancel()
            
            # Close PubSub and Redis client
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            self.connected = False
            logger.info("Disconnected from Redis")
        except Exception as e:
            logger.error(f"Error during Redis disconnect: {e}")
    
    async def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a Redis channel.
        
        Args:
            channel: The Redis channel to publish to
            message: The message to publish (will be converted to JSON)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            await self.connect()
        
        try:
            # Add timestamp if not present
            if isinstance(message, dict) and "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()
            
            # Convert message to JSON string
            json_message = json.dumps(message)
            
            # Publish to Redis
            result = await self.redis_client.publish(channel, json_message)
            logger.debug(f"Published message to {channel}, receivers: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to {channel}: {e}")
            return False
    
    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to a Redis channel and process messages with the provided callback.
        
        Args:
            channel: The Redis channel to subscribe to
            callback: Function to call with each received message
        """
        if not self.connected:
            await self.connect()
        
        # Add callback to subscribers dict
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
        
        # Subscribe to the channel if not already subscribed
        await self.pubsub.subscribe(channel)
        
        # Start a task to listen for messages
        task = asyncio.create_task(self._message_listener(channel))
        self.running_tasks.append(task)
        
        logger.info(f"Subscribed to channel: {channel}")
    
    async def _message_listener(self, channel: str):
        """
        Internal listener for Redis messages on a specific channel.
        
        Args:
            channel: The Redis channel to listen on
        """
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message is not None and message["type"] == "message":
                    # Parse the JSON message
                    try:
                        data = json.loads(message["data"])
                        
                        # Call all subscribers for this channel
                        if channel in self.subscribers:
                            for callback in self.subscribers[channel]:
                                await callback(data)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode JSON message: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info(f"Message listener for channel {channel} cancelled")
        except Exception as e:
            logger.error(f"Error in message listener for channel {channel}: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            bool: True if connected and operational, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            # Simple ping to check connection
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

# Global instance of the Redis service
redis_service = RedisPubSubService()