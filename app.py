import os
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_KEY = os.environ.get('OPENWEATHER_API_KEY')


def get_weather(city: str):
    if not API_KEY:
        return {"error": "OPENWEATHER_API_KEY not set"}
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return {"error": str(exc)}
    data = resp.json()
    if data.get("cod") != 200:
        return {"error": data.get("message", "Unknown error from API")}
    w = data.get("weather", [{}])[0]
    main = data.get("main", {})
    return {
        "data": {
            "city": data.get("name"),
            "country": data.get("sys", {}).get("country"),
            "temp": main.get("temp"),
            "description": w.get("description"),
            "icon": w.get("icon"),
        }
    }


@app.route("/", methods=("GET", "POST"))
def index():
    weather = None
    error = None
    city = None
    if request.method == "POST":
        city = (request.form.get("city") or "").strip()
        if not city:
            error = "Please enter a city name."
        else:
            result = get_weather(city)
            if "error" in result:
                error = result["error"]
            else:
                weather = result["data"]
    return render_template("index.html", weather=weather, error=error, city=city)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
