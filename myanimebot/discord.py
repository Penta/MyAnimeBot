import asyncio
import urllib.request
from configparser import ConfigParser
from datetime import datetime
from typing import List, Tuple

import aiohttp
import feedparser
import pytz
from dateutil.parser import parse as parse_datetime

import discord


# Our modules
import myanimebot.anilist as anilist
import myanimebot.commands as commands
import myanimebot.globals as globals  # TODO Rename globals module
import myanimebot.myanimelist as myanimelist
import myanimebot.utils as utils


class MyAnimeBot(discord.Client):
    async def on_ready(self):
        globals.logger.info("Logged in as " + globals.client.user.name + " (" + str(globals.client.user.id) + ")")

        globals.logger.info("Starting all tasks...")

        if globals.MAL_ENABLED:
            globals.task_feed = globals.client.loop.create_task(background_check_feed(globals.client.loop))

        if globals.ANI_ENABLED:
            globals.task_feed_anilist = globals.client.loop.create_task(anilist.background_check_feed(globals.client.loop))

        globals.task_thumbnail = globals.client.loop.create_task(update_thumbnail_catalog(globals.client.loop))
        globals.task_gameplayed = globals.client.loop.create_task(change_gameplayed(globals.client.loop))

    async def on_error(self, event, *args, **kwargs):
        globals.logger.exception("Crap! An unknown Discord error occured...")

    async def on_message(self, message):
        if message.author == globals.client.user: return

        words = message.content.strip().split()
        channel = message.channel
        author = str('{0.author.mention}'.format(message))

        # Check input validity
        if len(words) == 0:
            return

        # A user is trying to get help
        if words[0] == globals.prefix:
            if len(words) > 1:
                if words[1] == "ping":
                    await commands.ping_cmd(message, channel)
                
                elif words[1] == "here":
                    await commands.here_cmd(message.author, message.guild, channel)
                    
                elif words[1] == "add":
                    await commands.add_user_cmd(words, message)
                    
                elif words[1] == "delete":
                    await commands.delete_user_cmd(words, message)
                    
                elif words[1] == "stop":
                    if in_allowed_role(message.author, message.guild):
                        if (len(words) == 2):
                            cursor = globals.conn.cursor(buffered=True)
                            cursor.execute("SELECT server FROM t_servers WHERE server=%s", [str(message.guild.id)])
                            data = cursor.fetchone()
                        
                            if data is None: await message.channel.send("The server **" + str(message.guild) + "** is not in our database.")
                            else:
                                cursor.execute("DELETE FROM t_servers WHERE server = %s", [message.guild.id])
                                globals.conn.commit()
                                await message.channel.send("Server **" + str(message.guild) + "** deleted from our database.")
                            
                            cursor.close()
                        else: await message.channel.send("Too many arguments! Only type *stop* if you want to stop this bot on **" + message.guild + "**")
                    else: await message.channel.send("Only allowed users can use this command!")
                    
                elif words[1] == "info":
                    await commands.info_cmd(message, words)

                elif words[1] == "about":
                    await commands.about_cmd(channel)
                
                elif words[1] == "help":
                    await commands.help_cmd(channel)
                
                elif words[1] == "top":
                    if len(words) == 2:
                        try:
                            cursor = globals.conn.cursor(buffered=True)
                            cursor.execute("SELECT * FROM v_Top")
                            data = cursor.fetchone()
                            
                            if data is None: await message.channel.send("It seems that there is no statistics... (what happened?!)")
                            else:
                                topText = "**__Here is the global statistics of this bot:__**\n\n"
                                
                                while data is not None:
                                    topText += " - " + str(data[0]) + ": " + str(data[1]) + "\n"
                                        
                                    data = cursor.fetchone()
                                    
                                cursor = globals.conn.cursor(buffered=True)
                                cursor.execute("SELECT * FROM v_TotalFeeds")
                                data = cursor.fetchone()
                                
                                topText += "\n***Total user entry***: " + str(data[0])
                                
                                cursor = globals.conn.cursor(buffered=True)
                                cursor.execute("SELECT * FROM v_TotalAnimes")
                                data = cursor.fetchone()
                                
                                topText += "\n***Total unique manga/anime***: " + str(data[0])
                                
                                await message.channel.send(topText)
                            
                            cursor.close()
                        except Exception as e:
                            globals.logger.warning("An error occured while displaying the global top: " + str(e))
                            await message.channel.send("Unable to reply to your request at the moment...")
                    elif len(words) > 2:
                        keyword = str(' '.join(words[2:]))
                        globals.logger.info("Displaying the global top for the keyword: " + keyword)
                        
                        try:
                            cursor = globals.conn.cursor(buffered=True)
                            cursor.callproc('sp_UsersPerKeyword', [str(keyword), '20'])
                            for result in cursor.stored_results():
                                data = result.fetchone()
                                
                                if data is None: await message.channel.send("It seems that there is no statistics for the keyword **" + keyword + "**.")
                                else:
                                    topKeyText = "**__Here is the statistics for the keyword " + keyword + ":__**\n\n"
                                    
                                    while data is not None:
                                        topKeyText += " - " + str(data[0]) + ": " + str(data[1]) + "\n"
                                            
                                        data = result.fetchone()
                                        
                                    await message.channel.send(topKeyText)
                                
                            cursor.close()
                        except Exception as e:
                            globals.logger.warning("An error occured while displaying the global top for keyword '" + keyword + "': " + str(e))
                            await message.channel.send("Unable to reply to your request at the moment...")
                
                elif words[1] == "role":
                    if len(words) > 2:
                        if message.author.guild_permissions.administrator:
                            cursor = globals.conn.cursor(buffered=True)

                            if (words[2] == "everyone") | (words[2] == "@everyone"):
                                cursor.execute("UPDATE t_servers SET admin_group = NULL WHERE server = %s", [str(message.guild.id)])
                                globals.conn.commit()

                                await message.channel.send("Everybody is now allowed to use the bot!")
                            else:
                                rolesFound = message.role_mentions

                                if (len(rolesFound) > 1): await message.channel.send("Please specify only 1 group!")
                                elif (len(rolesFound) == 0): await message.channel.send("Please specify a correct group.")
                                else: 
                                    cursor.execute("UPDATE t_servers SET admin_group = %s WHERE server = %s", [str(rolesFound[0].id), str(message.guild.id)])
                                    globals.conn.commit()

                                    await message.channel.send("The role **" + str(rolesFound[0].name) + "** is now allowed to use this bot!")

                            cursor.close()
                        else: await message.channel.send("Only server's admins can use this command!")
                    else:
                        await message.channel.send("You have to specify a role!")

        # If mentioned
        elif globals.client.user in message.mentions:
            await channel.send(":heart:")


