from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import requests
import re
import src.bot_states as bot_states
import src.bot_messages as bot_messages
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
admin_keyboard = [['/client'], ['/courier'], ['/admin_panel']]

admin_functions_keyboard = [['/admin_get_courier_list'],
                            ['/admin_get_order_list'],
                            ['/admin_print_couriers_map'],
                            ['/admin_print_orders_map'],
                            ['/assign'],
                            ['/back']]

client_keyboard = [['/menu'], ['/makeorder'], ['/back']]
courier_keyboard = [['/getjob'], ['/back']]
back_only_keyboard = [['/back']]
yes_no_keyboard = [['Да'], ['Нет']]
order_keyboard = [['/cancel_order']]
priority_keyboard = [['HIGH'],
                     ['LOW'],
                     ['/cancel_order']]
user_location_keyboard = [[telegram.KeyboardButton(text="Отправить местоположение", request_location=True)],
                     ['/cancel_order']]
courier_location_keyboard = [[telegram.KeyboardButton(text="Отправить местоположение", request_location=True)],
                     ['/cancel_registration']]

reg_couriers_keyboard = [['/current_orders'], ['/back']]


standart_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
admin_markup = telegram.ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)
admin_functions_markup = telegram.ReplyKeyboardMarkup(admin_functions_keyboard, resize_keyboard=True)
order_reply_markup = telegram.ReplyKeyboardMarkup(order_keyboard, resize_keyboard=True)
client_markup = telegram.ReplyKeyboardMarkup(client_keyboard, resize_keyboard=True)
courier_markup = telegram.ReplyKeyboardMarkup(courier_keyboard, resize_keyboard=True)
back_only_markup = telegram.ReplyKeyboardMarkup(back_only_keyboard, resize_keyboard=True)
yes_no_markup = telegram.ReplyKeyboardMarkup(yes_no_keyboard, resize_keyboard=True)
reg_couriers_markup = telegram.ReplyKeyboardMarkup(reg_couriers_keyboard, resize_keyboard=True)

user_location_markup = telegram.ReplyKeyboardMarkup(user_location_keyboard, resize_keyboard=True)
courier_location_markup = telegram.ReplyKeyboardMarkup(courier_location_keyboard, resize_keyboard=True)
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


order_json = {}

def make_order(update, context):
    order_json.clear()
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.add_new_order, reply_markup=order_reply_markup)
    return bot_states.READ_NEW_ORDER


def read_new_order(update, context):
    order_json['text'] = update.message.text
    new_order_text = "Вы хотите заказать: " + update.message.text + "\n" \
        "Укажите своё местоположение: "
    context.bot.send_message(chat_id=update.message.chat_id, text=new_order_text, reply_markup=user_location_markup)
    return bot_states.READ_USER_LOCATION


def read_user_location(update, context):
    order_json['latitude'] = update.message.location['latitude']
    order_json['longitude'] = update.message.location['longitude']
    text = "Выберите приоритет вашего заказа: \n"
    context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=priority_markup)
    #context.bot.sendLocation(chat_id=update.message.chat_id, latitude=update.message.location['latitude'], longitude=update.message.location['longitude']);
    return bot_states.READ_USED_PRIORITY


order_id = 0


def read_user_priority(update, context):
    order_json['priority'] = update.message.text
    text = "Мы приняли ваш заказ!\n"
    global order_id
    print(order_id)
    print(order_json)
    Order.create(text=order_json['text'], locationX = order_json['latitude'], locationY = order_json['longitude'], order_id = order_id, priority = order_json['priority'], status = 0,
                 client_id=update.message.chat_id, courier = -1)
    order_id += 1
    order_json.clear()
    context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=client_markup)
    return ConversationHandler.END


def cancel_order(update, context):
    order_json.clear()
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.cancel_order, reply_markup=client_markup)
    return ConversationHandler.END


def cancel_registration(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.cancel_registration, reply_markup=courier_markup)
    return ConversationHandler.END


