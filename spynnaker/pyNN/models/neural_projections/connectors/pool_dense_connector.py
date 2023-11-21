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
from collections.abc import Iterable
import numpy
from numpy import integer, floating, float64, uint16, uint32
from numpy.typing import ArrayLike, NDArray
from pyNN.random import RandomDistribution
from typing import (
    Optional, Sequence, Tuple, Union, cast, overload, TYPE_CHECKING)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import Slice
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from spinn_front_end_common.interface.ds import DataSpecificationGenerator
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from .abstract_connector import AbstractConnector
from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.abstract_models import HasShapeKeyFields
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)


_DIMENSION_SIZE = (2 * BYTES_PER_WORD) + (6 * BYTES_PER_SHORT)
_KEY_INFO_SIZE = 3 * BYTES_PER_WORD
_CONN_SIZE = _KEY_INFO_SIZE + (3 * BYTES_PER_WORD) + (2 * BYTES_PER_SHORT)
_DIM_DTYPE = [("mask", uint32), ("shift", uint32), ("pre_start", uint16),
              ("pre_in_post_start", uint16), ("pre_in_post_end", uint16),
              ("pre_in_post_shape", uint16), ("recip_pool_stride", uint16),
              ("_PADDING", uint16)]


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
            pre_vertex_slice: Slice, post_vertex_slice: Slice
            ) -> NDArray[float64]:
        if isinstance(self.__weights, (int, float)):
            n_weights = self.__get_n_sub_weights(
                pre_vertex_slice, post_vertex_slice.n_atoms)
            return numpy.full(n_weights, self.__weights, dtype=float64)
        elif isinstance(self.__weights, Iterable):
            pre_in_post_shape = tuple(self.__get_pre_in_post_shape(pre_shape))
            all_weights = numpy.array(self.__weights, dtype=float64).reshape(
                pre_in_post_shape + post_shape)
            pre_in_post_start = self.__pre_as_post(pre_vertex_slice.start)
            pre_in_post_end = self.__pre_as_post(pre_vertex_slice.end)
            pip_slices = tuple(
                slice(pip_start, pip_end + 1) for pip_start, pip_end in zip(
                    pre_in_post_start, pre_in_post_end))
            # TODO check this is correct
            post_slices = post_vertex_slice.dimension
            return all_weights[pip_slices + post_slices].flatten()
        elif isinstance(self.__weights, RandomDistribution):
            n_weights = self.__get_n_sub_weights(
                pre_vertex_slice, post_vertex_slice.n_atoms)
            return numpy.array(self.__weights.next(n_weights), dtype=float64)
        else:
            raise SynapticConfigurationException(
                f"Unknown weights ({self.__weights})")

    @overload
    @staticmethod
    def __to_nd_shape(shape: None, n_dims: int, param_name: str) -> None:
        ...

    @overload
    @staticmethod
    def __to_nd_shape(shape: Union[int, Tuple[int, ...]], n_dims: int,
                      param_name: str) -> NDArray[integer]:
        ...

    @staticmethod
    def __to_nd_shape(shape, n_dims: int, param_name: str) -> Optional[
            NDArray[integer]]:
        if shape is None:
            return None
        if numpy.isscalar(shape):
            return numpy.array([shape] * n_dims, dtype=int)
        elif len(shape) == n_dims:
            return numpy.array(shape, dtype=int)
        raise SynapticConfigurationException(
            f"{param_name} must be an int or a tuple(int) with {n_dims}"
            " dimensions")

    @classmethod
    def get_post_pool_shape(
            cls, pre_shape: Tuple[int, ...],
            pool_shape: Union[int, Tuple[int, ...], None] = None,
            pool_stride: Union[int, Tuple[int, ...], None] = None) -> NDArray:
        real_pool_shape = cls.__to_nd_shape(
            pool_shape, len(pre_shape), "pool_shape")
        real_pool_stride = cls.__to_nd_shape(
            pool_stride, len(pre_shape), "pool_stride")
        if real_pool_stride is None:
            real_pool_stride = real_pool_shape
        shape = numpy.array(pre_shape)
        if real_pool_shape is not None:
            post_pool_shape = shape - (real_pool_shape - 1)
            shape = (post_pool_shape // real_pool_stride) + 1
        return shape

    def __get_pre_in_post_shape(self, pre_shape: Tuple[int, ...]) -> NDArray:
        return self.get_post_pool_shape(
            pre_shape, self.__pool_shape, self.__pool_stride)

    def __get_n_weights(
            self, pre_shape: Tuple[int, ...],
            post_shape: Tuple[int, ...]) -> NDArray:
        """
        Get the expected number of weights.
        """
        shape = self.__get_pre_in_post_shape(pre_shape)
        return numpy.prod(shape) * numpy.prod(post_shape)

    def __get_n_sub_weights(
            self, pre_vertex_slice: Slice, n_post_atoms: int) -> int:
        pre_in_post_start = self.__pre_as_post(pre_vertex_slice.start)
        pre_in_post_end = self.__pre_as_post(pre_vertex_slice.end)
        return (numpy.prod((pre_in_post_end - pre_in_post_start) + 1) *
                n_post_atoms)

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge, synapse_info):
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

    def __pre_as_post(self, pre_coords: ArrayLike) -> NDArray:
        """
        Write pre coordinates as post coordinates.

        :param ~collections.abc.Iterable pre_coords:
            An iterable of (x, y) coordinates
        :rtype: ~numpy.ndarray
        """
        coords = numpy.array(pre_coords)
        if self.__pool_stride is not None:
            coords //= self.__pool_stride
        return coords

    def local_only_n_bytes(
            self, incoming_slices: Sequence[Slice], n_post_atoms: int) -> int:
        """
        :param iterable(~pacman.model.graphs.common.Slice) incoming_slices:
        :param int n_post_atoms:
        :rtype: int
        """
        n_weights = [self.__get_n_sub_weights(s, n_post_atoms)
                     for s in incoming_slices]
        n_weights = [n + 1 if n % 2 != 0 else n for n in n_weights]
        n_dims = [len(s.shape) for s in incoming_slices]

        return int(
            (sum(n_dims) * _DIMENSION_SIZE) +
            (sum(n_weights) * BYTES_PER_SHORT) +
            (len(incoming_slices) * _CONN_SIZE))

    @staticmethod
    def __get_synapse_type(
            app_edge: ProjectionApplicationEdge, target: str) -> int:
        synapse_type = app_edge.post_vertex.get_synapse_id_by_target(target)
        # Checked during validation, assumed constant
        assert synapse_type is not None
        return synapse_type

    def write_local_only_data(
            self, spec: DataSpecificationGenerator,
            app_edge: ProjectionApplicationEdge,
            pre_vertex_slice: Slice, post_vertex_slice: Slice,
            key: int, mask: int, n_colour_bits: int,
            weight_scales: NDArray[floating]):
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
        # Write source key info
        spec.write_value(key, data_type=DataType.UINT32)
        spec.write_value(mask, data_type=DataType.UINT32)
        spec.write_value(n_colour_bits, data_type=DataType.UINT32)

        # Write numbers of things
        n_dims = len(pre_vertex_slice.shape)
        n_weights = self.__get_n_sub_weights(
            pre_vertex_slice, post_vertex_slice.n_atoms)
        spec.write_value(n_dims, data_type=DataType.UINT32)
        spec.write_value(n_weights, data_type=DataType.UINT32)

        # Write synapse information
        pos_synapse_type = self.__get_synapse_type(
            app_edge, self.__positive_receptor_type)
        neg_synapse_type = self.__get_synapse_type(
            app_edge, self.__negative_receptor_type)
        spec.write_value(pos_synapse_type, data_type=DataType.UINT16)
        spec.write_value(neg_synapse_type, data_type=DataType.UINT16)

        # Write delay
        post_delay = app_edge.post_vertex.synapse_dynamics.delay
        assert isinstance(post_delay, float)
        delay_step = (post_delay *
                      SpynnakerDataView.get_simulation_time_step_per_ms())
        local_delay = (delay_step %
                       app_edge.post_vertex.splitter.max_support_delay())
        spec.write_value(local_delay)

        # Generate the dimension information
        dim_info = numpy.zeros(n_dims, dtype=_DIM_DTYPE)
        if self.__pool_stride is not None:
            stride = self.__to_nd_shape(self.__pool_stride, n_dims, "")
            dim_info["recip_pool_stride"] = [
                self.__recip(p)
                for p in stride]  # pylint: disable=not-an-iterable
        else:
            dim_info["recip_pool_stride"] = self.__recip(1)
        if isinstance(app_edge.pre_vertex, HasShapeKeyFields):
            pre_start_size_mask_shift = numpy.array(
                app_edge.pre_vertex.get_shape_key_fields(pre_vertex_slice))
            start = pre_start_size_mask_shift[:, 0]
            size = pre_start_size_mask_shift[:, 1]
            dim_info["pre_start"] = start
            dim_info["mask"] = pre_start_size_mask_shift[:, 2]
            dim_info["shift"] = pre_start_size_mask_shift[:, 3]
        else:
            start = numpy.array(pre_vertex_slice.start)
            size = numpy.array(pre_vertex_slice.shape)
            n_bits = numpy.ceil(numpy.log2(size)).astype("int")
            shifts = numpy.concatenate(([0], numpy.cumsum(n_bits[:-1])))
            masks = numpy.left_shift(numpy.left_shift(1, n_bits) - 1, shifts)
            dim_info["pre_start"] = start
            dim_info["mask"] = masks
            dim_info["shift"] = shifts

        dim_info["pre_in_post_start"] = self.__pre_as_post(start)
        dim_info["pre_in_post_end"] = self.__pre_as_post(start + size)
        dim_info["pre_in_post_shape"] = (
            dim_info["pre_in_post_end"] - dim_info["pre_in_post_start"] + 1)
        spec.write_array(dim_info.view(uint32))

        # Work out which weights are for this connection
        weights = self.__decode_weights(
            app_edge.pre_vertex.atoms_shape, app_edge.post_vertex.atoms_shape,
            pre_vertex_slice, post_vertex_slice)

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
        final_weights = numpy.round(weights).astype(numpy.int16)
        spec.write_array(final_weights.view(uint32))

    @staticmethod
    def __recip(v: float) -> float:
        """
        Compute the reciprocal of a number as an signed 1-bit integer,
        14-bit fractional fixed point number, encoded in an integer.
        """
        return int(round((1 / v) * (1 << 14)))
