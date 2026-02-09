#!/usr/bin/env python3
# Copyright Penta & lulu (c) 2018/2022 - Under BSD License - Based on feed2discord.py by Eric Eisenhart

# Compatible for Python 3.7.X

# Library import
import asyncio
import logging
import sys
import urllib.request
import signal
from configparser import ConfigParser
from datetime import datetime
from typing import List, Tuple

import discord.utils

discord.utils.setup_logging = lambda *args, **kwargs: None

import discord

import aiohttp
import feedparser
from aiohttp.web_exceptions import HTTPError, HTTPNotModified
from dateutil.parser import parse as parse_datetime
from html2text import HTML2Text

# Our modules
import myanimebot.anilist as anilist
import myanimebot.globals as globals
import myanimebot.utils as utils
import myanimebot.myanimelist as myanimelist
import myanimebot.commands as commands
from myanimebot.discord import send_embed_wrapper, build_embed, MyAnimeBot


if not sys.version_info[:2] >= (3, 14):
	print("ERROR: Requires python 3.14 or newer.")
	exit(1)


async def exit_app(signum=None):
	globals.logger.debug("Received signal {}".format(signum))
	globals.logger.info("Closing all tasks...")
	
	if globals.MAL_ENABLED:
		globals.task_feed.cancel()

	if globals.ANI_ENABLED:
		globals.task_feed_anilist.cancel()
	
	if globals.HEALTHCHECK_ENABLED:
		globals.task_healthcheck.cancel()

	globals.task_thumbnail.cancel()
	globals.task_gameplayed.cancel()

	await asyncio.sleep(3)

	# Closing all ressources
	try:
		globals.conn.close()
	except Exception:
		pass

	if globals.client:
		await globals.client.close()
	
	globals.logger.critical("Script halted.")

def handle_signal(signum, frame):
    loop = asyncio.get_event_loop()
    loop.create_task(exit_app(signum))

# Starting main function	
if __name__ == "__main__":
	
	# Catch SIGINT signal (Ctrl-C)
	signal.signal(signal.SIGINT, handle_signal)
	signal.signal(signal.SIGTERM, handle_signal)
	
	# Run the app
	try:
		globals.client = MyAnimeBot()
		globals.client.run(globals.token)
	except Exception as e:
		globals.logger.error("Encountered exception while running the bot: {}".format(e))
