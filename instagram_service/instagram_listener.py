
from time import sleep
from random import randint

from config.config import Config
from instagram_service.instagram_handler_service import InstagramService

instagram_listener = InstagramService(Config)

while True:
    message = instagram_listener.listen()
    sleep(randint(45, 180))