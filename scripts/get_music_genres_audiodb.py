# While this technically runs, after letting this run for 3.5 hours
# it identified ALL genres as "Pop-Rock" which is useless.
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

def get_genre_audiodb(artist, track):
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

df = pd.read_csv('../data/spotify.csv')
df = df[['artistName', 'trackName']].drop_duplicates()
df = df.head(100)
tqdm.pandas(desc="Fetching genres")
df["predicted_genre"] = df.progress_apply(lambda row: get_genre_audiodb(row["artistName"], row["trackName"]), axis=1)
df.to_csv("../data/songs_with_genres_audiodb.csv", index=False)

print("Genre classification complete! Data saved as songs_with_genres_audiodb.csv.")
