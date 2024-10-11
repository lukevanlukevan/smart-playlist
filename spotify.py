import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

# Set up authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('S_CLIENT_ID'),
    client_secret=os.getenv('S_CLIENT_SECRET'),
    redirect_uri="http://example.com",
    scope="playlist-modify-public"
))

def create_playlist(name, description):
    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(user=user_id, name=name, public=True, description=description)
    return playlist

def add_tracks_to_playlist(playlist_id, track_ids):
    sp.playlist_add_items(playlist_id, track_ids)

def main():
    # playlist_name = "My New Playlist"
    # playlist_description = "This is a new playlist created with Spotipy"
    # track_ids = ["spotify:track:4cOdK2wGLETKBW3PvgPWqT", "spotify:track:1301WleyT98MSxVHPZCA6M"]  # Replace with your track IDs

    # Create a new playlist
    # playlist = create_playlist(playlist_name, playlist_description)
    # print(f"Created playlist: {playlist['name']}")

    # Add tracks to the playlist
    # add_tracks_to_playlist(playlist["id"], track_ids)
    # print(f"Added tracks to playlist: {playlist['name']}")
    results = sp.search(q='weezer', limit=20)
    for i, t in enumerate(results['tracks']['items']):
        print(' ', i, t['name'])

if __name__ == "__main__":
    main()