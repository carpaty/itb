# MIT License
#
# Copyright (c) 2024 carpaty https://github.com/carpaty
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -*- coding: utf-8 -*-
""" Util module """

import hashlib
import hmac
import logging
import os
import re
import secrets
from pathlib import Path
import yaml
import telegram
import db

VERSION = "0.1.0"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, )

logger = logging.getLogger(__name__)

cache = db.Cache()

cfg = yaml.safe_load(Path(__file__).with_name('menu.yaml').read_text(encoding="utf-8"))

KEY = os.environ.get('TELEGRAM_TOKEN', "XXX")

# Telegram only accepts [A-Za-z0-9_-]{1,256}; derive a stable value from the
# token so every instance agrees on it without extra configuration.
WEBHOOK_SECRET = os.environ.get('TELEGRAM_WEBHOOK_SECRET') or hmac.new(
    KEY.encode(), b"itb-webhook-secret", hashlib.sha256).hexdigest()

BOT = telegram.Bot(token=KEY)

BACK_BUTTON = '\U00002B05 Back'


def menu_keys(d):
    """
    Find all menu button labels in the menu configuration.

    :param d: Menu configuration
    :type d: dict
    :yield: Button label
    :rtype: generator
    """
    for k, v in d.items():
        yield k
        if isinstance(v, dict):
            yield from menu_keys(v)


def menu_pattern():
    """
    Build a regex matching exactly the reply keyboard buttons.

    :return: Regex pattern
    :rtype: re.Pattern
    """
    labels = [*menu_keys(cfg), BACK_BUTTON]
    return re.compile(f"^(?:{'|'.join(map(re.escape, labels))})$")


async def post_tg(uid, tg_text) -> None:
    """
    Send a message to a user on Telegram.

    :param uid: User ID
    :type uid: int
    :param tg_text: Text message to be sent
    :type tg_text: str
    """
    await BOT.send_message(chat_id=uid, text=tg_text)
    logger.info("Message sent to %s", uid)


def find_key(d, target_key, parent_key=None):
    """
    Find a key in a nested dictionary.

    :param d: The dictionary to search
    :type d: dict
    :param target_key: The key to find
    :type target_key: str
    :param parent_key: The parent key, defaults to None
    :type parent_key: str, optional
    :yield: Parent key
    :rtype: generator
    """
    for k, v in d.items():
        if k == target_key:
            yield parent_key
        if isinstance(v, dict):
            yield from find_key(v, target_key, k)


def find_desc(val, dictionary, desc=''):
    """
    Find a description in a nested dictionary.

    :param val: The value to find
    :type val: any
    :param dictionary: The dictionary to search
    :type dictionary: dict
    :param desc: The description key, defaults to ''
    :type desc: str, optional
    :yield: Description
    :rtype: generator
    """
    for _, v in dictionary.items():
        if v == val:
            yield v
        elif isinstance(v, dict):
            yield from find_desc(val, v, desc)
        elif isinstance(v, list):
            for d in v:
                for _ in find_desc(val, d, desc):
                    if desc in d:
                        yield d[desc]


def find(key, dictionary):
    """
    Find a key in a nested dictionary or list.

    :param key: The key to find
    :type key: str
    :param dictionary: The dictionary to search
    :type dictionary: dict
    :yield: Value associated with the key
    :rtype: generator
    """
    for k, v in dictionary.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            yield from find(key, v)
        elif isinstance(v, list):
            for d in v:
                yield from find(key, d)


def check_state(uid):
    """
    Check the state in the Position DB.

    :param uid: User ID
    :type uid: int
    :return: Database result
    :rtype: iteration
    """
    return cache.qselect(f"state_{uid}")


def update_state(uid, state):
    """
    Update the state in the Position DB.

    :param uid: User ID
    :type uid: int
    :param state: Current state
    :type state: str
    """
    state = {'current': state}
    cache.qinsert(f"state_{uid}", state)


def check_button(uid):
    """
    Check the button state in the Position DB.

    :param uid: User ID
    :type uid: int
    :return: Current button state
    :rtype: str
    """
    return cache.qselect(f"button_{uid}")


def update_button(uid, state):
    """
    Update the button state in the Position DB.

    :param uid: User ID
    :type uid: int
    :param state: Current button state
    :type state: str
    """
    state = {'current': state}
    cache.qinsert(f"button_{uid}", state)


def check_pending(uid):
    """
    Get the action waiting for a Yes/No confirmation.

    :param uid: User ID
    :type uid: int
    :return: Pending action and its data
    :rtype: dict
    """
    return cache.qselect(f"pending_{uid}")


def update_pending(uid, action, data):
    """
    Store an action waiting for a Yes/No confirmation.

    :param uid: User ID
    :type uid: int
    :param action: Action name
    :type action: str
    :param data: User input the action applies to
    :type data: str
    """
    cache.qinsert(f"pending_{uid}", {'action': action, 'data': data})


def clear_pending(uid):
    """
    Drop the pending confirmation of a user.

    :param uid: User ID
    :type uid: int
    """
    cache.qdelete(f"pending_{uid}")


def find_all_call(d, tag):
    """
    Find all calls from the data.

    :param d: YAML data
    :type d: dict
    :param tag: Name of the item
    :type tag: str
    :yield: Item
    :rtype: generator
    """
    for v in d.values():
        if v == tag:
            yield v
        elif isinstance(v, dict):
            yield from find_all_call(v, tag)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and tag in item:
                    yield item[tag]


def menu_calls():
    """
    Get the names of all calls declared in menu.yaml.

    :return: Call names
    :rtype: set[str]
    """
    return set(find_all_call(cfg, 'call'))


def call_pattern():
    """
    Get all call functions from menu.yaml.

    :return: Regex pattern
    :rtype: str
    """
    return re.compile(f"^({'|'.join(map(re.escape, sorted(menu_calls())))})$")


def user_check(uid):
    """
    Check if a user exists in the Users DB.

    :param uid: User ID
    :type uid: int
    :return: Database result
    :rtype: iteration
    """
    sql = db.Sql()
    res = sql.qselect(uid)
    return res


def user_insert(uid):
    """
    Insert a new user into the Users DB.

    :param uid: User ID
    :type uid: int
    :return: New API key
    :rtype: str
    """
    return rotate_key(uid)


def rotate_key(uid):
    """
    Generate a new API key for a user, invalidating the previous one.

    :param uid: User ID
    :type uid: int
    :return: New API key
    :rtype: str
    """
    api_key = secrets.token_hex(16)
    db.Sql().qinsert(uid, api_key)
    return api_key


def getuidbyhash(user_hash):
    """
    Get the user ID by hash.

    :param user_hash: User hash (UUID)
    :type user_hash: str
    :return: User ID, or None if the hash is unknown
    :rtype: int | None
    """
    sql = db.Sql()
    res = list(sql.qselect_hash(user_hash))
    return res[0].key.id_or_name if res else None


def gethashbyuid(uid):
    """
    Get the hash by user ID.

    :param uid: User ID
    :type uid: int
    :return: User hash (UUID)
    :rtype: str
    """
    sql = db.Sql()
    res = sql.qselect(uid)
    return res
