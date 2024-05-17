from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from json import dumps

from shapely import LineString

from beepbeepbeep.satellite import FieldOfView, OffNadir, Satellite

DEFAULT_TLE = (
    "1 99999U 24001A   24001.50000000  .00001103  00000-0  33518-4 0  9998\n"
    "2 99999 90.00000   0.7036 0003481 300.0000   0.3331 15.07816962  1770"
)


def parse_date(value: str):
    dt = datetime.fromisoformat(value)
    dt.replace(tzinfo=timezone.utc)
    return dt


def footprint(tle: str, t: datetime, off_nadir: OffNadir, fov: FieldOfView):
    sat = Satellite(tle)
    p0 = sat.position(t)
    poly = sat.footprint(t, off_nadir, fov)

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
                        "off-nadir-x": off_nadir.across,
                        "off-nadir-y": off_nadir.along,
                        "datetime": t.isoformat(),
                    },
                },
            ],
        }
    )
    print(fc)


def main():
    parser = ArgumentParser()
    parser.add_argument("--tle", default=DEFAULT_TLE)
    parser.add_argument(
        "--t", type=parse_date, default=datetime.now(timezone.utc).isoformat()
    )
    parser.add_argument("--off-nadir-x", type=float, default=0.0)
    parser.add_argument("--off-nadir-y", type=float, default=0.0)
    parser.add_argument("--fov-x", type=float, default=2.0)
    parser.add_argument("--fov-y", type=float, default=2.0)

    args = parser.parse_args()

    footprint(
        args.tle,
        args.t,
        OffNadir(args.off_nadir_y, args.off_nadir_x),
        FieldOfView(args.fov_x, args.fov_y),
    )


if __name__ == "__main__":
    main()
