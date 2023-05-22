import geopandas as gpd
import pandas as pd

# Load a GeoDataFrame containing regions in Ghana
regions = gpd.read_file("../data/World_Countries_(Generalized)/World_Countries__Generalized_.shp")
print(regions.crs)