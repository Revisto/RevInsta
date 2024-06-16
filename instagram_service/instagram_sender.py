import json

from config.config import Config
from message_broker.rabbitmq_service import RabbitMQService
from instagram_service.instagram_handler_service import InstagramService, ReplyToMessage
from logger.log import Logger

logger = Logger("InstagramSender")

def callback(ch, method, properties, body):
    logger.log_info("Received a message")
    message = json.loads(body)
    if message.get("action") == "reply":
        reply_to_message = ReplyToMessage(message["id"], message["client_context"])
        InstagramService(Config).reply_in_direct(message["text"], reply_to_message)
        logger.log_info(f"Replied to message: {message['text']}")
    if message.get("action") == "listen":
        logger.log_info("Listening to messages on command")
        InstagramService(Config).listen()

rabbitmq_service = RabbitMQService(Config)
logger.log_info("Service started")
rabbitmq_service.start_consuming({'telegram_to_instagram': callback})