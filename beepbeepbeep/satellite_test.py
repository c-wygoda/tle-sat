from datetime import datetime, timezone

from pytest import raises
from shapely import Point

from beepbeepbeep.satellite import Satellite


def test_position_invalid_datetime(polar_tle):
    sat = Satellite(polar_tle)
    t = datetime(2024, 4, 19, 12, 0, 0, 0)
    with raises(ValueError, match="datetime must be in utc"):
        sat.position(t)


def test_position(polar_tle):
    sat = Satellite(polar_tle)
    t = datetime(2024, 4, 19, 12, 0, 0, 0, timezone.utc)

    pos = sat.position(t)
    expected = Point(152.6226382884999, 78.18538506762289, 557934.9901695348)

    assert pos.equals(expected)
