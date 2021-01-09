import discord
import pytz

import myanimebot.globals as globals # TODO Rename globals module
import myanimebot.utils as utils


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
	description = "[{}]({})\n```{}```".format(utils.filter_name(feed.media.name), feed.media.url, feed.description)
	profile_url_label = "{}'s {}".format(feed.user.name, service_name)

	try:	
		embed = discord.Embed(colour=0xEED000, url=feed.media.url, description=description, timestamp=feed.date_publication.astimezone(pytz.timezone("utc")))
		embed.set_thumbnail(url=feed.media.image)
		embed.set_author(name=profile_url_label, url=profile_url, icon_url=icon_url)
		embed.set_footer(text="MyAnimeBot", icon_url=globals.iconBot)
		
		return embed
	except Exception as e:
		globals.logger.error("Error when generating the message: " + str(e))
		return

# Function used to send the embed
async def send_embed_wrapper(asyncioloop, channelid, client, embed):
	channel = client.get_channel(int(channelid))
	
	try:
		await channel.send(embed=embed)
		globals.logger.info("Message sent in channel: " + channelid)
	except Exception as e:
		globals.logger.debug("Impossible to send a message on '" + channelid + "': " + str(e)) 
		return
