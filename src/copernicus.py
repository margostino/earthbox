import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
import rasterio
import seaborn as sns
import yaml
from rasterio.io import MemoryFile
from rasterio.mask import mask
from scipy.interpolate import RectBivariateSpline
from sentinelsat import SentinelAPI
from shapely.geometry import Polygon
from shapely.ops import transform

with open("../config.yml", 'r') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
    username = config['copernicus']['username']
    password = config['copernicus']['password']


def normalize(x):
    return (x - np.mean(x)) / np.std(x)


def score(pixel_signature, target_spectral_signature):
    return np.mean((pixel_signature - target_spectral_signature) ** 2)


def get_object_db(osm_data_dir, base_name, sub_polygon=None, remove_non_polygons=True, swap_coordinates=False):
    shapes_filename = os.path.join(osm_data_dir, "gis_osm_" + base_name + "_free_1.shp")
    shapes = gpd.read_file(shapes_filename)
    shapes["geometry"] = shapes["geometry"].convex_hull

    print("Area shape count:", shapes.shape[0])

    if sub_polygon:
        shapes = shapes[shapes["geometry"].within(sub_polygon)]
        print("Sub-area shape count:", shapes.shape[0])

    if remove_non_polygons:
        shapes = shapes[shapes["geometry"].type == "Polygon"].copy()
        print("After removing non-closable geometries:", shapes.shape[0])

    if swap_coordinates:
        coordinate_swap = lambda p: Polygon([(y, x) for x, y in p.exterior.coords])
        shapes["geometry"] = shapes["geometry"].map(coordinate_swap)

    return shapes


def reproject(polygons, proj_from, proj_to):
    proj_from = pyproj.Proj(proj_from)
    proj_to = pyproj.Proj(proj_to)

    projection = pyproj.Transformer.from_proj(proj_from, proj_to)
    return [transform(projection.transform, p) for p in polygons]


def crop_memory_tiff_file(mem_file, polygons, crop):
    polygons = reproject(polygons, "EPSG:4326", mem_file.crs)
    result_image, result_transform = mask(mem_file, polygons, crop=crop)

    profile = mem_file.profile
    profile.update(width=result_image.shape[1],
                   height=result_image.shape[2],
                   transform=result_transform)

    result_f = MemoryFile().open(**profile)
    result_f.write(result_image)

    return result_f


def get_tallinn_polygon(swap_coordinates=False):
    tln_points = [
        (59.455947169131946, 24.532626930520898),
        (59.47862155366181, 24.564212623880273),
        (59.49535595077547, 24.69810849790371),
        (59.51138530046753, 24.825137916849023),
        (59.459087606762346, 24.907535377786523),
        (59.4147455486766, 24.929508034036523),
        (59.39832075950073, 24.844363991067773),
        (59.37664183245853, 24.814151588724023),
        (59.35249898189222, 24.75304013852871),
        (59.32798867805195, 24.573825660989648)
    ]

    # Copernicus hub likes polygons in lng/lat format
    return Polygon([(y, x) if swap_coordinates else (x, y) for x, y in tln_points])


def download():
    hub = SentinelAPI(username, password, "https://scihub.copernicus.eu/dhus")

    data_products = hub.query(
        get_tallinn_polygon(swap_coordinates=True),  # which area interests you
        date=("20200101", "20200420"),
        cloudcoverpercentage=(0, 10),  # we don't want clouds
        platformname="Sentinel-2",
        processinglevel="Level-2A"  # more processed, ready to use data
    )

    data_products = hub.to_geodataframe(data_products)
    # we want to avoid downloading overlapping images, so selecting by this keyword
    data_products = data_products[data_products["title"].str.contains("T35VLF")]

    hub.download("16082e6b-b32c-4cdc-8e0d-3d64f2432b88", "../data/copernicus/sentinel2")


def extrapolate(arr, target_dim):
    x = np.array(range(arr.shape[0]))
    y = np.array(range(arr.shape[1]))
    z = arr
    xx = np.linspace(x.min(), x.max(), target_dim[0])
    yy = np.linspace(y.min(), y.max(), target_dim[1])

    new_kernel = RectBivariateSpline(x, y, z, kx=2, ky=2)
    result = new_kernel(xx, yy)

    return result


