"""
WebSocket Client for Blockchain.info API

Handles real-time connection to Blockchain.info WebSocket API
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import websockets
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
messages_received = Counter(
    "blockchain_messages_received_total",
    "Total number of messages received from WebSocket",
    ["message_type"]
)

connection_duration = Histogram(
    "blockchain_websocket_connection_duration_seconds",
    "Duration of WebSocket connections"
)

message_processing_time = Histogram(
    "blockchain_message_processing_seconds",
    "Time spent processing messages"
)


class BlockchainWebSocketClient:
    """WebSocket client for Blockchain.info API"""
    
    def __init__(
        self,
        url: str = "wss://ws.blockchain.info/inv",
        message_handler: Optional[Callable[[Dict[str, Any]], None]] = None,
        reconnect_interval: int = 5,
        max_reconnect_attempts: int = 10
    ):
        self.url = url
        self.message_handler = message_handler
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        
    async def connect(self) -> None:
        """Establish WebSocket connection"""
        try:
            logger.info(f"Connecting to {self.url}")
            self.websocket = await websockets.connect(self.url)
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("Successfully connected to Blockchain.info WebSocket")
            
            # Send ping to test connection
            await self.send_ping()
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            await self.handle_reconnect()
    
    async def disconnect(self) -> None:
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from Blockchain.info WebSocket")
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to WebSocket"""
        if not self.is_connected or not self.websocket:
            logger.error("Not connected to WebSocket")
            return
            
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent message: {message}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            await self.handle_reconnect()
    
    async def send_ping(self) -> None:
        """Send ping message"""
        await self.send_message({"op": "ping"})
    
    async def subscribe_unconfirmed_transactions(self) -> None:
        """Subscribe to unconfirmed transactions"""
        await self.send_message({"op": "unconfirmed_sub"})
        logger.info("Subscribed to unconfirmed transactions")
    
    async def unsubscribe_unconfirmed_transactions(self) -> None:
        """Unsubscribe from unconfirmed transactions"""
        await self.send_message({"op": "unconfirmed_unsub"})
        logger.info("Unsubscribed from unconfirmed transactions")
    
    async def subscribe_address(self, address: str) -> None:
        """Subscribe to specific address"""
        await self.send_message({"op": "addr_sub", "addr": address})
        logger.info(f"Subscribed to address: {address}")
    
    async def unsubscribe_address(self, address: str) -> None:
        """Unsubscribe from specific address"""
        await self.send_message({"op": "addr_unsub", "addr": address})
        logger.info(f"Unsubscribed from address: {address}")
    
    async def subscribe_blocks(self) -> None:
        """Subscribe to new blocks"""
        await self.send_message({"op": "blocks_sub"})
        logger.info("Subscribed to new blocks")
    
    async def unsubscribe_blocks(self) -> None:
        """Unsubscribe from new blocks"""
        await self.send_message({"op": "blocks_unsub"})
        logger.info("Unsubscribed from new blocks")
    
    async def listen(self) -> None:
        """Listen for incoming messages"""
        if not self.websocket:
            logger.error("Not connected to WebSocket")
            return
            
        try:
            async for message in self.websocket:
                await self.process_message(message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.debug(f"WebSocket connection closed: {e}")
            self.is_connected = False
            if self.reconnect_attempts < self.max_reconnect_attempts:
                await self.handle_reconnect()
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
            self.is_connected = False
            await self.handle_reconnect()
    
    async def process_message(self, message: str) -> None:
        """Process incoming message"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            data = json.loads(message)
            message_type = data.get("op", "unknown")
            
            # Update metrics
            messages_received.labels(message_type=message_type).inc()
            
            logger.debug(f"Received message: {message_type}")
            
            # Handle different message types
            if message_type == "utx":
                await self.handle_unconfirmed_transaction(data)
            elif message_type == "block":
                await self.handle_new_block(data)
            elif message_type == "ping":
                await self.handle_ping_response(data)
            else:
                logger.debug(f"Unhandled message type: {message_type}")
            
            # Call custom message handler if provided
            if self.message_handler:
                await asyncio.create_task(self.message_handler(data))
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
        finally:
            # Record processing time
            processing_time = asyncio.get_event_loop().time() - start_time
            message_processing_time.observe(processing_time)
    
    async def handle_unconfirmed_transaction(self, data: Dict[str, Any]) -> None:
        """Handle unconfirmed transaction message"""
        transaction = data.get("x", {})
        tx_hash = transaction.get("hash", "unknown")
        logger.info(f"Unconfirmed transaction: {tx_hash}")
        
        # TODO: Add transaction processing logic
        # This will be implemented in the data processor
    
    async def handle_new_block(self, data: Dict[str, Any]) -> None:
        """Handle new block message"""
        block = data.get("x", {})
        block_hash = block.get("hash", "unknown")
        height = block.get("height", "unknown")
        logger.info(f"New block: {block_hash} (height: {height})")
        
        # TODO: Add block processing logic
        # This will be implemented in the data processor
    
    async def handle_ping_response(self, data: Dict[str, Any]) -> None:
        """Handle ping response"""
        logger.debug("Received ping response")
    
    async def handle_reconnect(self) -> None:
        """Handle reconnection logic"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return
            
        self.reconnect_attempts += 1
        self.is_connected = False
        
        logger.info(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts}) in {self.reconnect_interval} seconds...")
        await asyncio.sleep(self.reconnect_interval)
        
        try:
            await self.connect()
            if self.is_connected:
                logger.info("Successfully reconnected to WebSocket")
                self.reconnect_attempts = 0  # Reset counter on successful reconnection
        except Exception as e:
            logger.debug(f"Reconnection attempt {self.reconnect_attempts} failed: {e}")
            await self.handle_reconnect()
    
    async def run(self) -> None:
        """Main run loop"""
        await self.connect()
        
        if self.is_connected:
            # Subscribe to default channels
            await self.subscribe_unconfirmed_transactions()
            await self.subscribe_blocks()
            
            # Start listening for messages
            await self.listen()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect() 