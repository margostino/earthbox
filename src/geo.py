import os
import pandas as pd
import geopandas as gpd
import os

filename = '../data/karnataka.gpkg'
dirname = os.path.dirname(__file__)
path = os.path.join(dirname, filename)

roads_gdf = gpd.read_file(path, layer='karnataka_major_roads')

print(roads_gdf.info())

print("Geometry")
print(roads_gdf.geometry)

filtered = roads_gdf[roads_gdf['ref'].str.match('^NH') == True]
print(filtered.head())

print("Projections")
print(filtered.crs)

roads_reprojected = filtered.to_crs('EPSG:32643')
print(roads_reprojected.crs)

roads_reprojected['length'] = roads_reprojected['geometry'].length
total_length = roads_reprojected['length'].sum()
print('Total length of national highways in the state is {} KM'.format(total_length/1000))

districts_gdf = gpd.read_file(path, layer='karnataka_districts')
print(districts_gdf.head())

districts_reprojected = districts_gdf.to_crs('EPSG:32643')
joined = gpd.sjoin(roads_reprojected, districts_reprojected, how='left', predicate='intersects')
print(joined.head())

results = joined.groupby('DISTRICT')['length'].sum()/1000
print(results)