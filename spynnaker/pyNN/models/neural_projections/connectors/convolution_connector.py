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
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from pyNN.random import RandomDistribution
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from .abstract_connector import AbstractConnector
from data_specification.enums.data_type import DataType
from collections.abc import Iterable
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.utilities.utility_calls import get_n_bits

N_KERNEL_PARAMS = 8


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

    __slots__ = [
        "__kernel_weights",
        "__strides",
        "__padding_shape",
        "__pool_shape",
        "__pool_stride",
        "__positive_receptor_type",
        "__negative_receptor_type"
    ]

    def __init__(self, kernel_weights, kernel_shape=None, strides=None,
                 padding=None, pool_shape=None, pool_stride=None,
                 positive_receptor_type="excitatory",
                 negative_receptor_type="inhibitory", safe=True,
                 verbose=False, callback=None):
        """
        :param kernel_weights:
            The synaptic strengths, shared by neurons in the post population.
            Can be:
                * single value: kernel_shape must be provided;
                                the same value will be used for all weights
                * simple list: kernel_shape must be provided; the list must
                               be sized shape width * height
                * 2D list: If kernel_shape is provided, it must match
                * numpy.ndarray: As above for simple or 2D list
                * RandomDistribution: kernel_shape must be provided; weights
                                      will be drawn from the distribution
        :type kernel_weights:
            int or list or 2D-list or numpy.ndarray or RandomDistribution
        :param kernel_shape:
            The shape of the kernel if it cannot be determined from
            kernel_weights. If a single value is provided, a square kernel will
            be assumed.  If two values are provided, it will be assumed to be
            (n_rows, n_columns)
        :type kernel_shape: int or tuple(int,int)
        :param strides:
            Spatial sampling frequency, jumps between the post neurons.
            This matches the meaning of standard ML packages.  If a single
            value is provided, the same stride will be used for rows and
            columns.  If two values are provided it will be assumed to be
            (stride_rows, stride_columns)
        :type strides: int or tuple(int, int)
        :param padding:
            How many 'extra pixels' around the pre population will be added,
            only zero-valued pixels are currently supported.  If a single
            value is provided, the same padding will be used for rows and
            columns.  If two values are provided it will be assumed to be
            (padding_rows, padding_columns).  If True, automatic padding will
            be used based on the kernel shape.  If False or None, no padding
            will be used.
        :type padding: bool or int or tuple(int, int) or None
        :param pool_shape:
            Area of pooling, only average pooling is supported (and seems to
            make sense). If a single value is provided, the pooling area will
            be square.  If two values are provided it will be assumed to be
            (pooling_rows, pooling_columns).
        :type pool_shape: int or tuple(int, int)
        :param pool_stride:
            Jumps between pooling regions. If a single value is provided, the
            same stride will be used for rows and columns.  If two values are
            provided it will be assumed to be (stride_rows, stride_columns)
        :type pool_stride: int or tuple(int, int)
        :param str positive_receptor_type:
            The receptor type to add the positive weights to.  By default this
            is "excitatory".
        :param str negative_receptor_type:
            The receptor type to add the negative weights to.  By default this
            is "inhibitory".
        :param bool safe: (ignored)
        :param bool verbose: (ignored)
        :param callable callback: (ignored)
        """
        super(ConvolutionConnector, self).__init__(
            safe=safe, callback=callback, verbose=verbose)

        self.__decode_kernel(kernel_weights, kernel_shape)
        self.__decode_padding(padding)

        if strides is None:
            strides = (1, 1)
        self.__strides = self.__to_2d_shape(strides, "strides")
        self.__pool_shape = self.__to_2d_shape(pool_shape, "pool_shape")
        self.__pool_stride = self.__to_2d_shape(pool_stride, "pool_stride")

        self.__positive_receptor_type = positive_receptor_type
        self.__negative_receptor_type = negative_receptor_type

    @property
    def positive_receptor_type(self):
        return self.__positive_receptor_type

    @property
    def negative_receptor_type(self):
        return self.__negative_receptor_type

    @property
    def kernel_weights(self):
        return self.__kernel_weights

    def __get_kernel_shape(self, shape):
        if shape is None:
            raise SynapticConfigurationException(
                "kernel_shape must be provided")
        if numpy.isscalar(shape):
            return (shape, shape)
        if isinstance(shape, tuple) and len(shape) == 2:
            return shape
        raise SynapticConfigurationException(f"Unknown kernel_shape: {shape}")

    def __decode_kernel(self, w, shape):
        if isinstance(w, int) or isinstance(w, float):
            shape = self.__get_kernel_shape(shape)
            self.__kernel_weights = numpy.full(shape, w, dtype="float64")
        elif isinstance(w, Iterable):
            if all(isinstance(lst, Iterable) for lst in w):
                # 2D list
                if not all(len(lst) == len(w[0]) for lst in w):
                    raise SynapticConfigurationException(
                        "kernel_weights must be a 2D array with every row the"
                        " same length")
                self.__kernel_weights = numpy.array(w, dtype="float64")
            else:
                # 1D list
                shape = self.__get_kernel_shape(shape)
                self.__kernel_weights = numpy.array(
                    w, dtype="float64").reshape(shape)
        elif isinstance(w, RandomDistribution):
            shape = self.__get_kernel_shape(shape)
            self.__kernel_weights = numpy.array(
                w.next(numpy.prod(shape)), dtype="float64").reshape(shape)
        else:
            raise SynapticConfigurationException(
                f"Unknown combination of kernel_weights ({w}) and"
                f" kernel_shape ({shape})")

    @staticmethod
    def __to_2d_shape(shape, param_name):
        if shape is None:
            return None
        if numpy.isscalar(shape):
            return numpy.array([shape, shape], dtype='int')
        elif len(shape) == 1:
            return numpy.array([shape[0], 1], dtype='int')
        elif len(shape) == 2:
            return numpy.array(shape, dtype='int')
        raise SynapticConfigurationException(
            f"{param_name} must be an int or a tuple(int, int)")

    def __decode_padding(self, padding):
        if isinstance(padding, (int, Iterable)):
            self.__padding_shape = self.__to_2d_shape(padding, "padding")
        elif padding is None or padding is False:
            self.__padding_shape = numpy.zeros(2, dtype="int")
        elif padding:
            self.__padding_shape = self.__kernel_weights.shape // 2
        else:
            raise SynapticConfigurationException(
                f"Unrecognized padding {padding}")

    def get_post_shape(self, shape):
        """ Get the shape of the post image given the pre-image shape
        """
        shape = numpy.array(shape)
        if self.__pool_shape is not None:
            post_pool_shape = shape - (self.__pool_shape - 1)
            shape = (post_pool_shape // self.__pool_stride) + 1

        kernel_shape = numpy.array(self.__kernel_weights.shape)
        post_shape = (shape - (kernel_shape - 1) +
                      (2 * self.__padding_shape))

        return numpy.clip(
            post_shape // self.__strides, 1, numpy.inf).astype('int')

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(self, application_edge, synapse_info):
        pre = application_edge.pre_vertex
        post = application_edge.post_vertex
        if len(pre.atoms_shape) != 2 or len(post.atoms_shape) != 2:
            raise ConfigurationException(
                "The ConvolutionConnector only works where the Populations"
                " of a Projection are both 2D.  Please ensure that the"
                " Populations uses a Grid2D structure.")
        expected_post_shape = tuple(self.get_post_shape(pre.atoms_shape))
        if expected_post_shape != post.atoms_shape:
            raise ConfigurationException(
                f"With a source population with shape {pre.atoms_shape}, "
                "for a Convolution connector with the given parameters, "
                "the post-population must have a shape "
                f"{expected_post_shape}")
        if post.get_synapse_id_by_target(
                self.__positive_receptor_type) is None:
            raise ConfigurationException(
                "The post population doesn't have a synaptic receptor type of"
                f" {self.__positive_receptor_type}")
        if post.get_synapse_id_by_target(
                self.__negative_receptor_type) is None:
            raise ConfigurationException(
                "The post population doesn't have a synaptic receptor type of"
                f" {self.__negative_receptor_type}")

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        # All delays are 1 timestep
        return 1

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        # All delays are 1 timestep
        return 1

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        w, h = self.__kernel_weights.shape
        return numpy.clip(w * h, 0, post_vertex_slice.n_atoms)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        w, h = self.__kernel_weights.shape
        return numpy.clip(w * h, 0, synapse_info.n_pre_neurons)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        return numpy.amax(self.__kernel_weights)

    @overrides(AbstractConnector.could_connect)
    def could_connect(
            self, synapse_info, src_machine_vertex, dest_machine_vertex):
        pre_slice = src_machine_vertex.vertex_slice
        post_slice = dest_machine_vertex.vertex_slice
        pre_slice_x = pre_slice.get_slice(0)
        pre_slice_y = pre_slice.get_slice(1)
        post_slice_x = post_slice.get_slice(0)
        post_slice_y = post_slice.get_slice(1)
        hlf_k_w, hlf_k_h = numpy.array(self.__kernel_weights.shape) // 2

        # Get ranges allowed in post
        min_x = post_slice_x.start - hlf_k_w
        max_x = (post_slice_x.stop + hlf_k_w) - 1
        min_y = post_slice_y.start - hlf_k_h
        max_y = (post_slice_y.stop + hlf_k_h) - 1

        # Get pre-coordinates as post-coordinates
        (pre_x_min, pre_y_min), (pre_x_max, pre_y_max) = self.__pre_as_post(
            [[pre_slice_x.start, pre_slice_y.start],
             [pre_slice_x.stop - 1, pre_slice_y.stop - 1]])

        # No part of the pre square overlaps the post-square, don't connect
        if (pre_x_max < min_x or pre_x_min > max_x or
                pre_y_max < min_y or pre_y_min > max_y):
            return False

        # Otherwise, they do
        return True

    def __pre_as_post(self, pre_coords):
        """ Write pre coords as post coords.

        :param Iterable pre_coords: An iterable of (x, y) coordinates
        :rtype: numpy.ndarray
        """
        coords = numpy.array(pre_coords)
        if self.__pool_stride is not None:
            coords //= self.__pool_stride

        kernel_shape = numpy.array(self.__kernel_weights.shape)
        coords = coords - kernel_shape // 2 + self.__padding_shape
        coords //= self.__strides
        return coords

    @property
    def local_only_n_bytes(self):
        n_weights = self.__kernel_weights.size
        if n_weights % 2 != 0:
            n_weights += 1

        return (
            (6 * BYTES_PER_WORD) +
            (14 * BYTES_PER_SHORT) +
            (n_weights * BYTES_PER_SHORT))

    def write_local_only_data(
            self, spec, edge, r_info, synapse_info, weight_scales):
        # Get info about things
        pre_start = edge.pre_vertex.vertex_slice.start
        pre_shape = edge.pre_vertex.vertex_slice.shape
        kernel_shape = self.__kernel_weights.shape
        ps_x, ps_y = 1, 1
        if self.__pool_stride is not None:
            ps_x, ps_y = self.__pool_stride

        # Write source key info
        spec.write_value(r_info.first_key, data_type=DataType.UINT32)
        spec.write_value(r_info.first_mask, data_type=DataType.UINT32)

        # Write the column and row mask and shifts to extract the column and
        # row from the incoming spike
        n_bits_col = get_n_bits(pre_shape[0])
        col_mask = (1 << n_bits_col) - 1
        n_bits_row = get_n_bits(pre_shape[1])
        row_mask = ((1 << n_bits_row) - 1) << n_bits_col
        spec.write_value(col_mask, data_type=DataType.UINT32)
        spec.write_value(0, data_type=DataType.UINT32)
        spec.write_value(row_mask, data_type=DataType.UINT32)
        spec.write_value(n_bits_col, data_type=DataType.UINT32)

        # Write remaining connector details
        spec.write_value(pre_start[1], data_type=DataType.INT16)
        spec.write_value(pre_start[0], data_type=DataType.INT16)
        spec.write_value(pre_shape[1], data_type=DataType.INT16)
        spec.write_value(pre_shape[0], data_type=DataType.INT16)
        spec.write_value(kernel_shape[1], data_type=DataType.INT16)
        spec.write_value(kernel_shape[0], data_type=DataType.INT16)
        spec.write_value(self.__padding_shape[1], data_type=DataType.INT16)
        spec.write_value(self.__padding_shape[0], data_type=DataType.INT16)
        spec.write_value(self.__recip(self.__strides[1]),
                         data_type=DataType.INT16)
        spec.write_value(self.__recip(self.__strides[0]),
                         data_type=DataType.INT16)
        spec.write_value(self.__recip(ps_y), data_type=DataType.INT16)
        spec.write_value(self.__recip(ps_x), data_type=DataType.INT16)

        # Write synapse information
        post_app = edge.post_vertex.app_vertex
        pos_synapse_type = post_app.get_synapse_id_by_target(
            self.__positive_receptor_type)
        neg_synapse_type = post_app.get_synapse_id_by_target(
            self.__negative_receptor_type)
        spec.write_value(pos_synapse_type, data_type=DataType.UINT16)
        spec.write_value(neg_synapse_type, data_type=DataType.UINT16)

        # Encode weights with weight scaling
        encoded_kernel_weights = self.__kernel_weights.flatten()
        if len(encoded_kernel_weights) % 2 != 0:
            encoded_kernel_weights = numpy.concatenate(
                (encoded_kernel_weights, [0]))
        neg_weights = encoded_kernel_weights < 0
        pos_weights = encoded_kernel_weights > 0
        encoded_kernel_weights[neg_weights] *= weight_scales[neg_synapse_type]
        encoded_kernel_weights[pos_weights] *= weight_scales[pos_synapse_type]
        kernel_weights = numpy.round(encoded_kernel_weights).astype(
            numpy.int16)
        spec.write_array(kernel_weights.view(numpy.uint32))

    def __recip(self, v):
        """ Compute the reciprocal of a number as an signed 1-bit integer,
            14-bit fractional fixed point number, encoded in an integer
        """
        return int(round((1 / v) * (1 << 14)))
