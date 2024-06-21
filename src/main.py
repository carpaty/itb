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
Main Module
"""

import os
from contextlib import asynccontextmanager
from pydantic import BaseModel
import backoff
import telegram
from fastapi import FastAPI, Request
from starlette.responses import Response, PlainTextResponse
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    InlineQueryHandler,
    CallbackQueryHandler,
    filters,
    MessageHandler,
)

import utils
import inlinequery
import commands

from calls.button_func import button, button_int, worker

TELEGRAM_WEBHOOK_URL = os.environ.get('TELEGRAM_WEBHOOK_URL')


@backoff.on_exception(backoff.expo, telegram.error.RetryAfter, max_time=60)
async def set_webhook():
    """
    Set the webhook for the Telegram bot.

    This function sets the webhook for the Telegram bot using the URL specified
    in the environment variable `TELEGRAM_WEBHOOK_URL`.

    :raises: `telegram.error.RetryAfter`
    """
    if TELEGRAM_WEBHOOK_URL != "None":
        utils.logger.info(
            "Setting webhook by URL %s/webhook...", TELEGRAM_WEBHOOK_URL)
        await app_.bot.set_webhook(url=f"{TELEGRAM_WEBHOOK_URL}/webhook")
        utils.logger.info("Webhook set!")
    else:
        utils.logger.info("Webhook URL is None, skipping...")


@asynccontextmanager
async def lifespan(apps: FastAPI):  # pylint: disable=unused-argument
    """
    Manage the lifespan of the FastAPI application.

    This function manages the startup and shutdown sequences of the FastAPI application.

    :param apps: The FastAPI application instance.
    :type apps: FastAPI
    """
    await set_webhook()
    await app_.initialize()
    await app_.start()
    webhook_info = await app_.bot.get_webhook_info()
    utils.logger.info("Webhook info: %s", webhook_info)
    yield
    utils.logger.info("Stopping the application")
    if isinstance(app_, Application):
        await app_.stop()
        await app_.shutdown()


app_ = Application.builder().token(utils.KEY).build()
app_.add_handler(CommandHandler("start", commands.start))
app_.add_handler(CommandHandler("help", commands.help_command))
app_.add_handler(InlineQueryHandler(inlinequery.inlinequery))
app_.add_handler(MessageHandler(filters.Regex(
    utils.EMOJI_PATTERN), commands.keyboard))
app_.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND, commands.echocall))
app_.add_error_handler(commands.error_handler)

# This is your custom calls located in calls directory
# file name is button_func.py
app_.add_handler(CallbackQueryHandler(button, pattern=utils.call_pattern()))
app_.add_handler(CallbackQueryHandler(button_int, pattern="^inftrx"))

app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def telegram_webhook(request: Request) -> Response:
    """
    Handle incoming Telegram updates by putting them into the `update_queue`.

    :param request: The incoming request containing the Telegram update.
    :type request: Request
    :return: An empty response.
    :rtype: Response
    """
    await app_.update_queue.put(
        Update.de_json(data=await request.json(), bot=app_.bot)
    )
    return Response()


@app.get("/healthcheck")
async def health(_: Request) -> PlainTextResponse:
    """
    Health check endpoint.

    For the health endpoint, reply with a simple plain text message indicating
    the bot is running fine.

    :param _: The incoming request (ignored).
    :type _: Request
    :return: A plain text response.
    :rtype: PlainTextResponse
    """
    return PlainTextResponse(content="The bot is still running fine :)")


@app.get('/')
async def root(_: Request) -> PlainTextResponse:
    """
    Root page endpoint.

    :param _: The incoming request (ignored).
    :type _: Request
    :return: A plain text response.
    :rtype: PlainTextResponse
    """
    return PlainTextResponse(content="ITB")


class Items(BaseModel):
    """
    Data model for items in POST requests.

    :param hash: The hash identifier.
    :type hash: str
    :param text: The optional text message.
    :type text: str | None
    """
    hash: str
    text: str | None = None


@app.post('/tg')
async def tg_post(items: Items):
    """
    Send messages via the Telegram bot.

    :param items: The JSON items containing the hash and text.
    :type items: Items
    :return: A message indicating the result.
    :rtype: dict
    """
    post_hash = items.hash
    post_text = items.text
    await utils.post_tg(utils.getuidbyhash(post_hash), post_text)
    return {'message': "message sent"}


@app.get('/tg')
async def tg_get():
    """
    GET route for instructions on how to use the POST route.

    :return: Instructions for using the POST route.
    :rtype: dict
    """
    return {'message': f'''ERROR, please use POST request
        curl {os.environ.get('TELEGRAM_WEBHOOK_URL')}/tg \
             -H "Content-Type: application/json" -d '{{"hash":"XXX","text":"Alert!!"}}'
        '''}


@app.get('/cron')
async def cron():
    """
    Cron route for triggering periodic tasks.

    :return: A message indicating the result.
    :rtype: dict
    """
    await worker()
    return {'message': "message sent"}


if __name__ == '__main__':
    utils.logger.info("Bot started: v%s", utils.VERSION)
