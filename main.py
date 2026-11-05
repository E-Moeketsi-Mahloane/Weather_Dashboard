# I add a horizontal forecast row below the main current-weather card.
# The row shows 5 compact cards: day name, icon, max/min temp.
# I import datetime to turn "2026-11-05" into "Wed" — nicer to read.

import flet as ft
from datetime import datetime

from api_client import get_coordinates, get_current_weather, get_forecast, describe_weather


COLORS = {
    "bg": "#0f172a",
    "card": "#1e293b",
    "accent": "#38bdf8",
    "text": "#f1f5f9",
    "muted": "#94a3b8",
    "error": "#f87171",
    "success": "#4ade80",
}


def main(page: ft.Page):
    page.title = "Weather Dashboard"
    page.bgcolor = COLORS["bg"]
    page.padding = 24
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    city_input = ft.TextField(
        hint_text="Type a city, e.g. Cape Town",
        width=320,
        autofocus=True,
        filled=True,
        bgcolor=COLORS["card"],
        border_color=COLORS["accent"],
        color=COLORS["text"],
        on_submit=lambda e: refresh(e),
    )

    status_text = ft.Text("", color=COLORS["muted"], size=13, text_align=ft.TextAlign.CENTER)
    progress = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color=COLORS["accent"])

    # --- Current weather card (unchanged) ---
    city_label = ft.Text("—", size=20, weight=ft.FontWeight.BOLD, color=COLORS["text"], text_align=ft.TextAlign.CENTER)
    weather_icon = ft.Text("🌍", size=64, text_align=ft.TextAlign.CENTER)
    condition_label = ft.Text("Waiting for a search...", size=14, color=COLORS["muted"], text_align=ft.TextAlign.CENTER)
    temp_label = ft.Text("--", size=56, weight=ft.FontWeight.BOLD, color=COLORS["accent"], text_align=ft.TextAlign.CENTER)
    updated_label = ft.Text("", size=11, color=COLORS["muted"], text_align=ft.TextAlign.CENTER)

    result_card = ft.Container(
        content=ft.Column(
            [city_label, weather_icon, condition_label, temp_label, updated_label],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
        width=360,
        padding=24,
        bgcolor=COLORS["card"],
        border_radius=20,
        alignment=ft.alignment.center,
    )

    # --- NEW: forecast row ---
    # I use a Row with scroll=AUTO so if 5 cards don't fit on a narrow window,
    # the user can scroll horizontally instead of the layout breaking.
    # I also set spacing so the cards breathe.
    forecast_row = ft.Row(
        controls=[],
        spacing=10,
        alignment=ft.MainAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
    )

    forecast_label = ft.Text(
        "5-Day Forecast",
        size=16,
        weight=ft.FontWeight.W_600,
        color=COLORS["text"],
    )

    # I wrap the forecast section in a Column so I can toggle its visibility.
    forecast_section = ft.Column(
        [forecast_label, forecast_row],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
        visible=False,   # Hidden until we have data
    )

    def set_loading(is_loading: bool):
        progress.visible = is_loading
        refresh_button.disabled = is_loading
        page.update()

    def show_error(message: str):
        status_text.value = message
        status_text.color = COLORS["error"]
        condition_label.value = "Couldn't load weather"
        condition_label.color = COLORS["error"]
        temp_label.value = "--"
        weather_icon.value = "⚠️"
        updated_label.value = ""
        forecast_section.visible = False
        page.update()

    # This helper builds ONE small card for a single day.
    # I take the ISO date string and turn it into a short weekday name.
    def build_day_card(day_data: dict) -> ft.Container:
        # datetime.fromisoformat("2026-11-05").strftime("%a") -> "Wed"
        day_name = datetime.fromisoformat(day_data["date"]).strftime("%a")
        _, icon = describe_weather(day_data["weather_code"])

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(day_name, size=12, color=COLORS["muted"], weight=ft.FontWeight.W_600),
                    ft.Text(icon, size=24),
                    ft.Text(
                        f"{day_data['temp_max']:.0f}°",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=COLORS["text"],
                    ),
                    ft.Text(
                        f"{day_data['temp_min']:.0f}°",
                        size=12,
                        color=COLORS["muted"],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            width=72,
            padding=10,
            bgcolor=COLORS["card"],
            border_radius=12,
            alignment=ft.alignment.center,
        )

    def refresh(e=None):
        city = (city_input.value or "").strip()

        if not city:
            status_text.value = "Please type a city name first."
            status_text.color = COLORS["error"]
            page.update()
            return

        status_text.value = "Fetching weather..."
        status_text.color = COLORS["muted"]
        condition_label.color = COLORS["muted"]
        set_loading(True)

        try:
            location = get_coordinates(city)
            current = get_current_weather(location["lat"], location["lon"])
            forecast = get_forecast(location["lat"], location["lon"], days=5)

            # --- Update current card ---
            condition_text, icon = describe_weather(current["weather_code"])
            city_label.value = f"{location['name']}, {location['country']}".strip(", ")
            weather_icon.value = icon
            condition_label.value = condition_text
            condition_label.color = COLORS["text"]
            temp_label.value = f"{current['temperature']:.0f}{current['units']}"
            updated_label.value = "Updated just now"

            # --- Rebuild the forecast row ---
            # I clear old cards first, then append new ones.
            # This is simpler than trying to update existing cards in place.
            forecast_row.controls.clear()
            for day in forecast:
                forecast_row.controls.append(build_day_card(day))

            forecast_section.visible = True
            status_text.value = "✓ Weather loaded"
            status_text.color = COLORS["success"]

        except LookupError as err:
            show_error(str(err))
        except ConnectionError as err:
            show_error(str(err))
        except Exception as err:
            print(f"[UNEXPECTED] {type(err).__name__}: {err}")
            show_error("Something went wrong. Please try again.")
        finally:
            set_loading(False)

    refresh_button = ft.ElevatedButton(
        text="Refresh",
        icon=ft.icons.REFRESH,
        on_click=refresh,
        bgcolor=COLORS["accent"],
        color=COLORS["bg"],
        height=48,
    )

    page.add(
        ft.Text("Weather Dashboard", size=28, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
        ft.Text("Live data from Open-Meteo", size=12, color=COLORS["muted"]),
        ft.Divider(height=20, color="transparent"),
        city_input,
        ft.Row([refresh_button, progress], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
        status_text,
        ft.Divider(height=16, color="transparent"),
        result_card,
        ft.Divider(height=20, color="transparent"),
        forecast_section,   # NEW — appears after a successful search
    )


if __name__ == "__main__":
    ft.app(target=main)