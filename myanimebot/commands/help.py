import discord
import discord.ext.commands as discord_cmds


@discord_cmds.command(name="help")
async def help_cmd(ctx):
    ''' Responds to help command '''

    embed = discord.Embed(title="***MyAnimeBot Commands***", colour=0xEED000)
    embed.add_field(name="`here`", value="Register this channel. The bot will send new activities on registered channels.")
    embed.add_field(name="`stop`", value="Un-register this channel. The bot will now stop sending new activities for this channel.")
    embed.add_field(name="`info [mal|ani]`", value="Get the registered users for this server. Users can be filtered by specifying a service.")
    embed.add_field(name="`add {mal|ani} <user>`", value="Register a user for a specific service.\nEx: `add mal MyUser`")
    embed.add_field(name="`delete {mal|ani} <user>`", value="Remove a user for a specific service.\nEx: `delete ani MyUser`")
    embed.add_field(name="`role <@discord_role>`", value="Specify a role that is able to manage the bot.\nEx: `role @Moderator`, `role @everyone`")
    embed.add_field(name="`top`", value="Show statistics for this server.")
    embed.add_field(name="`ping`", value="Ping the bot.")
    embed.add_field(name="`about`", value="Get some information about this bot")
    await ctx.send(embed=embed)