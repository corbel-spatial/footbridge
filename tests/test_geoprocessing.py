import geopandas as gpd
import pandas as pd
import pytest
import shapely

import footbridge as ft


def test_buffer(ft_gdb) -> None:
    gdb, _gdb_path = ft_gdb
    for fc in gdb.fcs:
        with pytest.warns(UserWarning):
            fc_buffered = ft.buffer(fc, 5.0)
            assert isinstance(fc_buffered, ft.FeatureClass)
    # fc_buffered.show()


def test_clip(ft_gdb) -> None:
    gdb, _gdb_path = ft_gdb
    fc1 = gdb["test_polygons1"]
    fc2 = gdb["test_polygons2"]
    fc_clipped = ft.clip(fc1, fc2)
    assert isinstance(fc_clipped, ft.FeatureClass)
    # fc_clipped.show()


def test_overlay(ft_gdb) -> None:
    gdb, _gdb_path = ft_gdb
    fc1 = gdb["test_polygons1"]
    fc2 = gdb["test_polygons2"]
    fc_overlaid = ft.overlay(fc1, fc2, "union")
    assert isinstance(fc_overlaid, ft.FeatureClass)
    # fc_overlaid.show()


def test_project(ft_gdb) -> None:
    gdb, _gdb_path = ft_gdb
    fc1 = gdb["test_polygons1"]

    fc_projected1 = ft.project(fc=fc1, epsg=3857, crs="EPSG:4326")
    assert isinstance(fc_projected1, ft.FeatureClass)
    assert fc_projected1.crs == "EPSG:3857"

    fc_projected2 = ft.project(fc=fc1, crs="EPSG:3857")
    assert isinstance(fc_projected2, ft.FeatureClass)
    assert fc_projected2.crs == "EPSG:3857"

    fc_projected3 = ft.project(fc=fc1, epsg=3857)
    assert isinstance(fc_projected3, ft.FeatureClass)
    assert fc_projected3.crs == "EPSG:3857"

    with pytest.raises(ValueError):
        ft.project(fc=fc1)


def test_add_fcs(gdf_points, gdf_lines, gdf_polygons) -> None:
    gdb1 = ft.GeoDatabase()
    fc1 = ft.FeatureClass(src=gdf_points)
    fc2 = ft.FeatureClass(src=gdf_lines)
    fc3 = ft.FeatureClass(src=gdf_polygons)

    gdb1["fc_1"] = fc1
    gdb1["fc_2"] = fc2
    gdb1["fc_3"] = fc3

    with pytest.raises(KeyError):
        gdb1["fc_1"] = fc1

    with pytest.raises(KeyError):
        gdb1["fc_1"] = fc1

    with pytest.raises(KeyError):
        gdb1["bad"]["fc_1"] = fc1  # ty: ignore[invalid-assignment]

    with pytest.raises(KeyError):
        gdb1["bad"]["fc_1"] = fc1  # ty: ignore[invalid-assignment]


def test_add_fds(gdf_points, gdf_lines, gdf_polygons) -> None:
    gdb1 = ft.GeoDatabase()
    fc1 = ft.FeatureClass(src=gdf_points)
    fc2 = ft.FeatureClass(src=gdf_lines)
    fc3 = ft.FeatureClass(src=gdf_polygons)
    fds = ft.FeatureDataset(crs=fc1.crs)

    gdb1["fds_1"] = fds
    assert isinstance(gdb1["fds_1"], ft.FeatureDataset)
    gdb1["fds_1"]["fc_1"] = fc1
    gdb1["fds_1"]["fc_2"] = fc2
    gdb1["fds_1"]["fc_3"] = fc3

    with pytest.raises(KeyError):
        gdb1["fc_1"] = fc1

    with pytest.raises(KeyError):
        gdb1["fc_1"] = fc1

    with pytest.raises(KeyError):
        gdb1["fds_1"]["fc_1"] = fc1

    with pytest.raises(KeyError):
        gdb1["fds_1"]["fc_1"] = fc1

    with pytest.raises(KeyError):
        gdb1["bad"]["fc_1"] = fc1  # ty: ignore[invalid-assignment]

    with pytest.raises(KeyError):
        gdb1["fds1"]["bad"]["fc_1"] = fc1  # ty: ignore[invalid-argument-type, invalid-assignment]


