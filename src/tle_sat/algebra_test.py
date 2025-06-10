import numpy as np
from pytest import approx, mark

from tle_sat.algebra import (
    project_vector_onto_plane,
    rotate,
    unit_vector,
    vector_angle,
    vector_angle_signed,
)


@mark.parametrize(
    "v, uv",
    (
        (np.array([2, 0, 0]), np.array([1, 0, 0])),
        (np.array([1, 0, 0]), np.array([1, 0, 0])),
        (np.array([0, 0, 0]), np.array([0, 0, 0])),
    ),
)
def test_unit_vector(v, uv):
    assert (unit_vector(v) == uv).all()


@mark.parametrize(
    "v1, v2, angle",
    (
        (np.array([2, 0, 0]), np.array([2, 0, 0]), 0),
        (np.array([2, 0, 0]), np.array([2, 2, 0]), 45),
        (np.array([2, 0, 0]), np.array([0, 2, 0]), 90),
        (np.array([2, 0, 0]), np.array([-2, 2, 0]), 135),
        (np.array([2, 0, 0]), np.array([-2, 0, 0]), 180),
    ),
)
def test_vector_angle(v1, v2, angle):
    assert np.degrees(vector_angle(v1, v2)) == approx(angle)


@mark.parametrize(
    "v1, v2, n, angle",
    (
        (np.array([2, 0, 0]), np.array([2, 2, 0]), np.array([0, 0, 1]), 45),
        (np.array([2, 0, 0]), np.array([-2, 2, 0]), np.array([0, 0, 1]), 135),
        (np.array([2, 0, 0]), np.array([-2, -2, 0]), np.array([0, 0, 1]), -135),
        (np.array([2, 0, 0]), np.array([2, -2, 0]), np.array([0, 0, 1]), -45),
    ),
)
def test_vector_angle_signed(v1, v2, n, angle):
    assert np.degrees(vector_angle_signed(v1, v2, n)) == approx(angle)


@mark.parametrize(
    "v, n, r", ((np.array([10, 10, 10]), np.array([0, 0, 1]), np.array([10, 10, 0])),)
)
def test_project_vector_onto_plane(v, n, r):
    assert (project_vector_onto_plane(v, n) == r).all()


@mark.parametrize(
    "v,axis,theta,r",
    (
        (
            np.array([1, 1, 1]),
            np.array([10, 0, 0]),
            np.radians(90),
            np.array([1.0, -1.0, 1.0]),
        ),
        (
            np.array([1, 1, 1]),
            np.array([10, 0, 0]),
            np.radians(-90),
            np.array([1.0, 1.0, -1.0]),
        ),
    ),
)
def test_rotation_matrix(v, axis, theta, r):
    rotated = rotate(v, axis, theta)
    assert rotated == approx(r)
