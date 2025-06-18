import streamlit as st
import requests
import os
import random

# ---------------- Styling ---------------- #
st.set_page_config(page_title="Fork It, Let’s Eat", page_icon="🍽️", layout="centered")

st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: "Trebuchet MS", sans-serif;
        }
        .spot-card {
            border: 2px solid #ffcc80;
            border-radius: 15px;
            padding: 1em;
            margin-bottom: 1em;
            background-color: #fff3e0;
            box-shadow: 1px 1px 8px #e0cfcf;
        }
        .spot-card:hover {
            background-color: #fff0d5;
        }
        .big-pick {
            font-size: 1.6em;
            color: #d84315;
            font-weight: bold;
            background-color: #ffe5d0;
            border: 3px dashed #ffb74d;
            border-radius: 12px;
            padding: 1em;
            text-align: center;
            margin-top: 20px;
        }
        .rating {
            font-size: 1.2em;
            color: #ff9800;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- Constants ---------------- #
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY"))
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"

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

# ---------------- Header ---------------- #
st.markdown("<h1 style='text-align:center;'>🍳 Fork It, Let’s Eat</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic;'>A brunch roulette for chaotic moms who don’t want raw fish or kids near their croissants.</p>", unsafe_allow_html=True)

# ---------------- Input ---------------- #
zip_code = st.text_input("📍 Start from ZIP:", "77494")
selected_radius_text = st.selectbox("🚗 How far are we brunching?", list(RADIUS_OPTIONS.keys()))
min_rating_text = st.selectbox("⭐ Minimum Yelp-y Score?", RATING_OPTIONS)
filter_picky = st.checkbox("🙅‍♀️ No raw, weird, or rabbit food?", value=True)
blacklist = st.text_input("🚫 Hard pass places (comma-separated)").lower().split(',')

# ---------------- Buttons ---------------- #
find_food = st.button("✨ Fork It! Find Food!")
random_choice = st.button("🎲 Just Pick One For Me")

# ---------------- Helper ---------------- #
def get_filtered_results():
    # Step 1: Get coordinates from ZIP
    geo_resp = requests.get(GEOCODING_URL, params={"address": zip_code, "key": GOOGLE_API_KEY}).json()
    if geo_resp.get("status") != "OK":
        st.error(f"Location fail: {geo_resp.get('error_message')}")
        st.stop()
    loc = geo_resp["results"][0]["geometry"]["location"]
    lat, lng = loc["lat"], loc["lng"]

    # Step 2: Get places
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
        photo_url = None
        photos = place.get("photos")
        if photos:
            ref = photos[0].get("photo_reference")
            photo_url = f"{PHOTO_BASE_URL}?maxwidth=400&photoreference={ref}&key={GOOGLE_API_KEY}"
        spots.append({
            "name": place.get("name", "Unknown Spot"),
            "rating": rating,
            "address": place.get("vicinity", "???"),
            "map_url": f"https://www.google.com/maps/search/?api=1&query_place_id={place.get('place_id')}",
            "photo_url": photo_url
        })
    return sorted(spots, key=lambda x: x['rating'], reverse=True)

def mimosa_meter(rating):
    try:
        r = float(rating)
        if r >= 4.5:
            return "🥂🥂🥂🥂🥂 (Mimosas flowing like water)"
        elif r >= 4:
            return "🥂🥂🥂🥂 (Solid choice, babe)"
        elif r >= 3.5:
            return "🥂🥂🥂 (Might be fine with enough coffee)"
        elif r >= 3:
            return "🥂🥂 (Desperate times...)"
        else:
            return "🥂 (Only if it’s the last place on Earth)"
    except:
        return "No mimosa energy detected"

# ---------------- Run App ---------------- #
if find_food or random_choice:
    if not GOOGLE_API_KEY:
        st.error("Missing Google API key. Check secrets or env vars.")
        st.stop()

    st.write("🥞 Scouring the streets for carbs and caffeine...")
    try:
        results = get_filtered_results()
        if not results:
            st.warning("Nothing passed the vibe check. Try lowering your standards or increasing your radius.")
            st.stop()

        if random_choice:
            pick = random.choice(results)
            st.markdown(f"""
                <div class="big-pick">
                    🎯 BRUNCH FATE SEALED:<br><b>{pick['name']}</b><br>
                    ⭐ {pick['rating']} – {mimosa_meter(pick['rating'])}<br>
                    <a href="{pick['map_url']}" target="_blank">📍 Click for Maps</a>
                </div>
            """, unsafe_allow_html=True)
            if pick['photo_url']:
                st.image(pick['photo_url'], use_column_width=True)

        else:
            st.subheader(f"🍾 {len(results)} Brunchable Beauties Found:")
            for spot in results:
                st.markdown(f"<div class='spot-card'>", unsafe_allow_html=True)
                st.markdown(f"<h4>🍽️ {spot['name']}</h4>", unsafe_allow_html=True)
                if spot['photo_url']:
                    st.image(spot['photo_url'], use_column_width=True)
                st.markdown(f"""
                    <p>{spot['address']}<br>
                    ⭐ {spot['rating']} – <span class="rating">{mimosa_meter(spot['rating'])}</span><br>
                    <a href="{spot['map_url']}" target="_blank">📍 Open in Google Maps</a></p>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # ---------------- Spotify Vibes ---------------- #
        st.markdown("### 🎧 Brunch Vibes (Optional Dance-Off)")
        st.components.v1.iframe(
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX4WYpdgoIcn6?utm_source=generator",
            height=80, scrolling=False
        )

    except Exception as e:
        st.error(f"💥 Something exploded: {e}")

