import os
import re

import geojson
import pandas as pd
import xmltodict

from ._core import fc_to_gdf, list_layers, list_datasets


# Check for optional install of GDAL>=3.8 for raster support
try:
    from osgeo import gdal  # noqa # fmt: skip

    _gdal_installed = True
    _gdal_version = gdal.__version__
except ModuleNotFoundError:
    _gdal_installed = False
    _gdal_version = None
if _gdal_version:
    _version_split = _gdal_version.split(".")
    if int(_version_split[0]) < 3 or int(_version_split[1]) < 8:
        raise ImportError(
            "GDAL version must be >=3.8, please upgrade to a newer version"
        )

pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", None)


def fc_to_json(
    gdb_path: os.PathLike | str,
    fc_name: str,
    fp: None | os.PathLike | str = None,
    indent: None | int = None,
    **kwargs: dict,
) -> None | geojson.FeatureCollection:
    """Wraps geopandas.GeoDataFrame.to_json()"""
    gdf = fc_to_gdf(gdb_path=gdb_path, fc_name=fc_name)
    gjs = geojson.loads(gdf.to_json(**kwargs))

    if fp:
        fp = str(fp)
        if not fp.endswith(".geojson") or not fp.endswith(".json"):
            fp += ".geojson"
        with open(fp, "w") as f:
            geojson.dump(gjs, f, indent=indent)
        return None
    else:
        return gjs


def fc_to_parquet(
    gdb_path: os.PathLike | str, fc_name: str, fp: os.PathLike | str, **kwargs: dict
):
    """Wraps geopandas.GeoDataFrame.to_parquet()"""
    gdf = fc_to_gdf(gdb_path=gdb_path, fc_name=fc_name)

    if not fp.endswith(".parquet"):
        fp += ".parquet"

    gdf.to_parquet(fp, **kwargs)


def fc_to_shp(
    gdb_path: os.PathLike | str,
    fc_name: str,
    fp: None | os.PathLike | str,
    **kwargs: dict,
) -> None:
    """Wraps geopandas.GeoDataFrame.to_file(filename, driver="ESRI Shapefile")"""
    gdf = fc_to_gdf(gdb_path=gdb_path, fc_name=fc_name)

    if not fp.endswith(".shp"):
        fp += ".shp"

    if "driver" in kwargs:
        del kwargs["driver"]

    gdf.to_file(fp, **kwargs)


def get_info(gdb_path: os.PathLike | str) -> dict:
    """
    Return a dictionary view of the contents of a file geodatabase on disk.

    :param gdb_path: Path to the geodatabase
    :type gdb_path: os.PathLike | str
    :return: A dictionary where keys represent dataset types, and values are nested
        dictionaries with dataset names and their corresponding metadata.
    :rtype: dict

    """
    gdb_path = os.path.abspath(gdb_path)
    if not os.path.exists(gdb_path):
        raise FileNotFoundError(gdb_path)
    if not os.path.isdir(gdb_path):
        raise TypeError(f"{gdb_path} is not a directory")

    result = dict()

    with open(os.path.join(os.path.abspath(gdb_path), "a00000004.gdbtable"), "rb") as f:
        gdbtable = f.read()

        for root_name in [
            "DEFeatureClassInfo",
            "DEFeatureDataset",
            "DERasterDataset",
            "DETableInfo",
            "DEWorkspace",
            "ESRI_ItemInformation",
            "metadata",
            "typens:DEFeatureClassInfo",
            "typens:DEFeatureDataset",
            "typens:DERasterDataset",
            "typens:DETableInfo",
            "typens:DEWorkspace",
            "typens:ESRI_ItemInformation",
            "typens:metadata",
        ]:
            start_pos = 0
            while True:
                start_pos = gdbtable.find(bytes(f"<{root_name} ", "utf-8"), start_pos)
                end_pos = gdbtable.find(bytes(f"</{root_name}>", "utf-8"), start_pos)
                if start_pos == -1 or end_pos == -1:  # stop loop at the end of the file
                    break
                end_pos = end_pos + len(f"</{root_name}>")
                match = gdbtable[start_pos:end_pos].decode("utf-8")
                start_pos = end_pos

                xml_dict = xmltodict.parse(match)[root_name]

                root_name = (
                    root_name.replace("typens:", "")
                    .replace("DE", "")
                    .replace("Table", "")
                    .replace("Info", "")
                )
                if root_name not in result:
                    result[root_name] = list()
                result[root_name].append(xml_dict)

    return result