def build_embed(feed : utils.Feed):
    ''' Build the embed message related to the anime's status '''

    # Get service
    if feed.service == utils.Service.MAL:
        service_name = 'MyAnimeList'
        profile_url = "{}{}".format(globals.MAL_PROFILE_URL, feed.user.name)
        icon_url = globals.MAL_ICON_URL
    elif feed.service == utils.Service.ANILIST:
        service_name = 'AniList'
        profile_url = "{}{}".format(globals.ANILIST_PROFILE_URL, feed.user.name)
        icon_url = globals.ANILIST_ICON_URL
    else:
        raise NotImplementedError('Unknown service {}'.format(feed.service))
    description = utils.build_description_string(feed)
    content = "[{}]({})\n```{}```".format(utils.filter_name(feed.media.name), feed.media.url, description)
    profile_url_label = "{}'s {}".format(feed.user.name, service_name)

    try:
        embed = discord.Embed(colour=int(feed.status.value, 16), url=feed.media.url, description=content, timestamp=feed.date_publication.astimezone(pytz.timezone("utc")))
        embed.set_thumbnail(url=feed.media.image)
        embed.set_author(name=profile_url_label, url=profile_url, icon_url=icon_url)
        embed.set_footer(text="MyAnimeBot", icon_url=globals.iconBot)

        return embed
    except Exception as e:
        globals.logger.error("Error when generating the message: " + str(e))
        return


