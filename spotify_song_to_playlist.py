import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import os
from dotenv import load_dotenv
import base64
from io import BytesIO
import io
from PIL import Image
import requests
import random
load_dotenv()

# Spotify API credentials
CLIENT_ID = os.getenv('S_CLIENT_ID')
CLIENT_SECRET = os.getenv('S_CLIENT_SECRET')
REDIRECT_URI = 'https://smart-playlist.streamlit.app/'

# Define Spotify scope (the permissions you're requesting from the user)
SCOPE = "ugc-image-upload playlist-modify-public playlist-modify-private playlist-read-private user-library-read user-read-recently-played user-top-read"


def change_playlist_image(playlist_id, fig):
    img_bytes = pio.to_image(fig, format='png')

    image = Image.open(io.BytesIO(img_bytes))

    crop_box = (190-20, 100-20, 510+20, 420+20)
    cropped_image = image.crop(crop_box)

# Convert the image to RGBA mode
    cropped_image = cropped_image.convert("RGB")
    data = cropped_image.getdata()

    rand_rgb = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    new_data = []
    for item in data:
        # Change all black (also shades of black)
        # to a random color
        if item[0] < 200 and item[1] < 200 and item[2] < 200:
            new_data.append(rand_rgb)
        else:
            new_data.append(item)

    cropped_image.putdata(new_data)


    cropped_image_bytes = io.BytesIO()
    cropped_image.save(cropped_image_bytes, format='JPEG')
    cropped_image_bytes = cropped_image_bytes.getvalue()

    img_base64 = base64.b64encode(cropped_image_bytes).decode('utf-8')
    sp.playlist_upload_cover_image(playlist_id, img_base64)

    return img_bytes


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

    # Graph for song preview
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
                # visible=False,
                range=[0, 1],
                ticks="",
                tickwidth=0,
                ticklen=0,
                showticklabels=False  # Hide radial axis labels

            ),
            angularaxis=dict(
                ticklen=0,
                # linewidth=2,
                # visible=False,

                # showline=True,
                # showticklabels=False  # Hide angular axis labels
            ),
        ),
        showlegend=False
    )

    # Graph for cover photo
    fig2 = go.Figure()
    for i, label in enumerate(playlist):
        values = [lerp(label['features'][track], use[track]['range'][0], use[track]['range'][1]) for track in data if not use[track].get('hide', False)]
        data = [track for track in data if not use[track].get('hide', False)]

        df = pd.DataFrame(dict(
            r=values,
            theta=data
        ))

        fig2.add_trace(
            go.Scatterpolar(
                r=df['r'],
                theta=df['theta'],
                # fill="toself",  # No fill
                fill=None,
            )
        )

    fig2.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=False,
                range=[0, 1],
            ),
            angularaxis=dict(
                ticklen=0,
                showline=True,
                showticklabels=False  # Hide angular axis labels
            ),
        ),
        showlegend=False
    )

    return fig, fig2


def lerp(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)


def get_rec_from_track(play_url, limit=20, tune=None):
    # try:
    play_url = play_url.split("/")[-1].split("?")[0]
    song = sp.track(play_url)
    features = sp.audio_features(play_url) # type: list
    tune = tune # type: dict

    rec_obj = {}

    for opt in tune:
        if tune[opt] == 0:
            rec_obj[f'target_{opt}'] = features[0][opt]
        else:
            rec_obj[f'target_{opt}'] = features[0][opt]
            rec_obj[f'min_{opt}'] = features[0][opt] - tune[opt]
            rec_obj[f'max_{opt}'] = features[0][opt] + tune[opt]


    rec = sp.recommendations(
        seed_tracks=[play_url],
        limit=limit,
        **rec_obj
    )

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

with st.expander("How to use:"):
    st.write("1. Click the 'Authorize with Spotify' button below.")
    st.write("2. Log in to your Spotify account.")
    st.write("3. Copy the URL of a song you like on Spotify.")
    st.write("4. Paste the URL in the 'Enter a song URL' field.")
    st.write("5. Choose the number of recommendations you want.")
    st.write("6. Adjust the sliders to fine-tune the recommendations.")
    st.write("7. Click the 'Get recommendations' button.")
    st.write("8. Listen to the recommendations and create a playlist with them.")


