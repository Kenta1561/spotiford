import asyncio
from urllib.parse import urlparse, parse_qs

from discord.ext import commands
from discord.ext.commands.bot import Bot
from spotipy.oauth2 import SpotifyOauthError

from bot import embeds, utils
from cache import db_manager
from music import api

bot = Bot(command_prefix="-")


# region Checks

@bot.check
async def disallow_guilds(context):
    if context.guild:
        await context.send(
            "For security reasons, spotiford should only be used via DM."
        )
        return False
    return True


def is_authenticated():
    async def predicate(context):
        if not db_manager.has_user(context.author.id):
            await context.send("For that, you have to be logged in.")
            return False
        return True
    return commands.check(predicate)

# endregion


@bot.command()
async def login(context):
    await context.send(
        f"Authorize with your Spotify client here: {api._oauth.get_authorize_url()}")


@bot.command()
async def connect(context, url):
    try:
        code = parse_qs(urlparse(url).query)["code"][0]
        api.authorize_user(context.author.id, code)
        current_user = api.get_current_user(context.author.id)
        await context.send(embed=embeds.create_user_embed(current_user))
    except KeyError:
        await context.send("Sorry, you provided an invalid response url.")
    except SpotifyOauthError:
        await context.send(
            "Sorry, the authorization was unsuccessful. Please try again with `-login`."
        )


@bot.command()
@is_authenticated()
async def account(context):
    current_user = api.get_current_user(context.author.id)
    await context.send(embed=embeds.create_user_embed(current_user))


@bot.command()
@is_authenticated()
async def now(context):
    track = api.get_currently_playing(context.author.id)
    await context.send(embed=embeds.create_track_embed(track))


@bot.command()
@is_authenticated()
async def queue(context, *query):
    query_concat = " ".join(query)
    tracks = api.get_tracks(query_concat)
    embed = embeds.create_queueable_embed(query_concat, tracks)
    message = await context.send(embed=embed)

    for i in range(len(embed.fields)):
        await message.add_reaction(utils.number_emojis[i])

    # Add reactions for track selection
    def queue_reaction_check(reaction):
        return reaction.user_id == context.author.id and reaction.emoji.name in utils.number_emojis

    # Wait for user reaction
    try:
        reaction = await bot.wait_for(
            "raw_reaction_add", check=queue_reaction_check, timeout=30.0
        )
        selected_track = tracks[utils.number_emojis.index(reaction.emoji.name)]
        await message.delete()
        api.queue(context.author.id, selected_track)
        await context.send(embed=embeds.create_track_embed(selected_track))
    except asyncio.TimeoutError:
        await message.delete()
