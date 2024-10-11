import json
import os
import random
from openai import OpenAI
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from difflib import SequenceMatcher
import re
import spotdl

from dotenv import load_dotenv
load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_KEY')

client = OpenAI(
    # This is the default and can be omitted
    api_key=OPENAI_KEY
)

def query_prompt():
    print("Ask ChatGPT a for a playlist: ")
    query = input()
    return query


def make_playlist(query):
    print("Asking the robot overlords...")
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Create a playlist of 20 songs that are available on spotify, based on the following description: {query}, Make the first line a quriky genz styled name based on the request, then return ONLY a bullet list of songs names and artists. Remove all punctuation.",
            }
        ],
        model="gpt-4o",
    )
    playlist = response.choices[0].message.content
    return playlist

def parse_playlist(playlist):
    title = playlist.split("\n")[0]
    song_list = [line[2:] for line in playlist.split("\n") if line.startswith("-")]
    return title, song_list

# SPOTIFY STUFF
# Set up authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('S_CLIENT_ID'),
    client_secret=os.getenv('S_CLIENT_SECRET'),
    redirect_uri="http://example.com",
    scope="playlist-modify-public"
))

def create_playlist(name, description):
    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(user=user_id, name=name, public=True, description=description, collaborative=True)
    return playlist

def add_tracks_to_playlist(playlist_id, track_ids):
    sp.playlist_add_items(playlist_id, track_ids)

def track_from_name(song):
    results = sp.search(q=song.replace("by ", ""), limit=5)
    title = song.split("by")[0]

    ret = results['tracks']['items'][0]
    found = "".join(re.findall("[a-zA-Z ]", ret['name']))
    search = "".join(re.findall("[a-zA-Z ]", title))
    sim = similar(found, search)


    if sim > 0.45:
        return ret['id']
    else:
        return "foo"

def get_recommendations(seed_tracks):
    recommendations = sp.recommendations(seed_tracks=seed_tracks)
    recs = [rec['id'] for rec in recommendations['tracks']]
    return recs

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def prompt_yes_no(question, default="y"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "y":
        prompt = " [Y/n] "
    elif default == "n":
        prompt = " [y/N] "
    else:
        raise ValueError(f"Invalid default answer: '{default}'")

    while True:
        choice = input(question + prompt).strip().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")

def download_spotify(playlist):
    print("Downloading songs...")
    plist = playlist

    with open("playlist.json", "w") as f:
        json.dump(plist, f, indent=4)

    pname = "".join(re.findall("[a-zA-Z ]", plist['name']))

    os.makedirs(pname, exist_ok=True)
    os.chdir(pname)
    # link = "https://open.spotify.com/playlist/3qNch4XYwQY1HhbWyc0jff"
    command = f"spotdl {plist['external_urls']['spotify']}"
    # command = f"spotdl {link}"

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        print(f"Command output:\n{stdout}")
    else:
        print(f"Command failed with error:\n{stderr}")

def main():
    try:
        play_url = input("Enter a song URL: ").split("/")[-1].split("?")[0]
        song = sp.track(play_url)
        features = sp.audio_features(play_url)

        with open("track.json", "w") as f:
            json.dump(song, f, indent=4)

        with open("track_info.json", "w") as f:
            json.dump(features, f, indent=4)


        rec = sp.recommendations(
            seed_tracks=[play_url],
            target_danceability=features[0]['danceability'],
            min_danceability=features[0]['danceability']-0.2,
            max_danceability=features[0]['danceability']+0.2,
            target_energy=features[0]['energy'],
            min_energy=features[0]['energy']-0.2,
            max_energy=features[0]['energy']+0.2,
            target_key=features[0]['key'],
            min_key=features[0]['key'] - 2,
            max_key=features[0]['key'] + 2,
            target_loudness=features[0]['loudness'],
            target_mode=features[0]['mode'],
            target_speechiness=features[0]['speechiness'],
            target_acousticness=features[0]['acousticness'],
            target_instrumentalness=features[0]['instrumentalness'],
            target_liveness=features[0]['liveness'],
            target_valence=features[0]['valence'],
            target_tempo=features[0]['tempo'],
            min_tempo=features[0]['tempo'] - 30,
            max_tempo=features[0]['tempo'] + 30,
        )

        newplay = create_playlist(song['name'] + " suggested", "recs")
        recs = [rec['id'] for rec in rec['tracks']]
        add_tracks_to_playlist(newplay['id'], recs)
        print("Playlist created")

    except Exception as e:
        print("Something went wrong...")
        print(e)

if __name__ == "__main__":
    main()