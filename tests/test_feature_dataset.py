import geopandas as gpd
import pytest
import shapely

import footbridge as ft


def test_instantiate(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds_name, fds in gdb.items():
        assert isinstance(fds_name, str) or fds_name is None
        assert isinstance(fds, ft.FeatureDataset)

        for fc_name, fc in fds.items():
            assert isinstance(fc_name, str)
            assert isinstance(fc, ft.FeatureClass)

    fds1 = ft.FeatureDataset(crs="EPSG:4326")
    assert isinstance(fds1, ft.FeatureDataset)
    fds2 = ft.FeatureDataset(contents={"fc": ft.FeatureClass()})
    assert isinstance(fds2, ft.FeatureDataset)


def test_delitem(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.values():
        fcs = list(fds.fc_dict.keys())
        for fc_name in fcs:
            del fds[fc_name]
        assert len(fds) == 0


def test_fc_dict(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.values():
        for fc_name, fc in fds.fc_dict.items():
            assert isinstance(fc_name, str)
            assert isinstance(fc, ft.FeatureClass)


def test_fc_names(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.values():
        for fc_name in fds.fc_names:
            assert isinstance(fc_name, str)


def test_fcs(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.values():
        for fc in fds.fcs:
            assert isinstance(fc, ft.FeatureClass)


def test_getitem(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.values():
        fc_names = fds.keys()
        for fc_name in fc_names:
            assert isinstance(fds[fc_name], ft.FeatureClass)
        assert isinstance(fds[0], ft.FeatureClass)
        with pytest.raises(IndexError):
            f = fds[999]  # noqa: F841


def test_iter(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.values():
        for fc_name in fds:
            assert isinstance(fds[fc_name], ft.FeatureClass)


def test_len(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.values():
        assert len(fds) == 3


def test_setitem(ft_gdb):
    gdb, gdb_path = ft_gdb

    with pytest.raises(TypeError):
        fds: ft.FeatureDataset
        for fds in gdb.values():
            fds.__setitem__(
                "fc_test",
                ft.FeatureClass(
                    gpd.GeoDataFrame(
                        geometry=[
                            shapely.LineString([(0, 1), (1, 1)]),
                            shapely.Point(0, 1),
                        ],
                        crs="EPSG:4326",
                    )
                ),
            )

    fds: ft.FeatureDataset
    for fds in gdb.values():
        fc_names = list(fds.keys())
        for fc_name in fc_names:
            fds.__setitem__(fc_name + "_copy", fds[fc_name])
        assert len(fds) == 6 or len(fds) == 8

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            fds.__setitem__("bad", 0)

        with pytest.raises(ValueError):
            fds.__setitem__("0_bad", ft.FeatureClass())

        with pytest.raises(ValueError):
            fds.__setitem__("bad!@#$", ft.FeatureClass())


def test_feature_classes(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.values():
        for fc_name, fc in fds.fc_dict.items():
            assert isinstance(fc_name, str)
            assert isinstance(fc, ft.FeatureClass)


def test_crs(ft_gdb):
    gdb, gdb_path = ft_gdb
    for idx, fds in enumerate(gdb.values()):
        test_fc = ft.FeatureClass()
        with pytest.raises(AttributeError):
            assert test_fc.crs != fds.crs
            fds[f"bad_fc_{idx}"] = test_fc

    fds2 = ft.FeatureDataset()
    fds2["fc1"] = ft.FeatureClass(gpd.GeoDataFrame(geometry=[], crs="EPSG:4326"))
    assert fds2.crs.equals("EPSG:4326")


def test_enforce_crs(ft_gdb):
    gdb, gdb_path = ft_gdb
    for fds in gdb.fds_dict.values():
        assert isinstance(fds.enforce_crs, bool)
