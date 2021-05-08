import os
from urllib.parse import urlparse, parse_qs

from discord import Embed
from discord.ext.commands.bot import Bot

import music

bot = Bot(command_prefix="-")


@bot.command()
async def login(context):
    await context.send(f"Authorize with your Spotify client here: {music.oauth.get_authorize_url()}")


@bot.command()
async def connect(context, url):
    try:
        code = parse_qs(urlparse(url).query)["code"][0]
        music.authorize_user(context.author.id, code)
        current_user = music.get_current_user(context.author.id)
        await context.send(embed=create_user_embed(current_user))
    except KeyError:
        await context.send("Sorry, you provided an invalid response url.")


@bot.command()
async def queue(context, *query):
    query_concat = " ".join(query)
    await context.send(embed=create_queueable_embed(query_concat, music.get_tracks(query_concat)))


def create_user_embed(response):
    embed = Embed(
        title=f"Welcome, {response['display_name']}!",
        description="Successfully connected to your Spotify account."
    )
    embed.set_thumbnail(url=response['images'][0]['url'])

    return embed


def create_queueable_embed(query, response):
    embed = Embed(title=f"Results for '{query}'")
    for index, track in enumerate(response["tracks"]["items"]):
        artists = ', '.join([artist["name"] for artist in track["artists"]])
        embed.add_field(
            name=f"#{index + 1} {artists} - {track['name']}",
            value=track["album"]["name"],
            inline=False
        )

    return embed


bot.run(os.environ["DISCORD_BOT_TOKEN"])
