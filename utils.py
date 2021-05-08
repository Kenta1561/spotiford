# keycap emojis 1 through 5
number_emojis = [
    "\u0031\u20e3",
    "\u0032\u20e3",
    "\u0033\u20e3",
    "\u0034\u20e3",
    "\u0035\u20e3"
]


def concat_track_artists(track):
    return ", ".join([artist["name"] for artist in track["artists"]])
