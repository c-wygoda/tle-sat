from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime, timedelta, timezone
from json import dumps

from shapely import LineString, Point

from tle_sat.satellite import (
    FieldOfView,
    Satellite,
    TimeOfInterest,
    ViewAngles,
)

DEFAULT_TLE = (
    "1 99999U 24001A   24001.50000000  .00001103  00000-0  33518-4 0  9998\n"
    "2 99999 90.00000   0.7036 0003481 300.0000   0.3331 15.07816962  1770"
)


def parse_date(value: str):
    dt = datetime.fromisoformat(value)
    dt.replace(tzinfo=timezone.utc)
    return dt


def parse_positive_float(value: str):
    value: float = float(value)
    if value < 0:
        raise ArgumentTypeError("must be positive number")
    return value


def parse_latlng(value: str):
    parts = value.split(",")
    try:
        if len(parts) not in (2, 3):
            raise RuntimeError()
        return (
            float(parts[0]) % 360,
            float(parts[1]) % 180,
            float(parts[2]) if len(parts) == 3 else 0.0,
        )
    except Exception as exc:
        raise ArgumentTypeError("must be comma-separated lat,lng[,z]") from exc


def footprint(
    tle: str, t: datetime, view_angles: ViewAngles, fov: FieldOfView, pretty: bool
):
    sat = Satellite(tle)
    p0 = sat.position(t)
    poly = sat.footprint(t, view_angles, fov)

    track = LineString([sat.position(t + timedelta(seconds=s)) for s in range(10)])

    fc = dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": p0.__geo_interface__,
                    "properties": {"label": "sat"},
                },
                {
                    "type": "Feature",
                    "geometry": track.__geo_interface__,
                    "properties": {"label": "orbit direction"},
                },
                {
                    "type": "Feature",
                    "geometry": poly.__geo_interface__,
                    "properties": {
                        "label": "footprint",
                        "fov-x": fov.x,
                        "fov-y": fov.y,
                        "off-nadir-x": view_angles.across,
                        "off-nadir-y": view_angles.along,
                        "datetime": t.isoformat(),
                    },
                },
            ],
        },
        indent=2 if pretty else None,
    )
    print(fc)


def passes(tle: str, t0: datetime, t1: datetime, target: Point, pretty: bool):
    sat = Satellite(tle)
    passes = sat.passes(TimeOfInterest(t0, t1), target)
    fc = dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": sat.position(p.t).__geo_interface__,
                    "properties": {
                        "view:azimuth": p.azimuth,
                        "view:incidence": p.incidence,
                        "view:off_nadir:x": p.off_nadir.across,
                        "view:off_nadir:y": p.off_nadir.along,
                        "view:sun_azimuth": p.sun_azimuth,
                        "view:sun_elevation": p.sun_elevation,
                    },
                }
                for p in passes
            ],
        },
        indent=2 if pretty else None,
    )
    print(fc)


def orbit_track(tle: str, t0: datetime, t1: datetime, step: float, pretty: bool):
    sat = Satellite(tle)
    track = sat.orbit_track(TimeOfInterest(t0, t1), step)
    ls = dumps(
        {
            "type": "Feature",
            "geometry": track.__geo_interface__,
            "properties": {
                "start": t0.isoformat(),
                "end": t1.isoformat(),
            },
        },
        indent=2 if pretty else None,
    )
    print(ls)


def swath(
    tle: str,
    t0: datetime,
    t1: datetime,
    fov: FieldOfView,
    roll_start: float,
    roll_end: float,
    step: float,
    steps_across: int,
    pretty: bool,
):
    sat = Satellite(tle)
    geom = sat.swath(
        TimeOfInterest(t0, t1), fov, roll_start, roll_end, step, steps_across
    )

    ls = dumps(
        {
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": {
                "start": t0.isoformat(),
                "end": t1.isoformat(),
                "fov-x": fov.x,
                "fov-y": fov.y,
                "roll-start": roll_start,
                "roll-end": roll_end,
            },
        },
        indent=2 if pretty else None,
    )
    print(ls)


def main():
    now = datetime.now(timezone.utc)
    parser = ArgumentParser()
    parser.add_argument("--tle", default=DEFAULT_TLE)
    commands = parser.add_subparsers(dest="command")

    footprint_parser = commands.add_parser("footprint")
    footprint_parser.add_argument("--t", type=parse_date, default=now.isoformat())
    footprint_parser.add_argument(
        "--off-nadir-x", type=parse_positive_float, default=0.0
    )
    footprint_parser.add_argument(
        "--off-nadir-y", type=parse_positive_float, default=0.0
    )
    footprint_parser.add_argument("--fov-x", type=parse_positive_float, default=2.0)
    footprint_parser.add_argument("--fov-y", type=parse_positive_float, default=2.0)
    footprint_parser.add_argument("--pretty", action="store_true")

    passes_parser = commands.add_parser("passes")
    passes_parser.add_argument("--start", type=parse_date, default=now.isoformat())
    passes_parser.add_argument("--duration", type=parse_positive_float, default=6 * 60)
    passes_parser.add_argument("--pretty", action="store_true")
    passes_parser.add_argument("latlng", type=parse_latlng)

    orbit_track_parser = commands.add_parser("orbit-track")
    orbit_track_parser.add_argument("--start", type=parse_date, default=now.isoformat())
    orbit_track_parser.add_argument(
        "--duration", type=parse_positive_float, default=6 * 60
    )
    orbit_track_parser.add_argument("--step", type=float, default=1.0)
    orbit_track_parser.add_argument("--pretty", action="store_true")

    swath_parser = commands.add_parser("swath")
    swath_parser.add_argument("--start", type=parse_date, default=now.isoformat())
    swath_parser.add_argument("--duration", type=parse_positive_float, default=10)
    swath_parser.add_argument("--step", type=float, default=10.0)
    swath_parser.add_argument("--steps-across", type=int, default=10)
    swath_parser.add_argument("--fov-x", type=parse_positive_float, default=2.0)
    swath_parser.add_argument("--fov-y", type=parse_positive_float, default=2.0)
    swath_parser.add_argument("--roll-start", type=float, default=-15.0)
    swath_parser.add_argument("--roll-end", type=float, default=15.0)
    swath_parser.add_argument("--pretty", action="store_true")

    args = parser.parse_args()

    match args.command:
        case "footprint":
            footprint(
                args.tle,
                args.t,
                ViewAngles(args.off_nadir_y, args.off_nadir_x, 0.0),
                FieldOfView(args.fov_x, args.fov_y),
                args.pretty,
            )
        case "passes":
            passes(
                args.tle,
                args.start,
                args.start + timedelta(minutes=args.duration),
                Point(args.latlng),
                args.pretty,
            )
        case "orbit-track":
            orbit_track(
                args.tle,
                args.start,
                args.start + timedelta(minutes=args.duration),
                args.step,
                args.pretty,
            )
        case "swath":
            swath(
                args.tle,
                args.start,
                args.start + timedelta(minutes=args.duration),
                FieldOfView(args.fov_x, args.fov_y),
                args.roll_start,
                args.roll_end,
                args.step,
                args.steps_across,
                args.pretty,
            )
        case _:
            parser.print_usage()
            parser.exit(1, "\nerror: command missing\n")


if __name__ == "__main__":
    main()
