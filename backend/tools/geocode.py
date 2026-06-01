from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import timezonefinder

def geocode_place(place_name: str) -> dict:
    """
    Convert a place name to latitude, longitude and timezone.
    Returns dict with lat, lon, timezone or error message.
    """
    try:
        geolocator = Nominatim(user_agent="astroagent")
        location = geolocator.geocode(place_name, timeout=10)
        
        if not location:
            return {
                "error": f"Could not find location: {place_name}",
                "success": False
            }
        
        tf = timezonefinder.TimezoneFinder()
        timezone = tf.timezone_at(
            lat=location.latitude,
            lng=location.longitude
        )
        
        return {
            "place": place_name,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": timezone,
            "success": True
        }
        
    except GeocoderTimedOut:
        return {"error": "Geocoding timed out", "success": False}
    except GeocoderUnavailable:
        return {"error": "Geocoding service unavailable", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


if __name__ == "__main__":
    result = geocode_place("Mumbai, India")
    print(result)