def get_job(update, context):
    text = "До вашего трудоустройства остался всего один шаг!\n" \
        "Укажите своё местоположение: "
    context.bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=courier_location_markup)
    return bot_states.READ_COURIER_LOCATION


def read_courier_location(update, context):
    Courier.create(courier_id = update.message.chat_id, locationX = update.message.location['latitude'], locationY = update.message.location['longitude'])
    context.bot.send_message(chat_id=update.message.chat_id, text="Вы успешно устроены в нашу компанию!\n Ожидайте заказов.\n",reply_markup=reg_couriers_markup)

    return ConversationHandler.END


def current_orders(update, context):
    try:
        print(update.message.chat_id)
        # orders = Order.select().where(Order.courier == update.message.chat_id).get()
        map = src.map.Map()
        for order in Order.select().where(Order.courier == update.message.chat_id):
            print(order.locationX, order.locationY)
            map.add_placemark([order.locationX, order.locationY], hint='Заказ: {}'.format(order.order_id), icon_color="#ff0000")
        map.save_html('current_orders.html')
        filename = 'current_orders.jpg'
        output_stream = open(filename, 'wb')
        client = pdfcrowd.HtmlToImageClient('ansat_', '11f90dbbb4b98960fe5bfdd61cef9d5f')
        client.setScreenshotWidth(640)
        client.setScreenshotHeight(480)
        client.setOutputFormat('jpg')
        client.convertFileToStream('current_orders.html', output_stream)
        output_stream.close()

        context.bot.send_photo(chat_id=update.message.chat_id, photo=open(filename, 'rb'), reply_markup=back_only_markup)
        os.remove('current_orders.html')
        os.remove('current_orders.jpg')
        return ConversationHandler.END
    except Order.DoesNotExist:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.no_orders, reply_markup=back_only_markup)
        return ConversationHandler.END


assign_json = {}
def back(update, context):
    if update.message.chat_id not in managers:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.start_command_response, reply_markup=standart_markup)
    else:
        assign_json.clear()
        context.bot.send_message(chat_id=update.message.chat_id, text="Возвращаемся", reply_markup=admin_functions_markup)
    return ConversationHandler.END


def client(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.client_response, reply_markup=client_markup)
    return ConversationHandler.END


def courier(update, context):
    try:
        courier = Courier.select().where(Courier.courier_id == update.message.chat_id).get()
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.reg_courier_response, reply_markup=reg_couriers_markup)
        return ConversationHandler.END
    except Courier.DoesNotExist:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.new_courier_response, reply_markup=courier_markup)
        return ConversationHandler.END


def admin(update, context):
    if context.args:
        if context.args[0] == admin_key:
            managers.append(update.message.chat_id)
            context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.admin_panel, reply_markup=admin_functions_markup)
            print("manager added")
    return ConversationHandler.END


def admin_panel(update, context):
    if update.message.chat_id not in managers:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.not_admin, reply_markup=standart_markup)
        return ConversationHandler.END
    context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.admin_panel, reply_markup=admin_functions_markup)



def admin_print_orders_map(update, context):
    if update.message.chat_id not in managers:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.not_admin, reply_markup=standart_markup)
        return ConversationHandler.END
    print("create map")
    map = src.map.Map()
    for order in Order.select():
        print(order.locationX, order.locationY)
        map.add_placemark([order.locationX, order.locationY], hint='Заказ: {}'.format(order.order_id), icon_color="#ff0000")
    map.save_html('orders.html')
    print("save map")
    filename = 'orders.jpg'
    output_stream = open(filename, 'wb')
    client = pdfcrowd.HtmlToImageClient('ansat_', '11f90dbbb4b98960fe5bfdd61cef9d5f')
    client.setScreenshotWidth(640)
    client.setScreenshotHeight(480)
    client.setOutputFormat('jpg')
    client.convertFileToStream('orders.html', output_stream)
    output_stream.close()
    print("send map image")
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(filename, 'rb'), reply_markup=admin_functions_markup)
    os.remove('orders.html')
    os.remove('orders.jpg')
    return ConversationHandler.END

