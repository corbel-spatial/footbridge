from importlib.metadata import version as _version

from . import utils as utils
from ._core import FeatureClass as FeatureClass
from ._core import FeatureDataset as FeatureDataset
from ._core import GeoDatabase as GeoDatabase
from ._core import GeometryType as GeometryType
from ._core import list_datasets as list_datasets
from ._core import list_layers as list_layers
from ._geoprocessing import buffer as buffer
from ._geoprocessing import clip as clip
from ._geoprocessing import overlay as overlay
from ._geoprocessing import project as project
from ._geoprocessing import rotate as rotate

__version__ = _version("footbridge")
