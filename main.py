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
	user_id = message.chat.id
	# Init defaults for search func
	if not db_helper.check_if_exists(user_id):
		db_helper.set_defaults(user_id)
	await message.reply('Send me your query.')


@dp.message_handler(regexp='test')
async def get_user_query(message):
	results = []
	try:
		# todo: parse user settings from db
		async for res in search(message.text):
			results.append(res)
			if len(results) == 5:
				# return first 5 results. todo: add inline keyboard
				# with pagination
				await bot.send_message(message.chat.id, results)
	except Exception as e:
		# todo: if 503 change user-agent here	
		await bot.send_message(message.chat.id, e)


# debug func - db_helper testing
@dp.message_handler(regexp='Show')
async def my_settings(message):
	user_id = message.chat.id
	settings = db_helper.show_settings(user_id)
	response = '''Your settings:

Language: {0}
Safe search: {1}
Detailed: {2}
	'''.format(settings['lang'], settings['safe'], settings['detailed'])
	if settings:
		await bot.send_message(message.chat.id, settings)
	else:
		await bot.send_message(message.chat.id, 'Error')



if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)
