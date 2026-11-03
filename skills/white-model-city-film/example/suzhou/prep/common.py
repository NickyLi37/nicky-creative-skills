"""Shared projection and extent for every prep script."""
from pyproj import Transformer

# Local frame origin: centre of the old city (near Xuanmiao Temple). x east, y north, metres.
ORIGIN_LON, ORIGIN_LAT = 120.6230, 31.3110
LOCAL_CRS = f"+proj=tmerc +lat_0={ORIGIN_LAT} +lon_0={ORIGIN_LON} +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=m"
_fwd = Transformer.from_crs("EPSG:4326", LOCAL_CRS, always_xy=True)
_inv = Transformer.from_crs(_fwd.target_crs, "EPSG:4326", always_xy=True)

# Film extent (lon/lat): Gaoxin (west) to Caoxieshan / Weiting (east), Baodai Bridge (south) to north of Tiger Hill.
BBOX_LONLAT = (120.495, 31.235, 120.835, 31.425)  # west, south, east, north


def to_local(lon, lat):
    return _fwd.transform(lon, lat)


def to_lonlat(x, y):
    return _inv.transform(x, y)


_w, _s, _e, _n = BBOX_LONLAT
EXTENT_LOCAL = [to_local(_w, _s), to_local(_e, _s), to_local(_e, _n), to_local(_w, _n)]
