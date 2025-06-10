from contextlib import nullcontext
from datetime import datetime, timedelta, timezone

from numpy import around
from pytest import approx, mark, raises
from shapely import LineString, Point, Polygon, is_ccw
from shapely.geometry import mapping, shape

from tle_sat.satellite import (
    FieldOfView,
    FootprintError,
    Pass,
    Satellite,
    TimeOfInterest,
    ViewAngles,
)


def _assert_pass_equals(p1: Pass, p2: Pass):
    p1l = [
        p1.view_angles.across,
        p1.view_angles.along,
        p1.view_angles.off_nadir,
        p1.azimuth,
        p1.incidence,
        p1.sun_azimuth,
        p1.sun_elevation,
    ]
    p2l = [
        p2.view_angles.across,
        p2.view_angles.along,
        p2.view_angles.off_nadir,
        p2.azimuth,
        p2.incidence,
        p2.sun_azimuth,
        p2.sun_elevation,
    ]
    assert p1l == approx(p2l)


def _precision(geom: Polygon | LineString, precision=6):
    geojson = mapping(geom)
    geojson["coordinates"] = around(geojson["coordinates"], precision)
    return shape(geojson)


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
            Point(
                (152.62265368846292, 78.18538506751914, 557934.9901695215),
            ),
        ),
    ),
)
def test_position(polar_tle, t, p):
    sat = Satellite(polar_tle)

    pos = sat.position(t)

    assert _precision(pos, 7) == _precision(p, 7)


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
                        (175.6036122014024, 76.98714113663245),
                        (177.22396192537641, 76.81734966236745),
                        (177.71904671819485, 77.05665979118999),
                        (176.0554747349726, 77.21951692944646),
                        (175.6036122014024, 76.98714113663245),
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
        assert _precision(e, 8).equals(_precision(footprint, 8))

        if isinstance(e, Polygon):
            assert is_ccw(footprint.exterior)
            assert all(not is_ccw(interior) for interior in e.interiors)


