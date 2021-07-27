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
from spynnaker.pyNN.models.abstract_models import HasShapeKeyFields


class PoolDenseConnector(AbstractConnector):
    """
    Where the pre- and post-synaptic populations are considered as a 2D\
    array. Connect every post(row, col) neuron to many pre(row, col, kernel)\
    through a (kernel) set of weights and/or delays.

    .. admonition:: TODO

        Should these include `allow_self_connections` and `with_replacement`?

        TODO: ONLY AVERAGE POOLING IS ALLOWED AT THIS POINT!
    """

    __slots__ = [
        "__weights",
        "__pool_shape",
        "__pool_stride",
        "__positive_receptor_type",
        "__negative_receptor_type"
    ]

    def __init__(self, weights, pool_shape=None, pool_stride=None,
                 positive_receptor_type="excitatory",
                 negative_receptor_type="inhibitory", safe=True,
                 verbose=False, callback=None):
        """
        :param weights:
            The synaptic strengths
            Can be:
                * single value: the same value will be used for all weights
                * list: the total number of elements must be
                        (num after pooling * num post)
                * numpy.ndarray: As above for list
                * RandomDistribution: weights will be drawn at random
        :type kernel_weights:
            int or float or list or numpy.ndarray or RandomDistribution
        :param pool_shape:
            Area of pooling, only average pooling is supported (and seems to
            make sense). If a single value is provided, the pooling area will
            be square.  If two values are provided it will be assumed to be
            (pooling_rows, pooling_columns).
        :type pool_shape: int or tuple(int, int) or None
        :param pool_stride:
            Jumps between pooling regions. If a single value is provided, the
            same stride will be used for rows and columns.  If two values are
            provided it will be assumed to be (stride_rows, stride_columns)
        :type pool_stride: int or tuple(int, int) or None
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
        super(PoolDenseConnector, self).__init__(
            safe=safe, callback=callback, verbose=verbose)

        self.__weights = weights

        self.__pool_shape = self.__to_2d_shape(pool_shape, "pool_shape")
        self.__pool_stride = self.__to_2d_shape(pool_stride, "pool_stride")
        if self.__pool_stride is None:
            self.__pool_stride = self.__pool_shape

        self.__positive_receptor_type = positive_receptor_type
        self.__negative_receptor_type = negative_receptor_type

    @property
    def positive_receptor_type(self):
        return self.__positive_receptor_type

    @property
    def negative_receptor_type(self):
        return self.__negative_receptor_type

    @property
    def weights(self):
        return self.__weights

    def __decode_weights(
            self, pre_shape, post_shape, pre_vertex_slice, post_vertex_slice):
        if isinstance(self.__weights, (int, float)):
            n_weights = self.__get_n_weights(
                pre_vertex_slice.shape, post_vertex_slice.shape)
            return numpy.full(n_weights, self.__weights, dtype="float64")
        elif isinstance(self.__weights, Iterable):
            pre_in_post_shape = tuple(self.__get_pre_in_post_shape(pre_shape))
            all_weights = numpy.array(self.__weights, dtype="float64").reshape(
                pre_in_post_shape + post_shape)
            pre_in_post_start = self.__pre_as_post(pre_vertex_slice.start)
            pre_in_post_end = self.__pre_as_post(pre_vertex_slice.end)
            pip_slices = tuple(
                slice(pip_start, pip_end + 1) for pip_start, pip_end in zip(
                    pre_in_post_start, pre_in_post_end))
            post_slices = post_vertex_slice.slices
            return all_weights[pip_slices + post_slices].flatten()
        elif isinstance(self.__weights, RandomDistribution):
            n_weights = self.__get_n_weights(
                pre_vertex_slice.shape, post_vertex_slice.shape)
            return numpy.array(self.__weights.next(n_weights), dtype="float64")
        else:
            raise SynapticConfigurationException(
                f"Unknown weights ({self.__weights})")

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

    @staticmethod
    def get_post_pool_shape(
            pre_shape, pool_shape=None, pool_stride=None):
        pool_shape = PoolDenseConnector.__to_2d_shape(pool_shape, "pool_shape")
        pool_stride = PoolDenseConnector.__to_2d_shape(
            pool_stride, "pool_stride")
        if pool_stride is None:
            pool_stride = pool_shape
        shape = numpy.array(pre_shape)
        if pool_shape is not None:
            post_pool_shape = shape - (pool_shape - 1)
            shape = (post_pool_shape // pool_stride) + 1
        return shape

    def __get_pre_in_post_shape(self, pre_shape):
        return self.get_post_pool_shape(
            pre_shape, self.__pool_shape, self.__pool_stride)

    def __get_n_weights(self, pre_shape, post_shape):
        """ Get the expected number of weights
        """
        shape = self.__get_pre_in_post_shape(pre_shape)
        return numpy.prod(shape) * numpy.prod(post_shape)

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(self, application_edge, synapse_info):
        pre = application_edge.pre_vertex
        post = application_edge.post_vertex
        if len(pre.atoms_shape) != 2:
            raise ConfigurationException(
                "The PoolDenseConnector only works where the pre-Population"
                " of a Projection is 2D.  Please ensure that the"
                " Population uses a Grid2D structure.")

        if isinstance(self.__weights, Iterable):
            expected_n_weights = self.__get_n_weights(
                pre.atoms_shape, post.atoms_shape)
            if expected_n_weights != numpy.array(self.__weights).size:
                raise ConfigurationException(
                    f"With a source population with shape {pre.atoms_shape},"
                    f" and a target population with shape {post.atoms_shape},"
                    f" this connector requires {expected_n_weights} weights")
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
        # Every pre connects to every post
        return post_vertex_slice.n_atoms

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        # Every post connects to every pre
        return synapse_info.n_pre_neurons

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        n_conns = synapse_info.n_pre_neurons * synapse_info.n_post_neurons
        return super(PoolDenseConnector, self)._get_weight_maximum(
            self.__weights, n_conns, synapse_info)

    def __pre_as_post(self, pre_coords):
        """ Write pre coords as post coords.

        :param Iterable pre_coords: An iterable of (x, y) coordinates
        :rtype: numpy.ndarray
        """
        coords = numpy.array(pre_coords)
        if self.__pool_stride is not None:
            coords //= self.__pool_stride
        return coords

    @property
    def local_only_n_bytes(self):
        n_weights = self.__weights.size
        if n_weights % 2 != 0:
            n_weights += 1

        return (
            (6 * BYTES_PER_WORD) +
            (12 * BYTES_PER_SHORT) +
            (n_weights * BYTES_PER_SHORT))

    def write_local_only_data(
            self, spec, app_edge, pre_vertex_slice, post_vertex_slice,
            key, mask, weight_scales):
        # Get info about things
        ps_x, ps_y = 1, 1
        if self.__pool_stride is not None:
            ps_x, ps_y = self.__pool_stride
        pre_in_post_start = self.__pre_as_post(pre_vertex_slice.start)
        pre_in_post_end = self.__pre_as_post(pre_vertex_slice.end)
        pre_in_post_shape = (pre_in_post_end - pre_in_post_start) + 1

        # Write source key info
        spec.write_value(key, data_type=DataType.UINT32)
        spec.write_value(mask, data_type=DataType.UINT32)

        # Write the column and row mask and shifts to extract the column and
        # row from the incoming spike
        if isinstance(app_edge.pre_vertex, HasShapeKeyFields):
            (c_start, c_mask, c_shift), (r_start, r_mask, r_shift) = \
                app_edge.pre_vertex.get_shape_key_fields(pre_vertex_slice)
            start = (c_start, r_start)
            spec.write_value(c_mask, data_type=DataType.UINT32)
            spec.write_value(c_shift, data_type=DataType.UINT32)
            spec.write_value(r_mask, data_type=DataType.UINT32)
            spec.write_value(r_shift, data_type=DataType.UINT32)
        else:
            start = pre_vertex_slice.start
            n_bits_col = get_n_bits(pre_vertex_slice.shape[0])
            col_mask = (1 << n_bits_col) - 1
            n_bits_row = get_n_bits(pre_vertex_slice.shape[1])
            row_mask = ((1 << n_bits_row) - 1) << n_bits_col
            spec.write_value(col_mask, data_type=DataType.UINT32)
            spec.write_value(0, data_type=DataType.UINT32)
            spec.write_value(row_mask, data_type=DataType.UINT32)
            spec.write_value(n_bits_col, data_type=DataType.UINT32)

        # Write remaining connector details
        spec.write_value(start[1], data_type=DataType.INT16)
        spec.write_value(start[0], data_type=DataType.INT16)
        spec.write_value(pre_in_post_start[1], data_type=DataType.INT16)
        spec.write_value(pre_in_post_start[0], data_type=DataType.INT16)
        spec.write_value(pre_in_post_end[1], data_type=DataType.INT16)
        spec.write_value(pre_in_post_end[0], data_type=DataType.INT16)
        spec.write_value(pre_in_post_shape[1], data_type=DataType.INT16)
        spec.write_value(pre_in_post_shape[0], data_type=DataType.INT16)
        spec.write_value(self.__recip(ps_y), data_type=DataType.INT16)
        spec.write_value(self.__recip(ps_x), data_type=DataType.INT16)

        # Write synapse information
        pos_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__positive_receptor_type)
        neg_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__negative_receptor_type)
        spec.write_value(pos_synapse_type, data_type=DataType.UINT16)
        spec.write_value(neg_synapse_type, data_type=DataType.UINT16)

        # Work out which weights are for this connection
        weights = self.__decode_weights(
            app_edge.pre_vertex.atoms_shape, app_edge.post_vertex.atoms_shape,
            pre_vertex_slice, post_vertex_slice)

        # Encode weights with weight scaling
        if len(weights) % 2 != 0:
            weights = numpy.concatenate((weights, [0]))
        neg_weights = weights < 0
        pos_weights = weights > 0
        weights[neg_weights] *= weight_scales[neg_synapse_type]
        weights[pos_weights] *= weight_scales[pos_synapse_type]
        final_weights = numpy.round(weights).astype(numpy.int16)
        spec.write_array(final_weights.view(numpy.uint32))

    def __recip(self, v):
        """ Compute the reciprocal of a number as an signed 1-bit integer,
            14-bit fractional fixed point number, encoded in an integer
        """
        return int(round((1 / v) * (1 << 14)))
