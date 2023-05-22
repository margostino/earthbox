from skyfield.api import Topos, load

# Load TLE data (replace with specific TLE lines)
filepath = "../data/last_30_days_launches.tle"
satellites = load.tle_file(filepath)
satellite = satellites[15]

# Get your desired time (UTC)
ts = load.timescale()
# t = ts.utc(2023, 5, 22, 15, 20, 0)  # Replace with preferred date and time
#
# # Calculate satellite position in ECEF coordinates
# geocentric = satellite.at(t)
# x, y, z = geocentric.position.km
#
# # Convert ECEF to latitude, longitude, and altitude
# subpoint = geocentric.subpoint()
# latitude = subpoint.latitude.degrees
# longitude = subpoint.longitude.degrees
# altitude = subpoint.elevation.km
#
# print(f"Latitude {latitude}\nLongitude {longitude}\nAltitude {altitude}")

import csv
from datetime import datetime
from datetime import timedelta

now = datetime.now()


with open('../data/last_30_days_launches.csv', 'w') as f:
    writer = csv.writer(f)

    writer.writerow(["Satellite", "Latitude", "Longitude"])
    for i in range(30):
        date = now - timedelta(days=i)
        # convert datetime to Time
        t = ts.utc(date.year, date.month, date.day, date.hour, date.minute, date.second)
        geocentric = satellite.at(t)
        x, y, z = geocentric.position.km
        subpoint = geocentric.subpoint()
        latitude = subpoint.latitude.degrees
        longitude = subpoint.longitude.degrees
        altitude = subpoint.elevation.km

        print(f"Latitude {latitude}\nLongitude {longitude}\nAltitude {altitude}")
        writer.writerow([satellite.name, latitude, longitude])















# writer.writerow(row)