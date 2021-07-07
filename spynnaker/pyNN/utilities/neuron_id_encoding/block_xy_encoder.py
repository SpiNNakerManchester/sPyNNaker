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
from .math_utils import n_bits, generate_mask


class BlockXYEncoder(object):
    """ Encoding of neuron IDs in pixels using blocks
    """

    def __init__(self, shape, block_shape, row_is_most_significant=True):
        """
        """
        self.block_shape = np.asarray(block_shape)
        self.block_width = block_shape[1]
        self.block_height = block_shape[0]
        self.shape = np.asarray(shape)
        self.width = shape[1]
        self.height = shape[0]
        self.n_blocks = np.ceil(
            np.asarray(shape) / np.asarray(block_shape)).astype('int')
        self.n_per_block = int(np.prod(block_shape))

        # local row/column shifts and masks
        self._shift = n_bits(np.asarray(block_shape))
        self._mask = generate_mask(self._shift)

        # shift/masks to separate local from block ids
        self.shift_local = n_bits(self.n_per_block)
        self.mask_local = generate_mask(self.shift_local)

        # shift/masks for block id/coord
        self._shift_block = n_bits(self.n_blocks)
        self._mask_block = generate_mask(self._shift_block)

        self.row_is_most_significant = row_is_most_significant

    @property
    def row_msb(self):
        return self.row_is_most_significant

    @property
    def shift_block(self):
        return (self._shift_block[1] if self.row_msb else self._shift_block[0])

    @property
    def mask_block(self):
        return (self._mask_block[1] if self.row_msb else self._mask_block[0])

    @property
    def shift(self):
        return (self._shift[1] if self.row_msb else self._shift[0])

    @property
    def mask(self):
        return (self._mask[1] if self.row_msb else self._mask[0])

    def _block_shape(self):
        # if the coordinates are row, col use standard block shape, otherwise
        # the shape needs to be 'inverted'
        return (self.block_shape if self.row_msb
                else np.roll(self.block_shape, 1))

    def decode_with_field(self, ids):
        block_ids = np.right_shift(ids, self.shift_local)
        # rows, cols if self.row_msb else cols, rows
        block_coords = (np.right_shift(block_ids, self.shift_block),
                        np.bitwise_and(block_ids, self.mask_block))

        # rows, cols if self.row_msb else cols, rows
        local_coords = (np.right_shift(ids, self.shift),
                        np.bitwise_and(ids, self.mask))

        return block_coords * self._block_shape() + local_coords

    def _get_block_coords(self, msf, lsf):
        return (msf // self._block_shape()[0],
                lsf // self._block_shape()[1],)

    def _get_local_coords(self, msf, lsf):
        return (msf % self._block_shape()[0],
                lsf % self._block_shape()[1])

    def encode_with_field(self, msf, lsf):
        block_msf, block_lsf = self._get_block_coords(msf, lsf)
        local_msf, local_lsf = self._get_local_coords(msf, lsf)

        encoded_block = np.bitwise_or(
            np.left_shift(block_msf, self.shift_block),
            np.bitwise_and(block_lsf, self.mask_block))

        encoded_local = np.bitwise_or(np.left_shift(local_msf, self.shift),
                                      np.bitwise_and(local_lsf, self.mask))

        return np.bitwise_or(np.left_shift(encoded_block, self.shift_local),
                             np.bitwise_and(encoded_local, self.mask_local))

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
