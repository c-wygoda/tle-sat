import numpy as np
import numpy.typing as npt


def unit_vector(v: npt.ArrayLike) -> npt.ArrayLike:
    n = np.linalg.norm(v)
    return v / n if n != 0 else v


def vector_angle(v1: npt.ArrayLike, v2: npt.ArrayLike) -> np.float64:
    """
    Calculate the angle between vectors v1 and v2.

    Args:
        v1 (npt.ArrayLike)
        v2 (npt.ArrayLike)
    """
    return np.arccos(np.dot(unit_vector(v1), unit_vector(v2)))


def vector_angle_signed(
    v1: npt.ArrayLike, v2: npt.ArrayLike, n: npt.ArrayLike
) -> np.float64:
    """
    Calculate the signed angle between vectors v1 and v2 in the plane described
    by the normal vector n. A positive result is a clockwise angle from v1 to v2,
    a negative result a counterclockwise angle from v1 to v2.

    Args:
        v1 (npt.ArrayLike)
        v2 (npt.ArrayLike)
        look (npt.ArrayLike)
    """
    sign = np.array(np.sign(np.cross(v1, v2).dot(n)))
    sign[sign == 0] = 1

    return sign * vector_angle(v1, v2)


def project_vector_onto_plane(
    v: npt.ArrayLike, plane_normal: npt.ArrayLike
) -> npt.ArrayLike:
    d = np.dot(v, plane_normal) / np.dot(plane_normal, plane_normal)
    return v - d * plane_normal
