from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from redis import Redis
import json

from message_broker.rabbitmq_service import RabbitMQService
from config.config import Config

redis_telegram_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, password=Config.REDIS_PASSWORD, db=1)
rabbitmq_service = RabbitMQService(Config)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!"
    )

async def send_direct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message is not None:
        replied_message_id = update.message.reply_to_message.message_id
        instagram_data = redis_telegram_client.get(replied_message_id)
        if instagram_data is not None:
            instagram_data = json.loads(instagram_data)
            instagram_data["text"] = update.message.text
            rabbitmq_service.send_message_telegram_to_instagram(json.dumps(instagram_data))
            await update.message.set_reaction("👍")
            return
    
    await update.message.set_reaction("👎")
    


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT, send_direct))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()