import ephem
from datetime import datetime

date = "1995/06/15 05:00:00" # UTC
sun = ephem.Sun()
sun.compute(date)
print("heliocentric:", sun.hlong * 180 / 3.14159265)
ecl = ephem.Ecliptic(sun)
print("geocentric ecliptic:", ecl.lon * 180 / 3.14159265)
