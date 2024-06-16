from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from redis import Redis
import json

from message_broker.rabbitmq_service import RabbitMQService
from config.config import Config
from logger.log import Logger

logger = Logger("TelegramListener")
redis_telegram_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, password=Config.REDIS_PASSWORD, db=1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!"
    )
    logger.log_info(f"Start command issued by {user.mention_html()}")

async def listen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rabbitmq_service = RabbitMQService(Config)
    rabbitmq_service.send_message_telegram_to_instagram(json.dumps({"action": "listen"}))
    rabbitmq_service.close_connection()
    await update.message.set_reaction("👍")
    logger.log_info(f"Listen command issued by {update.effective_user.mention_html()}")


async def send_direct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message is not None:
        replied_message_id = update.message.reply_to_message.message_id
        instagram_data = redis_telegram_client.get(replied_message_id)
        if instagram_data is not None:
            instagram_data = json.loads(instagram_data)
            instagram_data["text"] = update.message.text
            instagram_data["action"] = "reply"
            rabbitmq_service = RabbitMQService(Config)
            rabbitmq_service.send_message_telegram_to_instagram(json.dumps(instagram_data))
            rabbitmq_service.close_connection()
            await update.message.set_reaction("👍")
            logger.log_info(f"Message sent: {update.message.text}")
            return
    
    await update.message.set_reaction("👎")
    logger.log_info("Message not sent")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("listen", listen))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT, send_direct))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.log_info("Service started")

if __name__ == "__main__":
    main()