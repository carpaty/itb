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
Command handlers for the Telegram bot.
"""

from telegram import Update
from telegram.ext import ContextTypes
import menu
import utils
from calls import button_func


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # pylint: disable=unused-argument
    """
    Handle the /start command.

    :param update: The update object.
    :type update: telegram.Update
    :param context: The context object.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE
    """
    if update.message and update.message.from_user:
        user_id = update.message.from_user.id
        utils.logger.info("User /start: %s", user_id)
        check_exist = utils.user_check(user_id)

        if check_exist:
            await update.message.reply_text(text='Welcome back')
        else:
            utils.user_insert(user_id)
            await update.message.reply_text(text='Welcome', disable_web_page_preview=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # pylint: disable=unused-argument
    """
    Handle the /help command.

    :param update: The update object.
    :type update: telegram.Update
    :param context: The context object.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE
    """
    if update.message and update.message.from_user:
        user_id = update.message.from_user.id
        utils.logger.info("User /help: %s", user_id)
        kbd = menu.gen_menu(user_id)
        await update.message.reply_text(text="Select option", reply_markup=kbd, disable_web_page_preview=True)


async def keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # pylint: disable=unused-argument
    """
    Handle keyboard interactions.

    :param update: The update object.
    :type update: telegram.Update
    :param context: The context object.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE
    """
    if update.message and update.message.from_user and update.message.text:
        user_id = update.message.from_user.id
        key_pressed = update.message.text
        utils.logger.info("User: %s pressed key: %s", user_id, key_pressed)
        res = menu.gen_menu(user_id, key_pressed)
        await update.message.reply_text(text="Select option", reply_markup=res, disable_web_page_preview=True)


async def echocall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # pylint: disable=unused-argument
    """
    Handle echo calls triggered when a user presses a button.

    :param update: The update object.
    :type update: telegram.Update
    :param context: The context object.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE
    """
    if update.message and update.message.from_user and update.message.text:
        user_id = update.message.from_user.id
        message_text = update.message.text
        utils.logger.info("User: %s typed: %s", user_id, message_text)
        method_name = utils.check_button(user_id)
        method_to_call = getattr(button_func, method_name['current'])
        text, ver = method_to_call(message_text)
        await update.message.reply_text(text=text, reply_markup=ver, disable_web_page_preview=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Log errors and send a message to the user.

    :param update: The update object.
    :type update: object
    :param context: The context object.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE
    """
    utils.logger.error(
        msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text('An error occurred. Please try again later.')
    else:
        utils.logger.error("Update is not a message: %s", update)
