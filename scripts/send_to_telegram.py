import os
import time
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, TimedOut, NetworkError
import asyncio

# Load environment variables from .env
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(ENV_PATH)

# Telegram Bot Token, Channel, and Chat ID from .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
TELEGRAM_RES_TOPIC = os.getenv("TELEGRAM_RES_TOPIC")  # ID Residential Proxies Topic
TELEGRAM_CHECKED_TOPIC = os.getenv("TELEGRAM_CHECKED_TOPIC")  # ID Checked Proxies Topic

# File paths for storing proxies from .env
BASE_PATH = os.getenv("BASE_PATH", os.path.join(PROJECT_ROOT, "data"))
RESIDENTIAL_PROXIES_FILE = os.getenv("RESIDENTIAL_PROXIES_FILE", os.path.join(BASE_PATH, "output/residential_proxies.txt"))
CHECKED_PROXIES_FILE = os.getenv("CHECKED_PROXIES_FILE", os.path.join(BASE_PATH, "output/checked_proxies.txt"))

# Initialize Telegram Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_telegram_message(message, chat_id, parse_mode=ParseMode.MARKDOWN, message_thread_id=None, retries=3):
    """
    Sends a message to a specified Telegram chat (channel or bot), with retry logic.
    """
    attempt = 0
    while attempt < retries:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode,
                message_thread_id=message_thread_id
            )
            print("Message sent successfully.")
            break
        except (TelegramError, TimedOut, NetworkError) as e:
            print(f"Error sending message (attempt {attempt + 1}/{retries}): {e}")
            attempt += 1
            if attempt >= retries:
                print(f"Failed to send message after {retries} attempts.")
                break
            await asyncio.sleep(2)  # Wait before retrying

def load_proxies_from_file(file_path):
    """
    Loads proxies from a given file path, ensuring file is accessible.
    """
    try:
        with open(file_path, "r") as file:
            proxies = [line.strip() for line in file if line.strip()]
            return proxies
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except Exception as e:
        print(f"An error occurred while loading proxies: {e}")
    return []

async def send_proxy_list_to_telegram(proxy_list, message_prefix, topic_id=None):
    """
    This function formats the proxy list and sends it to Telegram using Markdown for styling.
    """
    if proxy_list:
        # Format the proxy list into the desired format: protocol://ip:port
        formatted_proxies = [f"{proxy}" for proxy in proxy_list]
        
        # Make the message more readable by adding headers and some styling
        message = f"*{message_prefix}*\n\n"
        message += "\n".join(formatted_proxies)

        # Ensure the message doesn't exceed Telegram's 4096 character limit
        max_message_length = 4096
        chunks = [message[i:i + max_message_length] for i in range(0, len(message), max_message_length)]
        
        # Send each chunk
        for chunk in chunks:
            if topic_id:
                await send_telegram_message(chunk, TELEGRAM_CHANNEL, message_thread_id=topic_id)
            else:
                await send_telegram_message(chunk, TELEGRAM_CHANNEL)
    else:
        print(f"No proxies to send for {message_prefix}")

async def main():
    # Load proxies from Residential file
    residential_proxies = load_proxies_from_file(RESIDENTIAL_PROXIES_FILE)

    # Load proxies from Checked Proxies file
    checked_proxies = load_proxies_from_file(CHECKED_PROXIES_FILE)

    # Send residential proxies to their respective topic in channel
    if TELEGRAM_RES_TOPIC:
        await send_proxy_list_to_telegram(residential_proxies, "Residential Proxies", topic_id=int(TELEGRAM_RES_TOPIC))
    else:
        await send_proxy_list_to_telegram(residential_proxies, "Residential Proxies")

    # Send checked proxies to their respective topic in channel
    if TELEGRAM_CHECKED_TOPIC:
        await send_proxy_list_to_telegram(checked_proxies, "Checked Proxies", topic_id=int(TELEGRAM_CHECKED_TOPIC))
    else:
        await send_proxy_list_to_telegram(checked_proxies, "Checked Proxies")

if __name__ == "__main__":
    asyncio.run(main())