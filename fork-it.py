import streamlit as st
import requests
import os
import pandas as pd
import random

st.set_page_config(page_title="Fork It, Let’s Eat", page_icon="🥓", layout="centered")

GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY"))
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

RADIUS_OPTIONS = {
    "1 mile (~1.6 km)": 1600,
    "3 miles (~4.8 km)": 4800,
    "5 miles (~8 km)": 8000,
    "10 miles (~16 km)": 16000,
    "20 miles (~32 km)": 32000,
    "Max (31 miles / 50 km)": 50000
}
RATING_OPTIONS = ["Any", "3+", "3.5+", "4+", "4.5+"]
PICKY_EXCLUDE_TYPES = ["sushi_restaurant", "seafood_restaurant", "raw_bar", "vegetarian_restaurant"]

# Header
st.markdown("<h1 style='text-align:center;'>🍳 Fork It, Let’s Eat</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic;'>Grown women. Good food. No kids. No raw fish.</p>", unsafe_allow_html=True)

# Inputs
zip_code = st.text_input("📍 Start from ZIP:", "77494")
selected_radius_text = st.selectbox("🚗 How far are we brunching?", list(RADIUS_OPTIONS.keys()))
min_rating_text = st.selectbox("⭐ Minimum Rating?", RATING_OPTIONS)
filter_picky = st.checkbox("🙅‍♀️ No raw, weird, or rabbit food?", value=True)
blacklist = st.text_input("🚫 Banned restaurants? (comma-separated)").lower().split(',')

# Buttons
find_food = st.button("✨ Fork It! Find Food!")
random_choice = st.button("🎲 Just Pick One For Me")

def get_filtered_results():
    # Geocode
    geo_resp = requests.get(GEOCODING_URL, params={"address": zip_code, "key": GOOGLE_API_KEY}).json()
    if geo_resp.get("status") != "OK":
        st.error(f"Location fail: {geo_resp.get('error_message')}")
        st.stop()
    loc = geo_resp["results"][0]["geometry"]["location"]
    lat, lng = loc["lat"], loc["lng"]

    # Places
    places_resp = requests.get(PLACES_SEARCH_URL, params={
        "location": f"{lat},{lng}",
        "radius": RADIUS_OPTIONS[selected_radius_text],
        "type": "restaurant",
        "keyword": "brunch",
        "key": GOOGLE_API_KEY
    }).json()

    spots = []
    for place in places_resp.get("results", []):
        name = place.get("name", "").lower()
        if any(b.strip() and b.strip() in name for b in blacklist):
            continue
        rating = place.get("rating", 0)
        if min_rating_text != "Any" and rating < float(min_rating_text.replace("+", "")):
            continue
        if filter_picky and any(t in PICKY_EXCLUDE_TYPES for t in place.get("types", [])):
            continue
        spots.append({
            "name": place.get("name", "Unknown Spot"),
            "rating": rating,
            "address": place.get("vicinity", "???"),
            "map_url": f"https://www.google.com/maps/search/?api=1&query_place_id={place.get('place_id')}"
        })
    return sorted(spots, key=lambda x: x['rating'], reverse=True)

if find_food or random_choice:
    if not GOOGLE_API_KEY:
        st.error("Missing Google API key. Check secrets or env vars.")
        st.stop()

    st.write("🥞 Loading up the brunch buffet...")
    try:
        results = get_filtered_results()
        if not results:
            st.warning("Nada. Either brunch doesn't exist here or we're being *very* picky.")
            st.stop()

        if random_choice:
            pick = random.choice(results)
            st.success(f"🎯 You’re going to: **{pick['name']}**")
            st.markdown(f"""
                <p>{pick['address']}<br>
                ⭐ {pick['rating']} <br>
                <a href="{pick['map_url']}" target="_blank">📍 Open in Maps</a></p>
            """, unsafe_allow_html=True)
        else:
            st.subheader(f"🍾 {len(results)} Brunch-worthy Spots:")
            for spot in results:
                st.markdown(f"""
                    <div style='border:1px solid #f0c36d; border-radius:10px; background:#fffaf3; padding:10px; margin:10px 0'>
                        <b>{spot['name']}</b> <br>
                        {spot['address']}<br>
                        ⭐ {spot['rating']} <br>
                        <a href="{spot['map_url']}" target="_blank">📍 Open in Maps</a>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"💥 Something exploded: {e}")
