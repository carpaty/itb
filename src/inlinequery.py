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
Module for handling inline queries in a Telegram bot.
"""

from uuid import uuid4

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update)
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from telegram.ext import ContextTypes

from utils import logger


async def inlinequery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # pylint: disable=unused-argument
    """
    Handle the inline query.

    :param update: The update object.
    :type update: telegram.Update
    :param context: The context object.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE
    """
    if update.inline_query is not None:
        query = update.inline_query.query
        logger.info("Inline query received: %s", query)
    else:
        logger.info("Missing query")
        query = ""

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Caps",
            input_message_content=InputTextMessageContent(query.upper())
        ),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Bold",
            input_message_content=InputTextMessageContent(
                f"*{escape_markdown(query)}*",
                parse_mode=ParseMode.MARKDOWN
            )
        ),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Italic",
            input_message_content=InputTextMessageContent(
                f"_{escape_markdown(query)}_",
                parse_mode=ParseMode.MARKDOWN
            )
        )
    ]

    if update.inline_query is not None:
        await update.inline_query.answer(results)
