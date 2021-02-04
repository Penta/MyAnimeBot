import discord.ext.commands as discord_cmds


import myanimebot.utils as utils
import myanimebot.globals as globals
import myanimebot.commands.permissions as permissions


@discord_cmds.command(name="here")
@discord_cmds.check(permissions.in_allowed_role)
async def here_cmd(ctx):
    ''' Processes the command "here" and registers a channel to send new found feeds '''

    server = ctx.guild
    channel = ctx.channel
    
    if utils.is_server_in_db(server.id):
        # Server in DB, so we need to update the channel

        # Check if channel already registered
        channels = utils.get_channels(server.id)
        channels_id = [channel["channel"] for channel in channels]
        globals.logger.debug("Channels {} and channel id {}".format(channels_id, channel.id))
        if (str(channel.id) in channels_id):
            await ctx.send("Channel **{}** already in use for this server.".format(channel))
        else:
            cursor = globals.conn.cursor(buffered=True)
            cursor.execute("UPDATE t_servers SET channel = {} WHERE server = {}".format(channel.id, server.id))
            globals.conn.commit()
            cursor.close()
            
            await ctx.send("Channel updated to: **{}**.".format(channel))
    else:
        # No server found in DB, so register it
        cursor = globals.conn.cursor(buffered=True)
        cursor.execute("INSERT INTO t_servers (server, channel) VALUES ({},{})".format(server.id, channel.id))
        globals.conn.commit() # TODO Move to corresponding file
        
        await ctx.send("Channel **{}** configured for **{}**.".format(channel, server))
