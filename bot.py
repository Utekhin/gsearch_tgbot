import asyncio

from aiogram import Bot, Dispatcher, executor, types
from googlesearch import search

from core import db_helper
from core.config import API_TOKEN


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

# results are stored here
results = []


@dp.message_handler(commands=['start'])
async def welcome(message):
    # init defaults on first launch
    if not db_helper.check_if_exists(message.chat.id):
        db_helper.set_defaults(message.chat.id)

    _keyboard = [
            [types.KeyboardButton('🔧 Settings'),
            types.KeyboardButton('⚙ Source code')],
        ]
 
    keyboard = types.ReplyKeyboardMarkup(keyboard=_keyboard, resize_keyboard=True)

    await bot.send_message(
            message.chat.id, text='Send me your query.', reply_markup=keyboard)


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


# handles both search queries and switching pages:
# if instance of call is 'Message' it runs search func;
# if instance is 'CallbackQuery' it returns requested results page
@dp.callback_query_handler(lambda call: True)
@dp.message_handler(regexp='.*')
async def get_user_query(instance):
    keyboard = show_inline_keyboard()
    
    if isinstance(instance, types.Message):
        global results
        results = []
        try:
            settings = db_helper.show_settings(instance.chat.id)
            async for res in search(
                                query=instance.text, lang=settings['lang'],
                                safe=settings['safe'], tbs=settings['tbs'],
                                stop=40, user_agent=settings['user_agent'],
                                detailed=True):
                results.append(res)
                if len(results) == 8:
                    # returns first 5 results
                    response = show_results(results, 1)
                    await bot.send_message(
                            instance.chat.id, text=response, parse_mode='html',
                            disable_web_page_preview=True, reply_markup=keyboard)

        except Exception as e:
            # if user got http 503 error - change user agent
            db_helper.change_user_agent(instance.chat.id)
            await bot.send_message(instance.chat.id, text=e)

    elif isinstance(instance, types.CallbackQuery):
        response = show_results(results, int(instance.data))
        await bot.send_message(
                instance.from_user.id, text=response, parse_mode='html',
                disable_web_page_preview=True, reply_markup=keyboard)


def show_results(arr, page):
    # returns eight results depending on page
    results = arr[page*8-8:page*8]

    response = 'Page {}. Results:\n\n'.format(page)
    for r in results:
        response = response + '- <a href="{0}">{1}</a>\n\n'.format(r[1], r[0])
    return response


def show_inline_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
            types.InlineKeyboardButton(text='1', callback_data=1),
            types.InlineKeyboardButton(text='2', callback_data=2),
            types.InlineKeyboardButton(text='3', callback_data=3),
            types.InlineKeyboardButton(text='4', callback_data=4),
            types.InlineKeyboardButton(text='5', callback_data=5))

    return keyboard


# these handlers work everywhere
dp.register_message_handler(welcome, commands=['home'])
dp.register_message_handler(welcome, text='🔙 Back')
dp.register_message_handler(change_user_settings, text='🔙')
dp.register_message_handler(change_user_settings, text='🔧 Settings')
dp.register_message_handler(feedback_msg, text='⚙ Source code')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
