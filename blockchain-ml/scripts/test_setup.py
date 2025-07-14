#!/usr/bin/env python3
"""
Test script to verify the project setup

This script tests the basic functionality of the data pipeline
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_pipeline.websocket_client import BlockchainWebSocketClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket_client():
    """Test the WebSocket client functionality"""
    logger.info("Testing WebSocket client...")
    
    client = BlockchainWebSocketClient()
    
    # Test basic functionality
    assert client.url == "wss://ws.blockchain.info/inv"
    assert client.is_connected is False
    
    logger.info("✅ WebSocket client initialization test passed")
    
    # Test message processing
    test_message = '{"op": "utx", "x": {"hash": "test_hash"}}'
    await client.process_message(test_message)
    
    logger.info("✅ Message processing test passed")
    
    logger.info("All WebSocket client tests passed!")


async def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import websockets
        import prometheus_client
        import asyncio
        import json
        import logging
        
        # Test traditional ML imports
        import pandas as pd
        import numpy as np
        import sklearn
        import xgboost
        import lightgbm
        
        logger.info("✅ All required imports successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False


async def main():
    """Main test function"""
    logger.info("🚀 Starting Blockchain ML setup test...")
    
    # Test imports
    if not await test_imports():
        logger.error("❌ Import test failed")
        return False
    
    # Test WebSocket client
    try:
        await test_websocket_client()
    except Exception as e:
        logger.error(f"❌ WebSocket client test failed: {e}")
        return False
    
    logger.info("🎉 All tests passed! Your setup is ready.")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 