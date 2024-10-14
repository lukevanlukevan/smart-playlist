import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.graph_objects as go
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

# Spotify API credentials
CLIENT_ID = os.getenv('S_CLIENT_ID')
CLIENT_SECRET = os.getenv('S_CLIENT_SECRET')
REDIRECT_URI = 'https://smart-playlist.streamlit.app/'

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
        target_loudness=features[0]['loudness'],
        target_mode=features[0]['mode'],
        target_speechiness=features[0]['speechiness'],
        target_acousticness=features[0]['acousticness'],
        # min_acousticness=features[0]['acousticness'] - tune['acousticness'],
        # max_acousticness=features[0]['acousticness'] + tune['acousticness'],
        target_instrumentalness=features[0]['instrumentalness'],
        # min_instrumentalness=features[0]['instrumentalness'] - tune['instrumentalness'],
        # max_instrumentalness=features[0]['instrumentalness'] + tune['instrumentalness'],
        target_liveness=features[0]['liveness'],
        # min_liveness=features[0]['liveness'] - tune['liveness'],
        # max_liveness=features[0]['liveness'] + tune['liveness'],
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
if 'code' not in st.session_state:
    st.session_state['code'] = code
    st.query_params.clear()

usecode = st.session_state['code']


if usecode:
    st.subheader("Recommendations from a song")

    # Get the access token
    token_info = sp_oauth.get_access_token(usecode)
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

    spotify_recommendation_parameters = [
        {
            "name": "Acousticness",
            "description": "A measure from 0.0 to 1.0 of whether the track is acoustic. A higher value represents a higher likelihood that the track is acoustic.",
        },
        {
            "name": "Danceability",
            "description": "A measure from 0.0 to 1.0 of how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A higher value indicates a track that is more danceable.",
            "range": [0.0, 1.0, 0.2]
        },
        {
            "name": "Energy",
            "description": "A measure from 0.0 to 1.0 that represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale.",
            "range": [0.0, 1.0, 0.15]
        },
        {
            "name": "Instrumentalness",
            "description": "Predicts whether a track contains no vocals. 'Ooh' and 'aah' sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly 'vocal'. The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content.",
        },
        {
            "name": "Key",
            "description": "The key the track is in. Integers map to pitches using standard Pitch Class notation. E.g. 0 = C, 1 = C♯/D♭, 2 = D, and so on.",
            "range": [0, 11, 2]
        },
        {
            "name": "Liveness",
            "description": "Detects the presence of an audience in the recording. Higher liveness values represent an increased probability that the track was performed live. A value above 0.8 provides strong likelihood that the track is live.",
        },
        {
            "name": "Loudness",
            "description": "The overall loudness of a track in decibels (dB). Loudness values are averaged across the entire track and are useful for comparing relative loudness of tracks. Loudness is the quality of a sound that is the primary psychological correlate of physical strength (amplitude)."
        },
        {
            "name": "Mode",
            "description": "Mode indicates the modality (major or minor) of a track, the type of scale from which its melodic content is derived. Major is represented by 1 and minor is 0."
        },
        {
            "name": "Popularity",
            "description": "A measure from 0 to 100 of how popular the track is. The higher the value, the more popular the track. Popularity is based on the total number of plays the track has had and how recent those plays are."
        },
        {
            "name": "Speechiness",
            "description": "Speechiness detects the presence of spoken words in a track. The more exclusively speech-like the recording (e.g. talk show, audio book, poetry), the closer to 1.0 the attribute value. Values above 0.66 describe tracks that are probably made entirely of spoken words. Values between 0.33 and 0.66 describe tracks that may contain both music and speech, either in sections or layered, including such cases as rap music. Values below 0.33 most likely represent music and other non-speech-like tracks."
        },
        {
            "name": "Tempo",
            "description": "The overall estimated tempo of a track in beats per minute (BPM). In musical terminology, tempo is the speed or pace of a given piece and derives directly from the average beat duration.",
            "range": [0, 100, 20]
        },
        {
            "name": "Time Signature",
            "description": "An estimated overall time signature of a track. The time signature (meter) is a notational convention to specify how many beats are in each bar (or measure)."
        },
        {
            "name": "Valence",
            "description": "A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).",
            "range": [0.0, 1.0, 0.2]
        }
        ]

    with st.expander("Advanced options:"):
        st.info("These are variations from the original track's features. Sliders completely left will match the original track's features.", icon="ℹ️")

        tune = {}
        for param in spotify_recommendation_parameters:
            if "range" in param:
                tune[param["name"].lower()] = st.slider(
                    f"{param['name']} variation",
                    param["range"][0],
                    param["range"][1],
                    param["range"][2],
                    help=param["description"]
                )

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

