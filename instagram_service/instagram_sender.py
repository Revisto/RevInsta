
import json

from config.config import Config
from message_broker.rabbitmq_service import RabbitMQService
from instagram_service.instagram_handler_service import InstagramService, ReplyToMessage

instagram_listener = InstagramService(Config)

def callback(ch, method, properties, body):
    message = json.loads(body)
    reply_to_message = ReplyToMessage(message["id"], message["client_context"])
    instagram_listener.reply_in_direct(message["text"], reply_to_message)

rabbitmq_service = RabbitMQService(Config)
rabbitmq_service.start_consuming({'telegram_to_instagram': callback})