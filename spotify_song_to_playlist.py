import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.graph_objects as go
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

def create_playlist(name="Suggested playlist", description="Playlist created by the app"):
    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(user=user_id, name=name, public=True, description=description, collaborative=True)
    return playlist

def add_tracks_to_playlist(playlist_id, track_ids):
    sp.playlist_add_items(playlist_id, track_ids)

def get_recommendations(seed_tracks):
    recommendations = sp.recommendations(seed_tracks=seed_tracks)
    recs = [rec['id'] for rec in recommendations['tracks']]
    return recs

def do_plot(playlist):
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
            "hide": True
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
        showlegend=False
    )

    return fig

def lerp(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)

def get_rec_from_track(play_url, limit=20, tune=None):
    # try:
    play_url = play_url.split("/")[-1].split("?")[0]
    song = sp.track(play_url)
    features = sp.audio_features(play_url)

    rec = sp.recommendations(
        seed_tracks=[play_url],
        target_danceability=features[0]['danceability'],
        min_danceability=features[0]['danceability'] - tune['danceability'],
        max_danceability=features[0]['danceability'] + tune['danceability'],
        target_energy=features[0]['energy'],
        min_energy=features[0]['energy'] - tune['energy'],
        max_energy=features[0]['energy'] + tune['energy'],
        target_key=features[0]['key'],
        min_key=features[0]['key'] - tune['key'],
        max_key=features[0]['key'] + tune['key'],
        target_loudness=features[0]['loudness'] ,
        target_mode=features[0]['mode'],
        target_speechiness=features[0]['speechiness'],
        target_acousticness=features[0]['acousticness'],
        target_instrumentalness=features[0]['instrumentalness'],
        target_liveness=features[0]['liveness'],
        target_valence=features[0]['valence'],
        min_valence=features[0]['valence'] - tune['valence'],
        max_valence=features[0]['valence'] + tune['valence'],
        target_tempo=features[0]['tempo'],
        min_tempo=features[0]['tempo'] - tune['tempo'],
        max_tempo=features[0]['tempo'] + tune['tempo'],
        limit=limit
    )


    # newplay = create_playlist(song['name'] + " suggested", "recs")
    recs = [rec['id'] for rec in rec['tracks']]

    # add_tracks_to_playlist(newplay['id'], recs)
    # playlist = sp.playlist(newplay['id'])
    tracks_info = []
    for item in rec['tracks']:
        track = item
        track_info = {
            'image': track['album']['images'][0]['url'],
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


# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE)

# Display the Spotify login button
auth_url = sp_oauth.get_authorize_url()

st.set_page_config(page_title="Spotify Song to Playlist", layout="wide")
st.title("Spotify Song to Playlist")


# Capture the token after redirection
code = st.query_params.get("code")

if code:
    st.subheader("Recommendations from a song")

    # Get the access token
    token_info = sp_oauth.get_access_token(code)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    music_keys = ["A♭", "A", "B♭", "B", "C", "D♭", "D", "E♭", "E", "F", "G♭", "G"]

    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'playlist_created' not in st.session_state:
        st.session_state.playlist_created = False

    col1, col2 = st.columns(2)
    with col1:
        url = st.text_input("Enter a song URL", key="play_url")

    with col2:
        limit = st.number_input("Number of recommendations", min_value=1, max_value=100, value=20)

    with st.expander("Advanced options:"):
        st.info("Tune the recommendation parameters to control variation in tracks.")
        danceability = st.slider("Danceability variation", 0.0, 1.0, 0.2)
        energy = st.slider("Energy variation", 0.0, 1.0, 0.15)
        key = st.slider("Key variation", 0, 11, 2)
        valence = st.slider("Valence variation", 0.0, 1.0, 0.2)
        tempo = st.slider("Tempo variation _(BPM)_", 0, 100, 20)

    tune = {
        "danceability": danceability,
        "energy": energy,
        "key": key,
        "valence": valence,
        "tempo": tempo
    }

    if st.button("Get recommendations"):
        results = get_rec_from_track(url, limit=limit, tune=tune)
        st.session_state.results = results
        st.session_state.playlist_created = False  # Reset playlist creation state

    if st.session_state.results:
        results = st.session_state.results
        st.plotly_chart(do_plot(results))
        data = {
            "Image": [track['image'] for track in results],
            "Name": [track['name'] for track in results],
            "Artist": [track['artist'] for track in results],
            "BPM": [track['features']['tempo'] for track in results],
            "Key": [music_keys[int(track['features']['key'])] for track in results],
            "Preview": [track['preview_url'] for track in results]
        }
        tabledata = {
            "Name": [track['name'] for track in results],
            "Artist": [track['artist'] for track in results],
            "BPM": [track['features']['tempo'] for track in results],
            "Key": [music_keys[int(track['features']['key'])] for track in results],
        }
        df = pd.DataFrame(data)
        tdf = pd.DataFrame(tabledata)
        # Display the table with play buttons
        # st.table(df)
        st.dataframe(tdf.set_index(tdf.columns[0]), width=1000000)
        with st.expander("Preview recommendations"):
            for index, row in df.iterrows():
                prevcol1, prevcol2 = st.columns([1, 8])
                with prevcol1:
                    st.image(row['Image'], width=100)
                with prevcol2:
                    st.write(f"**{row['Name']}** by {row['Artist']}")
                    st.write(f"BPM: {row['BPM']}")
                    st.write(f"Key: {row['Key']}")

                playcol1, playcol2 = st.columns([1, 5], vertical_alignment="center")
                with playcol1:
                    st.link_button("Like on Spotify", f"https://open.spotify.com/track/{results[index]['id']}", use_container_width=True)
                with playcol2:
                    if row['Preview']:
                        st.audio(row['Preview'], format='audio/mp3')
                    else:
                        st.write("No preview available")

        st.subheader("Playlist creation")
        first_name = results[0]['name']
        input_name = st.text_input("Playlist name", value=f'{first_name} - Playlist')
        input_desc = st.text_input("Playlist description", value="Playlist created by the LV Smart Playlist")
        if st.button("Create playlist") and not st.session_state.playlist_created:
            newplay = create_playlist(input_name, input_desc)
            recs = [track['id'] for track in results]
            add_tracks_to_playlist(newplay['id'], recs)
            st.session_state.playlist_created = True  # Update playlist creation state
            st.write("Playlist created!")
            st.link_button("Open playlist", f"https://open.spotify.com/playlist/{newplay['id']}")
    else:
        pass

else:
    st.link_button("Authorize with Spotify", auth_url)