def test_iters(ft_gdb) -> None:
    gdb, _gdb_path = ft_gdb

    for fds in gdb.values():
        for fc_name, fc in fds.items():
            assert isinstance(fc_name, str)
            assert isinstance(fc, ft.FeatureClass)

    for fds in gdb.fds_dict.values():
        for fc_name, fc in fds.items():
            assert isinstance(fc_name, str)
            assert isinstance(fc, ft.FeatureClass)

    for fc_name, fc in gdb.fc_dict.items():
        assert isinstance(fc_name, str)
        assert isinstance(fc, ft.FeatureClass)

    for fds in gdb:
        this_fds = gdb[fds]
        for fc_name, fc in this_fds.fc_dict.items():
            assert isinstance(fc_name, str)
            assert isinstance(fc, ft.FeatureClass)


def test_sanitize_gdf_geometry(gdf_points, gdf_lines, gdf_polygons) -> None:
    with pytest.raises(TypeError):
        ft._core.sanitize_gdf_geometry(pd.DataFrame())  # ty: ignore[invalid-argument-type]

    with pytest.raises(TypeError):
        ft._core.sanitize_gdf_geometry(
            gpd.GeoDataFrame(
                geometry=[
                    shapely.GeometryCollection(),
                    shapely.Point(),
                ]
            )
        )

    gdf1 = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(
            [
                shapely.Point(),
                shapely.Point([0, 1]),
                shapely.MultiPoint([[0, 1], [0, 2]]),
                None,
            ]
        )
    )
    gdf1_geom_type, gdf1 = ft._core.sanitize_gdf_geometry(gdf1)
    assert gdf1_geom_type == "MultiPoint"

    gdf2 = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(
            [
                shapely.LineString(),
                shapely.LineString([[0, 1], [0, 2]]),
                shapely.MultiLineString([[[0, 1], [0, 2]], [[0, 4], [0, 5]]]),
                None,
            ]
        )
    )
    gdf2_geom_type, gdf2 = ft._core.sanitize_gdf_geometry(gdf2)
    assert gdf2_geom_type == "MultiLineString"

    gdf3 = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(
            [
                shapely.LinearRing(),
                shapely.LinearRing([[0, 1], [1, 1], [1, 0], [0, 0]]),
                shapely.MultiLineString([[[0, 1], [0, 2]], [[0, 4], [0, 5]]]),
                None,
            ]
        )
    )
    gdf3_geom_type, gdf3 = ft._core.sanitize_gdf_geometry(gdf3)
    assert gdf3_geom_type == "MultiLineString"

    gdf4 = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(
            [
                shapely.LineString(),
                shapely.LineString([[0, 1], [0, 2]]),
                shapely.LinearRing(),
                shapely.LinearRing([[0, 1], [1, 1], [1, 0], [0, 0]]),
                shapely.MultiLineString([[[0, 0], [1, 2]], [[4, 4], [5, 6]]]),
                None,
            ]
        )
    )
    gdf4_geom_type, gdf4 = ft._core.sanitize_gdf_geometry(gdf4)
    assert gdf4_geom_type == "MultiLineString"

    gdf5 = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(
            [
                shapely.LineString(),
                shapely.LineString([[0, 1], [0, 2]]),
                shapely.LinearRing(),
                shapely.LinearRing([[0, 1], [1, 1], [1, 0], [0, 0]]),
                None,
            ]
        )
    )
    gdf5_geom_type, gdf5 = ft._core.sanitize_gdf_geometry(gdf5)
    assert gdf5_geom_type == "LineString"

    gdf6 = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(
            [
                shapely.Polygon(),
                shapely.Polygon([[0, 1], [1, 1], [1, 0], [0, 0]]),
                shapely.MultiPolygon(
                    [
                        (
                            ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)),
                            [((0.1, 0.1), (0.1, 0.2), (0.2, 0.2), (0.2, 0.1))],
                        )
                    ]
                ),
                None,
            ]
        )
    )
    gdf6_geom_type, gdf6 = ft._core.sanitize_gdf_geometry(gdf6)
    assert gdf6_geom_type == "MultiPolygon"

    with pytest.raises(TypeError):
        gdf7 = gpd.GeoDataFrame(
            geometry=gpd.GeoSeries(
                [
                    shapely.LineString(),
                    shapely.LinearRing(),
                    shapely.MultiLineString(),
                    None,
                    shapely.Point(),
                ]
            )
        )
        ft._core.sanitize_gdf_geometry(gdf7)
