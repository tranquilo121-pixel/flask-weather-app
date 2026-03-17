import os
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_KEY = os.environ.get('OPENWEATHER_API_KEY')


def get_weather(city=None, lat=None, lon=None):
    if not API_KEY:
        return {"error": "OPENWEATHER_API_KEY not set"}
    url = "https://api.openweathermap.org/data/2.5/weather"
    if lat and lon:
        params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    else:
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
    wind = data.get("wind", {})
    return {
        "data": {
            "city": data.get("name"),
            "country": data.get("sys", {}).get("country"),
            "temp": round(main.get("temp")),
            "feels_like": round(main.get("feels_like")),
            "humidity": main.get("humidity"),
            "wind_speed": round(wind.get("speed", 0) * 3.6, 1),
            "description": w.get("description"),
            "icon": w.get("icon"),
        }
    }


def get_forecast(city=None, lat=None, lon=None):
    if not API_KEY:
        return []
    url = "https://api.openweathermap.org/data/2.5/forecast"
    if lat and lon:
        params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric", "cnt": 40}
    else:
        params = {"q": city, "appid": API_KEY, "units": "metric", "cnt": 40}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    seen_days = set()
    forecast = []
    for item in data.get("list", []):
        date = item["dt_txt"].split(" ")[0]
        time = item["dt_txt"].split(" ")[1]
        if date not in seen_days and time == "12:00:00":
            seen_days.add(date)
            w = item["weather"][0]
            forecast.append({
                "date": date,
                "temp_max": round(item["main"]["temp_max"]),
                "temp_min": round(item["main"]["temp_min"]),
                "icon": w["icon"],
                "description": w["description"],
            })
        if len(forecast) == 5:
            break

    return forecast


@app.route("/", methods=("GET", "POST"))
def index():
    weather = None
    forecast = []
    error = None
    city = None
    if request.method == "POST":
        lat = request.form.get("lat")
        lon = request.form.get("lon")
        city = (request.form.get("city") or "").strip()

        if lat and lon:
            result = get_weather(lat=lat, lon=lon)
            if "error" not in result:
                forecast = get_forecast(lat=lat, lon=lon)
        elif city:
            result = get_weather(city=city)
            if "error" not in result:
                forecast = get_forecast(city=city)
        else:
            result = {"error": "Please enter a city name."}

        if "error" in result:
            error = result["error"]
        else:
            weather = result["data"]
            city = weather["city"]

    return render_template("index.html", weather=weather, forecast=forecast, error=error, city=city)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