@mark.parametrize(
    "target,t,footprint",
    (
        (
            Point(13, 53, 0),
            datetime(2024, 4, 19, 21, 39, 59, tzinfo=timezone.utc),
            Polygon(
                (
                    (12.758568226651015, 52.90986634446963),
                    (13.2049640434975, 52.87415743814914),
                    (13.249443506713275, 53.09024543254505),
                    (12.799711385298904, 53.12031251783848),
                    (12.758568226651015, 52.90986634446963),
                )
            ),
        ),
    ),
)
def test_pass_footprint(polar_tle, target: Point, t: datetime, footprint: Polygon):
    sat = Satellite(polar_tle)

    passes = sat.passes(
        TimeOfInterest(t - timedelta(minutes=15), t + timedelta(minutes=15)), target
    )
    assert len(passes) == 1
    p = passes[0]

    actual_footprint = sat.footprint(t=p.t, view_angles=p.view_angles)

    assert _precision(footprint, 8).equals(_precision(actual_footprint, 8))
    assert actual_footprint.contains(target)
    assert _precision(footprint.centroid, 2).equals(_precision(target, 2))


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
                        along=0.0032728828939548784,
                        across=-43.59380106660251,
                        off_nadir=43.59380111810252,
                    ),
                    azimuth=246.15947939300213,
                    incidence=48.562604571072775,
                    sun_azimuth=309.16656999047194,
                    sun_elevation=4.040715864976827,
                ),
                Pass(
                    t=datetime(2024, 4, 19, 12, 0, 0, 14, tzinfo=timezone.utc),
                    view_angles=ViewAngles(
                        along=0.012069660121329796,
                        across=-2.346617620377203,
                        off_nadir=2.3466485905244348,
                    ),
                    azimuth=269.5108327202487,
                    incidence=2.551394982549624,
                    sun_azimuth=332.47196963951467,
                    sun_elevation=0.9843791778223044,
                ),
                Pass(
                    t=datetime(2024, 4, 19, 13, 35, 18, 176643, tzinfo=timezone.utc),
                    view_angles=ViewAngles(
                        along=0.03622040626905018,
                        across=41.385703005796536,
                        off_nadir=41.385710319442424,
                    ),
                    azimuth=113.21915039421725,
                    incidence=45.95408845935828,
                    sun_azimuth=355.78437020843967,
                    sun_elevation=-0.31876884759361007,
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

    for p1, p2 in zip(calculated, passes):
        _assert_pass_equals(p1, p2)


@mark.parametrize(
    "kwargs,track",
    (
        (
            {
                "toi": TimeOfInterest(
                    datetime(2024, 10, 15, 12, 0, 0, 0, timezone.utc),
                    datetime(2024, 10, 15, 12, 0, 10, 0, timezone.utc),
                )
            },
            LineString(
                (
                    (156.1914593403337, -79.17285283372755, 567798.5875704706),
                    (156.18728126576914, -79.1105217749056, 567788.6547832417),
                    (156.18310319120457, -79.04819034745724, 567778.6756299192),
                    (156.17892511663868, -78.98585854971941, 567768.6501484425),
                    (156.17474704207285, -78.92352637940978, 567758.5783768552),
                    (156.17056896750836, -78.86119383466138, 567748.4603534729),
                    (156.16639089294247, -78.79886091422956, 567738.2961168883),
                    (156.16221281837662, -78.7365276156297, 567728.0857057112),
                    (156.15803474381207, -78.6741939369995, 567717.8291588426),
                    (156.1538566692462, -78.6118598770988, 567707.5265154759),
                    (156.1496785946817, -78.54952543344785, 567697.1778148033),
                )
            ),
        ),
        (
            {
                "toi": TimeOfInterest(
                    datetime(2024, 10, 15, 12, 0, 0, 0, timezone.utc),
                    datetime(2024, 10, 15, 12, 1, 0, 0, timezone.utc),
                ),
                "step": 10,
            },
            LineString(
                (
                    (156.1914593403337, -79.17285283372755, 567798.5875704706),
                    (156.1496785946817, -78.54952543344785, 567697.1778148033),
                    (156.1078978490296, -77.92615949437118, 567591.1664422166),
                    (156.06611710337617, -77.30275316801038, 567480.5940142936),
                    (156.02433635772672, -76.67930462172131, 567365.5030352279),
                    (155.9825556120746, -76.05581204157784, 567245.9379344286),
                    (155.9407748664226, -75.43227363089389, 567121.9450473901),
                )
            ),
        ),
    ),
)
def test_orbit_track(polar_tle, kwargs, track):
    sat = Satellite(polar_tle)

    calculated = sat.orbit_track(**kwargs)
    assert _precision(calculated, 6) == _precision(track, 6)


@mark.parametrize(
    "kwargs,swath",
    (
        (
            {
                "toi": TimeOfInterest(
                    datetime(2024, 10, 15, 12, 0, 0, 0, timezone.utc),
                    datetime(2024, 10, 15, 12, 0, 10, 0, timezone.utc),
                ),
                "fov": FieldOfView(2, 2),
            },
            Polygon(
                (
                    (156.67365761439612, -79.26013698492127),
                    (156.57841233449656, -79.26048755802556),
                    (156.48317183508286, -79.26081028731662),
                    (156.38793395355083, -79.26110518749252),
                    (156.29269652755883, -79.26137227033416),
                    (156.19745739483662, -79.26161154470726),
                    (156.10221439299352, -79.26182301656364),
                    (156.006965359327, -79.26200668894187),
                    (155.91170813063107, -79.26216256196724),
                    (155.8164405430045, -79.26229063285119),
                    (155.7211604316591, -79.26239089588977),
                    (155.71902608469878, -79.1736112688249),
                    (155.7175277407713, -79.11128866663313),
                    (155.71599876193048, -79.04896567023418),
                    (155.71443966797176, -78.98664227835933),
                    (155.71285096699776, -78.92431848973247),
                    (155.71123315577717, -78.86199430224252),
                    (155.7095867199707, -78.79966971501283),
                    (155.70791213452264, -78.73734472653915),
                    (155.70620986395065, -78.6750193346902),
                    (155.7044803625537, -78.61269353856945),
                    (155.70272407477262, -78.55036733665398),
                    (155.70020500262126, -78.46159986199008),
                    (155.7889385058702, -78.46149190992259),
                    (155.87766028097946, -78.46135584928601),
                    (155.96637235301478, -78.46119168532044),
                    (156.05507674619756, -78.4609994204004),
                    (156.1437754840883, -78.46077905403604),
                    (156.23247058977083, -78.46053058287379),
                    (156.32116408603534, -78.46025400069634),
                    (156.40985799556208, -78.4599492984219),
                    (156.49855434110495, -78.45961646410294),
                    (156.58725514567465, -78.45925548292418),
                    (156.5965421722267, -78.548005082268),
                    (156.60314151880928, -78.61034393102135),
                    (156.60976764620642, -78.67268237734349),
                    (156.6164209987608, -78.73502042273991),
                    (156.62310203068236, -78.79735806808971),
                    (156.62981120638932, -78.85969531550688),
                    (156.6365490007245, -78.92203216647829),
                    (156.64331589925328, -78.98436862186306),
                    (156.65011239863813, -79.04670468375495),
                    (156.65693900687347, -79.10904035341271),
                    (156.66379624364902, -79.17137563208748),
                    (156.67365761439612, -79.26013698492127),
                )
            ),
        ),
        (
            {
                "toi": TimeOfInterest(
                    datetime(2024, 10, 15, 12, 0, 0, 0, timezone.utc),
                    datetime(2024, 10, 15, 12, 1, 0, 0, timezone.utc),
                ),
                "fov": FieldOfView(2, 2),
                "step": 10,
                "steps_across": 3,
            },
            Polygon(
                (
                    (156.67365761439612, -79.26013698492127),
                    (156.35618820104966, -79.26119730542354),
                    (156.03871584093721, -79.261948553579),
                    (155.7211604316591, -79.26239089588977),
                    (155.71902608469878, -79.1736112688249),
                    (155.70272407477262, -78.55036733665398),
                    (155.68377916300173, -77.92708264629658),
                    (155.6625803627087, -77.30375564318369),
                    (155.63944389752032, -76.68038473051257),
                    (155.61462946435182, -76.05696828805078),
                    (155.5883523229798, -75.4335046767285),
                    (155.58452572744008, -75.34480954527784),
                    (155.81810640202667, -75.34406502833158),
                    (156.05162332226413, -75.34307434748894),
                    (156.28514051437764, -75.34183724754735),
                    (156.2931266806678, -75.43051475045617),
                    (156.3504076959189, -76.0541031166526),
                    (156.40915111504924, -76.67764472084889),
                    (156.46957215305076, -77.30114118505203),
                    (156.53193045283052, -77.92459411233826),
                    (156.5965421722267, -78.548005082268),
                    (156.66379624364902, -79.17137563208748),
                    (156.67365761439612, -79.26013698492127),
                )
            ),
        ),
    ),
)
def test_swath(polar_tle, kwargs, swath):
    sat = Satellite(polar_tle)

    calculated = sat.swath(**kwargs)
    assert _precision(calculated, 7) == _precision(swath, 7)
