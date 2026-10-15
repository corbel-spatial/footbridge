import os
import uuid
import zipfile
from importlib.util import find_spec
from pathlib import Path
from random import uniform

import geopandas as gpd
import pytest
import shapely

import footbridge as ft

SAMPLES = 1000


@pytest.fixture
def samples() -> int:
    return SAMPLES


@pytest.fixture
def gdb_path(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("test") / "test.gdb"


@pytest.fixture
def gdf_points() -> gpd.GeoDataFrame:
    test_points = [
        shapely.Point(uniform(-170, 170), uniform(-70, 70)) for _ in range(SAMPLES)
    ]
    test_fields = {
        "sample1": [str(uuid.uuid4()) for _ in range(SAMPLES)],
        "sample2": [str(uuid.uuid4()) for _ in range(SAMPLES)],
        "sample3": [str(uuid.uuid4()) for _ in range(SAMPLES)],
    }
    return gpd.GeoDataFrame(data=test_fields, crs="EPSG:4326", geometry=test_points)


@pytest.fixture
def fc_points(gdb_path, gdf_points) -> Path:
    ft._core.gdf_to_fc(gdf_points, gdb_path, "test_points")
    return gdb_path / "test_points"


@pytest.fixture
def fds_fc_points(tmp_path, gdf_points) -> Path:
    gdb_path = tmp_path / "fc_points.gdb"
    ft._core.gdf_to_fc(
        gdf=gdf_points,
        gdb_path=gdb_path,
        fc_name="test_points",
        feature_dataset="test_dataset",
    )
    return gdb_path / "test_dataset" / "test_points"


@pytest.fixture
def gdf_polygons(gdf_points) -> gpd.GeoDataFrame:
    polys = gdf_points.copy().to_crs("EPSG:3857")
    polys = polys.buffer(5.0)
    polys = polys.to_crs("EPSG:4326")
    return gpd.GeoDataFrame(geometry=polys)


@pytest.fixture
def gdf_lines(gdf_polygons) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(geometry=gdf_polygons.boundary, crs=gdf_polygons.crs)


@pytest.fixture
def ft_gdb(
    gdb_path, gdf_points, gdf_lines, gdf_polygons
) -> tuple[ft.GeoDatabase, Path]:
    gdb = ft.GeoDatabase()
    gdb["test_points1"] = ft.FeatureClass(gdf_points)
    assert isinstance(gdb["test_points1"], ft.FeatureClass)
    assert gdb["test_points1"].geom_type == "Point"

    gdb["test_lines1"] = ft.FeatureClass(gdf_lines)
    assert isinstance(gdb["test_lines1"], ft.FeatureClass)
    assert gdb["test_lines1"].geom_type == "LineString"

    gdb["test_polygons1"] = ft.FeatureClass(gdf_polygons)
    assert isinstance(gdb["test_polygons1"], ft.FeatureClass)
    assert gdb["test_polygons1"].geom_type == "Polygon"

    fds = ft.FeatureDataset(crs=gdf_points.crs)
    fds["test_points2"] = ft.FeatureClass(gdf_points)
    fds["test_lines2"] = ft.FeatureClass(gdf_lines)
    fds["test_polygons2"] = ft.FeatureClass(gdf_polygons)

    gdb["test_fds"] = fds
    gdb.save(gdb_path)
    return gdb, gdb_path


@pytest.fixture
def esri_gdb(tmp_path) -> Path:
    z = os.path.join("tests", "test_data.gdb.zip")
    try:
        gdb_path = os.path.abspath(os.path.join("..", z))
        assert os.path.exists(gdb_path)
    except AssertionError:  # for CI testing -- do not touch!
        gdb_path = os.path.abspath(os.path.join(".", z))
    zf = zipfile.ZipFile(gdb_path, "r")
    zf.extractall(tmp_path)
    return tmp_path / "test_data.gdb"


@pytest.fixture
def gdal_version() -> str | None:
    if find_spec("osgeo") is not None:
        from osgeo import gdal

        gdal_version = gdal.__version__
    else:
        gdal_version = None
    return gdal_version
