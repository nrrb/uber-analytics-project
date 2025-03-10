import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import os
import time
from dotenv import load_dotenv

load_dotenv()
# Set up your Spotify API credentials (replace with your own)
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Authenticate using Client Credentials Flow
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

df = pd.read_csv('../data/spotify.csv')[['uri']].drop_duplicates()
track_uris = df['uri'].to_list()

# Retrieve track metadata in batches of 50
tracks_metadata = []
batch_size = 50
for i in range(0, len(track_uris), batch_size):
    batch = track_uris[i:i + batch_size]
    response = sp.tracks(batch)
    tracks_metadata.extend(response['tracks'])
    print(f"Fetched {i + len(batch)} of {len(track_uris)} tracks...")
    time.sleep(0.5)  # brief pause to respect rate limits

# Save track metadata to CSV
df_tracks = pd.json_normalize(tracks_metadata)
df_tracks.to_csv('../data/tracks_metadata.csv', index=False)
print("Track metadata saved to 'tracks_metadata.csv'.")