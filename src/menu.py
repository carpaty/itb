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
    BACK_BUTTON,
    find_key,
    find,
    cfg,
    update_state,
    check_state)

ROW_SIZE = 2


def _rows(buttons, size=ROW_SIZE):
    return [buttons[i:i + size] for i in range(0, len(buttons), size)]


def gen_menu(uid, item=""):
    """
    Generate a menu for the user.

    This function generates a menu based on the user's current state and the provided item.
    It returns either a ReplyKeyboardMarkup or InlineKeyboardMarkup object, depending on the
    structure of the menu configuration. Unknown items fall back to the main menu.

    :param uid: User ID
    :type uid: int
    :param item: Name of the button, defaults to ""
    :type item: str, optional
    :return: Keyboard markup
    :rtype: telegram.ReplyKeyboardMarkup | telegram.InlineKeyboardMarkup
    """
    uid = str(uid)
    if item == BACK_BUTTON:
        cur_stat = check_state(uid) or {}
        parents = list(find_key(cfg, cur_stat.get('current')))
        return gen_menu(uid, parents[0] if parents and parents[0] else "")

    list_find = next(find(item, cfg), None) if item else cfg
    if isinstance(list_find, list) and list_find:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(v['name'], callback_data=v['call'])] for v in list_find])
    if not isinstance(list_find, dict) or not list_find:
        return gen_menu(uid, "") if item else ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True)

    list_item_keyboard = list(list_find)
    if item:
        list_item_keyboard.append(BACK_BUTTON)
        update_state(uid, item)
    return ReplyKeyboardMarkup(_rows(list_item_keyboard), resize_keyboard=True)
