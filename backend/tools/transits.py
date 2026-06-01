import ephem
from datetime import datetime
import pytz
from birth_chart import compute_birth_chart, get_zodiac_sign, PLANETS, ZODIAC_SIGNS

def get_daily_transits(date: str, natal_chart: dict) -> dict:
    """
    Get current planetary transits for a given date
    and compare them to the user's natal chart.
    date: 'YYYY-MM-DD'
    natal_chart: output from compute_birth_chart()
    """
    try:
        # Use UTC noon for daily transits
        observer = ephem.Observer()
        observer.lat = '0'
        observer.lon = '0'
        observer.date = f"{date.replace('-', '/')} 12:00:00"

        transits = {}
        for name, planet in PLANETS.items():
            planet.compute(observer)
            degrees = float(planet.hlong) * 180 / 3.14159265
            degrees = degrees % 360
            sign = get_zodiac_sign(degrees)

            # Compare to natal position if available
            natal_pos = natal_chart.get("planets", {}).get(name, {})
            natal_degrees = natal_pos.get("degrees", None)
            natal_sign = natal_pos.get("sign", None)

            aspect = None
            if natal_degrees is not None:
                diff = abs(degrees - natal_degrees) % 360
                if diff > 180:
                    diff = 360 - diff
                if diff < 10:
                    aspect = "Conjunction"
                elif abs(diff - 60) < 10:
                    aspect = "Sextile"
                elif abs(diff - 90) < 10:
                    aspect = "Square"
                elif abs(diff - 120) < 10:
                    aspect = "Trine"
                elif abs(diff - 180) < 10:
                    aspect = "Opposition"

            transits[name] = {
                "current_degrees": round(degrees, 2),
                "current_sign": sign,
                "natal_sign": natal_sign,
                "aspect_to_natal": aspect
            }

        return {
            "success": True,
            "date": date,
            "transits": transits
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import json

    # First get natal chart
    natal = compute_birth_chart(
        date="1995-06-15",
        time="10:30",
        latitude=19.054999,
        longitude=72.8692035,
        timezone="Asia/Kolkata"
    )

    # Then get today's transits
    result = get_daily_transits("2026-06-01", natal)
    print(json.dumps(result, indent=2))