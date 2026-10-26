import warnings
from typing import Literal

import geopandas as gpd
import shapely

from ._core import FeatureClass


def buffer(fc: FeatureClass, distance: float, **kwargs: dict) -> FeatureClass:
    """
    Buffer a feature class by a specified distance

    Wraps geopandas.GeoSeries.buffer()

    :param fc: Input feature class to buffer
    :type fc: FeatureClass
    :param distance: Buffer distance in the units of the feature class's CRS
    :type distance: float
    :param kwargs: Keyword arguments of `geopandas.GeoSeries.buffer <https://geopandas.org/docs/reference/api/geopandas.GeoSeries.buffer.html>`__
    :type kwargs: dict

    :return: The buffered feature class
    :rtype: FeatureClass

    """
    gdf = fc.gdf.copy(deep=True)

    if not fc.crs or fc.crs.is_geographic:
        warnings.warn(
            "Geometry is in an unspecified or geographic coordinate reference system, which can produce inaccurate "
            "spatial processing results. Consider using 'footbridge.project()' first.",
            UserWarning,
        )
    with warnings.catch_warnings():  # hide geopandas warning about geographic CRS
        warnings.simplefilter("ignore")
        new_geom = gdf.buffer(distance=distance, **kwargs)  # ty: ignore[invalid-argument-type]

    gdf = gdf.set_geometry(new_geom)

    return FeatureClass(gdf)


def clip(fc: FeatureClass, mask_fc: FeatureClass, **kwargs: dict) -> FeatureClass:
    """
    Clip a feature class by a mask feature class.

    Wraps geopandas.clip()

    :param fc: Input feature class to be clipped
    :type fc: FeatureClass
    :param mask_fc: Feature class to use as the clipping boundary
    :type mask_fc: FeatureClass
    :param kwargs: Keyword arguments of `geopandas.clip <https://geopandas.org/docs/reference/api/geopandas.clip.html>`__
    :type kwargs: dict
    :return: The clipped feature class
    :rtype: FeatureClass
    """
    gdf = gpd.clip(gdf=fc._data, mask=mask_fc._data, **kwargs)  # ty: ignore[invalid-argument-type]
    return FeatureClass(gdf)


def overlay(
    fc1: FeatureClass,
    fc2: FeatureClass,
    how: Literal[
        "intersection", "union", "identity", "symmetric_difference", "difference"
    ] = "intersection",
    **kwargs: dict | None,
) -> FeatureClass:
    """
    Perform a spatial overlay between two FeatureClasses

    Wraps geopandas.overlay(), see the documentation for more details on the different `overlay methods <https://geopandas.org/en/stable/docs/user_guide/set_operations.html>`__

    :param fc1: First input feature class to be used in the overlay operation
    :type fc1: FeatureClass
    :param fc2: Second input feature class
    :type fc2: FeatureClass
    :param how: Method of spatial overlay
    :type how: str, defaults to :code:`intersection`
    :param kwargs: Keyword arguments of `geopandas.overlay <https://geopandas.org/docs/reference/api/geopandas.overlay.html>`__
    :type kwargs: dict
    :return: The clipped feature class
    :rtype: FeatureClass
    """
    gdf = gpd.overlay(df1=fc1._data, df2=fc2._data, how=how, **kwargs)  # ty: ignore[invalid-argument-type]
    return FeatureClass(gdf)


def project(
    fc: FeatureClass,
    epsg: int | None = None,
    crs: str | None = None,
) -> FeatureClass:
    """
    Transform geometries to a new coordinate reference system.

    Wraps geopandas.GeoDataFrame.to_crs().

    :param fc: Input feature class to be projected
    :type fc: FeatureClass
    :param epsg: EPSG code for the output feature class
    :type epsg: int
    :param crs: CRS for the output feature class, like "EPSG:4326" or a WKT definition, ignored if `epsg` is present
    :type crs: str
    :return: The reprojected feature class
    :rtype: FeatureClass
    """
    if epsg is None and crs is None:
        raise ValueError("EPSG or CRS must be provided")

    if epsg is not None:
        gdf = fc._data.to_crs(crs=None, epsg=epsg, inplace=False)
    else:
        gdf = fc._data.to_crs(crs=crs, epsg=None, inplace=False)  # ty: ignore[no-matching-overload]

    return FeatureClass(gdf)


def rotate(
    fc: FeatureClass,
    angle: float,
    origin: Literal["center", "centroid"]
    | tuple[float, float]
    | shapely.Point = "center",
    use_radians: bool = False,
) -> FeatureClass:
    """
    Rotate features around a point location.

    Wraps geopandas.GeoSeries.rotate().


    :param fc: Input feature class to be projected
    :type fc: FeatureClass
    :param angle: Rotation angle (defaults to degrees)
    :type angle: float
    :param origin: The origin around which to rotate (defaults to "center")
    :type origin: Literal["center", "centroid"] | tuple[float, float] | shapely.Point
    :param use_radians: Whether to use radians instead of degrees
    :type use_radians: bool
    :return: The rotated feature class
    :rtype: FeatureClass
    """
    if fc.geometry is None:
        raise RuntimeError()

    new_geom = fc.geometry.rotate(angle=angle, origin=origin, use_radians=use_radians)
    gdf = gpd.GeoDataFrame(fc, geometry=new_geom)
    return FeatureClass(gdf)
