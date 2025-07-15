from telegram import Bot
import os
import logging
import asyncio
import platform
import warnings

# Suppress all asyncio cleanup warnings on Windows
if platform.system() == 'Windows':
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
    warnings.filterwarnings("ignore", message=".*_ProactorBasePipeTransport.*")
    warnings.filterwarnings("ignore", message=".*Event loop is closed.*")

# Suppress httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix for Windows asyncio issue
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram_alert_async(message: str):
    """
    Send a Telegram alert message (async version).
    
    Args:
        message (str): The message to send
        
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    # Validate environment variables
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        return False
    
    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID not set in environment variables")
        return False
    
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f"Telegram alert sent successfully: {message[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False

def send_telegram_alert(message: str):
    """
    Send a Telegram alert message (sync wrapper).
    
    Args:
        message (str): The message to send
        
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    try:
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in an async context
            logger.warning("Called sync function from async context. Use send_telegram_alert_async instead.")
            return False
        except RuntimeError:
            # No running loop, we can create one
            pass
        
        # Use asyncio.run for proper cleanup
        return asyncio.run(send_telegram_alert_async(message))
        
    except Exception as e:
        logger.error(f"Error in sync telegram alert: {e}")
        return False

async def send_telegram_alert_batch(messages: list):
    """
    Send multiple Telegram alerts efficiently.
    
    Args:
        messages (list): List of messages to send
        
    Returns:
        list: List of success/failure booleans
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not set")
        return [False] * len(messages)
    
    bot = None
    results = []
    
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        for message in messages:
            try:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                logger.info(f"Batch message sent: {message[:30]}...")
                results.append(True)
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Failed to send batch message: {e}")
                results.append(False)
                
    except Exception as e:
        logger.error(f"Failed to initialize bot for batch sending: {e}")
        results = [False] * len(messages)
    finally:
        if bot:
            try:
                await bot.close()
            except Exception:
                pass  # Ignore cleanup errors
    
    return results

def test_telegram_bot():
    """Test the Telegram bot functionality."""
    print("🤖 Testing Telegram Bot...")
    print("=" * 50)
    
    # Check if environment variables are set
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("❌ TELEGRAM_BOT_TOKEN not set properly")
        print("💡 Please set your actual bot token in environment variables")
        return False
    
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "your_telegram_chat_id_here":
        print("❌ TELEGRAM_CHAT_ID not set properly")
        print("💡 Please set your actual chat ID in environment variables")
        return False
    
    print(f"✅ Bot Token: {'*' * len(TELEGRAM_BOT_TOKEN)}")
    print(f"✅ Chat ID: {TELEGRAM_CHAT_ID}")
    
    # Test sending a message
    test_message = "🚀 Blockchain ML System Test Alert!\n\nThis is a test message from your anomaly detection system."
    
    print(f"\n📤 Sending test message...")
    success = send_telegram_alert(test_message)
    
    if success:
        print("✅ Test message sent successfully!")
        print("📱 Check your Telegram chat for the message")
    else:
        print("❌ Failed to send test message")
        print("💡 Check your bot token and chat ID")
    
    return success

async def test_telegram_bot_async():
    """Async version of the test function."""
    print("🤖 Testing Telegram Bot (Async)...")
    print("=" * 50)
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram credentials not set")
        return False
    
    print(f"✅ Bot Token: {'*' * len(TELEGRAM_BOT_TOKEN)}")
    print(f"✅ Chat ID: {TELEGRAM_CHAT_ID}")
    
    test_message = "🚀 Blockchain ML System Async Test!\n\nThis is an async test message."
    
    print(f"\n📤 Sending test message (async)...")
    success = await send_telegram_alert_async(test_message)
    
    if success:
        print("✅ Async test message sent successfully!")
        print("📱 Check your Telegram chat for the message")
    else:
        print("❌ Failed to send async test message")
    
    return success

if __name__ == "__main__":
    test_telegram_bot()