# Capture the token after redirection
code = st.query_params.get("code")
if 'code' not in st.session_state:
    st.session_state['code'] = code
    # st.query_params.clear()

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
        url = st.text_input("Enter a song URL", key="play_url", value="https://open.spotify.com/track/4cSMfAD4NsTmoHLLthMoug?si=33800fc3e040410c")

    with col2:
        limit = st.number_input("Number of recommendations", min_value=1, max_value=100, value=20)

    spotify_recommendation_parameters = [
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
            "name": "Key",
            "description": "The key the track is in. Integers map to pitches using standard Pitch Class notation. E.g. 0 = C, 1 = C♯/D♭, 2 = D, and so on.",
            "range": [0, 11, 2]
        },
        {
            "name": "Tempo",
            "description": "The overall estimated tempo of a track in beats per minute (BPM). In musical terminology, tempo is the speed or pace of a given piece and derives directly from the average beat duration.",
            "range": [0, 100, 20]
        },
        {
            "name": "Valence",
            "description": "A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).",
            "range": [0.0, 1.0, 0.2]
        },
        {
            "name": "Acousticness",
            "description": "A measure from 0.0 to 1.0 of whether the track is acoustic. A higher value represents a higher likelihood that the track is acoustic.",
            "enabled": True
        },
        {
            "name": "Instrumentalness",
            "description": "Predicts whether a track contains no vocals. 'Ooh' and 'aah' sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly 'vocal'. The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content.",
            "enabled": True
        },
        {
            "name": "Liveness",
            "description": "Detects the presence of an audience in the recording. Higher liveness values represent an increased probability that the track was performed live. A value above 0.8 provides strong likelihood that the track is live.",
            "enabled": True
        },
        {
            "name": "Loudness",
            "description": "The overall loudness of a track in decibels (dB). Loudness values are averaged across the entire track and are useful for comparing relative loudness of tracks. Loudness is the quality of a sound that is the primary psychological correlate of physical strength (amplitude).",
            "hide": True,
            "range": [-60, 0, 10]
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
            "description": "Speechiness detects the presence of spoken words in a track. The more exclusively speech-like the recording (e.g. talk show, audio book, poetry), the closer to 1.0 the attribute value. Values above 0.66 describe tracks that are probably made entirely of spoken words. Values between 0.33 and 0.66 describe tracks that may contain both music and speech, either in sections or layered, including such cases as rap music. Values below 0.33 most likely represent music and other non-speech-like tracks.",
            "enabled": True
        }
    ]

    with st.expander("Advanced options:"):
        st.info("These are variations from the original track's features. Sliders completely left will match the original track's features.", icon="ℹ️")

        tune = {}
        for index, param in enumerate(spotify_recommendation_parameters):
            if "range" in param and index < 5 and not param.get("hide", False):
                tune[param["name"].lower()] = st.slider(
                    f"{param['name']} variation",
                    param["range"][0],
                    param["range"][1],
                    param["range"][2],
                    help=param["description"]
                )
        if st.checkbox("Super advanced options:"):
            st.info("Toggle to enable matching based on each parameter. Drag slider off of 0 to introduce variation in matched values.", icon="ℹ️")
            for index, param in enumerate(spotify_recommendation_parameters):
                if index > 4 and not param.get("hide", False):
                    with st.container(border=True):
                        on = param.get('enabled', False)
                        use = st.toggle(f"Match by '{param['name'].lower()}'", key=f"toggle_{param['name']}", value=on)
                        try:
                            min_val = param['range'][0] or 0
                            max_val = param['range'][1] or 1
                        except:
                            min_val = 0.0
                            max_val = 1.0
                        slider = st.slider(
                            f"{param['name']} variation",
                            min_value=min_val,
                            max_value=max_val,
                            value=0.0,
                            disabled=not use,
                            help=param["description"]
                        )
                        if use:
                            tune[param["name"].lower()] = slider



    if st.button("Get recommendations"):
        results = get_rec_from_track(url, limit=limit, tune=tune)
        st.session_state.results = results
        st.session_state.playlist_created = False  # Reset playlist creation state


    if st.session_state.results:
        results = st.session_state.results
        fig1, fig2 = do_plot(results)
        # st.plotly_chart(fig2)
        st.plotly_chart(fig1)

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
            image = change_playlist_image(newplay['id'], fig2)
            recs = [track['id'] for track in results]
            add_tracks_to_playlist(newplay['id'], recs)
            st.session_state.playlist_created = True  # Update playlist creation state
            st.link_button("Open playlist on Spotify", f"https://open.spotify.com/playlist/{newplay['id']}")
    else:
        pass

else:
    st.link_button("Authorize with Spotify", auth_url)
