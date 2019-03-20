import asyncio
from aiogram import Bot, Dispatcher, executor, types
from googlesearch import search

import db_helper
from config import API_TOKEN


# Initialize bot & dispatcher
bot = Bot(API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def welcome(message):
	# Init defaults for search func
	if not db_helper.check_if_exists(message.chat.id):
		db_helper.set_defaults(message.chat.id)
	await message.reply('Send me your query.')


@dp.message_handler(regexp='🔧 Settings')
async def change_user_settings(message):
	# show inline keyboard with params
	_keyboard = [
        [types.KeyboardButton('👅 Results language')], 
        [types.KeyboardButton('⏳ Time filter')],
        [types.KeyboardButton('🔞 Safe search')],
        [types.KeyboardButton('🔙 Back')],
    ]

	keyboard = types.ReplyKeyboardMarkup(keyboard=_keyboard)

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
								'Error. Enter /start and try again.')


@dp.message_handler(regexp='👅 Results language')
async def change_query_language(message):
	current = db_helper.show_settings(message.chat.id)
	reply = 'Your current language is: {}'.format(current['lang'])
	
	_keyboard = [
        [types.KeyboardButton('🇬🇧')], 
        [types.KeyboardButton('🇷🇺')],
        [types.KeyboardButton('🇪🇸')],
        [types.KeyboardButton('🇩🇪')],
        [types.KeyboardButton('🇨🇳')],
    ]

	keyboard = types.ReplyKeyboardMarkup(keyboard=_keyboard)
	await bot.send_message(message.chat.id, text=reply, reply_markup=keyboard)


@dp.message_handler(regexp='⏳ Time filter')
async def change_tbs(message):
	# todo: inline keyboard here. handle input in next func
	await bot.send_message(message.chat.id,
							'Choose how relevant results will be.')


@dp.message_handler(regexp='🔞 Safe search')
async def switch_safesearch(message):
	flag = db_helper.switch_safesearch(message.chat.id)
	await bot.send_message(message.chat.id,
							text='Done, now safe search is {}.'.format(flag))


@dp.message_handler(regexp='🔙 Back')
async def main_menu(message):
	# set main inline keyboard
	pass


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
