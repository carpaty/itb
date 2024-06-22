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

import logging
import uuid
import re
import os
import yaml
import telegram
import db

VERSION = "0.0.1"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, )

logger = logging.getLogger(__name__)

cache = db.Cache()

with open('menu.yaml', encoding="utf-8", mode="r") as f:
    file = f.read()
cfg = yaml.load(file, Loader=yaml.FullLoader)

KEY = os.environ.get('TELEGRAM_TOKEN', "XXX")

EMOJI_PATTERN = re.compile(
    "^["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"
    "]+"
)


async def post_tg(uid, tg_text) -> None:
    """
    Send a message to a user on Telegram.

    :param uid: User ID
    :type uid: int
    :param tg_text: Text message to be sent
    :type tg_text: str
    """
    bot = telegram.Bot(token=KEY)
    logger.info("Message '%s' sent to %s", tg_text, uid)
    await bot.send_message(chat_id=uid, text=tg_text)


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


def call_pattern():
    """
    Get all call functions from menu.yaml.

    :return: Regex pattern
    :rtype: str
    """
    return re.compile(f"^({'|'.join(find_all_call(cfg, 'call'))})$")


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
    """
    sql = db.Sql()
    sql.qinsert(uid, uuid.uuid4().hex)


def getuidbyhash(user_hash):
    """
    Get the user ID by hash.

    :param user_hash: User hash (UUID)
    :type user_hash: str
    :return: User ID
    :rtype: int
    """
    sql = db.Sql()
    res = list(sql.qselect_hash(user_hash))
    return res[0].id


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
