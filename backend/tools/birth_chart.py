import swisseph as swe
from datetime import datetime
import pytz
import json

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_zodiac_sign(degrees: float) -> str:
    index = int(degrees / 30) % 12
    return ZODIAC_SIGNS[index]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
}

def compute_birth_chart(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    timezone: str
) -> dict:
    try:
        # 1. Convert local time to UTC
        tz = pytz.timezone(timezone)
        local_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.utc)

        # 2. Convert to Julian Day
        utc_fractional_hour = utc_dt.hour + (utc_dt.minute / 60.0) + (utc_dt.second / 3600.0)
        julian_day = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_fractional_hour)

        planets_data = {}
        for name, planet_id in PLANETS.items():
            position, _ = swe.calc_ut(julian_day, planet_id)
            longitude = position[0]
            
            planets_data[name] = {
                "degrees": round(longitude, 2),
                "sign": get_zodiac_sign(longitude)
            }

        return {
            "success": True,
            "birth_date": date,
            "birth_time": time,
            "timezone": timezone,
            "planets": planets_data
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = compute_birth_chart("1995-06-15", "10:30", 19.05, 72.86, "Asia/Kolkata")
    print(json.dumps(result, indent=2))