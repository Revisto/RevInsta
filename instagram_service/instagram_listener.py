from time import sleep
from random import randint

from config.config import Config
from instagram_service.instagram_handler_service import InstagramService
from logger.log import Logger

logger = Logger("InstagramListener")
instagram_listener = InstagramService(Config)

logger.log_info("Service started")

while True:
    message = instagram_listener.listen()
    sleep_time = randint(60, 180)
    logger.log_info(f"Sleeping for {sleep_time} seconds")
    sleep(sleep_time)