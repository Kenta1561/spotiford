from discord import Embed

from bot import utils


def create_user_embed(response):
    """
    Create a Spotify user profile embed.

    :param response: Response from /me endpoint
    :return: Embed
    """

    embed = Embed(
        title=f"Welcome, {response['display_name']}!",
        description="Successfully connected to your Spotify account."
    )
    embed.set_thumbnail(url=response['images'][0]['url'])

    return embed


def create_tracks_embed(query, response):
    """
    Create an embed with a list of tracks.

    :param query: Search query
    :param response: Response containing list of tracks
    :return: Embed
    """

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
    """
    Create an embed with information about a single track.

    :param track: Track to display
    :return: Embed
    """

    embed = Embed(title=track["name"], description=utils.concat_track_artists(track))
    embed.set_thumbnail(url=track["album"]["images"][0]["url"])

    return embed
