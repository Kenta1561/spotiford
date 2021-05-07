from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import os


oauth = SpotifyOAuth(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    redirect_uri="http://localhost:8080",
    scope="user-read-email",
    open_browser=False
)

sessions = {}


def authorize_user(discord_id, code):
    access_token = oauth.get_access_token(code=code, as_dict=False)
    sessions[discord_id] = Spotify(auth=access_token)


def get_current_user(discord_id):
    return sessions[discord_id].current_user()
