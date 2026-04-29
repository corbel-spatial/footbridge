import os

import geojson
import geopandas as gpd
import pyogrio
import pytest
import shapely

import footbridge as ft


def test_fc_to_json(tmp_path, ft_gdb):
    gdb, gdb_path = ft_gdb
    for fc_name, fc in gdb.fc_dict.items():
        gjs = ft.utils.fc_to_json(gdb_path, fc_name)
        assert isinstance(gjs, geojson.FeatureCollection)

    for fc_name, fc in gdb.fc_dict.items():
        fp = str(tmp_path / fc_name) + ".geojson"
        ft.utils.fc_to_json(gdb_path, fc_name, fp, indent=2)

        fp = str(tmp_path / fc_name)
        ft.utils.fc_to_json(gdb_path, fc_name, fp, indent=2)


def test_fc_to_parquet(tmp_path, ft_gdb):
    gdb, gdb_path = ft_gdb
    for fc_name, fc in gdb.fc_dict.items():
        fp = str(tmp_path / fc_name) + ".parquet"
        ft.utils.fc_to_parquet(gdb_path, fc_name, fp)

        fp = str(tmp_path / fc_name)
        ft.utils.fc_to_parquet(gdb_path, fc_name, fp)


def test_fc_to_shp(tmp_path, ft_gdb):
    gdb, gdb_path = ft_gdb
    for fc_name, fc in gdb.fc_dict.items():
        fp = str(tmp_path / fc_name) + ".shp"
        ft.utils.fc_to_shp(gdb_path, fc_name, fp)

        fp = str(tmp_path / fc_name)
        ft.utils.fc_to_shp(gdb_path, fc_name, fp)


def test_fc_to_gdf(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fc in ft.utils.list_layers(gdb_path):
        gdf = ft.utils.fc_to_gdf(gdb_path, fc)
        assert isinstance(gdf, gpd.GeoDataFrame)
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        ft.utils.fc_to_gdf(gdb_path, 0)


def test_gdf_to_fc(ft_gdb):
    gdb, gdb_path = ft_gdb
    count = 0
    for fds in gdb.values():
        for fc_name, fc in fds.items():
            gdf = fc.gdf
            ft._core.gdf_to_fc(gdf, gdb_path, fc_name + "_copy")
            ft._core.gdf_to_fc(gdf, gdb_path, fc_name, overwrite=True)
            count += 2
    assert count == len(ft.utils.list_layers(gdb_path))

    with pytest.raises(FileNotFoundError):
        ft._core.gdf_to_fc(gpd.GeoDataFrame(), "thisfiledoesnotexist", "test")

    # noinspection PyUnresolvedReferences
    with pytest.raises(pyogrio.errors.GeometryError):
        for fc_name, fc in gdb.fc_dict.items():
            ft._core.gdf_to_fc(
                gdf=fc.gdf,
                gdb_path=gdb_path,
                fc_name=fc_name,
                feature_dataset=None,
                geometry_type="no",
                overwrite=True,
            )

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        ft._core.gdf_to_fc(list(), gdb_path, "test")

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        ft._core.gdf_to_fc(gpd.GeoDataFrame, "test", "test", overwrite="yes")

    ft._core.gdf_to_fc(
        gpd.GeoSeries([shapely.LineString([(0, 1), (1, 1)])]),
        gdb_path,
        "geoseries",
        overwrite=True,
    )


def test_get_info(tmp_path, esri_gdb):
    gdb = ft.GeoDatabase(
        contents={
            "fds": ft.FeatureDataset(
                {
                    "fc": ft.FeatureClass(
                        gpd.GeoDataFrame(
                            {"col1": ["c"]},
                            geometry=[shapely.LineString([(0, 1), (1, 1)])],
                            crs="WGS 84",
                        ),
                    )
                }
            )
        }
    )
    gdb_path = tmp_path / "out.gdb"
    gdb.save(gdb_path, overwrite=True)
    info = ft.utils.get_info(gdb_path)
    assert isinstance(info, dict)

    info = ft.utils.get_info(esri_gdb)
    assert isinstance(info, dict)

    with pytest.raises(FileNotFoundError):
        ft.utils.get_info("bad_path")

    with pytest.raises(TypeError):
        try:  # pytest
            ft.utils.get_info("pyproject.toml")
        except FileNotFoundError:  # coverage
            ft.utils.get_info(os.path.join("..", "pyproject.toml"))


def test_list_datasets(ft_gdb, esri_gdb):
    gdb, gdb_path = ft_gdb
    fds1 = ft.utils.list_datasets(gdb_path)
    assert len(fds1) == 2
    for k, v in fds1.items():
        assert isinstance(k, str) or k is None
        assert isinstance(v, list)

    fds3 = ft.utils.list_datasets(esri_gdb)
    assert isinstance(fds3, dict)
    assert len(fds3) == 0

    with pytest.raises(FileNotFoundError):
        ft.utils.list_datasets("bad_path")

    with pytest.raises(TypeError):
        try:  # pytest
            ft.utils.list_datasets("pyproject.toml")
        except FileNotFoundError:  # coverage
            ft.utils.list_datasets(os.path.join("..", "pyproject.toml"))


def test_list_layers(ft_gdb):
    gdb, gdb_path = ft_gdb
    lyrs = ft.utils.list_layers(gdb_path)
    assert len(lyrs) == 6

    with pytest.raises(FileNotFoundError):
        ft.utils.list_layers("bad_path")

    with pytest.raises(TypeError):
        try:  # pytest
            ft.utils.list_layers("pyproject.toml")
        except FileNotFoundError:  # coverage
            ft.utils.list_layers(os.path.join("..", "pyproject.toml"))


def test_list_rasters(ft_gdb, esri_gdb):
    rasters = ft.utils.list_rasters(esri_gdb)
    assert len(rasters) == 1
    for raster in rasters:
        assert isinstance(raster, str)

    gdb, gdb_path = ft_gdb
    rasters = ft.utils.list_rasters(gdb_path)
    assert len(rasters) == 0

    with pytest.raises(FileNotFoundError):
        ft.utils.list_rasters("bad_path")

    with pytest.raises(TypeError):
        try:  # pytest
            ft.utils.list_rasters("pyproject.toml")
        except FileNotFoundError:  # coverage
            ft.utils.list_rasters(os.path.join("..", "pyproject.toml"))


def test_raster_to_tif(tmp_path, capsys, esri_gdb, gdal_version):
    if not gdal_version:
        with pytest.raises(ImportError):
            ft.utils.raster_to_tif(
                gdb_path=esri_gdb,
                raster_name="random_raster",
                tif_path=None,
            )
    else:
        with capsys.disabled():
            print("\n\t*** GDAL installed:", gdal_version, "***")
        ft.utils.raster_to_tif(
            gdb_path=esri_gdb,
            raster_name="random_raster",
            tif_path=None,
        )

        tif_path = tmp_path / "test"
        ft.utils.raster_to_tif(
            gdb_path=esri_gdb,
            raster_name="random_raster",
            tif_path=str(tif_path),
        )

        tif_path = tmp_path / "test.tif"
        ft.utils.raster_to_tif(
            gdb_path=esri_gdb,
            raster_name="random_raster",
            tif_path=str(tif_path),
            options={"TILED": "YES"},
        )


def test_version():
    version = ft.__version__
    assert isinstance(version, str)
    assert "." in version
