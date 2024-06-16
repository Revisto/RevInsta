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
    sleep_time = randint(0.7 * 60 * 60, 1 * 60 * 60)
    logger.log_info(f"Sleeping for {sleep_time} seconds")
    sleep(sleep_time)