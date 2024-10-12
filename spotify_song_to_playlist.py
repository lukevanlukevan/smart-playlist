import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

# Spotify API credentials
CLIENT_ID=os.getenv('S_CLIENT_ID')
CLIENT_SECRET=os.getenv('S_CLIENT_SECRET')
REDIRECT_URI = 'https://lv-smart-playlist.streamlit.app/'

# Define Spotify scope (the permissions you're requesting from the user)
SCOPE = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read user-read-recently-played user-top-read"

def create_playlist(name, description):
    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(user=user_id, name=name, public=True, description=description, collaborative=True)
    return playlist

def add_tracks_to_playlist(playlist_id, track_ids):
    sp.playlist_add_items(playlist_id, track_ids)

def get_recommendations(seed_tracks):
    recommendations = sp.recommendations(seed_tracks=seed_tracks)
    recs = [rec['id'] for rec in recommendations['tracks']]
    return recs

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

def get_rec_from_track(play_url):
    # try:
    play_url = play_url.split("/")[-1].split("?")[0]
    song = sp.track(play_url)
    features = sp.audio_features(play_url)

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


    # newplay = create_playlist(song['name'] + " suggested", "recs")
    recs = [rec['id'] for rec in rec['tracks']]

    # add_tracks_to_playlist(newplay['id'], recs)
    # playlist = sp.playlist(newplay['id'])
    tracks_info = []
    for item in rec['tracks']:
        track = item
        track_info = {
            'id': track['id'],
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'preview_url': track['preview_url']
        }
        tracks_info.append(track_info)


    features = sp.audio_features([track['id'] for track in tracks_info])
    for track, feature in zip(tracks_info, features):
        track['features'] = feature

    return tracks_info

    # do_plot()

# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE)

# Display the Spotify login button
auth_url = sp_oauth.get_authorize_url()

st.title("Spotify Song to Playlist")


# Capture the token after redirection
code = st.query_params.get("code")

if code:
    # Get the access token
    token_info = sp_oauth.get_access_token(code)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    music_keys = ["A♭", "A", "B♭", "B", "C", "D♭", "D", "E♭", "E", "F", "G♭", "G"]

    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'playlist_created' not in st.session_state:
        st.session_state.playlist_created = False

    url = st.text_input("Enter a song URL", key="play_url")

    if st.button("Get recommendations"):
        results = get_rec_from_track(url)
        st.session_state.results = results
        st.session_state.playlist_created = False  # Reset playlist creation state

    if st.session_state.results:
        results = st.session_state.results
        data = {
            "Name": [track['name'] for track in results],
            "Artist": [track['artist'] for track in results],
            "BPM": [track['features']['tempo'] for track in results],
            "Key": [music_keys[int(track['features']['key'])] for track in results],
            "Preview": [track['preview_url'] for track in results]
        }
        df = pd.DataFrame(data)
        # Display the table with play buttons
        for index, row in df.iterrows():
            st.write(f"**{row['Name']}** by {row['Artist']} - BPM: {row['BPM']}, Key: {row['Key']}")
            if row['Preview']:
                st.audio(row['Preview'], format='audio/mp3')
            else:
                st.write("No preview available")

        if st.button("Create playlist") and not st.session_state.playlist_created:
            input_name = "Suggested Playlist"
            input_desc = "Playlist created by the app"
            newplay = create_playlist(input_name, input_desc)
            recs = [track['id'] for track in results]
            add_tracks_to_playlist(newplay['id'], recs)
            st.session_state.playlist_created = True  # Update playlist creation state
            st.write("Playlist created!")
            st.write(f"Listen to it [here](https://open.spotify.com/playlist/{newplay['id']})")
    else:
        st.write("Waiting for recommendations...")

else:
    st.write(f"Click [here to authorize]({auth_url}) with Spotify")
    st.write("Waiting for authentication...")

