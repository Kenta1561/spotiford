from discord import Embed

from bot import utils


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
