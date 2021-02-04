import datetime

import discord.ext.commands as discord_cmds


@discord_cmds.command(name="ping")
async def ping_cmd(ctx):
    ''' Responds to ping command '''
    messageTimestamp = ctx.message.created_at
    currentTimestamp = datetime.datetime.utcnow()
    delta = round((currentTimestamp - messageTimestamp).total_seconds() * 1000)

    print("Sending pong")
    await ctx.reply("pong ({}ms)".format(delta))
