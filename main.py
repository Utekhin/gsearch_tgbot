import asyncio
from aiogram import Bot, Dispatcher, executor, types
from googlesearch import search

import db_helper
from config import API_TOKEN


# Initialize bot & dispatcher
bot = Bot(API_TOKEN)
dp = Dispatcher(bot)


about = '''Asynchronous Google search Telegram bot built on \
<code>aiogram</code> & <code>googlesearch</code>.

GitHub repo: <a href='https://github.com/fleischgewehr/gsearch_tgbot'>here</a>'''


@dp.message_handler(commands=['start'])
async def welcome(message):
    # Init defaults for search func
    if not db_helper.check_if_exists(message.chat.id):
        db_helper.set_defaults(message.chat.id)

    _keyboard = [
            [types.KeyboardButton('🔧 Settings'),
            types.KeyboardButton('⚙ Source code'),]]
 
    keyboard = types.ReplyKeyboardMarkup(keyboard=_keyboard,
                                            resize_keyboard=True)
    await bot.send_message(message.chat.id, 
                            'Send me your query.', reply_markup=keyboard)

    dp.register_message_handler(change_user_settings, text='🔧 Settings')
    dp.register_message_handler(feedback_msg, text='⚙ Source code')


@dp.message_handler(regexp='🔧 Settings')
async def change_user_settings(message):
    # show inline keyboard with params
    _keyboard = [
        [types.KeyboardButton('👅 Results language'), 
        types.KeyboardButton('⏳ Time filter'),],
        [types.KeyboardButton('🔞 Safe search'),
        types.KeyboardButton('🔙 Back')],
    ]

    keyboard = types.ReplyKeyboardMarkup(keyboard=_keyboard,
                                            resize_keyboard=True)

    settings = db_helper.show_settings(message.chat.id)
    current_settings = '''Your settings:

- Language: {0}
- Safe search: {1}

Choose an option:
    '''.format(settings['lang'], settings['safe'])
    if settings:
        await bot.send_message(message.chat.id, current_settings,
                                reply_markup=keyboard)
    else:
        await bot.send_message(message.chat.id,
                                'Error. Enter /home and try again.')

    dp.register_message_handler(change_query_language,
                                text='👅 Results language')
    dp.register_message_handler(change_tbs,
                                text='⏳ Time filter')
    dp.register_message_handler(switch_safesearch,
                                text='🔞 Safe search')


dp.register_message_handler(welcome, commands=['home'])
dp.register_message_handler(welcome, text='🔙 Back')
dp.register_message_handler(change_user_settings, text='🔙')


async def feedback_msg(message):
    await bot.send_message(message.chat.id, text=about,
                            parse_mode='html', disable_web_page_preview=True)


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

    keyboard = types.ReplyKeyboardMarkup(keyboard=_keyboard,
                                        resize_keyboard=True)
    await bot.send_message(message.chat.id, text=reply, reply_markup=keyboard)

    dp.register_message_handler(lang_handler,
                                lambda message: message.text in db_helper.langs)


async def lang_handler(message):
    new_lang = db_helper.change_lang(message.chat.id, message.text)
    await bot.send_message(message.chat.id,
                'Your language was set to: {}.\n\n/home'.format(new_lang))


async def change_tbs(message):
    # todo: inline keyboard here. handle input in next func
    _keyboard = [
            [types.KeyboardButton('Last hour'),
            types.KeyboardButton('Last 24 hours'),
            types.KeyboardButton('Last month'),
            types.KeyboardButton('🔙')]
        ]

    keyboard = types.ReplyKeyboardMarkup(keyboard=_keyboard,
                                            resize_keyboard=True)
    await bot.send_message(message.chat.id,
        'Choose how relevant results will be.\n\n/home', reply_markup=keyboard)

    dp.register_message_handler(tbs_handler,
                            lambda message: message.text in db_helper.tbs_params)


async def tbs_handler(message):
    new_tbs = db_helper.change_tbs(message.chat.id, message.text)
    await bot.send_message(message.chat.id,
        'Now you will only get results from {}.\n\n/home'.format(message.text.lower()))


async def switch_safesearch(message):
    flag = db_helper.switch_safesearch(message.chat.id)
    await bot.send_message(message.chat.id,
                text='Done, now safe search is {}.'.format(flag))


@dp.message_handler(regexp='test')
async def get_user_query(message):
    results = []
    settings = db_helper.show_settings(message.chat.id)

    try:
        async for res in search(message.text, lang=settings['lang'],
                                tbs=settings['tbs'], safe=settings['safe'],
                                user_agent=settings['user_agent']):
            results.append(res)
            if len(results) == 5:
                # return first 5 results. todo: add inline keyboard
                # with pagination
                await bot.send_message(message.chat.id, results)

    except Exception as e:
        # if got 503 error - change user agent

        # TODO: fix new user agent format
        db_helper.change_user_agent(message.chat.id)
        await bot.send_message(message.chat.id, e)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
