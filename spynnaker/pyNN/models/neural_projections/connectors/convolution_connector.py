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
from collections.abc import (Iterable, Sequence)
from typing import (
    List, Optional, Sequence as TSequence, Tuple, Union,
    cast, overload, TYPE_CHECKING)

import numpy
from numpy import floating, float64, integer, int16, uint16, uint32
from numpy.typing import NDArray

from pyNN.random import RandomDistribution

from spinn_utilities.overrides import overrides

from pacman.model.graphs.abstract_vertex import AbstractVertex
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import MachineVertex

from spinn_front_end_common.utilities.constants import (
    BYTES_PER_SHORT, BYTES_PER_WORD)
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.models.common.local_only_2d_common import get_div_const

from .abstract_connector import AbstractConnector

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)

#: The size of the connector struct in bytes
CONNECTOR_CONFIG_SIZE = (10 * BYTES_PER_SHORT) + (4 * BYTES_PER_WORD)


_Weights = Union[
    int, float, List[Union[int, float]], Tuple[Union[int, float], ...],
    NDArray[float64], RandomDistribution]
_Shape = Union[int, Tuple[int, int], None]
_Padding = Union[bool, _Shape]


class ConvolutionConnector(AbstractConnector):
    """
    A 2D connector that centres on a post neuron.

    Special connector which dynamically maps a 2D kernel over a 2D plane,
    so that when the kernel is centred on a post-neuron,
    that post-neuron receives input from each pre-neuron
    that the kernel touches,
    and the weights of those pre-post connections
    are then the values of the kernel.
    """

    __slots__ = (
        "__kernel_weights",
        "__strides",
        "__padding_shape",
        "__pool_shape",
        "__pool_stride",
        "__positive_receptor_type",
        "__negative_receptor_type",
        "__filter_edges"
    )

    def __init__(self, kernel_weights: _Weights,
                 kernel_shape: _Shape = None,
                 strides: _Shape = None, padding: _Padding = None,
                 pool_shape: _Shape = None, pool_stride: _Shape = None,
                 positive_receptor_type: str = "excitatory",
                 negative_receptor_type: str = "inhibitory",
                 safe=True, verbose=False, callback=None, filter_edges=True):
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
        :param bool filter_edges:
            Whether to filter the edges based on connectivity or not; filtered
            means that the receiving cores will receive fewer packets, whereas
            non-filtered means that receiving cores will receive all packets
            whether relevant or not.  However non-filtered may be more
            efficient in the routing tables, so may be needed if routing
            compression doesn't work.
        """
        super().__init__(safe=safe, callback=callback, verbose=verbose)

        self.__kernel_weights = self.__decode_kernel(
            kernel_weights, kernel_shape)
        self.__padding_shape = self.__decode_padding(padding)
        self.__filter_edges = filter_edges

        if strides is None:
            self.__strides = numpy.array((1, 1), dtype=integer)
        else:
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
    def positive_receptor_type(self) -> str:
        """
        The receptor type to add the positive weights to.

        :rtype: str
        """
        return self.__positive_receptor_type

    @property
    def negative_receptor_type(self) -> str:
        """
         The receptor type to add the negative weights to.

        :rtype: str
        """
        return self.__negative_receptor_type

    @property
    def kernel_weights(self) -> NDArray[float64]:
        """
        The weights for this connection.

        :rtype: ndarray
        """
        return self.__kernel_weights

    def __get_kernel_shape(self, shape: _Shape) -> Tuple[int, int]:
        if shape is None:
            raise SynapticConfigurationException(
                "kernel_shape must be provided")
        if numpy.isscalar(shape):
            assert isinstance(shape, int)
            return (shape, shape)
        if isinstance(shape, tuple) and len(shape) == 2:
            return shape
        raise SynapticConfigurationException(f"Unknown kernel_shape: {shape}")

    def __decode_kernel(self, w: _Weights, shape: _Shape) -> NDArray[float64]:
        if isinstance(w, (int, float)):
            _shape = self.__get_kernel_shape(shape)
            return numpy.full(_shape, w, dtype=float64)
        elif isinstance(w, (Sequence, numpy.ndarray)):
            if all(isinstance(lst, (Sequence, numpy.ndarray)) for lst in w):
                ws = cast(TSequence[TSequence[float]], w)
                len0 = len(ws[0])
                # 2D list
                if not all(len(lst) == len0 for lst in ws):
                    raise SynapticConfigurationException(
                        "kernel_weights must be a 2D array with every row the"
                        " same length")
                return numpy.array(w, dtype=float64)
            else:
                # 1D list
                _shape = self.__get_kernel_shape(shape)
                return numpy.array(w, dtype=float64).reshape(_shape)
        elif isinstance(w, RandomDistribution):
            _shape = self.__get_kernel_shape(shape)
            return numpy.array(
                w.next(numpy.prod(_shape)), dtype=float64).reshape(_shape)
        else:
            raise SynapticConfigurationException(
                f"Unknown combination of kernel_weights ({w}) and"
                f" kernel_shape ({shape})")

    @overload
    @staticmethod
    def __to_2d_shape(shape: Union[int, Tuple[int, int]],
                      param_name: str) -> NDArray[integer]:
        ...

    @overload
    @staticmethod
    def __to_2d_shape(shape: None, param_name: str) -> None:
        ...

    @staticmethod
    def __to_2d_shape(shape: _Shape, param_name: str) -> Optional[
            NDArray[integer]]:
        if shape is None:
            return None
        if numpy.isscalar(shape):
            return numpy.array([shape, shape], dtype=integer)
        assert isinstance(shape, tuple)
        if len(shape) == 1:
            return numpy.array([shape[0], 1], dtype=integer)
        elif len(shape) == 2:
            return numpy.array(shape, dtype=integer)
        raise SynapticConfigurationException(
            f"{param_name} must be an int or a tuple(int, int)")

    def __decode_padding(self, padding: _Padding) -> NDArray[integer]:
        if isinstance(padding, (int, Iterable)):
            return self.__to_2d_shape(padding, "padding")
        elif padding is None or padding is False:
            return numpy.zeros(2, dtype=integer)
        elif padding:
            return self.__kernel_weights.shape // 2
        else:
            raise SynapticConfigurationException(
                f"Unrecognized padding {padding}")

    def get_post_shape(self, shape: Tuple[int, ...]):
        """
        Get the shape of the post image given the pre-image shape.
        """
        _shape = numpy.array(shape)
        if self.__pool_shape is not None:
            _shape = _shape // self.__pool_stride

        kernel_shape = numpy.array(self.__kernel_weights.shape)
        post_shape = (_shape - (kernel_shape - 1) +
                      (2 * self.__padding_shape))

        return tuple(int(i) for i in numpy.clip(
            post_shape // self.__strides, 1, numpy.inf).astype(integer))

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation):
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
        if not isinstance(synapse_info.delays, float):
            raise ConfigurationException(
                "The ConvolutionConnector only supports simple uniform delays")

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
        w, h = self.__kernel_weights.shape
        return numpy.clip(w * h, 0, n_post_atoms)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        w, h = self.__kernel_weights.shape
        return numpy.clip(w * h, 0, synapse_info.n_pre_neurons)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        return float(numpy.amax(self.__kernel_weights))

    @overrides(AbstractConnector.get_connected_vertices)
    def get_connected_vertices(
            self, s_info: SynapseInformation,
            source_vertex: ApplicationVertex,
            target_vertex: ApplicationVertex) -> Sequence[
                Tuple[MachineVertex, Sequence[AbstractVertex]]]:
        if not self.__filter_edges:
            return super(ConvolutionConnector, self).get_connected_vertices(
                s_info, source_vertex, target_vertex)
        pre_vertices = numpy.array(
            source_vertex.splitter.get_out_going_vertices(SPIKE_PARTITION_ID))
        post_slice_ranges = self.__pre_as_post_slice_ranges(
            m_vertex.vertex_slice for m_vertex in pre_vertices)
        hlf_k_w, hlf_k_h = numpy.array(self.__kernel_weights.shape) // 2

        connected: List[Tuple[MachineVertex, List[MachineVertex]]] = []
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

            # Test that the start coordinates are in range i.e. less than max
            start_in_range = numpy.logical_not(
                numpy.any(post_slice_ranges[:, 0] > [max_x, max_y], axis=1))
            # Test that the end coordinates are in range i.e. more than min
            end_in_range = numpy.logical_not(
                numpy.any(post_slice_ranges[:, 1] < [min_x, min_y], axis=1))
            # When both things are true, we have a vertex in range
            pre_in_range = pre_vertices[
                numpy.logical_and(start_in_range, end_in_range)]
            connected.append((post, list(pre_in_range)))
        return connected

    def __pre_as_post_slice_ranges(
            self, slices: Iterable[Slice]) -> NDArray[integer]:
        """
        Convert a generator of (multi-dimensional) pre-slices into an array of
        post-slices.
        """
        pre_slices = ((s.get_slice(0), s.get_slice(1)) for s in slices)
        coords = numpy.array([
            ((px.start, py.start), (px.stop - 1, py.stop - 1))
            for px, py in pre_slices])
        if self.__pool_stride is not None:
            coords //= self.__pool_stride

        kernel_shape = numpy.array(self.__kernel_weights.shape)
        coords = coords - kernel_shape // 2 + self.__padding_shape
        coords //= self.__strides
        return coords

    @property
    def kernel_n_bytes(self) -> int:
        """
        Size of the weights in bytes

        :rtype: int
        """
        n_weights = self.__kernel_weights.size
        return n_weights * BYTES_PER_SHORT

    @property
    def kernel_n_weights(self) -> int:
        """
        Size of the weights.

        :rtype: int
        """
        return self.__kernel_weights.size

    @property
    def parameters_n_bytes(self) -> int:
        """
        :rtype: int
        """
        return CONNECTOR_CONFIG_SIZE

    def get_local_only_data(
            self, app_edge: ProjectionApplicationEdge, local_delay: int,
            delay_stage: int, weight_index: int) -> NDArray[uint32]:
        """
        Gets the local only data

        :param ProjectionApplicationEdge app_edge:
        :param int local_delay:
        :param int delay_stage:
        :param int weight_index:
        :rtype: ndarray
        """
        # Get info about things
        kernel_shape = self.__kernel_weights.shape
        ps_x, ps_y = 1, 1
        if self.__pool_stride is not None:
            ps_x, ps_y = self.__pool_stride

        # Do a new list for remaining connector details as uint16s
        pos_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__positive_receptor_type)
        neg_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__negative_receptor_type)

        # Produce the values needed
        short_values = numpy.array([
            kernel_shape[1], kernel_shape[0],
            self.__padding_shape[1], self.__padding_shape[0],
            pos_synapse_type, neg_synapse_type, delay_stage, local_delay,
            weight_index, 0], dtype=uint16)
        long_values = numpy.array([
            get_div_const(self.__strides[1]), get_div_const(self.__strides[0]),
            get_div_const(ps_y), get_div_const(ps_x)], dtype=uint32)
        return numpy.concatenate((short_values.view(uint32), long_values))

    def get_encoded_kernel_weights(
            self, app_edge: ProjectionApplicationEdge,
            weight_scales: NDArray[floating]) -> NDArray[int16]:
        """
        Encode weights with weight scaling.

        :param ProjectionApplicationEdge app_edge:
        :param ndarray weight_scales:
        :rtype: ndarray
        """
        encoded_kernel_weights = self.__kernel_weights.flatten()
        neg_weights = encoded_kernel_weights < 0
        pos_weights = encoded_kernel_weights > 0
        pos_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__positive_receptor_type)
        neg_synapse_type = app_edge.post_vertex.get_synapse_id_by_target(
            self.__negative_receptor_type)
        encoded_kernel_weights[neg_weights] *= weight_scales[neg_synapse_type]
        encoded_kernel_weights[pos_weights] *= weight_scales[pos_synapse_type]
        return numpy.round(encoded_kernel_weights).astype(int16)
