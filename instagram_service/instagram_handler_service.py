import json
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from redis import Redis

from message_broker.rabbitmq_service import RabbitMQService
from logger.log import Logger

class ReplyToMessage:
    def __init__(self, message_id, client_context):
        self.id = message_id
        self.client_context = client_context

class InstagramService:
    def __init__(self, config):
        self.logger = Logger("InstagramService")
        self.client = Client()
        self.client.delay_range = [1, 3]
        self.client.load_settings("config/session.json")
        self.client.login(config.INSTAGRAM_USERNAME, config.INSTAGRAM_PASSWORD)
        try:
            self.client.account_info()
        except LoginRequired:
            self.client.relogin() # Use clean session
        self.client.dump_settings("config/session.json")
        self.thread_id = "340282366841710301244259189720640459822"
        self.redis_client = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD, db=0)
        self.rabbitmq_service = RabbitMQService(config)
        self.logger.log_info("Service started")

    def listen(self):
        self.logger.log_info("Listening for messages")
        messages = self.client.direct_messages(self.thread_id, amount=10)
        for message in messages:
            if int(message.user_id) == int(self.client.user_id):
                continue
            if self.redis_client.get(message.id) is not None:
                continue
            if message.text is not None:
                text = message.text
                clean_message = {
                    "id": message.id,
                    "client_context": message.client_context,
                    'type': 'text',
                    'text': text
                }
            elif message.clip is not None:
                download_link = str(message.clip.video_url)
                caption = message.clip.caption_text
                link = "https://www.instagram.com/p/" + message.clip.code
                clean_message = {
                    "id": message.id,
                    "client_context": message.client_context,
                    'type': 'reel',
                    'download_link': download_link,
                    'caption': caption,
                    'link': link
                }
            elif message.xma_share is not None:
                download_link = str(message.xma_share.preview_url)
                caption = message.xma_share.title
                link = str(message.xma_share.video_url)
                clean_message = {
                    "id": message.id,
                    "client_context": message.client_context,
                    'type': 'post',
                    'download_link': download_link,
                    'caption': caption,
                    'link': link
                }
            else:
                clean_message = {
                    'type': 'unknown'
                }
            self.rabbitmq_service.send_message_instagram_to_telegram(json.dumps(clean_message))
            self.logger.log_info(f"Sent message: {clean_message}")

    def reply_in_direct(self, text, reply_to_message):
        self.client.direct_send(text, thread_ids=[self.thread_id], reply_to_message=reply_to_message)
        self.logger.log_info(f"Replied to message: {text}")