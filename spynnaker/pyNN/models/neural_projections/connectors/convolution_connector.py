# Copyright (c) 2021 The University of Manchester
# Based on work Copyright (c) The University of Sussex,
# Garibaldi Pineda Garcia, James Turner, James Knight and Thomas Nowotny
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from pyNN.random import RandomDistribution
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from .abstract_connector import AbstractConnector
from collections.abc import Iterable
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.models.abstract_models import HasShapeKeyFields
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView

#: The number of 32-bit words in the source_key_info struct
SOURCE_KEY_INFO_WORDS = 7

#: The number of 16-bit shorts in the connector struct,
#: ignoring the source_key_info struct but including the delay and the
#: 32-bit weight index
CONNECTOR_CONFIG_SHORTS = 16


class ConvolutionConnector(AbstractConnector):
    """
    Where the pre- and post-synaptic populations are considered as a 2D
    array. Connect every post(row, column) neuron to many
    pre(row, column, kernel)
    through a (kernel) set of weights and/or delays.
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

            * single value: `kernel_shape` must be provided;
              the same value will be used for all weights
            * simple list: `kernel_shape` must be provided; the list must
              be sized shape width * height
            * 2D list: If `kernel_shape` is provided, it must match
            * :py:class:`~numpy.ndarray`: As above for simple or 2D list
            * :py:class:`~spynnaker.pyNN.RandomDistribution`:
              `kernel_shape` must be provided; weights will be drawn from the
              distribution
        :type kernel_weights:
            int or list or ~numpy.ndarray or ~spynnaker.pyNN.RandomDistribution
        :param kernel_shape:
            The shape of the kernel if it cannot be determined from
            `kernel_weights`. If a single value is provided, a square kernel
            will be assumed.  If two values are provided, it will be assumed to
            be (n_rows, n_columns)
        :type kernel_shape: int or tuple(int,int)
        :param strides:
            Spatial sampling frequency, jumps between the post neurons.
            This matches the meaning of standard ML packages.  If a single
            value is provided, the same stride will be used for rows and
            columns.  If two values are provided it will be assumed to be
            (stride_rows, stride_columns)
        :type strides: int or tuple(int, int)
        :param padding:
            How many 'extra pixels' around the pre-population will be added,
            only zero-valued pixels are currently supported.  If a single
            value is provided, the same padding will be used for rows and
            columns.  If two values are provided it will be assumed to be
            `(padding_rows, padding_columns)`.  If True, automatic padding will
            be used based on the kernel shape.  If False or `None`, no padding
            will be used.
        :type padding: bool or int or tuple(int, int) or None
        :param pool_shape:
            Area of pooling, only average pooling is supported (and seems to
            make sense). If a single value is provided, the pooling area will
            be square.  If two values are provided it will be assumed to be
            `(pooling_rows, pooling_columns)`.
        :type pool_shape: int or tuple(int, int) or None
        :param pool_stride:
            Jumps between pooling regions. If a single value is provided, the
            same stride will be used for rows and columns.  If two values are
            provided it will be assumed to be `(stride_rows, stride_columns)`
        :type pool_stride: int or tuple(int, int) or None
        :param str positive_receptor_type:
            The receptor type to add the positive weights to.  By default this
            is "``excitatory``".
        :param str negative_receptor_type:
            The receptor type to add the negative weights to.  By default this
            is "``inhibitory``".
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
        if self.__pool_stride is None:
            self.__pool_stride = self.__pool_shape
        if self.__pool_shape is not None:
            self.__kernel_weights /= numpy.prod(self.__pool_shape)

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
        """
        Get the shape of the post image given the pre-image shape.
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
                " of a Projection are both 2D.  Please ensure that both the"
                " Populations use a Grid2D structure.")
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
        return synapse_info.delays

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        return synapse_info.delays

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms, synapse_info, min_delay=None,
            max_delay=None):
        if min_delay is not None and max_delay is not None:
            delay = synapse_info.delays
            if min_delay > delay or max_delay < delay:
                return 0
        w, h = self.__kernel_weights.shape
        return numpy.clip(w * h, 0, n_post_atoms)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        w, h = self.__kernel_weights.shape
        return numpy.clip(w * h, 0, synapse_info.n_pre_neurons)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        return numpy.amax(self.__kernel_weights)

    @overrides(AbstractConnector.get_weight_minimum)
    def get_weight_minimum(self, weights, weight_random_sigma, synapse_info):
        # Use the kernel weights if user has supplied them
        if self.__kernel_weights is not None:
            return super(ConvolutionConnector, self).get_weight_minimum(
                self.__kernel_weights, weight_random_sigma, synapse_info)

        return super(ConvolutionConnector, self).get_weight_minimum(
            weights, weight_random_sigma, synapse_info)

    @overrides(AbstractConnector.get_connected_vertices)
    def get_connected_vertices(self, s_info, source_vertex, target_vertex):
        pre_vertices = numpy.array(
            source_vertex.splitter.get_out_going_vertices(SPIKE_PARTITION_ID))
        pre_slices = [m_vertex.vertex_slice for m_vertex in pre_vertices]
        pre_slices_x = [vtx_slice.get_slice(0) for vtx_slice in pre_slices]
        pre_slices_y = [vtx_slice.get_slice(1) for vtx_slice in pre_slices]
        pre_ranges = [[[px.start, py.start], [px.stop - 1, py.stop - 1]]
                      for px, py in zip(pre_slices_x, pre_slices_y)]
        pres_as_posts = self.__pre_as_post(pre_ranges)
        hlf_k_w, hlf_k_h = numpy.array(self.__kernel_weights.shape) // 2

        connected = list()
        for post in target_vertex.splitter.get_in_coming_vertices(
                SPIKE_PARTITION_ID):
            post_slice = post.vertex_slice
            post_slice_x = post_slice.get_slice(0)
            post_slice_y = post_slice.get_slice(1)

            # Get ranges allowed in post
            min_x = post_slice_x.start - hlf_k_w
            max_x = (post_slice_x.stop + hlf_k_w) - 1
            min_y = post_slice_y.start - hlf_k_h
            max_y = (post_slice_y.stop + hlf_k_h) - 1

            # Test that the start coords are in range i.e. less than max
            start_in_range = numpy.logical_not(
                numpy.any(pres_as_posts[:, 0] > [max_x, max_y], axis=1))
            # Test that the end coords are in range i.e. more than min
            end_in_range = numpy.logical_not(
                numpy.any(pres_as_posts[:, 1] < [min_x, min_y], axis=1))
            # When both things are true, we have a vertex in range
            pre_in_range = pre_vertices[
                numpy.logical_and(start_in_range, end_in_range)]
            connected.append((post, pre_in_range))

        return connected

    def get_max_n_incoming_slices(self, source_vertex, target_vertex):
        pre_slices = list(source_vertex.splitter.get_out_going_slices())
        pre_slices_x = [vtx_slice.get_slice(0) for vtx_slice in pre_slices]
        pre_slices_y = [vtx_slice.get_slice(1) for vtx_slice in pre_slices]
        pre_ranges = [[[px.start, py.start], [px.stop - 1, py.stop - 1]]
                      for px, py in zip(pre_slices_x, pre_slices_y)]
        pres_as_posts = self.__pre_as_post(pre_ranges)
        hlf_k_w, hlf_k_h = numpy.array(self.__kernel_weights.shape) // 2

        max_connected = 0
        for post_slice in target_vertex.splitter.get_in_coming_slices():
            post_slice_x = post_slice.get_slice(0)
            post_slice_y = post_slice.get_slice(1)

            # Get ranges allowed in post
            min_x = post_slice_x.start - hlf_k_w
            max_x = (post_slice_x.stop + hlf_k_w) - 1
            min_y = post_slice_y.start - hlf_k_h
            max_y = (post_slice_y.stop + hlf_k_h) - 1

            # Test that the start coords are in range i.e. less than max
            start_in_range = numpy.logical_not(
                numpy.any(pres_as_posts[:, 0] > [max_x, max_y], axis=1))
            # Test that the end coords are in range i.e. more than min
            end_in_range = numpy.logical_not(
                numpy.any(pres_as_posts[:, 1] < [min_x, min_y], axis=1))
            # When both things are true, we have a vertex in range
            pre_in_range = numpy.logical_and(start_in_range, end_in_range)
            n_connected = pre_in_range.sum()
            max_connected = max(max_connected, n_connected)

        return max_connected

    def __pre_as_post(self, pre_coords):
        """
        Write pre-population coordinates as post-population coordinates.

        :param ~collections.abc.Iterable pre_coords:
            An iterable of (x, y) coordinates
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
    def kernel_n_bytes(self):
        n_weights = self.__kernel_weights.size
        return n_weights * BYTES_PER_SHORT

    @property
    def kernel_n_weights(self):
        return self.__kernel_weights.size

    @property
    def parameters_n_bytes(self):
        return (
            (SOURCE_KEY_INFO_WORDS * BYTES_PER_WORD) +
            (CONNECTOR_CONFIG_SHORTS * BYTES_PER_SHORT))

    def get_local_only_data(
            self, app_edge, vertex_slice, key, mask, n_colour_bits,
            delay, weight_index):
        # Get info about things
        kernel_shape = self.__kernel_weights.shape
        ps_x, ps_y = 1, 1
        if self.__pool_stride is not None:
            ps_x, ps_y = self.__pool_stride

        # Start with source key info
        values = [key, mask, n_colour_bits]

        # Add the column and row mask and shifts to extract the column and
        # row from the incoming spike
        if isinstance(app_edge.pre_vertex, HasShapeKeyFields):
            (c_start, _c_end, c_mask, c_shift), \
                (r_start, _r_end, r_mask, r_shift) = \
                app_edge.pre_vertex.get_shape_key_fields(vertex_slice)
            start = (c_start, r_start)
            values.extend([c_mask, c_shift, r_mask, r_shift])
        else:
            start = vertex_slice.start
            n_bits_col = get_n_bits(vertex_slice.shape[0])
            col_mask = (1 << n_bits_col) - 1
            n_bits_row = get_n_bits(vertex_slice.shape[1])
            row_mask = ((1 << n_bits_row) - 1) << n_bits_col
            values.extend([col_mask, 0, row_mask, n_bits_col])

        # Do a new list for remaining connector details as uint16s
        pos_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__positive_receptor_type)
        neg_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__negative_receptor_type)
        short_values = numpy.array([
            start[1], start[0],
            kernel_shape[1], kernel_shape[0],
            self.__padding_shape[1], self.__padding_shape[0],
            self.__recip(self.__strides[1]), self.__recip(self.__strides[0]),
            self.__recip(ps_y), self.__recip(ps_x),
            pos_synapse_type, neg_synapse_type], dtype="uint16")

        # Work out delay
        delay_step = (delay *
                      SpynnakerDataView.get_simulation_time_step_per_ms())
        local_delay = (delay_step %
                       app_edge.post_vertex.splitter.max_support_delay())

        data = [numpy.array(values, dtype="uint32"),
                short_values.view("uint32"),
                numpy.array([local_delay, weight_index], dtype="uint32")]
        return data

    def get_encoded_kernel_weights(self, app_edge, weight_scales):
        # Encode weights with weight scaling
        encoded_kernel_weights = self.__kernel_weights.flatten()
        neg_weights = encoded_kernel_weights < 0
        pos_weights = encoded_kernel_weights > 0
        pos_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__positive_receptor_type)
        neg_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__negative_receptor_type)
        encoded_kernel_weights[neg_weights] *= weight_scales[neg_synapse_type]
        encoded_kernel_weights[pos_weights] *= weight_scales[pos_synapse_type]
        kernel_weights = numpy.round(encoded_kernel_weights).astype(
            numpy.int16)
        return kernel_weights

    def __recip(self, v):
        """
        Compute the reciprocal of a number as an signed 1-bit integer,
        14-bit fractional fixed point number, encoded in an integer.
        """
        return int(round((1 / v) * (1 << 14)))
