import footbridge as ft


def test_gdb_fixtures(ft_gdb, esri_gdb):
    gdb, gdb_path = ft_gdb

    for this_gdb in [gdb, ft.GeoDatabase(path=esri_gdb)]:
        assert isinstance(this_gdb, ft.GeoDatabase)
        for fds_name, fds in this_gdb.items():
            assert isinstance(fds_name, str) or fds_name is None
            assert isinstance(fds, ft.FeatureDataset)

            for fc_name, fc in fds.items():
                assert isinstance(fc_name, str)
                assert isinstance(fc, ft.FeatureClass)
