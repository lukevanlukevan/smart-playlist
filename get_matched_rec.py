import json
import os
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from difflib import SequenceMatcher
import re
import plotly.graph_objects as go
import pandas as pd

from dotenv import load_dotenv
load_dotenv()
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



def do_plot():

    with open("playlist_info.json", "r") as f:
        playlist = json.load(f)
    use = {
        "danceability": {
            "range": [0, 1],
        },
        "energy": {
            "range": [0, 1],
        },
        "key": {
            "range": [-1, 11],
        },
        "loudness": {
            "range": [-60, 0],
        },
        "mode": {
            "range": [0, 1],
        },
        "speechiness": {
            "range": [0, 1],
            "hide": True,
        },
        "acousticness": {
            "range": [0, 1],
        },
        "instrumentalness": {
            "range": [0, 1],
        },
        "liveness": {
            "range": [0, 1],
        },
        "valence": {
            "range": [0, 1],
        },
        "tempo": {
            "range": [40, 200],
            "hide": False,
        }

    }

    data = [label for label in playlist[0]['features'].keys() if label in use]

    fig = go.Figure()
    for i, label in enumerate(playlist):
        values = [lerp(label['features'][track], use[track]['range'][0], use[track]['range'][1]) for track in data if not use[track].get('hide', False)]
        data = [track for track in data if not use[track].get('hide', False)]

        df = pd.DataFrame(dict(
            r=values,
            theta=data
        ))

        fig.add_trace(
            go.Scatterpolar(
                r=df['r'],
                theta=df['theta'],
                # fill="toself",  # No fill
                fill=None,
                name=f"{label['name']} ({label['artist']})",
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True
    )

    fig.show()


def lerp(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)

def main():
    # try:
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
        limit=40
    )

    newplay = create_playlist(song['name'] + " suggested", "recs")
    recs = [rec['id'] for rec in rec['tracks']]
    add_tracks_to_playlist(newplay['id'], recs)
    print("Playlist created")
    playlist = sp.playlist(newplay['id'])
    # playlist = sp.playlist("https://open.spotify.com/playlist/2XEnnhTMP3qKvPqacPxsCC?si=e12bbbec05cd48dc")
    tracks_info = []
    for item in playlist['tracks']['items']:
        track = item['track']
        track_info = {
            'id': track['id'],
            'name': track['name'],
            'artist': track['artists'][0]['name']
        }
        tracks_info.append(track_info)

    features = sp.audio_features([track['id'] for track in tracks_info])
    for track, feature in zip(tracks_info, features):
        track['features'] = feature

    with open("playlist_info.json", "w") as f:
        json.dump(tracks_info, f, indent=4)

    do_plot()

    # except Exception as e:
    #     print("Something went wrong...")
    #     print(e)

if __name__ == "__main__":
    main()