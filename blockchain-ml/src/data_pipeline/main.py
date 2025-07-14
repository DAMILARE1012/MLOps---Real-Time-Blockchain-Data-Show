"""
Main entry point for the data pipeline

Runs the WebSocket client and data processing pipeline
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from prometheus_client import start_http_server

from .websocket_client import BlockchainWebSocketClient
from .message_queue import RedisMessageQueue, MessageProcessor
from .database_handler import DatabaseHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_pipeline.log')
    ]
)

logger = logging.getLogger(__name__)


class DataPipeline:
    """Main data pipeline orchestrator"""
    
    def __init__(
        self, 
        prometheus_port: int = 8001,
        redis_url: str = "redis://localhost:6379",
        database_url: str = "postgresql://blockchain_user:blockchain_password@localhost:5432/blockchain_ml"
    ):
        self.prometheus_port = prometheus_port
        self.redis_url = redis_url
        self.database_url = database_url
        self.websocket_client: Optional[BlockchainWebSocketClient] = None
        self.message_queue: Optional[RedisMessageQueue] = None
        self.database: Optional[DatabaseHandler] = None
        self.message_processor: Optional[MessageProcessor] = None
        self.running = False
        
    async def start_prometheus_server(self) -> None:
        """Start Prometheus metrics server"""
        try:
            start_http_server(self.prometheus_port)
            logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
    
    async def message_handler(self, message: dict) -> None:
        """Custom message handler for processing blockchain data"""
        try:
            # Queue the message for processing
            if self.message_queue:
                await self.message_queue.enqueue_message(message)
                logger.debug(f"Queued message: {message.get('op', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
    
    async def process_message(self, message: dict) -> None:
        """Process message from queue and store in database"""
        try:
            message_type = message.get("op", "unknown")
            
            if message_type == "utx":
                # Handle unconfirmed transaction
                transaction_data = message.get("x", {})
                if self.database:
                    await self.database.store_transaction(transaction_data)
                    logger.info(f"Stored unconfirmed transaction: {transaction_data.get('hash', 'unknown')}")
                    
            elif message_type == "block":
                # Handle new block
                block_data = message.get("x", {})
                if self.database:
                    await self.database.store_block(block_data)
                    logger.info(f"Stored new block: {block_data.get('hash', 'unknown')}")
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def start(self) -> None:
        """Start the data pipeline"""
        logger.info("Starting Blockchain ML Data Pipeline")
        
        # Start Prometheus metrics server
        await self.start_prometheus_server()
        
        try:
            # Initialize Redis message queue
            logger.info("Connecting to Redis...")
            self.message_queue = RedisMessageQueue(self.redis_url)
            await self.message_queue.connect()
            
            # Initialize PostgreSQL database
            logger.info("Connecting to PostgreSQL...")
            self.database = DatabaseHandler(self.database_url)
            await self.database.connect()
            
            # Initialize message processor
            self.message_processor = MessageProcessor(
                self.message_queue, 
                self.process_message
            )
            
            # Initialize WebSocket client
            self.websocket_client = BlockchainWebSocketClient(
                message_handler=self.message_handler
            )
            
            self.running = True
            
            # Start message processor in background
            processor_task = asyncio.create_task(
                self.message_processor.start_processing()
            )
            
            # Run the WebSocket client
            await self.websocket_client.run()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in data pipeline: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the data pipeline"""
        logger.info("Stopping Blockchain ML Data Pipeline")
        self.running = False
        
        # Stop message processor
        if self.message_processor:
            await self.message_processor.stop_processing()
        
        # Disconnect WebSocket client
        if self.websocket_client:
            await self.websocket_client.disconnect()
        
        # Disconnect database
        if self.database:
            await self.database.disconnect()
        
        # Disconnect message queue
        if self.message_queue:
            await self.message_queue.disconnect()
        
        logger.info("Data pipeline stopped")


async def main():
    """Main function"""
    # Create data pipeline
    pipeline = DataPipeline()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(pipeline.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the pipeline
        await pipeline.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 