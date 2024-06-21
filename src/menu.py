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

"""
Menu parser
"""
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton)

from utils import (
    find_key,
    find,
    cfg,
    update_state,
    check_state)


def gen_menu(uid, item=""):
    """
    Generate a menu for the user.

    This function generates a menu based on the user's current state and the provided item.
    It returns either a ReplyKeyboardMarkup or InlineKeyboardMarkup object, depending on the
    structure of the menu configuration.

    :param uid: User ID
    :type uid: int
    :param item: Name of the button, defaults to ""
    :type item: str, optional
    :return: JSON representation of the keyboard markup
    :rtype: str
    """
    uid = str(uid)
    if 'Back' in item:
        cur_stat = check_state(uid)
        try:
            a = list(find_key(cfg, cur_stat['current']))
        except KeyError:
            a = ''
        if any(a):
            return gen_menu(uid, a[0])
        return gen_menu(uid, "")

    list_item_keyboard = []
    list_item_inline = []
    if item:
        list_find = {}
        for i in find(item, cfg):
            list_find = i
        if isinstance(list_find, dict) and list_find:
            for key, _ in list_find.items():
                list_item_keyboard.append(key)
            list_item_keyboard.append('\U00002B05 Back')
            update_state(uid, item)
        elif isinstance(list_find, list):
            for v in list_find:
                list_item_inline.append(InlineKeyboardButton(
                    v['name'], callback_data=v['call']))
    else:
        for key, _ in cfg.items():
            list_item_keyboard.append(key)
    if list_item_keyboard:
        ver = ReplyKeyboardMarkup([list_item_keyboard], resize_keyboard=True)
        return ver.to_json()

    ver = InlineKeyboardMarkup([list_item_inline])
    return ver
