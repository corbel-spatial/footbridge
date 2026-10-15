import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import shapely
from pyproj.crs import CRS
from scipy.stats import geom

import footbridge as ft


def test_instantiate_fc(fc_points, fds_fc_points) -> None:
    with pytest.raises(TypeError):
        _ = ft.FeatureClass(0)

    fc1 = ft.FeatureClass(fc_points)
    assert isinstance(fc1.gdf, gpd.GeoDataFrame)

    fc2 = ft.FeatureClass(fds_fc_points)
    assert isinstance(fc2.gdf, gpd.GeoDataFrame)

    fc3 = ft.FeatureClass(gpd.GeoSeries([shapely.Point(0, 1)]))
    assert isinstance(fc3.gdf, gpd.GeoDataFrame)

    fc4 = ft.FeatureClass(fc3)
    assert isinstance(fc4.gdf, gpd.GeoDataFrame)

    with pytest.raises(TypeError):
        _ = ft.FeatureClass("test.gdb")

    with pytest.raises(FileNotFoundError):
        _ = ft.FeatureClass("doesnotexist.gdb/test_fc")


def test_instatiate_gdf() -> None:
    fc1 = ft.FeatureClass(gpd.GeoDataFrame(geometry=[shapely.Point(0, 1)]))
    assert isinstance(fc1.gdf, gpd.GeoDataFrame)

    fc2 = ft.FeatureClass(gpd.GeoDataFrame(geometry=[]))
    assert isinstance(fc2.gdf, gpd.GeoDataFrame)


def test_instatiate_none() -> None:
    fc1 = ft.FeatureClass()
    assert isinstance(fc1.gdf, gpd.GeoDataFrame)
    assert len(fc1.gdf) == 0


def test_delitem(gdf_points, samples) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    del fc1[500]
    assert len(fc1) == samples - 1
    with pytest.raises(TypeError):
        del fc1["test"]


