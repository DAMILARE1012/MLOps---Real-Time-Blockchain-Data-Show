"""
Unit tests for WebSocket client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.data_pipeline.websocket_client import BlockchainWebSocketClient


class TestBlockchainWebSocketClient:
    """Test cases for BlockchainWebSocketClient"""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance"""
        return BlockchainWebSocketClient()
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initialization"""
        assert client.url == "wss://ws.blockchain.info/inv"
        assert client.is_connected is False
        assert client.reconnect_attempts == 0
    
    @pytest.mark.asyncio
    async def test_send_ping(self, client):
        """Test sending ping message"""
        with patch.object(client, 'send_message') as mock_send:
            await client.send_ping()
            mock_send.assert_called_once_with({"op": "ping"})
    
    @pytest.mark.asyncio
    async def test_subscribe_unconfirmed_transactions(self, client):
        """Test subscribing to unconfirmed transactions"""
        with patch.object(client, 'send_message') as mock_send:
            await client.subscribe_unconfirmed_transactions()
            mock_send.assert_called_once_with({"op": "unconfirmed_sub"})
    
    @pytest.mark.asyncio
    async def test_subscribe_address(self, client):
        """Test subscribing to specific address"""
        test_address = "1A828tTnkVFJfSvLCqF42ohZ51ksS3jJgX"
        with patch.object(client, 'send_message') as mock_send:
            await client.subscribe_address(test_address)
            mock_send.assert_called_once_with({
                "op": "addr_sub",
                "addr": test_address
            })
    
    @pytest.mark.asyncio
    async def test_subscribe_blocks(self, client):
        """Test subscribing to new blocks"""
        with patch.object(client, 'send_message') as mock_send:
            await client.subscribe_blocks()
            mock_send.assert_called_once_with({"op": "blocks_sub"})
    
    @pytest.mark.asyncio
    async def test_process_message_utx(self, client):
        """Test processing unconfirmed transaction message"""
        message = '{"op": "utx", "x": {"hash": "test_hash"}}'
        
        with patch.object(client, 'handle_unconfirmed_transaction') as mock_handler:
            await client.process_message(message)
            mock_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_block(self, client):
        """Test processing new block message"""
        message = '{"op": "block", "x": {"hash": "test_hash", "height": 123}}'
        
        with patch.object(client, 'handle_new_block') as mock_handler:
            await client.process_message(message)
            mock_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_invalid_json(self, client):
        """Test processing invalid JSON message"""
        message = 'invalid json'
        
        # Should not raise an exception
        await client.process_message(message)
    
    @pytest.mark.asyncio
    async def test_handle_unconfirmed_transaction(self, client):
        """Test handling unconfirmed transaction"""
        data = {
            "x": {
                "hash": "test_hash",
                "inputs": [],
                "out": []
            }
        }
        
        # Should not raise an exception
        await client.handle_unconfirmed_transaction(data)
    
    @pytest.mark.asyncio
    async def test_handle_new_block(self, client):
        """Test handling new block"""
        data = {
            "x": {
                "hash": "test_hash",
                "height": 123,
                "txIndexes": []
            }
        }
        
        # Should not raise an exception
        await client.handle_new_block(data)
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager"""
        with patch.object(client, 'connect') as mock_connect:
            with patch.object(client, 'disconnect') as mock_disconnect:
                async with client:
                    mock_connect.assert_called_once()
                
                mock_disconnect.assert_called_once() 