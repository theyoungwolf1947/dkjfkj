# coding=utf-8
"""
geometry module
Contains utility functions for computational geometry
"""

from typing import Optional, Any, Sequence, Dict
import numpy as np
import shapely as sp
from shapely.geometry import Point, LineString, LinearRing
from random import randint

from libs.utils.custom_types import Vector2d, Coords2d


def magnitude(vector: Vector2d) -> float:
    """
    Returns the magnitude of a vectorector
    :param vector: vector as a tuple
    :return: float
    """
    mag = np.sqrt(vector[0]**2 + vector[1]**2)
    return mag


def direction_vector(point_1: Coords2d, point_2: Coords2d) -> Vector2d:
    """
    Convenient function to calculate the direction vector between two points
    :return: tuple containing x, y values
    """
    output_vector = point_2[0] - point_1[0], point_2[1] - point_1[1]
    return normalized_vector(output_vector)


def ccw_angle(vector_1: Vector2d, vector_2: Optional[Vector2d] = None) -> float:
    """
    Calculates the counter clockwise angle (in degrees) between vector_1 and vector_2
    if only one vector is given returns the ccw angle of the vector between [O, 360[
    :param vector_1: tuple
    :param vector_2: tuple
    :return: float, angle in deg
    """
    ang1 = np.arctan2(*vector_1[::-1])
    ang2 = ang1 if vector_2 is None else np.arctan2(*vector_2[::-1])
    ang1 = 0 if vector_2 is None else ang1
    ang = np.rad2deg((ang2 - ang1) % (2 * np.pi))
    # WARNING : we round the angle to prevent floating point error
    return np.round(ang) % 360.0


def nearest_point(point: Point, perimeter: LinearRing) -> Point:
    """
    Returns the first nearest point of a perimeter from a specific point
    :param point: shapely point
    :param perimeter:  shapely linearRing
    :return: shapely point
    """
    dist = perimeter.project(point)
    nearest_p = perimeter.interpolate(dist)
    return nearest_p


def point_dict_to_tuple(point_as_dict: Dict[str, str]) -> Coords2d:
    """
    Transform a point as a dict into a point as a tuple
    ex: {'x': 2.0, 'y': 3.2 } -> (2.0, 3.2)
    :param point_as_dict:
    :return: tuple of floats
    """
    return point_as_dict['x'], point_as_dict['y']


def move_point(point: Coords2d, vector: Vector2d, coeff: Optional[float] = 1.0) -> Coords2d:
    """
    Utility function to translate a point according to a vector direction
    :param point:
    :param vector:
    :param coeff:
    :return: a coordinates tuple
    """
    _x = point[0] + vector[0] * coeff
    _y = point[1] + vector[1] * coeff
    return _x, _y


def scale_line(line_string: LineString, ratio: float) -> LineString:
    """
    Returns a slightly longer lineString
    :param line_string:
    :param ratio:
    :return: LineString:
    """
    # noinspection PyUnresolvedReferences
    return sp.affinity.scale(line_string, ratio, ratio)


def unit_vector(angle: float) -> Vector2d:
    """
    Returns a unit vector oriented according to angle
    :param angle: float : an angle in degrees
    :return: a vector tuple
    """
    # convert angle to range [-pi, pi]
    angle %= 360
    angle = angle - 360 * np.sign(angle) if np.abs(angle) > 180 else angle
    rad = angle * np.pi / 180
    return np.cos(rad), np.sin(rad)


def normal(vector: Vector2d) -> Vector2d:
    """
    A CCW normal of the edge of length 1
    :return: a tuple containing x, y values
    """
    normal_vector = -vector[1], vector[0]
    return normalized_vector(normal_vector)


def normalized_vector(vector: Vector2d) -> Vector2d:
    """
    Returns a vector of same direction but of length 1
    :param vector:
    :return:
    """
    vector_length = magnitude(vector)
    coord_x = vector[0] / vector_length
    coord_y = vector[1] / vector_length

    return coord_x, coord_y


def barycenter(point_1: Coords2d, point_2: Coords2d, coeff: float) -> Coords2d:
    """
    Calculates the barycenter of two points
    :param point_1: coordinates tuple
    :param point_2: coordinates tuple
    :param coeff: float, barycenter coefficient
    :return: coordinates tuple
    """
    x_coord = point_1[0] + (point_2[0] - point_1[0]) * coeff
    y_coord = point_1[1] + (point_2[1] - point_1[1]) * coeff
    return x_coord, y_coord


def previous(item: Any, list_items: Sequence) -> Any:
    """
    Returns the previous item in a list
    :param item:
    :param list_items:
    :return: item
    """
    i_x = list_items.index(item)
    i_x = len(list_items) if i_x == 0 else i_x
    return list_items[i_x - 1]


def random_unit(dec: int = 100) -> float:
    """
    Returns a random float between -1 and +1
    :param dec: precision
    :return:
    """
    return float((randint(0, 2 * dec + 1) - dec)/dec)


def add_random_noise(coords: Coords2d, maximum: float = 1.0) -> Coords2d:
    """
    Adds random error to coordinates to test snapping
    :param coords:
    :param maximum: max absolute value of noise
    :return:
    """
    x_coord = coords[0] + random_unit() * maximum
    y_coord = coords[1] + random_unit() * maximum
    return x_coord, y_coord