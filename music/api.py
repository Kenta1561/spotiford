import os

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

from cache.db_manager import DatabaseCacheHandler

# TODO Rework auth on unsuccessful auth, avoid stdout prompt

_cache_handler = DatabaseCacheHandler()
_auth_scopes = [
    "user-read-email",
    "streaming",
    "user-read-currently-playing",
    "user-library-read",
    "user-library-modify"
]
_oauth = SpotifyOAuth(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    redirect_uri="http://localhost:8080",
    scope=",".join(_auth_scopes),
    open_browser=False,
    cache_handler=_cache_handler
)

_client = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"]
))
_auth_client = Spotify(oauth_manager=_oauth)

def set_user(discord_id):
    """
    Set the current user of the cache handler to the provided discord user.

    Must run before each authenticated endpoint request.

    :param discord_id: Discord user id
    """

    _cache_handler.current_user = discord_id


# region Authentication

def authorize_user(discord_id, code):
    """
    Retrieve and cache the access token for the given user.

    Caching is handled automatically by spotipy by invoking get_access_token.

    :param discord_id: Discord user id
    :param code: Authorization code
    """

    _cache_handler.current_user = discord_id
    _oauth.get_access_token(code, as_dict=True)


# endregion

# region Information

def get_user():
    """
    Get the Spotify user for the given Discord user.

    Corresponds to endpoint '/me'.

    :param discord_id: Discord user id
    :return:
    """

    return _auth_client.current_user()


def get_tracks(query):
    """
    Get tracks based on a search query.

    Corresponds to endpoint '/search'.
    Does not require an authenticated client.

    :param query: Search query
    :return: List of matched tracks
    """

    return _client.search(query, type="track", limit=5)["tracks"]["items"]


def get_currently_playing():
    """
    Get the currently playing track.

    Corresponds to endpoint '/me/player'.

    :param discord_id: Discord user id
    :return: Currently playing track
    """

    return _auth_client.current_user_playing_track()["item"]


# endregion

# region Library

def is_saved(track):
    """
    Check whether the given track is saved in the user's library.

    Corresponds to endpoint '/me/tracks/contains'.

    :param discord_id: Discord user id
    :param track: Track to check
    :return: True, if track is saved
    """

    return _auth_client.current_user_saved_tracks_contains([track["uri"]])[0]


def save_track(track):
    """
    Save a track to the user's library.

    Corresponds to endpoint PUT '/me/tracks'.

    :param discord_id: Discord user id
    :param track: Track to save
    """

    _auth_client.current_user_saved_tracks_add([track["uri"]])


def remove_track(track):
    """
    Remove a track from the user's library.

    Corresponds to endpoint DELETE '/me/tracks'.

    :param discord_id: Discord user id
    :param track: Track to remove
    """

    _auth_client.current_user_saved_tracks_delete([track["uri"]])


# endregion

# region Queue

def queue(track):
    """
    Queue a track.

    Corresponds to POST '/me/player/queue'.

    :param discord_id: Discord user id
    :param track: Track to queue
    """

    _auth_client.add_to_queue(track["uri"])


# endregion

# region Playback

def play():
    """
    Start/resume the playback.

    Corresponds to endpoint PUT '/me/player/play'.

    :param discord_id: Discord user id
    """

    _auth_client.start_playback()


def play_track(track):
    """
    Play the provided track.
    :param track: Track to play
    """

    _auth_client.start_playback(uris=[track["uri"]])


def pause():
    """
    Pause the playback.

    Corresponds to endpoint PUT '/me/player/pause'.

    :param discord_id: Discord user id
    """

    _auth_client.pause_playback()


def next_track():
    """
    Skip to the next track.

    Corresponds to endpoint POST '/me/player/next'.

    :param discord_id: Discord user id
    """

    _auth_client.next_track()


def previous_track():
    """
    Skip to the previous track.

    Corresponds to endpoint POST '/me/player/previous'.

    :param discord_id: Discord user id
    """

    _auth_client.previous_track()


# endregion
