import random

title = "**Retro Vibe Kitchen Jive**"
playlist_name = [word.replace("*", "").lower() for word in title.split(" ")]
random.shuffle(playlist_name)
playlist_name = "".join(playlist_name)

print(playlist_name)