def get_material_reflectance_spectrum(spectral_library_dir, material_name, bands, normalize):
    all_bands = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B10", "B11", "B12"]
    material_dir = os.path.join(spectral_library_dir, "ASCIIdata/ASCIIdata_splib07b_rsSentinel2")

    for root, _, files in os.walk(material_dir):
        for file in files:
            if "S07SNTL2_" + material_name + "_" in file:
                full_file = os.path.join(root, file)
                df = pd.read_csv(full_file)

                spectrum = df[df.columns[0]].values
                needed_band_idx = [all_bands.index(b) for b in bands]
                spectrum = spectrum[needed_band_idx]

                if normalize:
                    spectrum = (spectrum - np.mean(spectrum)) / np.std(spectrum)

                return spectrum


src_root_data_dir = "../data/copernicus/sentinel2"
tiff_root_data_dir = "../data/copernicus/tiff_data"

bands = ["B02", "B03", "B04", "B08", "B8A", "B11", "B12"]
resolutions = ["R10m", "R10m", "R10m", "R10m", "R20m", "R20m", "R20m"]
bands_and_resolutions = list(zip(bands, resolutions))

target_dim = (10980, 10980)

# src_data_dirs = []
#
# for x in os.listdir(src_root_data_dir):
#     date = x.split("_")[2].split("T")[0]
#     src_data_dir = glob.glob(os.path.join(src_root_data_dir, x, "GRANULE/*/IMG_DATA"))[0]
#
#     src_data_dirs.append((date, src_data_dir))
#
# src_data_dirs = sorted(src_data_dirs, key=lambda x: x[0])
#
# for date, src_data_dir in src_data_dirs:
#     tiff_file = os.path.join(tiff_root_data_dir, date + ".tiff")
#
#     if os.path.exists(tiff_file):
#         continue
#
#     tiff_f = None
#
#     for i, (band, resolution) in enumerate(bands_and_resolutions, start=1):
#         band_file = glob.glob(os.path.join(src_data_dir, resolution, "*_" + band + "_*.jp2"))[0]
#
#         band_f = rasterio.open(band_file, driver="JP2OpenJPEG")
#         band_data = band_f.read(1)
#
#         if band_data.shape[0] < target_dim[0] and band_data.shape[1] < target_dim[1]:
#             print("Extrapolating", band_data.shape, "to", target_dim)
#             band_data = extrapolate(band_data, target_dim).astype(band_f.dtypes[0])
#
#         if tiff_f is None:
#             profile = band_f.profile
#             profile.update(driver="Gtiff", count=len(bands_and_resolutions))
#             tiff_f = MemoryFile().open(**profile)
#
#         print("Writing band {} for date {}".format(band, date))
#         tiff_f.write(band_data, i)
#
#         band_f.close()
#
#     tiff_f_cropped = crop_memory_tiff_file(tiff_f, [get_tallinn_polygon()], crop=True)
#
#     tiff_f.close()
#     tiff_f = None
#
#     with rasterio.open(tiff_file, "w", **tiff_f_cropped.profile) as f:
#         f.write(tiff_f_cropped.read())
#
#     tiff_f_cropped.close()

osm_data_root_dir = "../data/copernicus/osm"
tiff_file = os.path.join(tiff_root_data_dir, "20200407.tiff")

shapes = get_object_db(osm_data_root_dir, "landuse_a",
                       get_tallinn_polygon(swap_coordinates=True),
                       remove_non_polygons=True,
                       swap_coordinates=True)

shapes = shapes[shapes["fclass"].isin(["forest", "park"])]

with rasterio.open(tiff_file, driver="Gtiff") as tiff_f:
    tiff_data = tiff_f.read()
    tiff_profile = tiff_f.profile

    roads = shapes["geometry"].values
    roads = reproject(roads, "EPSG:4326", tiff_profile["crs"])

    result_data, result_transform = mask(tiff_f, roads, crop=True)

print(tiff_data.shape)
print(result_data.shape)

fig, ax = plt.subplots(figsize=(12, 12))
ax.matshow(result_data[5])
# plt.show()

target_spectrum = get_material_reflectance_spectrum("../data/copernicus/materials/usgs_splib07",
                                                    "Sheet_Metal",
                                                    bands=bands,
                                                    normalize=True)
plt.plot(target_spectrum)
# plt.show()

tiff_data = np.apply_along_axis(normalize, 0, tiff_data)
heatmap_mse = np.apply_along_axis(lambda x: score(x, target_spectrum), 0, tiff_data)

sns.distplot(heatmap_mse, kde=False)

heatmap_mse_cropped = np.vectorize(lambda x: x if x < 0.2 else np.nan)(heatmap_mse)

fig, ax = plt.subplots(figsize=(12, 12))
ax.matshow(heatmap_mse_cropped[750:1250, 1100:1600])
plt.show()
