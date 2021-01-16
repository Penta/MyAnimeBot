import pytest
import discord
import myanimebot.commands as commands
import myanimebot.globals as globals
from myanimebot.discord import MyAnimeBot
import discord.ext.test as dpytest


@pytest.fixture
def client(event_loop):
    ''' Create our mock client to be used for testing purposes '''

    intents = discord.Intents.default()
    intents.members = True

    c = MyAnimeBot(loop=event_loop, intents=intents)
    dpytest.configure(c)

    return c


@pytest.mark.asyncio
async def test_about_cmd(client):
    guild = client.guilds[0]
    channel = guild.text_channels[0]

    await commands.about_cmd(channel)

    embed = discord.Embed(title="***MyAnimeBot Commands***", colour=0xEED000)
    embed.title = "MyAnimeBot version {} by Penta & lulu".format(globals.VERSION)
    embed.colour = 0xEED000
    embed.description = """MyAnimeBot checks MyAnimeList and Anilist profiles for specified users, and send a message for every new activities found.
        More help with the **{} help** command.
        
        Check our GitHub page for more informations: https://github.com/Penta/MyAnimeBot
        """.format(globals.prefix)

    dpytest.verify_embed(embed=embed)

    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_help_cmd(client):
    guild = client.guilds[0]
    channel = guild.text_channels[0]

    await commands.help_cmd(channel)

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

    dpytest.verify_embed(embed=embed)

    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_ping_cmd(client):
    guild = client.guilds[0]
    channel = guild.text_channels[0]

    message = await channel.send("Test Message")
    await dpytest.empty_queue()

    await commands.ping_cmd(message, channel)
    dpytest.verify_message(text="pong", contains=True)

    await dpytest.empty_queue()
