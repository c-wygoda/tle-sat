from pytest import fixture


@fixture
def polar_tle():
    """
    inclination: 90°
    altitude: 550km
    argument of perigee: 300°
    launched: 2024-01-01T12:00:00
    """
    yield (
        "1 99999U 24001A   24001.50000000  .00001103  00000-0  33518-4 0  9998\n"
        "2 99999 90.00000   0.7036 0003481 300.0000   0.3331 15.07816962  1770"
    )