def test_getitem(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    assert isinstance(fc1[0], gpd.GeoDataFrame)
    assert isinstance(fc1[-1], gpd.GeoDataFrame)
    assert isinstance(fc1[100:105], gpd.GeoDataFrame)
    assert isinstance(fc1[100, 200, 300], gpd.GeoDataFrame)
    assert isinstance(fc1[(100, 200, 300)], gpd.GeoDataFrame)
    assert isinstance(fc1[[100, 200, 300]], gpd.GeoDataFrame)
    assert isinstance(fc1[10, 100:105, 200, 300:305], gpd.GeoDataFrame)
    with pytest.raises(KeyError):
        _ = fc1["test"]  # ty: ignore[invalid-argument-type]


def test_iter(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    for row in fc1:
        assert isinstance(row, tuple)
        assert isinstance(row[0], int)
        assert isinstance(row[1], str)
        assert isinstance(row[2], str)
        assert isinstance(row[3], str)
        assert isinstance(row[4], shapely.Point)


def test_len(gdf_points, samples) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    assert len(fc1) == samples


def test_setitem(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    fc1[(0, "geometry")] = None
    fc1[(-1, 0)] = None
    with pytest.raises(TypeError):
        fc1[("s", "geometry")] = None  # ty: ignore[invalid-assignment]
    with pytest.raises(TypeError):
        fc1[(0, {})] = None  # ty: ignore[invalid-assignment]

    for c in fc1._data.columns:
        assert isinstance(c, str)


def test_crs(ft_gdb) -> None:
    gdb, _ = ft_gdb

    for fc in gdb.fcs:
        assert isinstance(fc.crs, CRS)

    fc1 = ft.FeatureClass()
    assert fc1.crs is None


def test_gdf(ft_gdb) -> None:
    gdb, _gdb_path = ft_gdb
    for fc in gdb.fcs:
        assert isinstance(fc.gdf, gpd.GeoDataFrame)


def test_geom_type(ft_gdb) -> None:
    gdb, _gdb_path = ft_gdb
    for fc in gdb.fcs:
        assert fc.geom_type in (
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "Polygon",
            "MultiPolygon",
            None,
        )

    fc1 = ft.FeatureClass()
    assert fc1.geom_type is None


def test_geometry(gdf_polygons) -> None:
    fc1 = ft.FeatureClass(gdf_polygons)
    assert isinstance(fc1.geometry, gpd.GeoSeries)
    assert isinstance(fc1.geometry.bounds, pd.DataFrame)
    with pytest.raises(AttributeError):
        # noinspection property-access
        fc1.geometry = False  # ty: ignore[invalid-assignment]

    fc2 = ft.FeatureClass()
    assert fc2.geometry is None


def test_append(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    count = len(fc1)
    new_row = fc1[0]
    fc1.append(new_row)
    assert len(fc1) == count + 1
    assert fc1[0].iat[0, 0] == fc1[-1].iat[0, 0]

    fc2 = ft.FeatureClass(fc1)
    count = len(fc2)
    new_row = ft.FeatureClass(fc2[0])
    fc2.append(new_row)
    assert len(fc2) == count + 1
    assert fc2[0].iat[0, 0] == fc2[-1].iat[0, 0]

    with pytest.raises(TypeError):
        fc2.append("bad_input")  # ty: ignore[invalid-argument-type]


def test_calculate(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    fc1.calculate(
        "sample1",
        "test",
    )
    # fc1.select_columns("sample1", geometry=False).head()

    fc2 = ft.FeatureClass(gdf_points)
    fc2.calculate(
        "test2",
        "test",
    )
    # fc2.select_columns("test2", geometry=False).head()

    fc3 = ft.FeatureClass(gdf_points)
    fc3.calculate("test3", 2 * 2, np.uint8)
    # fc3.select_columns("test3", geometry=False).head()

    fc4 = ft.FeatureClass(gdf_points)
    fc4.calculate(
        "test4",
        "$sample2$ + '___' + $sample2$ + '___' + $sample3$",
        str,
    )
    # fc4.select_columns("test4", geometry=False).head()

    with pytest.raises(KeyError):
        fc4.calculate("sample1", "$badcol$")


def test_clear(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    fc1.clear()
    assert len(fc1) == 0


def test_copy(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    fc2 = fc1.copy()
    assert len(fc1) == len(fc2)
    assert fc1 != fc2


def test_head(gdf_points) -> None:
    fc1 = ft.FeatureClass(src=gdf_points)
    h1 = fc1.head(n=5, silent=False, geometry=True)
    assert isinstance(h1, pd.DataFrame)
    assert len(h1) == 5
    assert h1.active_geometry_name == "geometry"

    fc2 = ft.FeatureClass(src=gdf_points)
    h2 = fc2.head(n=5, silent=True, geometry=False)
    assert isinstance(h2, pd.DataFrame)
    assert len(h2) == 5
    with pytest.raises(AttributeError):
        _ = h2.active_geometry_name
    # check for mutation of the original fc
    assert fc2._data.active_geometry_name == "geometry"
    assert fc2.geometry is not None
    assert len(fc2.geometry) == 1000


def test_insert(gdf_points, samples) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    new_row = fc1[500]
    fc1.insert(600, new_row)
    assert len(fc1) == samples + 1
    assert fc1[500].iat[0, 0] == fc1[600].iat[0, 0]
    fc1.insert(0, new_row)
    fc1.insert(-1, new_row)

    with pytest.raises(TypeError):
        fc1.insert("s", new_row)  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError):
        fc1.insert(0, "s")  # ty: ignore[invalid-argument-type]
    with pytest.raises(ValueError):
        fc1.insert(500, gpd.GeoDataFrame())
    with pytest.raises(ValueError):
        fc1.insert(500, gpd.GeoDataFrame(columns=["test"]))

    with pytest.raises(TypeError):
        fc2 = ft.FeatureClass(gpd.GeoDataFrame(geometry=[shapely.Point(0, 1)]))
        fc2.insert(
            -1,
            gpd.GeoDataFrame(
                geometry=[
                    shapely.LineString([(0, 1), (1, 1)]),
                    shapely.Point(0, 1),
                ]
            ),
        )

    # validate geometry
    fc3 = ft.FeatureClass()
    assert fc3.geom_type is None

    fc3 = ft.FeatureClass(
        gpd.GeoDataFrame(
            {"col1": ["a"]}, geometry=[shapely.LineString([(0, 1), (1, 1)])]
        )
    )

    fc3.insert(
        -1,
        gpd.GeoDataFrame(
            {"col1": ["b"]}, geometry=[shapely.LineString([(0, 1), (1, 1)])]
        ),
    )
    assert fc3.geom_type == "LineString"

    fc3.insert(
        -1,
        ft.FeatureClass(
            gpd.GeoDataFrame(
                {"col1": ["c"]},
                geometry=[shapely.LineString([(0, 1), (1, 1)])],
            )
        ),
    )

    fc3.insert(
        -1,
        gpd.GeoDataFrame(
            {"col1": ["c"]},
            geometry=[shapely.LineString([(0, 1), (1, 1)])],
        ),
    )

    with pytest.raises(TypeError):
        fc3.insert(
            -1,
            gpd.GeoDataFrame(
                {"col1": ["d", "e"]},
                geometry=[
                    shapely.LineString([(0, 1), (1, 1)]),
                    shapely.MultiLineString([[(0, 1), (1, 1)], [(0, 1), (1, 1)]]),
                ],
            ),
        )

    with pytest.raises(TypeError):
        fc3.insert(
            -1,
            gpd.GeoDataFrame(
                {"col1": ["x", "y", "z"]},
                geometry=[
                    shapely.LineString([(0, 1), (1, 1)]),
                    shapely.MultiLineString([[(0, 1), (1, 1)], [(0, 1), (1, 1)]]),
                    shapely.Point(0, 0),
                ],
            ),
        )

    with pytest.raises(TypeError):
        fc3.insert(
            -1, gpd.GeoDataFrame({"col1": ["test"]}, geometry=[shapely.Point(0, 0)])
        )


def test_list_fields(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    assert fc1.list_fields() == [
        "ObjectID",
        "sample1",
        "sample2",
        "sample3",
        "geometry",
    ]


def test_save(gdf_points, gdb_path) -> None:
    fc1 = ft.FeatureClass(gdf_points)

    fc1.save(
        gdb_path=gdb_path,
        fc_name="test_points1",
        feature_dataset=None,
        overwrite=False,
    )
    fc1.save(
        gdb_path=gdb_path,
        fc_name="test_points2",
        feature_dataset="test_fds",
        overwrite=False,
    )
    with pytest.raises(FileExistsError):
        fc1.save(
            gdb_path=gdb_path,
            fc_name="test_points2",
            feature_dataset="test_fds",
            overwrite=False,
        )

    with pytest.raises(FileNotFoundError):
        fc1.save(gdb_path="bad_path", fc_name="fc_name")


def test_show(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    fc1.show(block=False)


def test_select_columns(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    cols1 = fc1.select_columns(["sample1", "sample2"])
    assert len(cols1) == 1000

    cols2 = fc1.select_columns(["sample1"], geometry=False)
    assert len(cols2) == 1000

    cols3 = fc1.select_columns("sample1", geometry=False)
    assert len(cols3) == 1000

    cols4 = fc1.select_columns("geometry", geometry=False)
    assert len(cols4) == 1000

    cols5 = fc1.select_columns(["sample1", "sample2", "geometry"], geometry=False)
    assert len(cols5) == 1000

    with pytest.raises(KeyError):
        _ = fc1.select_columns(["bad"])


def test_select_rows(gdf_points, samples) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    rows1 = fc1.select_rows("ObjectID < 10")

    assert len(rows1) == 10
    rows2 = fc1.select_rows("sample1 > sample2")
    assert len(rows2) < samples

    rows3 = fc1.select_rows("ObjectID == 1")
    assert len(rows3) == 1

    test_id = fc1[0].iat[0, 0]
    assert isinstance(test_id, str)
    rows4 = fc1.select_rows(f"sample1 == '{test_id}'")
    assert len(rows4) == 1
    rows5 = fc1.select_rows(f'sample1 == "{test_id}"')
    assert len(rows5) == 1


def test_sort(gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    case1 = fc1[0].iat[0, 0]
    fc1.sort("sample1", ascending=True)
    case2 = fc1[0].iat[0, 0]
    fc1.sort("sample1", ascending=False)
    case3 = fc1[0].iat[0, 0]
    assert case1 != case2 != case3


def test_to_json(tmp_path, gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    fp = str(tmp_path / "pts.geojson")
    js1 = fc1.to_json(fp, indent=2)
    assert isinstance(js1, dict)

    fc2 = ft.FeatureClass(gdf_points)
    fp = str(tmp_path / "pts")
    js2 = fc2.to_json(fp, indent=2)
    assert isinstance(js2, dict)

    fc3 = ft.FeatureClass()
    fp = str(tmp_path / "no_geometry")
    js3 = fc3.to_json(fp, indent=2)
    assert isinstance(js3, dict)


def test_to_shp(tmp_path, gdf_points) -> None:
    fc1 = ft.FeatureClass(gdf_points)
    fp = str(tmp_path / "pts.shp")
    fc1.to_shp(fp)

    fc2 = ft.FeatureClass(gdf_points)
    fp = str(tmp_path / "pts")
    fc2.to_shp(fp)
