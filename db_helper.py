from pymongo import MongoClient

from config import CREDENTIALS


client = MongoClient(CREDENTIALS)
db = client.tg_bot
collection = db.user_settings


def set_defaults(user_id):
	post = {
		'user': user_id,
		'lang': 'en',
		'tbs': 0,
		'safe': 'off',
		'user_agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)',
		'detailed': 'off',
	}

	db.user_settings.insert_one(post)


def change_settings(user_id, key, val):
	db.user_settings.replace_one({'user': user_id}, {key: val})


def show_settings(user_id):
	settings = db.user_settings.find_one({'user': user_id})
	del settings['_id']
	return settings


def check_if_exists(user_id):
	return True if db.user_settings.find_one({'user': user_id}) else False