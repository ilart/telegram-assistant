import logging
import requests
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from telegram import ReplyKeyboardMarkup

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
URL_CAT = 'https://api.thecatapi.com/v1/images/search'
URL_DOG = 'https://api.thedogapi.com/v1/images/search'
URL_EDADEAL = 'https://edadeal.ru/syktyvkar/offers?search=barilla&title=barilla'
ROW = "{offer} \n {store}"
OFFER_TAG = "p-offers__offer"
DRIVER_SLEEP = 7
NEW_PRICE_TAG = "b-offer__price-new"
EMPTY_INPUT = ('Ошибка входхны данных. Файл .env должен содержать параметр '
               'TOKEN. Текущее значение TOKEN={value} ')
SAY_HI = 'Привет, я бот. И пока я ничего не умею'
HELLO = 'Привет {name}'
CONNECTION_ERROR = 'Произошла ошибка: {error}'
REQUEST_ERROR = ('Прервалась связь с сервером'
                 ' URL={url}. {exc}')

updater = Updater(token=TOKEN)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_new_image():
    try:
        url = URL_CAT
        photo = requests.get(url).json()[0]['url']
    except requests.exceptions.RequestException as exception:
        logging.error(exception)
        url = URL_DOG
        photo = requests.get(url).json()[0]['url']
    except Exception as exception:
        raise ConnectionError(
            REQUEST_ERROR.format(
                url=url,
                exc=exception
            )
        )
    return photo


def say_hi(update, context):
    context.bot.send_message(
        update.effective_chat.id,
        SAY_HI
    )


def newcat(update, context):
    context.bot.send_photo(update.effective_chat.id, get_new_image())


def barilla(update, context):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options=options)
    driver.implicitly_wait(DRIVER_SLEEP)
    offer_info = dict(offer='', store='')
    prev_offer_info = offer_info.copy()
    best_offers = []

    try:
        driver.get(URL_EDADEAL)
        offers = driver.find_elements(By.CLASS_NAME, OFFER_TAG)
    except Exception as error:
        logging.error(error)

    for offer in offers:
        store = offer.find_elements(By.TAG_NAME, 'img')[0].get_attribute("title")
        offer = offer.text.split('\n')
        offer_info['offer'] = f"{offer[0]} {offer[3]} руб. {offer[5]}"
        offer_info['store'] = store
        if offer_info == prev_offer_info:
            continue
        prev_offer_info = offer_info.copy()
        best_offers.append(ROW.format(offer=offer_info['offer'], store=store))
    context.bot.send_message(update.effective_chat.id, '\n---\n'.join(best_offers))


def wake_up(update, context):
    chat = update.effective_chat
    text = HELLO.format(name={update.message.chat.first_name})
    print(f'chat_id {chat}')
    button = ReplyKeyboardMarkup([
        ['/newcat'],
        ['/barilla']],
        resize_keyboard=True
    )
    context.bot.send_message(chat_id=chat.id, text=text, reply_markup=button)
    context.bot.send_photo(chat.id, get_new_image())


def main():
    if not TOKEN:
        message = EMPTY_INPUT.format(value=TOKEN)
        logging.error(message)
        raise ValueError(message)
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('newcat', newcat))
    updater.dispatcher.add_handler(CommandHandler('barilla', barilla))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, say_hi))

    updater.start_polling(poll_interval=10)
    updater.idle()

if __name__ == "__main__":
    main()
