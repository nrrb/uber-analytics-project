# I didn't use this method because 13300 songs would have cost $37-50 to process on GPT-4
import pandas as pd
import openai
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_genre(artist, song):
    # Simplified prompt to reduce token consumption
    prompt = f"Song: {song}\nArtist: {artist}\nGenre:"
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a music expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error with {artist} - {song}: {e}")
        return None

df = pd.read_csv('../data/spotify.csv')
df = df[['artistName', 'trackName']].drop_duplicates()
df["predicted_genre"] = [
    get_genre(row["artistName"], row["trackName"]) 
    for _, row in tqdm(df.iterrows(), total=len(df))
]
df.to_csv("../data/songs_with_genres_chatgpt.csv", index=False)

print("Genre classification complete! Data saved as songs_with_genres_chatgpt.csv.")
