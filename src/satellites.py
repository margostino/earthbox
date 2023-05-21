from skyfield.api import Topos, load

# Load TLE data (replace with specific TLE lines)
filepath = "../data/last_30_days_launches.tle"
satellites = load.tle_file(filepath)
satellite = satellites[0]

# Get your desired time (UTC)
ts = load.timescale()
t = ts.utc(2023, 5, 20, 0, 0, 0)  # Replace with preferred date and time

# Calculate satellite position in ECEF coordinates
geocentric = satellite.at(t)
x, y, z = geocentric.position.km

# Convert ECEF to latitude, longitude, and altitude
subpoint = geocentric.subpoint()
latitude = subpoint.latitude.degrees
longitude = subpoint.longitude.degrees
altitude = subpoint.elevation.km

print(f"Latitude {latitude}\nLongitude {longitude}\nAltitude {altitude}")