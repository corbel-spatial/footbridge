Installation
============

.. note::
    :code:`footbridge` supports vector feature class and raster dataset operations on geodatabases.
    Raster support depends on `GDAL <https://gdal.org/>`__, which is included when installed in a :code:`conda` environment.
    Installing with :code:`pip` only supports vector operations by default. See details below.

Conda (recommended)
-------------------

In an active `conda <https://www.anaconda.com/docs/getting-started/getting-started>`__ environment::

    conda install footbridge -c conda-forge


Pip
---

For vector feature class support only::

    python -m pip install footbridge

For vector *and* raster dataset support you must have already installed the `GDAL binaries <https://gdal.org/en/stable/download.html#binaries>`__ (version >= 3.8), then::

    python -m pip install footbridge[raster]

On Windows you can easily install GDAL via cgohlke's `geospatial-wheels <https://github.com/cgohlke/geospatial-wheels>`__ with::

    pip install --index https://gisidx.github.io/gwi gdal

ArcGIS Pro
----------

.. warning::

    This is experimental and may not work depending on your installation of ArcGIS!

To install in an ArcGIS Pro :code:`conda` environment:

1. Open the `Python Command Prompt <https://developers.arcgis.com/python/latest/guide/install-and-set-up/arcgis-pro/#installation-using-python-command-prompt>`__, which can be launched from the Start Menu > All Programs > ArcGIS > Python Command Prompt.

2. Create a new cloned environment::

    conda create --clone arcgispro-py3 --name arcgispro-py3-clone

3. Activate the new environment::

    proswap arcgispro-py3-clone

4. Install `footbridge`::

    conda install -c conda-forge footbridge

5. Test the installation::

    python -c "import footbridge"
