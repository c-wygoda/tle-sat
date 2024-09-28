from contextlib import nullcontext
from datetime import datetime, timedelta, timezone

from pytest import approx, mark, raises
from shapely import Point, Polygon

from tle_sat.satellite import (
    FieldOfView,
    FootprintError,
    Pass,
    Satellite,
    TimeOfInterest,
    ViewAngles,
)


def test_position_invalid_datetime(polar_tle):
    sat = Satellite(polar_tle)
    t = datetime(2024, 4, 19, 12, 0, 0, 0)

    with raises(ValueError, match="datetime must be in utc"):
        sat.position(t)


@mark.parametrize(
    "t, p",
    (
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            Point(152.6226382884999, 78.18538506762289, 557934.9901695348),
        ),
    ),
)
def test_position(polar_tle, t, p):
    sat = Satellite(polar_tle)

    pos = sat.position(t)

    assert pos.equals(p)


@mark.parametrize(
    "t,o,v",
    (
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            [-5, 0, 0],
            ViewAngles(-0.3, -11.5, 11.555752058027988),
        ),
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            [5, 0, 0],
            ViewAngles(-0.7, 11.5, 11.555752058027988),
        ),
    ),
)
def test_view_angles(polar_tle, t, o, v):
    sat = Satellite(polar_tle)
    p = sat.position(t)

    on = sat.view_angles(t, Point(p.x + o[0], p.y + o[1], o[2]))

    assert on.across == approx(v.across, abs=0.1)
    assert on.along == approx(v.along, abs=0.1)
    assert on.off_nadir == approx(v.off_nadir, abs=0.1)


@mark.parametrize(
    "t, v, f, expectation",
    (
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            ViewAngles(0, 45, 45),
            FieldOfView(2, 2),
            nullcontext(
                Polygon(
                    (
                        (127.7379246591503, 76.95181009374622),
                        (129.391022866435, 77.1132119968597),
                        (128.95920974658245, 77.3478604621005),
                        (127.26201922293443, 77.19358515346873),
                        (127.7379246591503, 76.95181009374622),
                    )
                )
            ),
        ),
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            ViewAngles(0, 90, 45),
            FieldOfView(2, 2),
            raises(FootprintError, match="footprint not fully on earth"),
        ),
    ),
)
def test_footprint(polar_tle, t, v, f, expectation):
    sat = Satellite(polar_tle)

    with expectation as e:
        footprint = sat.footprint(t, v, f)
        assert e.equals(footprint)


@mark.parametrize(
    "t,target,passes",
    (
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            Point(151.6226382884999, 78.18538506762289, 0),
            [
                Pass(
                    t=datetime(2024, 4, 19, 10, 24, 10, 13017, tzinfo=timezone.utc),
                    view_angles=ViewAngles(
                        along=0.003286938613857222,
                        across=-43.59378581863903,
                        off_nadir=43.59378587058238,
                    ),
                    azimuth=246.15947980920845,
                    incidence=48.56258642963941,
                    sun_azimuth=309.1665849748783,
                    sun_elevation=4.040713411924881,
                ),
                Pass(
                    t=datetime(2024, 4, 19, 12, 0, 0, 14, tzinfo=timezone.utc),
                    view_angles=ViewAngles(
                        along=0.012069782991351924,
                        across=-2.3465815282339757,
                        off_nadir=2.3466124994902096,
                    ),
                    azimuth=269.51084026095725,
                    incidence=2.5513557385532977,
                    sun_azimuth=332.4719846650721,
                    sun_elevation=0.9843777205236294,
                ),
                Pass(
                    t=datetime(2024, 4, 19, 13, 35, 18, 176643, tzinfo=timezone.utc),
                    view_angles=ViewAngles(
                        along=0.036206722030285,
                        across=41.38571967607966,
                        off_nadir=41.38572698419228,
                    ),
                    azimuth=113.21914991193279,
                    incidence=45.954108011810156,
                    sun_azimuth=355.78438524781876,
                    sun_elevation=-0.318769078583524,
                ),
            ],
        ),
    ),
)
def test_passes(polar_tle, t, target, passes):
    sat = Satellite(polar_tle)

    calculated = sat.passes(
        TimeOfInterest(t - timedelta(hours=2), t + timedelta(hours=2)),
        target,
    )
    assert calculated == passes
