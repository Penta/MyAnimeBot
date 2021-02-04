import discord
import discord.ext.commands as discord_cmds

import myanimebot.globals as globals


@discord_cmds.command(name="about")
async def about_cmd(ctx):
    ''' Responds to about command with a brief description of this bot '''

    embed = discord.Embed(title="***MyAnimeBot Commands***", colour=0xEED000)
    embed.title = "MyAnimeBot version {} by Penta & lulu".format(globals.VERSION)
    embed.colour = 0xEED000
    embed.description = """MyAnimeBot checks MyAnimeList and Anilist profiles for specified users, and send a message for every new activities found.
        More help with the **{} help** command.
        
        Check our GitHub page for more informations: https://github.com/Penta/MyAnimeBot
        """.format(globals.prefix)
    embed.set_thumbnail(url=globals.iconBot)

    await ctx.send(embed=embed)