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

from __future__ import annotations
from collections.abc import Iterable, Sized
import numpy
from numpy import integer, floating, float64, uint16, uint32
from numpy.typing import ArrayLike, NDArray
from pyNN.random import RandomDistribution
from typing import (
    Optional, Tuple, Union, cast, TYPE_CHECKING)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import Slice
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from .abstract_connector import AbstractConnector
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.common.local_only_2d_common import get_div_const
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)


_DIMENSION_SIZE = BYTES_PER_WORD
_CONN_SIZE = (6 * BYTES_PER_SHORT)


class PoolDenseConnector(AbstractConnector):
    """
    Where the pre- and post-synaptic populations are considered as a 2D
    array. Connect every post(row, column) neuron to many
    pre(row, column, kernel)
    through a (kernel) set of weights and/or delays.
    """

    __slots__ = (
        "__weights",
        "__pool_shape",
        "__pool_stride",
        "__positive_receptor_type",
        "__negative_receptor_type")

    def __init__(self, weights: ArrayLike,
                 pool_shape: Union[int, Tuple[int], None] = None,
                 pool_stride: Union[int, Tuple[int], None] = None,
                 positive_receptor_type: str = "excitatory",
                 negative_receptor_type: str = "inhibitory",
                 safe=True, verbose=False, callback=None):
        """
        :param weights:
            The synaptic strengths. Can be:

            * single value: the same value will be used for all weights
            * :py:class:`list`: the total number of elements must be
              (number after pooling * number post)
            * :py:class:`~numpy.ndarray`: As above for list
            * :py:class:`~spynnaker.pyNN.RandomDistribution`:
              weights will be drawn at random
        :type weights:
            int or float or list(int or float) or ~numpy.ndarray or
            ~spynnaker.pyNN.RandomDistribution
        :param pool_shape:
            Shape of average pooling. If a single value is provided, it will
            be used for every dimension, otherwise must be the same number of
            values as there are dimensions in the source.
        :type pool_shape: int or tuple(int) or None
        :param pool_stride:
            Jumps between pooling regions. If a single value is provided, the
            same stride will be used for all dimensions, otherwise must be
            the same number of values as there are dimensions in the source.
            If `None`, and pool_shape is provided, pool_stride will be set to
            pool_shape.
        :type pool_stride: int or tuple(int) or None
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
        super().__init__(safe=safe, callback=callback, verbose=verbose)
        self.__weights = numpy.array(weights)
        self.__pool_shape = pool_shape
        self.__pool_stride = pool_shape if pool_stride is None else pool_stride
        self.__positive_receptor_type = positive_receptor_type
        self.__negative_receptor_type = negative_receptor_type

    @property
    def positive_receptor_type(self) -> str:
        """
        :rtype: str
        """
        return self.__positive_receptor_type

    @property
    def negative_receptor_type(self) -> str:
        """
        :rtype: str
        """
        return self.__negative_receptor_type

    @property
    def weights(self) -> NDArray:
        """
        :rtype: ~numpy.ndarray
        """
        return self.__weights

    def __decode_weights(
            self, pre_shape: Tuple[int, ...], post_shape: Tuple[int, ...],
            post_vertex_slice: Slice) -> NDArray[float64]:
        if isinstance(self.__weights, (int, float)):
            n_weights = self.__get_n_weights(
                pre_shape, post_vertex_slice.n_atoms)
            return numpy.full(n_weights, self.__weights, dtype=float64)
        elif isinstance(self.__weights, Iterable):
            pre_in_post_shape = tuple(self.__get_pre_in_post_shape(pre_shape))
            all_weights = numpy.array(self.__weights, dtype=float64).reshape(
                pre_in_post_shape + post_shape)
            pip_slices = tuple(
                slice(0, pip_end + 1) for pip_end in pre_in_post_shape)
            # TODO check this is correct
            post_slices = post_vertex_slice.dimension
            return all_weights[pip_slices + post_slices].flatten()
        elif isinstance(self.__weights, RandomDistribution):
            n_weights = self.__get_n_weights(
                pre_shape, post_vertex_slice.n_atoms)
            return numpy.array(self.__weights.next(n_weights), dtype=float64)
        else:
            raise SynapticConfigurationException(
                f"Unknown weights ({self.__weights})")

    @staticmethod
    def __to_nd_shape_or_none(
            shape: Optional[Union[int, Tuple[int, ...]]], n_dims: int,
            param_name: str) -> Optional[NDArray[integer]]:
        if shape is None:
            return None
        return PoolDenseConnector.__to_nd_shape(shape, n_dims, param_name)

    @staticmethod
    def __to_nd_shape(shape: Union[int, Tuple[int, ...]],
                      n_dims: int, param_name: str) -> NDArray[integer]:
        if numpy.isscalar(shape):
            return numpy.array([shape] * n_dims, dtype=int)
        shape_tuple = cast(Sized, shape)
        if len(shape_tuple) == n_dims:
            return numpy.array(shape_tuple, dtype=int)
        raise SynapticConfigurationException(
            f"{param_name} must be an int or a tuple(int) with {n_dims}"
            " dimensions")

    @classmethod
    def get_post_pool_shape(
            cls, pre_shape: Tuple[int, ...],
            pool_shape: Union[int, Tuple[int, ...], None] = None,
            pool_stride: Union[int, Tuple[int, ...], None] = None) -> NDArray:
        """
        The shape considering the stride

        :param pre_shape: tuple(int)
        :type pool_shape: int, tuple(int) or None
        :type pool_stride: int, tuple(int) or None
        :rtype: ndarray
        """
        real_pool_shape = cls.__to_nd_shape_or_none(
            pool_shape, len(pre_shape), "pool_shape")
        real_pool_stride = cls.__to_nd_shape_or_none(
            pool_stride, len(pre_shape), "pool_stride")
        if real_pool_stride is None:
            real_pool_stride = real_pool_shape
        shape = numpy.array(pre_shape)
        if real_pool_shape is not None:
            shape = shape // real_pool_stride
        return shape

    def __get_pre_in_post_shape(self, pre_shape: Tuple[int, ...]) -> NDArray:
        return self.get_post_pool_shape(
            pre_shape, self.__pool_shape, self.__pool_stride)

    def __get_n_weights(
            self, pre_shape: Tuple[int, ...],
            post_n_atoms: int) -> int:
        """
        Get the expected number of weights.
        """
        shape = self.__get_pre_in_post_shape(pre_shape)
        return numpy.prod(shape) * post_n_atoms

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation):
        pre = application_edge.pre_vertex
        post = application_edge.post_vertex
        if len(pre.atoms_shape) != 2:
            raise ConfigurationException(
                "The PoolDenseConnector only works where the pre-Population"
                " of a Projection is 2D.  Please ensure that the"
                " Population uses a Grid2D structure.")

        if isinstance(self.__weights, Iterable):
            expected_n_weights = self.__get_n_weights(
                pre.atoms_shape, post.n_atoms)
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
        if not isinstance(synapse_info.delays, float):
            raise ConfigurationException(
                "The PoolDenseConnector only supports simple uniform delays")

    @staticmethod
    def __delay(synapse_info: SynapseInformation) -> float:
        # Checked by validate_connection above
        return cast(float, synapse_info.delays)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        return self.__delay(synapse_info)

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        return self.__delay(synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        if min_delay is not None and max_delay is not None:
            if not (min_delay <= self.__delay(synapse_info) <= max_delay):
                return 0
        # Every pre connects to every post
        return n_post_atoms

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        # Every post connects to every pre
        return synapse_info.n_pre_neurons

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        if isinstance(self.__weights, Iterable):
            return numpy.amax(numpy.abs(self.__weights))
        n_conns = synapse_info.n_pre_neurons * synapse_info.n_post_neurons
        return super()._get_weight_maximum(
            self.__weights, n_conns, synapse_info)

    def local_only_n_bytes(self, pre_shape: Tuple[int, ...],
                           n_post_atoms: int) -> int:
        """
        :param tuple(int) pre_shape:
        :param int n_post_atoms:
        :rtype: int
        """
        n_weights = self.__get_n_weights(pre_shape, n_post_atoms)
        n_weights = n_weights + 1 if n_weights % 2 != 0 else n_weights
        n_dims = len(pre_shape)

        return int((n_dims * _DIMENSION_SIZE) + (n_weights * BYTES_PER_SHORT) +
                   _CONN_SIZE)

    def get_local_only_data(
            self, app_edge: ProjectionApplicationEdge, local_delay: int,
            delay_stage: int, post_vertex_slice: Slice,
            weight_scales: NDArray[floating]) -> NDArray[uint32]:
        """
        :param ~data_specification.DataSpecificationGenerator spec:
        :param ~pacman.model.graphs.application.ApplicationEdge app_edge:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param int key:
        :param int mask:
        :param int n_colour_bits:
        :param weight_scales:
        """

        # Write numbers of things
        n_dims = len(app_edge.pre_vertex.atoms_shape)
        n_weights = self.__get_n_weights(
            app_edge.pre_vertex.atoms_shape, post_vertex_slice.n_atoms)

        # Write synapse information
        pos_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__positive_receptor_type)
        neg_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__negative_receptor_type)

        short_data = numpy.array([
            n_dims, n_weights, pos_synapse_type, neg_synapse_type,
            delay_stage, local_delay], dtype=numpy.int16).view(uint32)
        all_data = [short_data]

        # Generate the stride information
        if self.__pool_stride is not None:
            stride = self.__to_nd_shape(self.__pool_stride, n_dims, "")
            all_data.append(numpy.array(
                [get_div_const(s) for s in stride], dtype=uint32))
        else:
            all_data.append(numpy.array(
                [get_div_const(1) for _ in range(n_dims)], dtype=uint32))

        # Work out which weights are for this connection
        weights = self.__decode_weights(
            app_edge.pre_vertex.atoms_shape, app_edge.post_vertex.atoms_shape,
            post_vertex_slice)

        # Divide weights by pooling area if needed
        if self.__pool_shape is not None:
            shape = self.__to_nd_shape(self.__pool_shape, n_dims, "")
            area = numpy.prod(shape)
            weights = weights / area

        # Encode weights with weight scaling
        if len(weights) % 2 != 0:
            weights = numpy.concatenate((weights, numpy.zeros(1)))
        neg_weights = weights < 0
        pos_weights = weights > 0
        weights[neg_weights] *= weight_scales[neg_synapse_type]
        weights[pos_weights] *= weight_scales[pos_synapse_type]
        all_data.append(numpy.round(weights).astype(uint16).view(uint32))
        return numpy.concatenate(all_data)
