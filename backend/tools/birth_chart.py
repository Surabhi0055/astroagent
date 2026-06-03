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

def calculate_aspects(planets_data):
    aspects = []
    planet_names = list(planets_data.keys())
    
    aspect_defs = {
        "Conjunction": (0, 8),
        "Sextile": (60, 6),
        "Square": (90, 8),
        "Trine": (120, 8),
        "Opposition": (180, 8)
    }
    
    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1 = planet_names[i]
            p2 = planet_names[j]
            deg1 = planets_data[p1]["degrees"]
            deg2 = planets_data[p2]["degrees"]
            
            diff = abs(deg1 - deg2)
            if diff > 180:
                diff = 360 - diff
                
            for name, (angle, orb) in aspect_defs.items():
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "planet1": p1,
                        "planet2": p2,
                        "aspect": name,
                        "orb": round(abs(diff - angle), 2)
                    })
    return aspects

def compute_birth_chart(
    date: str,
    time: str,
    place_name: str,
    mode: str = "western"
) -> dict:
    try:
        # Internally geocode the place to avoid LLM hallucinating timezones
        from tools.geocode import geocode_place
        geo = geocode_place(place_name)
        if not geo.get("success"):
            return {"success": False, "error": f"Could not find location: {place_name}"}
            
        latitude = geo["latitude"]
        longitude = geo["longitude"]
        timezone = geo["timezone"]

        tz = pytz.timezone(timezone)
        local_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.utc)

        utc_fractional_hour = utc_dt.hour + (utc_dt.minute / 60.0) + (utc_dt.second / 3600.0)
        julian_day = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_fractional_hour)

        flags = swe.FLG_SWIEPH
        if mode == "vedic":
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            flags |= swe.FLG_SIDEREAL

        planets_data = {}
        for name, planet_id in PLANETS.items():
            position, _ = swe.calc_ut(julian_day, planet_id, flags)
            lon = position[0]
            planets_data[name] = {
                "degrees": round(lon, 2),
                "sign": get_zodiac_sign(lon)
            }

        # Calculate houses (Placidus system by default, handling Sidereal mode if applied)
        cusps, ascmc = swe.houses(julian_day, latitude, longitude, b'P')
        
        houses_data = {}
        for i in range(1, 13):
            cusp_deg = cusps[i - 1]
            houses_data[str(i)] = {
                "degrees": round(cusp_deg, 2),
                "sign": get_zodiac_sign(cusp_deg)
            }
            
        ascendant = ascmc[0]
        midheaven = ascmc[1]

        # Aspects
        aspects_data = calculate_aspects(planets_data)

        # Planets in houses mapping
        for name, p in planets_data.items():
            deg = p["degrees"]
            house_num = 12
            for i in range(1, 13):
                c_start = cusps[i - 1]
                c_end = cusps[i] if i < 12 else cusps[0]
                # Handle 360 crossover
                if c_start <= c_end:
                    if c_start <= deg < c_end:
                        house_num = i
                        break
                else:
                    if deg >= c_start or deg < c_end:
                        house_num = i
                        break
            p["house"] = house_num

        return {
            "success": True,
            "birth_date": date,
            "birth_time": time,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "mode": mode,
            "planets": planets_data,
            "houses": houses_data,
            "ascendant": {"degrees": round(ascendant, 2), "sign": get_zodiac_sign(ascendant)},
            "midheaven": {"degrees": round(midheaven, 2), "sign": get_zodiac_sign(midheaven)},
            "aspects": aspects_data
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = compute_birth_chart("1995-06-15", "10:30", 19.05, 72.86, "Asia/Kolkata")
    print(json.dumps(result, indent=2))