from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import requests
import re
import bot_states, bot_messages
import telegram
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

custom_keyboard = [['/client'], ['/courier']]
client_keyboard = [['/menu'], ['/makeorder'], ['/back']]
courier_keyboard = [['/back']]
order_keyboard = [['/cancel_order']]

standart_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
order_reply_markup = telegram.ReplyKeyboardMarkup(order_keyboard, resize_keyboard=True)
client_markup = telegram.ReplyKeyboardMarkup(client_keyboard, resize_keyboard=True)
courier_markup = telegram.ReplyKeyboardMarkup(courier_keyboard, resize_keyboard=True)

def get_url():
    contents = requests.get('https://random.dog/woof.json').json()
    url = contents['url']
    return url


def start(update, context):
    update.message.reply_text(bot_messages.start_command_response, reply_markup=standart_markup)


def menu(update, context):
    url = get_url()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)


def make_order(update, context):
    if not context.args:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.add_new_order, reply_markup=order_reply_markup)
        return bot_states.READ_NEW_ORDER
    order_text = "Вы заказали: " + ' '.join(context.args)
    user_id = update.message.from_user.id
    context.bot.send_message(chat_id=update.message.chat_id, text=order_text, reply_markup=client_markup)


def read_new_order(update, context):
    new_order_text = "Вы заказали: " + update.message.text

    user_id = update.message.from_user.id
    context.bot.send_message(chat_id=update.message.chat_id, text=new_order_text, reply_markup=client_markup)
    return ConversationHandler.END


def cancel_order(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.cancel_order, reply_markup=client_markup)
    return ConversationHandler.END


def back(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.start_command_response, reply_markup=standart_markup)
    return ConversationHandler.END


def client(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.client_response, reply_markup=client_markup)
    return ConversationHandler.END


def courier(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.courier_response, reply_markup=courier_markup)
    return ConversationHandler.END


def ping(update, context):
    print(update.message.chat_id)
    context.bot.send_message(chat_id=1025926145, text="/showorders")


token = os.environ['TELEGRAM_BOT_TOKEN']
updater = Updater(token, use_context=True)
dp = updater.dispatcher


def main():
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('menu', menu))

    make_order_handler = ConversationHandler(
        entry_points=[CommandHandler('makeorder', make_order)],

        states={
            bot_states.READ_NEW_ORDER: [MessageHandler(Filters.text, read_new_order)]
        },

        fallbacks=[CommandHandler('cancel_order', cancel_order)]
    )
    dp.add_handler(make_order_handler)
    dp.add_handler(CommandHandler('client', client))
    dp.add_handler(CommandHandler('courier', courier))
    dp.add_handler(CommandHandler('back', back))


    dp.add_handler(CommandHandler('ping', ping)) # TODO

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
