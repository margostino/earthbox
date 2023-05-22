import geopandas as gpd
import pandas as pd
import datetime
from pyorbital.orbital import Orbital
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


# # Load a GeoDataFrame containing regions in Ghana
# regions = gpd.read_file("../data/World_Countries_(Generalized)/World_Countries__Generalized_.shp")
# print(regions.crs)
#
# satellite_df = pd.read_csv("../data/last_30_days_launches.csv")
#
# # filter dataset where column "satellite" is equal to "Sentinel-2A"
# satellite_df = satellite_df[satellite_df["Satellite"] == "LUMELITE-4"]
# print(satellite_df.head())

tle_filepath = "../data/last_30_days_launches.tle"
satellite = Orbital("LIGHTCUBE", tle_file=tle_filepath)
start_time = datetime.datetime.utcnow()
end_time = start_time + datetime.timedelta(hours=1)  # Adjust the duration as needed

# Define the time interval
time_resolution = datetime.timedelta(seconds=10)
now = datetime.datetime.utcnow()
# Generate the time points
time_points = []
current_time = start_time
while current_time < end_time:
    time_points.append(current_time)
    current_time += time_resolution

# Get the latitudes and longitudes for each time point
# latitudes, longitudes, _ = satellite.get_lonlatalt(time_points)
latitudes, longitudes, _ = satellite.get_lonlatalt(now)

# Create a Basemap instance
m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='l')

# Draw coastlines, countries, and other map features
m.drawcoastlines()
m.drawcountries()
m.drawmapboundary()

# Convert latitudes and longitudes to map coordinates
x, y = m(longitudes, latitudes)

# Plot the trajectory points
m.plot(x, y, linestyle='-', linewidth=2)

# Show the plot
plt.show()