def list_rasters(gdb_path: os.PathLike | str) -> list[str]:
    """
    Lists all raster datasets within a specified file geodatabase on disk.

    If the geodatabase is empty or not valid, an empty list is returned.

    :param gdb_path: The path to the geodatabase file
    :type gdb_path: os.PathLike | str
    :return: A list of raster datasets in the specified geodatabase file
    :rtype: list[str]

    Reference:
        * https://github.com/rouault/dump_gdbtable/wiki/FGDB-Spec

    """
    gdb_path = os.path.abspath(gdb_path)
    if not os.path.exists(gdb_path):
        raise FileNotFoundError(gdb_path)
    if not os.path.isdir(gdb_path):
        raise TypeError(f"{gdb_path} is not a directory")

    gdbtable = os.path.join(gdb_path, "a00000004.gdbtable")
    fcs = list_layers(gdb_path)
    fds = list_datasets(gdb_path)

    # get \dataset paths
    with open(gdbtable, "r", encoding="MacRoman") as f:
        contents = f.read()
    rasters = re.findall(
        r"<CatalogPath>\\([a-zA-Z0-9_]+)</CatalogPath>",
        contents,
    )

    # remove the feature classes
    for fc in fcs:
        if fc in rasters:
            rasters.remove(fc)
    for fd in fds.keys():
        if fd in rasters:
            rasters.remove(fd)
    return rasters


# PYNoinspection
def raster_to_tif(
    gdb_path: os.PathLike | str,
    raster_name: str,
    tif_path: None | os.PathLike | str = None,
    options: None | dict = None,
):
    """
    Converts a raster stored in a file geodatabase to a GeoTIFF file.

    Reads the raster from the input geodatabase, including masking data, and saves it as a GeoTIFF
    file at the specified output path.

    :param gdb_path: The path to the input file geodatabase containing the raster
    :type gdb_path: os.PathLike | str
    :param raster_name: The name of the raster in the geodatabase to be converted
    :type raster_name: str
    :param tif_path: The optional path where the GeoTIFF file should be saved. If not
        provided, the output GeoTIFF file will be saved with the same name as the raster
        in the GDB directory. Defaults to None.
    :type tif_path: os.PathLike | str, optional
    :param options: Additional keyword arguments for writing the GeoTIFF file, see the documentation: https://gdal.org/en/stable/drivers/raster/gtiff.html#creation-options
    :type options: dict, optional
    """
    if not _gdal_installed:
        raise ImportError(
            "GDAL not installed, footbridge cannot support raster operations"
        )

    gdb_path = os.path.abspath(gdb_path)
    if not os.path.exists(gdb_path):
        raise FileNotFoundError(gdb_path)
    if not os.path.isdir(gdb_path):
        raise TypeError(f"{gdb_path} is not a directory")

    if tif_path is None:
        tif_path = os.path.join(os.path.dirname(gdb_path), raster_name + ".tif")

    if not tif_path.endswith(".tif"):
        tif_path += ".tif"

    gdal.UseExceptions()
    with gdal.Open(f"OpenFileGDB:{gdb_path}:{raster_name}") as raster:
        tif_drv: gdal.Driver = gdal.GetDriverByName("GTiff")
        if options:
            tif_drv.CreateCopy(tif_path, raster, strict=0, options=options)
        else:
            tif_drv.CreateCopy(tif_path, raster, strict=0)