async def send_embed_wrapper(asyncioloop, channelid, client, embed):
    ''' Send an embed message to a channel '''

    channel = client.get_channel(int(channelid))

    try:
        await channel.send(embed=embed)
        globals.logger.info("Message sent in channel: {}".format(channelid))
    except Exception as e:
        globals.logger.debug("Impossible to send a message on '{}': {}".format(channelid, e)) 
        return

    # Main function that check the RSS feeds from MyAnimeList
async def background_check_feed(asyncioloop):
    globals.logger.info("Starting up background_check_feed")
    
    # We configure the http header
    http_headers = { "User-Agent": "MyAnimeBot Discord Bot v" + globals.VERSION, }
    timeout = aiohttp.ClientTimeout(total=5)
    
    await globals.client.wait_until_ready()
    
    globals.logger.debug("Discord client connected, unlocking background_check_feed...")
    
    while not globals.client.is_closed():
        try:
            db_user = globals.conn.cursor(buffered=True, dictionary=True)
            db_user.execute("SELECT mal_user, servers FROM t_users WHERE service=%s", [globals.SERVICE_MAL])
            data_user = db_user.fetchone()
        except Exception as e:
            globals.logger.critical("Database unavailable! (" + str(e) + ")")
            quit()

        while data_user is not None:
            user = utils.User(id=None,
                                service_id=None,
                                name=data_user[globals.DB_USER_NAME],
                                servers=data_user["servers"].split(','))
            stop_boucle = 0
            feed_type = 1

            try:
                while stop_boucle == 0 :
                    try:
                        async with aiohttp.ClientSession() as httpclient:
                            if feed_type == 1 :
                                http_response = await httpclient.request("GET", "https://myanimelist.net/rss.php?type=rm&u=" + user.name, headers=http_headers, timeout=timeout)
                                media = "manga"
                            else : 
                                http_response = await httpclient.request("GET", "https://myanimelist.net/rss.php?type=rw&u=" + user.name, headers=http_headers, timeout=timeout)
                                media = "anime"
                        http_data = await http_response.read()
                    except asyncio.TimeoutError:
                        globals.logger.error("Error while loading RSS of '{}': Timeout".format(user.name))
                        break
                    except Exception as e:
                        globals.logger.exception("Error while loading RSS ({}) of '{}':\n".format(feed_type, user.name))
                        break

                    feeds_data = feedparser.parse(http_data)
                    
                    for feed_data in feeds_data.entries:
                        pubDateRaw = datetime.strptime(feed_data.published, '%a, %d %b %Y %H:%M:%S %z').astimezone(globals.timezone)
                        pubDate = pubDateRaw.strftime("%Y-%m-%d %H:%M:%S")
                        if feed_type == 1:
                            media_type = utils.MediaType.MANGA
                        else:
                            media_type = utils.MediaType.ANIME

                        feed = myanimelist.build_feed_from_data(feed_data, user, None, pubDateRaw.timestamp(), media_type)
                        
                        cursor = globals.conn.cursor(buffered=True)
                        cursor.execute("SELECT published, title, url, type FROM t_feeds WHERE published=%s AND title=%s AND user=%s AND type=%s AND obsolete=0 AND service=%s", [pubDate, feed.media.name, user.name, feed.get_status_str(), globals.SERVICE_MAL])
                        data = cursor.fetchone()

                        if data is None:
                            var = datetime.now(globals.timezone) - pubDateRaw
                            
                            globals.logger.debug(" - " + feed.media.name + ": " + str(var.total_seconds()))
                        
                            if var.total_seconds() < globals.secondMax:
                                globals.logger.info(user.name + ": Item '" + feed.media.name + "' not seen, processing...")
                                
                                cursor.execute("SELECT thumbnail FROM t_animes WHERE guid=%s AND service=%s LIMIT 1", [feed.media.url, globals.SERVICE_MAL]) # TODO Change that ?
                                data_img = cursor.fetchone()
                                
                                if data_img is None:
                                    try:
                                        image = myanimelist.get_thumbnail(feed.media.url)
                                        
                                        globals.logger.info("First time seeing this " + media + ", adding thumbnail into database: " + image)
                                    except Exception as e:
                                        globals.logger.warning("Error while getting the thumbnail: " + str(e))
                                        image = ""
                                        
                                    cursor.execute("INSERT INTO t_animes (guid, service, title, thumbnail, found, discoverer, media) VALUES (%s, %s, %s, %s, NOW(), %s, %s)", [feed.media.url, globals.SERVICE_MAL, feed.media.name, image, user.name, media])
                                    globals.conn.commit()
                                else: image = data_img[0]
                                feed.media.image = image

                                cursor.execute("UPDATE t_feeds SET obsolete=1 WHERE published=%s AND title=%s AND user=%s AND service=%s", [pubDate, feed.media.name, user.name, globals.SERVICE_MAL])
                                cursor.execute("INSERT INTO t_feeds (published, title, service, url, user, found, type) VALUES (%s, %s, %s, %s, %s, NOW(), %s)", (pubDate, feed.media.name, globals.SERVICE_MAL, feed.media.url, user.name, feed.get_status_str()))
                                globals.conn.commit()
                                
                                for server in user.servers:
                                    db_srv = globals.conn.cursor(buffered=True)
                                    db_srv.execute("SELECT channel FROM t_servers WHERE server = %s", [server])
                                    data_channel = db_srv.fetchone()
                                    
                                    while data_channel is not None:
                                        for channel in data_channel: await send_embed_wrapper(asyncioloop, channel, globals.client, build_embed(feed))
                                        
                                        data_channel = db_srv.fetchone()
                    if feed_type == 1:
                        feed_type = 0
                        await asyncio.sleep(globals.MYANIMELIST_SECONDS_BETWEEN_REQUESTS)
                    else:
                        stop_boucle = 1
                    
            except Exception as e:
                globals.logger.exception("Error when parsing RSS for '{}':\n".format(user.name))
            
            await asyncio.sleep(globals.MYANIMELIST_SECONDS_BETWEEN_REQUESTS)

            data_user = db_user.fetchone()


