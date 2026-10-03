from importlib import metadata

import pandas as pd

from . import utils as utils
from ._core import FeatureClass as FeatureClass
from ._core import FeatureDataset as FeatureDataset
from ._core import GeoDatabase as GeoDatabase
from ._core import list_datasets as list_datasets
from ._core import list_layers as list_layers
from ._geoprocessing import buffer as buffer
from ._geoprocessing import clip as clip
from ._geoprocessing import overlay as overlay

__version__ = metadata.version("footbridge")

pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", None)
