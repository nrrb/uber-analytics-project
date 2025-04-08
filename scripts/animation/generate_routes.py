import pandas as pd
import hashlib
import requests
import time
import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import math

# === CONFIG ===
MAPBOX_TOKEN = "sk.eyJ1IjoibmljaG9sYXM3NzciLCJhIjoiY205ODMyN3MzMGU2OTJtcTJjcWtyZWJlNSJ9.AnFWV0t9Cfpl7XABWosHDg"  # Replace this
INPUT_CSV = "../../data/rides.csv"
CACHE_FILE = "cache.json"
OUTPUT_DIR = "output/geojson/cleaned"
GEOCODE_BASE = "https://api.mapbox.com/geocoding/v5/mapbox.places/"
DIRECTIONS_BASE = "https://api.mapbox.com/directions/v5/mapbox/driving/"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

CHICAGO_LAT = 41.8781
CHICAGO_LON = -87.6298
MAX_MILES = 100

# === INIT ===
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        cache = json.load(f)
else:
    cache = {}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def cache_key(*args):
    return hashlib.md5("::".join(args).encode()).hexdigest()

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def is_valid_point(lat, lon):
    return haversine(lat, lon, CHICAGO_LAT, CHICAGO_LON) <= MAX_MILES

def safe_request(url):
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return r.json()
            print(f"[HTTP {r.status_code}] {url}")
        except Exception as e:
            print(f"[Request Failed] {e}")
        time.sleep(RETRY_DELAY)
    return None

def geocode(address):
    print(f"[GEOCODE] {address}")
    key = cache_key("geocode", address)
    if key in cache:
        return cache[key]
    url = f"{GEOCODE_BASE}{requests.utils.quote(address)}.json?access_token={MAPBOX_TOKEN}&limit=1"
    data = safe_request(url)
    coords = None
    if data and data.get("features"):
        coords = data["features"][0]["geometry"]["coordinates"]
        # Filter out-of-bounds geocoded results
        if not is_valid_point(coords[1], coords[0]):
            print(f"[SKIPPED] Geocoded point {coords} too far from Chicago")
            coords = None
    cache[key] = coords
    return coords

def route_between(c1, c2):
    if not is_valid_point(c1[1], c1[0]) or not is_valid_point(c2[1], c2[0]):
        print(f"[SKIPPED] One or both points out of range: {c1}, {c2}")
        return None

    print(f"[ROUTE] {c1} -> {c2}")
    key = cache_key("route", str(c1), str(c2))
    if key in cache:
        return cache[key]

    coords_str = f"{c1[0]},{c1[1]};{c2[0]},{c2[1]}"
    url = f"{DIRECTIONS_BASE}{coords_str}?access_token={MAPBOX_TOKEN}&geometries=geojson"
    data = safe_request(url)

    geometry = None
    if data and data.get("routes"):
        route = data["routes"][0]["geometry"]
        coords = route.get("coordinates", [])
        coords = [pt for pt in coords if is_valid_point(pt[1], pt[0])]
        if coords:
            route["coordinates"] = coords
            geometry = route
        else:
            print("[SKIPPED] All route points filtered out as outliers")

    cache[key] = geometry
    return geometry

def save_geojson(day, features):
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    out_path = os.path.join(OUTPUT_DIR, f"{day}.geojson")
    with open(out_path, "w") as f:
        json.dump(geojson, f)
    print(f"[SAVED] {out_path}")

# === MAIN WORK ===
df = pd.read_csv(INPUT_CSV)
df["ride_start"] = pd.to_datetime(df["ride_start"])
df = df.sort_values("ride_start")

# Geocode pickup and dropoff
df["pickup_coords"] = df["pickup_address"].apply(geocode)
df["dropoff_coords"] = df["dropoff_address"].apply(geocode)
df = df[df["pickup_coords"].notnull() & df["dropoff_coords"].notnull()]

routes_by_day = defaultdict(list)

for i in range(len(df)):
    ride = df.iloc[i]
    ride_time = ride["ride_start"]
    if ride_time.time() < pd.to_datetime("05:00").time():
        day = (ride_time - pd.Timedelta(days=1)).date()
    else:
        day = ride_time.date()

    # 1. pickup → dropoff
    g1 = route_between(ride["pickup_coords"], ride["dropoff_coords"])
    if g1:
        routes_by_day[day].append({
            "type": "Feature",
            "geometry": g1,
            "properties": {
                "timestamp": ride["ride_start"].isoformat()
            }
        })

    # 2. dropoff → next pickup (if available)
    if i < len(df) - 1:
        next_ride = df.iloc[i + 1]
        g2 = route_between(ride["dropoff_coords"], next_ride["pickup_coords"])
        if g2:
            routes_by_day[day].append({
                "type": "Feature",
                "geometry": g2,
                "properties": {
                    "timestamp": next_ride["ride_start"].isoformat()
                }
            })

# === OUTPUT ===
for day, features in routes_by_day.items():
    save_geojson(str(day), features)

save_cache()
print("✅ Done generating cleaned route files.")
