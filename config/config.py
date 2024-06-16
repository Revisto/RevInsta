import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
    INSTAGRAM_TARGET_USERNAME = os.getenv('INSTAGRAM_TARGET_USERNAME')
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = int(os.getenv('REDIS_PORT'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
    RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    TELEGRAM_LOG_CHAT_ID = os.getenv('TELEGRAM_LOG_CHAT_ID')