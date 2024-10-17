import base64
import io
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import colorsys
import random
import re
import platform

load_dotenv()

st.set_page_config(page_title="Playlist Cover Generator")


def lerp(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)

def hsv_to_rgb(h, s, v):
    return tuple(int(i * 255) for i in colorsys.hsv_to_rgb(h / 360, s / 100, v / 100))

def gen_art(words, blur_radius, background_color):
    width, height = 1000, 1000
    image = Image.new('RGB', (width, height), color=background_color)

    draw = ImageDraw.Draw(image)

    text_size = 70
    font_path = "arial.ttf"
    font = ImageFont.truetype(font_path, text_size)

    bg_luminance = colorsys.rgb_to_hsv(*background_color)[2]
    color = "black" if bg_luminance > 60 else "white"

    y_offset = 0
    for _ in range(20):
        shuffled_words = words.split()
        random.shuffle(shuffled_words)
        words = " ".join(shuffled_words)
        text_bbox = draw.textbbox((0, 0), words, font=font)
        text_height = text_bbox[3] - text_bbox[1]
        draw.text((0, y_offset), words, fill=color, font=font)
        y_offset += text_height

    blurred_image = image.filter(ImageFilter.GaussianBlur(blur_radius))

    img_bytes = io.BytesIO()
    blurred_image.save(img_bytes, format='JPEG', quality=9)  # Adjust quality parameter
    img_bytes = img_bytes.getvalue()

    return img_bytes

# SPOTIPY
CLIENT_ID = os.getenv('S_CLIENT_ID')
CLIENT_SECRET = os.getenv('S_CLIENT_SECRET')
if not platform.processor() == "":
    REDIRECT_URI = 'http://localhost:8501/'
else:
    REDIRECT_URI = 'https://lv-cover-generator.streamlit.app/'

SCOPE = "ugc-image-upload playlist-modify-public playlist-modify-private playlist-read-private user-library-read"

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE)

auth_url = sp_oauth.get_authorize_url()

code = st.query_params.get("code")
if 'code' not in st.session_state:
    st.session_state['code'] = code

usecode = st.session_state['code']


if usecode:
    token_info = sp_oauth.get_access_token(usecode)
    sp = spotipy.Spotify(auth=token_info['access_token'])

    st.title("Playlist Cover Generator")

    link = st.text_input('Playlist link')
    blur_radius = 4

    if 'background_color' not in st.session_state or st.button("Re-randomize Image"):
        st.session_state['background_color'] = hsv_to_rgb(random.randint(0, 360), random.randint(40, 80), random.randint(40, 80))
        if 'img_bytes' in st.session_state:
            del st.session_state['img_bytes']

    background_color = st.session_state['background_color']

    if link:
        playlist_id = link
        playlist = sp.playlist(playlist_id)
        tracks_names = " ".join([re.sub(r'[^a-zA-Z\s]', '', track['track']['name']).strip().lower() for track in playlist['tracks']['items']])
        if tracks_names:
            if 'img_bytes' not in st.session_state:
                st.session_state['img_bytes'] = gen_art(tracks_names, blur_radius, background_color)

            img_bytes = st.session_state['img_bytes']
            st.image(img_bytes, use_column_width=True)

            if st.button("Change playlist cover"):
                img = Image.open(io.BytesIO(img_bytes))
                jpeg_buffer = io.BytesIO()
                img.save(jpeg_buffer, format='JPEG')
                jpeg_bytes = jpeg_buffer.getvalue()
                img_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')

                sp.playlist_upload_cover_image(playlist_id, img_base64)

else:
    st.link_button("Authorize with Spotify", auth_url)
