from xstac import xarray_to_stac, fix_attrs
from xstac._xstac import _bbox_to_geometry
import xarray as xr
import numpy as np
import pandas as pd
import pytest
import pystac

import xstac


data = np.empty((40, 584, 284), dtype="float32")
x = xr.DataArray(
    np.arange(-5802250.0, -5519250 + 1000, 1000),
    name="x",
    dims="x",
    attrs={
        "units": "m",
        "long_name": "x coordinate of projection",
        "standard_name": "projection_x_coordinate",
    },
)
y = xr.DataArray(
    np.arange(-39000.0, -622000.0 - 1000, -1000.0),
    name="y",
    dims="y",
    attrs={
        "units": "m",
        "long_name": "y coordinate of projection",
        "standard_name": "projection_y_coordinate",
    },
)
time = xr.DataArray(
    pd.date_range(start="1980-07-01", freq="A-JUL", periods=40),
    name="time",
    dims="time",
    attrs={
        "standard_name": "time",
        "bounds": "time_bnds",
        "long_name": "24-hour day based on local time",
    },
)
lat = xr.DataArray(
    np.empty((584, 284)),
    coords={"y": y, "x": x},
    dims=("y", "x"),
    name="lat",
    attrs={
        "units": "degrees_north",
        "long_name": "latitude coordinate",
        "standard_name": "latitude",
    },
)
lon = xr.DataArray(
    np.empty((584, 284)),
    coords={"y": y, "x": x},
    dims=("y", "x"),
    name="lon",
    attrs={
        "units": "degrees_east",
        "long_name": "longitude coordinate",
        "standard_name": "longitude",
    },
)

coords = dict(time=time, y=y, x=x, lat=lat, lon=lon)


@pytest.fixture
def ds():
    ds = xr.Dataset(
        {
            "prcp": xr.DataArray(
                data,
                coords=coords,
                dims=("time", "y", "x"),
                attrs={
                    "grid_mapping": "lambert_conformal_conic",
                    "cell_methods": "area: mean time: sum within days time: sum over days",
                    "units": "mm",
                    "long_name": "annual total precipitation",
                },
            ),
            "swe": xr.DataArray(data, coords=coords, dims=("time", "y", "x")),
            "time_bnds": xr.DataArray(
                np.empty((40, 2), dtype="datetime64[ns]"),
                name="time_bnds",
                coords={"time": time},
                dims=("time", "nv"),
                attrs={"time": "days since 1950-01-01 00:00:00"},
            ),
            "lambert_conformal_conic": xr.DataArray(
                np.array(-32767, dtype="int16"),
                name="lambert_conformal_conic",
                attrs={
                    "grid_mapping_name": "lambert_conformal_conic",
                    "longitude_of_central_meridian": -100.0,
                    "latitude_of_projection_origin": 42.5,
                    "false_easting": 0.0,
                    "false_northing": 0.0,
                    "standard_parallel": np.array([25.0, 60.0]),
                    "semi_major_axis": 6378137.0,
                    "inverse_flattening": 298.257223563,
                },
            ),
        },
        attrs={
            "Conventions": "CF-1.6",
            "Version_data": "Daymet Data Version 4.0",
            "Version_software": "Daymet Software Version 4.0",
            "citation": "Please see http://daymet.ornl.gov/ for current Daymet data citation information",
            "references": "Please see http://daymet.ornl.gov/ for current information on Daymet references",
            "source": "Daymet Software Version 4.0",
            "start_year": [1980],
        },
    )
    return fix_attrs(ds)


