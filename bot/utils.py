# key cap emojis 1 through 5
number_emojis = [
    "\u0031\u20e3",
    "\u0032\u20e3",
    "\u0033\u20e3",
    "\u0034\u20e3",
    "\u0035\u20e3"
]

heart_emoji = "\u2764"
broken_heart_emoji = "\U0001f494"


def concat_track_artists(track):
    """
    Concatenate the names of multiple artists of a track.

    :param track: Track
    :return: Multiple artist names separated by commas
    """

    return ", ".join([artist["name"] for artist in track["artists"]])