def admin_print_couriers_map(update, context):
    if update.message.chat_id not in managers:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.not_admin, reply_markup=standart_markup)
        return ConversationHandler.END
    print("create map")
    map = src.map.Map()
    for courier in Courier.select():
        print(courier.locationX, courier.locationY)
        map.add_placemark([courier.locationX, courier.locationY], hint='Курьер: {}'.format(courier.courier_id), icon_color="#ff00ff")
    map.save_html('couriers.html')
    print("save map")
    filename = 'couriers.jpg'
    output_stream = open(filename, 'wb')
    client = pdfcrowd.HtmlToImageClient('ansat_', '11f90dbbb4b98960fe5bfdd61cef9d5f')
    client.setScreenshotWidth(640)
    client.setScreenshotHeight(480)
    client.setOutputFormat('jpg')
    client.convertFileToStream('couriers.html', output_stream)
    output_stream.close()
    print("send map image")
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(filename, 'rb'), reply_markup=admin_functions_markup)
    os.remove('couriers.html')
    os.remove('couriers.jpg')
    return ConversationHandler.END


def admin_get_order_list(update, context):
    if update.message.chat_id not in managers:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.not_admin, reply_markup=standart_markup)
        return ConversationHandler.END
    result = ""
    for order in Order.select():
        print(order.locationX, order.locationY)

        result = result + "Order ID: " + str(order.order_id) + "\n"
        result = result + "Status: " + str(order.status) + "\n"
        result = result + "Text: " + str(order.text) + "\n"
        result = result + "Priority: " + str(order.priority) + "\n"
        if order.courier != -1:
            result = result + "Courier: " + str(order.courier) + "\n"
        result = result + "\n"
    if len(result) == 0:
        context.bot.send_message(chat_id=update.message.chat_id, text="Заказы еще не появились..", reply_markup=admin_functions_markup)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text=result, reply_markup=admin_functions_markup)
    return ConversationHandler.END


def admin_get_courier_list(update, context):
    if update.message.chat_id not in managers:
        context.bot.send_message(chat_id=update.message.chat_id, text=bot_messages.not_admin, reply_markup=standart_markup)
        return ConversationHandler.END
    result = ""
    try:
        for courier in Courier.select():
            result = result + "Courier ID: " + str(courier.courier_id) + "\n"
        if len(result) == 0:
            context.bot.send_message(chat_id=update.message.chat_id, text="Курьеры еще не появились..", reply_markup=admin_functions_markup)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text=result, reply_markup=admin_functions_markup)
    except Courier.DoesNotExist:
        context.bot.send_message(chat_id=update.message.chat_id, text="Курьеры еще не появились..", reply_markup=admin_functions_markup)
    return ConversationHandler.END



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
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(filename, 'rb'), reply_markup=back_only_markup)
    os.remove('test_map.html')
    os.remove('test_image.jpg')