def test_xarray_to_stac(ds):
    template = {
        "id": "id",
        "type": "Collection",
        "links": [],
        "description": "description",
        "license": "license",
        "stac_version": "1.0.0",
    }
    result = xarray_to_stac(
        ds,
        template=template,
        temporal_dimension="time",
        x_dimension="x",
        y_dimension="y",
    )
    assert result.id == "id"
    assert isinstance(result, pystac.Collection)
    assert result.description == "description"
    assert result.license == "license"

    dimensions = result.extra_fields["cube:dimensions"]
    expected = {
        "time": {
            "type": "temporal",
            "description": "24-hour day based on local time",
            "extent": ["1980-07-31T00:00:00Z", "2019-07-31T00:00:00Z"],
        },
        "x": {
            "type": "spatial",
            "axis": "x",
            "description": "x coordinate of projection",
            "extent": [-5802250.0, -5519250.0],
            "step": 1000.0,
            "reference_system": {
                "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
                "type": "ProjectedCRS",
                "name": "undefined",
                "base_crs": {
                    "name": "undefined",
                    "datum": {
                        "type": "GeodeticReferenceFrame",
                        "name": "undefined",
                        "ellipsoid": {
                            "name": "undefined",
                            "semi_major_axis": 6378137,
                            "inverse_flattening": 298.257223563,
                        },
                    },
                    "coordinate_system": {
                        "subtype": "ellipsoidal",
                        "axis": [
                            {
                                "name": "Longitude",
                                "abbreviation": "lon",
                                "direction": "east",
                                "unit": "degree",
                            },
                            {
                                "name": "Latitude",
                                "abbreviation": "lat",
                                "direction": "north",
                                "unit": "degree",
                            },
                        ],
                    },
                },
                "conversion": {
                    "name": "unknown",
                    "method": {
                        "name": "Lambert Conic Conformal (2SP)",
                        "id": {"authority": "EPSG", "code": 9802},
                    },
                    "parameters": [
                        {
                            "name": "Latitude of 1st standard parallel",
                            "value": 25,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8823},
                        },
                        {
                            "name": "Latitude of 2nd standard parallel",
                            "value": 60,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8824},
                        },
                        {
                            "name": "Latitude of false origin",
                            "value": 42.5,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8821},
                        },
                        {
                            "name": "Longitude of false origin",
                            "value": -100,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8822},
                        },
                        {
                            "name": "Easting at false origin",
                            "value": 0,
                            "unit": "metre",
                            "id": {"authority": "EPSG", "code": 8826},
                        },
                        {
                            "name": "Northing at false origin",
                            "value": 0,
                            "unit": "metre",
                            "id": {"authority": "EPSG", "code": 8827},
                        },
                    ],
                },
                "coordinate_system": {
                    "subtype": "Cartesian",
                    "axis": [
                        {
                            "name": "Easting",
                            "abbreviation": "E",
                            "direction": "east",
                            "unit": "metre",
                        },
                        {
                            "name": "Northing",
                            "abbreviation": "N",
                            "direction": "north",
                            "unit": "metre",
                        },
                    ],
                },
            },
        },
        "y": {
            "type": "spatial",
            "axis": "y",
            "description": "y coordinate of projection",
            "extent": [-622000.0, -39000.0],
            "step": -1000.0,
            "reference_system": {
                "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
                "type": "ProjectedCRS",
                "name": "undefined",
                "base_crs": {
                    "name": "undefined",
                    "datum": {
                        "type": "GeodeticReferenceFrame",
                        "name": "undefined",
                        "ellipsoid": {
                            "name": "undefined",
                            "semi_major_axis": 6378137,
                            "inverse_flattening": 298.257223563,
                        },
                    },
                    "coordinate_system": {
                        "subtype": "ellipsoidal",
                        "axis": [
                            {
                                "name": "Longitude",
                                "abbreviation": "lon",
                                "direction": "east",
                                "unit": "degree",
                            },
                            {
                                "name": "Latitude",
                                "abbreviation": "lat",
                                "direction": "north",
                                "unit": "degree",
                            },
                        ],
                    },
                },
                "conversion": {
                    "name": "unknown",
                    "method": {
                        "name": "Lambert Conic Conformal (2SP)",
                        "id": {"authority": "EPSG", "code": 9802},
                    },
                    "parameters": [
                        {
                            "name": "Latitude of 1st standard parallel",
                            "value": 25,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8823},
                        },
                        {
                            "name": "Latitude of 2nd standard parallel",
                            "value": 60,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8824},
                        },
                        {
                            "name": "Latitude of false origin",
                            "value": 42.5,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8821},
                        },
                        {
                            "name": "Longitude of false origin",
                            "value": -100,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8822},
                        },
                        {
                            "name": "Easting at false origin",
                            "value": 0,
                            "unit": "metre",
                            "id": {"authority": "EPSG", "code": 8826},
                        },
                        {
                            "name": "Northing at false origin",
                            "value": 0,
                            "unit": "metre",
                            "id": {"authority": "EPSG", "code": 8827},
                        },
                    ],
                },
                "coordinate_system": {
                    "subtype": "Cartesian",
                    "axis": [
                        {
                            "name": "Easting",
                            "abbreviation": "E",
                            "direction": "east",
                            "unit": "metre",
                        },
                        {
                            "name": "Northing",
                            "abbreviation": "N",
                            "direction": "north",
                            "unit": "metre",
                        },
                    ],
                },
            },
        },
    }
    assert dimensions == expected
    expected = {
        "lat": {
            "type": "auxiliary",
            "description": "latitude coordinate",
            "dimensions": ["y", "x"],
            "unit": "degrees_north",
            "shape": [584, 284],
            "attrs": {
                "units": "degrees_north",
                "long_name": "latitude coordinate",
                "standard_name": "latitude",
            },
        },
        "lon": {
            "type": "auxiliary",
            "description": "longitude coordinate",
            "dimensions": ["y", "x"],
            "unit": "degrees_east",
            "shape": [584, 284],
            "attrs": {
                "units": "degrees_east",
                "long_name": "longitude coordinate",
                "standard_name": "longitude",
            },
        },
        "prcp": {
            "type": "data",
            "description": "annual total precipitation",
            "dimensions": ["time", "y", "x"],
            "unit": "mm",
            "shape": [40, 584, 284],
            "attrs": {
                "grid_mapping": "lambert_conformal_conic",
                "cell_methods": "area: mean time: sum within days time: sum over days",
                "units": "mm",
                "long_name": "annual total precipitation",
            },
        },
        "swe": {
            "type": "data",
            "dimensions": ["time", "y", "x"],
            "shape": [40, 584, 284],
            "attrs": {},
        },
        "time_bnds": {
            "type": "data",
            "dimensions": ["time", "nv"],
            "shape": [40, 2],
            "attrs": {"time": "days since 1950-01-01 00:00:00"},
        },
        "lambert_conformal_conic": {
            "type": "data",
            "dimensions": [],
            "shape": [],
            "attrs": {
                "grid_mapping_name": "lambert_conformal_conic",
                "longitude_of_central_meridian": -100.0,
                "latitude_of_projection_origin": 42.5,
                "false_easting": 0.0,
                "false_northing": 0.0,
                "standard_parallel": [25.0, 60.0],
                "semi_major_axis": 6378137.0,
                "inverse_flattening": 298.257223563,
            },
        },
    }
    assert result.extra_fields["cube:variables"] == expected


