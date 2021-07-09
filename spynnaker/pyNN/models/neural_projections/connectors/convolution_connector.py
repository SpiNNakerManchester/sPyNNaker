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

import numpy
import numpy as np
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from pyNN.random import RandomDistribution
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_connector import (AbstractConnector)
from spynnaker.pyNN.utilities.neuron_id_encoding import XYEncoder
from data_specification.enums.data_type import DataType

HEIGHT, WIDTH = 0, 1
N_KERNEL_PARAMS = 8

CONV_PARAMS = [
    'pre_w', 'pre_h',
    'stride_w', 'stride_h'
    'post_w', 'post_h'
]

DEC_BITS = 11


class ConvolutionKernel(numpy.ndarray):
    pass


def shape2word(sw, sh):
    return numpy.uint32(
        ((numpy.uint32(sh) & 0xFFFF) << 16) | (numpy.uint32(sw) & 0xFFFF))


class ConvolutionConnector(AbstractConnector):
    """
    Where the pre- and post-synaptic populations are considered as a 2D\
    array. Connect every post(row, col) neuron to many pre(row, col, kernel)\
    through a (kernel) set of weights and/or delays.

    .. admonition:: TODO

        Should these include `allow_self_connections` and `with_replacement`?

        TODO: ONLY AVERAGE POOLING IS ALLOWED AT THIS POINT!
    """

    def __init__(self, shape_pre, weights_kernel, strides, padding,
                 pooling=None, pool_stride=None,
                 most_significant_rows=True,
                 safe=True, verbose=False, callback=None):
        """
        :param shape_pre:
            2D shape of the pre population (rows/height, columns/width, e.g.
            the input image shape)
        :type shape_pre: list(int) or tuple(int,int)
        :param weights_kernel:
            The synaptic strengths, shared by neurons in the post population
        :type weights_kernel: numpy.ndarray(float, size=(int, int))
        :param strides: Spatial sampling frequency, jumps between the post
        neurons. This matches the meaning of standard ML packages
        :type strides: int or tuple(int, int)
        :param padding: How many 'extra pixels' around the pre population will
        be added, only zero-valued pixels are currently supported
        :type padding: str or int or tuple(int, int)
        :param pooling: Area of pooling, only average pooling is supported
        (and seems to make sense)
        :type pooling: int or tuple(int, int)
        :param pool_stride: Jumps between pooling regions
        :type pool_stride: int or tuple(int, int)
        :param most_significant_rows: Whether to use rows as the most
        significant part of neuron id bit fields.
        :type most_significant_rows: bool
        :param bool safe:
        :param bool verbose:
        :param callable callback: (ignored)
        """
        super(ConvolutionConnector, self).__init__(
            safe=safe, callback=callback, verbose=verbose)

        self.single_pre_to_post_pack = False
        self.most_significant_rows = most_significant_rows
        self.pre_shape = self.to_2d_shape(shape_pre)
        self.pre_size = int(np.prod(self.pre_shape))
        self.kernel_shape = self.to_2d_shape(weights_kernel.shape)
        self.kernel = weights_kernel
        self.strides = self.to_2d_shape(strides)
        self.padding = self.to_2d_shape(self.decode_padding(padding))

        self.pooling = not (pooling is None)
        pooling = 0 if pooling is None else pooling
        self.pool_area = self.to_2d_shape(pooling)
        self.pool_shape = self.to_2d_shape(shape_pre)

        if pool_stride is None:
            if pooling:
                pool_stride = self.pool_area
            else:
                pool_stride = 0

        self.pool_strides = self.to_2d_shape(pool_stride)

        self.post_shape = self.get_post_shape()
        self.post_size = int(numpy.prod(self.post_shape))

        # Get the kernel size
        self._kernel_w = self.kernel_shape[WIDTH]
        self._kernel_h = self.kernel_shape[HEIGHT]

        # The half-value used here indicates the half-way array position
        self._hlf_k_w = self._kernel_w // 2
        self._hlf_k_h = self._kernel_h // 2

        # Cache values for the pre and post sizes
        self._pre_w = self.pre_shape[WIDTH]
        self._pre_h = self.pre_shape[HEIGHT]
        self._post_w = self.post_shape[WIDTH]
        self._post_h = self.post_shape[HEIGHT]

        self._post_start_w = self.padding[WIDTH]
        self._post_start_h = self.padding[HEIGHT]

        self._post_step_w = self.strides[WIDTH]
        self._post_step_h = self.strides[HEIGHT]

        # Make sure the supplied values are in the correct format
        self._krn_weights = self.__get_kernel_vals(weights_kernel)
        self._krn_delays = self.__get_kernel_vals(1)

        self._shape_common = shape_pre
        self._common_w = self._shape_common[WIDTH]
        self._common_h = self._shape_common[HEIGHT]
        self._shape_pre = self.pre_shape
        self._shape_post = self.post_shape

        self.requires_spike_mapping = True
        self.needs_dma_weights = False

        # Create storage for later
        self._post_as_pre = {}

        self._input_encoder = XYEncoder(
            self._shape_pre, self.most_significant_rows)
        self._output_encoder = XYEncoder(
            self._shape_post, self.most_significant_rows)

        self.conn_list = []

    @staticmethod
    def to_2d_shape(shape):
        if numpy.isscalar(shape):
            return numpy.asarray([shape, shape], dtype='int')
        elif len(shape) == 1:
            return numpy.asarray([shape[0], 1], dtype='int')
        elif len(shape) == 2:
            return numpy.asarray(shape, dtype='int')

        raise SpynnakerException('The current implementation does not support'
                                 'more dimensions than 2')

    def decode_padding(self, padding):
        if isinstance(padding, str):
            if padding == 'same':
                return self.kernel_shape // 2
            elif padding == 'valid':
                return numpy.asarray([0, 0])
        else:
            return numpy.asarray(padding)

    def shapes_are_compatible(self, pre, post):
        pre_has_structure = True  # PyNN structures are pretty shit

        # pre_has_structure = (not pre.structure is None and
        #                      isinstance(pre.structure, BaseStructure))
        # if not pre_has_structure:
        #     raise SpynnakerException(
        #         "In Convolution Connector: "
        #         "Pre-synaptic population {} has no structure "
        #         "attached to it. Make sure to add one.".format(pre))

        post_has_structure = True  # PyNN structures are pretty shit
        # post_has_structure = (not post.structure is None and
        #                       isinstance(post.structure, BaseStructure))
        # if not post_has_structure:
        #     raise SpynnakerException(
        #         "In Convolution Connector: "
        #         "Post-synaptic population {} has no structure "
        #         "attached to it. Make sure to add one.".format(post))

        # had to change this because of the new XY encoder :(
        pre_size_good = pre.size >= numpy.prod(self.pre_shape)
        post_size_good = post.size >= numpy.prod(self.post_shape)

        return (pre_size_good and post_size_good and
                pre_has_structure and post_has_structure)

    @staticmethod
    def calculate_post_shape(shape, kernel_shape,
                             padding=np.array([0, 0]),
                             stride=np.array([1, 1]),
                             pooling=False,
                             pool_shape=np.array([1, 1]),
                             pool_stride=np.array([1, 1])):
        _r, _c = shape[HEIGHT], shape[WIDTH]
        if pooling:
            s = (np.asarray([_r, _c]) - (pool_shape - 1))
            _r, _c = (s // pool_stride) + 1

        s = (np.asarray([_r, _c]) - (np.asarray(kernel_shape) - 1) +
             2 * padding)

        return np.clip((s // stride), 1, np.inf).astype('int')

    def get_post_shape(self):
        _r, _c = self.pre_shape[HEIGHT], self.pre_shape[WIDTH]
        if self.pooling:
            s = (np.asarray([_r, _c]) - (self.pool_area - 1))
            self.pool_shape = (s // self.pool_strides) + 1
            _r, _c = self.pool_shape

        s = (np.asarray([_r, _c]) - (self.kernel_shape - 1) +
             2 * self.padding)
        return np.clip((s // self.strides), 1, np.inf).astype('int')

    def __decode_with_field(self, ids, shift):
        mask = self.__mask(shift)
        return (np.right_shift(ids, shift),
                np.bitwise_and(ids, mask))

    def __encode_with_field(self, msb, lsb, shift):
        mask = self.__mask(shift)
        return np.bitwise_or(np.left_shift(msb, shift),
                             np.bitwise_and(lsb, mask))

    def __mask(self, shift):
        return (1 << shift) - 1

    def __n_bits(self, max_val):
        return int(np.ceil(np.log2(max_val)))

    @property
    def is_row_msb(self):
        return self.most_significant_rows

    @property
    def is_col_msb(self):
        return not self.most_significant_rows

    @property
    def post_shift(self):
        return self._output_encoder.shift

    def _decode_ids(self, ids, is_pre):
        enc = self._input_encoder if is_pre else self._output_encoder
        return enc.decode_ids(ids)

    def _encode_coords(self, rows, cols, is_pre):
        enc = self._input_encoder if is_pre else self._output_encoder
        return enc.encode_coords(rows, cols)

    def __to_post_coords(self, post_vertex_slice):
        """ Get a list of possible post-slice coordinates.

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :rtype: tuple(~numpy.ndarray, ~numpy.ndarray)
        """
        post = numpy.arange(
            post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)
        return numpy.divmod(post, self._post_w)

    def __map_to_pre_coords(self, post_r, post_c):
        """ Get a map from post to pre coords.

        :param ~numpy.ndarray post_r: rows
        :param ~numpy.ndarray post_c: columns
        :rtype: tuple(~numpy.ndarray, ~numpy.ndarray)
        """
        a = numpy.asarray([post_r, post_c])
        return self.padding + a * self.strides

    def __post_as_pre(self, post_vertex_slice):
        """ Write post coords as pre coords.

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :rtype: tuple(~numpy.ndarray, ~numpy.ndarray)
        """
        # TODO: When slices become hashable, update this code to use them
        # directly as the cache index
        if str(post_vertex_slice) not in self._post_as_pre:
            post_r, post_c = self.__to_post_coords(post_vertex_slice)
            self._post_as_pre[str(post_vertex_slice)] = \
                self.__map_to_pre_coords(post_r, post_c)
        return self._post_as_pre[str(post_vertex_slice)]

    def pre_as_post(self, pre_r, pre_c):
        """ Write pre coords as post coords.

        :param int pre_r: row
        :param int pre_c: column
        :rtype: tuple(int,int)
        """
        _r, _c = pre_r, pre_c
        coords = np.asarray([_r, _c])
        if self.pooling:
            # s = (numpy.asarray([_r, _c]) - (self.pool_area))
            coords //= self.pool_strides[:, np.newaxis]

        coords = (coords - self.kernel_shape[:, np.newaxis] // 2 +
                  self.padding[:, np.newaxis])
        coords //= self.strides[:, np.newaxis]
        return coords

    def __get_kernel_vals(self, vals):
        """ Convert kernel values given into the correct format.

        :param vals:
        :type vals: int or float or ~pyNN.random.NumpyRNG or ~numpy.ndarray\
            or ConvolutionKernel
        :rtype: ~numpy.ndarray
        """
        if vals is None:
            return None
        krn_size = self._kernel_h * self._kernel_w
        krn_shape = (self._kernel_h, self._kernel_w)
        if isinstance(vals, RandomDistribution):
            return numpy.array(vals.next(krn_size)).reshape(krn_shape)
        elif numpy.isscalar(vals):
            return vals * numpy.ones(krn_shape)
        elif ((isinstance(vals, numpy.ndarray) or
                isinstance(vals, ConvolutionKernel)) and
                vals.shape[HEIGHT] == self._kernel_h and
                vals.shape[WIDTH] == self._kernel_w):
            return vals.view(ConvolutionKernel)
        # TODO: make this error more descriptive?
        raise SpynnakerException(
            "Error generating KernelConnector values; if you have supplied "
            "weight and/or delay kernel then ensure they are the same size "
            "as specified by the shape kernel values.")

    def __compute_statistics(
            self, weights, delays, pre_vertex_slice, post_vertex_slice):
        """ Compute the relevant information required for the connections.
        """
        return

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        return 1

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        return 1

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        return 1

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        return 1

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        # I think this is overestimated, but not by much
        n_conns = (
            self._pre_w * self._pre_h * self._kernel_w * self._kernel_h)
        # Use the kernel weights if user has supplied them
        if self._krn_weights is not None:
            return self._get_weight_maximum(self._krn_weights, n_conns,
                                            synapse_info)

        return self._get_weight_maximum(synapse_info.weights, n_conns,
                                        synapse_info)

    def __repr__(self):
        return "ConvolutionConnector(shape_kernel[{},{}])".format(
            self._kernel_w, self._kernel_h)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        block = numpy.zeros(0, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block['weight'] = 0
        block['delay'] = 1

        return block

    def _pre_size_max_coord(self):
        return self._input_encoder.max_coord_size()

    def __get_pre_id_as_post_coord_list(self, pre_slice, post_slice):
        pre_w, pre_h = self.pre_shape[WIDTH], self.pre_shape[HEIGHT]
        post_w, post_h = self.post_shape[WIDTH], self.post_shape[HEIGHT]
        if pre_slice is None:
            pre_ids = np.arange(0, self._pre_size_max_coord())
        else:
            pre_ids = np.arange(pre_slice.lo_atom, pre_slice.hi_atom + 1)
        pre_rows, pre_cols = self._decode_ids(pre_ids, is_pre=True)
        post_rows, post_cols = self.pre_as_post(pre_rows, pre_cols)

        unused_pre = np.int8(-127)
        ids = numpy.where(numpy.logical_or(pre_rows >= pre_h,
                                           pre_cols >= pre_w))
        post_rows[ids] = unused_pre
        post_cols[ids] = unused_pre

        # ids = numpy.where(numpy.logical_or(post_rows >= post_h,
        #                                    post_cols >= post_w))
        # post_rows[ids] = unused_pre
        # post_cols[ids] = unused_pre

        coords = []
        for post_r, post_c in zip(post_rows, post_cols):
            post_rc = numpy.uint16(
                ((numpy.uint16(post_r & 0xFF)) << 8) |
                (numpy.uint16(post_c & 0xFF))
            )
            # print(r * w + c, post_r, post_c, post_rc)
            # print(numpy.binary_repr(r_8, width=8))
            # print(numpy.binary_repr(c_8, width=8))
            # print(numpy.binary_repr(post_r, width=16))
            # print(numpy.binary_repr(post_c, width=16))
            # print(numpy.binary_repr(post_rc, width=16))
            coords.append(post_rc)

        if len(coords) % 2 == 1:
            coords.append(numpy.uint16(0))

        cs = []
        for idx in range(0, len(coords), 2):
            x0, x1 = coords[idx], coords[idx+1]
            o = numpy.uint32((numpy.uint32(x0) << 16) | numpy.uint32(x1))
            # print(o)
            cs.append(o)

        return numpy.hstack(cs)

    @staticmethod
    def pack_kernel(kernel):
        n = len(kernel)
        n = int(numpy.ceil(n / 2.0))
        pack = numpy.zeros(n, dtype='uint32')
        scale = float(1 << DEC_BITS)
        for pidx in range(n):
            kidx = pidx * 2
            v0 = numpy.int32(0)
            v0 = v0 | numpy.int32(numpy.round(kernel[kidx] * scale))

            v1 = numpy.int32(0)
            if kidx + 1 < len(kernel):
                v1 = v1 | numpy.int32(numpy.round(kernel[kidx+1] * scale))

            pack[pidx] = numpy.uint32((v0 << 16) | (v1 & 0xFFFF))

            # if kidx + 1 < len(kernel):
            #     print(kernel[kidx],
            #           kernel[kidx+1])
            #     print(numpy.round(kernel[kidx] * scale),
            #           numpy.round(kernel[kidx+1] * scale))
            #     print(numpy.int16(numpy.round(kernel[kidx] * scale)),
            #           numpy.int16(numpy.round(kernel[kidx + 1] * scale)))
            #     print(numpy.uint32(v0), numpy.uint32(v1))
            #     print(numpy.binary_repr(v0, 32))
            #     print(numpy.binary_repr(v1, 32))
            #     print(numpy.binary_repr(v0 << 16, 32))
            #     print(numpy.binary_repr(v1 & 0xFFFF, 32))
            #     print(numpy.binary_repr(pack[pidx], 32))
            #     print(numpy.uint16(pack[pidx] >> 16),
            #           numpy.uint16(pack[pidx] & 0xFFFF))
            #     print(numpy.int16(pack[pidx] >> 16),
            #           numpy.int16(pack[pidx] & 0xFFFF))
        # print(kernel)
        # print(pack)

        return pack

    def get_local_only_data(self, pre_slice=None, post_slice=None):
        # print(self)
        pre_start = numpy.uint32(0 if pre_slice is None
                                 else pre_slice.lo_atom)
        pre_end = numpy.uint32(self._pre_size_max_coord() if pre_slice is None
                               else pre_slice.hi_atom + 1)

        post_start = numpy.uint32(0 if post_slice is None
                                  else post_slice.lo_atom)
        post_end = numpy.uint32(self.post_size if post_slice is None
                                else post_slice.hi_atom + 1)

        wk = 1. / numpy.prod(self.pool_area) if self.pooling else 1.

        # klist = self.pack_kernel(self.kernel.flatten() * wk)
        klist = DataType.S1615.encode_as_numpy_int_array(
            self.kernel.flatten() * wk)

        shapes = [
            shape2word(self.pre_shape[WIDTH], self.pre_shape[HEIGHT]),
            shape2word(self.post_shape[WIDTH], self.post_shape[HEIGHT]),
            shape2word(self.padding[WIDTH], self.padding[HEIGHT]),
            shape2word(self.strides[WIDTH], self.strides[HEIGHT]),
            shape2word(self.kernel_shape[WIDTH], self.kernel_shape[HEIGHT]),
            shape2word(self.pool_area[WIDTH], self.pool_area[HEIGHT]),
            shape2word(self.pool_strides[WIDTH], self.pool_strides[HEIGHT]),
        ]

        pre2post = self.__get_pre_id_as_post_coord_list(pre_slice, post_slice)
        # print(shapes)
        # # print(self.kernel.flatten())
        # print(klist)
        # first is for length of data
        # second is for number of pre-starts
        data = [shape2word(pre_end, pre_start),
                shape2word(post_end, post_start)]
        data.extend(shapes)
        data.extend(klist)
        data.extend(pre2post)
        return data

    @property
    # @overrides(AbstractConnector.get_local_only_info_size)
    def get_local_only_info_size(self):
        return len(self.get_local_only_data())

    @property
    def _kernel_properties(self):
        """
        :rtype: list(int)
        """
        return []

    def gen_delays_id(self, delays):
        return 0

    def gen_delay_params_size_in_bytes(self, delays):
        return 0

    def gen_delay_params(self, delays, pre_vertex_slice, post_vertex_slice):
        return []

    def gen_weights_id(self, weights):
        return 0

    def gen_weight_params_size_in_bytes(self, weights):
        return 0

    def gen_weights_params(self, weights, pre_vertex_slice, post_vertex_slice):
        return []

    @property
    def gen_connector_id(self):
        return 0

    def gen_connector_params(
            self, pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        return []

    @property
    def gen_connector_params_size_in_bytes(self):
        return 0

    def get_conv_size_in_bytes(self):
        return self._kernel_h * self._kernel_w * BYTES_PER_WORD

    @overrides(AbstractConnector.could_connect)
    def could_connect(self, _synapse_info, _pre_slice, _post_slice):
        # Filter edge if both are views and outside limits
        pre_ids = np.array([_pre_slice.lo_atom, _pre_slice.hi_atom])
        pre_height, pre_width = self.pre_shape
        pre_rows, pre_cols = self._decode_ids(pre_ids, is_pre=True)
        # pre_rows[1] = min(pre_height - 1, pre_rows[1])
        # pre_cols[1] = min(pre_width - 1, pre_cols[1])

        post_ids = np.array([_post_slice.lo_atom, _post_slice.hi_atom])
        post_height, post_width = self.post_shape
        post_rows, post_cols = self._decode_ids(post_ids, is_pre=False)

        kheigth, kwidth = self.kernel_shape
        hkh, hkw = kheigth // 2, kwidth // 2
        min_post_row, max_post_row = (max(0, post_rows[0] - hkh),
                                      min(pre_height - 1, post_rows[1] + hkh))

        min_post_col, max_post_col = (max(0, post_cols[0] - hkw),
                                      min(pre_width - 1, post_cols[1] + hkw))

        # one to the left of the other
        if ((pre_cols[0] > max_post_col) or (min_post_col > pre_cols[1])):
            return False

        # one starts bellow the other
        if ((pre_rows[0] > max_post_row) or (min_post_row > pre_rows[1])):
            return False

        # row0 = max(pre_rows[0], min_post_row)
        # row1 = min(pre_rows[1], max_post_row)
        # col0 = max(pre_cols[0], min_post_col)
        # col1 = min(pre_cols[1], max_post_col)
        #
        # dr = row1 - row0
        # dc = col1 - col0
        # connect = dr > 0 or dc > 0
        #
        return True
