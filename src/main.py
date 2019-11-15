from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import requests
import re
import src.bot_states as bot_states
import src.bot_messages as bot_essages
from src.data_base import Courier
from src.data_base import Order
import telegram
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os
import src.map
import pdfcrowd

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

custom_keyboard = [['/client'], ['/courier']]
client_keyboard = [['/menu'], ['/makeorder'], ['/back']]
courier_keyboard = [['/back']]
order_keyboard = [['/cancel_order']]
priority_keyboard = [['HIGH'],
                     ['LOW'],
                     ['/cancel_order']]
location_keyboard = [[telegram.KeyboardButton(text="Отправить местоположение", request_location=True)],
                     ['/cancel_order']]

standart_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
order_reply_markup = telegram.ReplyKeyboardMarkup(order_keyboard, resize_keyboard=True)
client_markup = telegram.ReplyKeyboardMarkup(client_keyboard, resize_keyboard=True)
courier_markup = telegram.ReplyKeyboardMarkup(courier_keyboard, resize_keyboard=True)

location_markup = telegram.ReplyKeyboardMarkup(location_keyboard, resize_keyboard=True)
priority_markup = telegram.ReplyKeyboardMarkup(priority_keyboard, resize_keyboard=True)


def get_url(admin):
    if admin:
        contents = requests.get('https://random.dog/woof.json').json()
        url = contents['url']
        return url
    contents = requests.get('https://www.themealdb.com/api/json/v1/1/random.php').json()
    url = contents['meals'][0]['strMealThumb']
    return url


def start(update, context):
    update.message.reply_text(bot_messages.start_command_response, reply_markup=standart_markup)


def menu(update, context):
    chat_id = update.message.chat_id
    url = get_url(chat_id in managers)
    context.bot.send_photo(chat_id=chat_id, photo=url)


def make_order(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.add_new_order, reply_markup=order_reply_markup)
    return bot_states.READ_NEW_ORDER


def read_new_order(update, context):
    new_order_text = "Вы хотите заказать: " + update.message.text + "\n" \
        "Укажите своё местоположение: "
    context.bot.send_message(chat_id=update.message.chat_id, text=new_order_text, reply_markup=location_markup)
    return bot_states.READ_USER_LOCATION


def read_user_location(update, context):
    text = "Выберите приоритет вашего заказа: \n"
    context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=priority_markup)
    #context.bot.sendLocation(chat_id=update.message.chat_id, latitude=update.message.location['latitude'], longitude=update.message.location['longitude']);
    return bot_states.READ_USED_PRIORITY


def read_user_priority(update, context):
    text = "Мы приняли ваш заказ!\n"

    context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=client_markup)
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


def admin(update, context):
    if context.args:
        if context.args[0] == admin_key:
            managers.append(update.message.chat_id)
            print("manager added")
    return None


# FOR DEBUGING
def ping(update, context):
    print("context")
    print(type(context))
    print("update")
    print(update)

    map = src.map.Map()
    map.add_placemark([55.7550256, 48.7445183], hint='Заказ 1', icon_color="#ff0000")
    map.add_placemark([55.7550256, 48.7455183], hint='Заказ 2', icon_color="#0000ff")
    map.add_route([55.7550256, 48.7455183], [55.7550256, 48.7445183])
    map.save_html('test_map.html')

    filename = 'test_image.jpg'
    output_stream = open(filename, 'wb')
    client = pdfcrowd.HtmlToImageClient('ansat_', '11f90dbbb4b98960fe5bfdd61cef9d5f')
    client.setScreenshotWidth(640)
    client.setScreenshotHeight(480)
    client.setOutputFormat('jpg')
    client.convertFileToStream('test_map.html', output_stream)
    output_stream.close()

    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(filename, 'rb'), reply_markup=location_markup)


managers = []
admin_key = os.environ['TELEGRAM_ADMIN_KEY']
token = os.environ['TELEGRAM_BOT_TOKEN']
updater = Updater(token, use_context=True)
dp = updater.dispatcher


def main():
    Courier.create_table()
    Order.create_table()

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('menu', menu))

    make_order_handler = ConversationHandler(
        entry_points=[CommandHandler('makeorder', make_order)],

        states={
            bot_states.READ_NEW_ORDER: [MessageHandler(Filters.text, read_new_order)],
            bot_states.READ_USER_LOCATION: [MessageHandler(Filters.location, read_user_location)],
            bot_states.READ_USED_PRIORITY: [MessageHandler(Filters.text, read_user_priority)]
        },

        fallbacks=[CommandHandler('cancel_order', cancel_order)]
    )
    dp.add_handler(make_order_handler)
    dp.add_handler(CommandHandler('client', client))
    dp.add_handler(CommandHandler('courier', courier))
    dp.add_handler(CommandHandler('back', back))
    dp.add_handler(CommandHandler('admin', admin))

    dp.add_handler(CommandHandler('ping', ping))  # TODO

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
