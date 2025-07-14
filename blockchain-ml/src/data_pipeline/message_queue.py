"""
Redis Message Queue Handler

Handles message queuing and buffering for the blockchain data pipeline
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
messages_queued = Counter(
    "blockchain_messages_queued_total",
    "Total number of messages queued",
    ["message_type"]
)

messages_processed = Counter(
    "blockchain_messages_processed_total",
    "Total number of messages processed from queue",
    ["message_type"]
)

queue_processing_time = Histogram(
    "blockchain_queue_processing_seconds",
    "Time spent processing messages from queue"
)


class RedisMessageQueue:
    """Redis-based message queue for blockchain data"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        queue_name: str = "blockchain_messages",
        batch_size: int = 100,
        flush_interval: int = 30
    ):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("Disconnected from Redis")
    
    async def enqueue_message(self, message: Dict[str, Any], priority: int = 0) -> None:
        """Add message to queue"""
        if not self.is_connected:
            raise ConnectionError("Not connected to Redis")
        
        try:
            # Add timestamp and priority to message
            message_data = {
                "data": message,
                "timestamp": asyncio.get_event_loop().time(),
                "priority": priority
            }
            
            # Serialize message
            message_json = json.dumps(message_data)
            
            # Add to Redis sorted set with timestamp as score
            await self.redis_client.zadd(
                self.queue_name,
                {message_json: message_data["timestamp"]}
            )
            
            # Update metrics
            message_type = message.get("op", "unknown")
            messages_queued.labels(message_type=message_type).inc()
            
            logger.debug(f"Queued message: {message_type}")
            
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            raise
    
    async def dequeue_message(self) -> Optional[Dict[str, Any]]:
        """Get next message from queue"""
        if not self.is_connected:
            raise ConnectionError("Not connected to Redis")
        
        try:
            # Get message with lowest score (oldest)
            messages = await self.redis_client.zrange(
                self.queue_name,
                0,
                0,
                withscores=True
            )
            
            if not messages:
                return None
            
            message_json, score = messages[0]
            message_data = json.loads(message_json)
            
            # Remove message from queue
            await self.redis_client.zrem(self.queue_name, message_json)
            
            # Update metrics
            message_type = message_data["data"].get("op", "unknown")
            messages_processed.labels(message_type=message_type).inc()
            
            logger.debug(f"Dequeued message: {message_type}")
            
            return message_data["data"]
            
        except Exception as e:
            logger.error(f"Failed to dequeue message: {e}")
            raise
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        if not self.is_connected:
            return 0
        
        try:
            return await self.redis_client.zcard(self.queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0
    
    async def clear_queue(self) -> None:
        """Clear all messages from queue"""
        if not self.is_connected:
            return
        
        try:
            await self.redis_client.delete(self.queue_name)
            logger.info("Queue cleared")
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        if not self.is_connected:
            return {"size": 0, "connected": False}
        
        try:
            size = await self.get_queue_size()
            return {
                "size": size,
                "connected": True,
                "queue_name": self.queue_name,
                "redis_url": self.redis_url
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"size": 0, "connected": False, "error": str(e)}
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


class MessageProcessor:
    """Process messages from the queue"""
    
    def __init__(self, queue: RedisMessageQueue, processor_func=None):
        self.queue = queue
        self.processor_func = processor_func
        self.running = False
        
    async def start_processing(self) -> None:
        """Start processing messages from queue"""
        self.running = True
        logger.info("Starting message processor")
        
        while self.running:
            try:
                # Get message from queue
                message = await self.queue.dequeue_message()
                
                if message is None:
                    # No messages, wait a bit
                    await asyncio.sleep(1)
                    continue
                
                # Process message
                start_time = asyncio.get_event_loop().time()
                
                if self.processor_func:
                    await self.processor_func(message)
                
                # Record processing time
                processing_time = asyncio.get_event_loop().time() - start_time
                queue_processing_time.observe(processing_time)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await asyncio.sleep(1)
    
    async def stop_processing(self) -> None:
        """Stop processing messages"""
        self.running = False
        logger.info("Stopping message processor") 