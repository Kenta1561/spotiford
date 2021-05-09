import asyncio
from functools import partial
from urllib.parse import urlparse, parse_qs

from discord.ext import commands
from discord.ext.commands.bot import Bot
from spotipy import SpotifyException
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

def reaction_check(discord_id, allowed_emojis, reaction):
    """
    Event check predicate to validate a raw_reaction_add event.

    Check whether the reaction is made by the original user that invoked the command
    and whether the reaction emoji is in a list of valid emojis.

    :param discord_id: Discord user id
    :param allowed_emojis: List of valid emojis
    :param reaction: Reaction object
    :return: True, if event is valid
    """

    return reaction.user_id == discord_id and reaction.emoji.name in allowed_emojis


# region Auth

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


# endregion

# region Information

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

    If the track is saved by the user, reacting with a broken heart
    emoji removes the track from the library.

    If the track is not saved by the user, reacting with a heart emoji saves the track
    to the library.

    :param context: Invocation context
    """

    discord_id = context.author.id
    track = api.get_currently_playing(context.author.id)
    message = await context.send(embed=embeds.create_track_embed(track))

    if api.is_saved(discord_id, track):
        await message.add_reaction(utils.broken_heart_emoji)
        await handle_dislike(context, message, discord_id, track)
    else:
        await message.add_reaction(utils.heart_emoji)
        await handle_like(context, message, discord_id, track)


async def handle_dislike(context, message, discord_id, track):
    """
    Wait for the user to react with a broken heart emoji to a track embed.
    Remove the song from the user's library.

    :param context: Invocation context
    :param message: Track embed message
    :param discord_id: Discord user id
    :param track: Track
    """

    try:
        await bot.wait_for(
            "raw_reaction_add",
            check=partial(reaction_check, discord_id, utils.broken_heart_emoji),
            timeout=30.0
        )
        api.remove_track(discord_id, track)
        await message.delete()
        await context.send(f"Removed {track['name']} from your library.")
    except asyncio.TimeoutError:
        pass


async def handle_like(context, message, discord_id, track):
    """
    Wait for the user to react with a heart emoji to a track embed.
    Add the song to the user's library.

    :param context:
    :param message:
    :param discord_id:
    :param track:
    :return:
    """

    try:
        await bot.wait_for(
            "raw_reaction_add",
            check=partial(reaction_check, discord_id, utils.heart_emoji),
            timeout=30.0
        )
        api.save_track(discord_id, track)
        await message.delete()
        await context.send(f"Saved {track['name']} to your library.")
    except asyncio.TimeoutError:
        pass


# region Playback

@bot.command()
@is_authenticated()
async def play(context):
    """
    Start/resume the playback.

    Ignore the exception raised when trying to invoke this command while a track
    is already playing.

    :param context: Invocation context
    """

    try:
        api.play(context.author.id)
    except SpotifyException:
        pass


@bot.command()
@is_authenticated()
async def pause(context):
    """
    Pause the playback.

    Ignore the exception raised when trying to invoke this command while the playback
    is already paused.

    :param context: Invocation context
    """

    try:
        api.pause(context.author.id)
    except SpotifyException:
        pass


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

    discord_id = context.author.id
    query_concat = " ".join(query)
    tracks = api.get_tracks(query_concat)
    embed = embeds.create_tracks_embed(query_concat, tracks)
    message = await context.send(embed=embed)

    for i in range(len(embed.fields)):
        await message.add_reaction(utils.number_emojis[i])

    # Wait for user reaction
    try:
        reaction = await bot.wait_for(
            "raw_reaction_add",
            check=partial(reaction_check, discord_id, utils.number_emojis),
            timeout=30.0
        )
        selected_track = tracks[utils.number_emojis.index(reaction.emoji.name)]
        await message.delete()
        api.queue(context.author.id, selected_track)
        await context.send(embed=embeds.create_track_embed(selected_track))
    except asyncio.TimeoutError:
        await message.delete()

# endregion
