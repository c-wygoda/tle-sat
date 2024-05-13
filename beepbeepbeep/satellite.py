from datetime import datetime, timezone

from shapely import Point
from skyfield.positionlib import Geocentric
from skyfield.sgp4lib import EarthSatellite
from skyfield.toposlib import wgs84


def assert_is_utc(t: datetime):
    if t.tzinfo != timezone.utc:
        raise ValueError("datetime must be in utc")


class Satellite:
    model: EarthSatellite

    def __init__(self, tle: str):
        lines = tle.splitlines()
        match len(lines):
            case 2:
                self.model = EarthSatellite(line1=lines[0], line2=lines[1])
            case 3:
                self.model = EarthSatellite(line1=lines[1], line2=lines[2])
            case _:
                raise RuntimeError("tle strings must be 2 or 3 lines")

    def at(self, t: datetime) -> Geocentric:
        assert_is_utc(t)
        return self.model.at(self.model.ts.from_datetime(t))

    def position(self, t: datetime) -> Point:
        pos = self.at(t)
        ll = wgs84.subpoint_of(pos)
        alt = wgs84.height_of(pos).m
        return Point(ll.longitude.degrees, ll.latitude.degrees, alt)
