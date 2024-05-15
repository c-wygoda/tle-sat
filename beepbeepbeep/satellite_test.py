from datetime import datetime, timezone

import numpy as np
from pytest import approx, mark, raises
from shapely import Point

from beepbeepbeep.satellite import Satellite


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
    "t,o,a",
    (
        (datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc), [-5, 0, 0], [-0.3, -11.5]),
        (datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc), [5, 0, 0], [-0.7, 11.5]),
    ),
)
def test_off_nadir(polar_tle, t, o, a):
    sat = Satellite(polar_tle)
    p = sat.position(t)

    on = sat.off_nadir(t, Point(p.x + o[0], p.y + o[1], o[2]))

    assert np.degrees(on) == approx(a, abs=0.1)
