import ephem
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
import timezonefinder

PLANETS = {
    "Sun": ephem.Sun(),
    "Moon": ephem.Moon(),
    "Mercury": ephem.Mercury(),
    "Venus": ephem.Venus(),
    "Mars": ephem.Mars(),
    "Jupiter": ephem.Jupiter(),
    "Saturn": ephem.Saturn(),
}

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_zodiac_sign(degrees: float) -> str:
    index = int(degrees / 30) % 12
    return ZODIAC_SIGNS[index]

def compute_birth_chart(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    timezone: str
) -> dict:

    try:
        # Parse local datetime and convert to UTC
        tz = pytz.timezone(timezone)
        local_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.utc)

        # Set up observer
        observer = ephem.Observer()
        observer.lat = str(latitude)
        observer.lon = str(longitude)
        observer.date = utc_dt.strftime("%Y/%m/%d %H:%M:%S")

        # Compute planets
        planets_data = {}
        for name, planet in PLANETS.items():
            planet.compute(observer)
            degrees = float(planet.hlong) * 180 / 3.14159265
            degrees = degrees % 360
            sign = get_zodiac_sign(degrees)
            planets_data[name] = {
                "degrees": round(degrees, 2),
                "sign": sign
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
    result = compute_birth_chart(
        date="1995-06-15",
        time="10:30",
        latitude=19.054999,
        longitude=72.8692035,
        timezone="Asia/Kolkata"
    )
    import json
    print(json.dumps(result, indent=2))