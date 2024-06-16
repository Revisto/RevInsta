import json
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from redis import Redis
from functools import wraps
import os

from message_broker.rabbitmq_service import RabbitMQService
from logger.log import Logger
from utils.singleton import Singleton

def handle_login_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        for i in range(2):
            try:
                return func(self, *args, **kwargs)
            except LoginRequired:
                self.logger.log_info("Session is invalid, need to login via username and password")
                self.login()
        self.logger.log_error("Couldn't login user with either password or session")
        raise Exception("Couldn't login user with either password or session")

    return wrapper

class ReplyToMessage:
    def __init__(self, message_id, client_context):
        self.id = message_id
        self.client_context = client_context

class InstagramService(metaclass=Singleton):

    def __init__(self, config):
        self.config = config
        self.logger = Logger("InstagramService")
        self.client = Client()
        self.client.delay_range = [1, 3]
        self.session_path = "config/session.json"
        self.login()
        #self.user_id = self.client.user_id_from_username(config.INSTAGRAM_TARGET_USERNAME)
        #self.thread_id = self.client.direct_thread_by_participants([self.user_id])["thread"]["thread_id"]
        self.thread_id = "340282366841710301244259189720640459822"
        self.redis_client = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD, db=0)
        self.logger.log_info("Service started")

    def login(self):
        if os.path.exists(self.session_path):
            self.session = self.client.load_settings(self.session_path)
        else:
            self.session = None
            
        login_via_session = False
        login_via_pw = False

        if self.session:
            try:
                self.client.set_settings(self.session)
                self.client.login(self.config.INSTAGRAM_USERNAME, self.config.INSTAGRAM_PASSWORD)

                # check if session is valid
                try:
                    self.client.get_timeline_feed()
                except LoginRequired:
                    self.logger.log_info("Session is invalid, need to login via username and password")

                    old_session = self.client.get_settings()

                    # use the same device uuids across logins
                    self.client.set_settings({})
                    self.client.set_uuids(old_session["uuids"])

                    self.client.login(self.config.INSTAGRAM_USERNAME, self.config.INSTAGRAM_PASSWORD)
                login_via_session = True
            except Exception as e:
                self.logger.log_info("Couldn't login user using session information: %s" % e)

        if not login_via_session:
            try:
                self.logger.log_info("Attempting to login via username and password. username: %s" % self.config.INSTAGRAM_USERNAME)
                if self.client.login(self.config.INSTAGRAM_USERNAME, self.config.INSTAGRAM_PASSWORD):
                    login_via_pw = True
            except Exception as e:
                self.logger.log_info("Couldn't login user using username and password: %s" % e)

        if not login_via_pw and not login_via_session:
            self.logger.log_error("Couldn't login user with either password or session")
            raise Exception("Couldn't login user with either password or session")

        self.client.dump_settings(self.session_path)
        self.logger.log_info("Logged in successfully")


    @handle_login_required
    def listen(self):
        is_rabbitmq_connected = False
        self.logger.log_info("Listening for messages")
        messages = self.client.direct_messages(self.thread_id, amount=10)
        messages.reverse()
        for message in messages:
            if int(message.user_id) == int(self.client.user_id):
                continue
            if self.redis_client.get(message.id) is not None:
                continue
            if not is_rabbitmq_connected:
                rabbitmq_service = RabbitMQService(self.config)
                self.logger.log_info("Connected to RabbitMQ to send messages to Telegram")
                is_rabbitmq_connected = True

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

            rabbitmq_service.send_message_instagram_to_telegram(json.dumps(clean_message))
            self.logger.log_info(f"Sent message: {clean_message}")

        if is_rabbitmq_connected:
            rabbitmq_service.close_connection()
            self.logger.log_info("Disconnected from RabbitMQ")

    @handle_login_required
    def reply_in_direct(self, text, reply_to_message):
        self.client.direct_send(text, thread_ids=[self.thread_id], reply_to_message=reply_to_message)
        self.logger.log_info(f"Replied to message: {text}")