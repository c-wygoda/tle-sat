from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from shapely import Point, Polygon
from skyfield.geometry import line_and_ellipsoid_intersection
from skyfield.positionlib import Distance, Geocentric
from skyfield.sgp4lib import EarthSatellite
from skyfield.toposlib import GeographicPosition, ITRSPosition, itrs, wgs84

from beepbeepbeep.algebra import (
    project_vector_onto_plane,
    rotate,
    unit_vector,
    vector_angle_signed,
)


def assert_is_utc(t: datetime):
    if t.tzinfo != timezone.utc:
        raise ValueError("datetime must be in utc")


@dataclass
class OffNadir:
    along: float
    across: float


@dataclass
class FieldOfView:
    x: float
    y: float


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

    def off_nadir(self, t: datetime, target: Point) -> OffNadir:
        sat_pos = self.at(t)
        sat_loc, sat_velocity = sat_pos.frame_xyz_and_velocity(itrs)
        target_loc: Distance = wgs84.latlon(target.y, target.x, target.z).itrs_xyz
        nadir_loc: Distance = wgs84.subpoint_of(sat_pos).itrs_xyz
        target_vector = target_loc.m - sat_loc.m
        nadir_vector = nadir_loc.m - sat_loc.m
        orbital_plane_normal = np.cross(nadir_vector, sat_velocity.km_per_s)
        cross_plane_normal = np.cross(orbital_plane_normal, nadir_vector)

        target_cross_vector = project_vector_onto_plane(
            target_vector,
            cross_plane_normal,
        )
        target_along_vector = project_vector_onto_plane(
            target_vector,
            orbital_plane_normal,
        )

        cross_angle = np.degrees(
            vector_angle_signed(
                nadir_vector,
                target_cross_vector,
                cross_plane_normal,
            )
        )
        along_angle = np.degrees(
            vector_angle_signed(
                nadir_vector,
                target_along_vector,
                orbital_plane_normal,
            )
        )
        return OffNadir(along_angle, cross_angle)

    def footprint(
        self, t: datetime, off_nadir: OffNadir, fov=FieldOfView(2.0, 2.0)
    ) -> Polygon:
        sat_pos = self.at(t)
        sat_loc, sat_velocity = sat_pos.frame_xyz_and_velocity(itrs)
        nadir_loc: Distance = wgs84.subpoint_of(sat_pos).itrs_xyz

        nadir_vector = nadir_loc.m - sat_loc.m
        orbital_plane_normal = np.cross(nadir_vector, sat_velocity.m_per_s)
        cross_plane_normal = np.cross(orbital_plane_normal, nadir_vector)

        radii = [wgs84.radius.m, wgs84.radius.m, wgs84.polar_radius.m]

        def ray(front: bool, right: bool) -> GeographicPosition:
            a = off_nadir.along + 0.5 * (fov.y if front else -fov.y)
            b = -off_nadir.across + 0.5 * (-fov.x if right else fov.x)

            vector = rotate(nadir_vector, orbital_plane_normal, np.radians(a))
            vector = rotate(vector, cross_plane_normal, np.radians(b))

            intersection = line_and_ellipsoid_intersection(
                sat_loc.m, unit_vector(vector), radii
            )

            pos = ITRSPosition(Distance(m=intersection)).at(sat_pos.t)
            return wgs84.geographic_position_of(pos)

        fr = ray(True, True)
        fl = ray(True, False)
        rl = ray(False, False)
        rr = ray(False, True)

        poly = Polygon(
            [[p.longitude.degrees, p.latitude.degrees] for p in (fr, fl, rl, rr, fr)]
        )
        return poly
