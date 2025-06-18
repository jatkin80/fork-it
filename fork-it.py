import streamlit as st
import requests
import os
import random


st.set_page_config(page_title="Find a Spot", page_icon="🍽️", layout="centered")

st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Georgia', serif;
            color: #3E2723;
            background-color: #F1F8E9;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Roboto Slab', Georgia, serif;
            color: #880E4F;
            text-align: center;
            padding-bottom: 0.5em;
             font-weight: bold;
        }

        .spot-card {
            background-color: #FFFFFF;
            border: 1px solid #d7ccc8;
            border-radius: 8px;
            padding: 1.5em;
            margin-bottom: 1.5em;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
        }

        .spot-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 5px 10px rgba(0,0,0,0.12);
        }

        .big-pick {
            font-size: 1.6em;
            font-weight: bold;
            color: #FFFFFF;
            background-color: #880E4F;
            padding: 1em;
            border-radius: 6px;
            box-shadow: 0 4px 8px rgba(136, 14, 79, 0.4);
            text-align: center;
            margin: 1.5em 0;
        }

        .rating {
            font-size: 1em;
            color: #FF9800;
            font-weight: bold;
        }

        .stButton>button {
            background-color: #880E4F;
            color: white; /* Default text color */
            border: none;
            border-radius: 6px;
            font-weight: bold;
            padding: 0.7em 1.5em;
            margin-top: 0.8em;
            transition: background-color 0.2s ease-in-out, box_shadow 0.2s ease-in-out;
        }

        .stButton>button:hover {
            background-color: #6A1B9A;
            color: #3E2723; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .stButton>button:active {
            background-color: #4A148C;
            color: #3E2723; 
        }


        .stTextInput>div>input {
            background-color: #FFFFFF;
            border: 1px solid #D7CCC8;
            border-radius: 6px;
            padding: 0.7em 1em;
            color: #3E2723;
        }

         .stTextInput>div>input:focus {
            border-color: #880E4F;
            box-shadow: 0 0 0 0.2rem rgba(136, 14, 79, 0.25);
            outline: none;
        }

        iframe {
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }

        .css-1d3y0rq {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

    </style>
""", unsafe_allow_html=True)


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY is None:
    try:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    except (KeyError, st.errors.StreamlitAPIException):
        GOOGLE_API_KEY = None

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"

RADIUS_OPTIONS = {
    "1 mile": 1600,
    "3 miles": 4800,
    "5 miles": 8000,
    "10 miles": 16000,
    "20 miles": 32000,
    "Max (31 miles)": 50000
}
RATING_OPTIONS = ["Any", "3+", "3.5+", "4+", "4.5+"]

PREFERENCE_OPTIONS_MAP = {
    "Restaurant (General)": {"type": "restaurant"},
    "Brunch Spot": {"type": "restaurant", "keyword": "brunch"},
    "Lunch Spot": {"type": "restaurant", "keyword": "lunch"},
    "Dinner Spot": {"type": "restaurant", "keyword": "dinner"},
    "Cafe / Coffee Shop": {"type": "cafe"},
    "Bar / Pub": {"type": "bar"},
    "Craft Beer Bar": {"type": "bar", "keyword": "craft beer"},
    "Pizza Place": {"type": "meal_takeaway", "keyword": "pizza"},
    "Mexican Restaurant": {"type": "restaurant", "keyword": "mexican food"},
}

PICKY_EXCLUDE_TYPES = ["sushi_restaurant", "seafood_restaurant", "raw_bar", "vegetarian_restaurant", "vegan_restaurant", "thai_restaurant"]


st.markdown("<h1 style='text-align:center;'>🍽️ Find a Spot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic;'>Let's find a place to eat or drink!</p>", unsafe_allow_html=True)

zip_code = st.text_input("📍 Start from ZIP:", "77494")
selected_radius_text = st.selectbox("🚗 How far are we going?", list(RADIUS_OPTIONS.keys()))
min_rating_text = st.selectbox("⭐ Minimum Rating?", RATING_OPTIONS)

selected_preference = st.selectbox("🍔 What vibe are we looking for?", list(PREFERENCE_OPTIONS_MAP.keys()))

filter_gluten_free = st.checkbox("🌾 Look for Gluten-Free options?")

filter_picky = st.checkbox("🙅‍♀️ Apply 'picky' filters (e.g., No raw fish, etc.)?", value=True)

blacklist = st.text_input("🚫 Hard pass places (comma-separated)").lower().split(',')
col1, col2 = st.columns(2)
with col1:
    find_food = st.button("✨ Search!", use_container_width=True)
with col2:
    random_choice = st.button("🎲 Just Pick One For Me", use_container_width=True)


def is_valid_image_url(url, timeout=5):
    """
    Checks if a URL points to a valid image by making a HEAD request.
    Handles redirects from the Google Places Photo API.
    Returns True if the URL successfully leads to an image, False otherwise.
    """
    if not url:
        return False
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if content_type.startswith('image/'):
                return True
        return False
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.RequestException as e:
        return False


def get_filtered_results(preference_key, include_gluten_free, apply_picky_filter):
    if preference_key not in PREFERENCE_OPTIONS_MAP:
        st.error(f"Unknown preference selected: {preference_key}")
        return []

    api_params_base = PREFERENCE_OPTIONS_MAP[preference_key]
    place_type = api_params_base.get("type")
    initial_keyword = api_params_base.get("keyword", "")

    final_keyword = initial_keyword
    if include_gluten_free:
        if final_keyword:
            final_keyword += " gluten free" 
        else:
            final_keyword = "gluten free"

    geo_resp = requests.get(GEOCODING_URL, params={"address": zip_code, "key": GOOGLE_API_KEY}).json()
    if geo_resp.get("status") != "OK":
        st.error(f"Location fail: {geo_resp.get('error_message')}")
        return []

    loc = geo_resp["results"][0]["geometry"]["location"]
    lat, lng = loc["lat"], loc["lng"]

    places_params = {
        "location": f"{lat},{lng}",
        "radius": RADIUS_OPTIONS[selected_radius_text],
        "key": GOOGLE_API_KEY
    }

    if place_type:
        places_params["type"] = place_type

    if final_keyword:
        places_params["keyword"] = final_keyword

    places_resp = requests.get(PLACES_SEARCH_URL, params=places_params).json()

    spots = []
    for place in places_resp.get("results", []):
        name_lower = place.get("name", "").lower()
        if any(b.strip() and b.strip() in name_lower for b in blacklist):
            continue

        rating = place.get("rating", 0)
        min_rating_val = 0.0
        if min_rating_text != "Any":
            try:
                min_rating_val = float(min_rating_text.replace("+", ""))
            except ValueError:
                st.warning(f"Invalid rating format: {min_rating_text}")

        if min_rating_text != "Any" and rating < min_rating_val:
            continue

        if apply_picky_filter and place_type in ["restaurant", "meal_takeaway"] and any(t in PICKY_EXCLUDE_TYPES for t in place.get("types", [])):
             continue

        validated_photo_url = None
        photos_data = place.get("photos")
        if photos_data:
            photo_reference = photos_data[0].get("photo_reference")
            if photo_reference:
                potential_api_photo_url = f"{PHOTO_BASE_URL}?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_API_KEY}"
                if potential_api_photo_url and is_valid_image_url(potential_api_photo_url):
                     validated_photo_url = potential_api_photo_url


        spots.append({
            "name": place.get("name", "Unknown Spot"),
            "rating": rating,
            "address": place.get("vicinity", "???"),
            "map_url": f"https://www.google.com/maps/search/?api=1&query_place_id={place.get('place_id')}",
            "photo_url": validated_photo_url
        })
    return sorted(spots, key=lambda x: x['rating'], reverse=True)


if find_food or random_choice:
    if not GOOGLE_API_KEY:
        st.error("Missing Google API key. Check secrets or env vars.")
        st.stop()

    search_description = selected_preference.lower()
    if filter_gluten_free:
         search_description = f"{search_description} with gluten-free options"

    st.write(f"🔎 Searching for a great {search_description} near {zip_code}...")

    try:
        results = get_filtered_results(selected_preference, filter_gluten_free, filter_picky)

        if not results:
            message = f"Couldn't find any {search_description} places matching your criteria."
            if filter_gluten_free:
                message += " Finding good gluten-free options via search can be tricky!"
            message += " Try lowering your standards or increasing your radius."
            st.warning(message)
            st.stop()

        if random_choice:
            pick = random.choice(results)
            st.markdown(f"""
                <div class="big-pick">
                    🎯 YOUR PICK IS:<br><b>{pick['name']}</b><br>
                    ⭐ {pick['rating']}<br>
                    <a href="{pick['map_url']}" target="_blank">📍 Click for Maps</a>
                </div>
            """, unsafe_allow_html=True)
            if pick['photo_url']:
                st.image(pick['photo_url'], use_container_width=True)

        else:
            st.subheader(f"✨ {len(results)} {search_description.replace(' with', ' With')} Spots Found:") 
            for spot in results:
                st.markdown(f"<div class='spot-card'>", unsafe_allow_html=True)
                st.markdown(f"<h4>🍽️ {spot['name']}</h4>", unsafe_allow_html=True)
                if spot['photo_url']:
                    st.image(spot['photo_url'], use_container_width=True)
                st.markdown(f"""
                    <p>{spot['address']}<br>
                    ⭐ {spot['rating']}<br>
                    <a href="{spot['map_url']}" target="_blank">📍 Open in Google Maps</a></p>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 🎧 Get in the mood")
        st.components.v1.iframe(
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX4WYpdgoIcn6?utm_source=generator",
            height=80, scrolling=False
        )

    except Exception as e:
        st.error(f"💥 Something went wrong: {e}")
