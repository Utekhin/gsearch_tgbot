from pymongo import MongoClient
from googlesearch import get_random_user_agent

from core.config import CREDENTIALS


# make connection with mongodb storage
client = MongoClient(CREDENTIALS)
db = client.tg_bot
collection = db.user_settings


# dict for change_tbs()
tbs_params = {
        'Last hour': 'qdr:h',
        'Last 24 hours': 'qdr:d',
        'Last month': 'qdr:m',
        }

# dict for change_lang()
langs = {
        '🇬🇧': 'en',
        '🇷🇺': 'ru',
        '🇪🇸': 'es',
        '🇩🇪': 'de',
        '🇨🇳': 'cn',
        }


def set_defaults(user_id):
    post = {
        'user': user_id,
        'lang': 'en',
        'tbs': 0,
        'safe': 'off',
        'user_agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)',
    }

    db.user_settings.insert_one(post)


def change_user_agent(user_id):
    db.user_settings.update_one(
        {'user': user_id}, {'$set': {'user_agent': get_random_user_agent()}})


def change_lang(user_id, new_lang):
    db.user_settings.update_one(
        {'user': user_id}, {'$set': {'lang': langs[new_lang]}})
    return show_settings(user_id)['lang']


def switch_safesearch(user_id):
    current_settings = show_settings(user_id)
    if current_settings['safe'] == 'off':
        db.user_settings.update_one(
            {'user': user_id}, {'$set': {'safe': 'on'}})
    else:
        db.user_settings.update_one(
            {'user': user_id}, {'$set': {'safe': 'off'}})
    return show_settings(user_id)['safe']


def change_tbs(user_id, new_val):
    db.user_settings.update_one(
        {'user': user_id}, {'$set': {'tbs': tbs_params[new_val]}})
    return show_settings(user_id)['tbs']


def show_settings(user_id):
    settings = db.user_settings.find_one({'user': user_id})
    del settings['_id']
    return settings


def check_if_exists(user_id):
    return True if db.user_settings.find_one({'user': user_id}) else False
