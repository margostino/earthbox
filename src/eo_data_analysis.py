import geopandas as gpd
import os
from datetime import datetime
from eodal.core.sensors.sentinel2 import Sentinel2
from eodal.mapper.feature import Feature
from eodal.mapper.filter import Filter
from eodal.mapper.mapper import Mapper, MapperConfigs
from typing import List


#%% user-inputs
# -------------------------- Collection -------------------------------
collection: str = 'sentinel2-msi'

# ------------------------- Time Range ---------------------------------
time_start: datetime = datetime(2022,3,1)  		# year, month, day (incl.)
time_end: datetime = datetime(2022,6,30)   		# year, month, day (incl.)

# ---------------------- Spatial Feature  ------------------------------
filename = '../data/sample_polygons/lake_lucerne.gpkg'
dirname = os.path.dirname(__file__)
geom = os.path.join(dirname, filename)
# geom: Path = Path('data/sample_polygons/lake_lucerne.gpkg')

# ------------------------- Metadata Filters ---------------------------
metadata_filters: List[Filter] = [
    Filter('cloudy_pixel_percentage','<', 80),
    Filter('processing_level', '==', 'Level-2A')
]

#%% query the scenes available (no I/O of scenes, this only fetches metadata)
feature = Feature.from_geoseries(gpd.read_file(geom).geometry)
mapper_configs = MapperConfigs(
    collection=collection,
    time_start=time_start,
    time_end=time_end,
    feature=feature,
    metadata_filters=metadata_filters,
)

# now, a new Mapper instance is created
mapper = Mapper(mapper_configs)
mapper.query_scenes()

#%% load the scenes available from STAC (reading bands B02 "blue", B03 "green", B04 "red")
scene_kwargs = {
    'scene_constructor': Sentinel2.from_safe,
    'scene_constructor_kwargs': {'band_selection': ['B02', 'B03', 'B04']}
}

mapper.load_scenes(scene_kwargs=scene_kwargs)

# the data loaded into `mapper.data` as a EOdal SceneCollection
mapper.data