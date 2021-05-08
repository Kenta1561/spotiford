import asyncio
import os
from urllib.parse import urlparse, parse_qs

from discord.ext.commands.bot import Bot
from discord.embeds import Embed

from spotipy.oauth2 import SpotifyOauthError

import music
import utils

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
    except SpotifyOauthError:
        await context.send("Sorry, the authorization was unsuccessful. Please try again with `-login`.")


@bot.command()
async def account(context):
    current_user = music.get_current_user(context.author.id)
    await context.send(embed=create_user_embed(current_user))


@bot.command()
async def queue(context, *query):
    query_concat = " ".join(query)
    tracks = music.get_tracks(query_concat)
    embed = create_queueable_embed(query_concat, tracks)
    message = await context.send(embed=embed)

    for i in range(len(embed.fields)):
        await message.add_reaction(utils.number_emojis[i])

    # Add reactions for track selection
    def queue_reaction_check(reaction):
        return reaction.user_id == context.author.id and reaction.emoji.name in utils.number_emojis

    # Wait for user reaction
    try:
        reaction = await bot.wait_for("raw_reaction_add", check=queue_reaction_check, timeout=30.0)
        selected_track = tracks[utils.number_emojis.index(reaction.emoji.name)]
        await message.delete()
        music.queue(context.author.id, selected_track)
        await context.send(embed=create_track_embed(selected_track))
    except asyncio.TimeoutError:
        await message.delete()


def create_user_embed(response):
    embed = Embed(
        title=f"Welcome, {response['display_name']}!",
        description="Successfully connected to your Spotify account."
    )
    embed.set_thumbnail(url=response['images'][0]['url'])

    return embed


def create_queueable_embed(query, response):
    embed = Embed(title=f"Results for '{query}'")
    for index, track in enumerate(response):
        artists = utils.concat_track_artists(track)
        embed.add_field(
            name=f"#{index + 1} {artists} - {track['name']}",
            value=track["album"]["name"],
            inline=False
        )

    return embed


def create_track_embed(track):
    embed = Embed(title=track["name"], description=utils.concat_track_artists(track))
    embed.set_thumbnail(url=track["album"]["images"][0]["url"])

    return embed


bot.run(os.environ["DISCORD_BOT_TOKEN"])
