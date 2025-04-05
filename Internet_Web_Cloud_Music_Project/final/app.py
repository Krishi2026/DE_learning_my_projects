import os
from flask import Flask, request, jsonify, render_template
import requests
import time
import base64
from gbmodel.model_datastore import model

# Initialize database
db = model()

# Initialize Flask app
app = Flask(__name__)

# API keys from environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

SPOTIFY_ACCESS_TOKEN = None  # Holds Spotify access token
SPOTIFY_TOKEN_EXPIRY = None  # Expiry timestamp for Spotify token


def get_spotify_token():
    """
    Fetch and cache Spotify access token using client credentials flow.

    Returns:
        str: Spotify access token.
    Raises:
        Exception: If unable to retrieve Spotify access token.
    """
    global SPOTIFY_ACCESS_TOKEN, SPOTIFY_TOKEN_EXPIRY
    if SPOTIFY_TOKEN_EXPIRY and time.time() < SPOTIFY_TOKEN_EXPIRY:
        return SPOTIFY_ACCESS_TOKEN

    auth_header = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_header.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        response_data = response.json()
        SPOTIFY_ACCESS_TOKEN = response_data.get("access_token")
        SPOTIFY_TOKEN_EXPIRY = time.time() + response_data.get("expires_in", 3600)
        return SPOTIFY_ACCESS_TOKEN
    else:
        raise Exception("Unable to retrieve Spotify access token.")


@app.route("/")
def welcome():
    """Render the welcome page."""
    return render_template("welcome.html")


@app.route("/main")
def main():
    """Render the main page."""
    return render_template("index.html")


@app.route("/autocomplete")
def autocomplete():
    """
    Fetch city suggestions dynamically using Google Places API.
    
    Query Parameters:
        input (str): The user input for city suggestions.

    Returns:
        JSON: A list of city suggestions or error details.
    """
    input_text = request.args.get("input")
    if not input_text:
        return jsonify({"error": "No input provided"}), 400

    # Fetch Google Places API Key from environment variables
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "AIzaSyA_pWbJfHl10MtJLL-5NuVHSV-FpJUj3wE")

    # Google Places Autocomplete API URL
    places_url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={input_text}&types=(cities)&key={GOOGLE_PLACES_API_KEY}"

    try:
        response = requests.get(places_url)
        if response.status_code == 200:
            data = response.json()
            predictions = [
                {"description": prediction["description"]}
                for prediction in data.get("predictions", [])
            ]
            return jsonify({"predictions": predictions})
        else:
            return jsonify({"error": "Failed to fetch city suggestions", "details": response.text}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error occurred"}), 500


@app.route("/get_weather")
def get_weather():
    """
    Fetch current weather data for a specified city.
    
    Query Parameters:
        city (str): Name of the city.

    Returns:
        JSON: Weather data or error details.
    """
    city = request.args.get("city")
    
    if not city:
        return jsonify({"error": "City not provided"}), 400
 
    if "," in city:
        city_name = city.split(",")[0].strip()
    else:
        city_name = city.strip()

    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(weather_url)
    if response.status_code == 200:
        weather_data = response.json()
        weather_description = weather_data["weather"][0]["description"]

        # Log weather data into the database
        db.insert(
            title=f"Weather Data for {city}",
            description=f"Weather: {weather_description}",
            weather=weather_description,
            url="N/A",
            image_url="N/A",
            type="Weather",
            user="N/A",
        )

        return jsonify(weather_data)
    else:
        return jsonify({"error": "Unable to fetch weather data"}), 500


@app.route("/get_photos")
def get_photos():
    """
    Fetch a random photo from Unsplash based on tags.

    Query Parameters:
        tags (str): Keywords to search for photos.

    Returns:
        JSON: Photo details or error message.
    """
    tags = request.args.get("tags")
    if not tags:
        return jsonify({"error": "Tags not provided"}), 400

    # Build the Unsplash API URL
    unsplash_url = f"https://api.unsplash.com/photos/random?query={tags}&client_id={UNSPLASH_API_KEY}"

    try:
        response = requests.get(unsplash_url)
        if response.status_code == 200:
            data = response.json()
            if "urls" in data:
                return jsonify(data)
            else:
                return jsonify({"error": "No image found"}), 404
        else:
            return jsonify({"error": "Failed to fetch Unsplash image", "details": response.text}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error occurred"}), 500


@app.route("/get_songs")
def get_songs():
    """
    Fetch Spotify playlists based on the weather description.

    Query Parameters:
        weather (str): Weather description.

    Returns:
        JSON: List of playlists or error message.
    """
    weather = request.args.get("weather")
    if not weather:
        return jsonify({"error": "Weather description not provided"}), 400

    get_spotify_token()
    spotify_url = f"https://api.spotify.com/v1/search?q={weather}&type=playlist&limit=5"
    headers = {"Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"}
    response = requests.get(spotify_url, headers=headers)

    if response.status_code == 200:
        playlists = response.json().get("playlists", {}).get("items", [])
        valid_playlists = []
        
        # Safely filter out invalid playlists
        for playlist in playlists:
            if not playlist:
                continue
            name = playlist.get("name")
            url = playlist.get("external_urls", {}).get("spotify")
            images = playlist.get("images")

            if name and url and images:
                valid_playlists.append({
                    "name": name,
                    "description": playlist.get("description", "No description available."),
                    "url": url,
                    "image": images[0].get("url") if images else "/static/default_image.jpg",
                })
                # Insert the valid playlist into the database
                db.insert(
                    title=name,
                    description=playlist.get("description", ""),
                    weather=weather,
                    url=url,
                    image_url=images[0].get("url") if images else "",
                    type="Playlist",
                    user="N/A",
                )

        return jsonify(valid_playlists)
    else:
        return jsonify({"error": "Unable to fetch playlists"}), 500


@app.route("/trending_playlists")
def trending_playlists():
    """
    Display playlists grouped by weather type from the database.
    
    Returns:
        HTML: Rendered template with grouped playlists.
    """
    records = db.select()
    grouped_playlists = {}
    for record in records:
        weather = record["weather"]
        if weather not in grouped_playlists:
            grouped_playlists[weather] = []
        grouped_playlists[weather].append({
            "title": record["title"],
            "url": record["url"],
            "image_url": record["image_url"],
        })
    return render_template("trending_playlists.html", grouped_playlists=grouped_playlists)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
