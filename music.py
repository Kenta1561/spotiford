import os

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

oauth = SpotifyOAuth(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    redirect_uri="http://localhost:8080",
    scope="user-read-email,streaming",
    open_browser=False
)

simple_client = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"]
))

_sessions = {}


def authorize_user(discord_id, code):
    access_token = oauth.get_access_token(code=code, as_dict=False)
    _sessions[discord_id] = Spotify(auth=access_token)


def get_current_user(discord_id):
    return _sessions[discord_id].current_user()


def get_tracks(query):
    return simple_client.search(query, type="track", limit=5)["tracks"]["items"]


def queue(discord_id, track):
    return _sessions[discord_id].add_to_queue(track["uri"])