async def fetch_activities_anilist():
    await anilist.check_new_activities()


# Get a random anime name and change the bot's activity
async def change_gameplayed(asyncioloop):
    globals.logger.info("Starting up change_gameplayed")
    
    await globals.client.wait_until_ready()
    await asyncio.sleep(1)

    while not globals.client.is_closed():
        # Get a random anime name from the users' list
        cursor = globals.conn.cursor(buffered=True)
        cursor.execute("SELECT title FROM t_animes ORDER BY RAND() LIMIT 1")
        data = cursor.fetchone()
        anime = utils.truncate_end_show(data[0])
        
        # Try to change the bot's activity
        try:
            if data is not None: await globals.client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=anime))
        except Exception as e:
            globals.logger.warning("An error occured while changing the displayed anime title: " + str(e))
            
        cursor.close()
        # Do it every minute
        await asyncio.sleep(60)

async def update_thumbnail_catalog(asyncioloop):
    globals.logger.info("Starting up update_thumbnail_catalog")
    
    while not globals.client.is_closed():
        await asyncio.sleep(43200)
        
        globals.logger.info("Automatic check of the thumbnail database on going...")
        reload = 0
        
        cursor = globals.conn.cursor(buffered=True)
        cursor.execute("SELECT guid, title, thumbnail FROM t_animes")
        data = cursor.fetchone()

        while data is not None:
            try:
                if (data[2] != "") : urllib.request.urlopen(data[2])
                else: reload = 1
            except urllib.error.HTTPError as e:
                globals.logger.warning("HTTP Error while getting the current thumbnail of '" + str(data[1]) + "': " + str(e))
                reload = 1
            except Exception as e:
                globals.logger.debug("Error while getting the current thumbnail of '" + str(data[1]) + "': " + str(e))
            
            if (reload == 1) :
                try:
                    image = myanimelist.get_thumbnail(data[0])
                        
                    cursor.execute("UPDATE t_animes SET thumbnail = %s WHERE guid = %s", [image, data[0]])
                    globals.conn.commit()
                        
                    globals.logger.info("Updated thumbnail found for \"" + str(data[1]) + "\": %s", image)
                except Exception as e:
                    globals.logger.warning("Error while downloading updated thumbnail for '" + str(data[1]) + "': " + str(e))

            await asyncio.sleep(3)
            data = cursor.fetchone()

        cursor.close()

        globals.logger.info("Thumbnail database checked.")
