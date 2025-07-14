"""
PostgreSQL Database Handler

Handles database operations for storing blockchain data
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
database_operations = Counter(
    "blockchain_database_operations_total",
    "Total number of database operations",
    ["operation", "table"]
)

database_operation_time = Histogram(
    "blockchain_database_operation_seconds",
    "Time spent on database operations",
    ["operation"]
)


class DatabaseHandler:
    """PostgreSQL database handler for blockchain data"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self.is_connected = False
        
    async def connect(self) -> None:
        """Connect to PostgreSQL database"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            self.is_connected = True
            logger.info("Connected to PostgreSQL database")
            
            # Create tables if they don't exist
            await self.create_tables()
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from database"""
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("Disconnected from PostgreSQL database")
    
    async def create_tables(self) -> None:
        """Create database tables if they don't exist"""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            # Create transactions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    tx_hash VARCHAR(64) UNIQUE NOT NULL,
                    block_height INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    total_value BIGINT,
                    fee BIGINT,
                    input_count INTEGER,
                    output_count INTEGER,
                    is_confirmed BOOLEAN DEFAULT FALSE,
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create blocks table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    id SERIAL PRIMARY KEY,
                    block_hash VARCHAR(64) UNIQUE NOT NULL,
                    height INTEGER UNIQUE NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    size INTEGER,
                    tx_count INTEGER,
                    total_btc_sent BIGINT,
                    reward BIGINT,
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create transaction inputs/outputs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transaction_io (
                    id SERIAL PRIMARY KEY,
                    tx_hash VARCHAR(64) REFERENCES transactions(tx_hash),
                    address VARCHAR(255),
                    value BIGINT,
                    is_input BOOLEAN,
                    script_type VARCHAR(50),
                    script_hex TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_timestamp 
                ON transactions(timestamp)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_hash 
                ON transactions(tx_hash)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_value 
                ON transactions(total_value)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_blocks_height 
                ON blocks(height)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_blocks_timestamp 
                ON blocks(timestamp)
            """)
            
            logger.info("Database tables created/verified")
    
    async def store_transaction(self, transaction_data: Dict[str, Any]) -> None:
        """Store transaction data in database"""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.pool.acquire() as conn:
                # Extract transaction data
                tx_hash = transaction_data.get("hash")
                block_height = transaction_data.get("block_index")
                timestamp = datetime.fromtimestamp(transaction_data.get("time", 0))
                total_value = sum(out.get("value", 0) for out in transaction_data.get("out", []))
                fee = transaction_data.get("fee", 0)
                input_count = len(transaction_data.get("inputs", []))
                output_count = len(transaction_data.get("out", []))
                is_confirmed = block_height is not None
                
                # Insert transaction
                await conn.execute("""
                    INSERT INTO transactions 
                    (tx_hash, block_height, timestamp, total_value, fee, 
                     input_count, output_count, is_confirmed, raw_data)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (tx_hash) DO UPDATE SET
                    block_height = EXCLUDED.block_height,
                    is_confirmed = EXCLUDED.is_confirmed,
                    raw_data = EXCLUDED.raw_data
                """, tx_hash, block_height, timestamp, total_value, fee,
                     input_count, output_count, is_confirmed, json.dumps(transaction_data))
                
                # Store transaction inputs
                for input_data in transaction_data.get("inputs", []):
                    prev_out = input_data.get("prev_out", {})
                    address = prev_out.get("addr")
                    value = prev_out.get("value", 0)
                    script = prev_out.get("script", "")
                    
                    if address:
                        await conn.execute("""
                            INSERT INTO transaction_io 
                            (tx_hash, address, value, is_input, script_hex)
                            VALUES ($1, $2, $3, $4, $5)
                        """, tx_hash, address, value, True, script)
                
                # Store transaction outputs
                for output_data in transaction_data.get("out", []):
                    address = output_data.get("addr")
                    value = output_data.get("value", 0)
                    script = output_data.get("script", "")
                    
                    if address:
                        await conn.execute("""
                            INSERT INTO transaction_io 
                            (tx_hash, address, value, is_input, script_hex)
                            VALUES ($1, $2, $3, $4, $5)
                        """, tx_hash, address, value, False, script)
                
                # Update metrics
                database_operations.labels(operation="insert", table="transactions").inc()
                
                logger.debug(f"Stored transaction: {tx_hash}")
                
        except Exception as e:
            logger.error(f"Failed to store transaction: {e}")
            raise
        finally:
            # Record operation time
            operation_time = asyncio.get_event_loop().time() - start_time
            database_operation_time.labels(operation="store_transaction").observe(operation_time)
    
    async def store_block(self, block_data: Dict[str, Any]) -> None:
        """Store block data in database"""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.pool.acquire() as conn:
                # Extract block data
                block_hash = block_data.get("hash")
                height = block_data.get("height")
                timestamp = datetime.fromtimestamp(block_data.get("time", 0))
                size = block_data.get("size", 0)
                tx_count = len(block_data.get("txIndexes", []))
                total_btc_sent = block_data.get("totalBTCSent", 0)
                reward = block_data.get("reward", 0)
                
                # Insert block
                await conn.execute("""
                    INSERT INTO blocks 
                    (block_hash, height, timestamp, size, tx_count, 
                     total_btc_sent, reward, raw_data)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (block_hash) DO UPDATE SET
                    raw_data = EXCLUDED.raw_data
                """, block_hash, height, timestamp, size, tx_count,
                     total_btc_sent, reward, json.dumps(block_data))
                
                # Update metrics
                database_operations.labels(operation="insert", table="blocks").inc()
                
                logger.debug(f"Stored block: {block_hash} (height: {height})")
                
        except Exception as e:
            logger.error(f"Failed to store block: {e}")
            raise
        finally:
            # Record operation time
            operation_time = asyncio.get_event_loop().time() - start_time
            database_operation_time.labels(operation="store_block").observe(operation_time)
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction by hash"""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM transactions WHERE tx_hash = $1
                """, tx_hash)
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get transaction: {e}")
            raise
    
    async def get_recent_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent transactions"""
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM transactions 
                    ORDER BY timestamp DESC 
                    LIMIT $1
                """, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get recent transactions: {e}")
            raise
    
    async def get_transaction_count(self) -> int:
        """Get total number of transactions"""
        if not self.is_connected:
            return 0
        
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM transactions")
                return count
        except Exception as e:
            logger.error(f"Failed to get transaction count: {e}")
            return 0
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.is_connected:
            return {"connected": False}
        
        try:
            async with self.pool.acquire() as conn:
                tx_count = await conn.fetchval("SELECT COUNT(*) FROM transactions")
                block_count = await conn.fetchval("SELECT COUNT(*) FROM blocks")
                io_count = await conn.fetchval("SELECT COUNT(*) FROM transaction_io")
                
                return {
                    "connected": True,
                    "transaction_count": tx_count,
                    "block_count": block_count,
                    "io_count": io_count,
                    "database_url": self.database_url
                }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"connected": False, "error": str(e)}
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect() 