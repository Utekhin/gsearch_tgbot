import asyncio

from aiogram import Bot, Dispatcher, executor, types
from googlesearch import search

import db_helper
from config import API_TOKEN


# initialize bot & dispatcher
bot = Bot(API_TOKEN)
dp = Dispatcher(bot)

# response templates
about = '''Asynchronous Google search Telegram bot built on \
<code>aiogram</code> & <code>googlesearch</code>.

GitHub repo: <a href='https://github.com/fleischgewehr/gsearch_tgbot'>here</a>'''
current_settings = '''Your settings:

- Language: {0}
- Safe search: {1}

Choose an option:'''


@dp.message_handler(commands=['start'])
async def welcome(message):
    # init defaults on first launch
    if not db_helper.check_if_exists(message.chat.id):
        db_helper.set_defaults(message.chat.id)

    _keyboard = [
            [types.KeyboardButton('🔧 Settings'),
            types.KeyboardButton('⚙ Source code')],
        ]
 
    keyboard = types.ReplyKeyboardMarkup(
            keyboard=_keyboard, resize_keyboard=True)

    await bot.send_message(
            message.chat.id, text='Send me your query.', reply_markup=keyboard)


    dp.register_message_handler(change_user_settings, text='🔧 Settings')
    dp.register_message_handler(feedback_msg, text='⚙ Source code')


async def change_user_settings(message):
    _keyboard = [
        [types.KeyboardButton('👅 Results language'), 
        types.KeyboardButton('⏳ Time filter'),],
        [types.KeyboardButton('🔞 Safe search'),
        types.KeyboardButton('🔙 Back')],
    ]

    keyboard = types.ReplyKeyboardMarkup(
            keyboard=_keyboard, resize_keyboard=True)

    settings = db_helper.show_settings(message.chat.id)

    if settings:
        await bot.send_message(
                message.chat.id,
                text=current_settings.format(settings['lang'], settings['safe']),
                reply_markup=keyboard)
    else:
        await bot.send_message(
                message.chat.id, text='Error. Enter /home and try again.')

    dp.register_message_handler(change_query_language, text='👅 Results language')
    dp.register_message_handler(change_tbs, text='⏳ Time filter')
    dp.register_message_handler(switch_safesearch, text='🔞 Safe search')


async def feedback_msg(message):
    await bot.send_message(
            message.chat.id, text=about, parse_mode='html',
            disable_web_page_preview=True)


async def change_query_language(message):
    current = db_helper.show_settings(message.chat.id)
    reply = 'Your current language is: {}.\n\n/home'.format(current['lang'])
    
    _keyboard = [
        [types.KeyboardButton('🇬🇧'), 
        types.KeyboardButton('🇷🇺'),
        types.KeyboardButton('🇪🇸'),
        types.KeyboardButton('🇩🇪'),
        types.KeyboardButton('🇨🇳'),
        types.KeyboardButton('🔙')],
    ]

    keyboard = types.ReplyKeyboardMarkup(
            keyboard=_keyboard, resize_keyboard=True)
    await bot.send_message(message.chat.id, text=reply, reply_markup=keyboard)

    # handling only possible langs specified in langs dict in db_helper
    dp.register_message_handler(
        lang_handler, lambda message: message.text in db_helper.langs)


async def lang_handler(message):
    new_lang = db_helper.change_lang(message.chat.id, message.text)
    await bot.send_message(
            message.chat.id, 
            text='Your language was set to: {}.\n\n/home'.format(new_lang))


async def change_tbs(message):
    _keyboard = [
            [types.KeyboardButton('Last hour'),
            types.KeyboardButton('Last 24 hours'),
            types.KeyboardButton('Last month'),
            types.KeyboardButton('🔙')],
        ]

    keyboard = types.ReplyKeyboardMarkup(
            keyboard=_keyboard, resize_keyboard=True)

    await bot.send_message(
            message.chat.id, text='Choose how relevant results will be.\n\n/home',
            reply_markup=keyboard)

    # handling only tbs options such as 'last hour' etc
    dp.register_message_handler(
        tbs_handler, lambda message: message.text in db_helper.tbs_params)


async def tbs_handler(message):
    new_tbs = db_helper.change_tbs(message.chat.id, message.text)
    await bot.send_message(
            message.chat.id,
            text='Now you will only get results from {}.\n\n/home'.format(
                                                        message.text.lower()))


async def switch_safesearch(message):
    flag = db_helper.switch_safesearch(message.chat.id)
    await bot.send_message(
            message.chat.id, text='Done, now safe search is {}.'.format(flag))


# placing 'test query' prevents from random queries during testing
# will be replaced to normal regex later on
@dp.message_handler(regexp='seth rollins')
async def get_user_query(message):
    results = []
    settings = db_helper.show_settings(message.chat.id)
    try:
        async for res in search(
                            query=message.text, lang=settings['lang'],
                            safe=settings['safe'], tbs=settings['tbs'],
                            user_agent=settings['user_agent'], detailed=True):
            results.append(res)
            if len(results) == 5:
                # return first 5 results. todo: add inline keyboard
                # with pagination
                response = show_results(results, 1)
                await bot.send_message(
                        message.chat.id, text=response, parse_mode='html',
                        disable_web_page_preview=True)

    except Exception as e:
        # if user got http 503 error - change user agent
        db_helper.change_user_agent(message.chat.id)
        await bot.send_message(message.chat.id, text=e)


def show_results(arr, page):
    # returns five results depending on page
    results = arr[page*5-5:page*5]

    response = 'Page {}. Results:\n\n'.format(page)
    for r in results:
        response = response + '- <a href="{0}">{1}</a>\n\n'.format(r[1], r[0])
    return response


# these handlers work everywhere
dp.register_message_handler(welcome, commands=['home'])
dp.register_message_handler(welcome, text='🔙 Back')
dp.register_message_handler(change_user_settings, text='🔙')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