def test_validation_with_none():
    # https://github.com/TomAugspurger/xstac/issues/9
    template = {
        "type": "Collection",
        "id": "cesm2-lens",
        "stac_version": "1.0.0",
        "description": "desc",
        "stac_extensions": [
            "https://stac-extensions.github.io/datacube/v2.0.0/schema.json"
        ],
        "extent": {
            "spatial": {"bbox": [[-180, -90, 180, 90]]},
            "temporal": {
                "interval": [["1851-01-01T00:00:00Z", "1851-01-01T00:00:00Z"]]
            },
        },
        "providers": [],
        "license": "CC0-1.0",
        "links": [],
    }
    ds = xr.Dataset(
        {
            "data": xr.DataArray(
                [1, 2],
                dims=("time",),
                coords={"time": pd.to_datetime(["2021-01-01", "2021-01-02"])},
            )
        }
    )
    ds.time.attrs["long_name"] = "time"
    c = xarray_to_stac(ds, template, temporal_dimension="time")
    c.normalize_hrefs("/")
    c.validate()


def test_xarray_to_stac_item(ds):
    template = {
        "id": "id",
        "type": "Feature",
        "links": [],
        "geometry": None,
        "stac_version": "1.0.0",
        "properties": {"datetime": "2021-01-01T00:00:00Z"},
        "assets": {},
    }
    result = xarray_to_stac(
        ds,
        template=template,
        temporal_dimension="time",
        x_dimension="x",
        y_dimension="y",
    )
    assert result.id == "id"
    assert isinstance(result, pystac.Item)

    dimensions = result.properties["cube:dimensions"]
    expected = {
        "time": {
            "type": "temporal",
            "description": "24-hour day based on local time",
            "extent": ["1980-07-31T00:00:00Z", "2019-07-31T00:00:00Z"],
        },
        "x": {
            "type": "spatial",
            "axis": "x",
            "description": "x coordinate of projection",
            "extent": [-5802250.0, -5519250.0],
            "step": 1000.0,
            "reference_system": {
                "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
                "type": "ProjectedCRS",
                "name": "undefined",
                "base_crs": {
                    "name": "undefined",
                    "datum": {
                        "type": "GeodeticReferenceFrame",
                        "name": "undefined",
                        "ellipsoid": {
                            "name": "undefined",
                            "semi_major_axis": 6378137,
                            "inverse_flattening": 298.257223563,
                        },
                    },
                    "coordinate_system": {
                        "subtype": "ellipsoidal",
                        "axis": [
                            {
                                "name": "Longitude",
                                "abbreviation": "lon",
                                "direction": "east",
                                "unit": "degree",
                            },
                            {
                                "name": "Latitude",
                                "abbreviation": "lat",
                                "direction": "north",
                                "unit": "degree",
                            },
                        ],
                    },
                },
                "conversion": {
                    "name": "unknown",
                    "method": {
                        "name": "Lambert Conic Conformal (2SP)",
                        "id": {"authority": "EPSG", "code": 9802},
                    },
                    "parameters": [
                        {
                            "name": "Latitude of 1st standard parallel",
                            "value": 25,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8823},
                        },
                        {
                            "name": "Latitude of 2nd standard parallel",
                            "value": 60,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8824},
                        },
                        {
                            "name": "Latitude of false origin",
                            "value": 42.5,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8821},
                        },
                        {
                            "name": "Longitude of false origin",
                            "value": -100,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8822},
                        },
                        {
                            "name": "Easting at false origin",
                            "value": 0,
                            "unit": "metre",
                            "id": {"authority": "EPSG", "code": 8826},
                        },
                        {
                            "name": "Northing at false origin",
                            "value": 0,
                            "unit": "metre",
                            "id": {"authority": "EPSG", "code": 8827},
                        },
                    ],
                },
                "coordinate_system": {
                    "subtype": "Cartesian",
                    "axis": [
                        {
                            "name": "Easting",
                            "abbreviation": "E",
                            "direction": "east",
                            "unit": "metre",
                        },
                        {
                            "name": "Northing",
                            "abbreviation": "N",
                            "direction": "north",
                            "unit": "metre",
                        },
                    ],
                },
            },
        },
        "y": {
            "type": "spatial",
            "axis": "y",
            "description": "y coordinate of projection",
            "extent": [-622000.0, -39000.0],
            "step": -1000.0,
            "reference_system": {
                "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
                "type": "ProjectedCRS",
                "name": "undefined",
                "base_crs": {
                    "name": "undefined",
                    "datum": {
                        "type": "GeodeticReferenceFrame",
                        "name": "undefined",
                        "ellipsoid": {
                            "name": "undefined",
                            "semi_major_axis": 6378137,
                            "inverse_flattening": 298.257223563,
                        },
                    },
                    "coordinate_system": {
                        "subtype": "ellipsoidal",
                        "axis": [
                            {
                                "name": "Longitude",
                                "abbreviation": "lon",
                                "direction": "east",
                                "unit": "degree",
                            },
                            {
                                "name": "Latitude",
                                "abbreviation": "lat",
                                "direction": "north",
                                "unit": "degree",
                            },
                        ],
                    },
                },
                "conversion": {
                    "name": "unknown",
                    "method": {
                        "name": "Lambert Conic Conformal (2SP)",
                        "id": {"authority": "EPSG", "code": 9802},
                    },
                    "parameters": [
                        {
                            "name": "Latitude of 1st standard parallel",
                            "value": 25,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8823},
                        },
                        {
                            "name": "Latitude of 2nd standard parallel",
                            "value": 60,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8824},
                        },
                        {
                            "name": "Latitude of false origin",
                            "value": 42.5,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8821},
                        },
                        {
                            "name": "Longitude of false origin",
                            "value": -100,
                            "unit": "degree",
                            "id": {"authority": "EPSG", "code": 8822},
                        },
                        {
                            "name": "Easting at false origin",
                            "value": 0,
                            "unit": "metre",
                            "id": {"authority": "EPSG", "code": 8826},
                        },
                        {
                            "name": "Northing at false origin",
                            "value": 0,
                            "unit": "metre",
                            "id": {"authority": "EPSG", "code": 8827},
                        },
                    ],
                },
                "coordinate_system": {
                    "subtype": "Cartesian",
                    "axis": [
                        {
                            "name": "Easting",
                            "abbreviation": "E",
                            "direction": "east",
                            "unit": "metre",
                        },
                        {
                            "name": "Northing",
                            "abbreviation": "N",
                            "direction": "north",
                            "unit": "metre",
                        },
                    ],
                },
            },
        },
    }
    assert dimensions == expected
    expected = {
        "lat": {
            "type": "auxiliary",
            "description": "latitude coordinate",
            "dimensions": ["y", "x"],
            "unit": "degrees_north",
            "shape": [584, 284],
            "attrs": {
                "units": "degrees_north",
                "long_name": "latitude coordinate",
                "standard_name": "latitude",
            },
        },
        "lon": {
            "type": "auxiliary",
            "description": "longitude coordinate",
            "dimensions": ["y", "x"],
            "unit": "degrees_east",
            "shape": [584, 284],
            "attrs": {
                "units": "degrees_east",
                "long_name": "longitude coordinate",
                "standard_name": "longitude",
            },
        },
        "prcp": {
            "type": "data",
            "description": "annual total precipitation",
            "dimensions": ["time", "y", "x"],
            "unit": "mm",
            "shape": [40, 584, 284],
            "attrs": {
                "grid_mapping": "lambert_conformal_conic",
                "cell_methods": "area: mean time: sum within days time: sum over days",
                "units": "mm",
                "long_name": "annual total precipitation",
            },
        },
        "swe": {
            "type": "data",
            "dimensions": ["time", "y", "x"],
            "shape": [40, 584, 284],
            "attrs": {},
        },
        "time_bnds": {
            "type": "data",
            "dimensions": ["time", "nv"],
            "shape": [40, 2],
            "attrs": {"time": "days since 1950-01-01 00:00:00"},
        },
        "lambert_conformal_conic": {
            "type": "data",
            "dimensions": [],
            "shape": [],
            "attrs": {
                "grid_mapping_name": "lambert_conformal_conic",
                "longitude_of_central_meridian": -100.0,
                "latitude_of_projection_origin": 42.5,
                "false_easting": 0.0,
                "false_northing": 0.0,
                "standard_parallel": [25.0, 60.0],
                "semi_major_axis": 6378137.0,
                "inverse_flattening": 298.257223563,
            },
        },
    }
    assert result.properties["cube:variables"] == expected

    assert result.properties["start_datetime"] == "1980-07-31T00:00:00Z"
    assert result.properties["end_datetime"] == "2019-07-31T00:00:00Z"


def test_bbox_to_geometry():
    import shapely.geometry

    bbox = [
        -160.2988400944475,
        17.960033949329812,
        -154.7780670634169,
        23.51232608231902,
    ]
    result = shapely.geometry.mapping(shapely.geometry.shape(_bbox_to_geometry(bbox)))
    expected = shapely.geometry.mapping(shapely.geometry.box(*bbox))
    assert result == expected
