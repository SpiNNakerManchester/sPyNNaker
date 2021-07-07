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
from .math_utils import (n_bits, generate_mask)


class XYEncoder:
    """ Encode coordinates in fields of an integer
    """
    def __init__(self, shape, row_is_most_significant=True):
        self.shape = shape
        self.width = shape[1]
        self.height = shape[0]
        self._n_bits = n_bits(np.asarray(shape))
        self._shift = self._n_bits
        self._mask = generate_mask(self._shift)
        self.row_is_most_significant = row_is_most_significant

    @property
    def row_msb(self):
        return self.row_is_most_significant

    @property
    def shift(self):
        return (self._shift[1] if self.row_msb else self._shift[0])

    @property
    def mask(self):
        return (self._mask[1] if self.row_msb else self._mask[0])

    def decode_with_field(self, ids):
        return (np.right_shift(ids, self.shift),
                np.bitwise_and(ids, self.mask))

    def encode_with_field(self, msf, lsf):
        return np.bitwise_or(np.left_shift(msf, self.shift),
                             np.bitwise_and(lsf, self.mask))

    def convert_ids(self, ids):
        """convert from row major to XY"""
        rows, cols = ids // self.width, ids % self.width
        return self.encode_coords(rows, cols)

    def decode_ids(self, ids):
        """from XY ids to row, column pairs"""
        msb, lsb = self.decode_with_field(ids)
        rows, cols = (msb, lsb) if self.row_msb else (lsb, msb)

        return rows, cols

    def encode_coords(self, rows, cols):
        """from row, column pairs to XY ids"""
        msb, lsb = (rows, cols) if self.row_msb else (cols, rows)
        ids = self.encode_with_field(msb, lsb)

        return ids

    def get_valid_encoded_ids(self):
        """from the original image, get all the row, columns pairs as
           XY-encoded ids
        """
        n_in_rows = self.shape[0]
        n_in_cols = self.shape[1]
        rows = np.repeat(np.arange(n_in_rows), n_in_cols)
        cols = np.tile(np.arange(n_in_cols), n_in_rows)
        ids = self.encode_coords(rows, cols)

        return ids

    def max_coord_size(self):
        r = self.height - 1
        c = self.width - 1
        return self.encode_coords(r, c) + 1
