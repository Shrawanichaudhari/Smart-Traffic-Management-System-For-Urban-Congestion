import asyncio
import json
import logging
from typing import Dict, Any, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_service")

class WebSocketManager:
    """
    WebSocket connection manager for handling real-time data streaming to clients.
    Maintains active connections and provides broadcasting capabilities.
    """
    
    def __init__(self):
        # Store active connections by client ID and channel
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Track which channels each client is subscribed to
        self.client_subscriptions: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations on connection dictionaries
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Accept a new WebSocket connection and store it.
        
        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the client
        """
        await websocket.accept()
        async with self.lock:
            if client_id not in self.active_connections:
                self.active_connections[client_id] = {}
                self.client_subscriptions[client_id] = set()
            
            # Store the main connection
            self.active_connections[client_id]["main"] = websocket
            logger.info(f"Client {client_id} connected")
    
    async def disconnect(self, client_id: str):
        """
        Remove a client's connections when they disconnect.
        
        Args:
            client_id: Unique identifier for the client
        """
        async with self.lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            
            if client_id in self.client_subscriptions:
                del self.client_subscriptions[client_id]
            
            logger.info(f"Client {client_id} disconnected")
    
    async def subscribe(self, client_id: str, channel: str):
        """
        Subscribe a client to a specific channel.
        
        Args:
            client_id: Unique identifier for the client
            channel: The channel to subscribe to
        """
        async with self.lock:
            if client_id in self.client_subscriptions:
                self.client_subscriptions[client_id].add(channel)
                logger.info(f"Client {client_id} subscribed to {channel}")
                
                # Confirm subscription to the client
                if client_id in self.active_connections and "main" in self.active_connections[client_id]:
                    await self.active_connections[client_id]["main"].send_json({
                        "type": "subscription",
                        "status": "success",
                        "channel": channel
                    })
    
    async def unsubscribe(self, client_id: str, channel: str):
        """
        Unsubscribe a client from a specific channel.
        
        Args:
            client_id: Unique identifier for the client
            channel: The channel to unsubscribe from
        """
        async with self.lock:
            if client_id in self.client_subscriptions and channel in self.client_subscriptions[client_id]:
                self.client_subscriptions[client_id].remove(channel)
                logger.info(f"Client {client_id} unsubscribed from {channel}")
                
                # Confirm unsubscription to the client
                if client_id in self.active_connections and "main" in self.active_connections[client_id]:
                    await self.active_connections[client_id]["main"].send_json({
                        "type": "unsubscription",
                        "status": "success",
                        "channel": channel
                    })
    
    async def broadcast(self, channel: str, message: Dict[str, Any]):
        """
        Broadcast a message to all clients subscribed to a specific channel.
        
        Args:
            channel: The channel to broadcast on
            message: The message to send
        """
        disconnected_clients = []
        
        # Prepare the message with channel information
        full_message = {
            "channel": channel,
            "data": message,
            "timestamp": message.get("timestamp", None)
        }
        
        async with self.lock:
            # Find all clients subscribed to this channel
            for client_id, subscriptions in self.client_subscriptions.items():
                if channel in subscriptions and client_id in self.active_connections:
                    try:
                        # Send the message to the client
                        websocket = self.active_connections[client_id].get("main")
                        if websocket:
                            await websocket.send_json(full_message)
                    except WebSocketDisconnect:
                        # Mark for removal if disconnected
                        disconnected_clients.append(client_id)
                    except Exception as e:
                        logger.error(f"Error sending message to client {client_id}: {e}")
                        disconnected_clients.append(client_id)
        
        # Clean up any disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def send_personal_message(self, client_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific client.
        
        Args:
            client_id: Unique identifier for the client
            message: The message to send
        """
        async with self.lock:
            if client_id in self.active_connections and "main" in self.active_connections[client_id]:
                try:
                    await self.active_connections[client_id]["main"].send_json(message)
                except Exception as e:
                    logger.error(f"Error sending personal message to client {client_id}: {e}")
                    await self.disconnect(client_id)
    
    def get_subscribed_clients(self, channel: str) -> List[str]:
        """
        Get a list of client IDs subscribed to a specific channel.
        
        Args:
            channel: The channel to check
            
        Returns:
            List of client IDs subscribed to the channel
        """
        subscribed_clients = []
        for client_id, subscriptions in self.client_subscriptions.items():
            if channel in subscriptions:
                subscribed_clients.append(client_id)
        return subscribed_clients
    
    def get_active_channels(self) -> Set[str]:
        """
        Get a set of all active channels with at least one subscriber.
        
        Returns:
            Set of active channel names
        """
        active_channels = set()
        for subscriptions in self.client_subscriptions.values():
            active_channels.update(subscriptions)
        return active_channels

# Global instance of the WebSocket manager
websocket_manager = WebSocketManager()