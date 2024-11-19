from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isnan

import numpy as np
from platformdirs import user_cache_dir
from shapely import LineString, Point, Polygon
from skyfield.api import Loader, Time
from skyfield.geometry import line_and_ellipsoid_intersection
from skyfield.jpllib import ChebyshevPosition
from skyfield.positionlib import Distance, Geocentric
from skyfield.sgp4lib import EarthSatellite
from skyfield.toposlib import ITRSPosition, itrs, wgs84
from skyfield.vectorlib import VectorSum

from tle_sat.algebra import (
    project_vector_onto_plane,
    rotate,
    unit_vector,
    vector_angle,
    vector_angle_signed,
)


def assert_is_utc(t: datetime):
    if t.tzinfo != timezone.utc:
        raise ValueError("datetime must be in utc")


@dataclass
class ViewAngles:
    along: float
    across: float
    off_nadir: float


@dataclass
class FieldOfView:
    x: float
    y: float


@dataclass
class TimeOfInterest:
    start: datetime
    end: datetime


@dataclass
class Pass:
    t: datetime
    view_angles: ViewAngles
    azimuth: float
    incidence: float
    sun_azimuth: float
    sun_elevation: float


class FootprintError(OverflowError):
    """"""


class Satellite:
    model: EarthSatellite
    sun: ChebyshevPosition
    earth: VectorSum

    def __init__(
        self,
        tle: str,
        cache_dir: str | None = None,
        ephem_filename="de421.bsp",
    ):
        lines = tle.splitlines()
        match len(lines):
            case 2:
                self.model = EarthSatellite(line1=lines[0], line2=lines[1])
            case 3:
                self.model = EarthSatellite(line1=lines[1], line2=lines[2])
            case _:
                raise RuntimeError("tle strings must be 2 or 3 lines")

        ephem = Loader(cache_dir or user_cache_dir(__package__))(ephem_filename)
        self.sun = ephem["Sun"]
        self.earth = ephem["Earth"]

    def at(self, t: datetime | Time) -> Geocentric:
        if isinstance(t, datetime):
            assert_is_utc(t)
            t = self.model.ts.from_datetime(t)
        return self.model.at(t)

    def position(self, t: datetime | Time) -> Point:
        pos = self.at(t)
        ll = wgs84.subpoint_of(pos)
        alt = wgs84.height_of(pos).m
        return Point(ll.longitude.degrees, ll.latitude.degrees, alt)

    def view_angles(self, t: datetime | Time, target: Point) -> ViewAngles:
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
        off_nadir_angle = np.degrees(vector_angle(nadir_vector, target_vector))

        return ViewAngles(along_angle, cross_angle, off_nadir_angle)

    def los(self, t: datetime | Time, roll: float, pitch: float):
        sat_pos = self.at(t)
        sat_loc, sat_velocity = sat_pos.frame_xyz_and_velocity(itrs)
        nadir_loc: Distance = wgs84.subpoint_of(sat_pos).itrs_xyz
        nadir_vector = nadir_loc.m - sat_loc.m
        orbital_plane_normal = np.cross(nadir_vector, sat_velocity.m_per_s)
        cross_plane_normal = np.cross(orbital_plane_normal, nadir_vector)

        vector = rotate(nadir_vector, orbital_plane_normal, np.radians(pitch))
        vector = rotate(vector, cross_plane_normal, np.radians(roll))

        radii = [wgs84.radius.m, wgs84.radius.m, wgs84.polar_radius.m]
        intersection = line_and_ellipsoid_intersection(
            sat_loc.m, unit_vector(vector), radii
        )

        pos = ITRSPosition(Distance(m=intersection)).at(sat_pos.t)
        if any((isnan(p) for p in pos.position.m)):
            raise OverflowError("LOS not intersecting earth")
        geo_pos = wgs84.geographic_position_of(pos)
        return Point(geo_pos.longitude.degrees, geo_pos.latitude.degrees)

    def footprint(
        self, t: datetime | Time, view_angles: ViewAngles, fov=FieldOfView(2.0, 2.0)
    ) -> Polygon:
        try:
            fr = self.los(
                t,
                -view_angles.across - 0.5 * fov.x,
                view_angles.along + 0.5 * fov.y,
            )
            fl = self.los(
                t,
                -view_angles.across + 0.5 * fov.x,
                view_angles.along + 0.5 * fov.y,
            )
            rl = self.los(
                t,
                -view_angles.across + 0.5 * fov.x,
                view_angles.along - 0.5 * fov.y,
            )
            rr = self.los(
                t,
                -view_angles.across - 0.5 * fov.x,
                view_angles.along - 0.5 * fov.y,
            )
        except OverflowError as exc:
            raise FootprintError("footprint not fully on earth") from exc

        return Polygon([fr, fl, rl, rr, fr])

    def passes(self, toi: TimeOfInterest, target: Point) -> list[Pass]:
        assert_is_utc(toi.start)
        assert_is_utc(toi.end)

        topos = wgs84.latlon(target.y, target.x, target.z)
        pass_events = self.model.find_events(
            topos,
            self.model.ts.from_datetime(toi.start),
            self.model.ts.from_datetime(toi.end),
        )

        los = self.model - topos
        loc = self.earth + topos

        def build_pass(t: Time):
            alt, az, _ = los.at(t).altaz()
            sun_alt, sun_az, _ = loc.at(t).observe(self.sun).apparent().altaz()

            return Pass(
                t=t.utc_datetime(),
                view_angles=self.view_angles(t, target),
                azimuth=(az.degrees + 180.0) % 360.0,
                incidence=90.0 - alt.degrees,
                sun_azimuth=sun_az.degrees,
                sun_elevation=sun_alt.degrees,
            )

        return [build_pass(pass_events[0][i]) for i in range(1, len(pass_events[0]), 3)]

    def orbit_track(self, toi: TimeOfInterest, step: float = 1.0):
        assert_is_utc(toi.start)
        assert_is_utc(toi.end)
        if step <= 0.0:
            raise RuntimeError("step must be > 0")

        t = toi.start
        points = []
        while True:
            t = min(t, toi.end)

            sat_pos = self.at(t)
            nadir_pos = wgs84.geographic_position_of(sat_pos)
            points.append(
                Point(
                    nadir_pos.longitude.degrees,
                    nadir_pos.latitude.degrees,
                    nadir_pos.elevation.m,
                )
            )

            if t == toi.end:
                break
            t += timedelta(seconds=step)
        return LineString(points)

    def swath(
        self,
        toi: TimeOfInterest,
        fov: FieldOfView,
        roll_0: float = 0.0,
        roll_1: float = 0.0,
        step: float = 1.0,
        steps_across: int = 10,
    ):
        assert_is_utc(toi.start)
        assert_is_utc(toi.end)
        if step <= 0.0:
            raise RuntimeError("step must be > 0")
        if steps_across <= 0:
            raise RuntimeError("steps_across must be > 0")

        t = toi.start
        points_left = []
        points_right = []
        while True:
            t = min(t, toi.end)
            for right in (False, True):
                ona = roll_1 if right else roll_0
                roll = (ona) + (1 if right else -1) * 0.5 * fov.x
                (points_right if right else points_left).append(self.los(t, roll, 0))
            if t == toi.end:
                break
            t += timedelta(seconds=step)
        points_left.reverse()

        width = roll_1 - roll_0 + fov.x
        steps = steps_across + 1
        step_width = width / steps_across
        points_rear = [
            self.los(
                toi.start,
                roll=(roll_0 - 0.5 * fov.x) + i * step_width,
                pitch=-0.5 * fov.y,
            )
            for i in range(steps)
        ]
        points_front = [
            self.los(
                toi.end,
                roll=(roll_0 - 0.5 * fov.x) + i * step_width,
                pitch=0.5 * fov.y,
            )
            for i in range(steps - 1, -1, -1)
        ]

        pts = points_rear + points_right + points_front + points_left
        pts += [pts[0]]
        return Polygon(pts)
