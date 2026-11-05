# Weather Dashboard — Capstone App

A Flet desktop app that fetches live weather data from the free Open-Meteo API
(no API key required) and displays the city, temperature, and conditions in a
styled dark interface.

## Features

- Search any city by name (geocoding via Open-Meteo)
- Live current temperature + condition, with a weather emoji icon
- Refresh button (or press Enter in the search field)
- Friendly, human-readable error messages for:
  - empty input
  - city not found
  - network / timeout failures
  - unexpected errors
- Loading spinner while a request is in flight
- Single-source colour palette for consistency

## Tech stack

- **Python 3.10+**
- **Flet** — UI framework
- **requests** — HTTP client
- **Open-Meteo** — free weather + geocoding API (no key)
