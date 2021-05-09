import os

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

from cache.db_manager import DatabaseCacheHandler

_cache_handler = DatabaseCacheHandler()
_oauth = SpotifyOAuth(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    redirect_uri="http://localhost:8080",
    scope="user-read-email,streaming,user-read-currently-playing",
    open_browser=False,
    cache_handler=_cache_handler
)

_client = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"]
))
_auth_client = Spotify(oauth_manager=_oauth)


# region Authentication

def authorize_user(discord_id, code):
    _cache_handler.current_user = discord_id
    _oauth.get_access_token(code, as_dict=True)


# endregion

# region API Endpoints

def get_current_user(discord_id):
    _cache_handler.current_user = discord_id
    return _auth_client.current_user()


def get_tracks(query):
    return _client.search(query, type="track", limit=5)["tracks"]["items"]


def get_currently_playing(discord_id):
    _cache_handler.current_user = discord_id
    return _auth_client.current_user_playing_track()["item"]


def queue(discord_id, track):
    _cache_handler.current_user = discord_id
    return _auth_client.add_to_queue(track["uri"])

# endregion
