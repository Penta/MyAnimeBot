import discord
import pytz

import myanimebot.globals as globals # TODO Rename globals module
import myanimebot.utils as utils

def build_embed(user, item_title, item_link, item_description, pub_date, image, service: utils.Service):
	''' Build the embed message related to the anime's status '''

	# Get service
	if service == utils.Service.MAL:
		service_name = 'MyAnimeList'
		profile_url = "{}{}".format(globals.MAL_PROFILE_URL, user)
		icon_url = globals.MAL_ICON_URL
	elif service == utils.Service.ANILIST:
		service_name = 'AniList'
		profile_url = "{}{}".format(globals.ANILIST_PROFILE_URL, user)
		icon_url = globals.ANILIST_ICON_URL
	else:
		raise NotImplementedError('Unknown service {}'.format(service))
	description = "[{}]({})\n```{}```".format(utils.filter_name(item_title), item_link, item_description)
	profile_url_label = "{}'s {}".format(user, service_name)

	try:	
		embed = discord.Embed(colour=0xEED000, url=item_link, description=description, timestamp=pub_date.astimezone(pytz.timezone("utc")))
		embed.set_thumbnail(url=image)
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
