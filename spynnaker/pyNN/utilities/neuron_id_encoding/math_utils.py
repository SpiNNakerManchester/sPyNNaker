# Copyright (c) The University of Sussex, Garibaldi Pineda Garcia,
# James Turner, James Knight and Thomas Nowotny
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import numpy as np

ROWS_AS_MSB = bool(1)


def n_bits(max_val):
    return np.uint32(np.ceil(np.log2(max_val)))


def generate_mask(shift):
    return (1 << shift) - 1


def power_of_2_size(width=None, height=None, most_significant_rows=True, shape=None):
    if width is not None and height is not None:
        return power_of_2_size_wh(width, height, most_significant_rows)
    elif shape is not None:
        return power_of_2_size_s(shape, most_significant_rows)

    raise Exception("Either provide (width and height) or shape")


def power_of_2_size_wh(width, height, most_significant_rows):
    msb_size = width if most_significant_rows else height
    lsb_size = height if most_significant_rows else width
    msb_bits = n_bits(msb_size)
    lsb_bits = n_bits(lsb_size)

    return int(2**(msb_bits + lsb_bits))


def power_of_2_size_s(shape, most_significant_rows):
    height, width = shape
    return power_of_2_size_wh(width, height, most_significant_rows)


def max_coord_size(width=None, height=None, most_significant_rows=True, shape=None):
    if width is not None and height is not None:
        return max_coord_size_wh(width, height, most_significant_rows)
    elif shape is not None:
        return max_coord_size_s(shape, most_significant_rows)

    raise Exception("Either provide (width and height) or shape")


def max_coord_size_wh(width, height, most_significant_rows):
    r = height - 1
    c = width - 1
    return encode_coords(r, c, width, height, most_significant_rows) + 1


def max_coord_size_s(shape, most_significant_rows):
    height, width = shape
    return max_coord_size_wh(width, height, most_significant_rows)


def get_power_of_2_shape(shape):
    bits = n_bits(shape)
    return np.uint32(np.power(2, bits))


def get_augmented_shape(shape, most_significant_rows):
    bits = n_bits(shape)
    ash = np.uint32(np.power(2, bits))
    sh = (shape[0], ash[1]) if most_significant_rows else (ash[0], shape[1])
    return sh
