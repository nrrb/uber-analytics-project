# While this technically runs, it's extremely sparse in identification.
# At track-level identification, it missed 97% of my songs. 
# At artist-level identification, it missed 52% of my artists.
import os
import time
import requests
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('AUDIODB_API_KEY')
if not api_key:
    raise ValueError("Please set your AUDIODB_API_KEY in the .env file.")

def get_genre_audiodb_track(artist, track):
    base_url = f"https://theaudiodb.com/api/v1/json/{api_key}/searchtrack.php"
    params = {"s": artist, "t": track}
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and data.get("track"):
            genre = data["track"][0].get("strGenre")
        else:
            genre = None
    except Exception as e:
        print(f"Error fetching genre for {artist} - {track}: {e}")
        genre = None

    # Wait 0.5 seconds to stay within 2 calls per second
#    time.sleep(0.5)
    return genre

def get_genre_audiodb_artist(artist):
    base_url = f"https://www.theaudiodb.com/api/v1/json/{api_key}/search.php"
    params = {"s": artist}
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and data.get("artists"):
            genre = data["artists"][0].get("strGenre")
        else:
            genre = None
    except Exception as e:
        print(f"Error fetching genre for {artist}: {e}")
        genre = None

    # Wait 0.5 seconds to stay within 2 calls per second
#    time.sleep(0.5)
    return genre




df = pd.read_csv('../data/spotify.csv')
df = df['artistName'].to_frame().drop_duplicates()
df = df.head(100)
tqdm.pandas(desc="Fetching genres")
df["predicted_genre"] = df.progress_apply(lambda row: get_genre_audiodb_artist(row["artistName"]), axis=1)
df.to_csv("../data/artists_with_genres_audiodb.csv", index=False)

print("Genre classification complete! Data saved as artists_with_genres_audiodb.csv.")