def assign(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Какому заказу назначить исполнителя? \n", reply_markup=back_only_markup)
    return bot_states.ASSIGN_ORDER


def print_order(order_id):
    order_text = ""
    try:
        tmp_order = Order.select().where(Order.order_id == order_id).get()
        order_text = "Order ID: {}, \nText: {}, \nPriority: {} \n".format(tmp_order.order_id, tmp_order.text, tmp_order.priority)
        if tmp_order.courier != -1:
            order_text = order_text + "Courier: " + str(tmp_order.courier)
        return order_text
    except Order.DoesNotExist:
        return order_text


def assign_order(update, context):
    order = update.message.text
    try:
        tmp_order = Order.select().where(Order.order_id == order).get()
        context.bot.send_message(chat_id=update.message.chat_id, text="Вы хотите назначить курьера на заказ: \n" + print_order(tmp_order.order_id) + "Введите номер курьера:\n",
                                 reply_markup=back_only_markup)
        assign_json['order'] = order
        return bot_states.ASSIGN_COURIER
    except Order.DoesNotExist:
        context.bot.send_message(chat_id=update.message.chat_id, text="Такого заказа не существует \n", reply_markup=admin_functions_markup)
        return ConversationHandler.END


def assign_courier(update, context):
    courier = update.message.text
    try:
        tmp_courier = Courier.select().where(Courier.courier_id == courier).get()
        context.bot.send_message(chat_id=update.message.chat_id, text="Вы хотите назначить курьера: \n"
                                                                      "Courier ID: {}, \n".format(tmp_courier.courier_id),
                                 reply_markup=yes_no_markup)
        assign_json['courier'] = courier
        return bot_states.ASSIGN_CONFIRM
    except Courier.DoesNotExist:
        context.bot.send_message(chat_id=update.message.chat_id, text="Такого курьера не существует \n", reply_markup=admin_functions_markup)
        return ConversationHandler.END


def assign_confirm(update, context):
    text = update.message.text
    print("assign confirm", text)
    if text == "Да":
        tmp_order = Order.select().where(Order.order_id == assign_json['order']).get()
        tmp_order.courier = assign_json['courier']
        tmp_order.save()
        print("Link done")
        context.bot.send_message(chat_id=assign_json['courier'], text="Вам пришел заказ:\n" + print_order(assign_json['order']), reply_markup=reg_couriers_markup)
        user_id = Order.get(Order.order_id == assign_json['order']).client_id
        context.bot.send_message(chat_id=user_id, text="Ваш заказ взят курьером {} \n".format(assign_json['courier']), reply_markup=standart_markup)
        context.bot.send_message(chat_id=update.message.chat_id, text="К заказу успешно прикреплен курьер. \nСообщение ему скоро будет отправлено! \n", reply_markup=admin_functions_markup)
    else:
        assign_json.clear()
        context.bot.send_message(chat_id=update.message.chat_id, text="Отменяем операцию \n", reply_markup=admin_functions_markup)
    return ConversationHandler.END


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

    make_courier_handler = ConversationHandler(
        entry_points=[CommandHandler('getjob', get_job)],

        states={
            bot_states.READ_COURIER_LOCATION: [MessageHandler(Filters.location, read_courier_location)]
        },

        fallbacks=[CommandHandler('cancel_registration', cancel_registration)]
    )

    link_order_handler = ConversationHandler(
        entry_points=[CommandHandler('assign', assign)],

        states={
            bot_states.ASSIGN_ORDER: [MessageHandler(Filters.text, assign_order)],
            bot_states.ASSIGN_COURIER: [MessageHandler(Filters.text, assign_courier)],
            bot_states.ASSIGN_CONFIRM: [MessageHandler(Filters.text, assign_confirm)]
        },

        fallbacks=[CommandHandler('back', back)]
    )
    dp.add_handler(link_order_handler)

    dp.add_handler(make_courier_handler)
    dp.add_handler(CommandHandler('current_orders', current_orders))
    dp.add_handler(CommandHandler('cancel_registration', cancel_registration))
    dp.add_handler(CommandHandler('admin_get_order_list', admin_get_order_list))
    dp.add_handler(CommandHandler('admin_get_courier_list', admin_get_courier_list))
    dp.add_handler(CommandHandler('admin_print_orders_map', admin_print_orders_map))
    dp.add_handler(CommandHandler('admin_print_couriers_map', admin_print_couriers_map))

    dp.add_handler(CommandHandler('client', client))
    dp.add_handler(CommandHandler('courier', courier))
    dp.add_handler(CommandHandler('back', back))
    dp.add_handler(CommandHandler('admin', admin))
    dp.add_handler(CommandHandler('admin_panel', admin_panel))

    dp.add_handler(CommandHandler('ping', ping))  # TODO

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
