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
    """
    Global check function to verify that the command was invoked in a DM channel.

    To avoid security risks by exposing Oauth access tokens to third parties,
    all requests from guilds are rejected and a warning is sent.

    :param context: Invocation context
    :return: True, if command was invoked in a DM channel
    """

    if context.guild:
        await context.send(
            "For security reasons, spotiford should only be used via DM."
        )
        return False
    return True


def is_authenticated():
    """
    Check if the user is already authenticated with Spotify.

    :return: True, if authenticated
    """

    async def predicate(context):
        if not db_manager.has_user(context.author.id):
            await context.send("For that, you have to be logged in.")
            return False
        return True

    return commands.check(predicate)


# endregion


@bot.command()
async def login(context):
    """
    Send an Oauth authorization url.

    :param context: Invocation context
    """

    await context.send(
        f"Authorize with your Spotify client here: {api._oauth.get_authorize_url()}")


@bot.command()
async def connect(context, url):
    """
    Establish a connection to the Spotify API.

    Upon successful connection, a greeting with the user profile is displayed.

    :param context: Invocation context
    :param url: Authorization url from redirected page with code
    """
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
    """
    Send the Spotify profile of the user.

    :param context: Invocation context
    """

    current_user = api.get_current_user(context.author.id)
    await context.send(embed=embeds.create_user_embed(current_user))


@bot.command()
@is_authenticated()
async def now(context):
    """
    Display the currently playing track.

    :param context: Invocation context
    """

    track = api.get_currently_playing(context.author.id)
    await context.send(embed=embeds.create_track_embed(track))


@bot.command()
@is_authenticated()
async def queue(context, *query):
    """
    Search for a song and add it to the playback queue.

    Upon request, up to five tracks matching the provided query are displayed.
    The user can selected a track to be queued by reacting with one of the key cap
    emojis from 1 through 5.

    :param context: Invocation context
    :param query: Search query
    """

    query_concat = " ".join(query)
    tracks = api.get_tracks(query_concat)
    embed = embeds.create_tracks_embed(query_concat, tracks)
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
