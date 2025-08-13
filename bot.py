import os
import logging
import openai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ВАЖНО: для полной функциональности надо добавить свои функции (распознавание речи, озвучка, карточки, экспорт в Notion и т.п.)
# Здесь базовый пример для старта общения и исправления ошибок

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

openai.api_key = OPENAI_API_KEY

CHOOSING, TYPING_REPLY = range(2)

topics = ['Cafe', 'Hospital', 'Airport', 'Small Talk']

def get_gpt_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful English tutor assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [topics]
    await update.message.reply_text(
        "Hi! Choose a topic to practice your English:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSING

async def choose_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text
    if user_choice not in topics:
        await update.message.reply_text("Please choose a topic from the keyboard.")
        return CHOOSING
    context.user_data['topic'] = user_choice
    await update.message.reply_text(
        f"Great! Let's talk about {user_choice}. Send me a message or voice note in English.",
        reply_markup=ReplyKeyboardRemove()
    )
    return TYPING_REPLY

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    topic = context.user_data.get('topic', 'General')
    prompt = f"Correct and respond conversationally to this message about {topic}: {user_text}"
    response = get_gpt_response(prompt)
    await update.message.reply_text(response)
    return TYPING_REPLY

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bye! You can start again with /start.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_topic)],
            TYPING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
