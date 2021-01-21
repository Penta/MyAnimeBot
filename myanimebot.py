#!/usr/bin/env python3
# Copyright Penta & lulu (c) 2018/2021 - Under BSD License - Based on feed2discord.py by Eric Eisenhart

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

import aiohttp
import discord
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
from myanimebot.discord import send_embed_wrapper, build_embed, in_allowed_role, MyAnimeBot


if not sys.version_info[:2] >= (3, 7):
	print("ERROR: Requires python 3.7 or newer.")
	exit(1)


def exit_app(signum=None, frame=None):
	globals.logger.debug("Received signal {}".format(signum))
	globals.logger.info("Closing all tasks...")
	
	if globals.MAL_ENABLED:
		globals.task_feed.cancel()

	if globals.ANI_ENABLED:
		globals.task_feed_anilist.cancel()

	globals.task_thumbnail.cancel()
	globals.task_gameplayed.cancel()

	# Closing all ressources
	globals.conn.close()
	
	globals.logger.critical("Script halted.")

	exit(0)


# Starting main function	
if __name__ == "__main__":
	
	# Catch SIGINT signal (Ctrl-C)
	signal.signal(signal.SIGINT, exit_app)
	
	# Run the app
	try:
		globals.client = MyAnimeBot()
		globals.client.run(globals.token)
	except Exception as e:
		globals.logger.error("Encountered exception while running the bot: {}".format(e))

	exit_app()

