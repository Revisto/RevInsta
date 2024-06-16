from redis import Redis
import json
import requests
import io
from time import sleep

from message_broker.rabbitmq_service import RabbitMQService
from config.config import Config
from logger.log import Logger

# Create an instance of Logger
logger = Logger("TelegramSender")

redis_instagram_client = Redis(
    host=Config.REDIS_HOST, port=Config.REDIS_PORT, password=Config.REDIS_PASSWORD, db=0
)
redis_telegram_client = Redis(
    host=Config.REDIS_HOST, port=Config.REDIS_PORT, password=Config.REDIS_PASSWORD, db=1
)


class TelegramSender:
    def __init__(self, config):
        self.TELEGRAM_BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
        self.CHAT_ID = config.TELEGRAM_CHAT_ID

    def send_text_message(self, text, chat_id=None):
        if chat_id is None:
            chat_id = self.CHAT_ID

        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        req = requests.post(url, data=data)
        if req.status_code == 200:
            message_id = json.loads(req.text)["result"]["message_id"]
            return message_id
        else:
            if "retry after" in json.loads(req.text)["description"]:
                sleep(30)
            else:
                logger.log_critical(f"Failed to send text message: {json.loads(req.text)['description']}")
            return None

    def send_video_message(self, video_url, caption):
        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendVideo"
        data = {"parse_mode": "HTML", "chat_id": self.CHAT_ID, "caption": caption}
        video = requests.get(video_url)
        video_stream = io.BytesIO(video.content)
        video_stream.name = "video.mp4"
        files = {"video": video_stream}
        req = requests.post(url, data=data, files=files)
        response = json.loads(req.text)
        if req.status_code == 200:
            message_id = response["result"]["message_id"]
            return message_id
        else:
            logger.log_critical(f"Failed to send video message: {response['description']}")
            return None

    def send_photo_message(self, photo_url, caption):
        url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendPhoto"
        data = {"parse_mode": "HTML", "chat_id": self.CHAT_ID, "caption": caption}
        photo = requests.get(photo_url)
        photo_stream = io.BytesIO(photo.content)
        photo_stream.name = "photo.jpg"
        files = {"photo": photo_stream}
        req = requests.post(url, data=data, files=files)
        response = json.loads(req.text)
        if req.status_code == 200:
            message_id = response["result"]["message_id"]
            return message_id
        else:
            logger.log_critical(f"Failed to send photo message: {response['description']}")
            return None


telegram_sender = TelegramSender(Config)


def instagram_to_telegram_callback(ch, method, properties, body):
    message = json.loads(body)
    message_id = None
    if message.get("id") is not None:
        redis_instagram_client.set(message["id"], 1)
        logger.log_info(f"Message ID: {message['id']} saved to Redis")

    if message.get("type") == "text":
        message_id = telegram_sender.send_text_message(message["text"])
        logger.log_info(f"Text message sent with ID: {message_id}")

    if message.get("type") == "reel":
        caption = f'{message["caption"]}\n\n<a href="{message["link"]}">Link</a>'
        message_id = telegram_sender.send_video_message(
            message["download_link"], caption
        )
        logger.log_info(f"Reel message sent with ID: {message_id}")

    if message.get("type") == "post":
        caption = f'{message["caption"]}\n\n<a href="{message["link"]}">Link</a>'
        message_id = telegram_sender.send_photo_message(
            message["download_link"], caption
        )
        logger.log_info(f"Post message sent with ID: {message_id}")

    if message.get("type") == "unknown":
        telegram_sender.send_text_message("Unknown message type")
        logger.log_info("Unknown message type sent to Telegram")

    if message_id is not None:
        redis_telegram_client.set(
            message_id,
            json.dumps(
                {"id": message["id"], "client_context": message["client_context"]}
            ),
        )
        logger.log_info(f"Message ID: {message_id} saved to Redis")


def log_in_telegram_callback(ch, method, properties, body):
    message = body.decode("utf-8")
    telegram_sender.send_text_message(message, Config.TELEGRAM_LOG_CHAT_ID)


rabbitmq_service = RabbitMQService(Config)
rabbitmq_service.start_consuming(
    {
        "instagram_to_telegram": instagram_to_telegram_callback,
        "logs": log_in_telegram_callback,
    }
)
logger.log_info("Service started")
