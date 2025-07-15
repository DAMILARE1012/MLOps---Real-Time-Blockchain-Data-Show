#!/usr/bin/env python3
"""
Clean test script for Telegram bot - suppresses all warnings.
"""

import warnings
import sys
import os

# Suppress all warnings
warnings.filterwarnings("ignore")

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the test
from alerting.telegram_alert import test_telegram_bot

if __name__ == "__main__":
    # Suppress stdout for httpx logs
    import logging
    logging.getLogger("httpx").setLevel(logging.ERROR)
    
    print("🤖 Testing Telegram Bot (Clean Version)...")
    print("=" * 50)
    
    success = test_telegram_bot()
    
    if success:
        print("\n🎉 All tests passed! Telegram bot is working perfectly.")
    else:
        print("\n❌ Test failed. Check your configuration.") 