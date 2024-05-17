from datetime import datetime, timedelta, timezone

from pytest import approx, mark, raises
from shapely import Point, Polygon

from beepbeepbeep.satellite import (
    FieldOfView,
    OffNadir,
    Pass,
    Satellite,
    TimeOfInterest,
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
    "t,o,e",
    (
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            [-5, 0, 0],
            OffNadir(-0.3, -11.5),
        ),
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            [5, 0, 0],
            OffNadir(-0.7, 11.5),
        ),
    ),
)
def test_off_nadir(polar_tle, t, o, e):
    sat = Satellite(polar_tle)
    p = sat.position(t)

    on = sat.off_nadir(t, Point(p.x + o[0], p.y + o[1], o[2]))

    assert on.across == approx(e.across, abs=0.1)
    assert on.along == approx(e.along, abs=0.1)


@mark.parametrize(
    "t, o, f, e",
    (
        (
            datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc),
            OffNadir(0, 45),
            FieldOfView(2, 2),
            Polygon(
                (
                    (127.7379246591503, 76.95181009374622),
                    (129.391022866435, 77.1132119968597),
                    (128.95920974658245, 77.3478604621005),
                    (127.26201922293443, 77.19358515346873),
                    (127.7379246591503, 76.95181009374622),
                )
            ),
        ),
    ),
)
def test_footprint(polar_tle, t, o, f, e):
    sat = Satellite(polar_tle)

    footprint = sat.footprint(t, o, f)

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
                    off_nadir=OffNadir(
                        along=0.003286938613857222,
                        across=-43.59378581863903,
                    ),
                    azimuth=246.15947980920845,
                    incidence=48.56258642963941,
                    sun_azimuth=309.1665849748783,
                    sun_elevation=4.040713411924881,
                ),
                Pass(
                    t=datetime(2024, 4, 19, 12, 0, 0, 14, tzinfo=timezone.utc),
                    off_nadir=OffNadir(
                        along=0.012069782991351924,
                        across=-2.3465815282339757,
                    ),
                    azimuth=269.51084026095725,
                    incidence=2.5513557385532977,
                    sun_azimuth=332.4719846650721,
                    sun_elevation=0.9843777205236294,
                ),
                Pass(
                    t=datetime(2024, 4, 19, 13, 35, 18, 176643, tzinfo=timezone.utc),
                    off_nadir=OffNadir(
                        along=0.036206722030285,
                        across=41.38571967607966,
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
