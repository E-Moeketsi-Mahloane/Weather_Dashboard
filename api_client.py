# I'm adding a new function to fetch the 5-day forecast.
# The key API changes from before:
# 1. I request "daily" variables instead of "current"
# 2. I set forecast_days=5
# 3. I MUST set timezone=auto when using daily (Open-Meteo requires this)
# I also keep the current weather function so the app still shows "now".

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 10


def get_coordinates(city_name):
    # This function is unchanged — it still turns a city name into lat/lon.
    params = {
        "name": city_name,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    try:
        response = requests.get(GEOCODE_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        raise ConnectionError("The request timed out. Check your internet and try again.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("I couldn't reach the weather service. Are you online?")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"The weather service returned an error: {e.response.status_code}")
    except ValueError:
        raise ConnectionError("I got a bad response from the weather service.")

    if "results" not in data or len(data["results"]) == 0:
        raise LookupError(f"I couldn't find a place called '{city_name}'. Try another spelling.")

    result = data["results"][0]
    return {
        "name": result.get("name", city_name),
        "country": result.get("country", ""),
        "lat": result["latitude"],
        "lon": result["longitude"],
    }


def get_current_weather(lat, lon):
    # Unchanged — still fetches "now" for the big display card.
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code",
        "timezone": "auto",
    }

    try:
        response = requests.get(WEATHER_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        raise ConnectionError("The weather request timed out. Please refresh.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("I lost connection to the weather service. Please refresh.")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"Weather service error: {e.response.status_code}")
    except ValueError:
        raise ConnectionError("I received an unreadable weather response.")

    current = data.get("current")
    if not current:
        raise LookupError("The weather service didn't return current conditions.")

    return {
        "temperature": current.get("temperature_2m"),
        "weather_code": current.get("weather_code"),
        "units": data.get("current_units", {}).get("temperature_2m", "°C"),
    }


# This is the new function.
# I request daily max/min temperature and the daily weather code.
# Open-Meteo returns parallel arrays: daily.time[], daily.temperature_2m_max[], etc.
# I zip them into a list of dicts so the UI doesn't have to index into arrays.
def get_forecast(lat, lon, days=5):
    params = {
        "latitude": lat,
        "longitude": lon,
        # These are the daily variables I want. I only ask for what I display.
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "forecast_days": days,          # 5 days, as requested
        "timezone": "auto",              # REQUIRED when using daily
    }

    try:
        response = requests.get(WEATHER_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        raise ConnectionError("The forecast request timed out. Please refresh.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("I lost connection while fetching the forecast.")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"Forecast service error: {e.response.status_code}")
    except ValueError:
        raise ConnectionError("I received an unreadable forecast response.")

    daily = data.get("daily")
    if not daily or "time" not in daily:
        raise LookupError("The forecast service didn't return daily data.")

    # I build a list of dicts — one per day.
    # daily["time"] is like ["2026-11-05", "2026-11-06", ...]
    # daily["temperature_2m_max"] is like [24.1, 25.3, ...]
    forecast = []
    for i, date_str in enumerate(daily["time"]):
        forecast.append({
            "date": date_str,
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "weather_code": daily["weather_code"][i],
        })

    return forecast


# I reuse the same WMO code mapping from before.
# I'll add short labels since the forecast row is compact.
def describe_weather(code):
    mapping = {
        0:  ("Clear", "☀️"),
        1:  ("Mainly clear", "🌤️"),
        2:  ("Partly cloudy", "⛅"),
        3:  ("Overcast", "☁️"),
        45: ("Fog", "🌫️"),
        48: ("Fog", "🌫️"),
        51: ("Drizzle", "🌦️"),
        53: ("Drizzle", "🌦️"),
        55: ("Drizzle", "🌧️"),
        61: ("Rain", "🌦️"),
        63: ("Rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        71: ("Snow", "🌨️"),
        73: ("Snow", "🌨️"),
        75: ("Heavy snow", "❄️"),
        80: ("Showers", "🌦️"),
        81: ("Showers", "🌧️"),
        82: ("Showers", "⛈️"),
        95: ("Thunder", "⛈️"),
        96: ("Thunder", "⛈️"),
        99: ("Thunder", "⛈️"),
    }
    return mapping.get(code, ("Unknown", "❓"))