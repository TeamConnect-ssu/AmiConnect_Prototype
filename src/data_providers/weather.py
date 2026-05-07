"""Fetch real weather data from OpenWeatherMap and return Korean response_text."""
from __future__ import annotations

import os
import urllib.request
import json


def get_weather_response() -> str:
    api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    city = os.environ.get("OPENWEATHER_CITY", "Seoul")
    lang = os.environ.get("OPENWEATHER_LANG", "kr")

    if not api_key:
        return "날씨 정보를 가져올 수 없어요. API 키를 설정해주세요."

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={api_key}&units=metric&lang={lang}"
        )
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read())

        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        desc = data["weather"][0]["description"]
        wind = data["wind"]["speed"]

        # 어르신 맞춤 문장 조합
        parts = [f"지금 {city}는 {desc}이고, 기온은 {temp}도예요."]

        if feels <= 5:
            parts.append(f"체감온도는 {feels}도로 많이 춥네요. 외출하실 때 두껍게 입으세요.")
        elif feels <= 12:
            parts.append(f"체감온도는 {feels}도예요. 겉옷 챙기세요.")
        elif feels >= 30:
            parts.append("많이 더우니 시원하게 계세요.")

        if wind >= 7:
            parts.append("바람도 많이 부니 조심하세요.")

        return " ".join(parts)

    except Exception:
        return "날씨 정보를 잠시 가져오지 못했어요."
