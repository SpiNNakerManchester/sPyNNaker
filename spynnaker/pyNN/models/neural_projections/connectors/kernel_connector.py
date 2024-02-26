# Copyright (c) 2017 The University of Manchester
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
from typing import Dict, List, Optional, Sequence, Tuple, Union, TYPE_CHECKING

import numpy
from numpy import floating, integer, ndarray, uint32
from numpy.typing import NDArray
from typing_extensions import TypeAlias

from pyNN.random import RandomDistribution
from pyNN.space import Space

from spinn_utilities.overrides import overrides

from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice

from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.types import (
    Delay_Types, Weight_Delay_Types, Weight_Types)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    _TwoD: TypeAlias = Union[List[int], Tuple[int, int]]

_Kernel: TypeAlias = Union[
    float, int, List[float], NDArray[numpy.floating], RandomDistribution]

HEIGHT, WIDTH = 0, 1
N_KERNEL_PARAMS = 8


class ConvolutionKernel(ndarray):
    """
    Thin wrapper around a numpy array.
    """
    pass


def shape2word(
        short1: Union[int, integer], short2: Union[int, integer]) -> uint32:
    """
    Combines two short values into 1 int by shifting the first 16 places

    :param int short1: first 2 byte value
    :param int short2: second 2 bytes value
    :rtype: int
    """
    return uint32(((uint32(short2) & 0xFFFF) << 16) | (uint32(short1) & 0xFFFF))


class KernelConnector(AbstractGenerateConnectorOnMachine,
                      AbstractGenerateConnectorOnHost):
    """
    Where the pre- and post-synaptic populations are considered as a 2D
    array. Connect every post(row, column) neuron to many
    pre(row, column, kernel)
    through a (kernel) set of weights and/or delays.
    """
    __slots__ = (
        "_kernel_w", "_kernel_h",
        "_hlf_k_w", "_hlf_k_h",
        "_pre_w", "_pre_h",
        "_post_w", "_post_h",
        "_pre_start_w", "_pre_start_h",
        "_post_start_w", "_post_start_h",
        "_pre_step_w", "_pre_step_h",
        "_post_step_w", "_post_step_h",
        "_krn_weights", "_krn_delays", "_shape_common",
        "_common_w", "_common_h",
        "_shape_pre", "_shape_post",
        "_post_as_pre")

    def __init__(
            self, shape_pre: _TwoD, shape_post: _TwoD, shape_kernel: _TwoD,
            weight_kernel: Optional[_Kernel] = None,
            delay_kernel: Optional[_Kernel] = None,
            shape_common: Optional[_TwoD] = None,
            pre_sample_steps_in_post: Optional[_TwoD] = None,
            pre_start_coords_in_post: Optional[_TwoD] = None,
            post_sample_steps_in_pre: Optional[_TwoD] = None,
            post_start_coords_in_pre: Optional[_TwoD] = None,
            safe: bool = True, space: Optional[Space] = None,
            verbose: bool = False, callback: None = None):
        """
        :param shape_pre:
            2D shape of the pre-population (rows/height, columns/width, usually
            the input image shape)
        :type shape_pre: list(int) or tuple(int,int)
        :param shape_post:
            2D shape of the post-population (rows/height, columns/width)
        :type shape_post: list(int) or tuple(int,int)
        :param shape_kernel:
            2D shape of the kernel (rows/height, columns/width)
        :type shape_kernel: list(int) or tuple(int,int)
        :param weight_kernel: (optional)
            2D matrix of size shape_kernel describing the weights
        :type weight_kernel: ~numpy.ndarray or ~pyNN.random.RandomDistribution
            or int or float or list(int) or list(float) or None
        :param delay_kernel: (optional)
            2D matrix of size shape_kernel describing the delays
        :type delay_kernel: ~numpy.ndarray or ~pyNN.random.RandomDistribution
            or int or float or list(int) or list(float) or None
        :param shape_common: (optional)
            2D shape of common coordinate system (for both pre- and post-,
            usually the input image sizes)
        :type shape_common: list(int) or tuple(int,int) or None
        :param pre_sample_steps_in_post: (optional)
            Sampling steps/jumps for pre-population <=> (stepX, stepY)
        :type pre_sample_steps_in_post: None or list(int) or tuple(int,int)
        :param pre_start_coords_in_post: (optional)
            Starting row/column for pre-population sampling <=> (offX, offY)
        :type pre_start_coords_in_post: None or list(int) or tuple(int,int)
        :param post_sample_steps_in_pre: (optional)
            Sampling steps/jumps for post-population <=> (stepX, stepY)
        :type post_sample_steps_in_pre: None or list(int) or tuple(int,int)
        :param post_start_coords_in_pre: (optional)
            Starting row/column for post-population sampling <=> (offX, offY)
        :type post_start_coords_in_pre: None or list(int) or tuple(int,int)
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param ~pyNN.space.Space space:
            Currently ignored; for future compatibility.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param callable callback: (ignored)
        """
        super().__init__(safe=safe, callback=callback, verbose=verbose)
        assert space is None, "non-None space unsupported"

        # Get the kernel size
        self._kernel_w = shape_kernel[WIDTH]
        self._kernel_h = shape_kernel[HEIGHT]

        # The half-value used here indicates the half-way array position
        self._hlf_k_w = shape_kernel[WIDTH] // 2
        self._hlf_k_h = shape_kernel[HEIGHT] // 2

        # Cache values for the pre and post sizes
        self._pre_w = shape_pre[WIDTH]
        self._pre_h = shape_pre[HEIGHT]
        self._post_w = shape_post[WIDTH]
        self._post_h = shape_post[HEIGHT]

        # Get the starting coordinates and step sizes (or defaults if not given)
        if pre_start_coords_in_post is None:
            self._pre_start_w = 0
            self._pre_start_h = 0
        else:
            self._pre_start_w = pre_start_coords_in_post[WIDTH]
            self._pre_start_h = pre_start_coords_in_post[HEIGHT]

        if post_start_coords_in_pre is None:
            self._post_start_w = 0
            self._post_start_h = 0
        else:
            self._post_start_w = post_start_coords_in_pre[WIDTH]
            self._post_start_h = post_start_coords_in_pre[HEIGHT]

        if pre_sample_steps_in_post is None:
            self._pre_step_w = 1
            self._pre_step_h = 1
        else:
            self._pre_step_w = pre_sample_steps_in_post[WIDTH]
            self._pre_step_h = pre_sample_steps_in_post[HEIGHT]

        if post_sample_steps_in_pre is None:
            self._post_step_w = 1
            self._post_step_h = 1
        else:
            self._post_step_w = post_sample_steps_in_pre[WIDTH]
            self._post_step_h = post_sample_steps_in_pre[HEIGHT]

        # Make sure the supplied values are in the correct format
        self._krn_weights = self.__get_kernel_vals(weight_kernel)
        self._krn_delays = self.__get_kernel_vals(delay_kernel)

        self._shape_common = \
            shape_pre if shape_common is None else shape_common
        self._common_w = self._shape_common[WIDTH]
        self._common_h = self._shape_common[HEIGHT]
        self._shape_pre = shape_pre
        self._shape_post = shape_post

        # Create storage for later
        self._post_as_pre: Dict[
            Slice, Tuple[NDArray[integer], NDArray[integer]]] = {}

    def __to_post_coords(
            self, post_vertex_slice: Slice) -> Tuple[
                NDArray[integer], NDArray[integer]]:
        """
        Get a list of possible post-slice coordinates.

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :rtype: tuple(~numpy.ndarray, ~numpy.ndarray)
        """
        post = numpy.arange(
            post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1,
            dtype=uint32)
        return numpy.divmod(post, self._post_w)

    def __map_to_pre_coords(
            self, post_r: NDArray[integer], post_c: NDArray[integer]) -> Tuple[
                NDArray[integer], NDArray[integer]]:
        """
        Get a map from post to pre-population coordinates.

        :param ~numpy.ndarray post_r: rows
        :param ~numpy.ndarray post_c: columns
        :rtype: tuple(~numpy.ndarray, ~numpy.ndarray)
        """
        return (self._post_start_h + post_r * self._post_step_h,
                self._post_start_w + post_c * self._post_step_w)

    def __post_as_pre(self, post_vertex_slice: Slice) -> Tuple[
            NDArray[integer], NDArray[integer]]:
        """
        Write post-population coordinates as pre-population coordinates.

        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :rtype: tuple(~numpy.ndarray, ~numpy.ndarray)
        """
        # directly as the cache index
        if post_vertex_slice not in self._post_as_pre:
            post_r, post_c = self.__to_post_coords(post_vertex_slice)
            self._post_as_pre[post_vertex_slice] = \
                self.__map_to_pre_coords(post_r, post_c)
        return self._post_as_pre[post_vertex_slice]

    def __pre_as_post(self, pre_r: int, pre_c: int) -> Tuple[int, int]:
        """
        Write pre-population coordinates as post-population coordinates.

        :param int pre_r: row
        :param int pre_c: column
        :rtype: tuple(int,int)
        """
        r = ((pre_r - self._pre_start_h - 1) // self._pre_step_h) + 1
        c = ((pre_c - self._pre_start_w - 1) // self._pre_step_w) + 1
        return (r, c)

    def __get_kernel_vals(self, values: Optional[Union[
            _Kernel, Weight_Delay_Types]]) -> Optional[ConvolutionKernel]:
        """
        Convert kernel values given into the correct format.

        :param values:
        :type values: int or float or ~pyNN.random.RandomDistribution
            or ~numpy.ndarray or ConvolutionKernel
        :rtype: ~numpy.ndarray
        """
        if values is None:
            return None
        if isinstance(values, list):
            values = numpy.asarray(values)
        krn_size = self._kernel_h * self._kernel_w
        krn_shape = (self._kernel_h, self._kernel_w)
        if isinstance(values, RandomDistribution):
            return numpy.array(values.next(krn_size)).reshape(krn_shape).view(
                ConvolutionKernel)
        elif numpy.isscalar(values):
            return numpy.full(krn_shape, values).view(ConvolutionKernel)
        elif ((isinstance(values, numpy.ndarray) or
               isinstance(values, ConvolutionKernel)) and
              values.shape[HEIGHT] == self._kernel_h and
              values.shape[WIDTH] == self._kernel_w):
            return values.view(ConvolutionKernel)
        raise SpynnakerException(
            "Error generating KernelConnector values; if you have supplied "
            "weight and/or delay kernel then ensure they are the same size "
            "as specified by the shape kernel values (height: "
            f"{self._kernel_h} and width: {self._kernel_w}).")

    def __compute_statistics(
            self, weights: Optional[Weight_Types],
            delays: Optional[Delay_Types], post_vertex_slice: Slice,
            n_pre_neurons: int) -> Tuple[
                int, NDArray[uint32], NDArray[uint32], NDArray[floating],
                NDArray[floating]]:
        """
        Compute the relevant information required for the connections.

        :param weights:
        :type weights: int or float or ~pyNN.random.RandomDistribution or
            ~numpy.ndarray or ConvolutionKernel
        :param delays:
        :type delays: int or float or ~pyNN.random.RandomDistribution or
            ~numpy.ndarray or ConvolutionKernel
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        """
        # If __compute_statistics is called more than once, there's
        # no need to get the user-supplied weights and delays again
        if self._krn_weights is None:
            self._krn_weights = self.__get_kernel_vals(weights)
        if self._krn_delays is None:
            self._krn_delays = self.__get_kernel_vals(delays)
        assert self._krn_weights is not None
        assert self._krn_delays is not None

        post_as_pre_r, post_as_pre_c = self.__post_as_pre(post_vertex_slice)
        coords: Dict[int, List[int]] = {}
        hh, hw = self._hlf_k_h, self._hlf_k_w
        all_pre_ids: List[int] = []
        all_post_ids: List[int] = []
        all_delays: List[NDArray[floating]] = []
        all_weights: List[NDArray[floating]] = []
        count = 0
        post_lo = post_vertex_slice.lo_atom

        # Loop over pre-vertices
        for pre_idx in range(n_pre_neurons):
            pre_r, pre_c = divmod(pre_idx, self._pre_w)
            coords[pre_idx] = []

            # Test whether the coordinates should be included based on the
            # step function (in the pre) and skip if not
            if not (((pre_r - self._pre_start_h) % self._pre_step_h == 0) and
                    ((pre_c - self._pre_start_w) % self._pre_step_w == 0)):
                continue

            # Loop over post-vertices
            for post_idx in range(
                    post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1):
                # convert to common coordinate system
                pac_r = post_as_pre_r[post_idx - post_lo]
                pac_c = post_as_pre_c[post_idx - post_lo]

                # now convert common to pre coordinates
                pap_r, pap_c = self.__pre_as_post(pac_r, pac_c)

                # Obtain coordinates to test against kernel sizes
                dr = pap_r - pre_r
                kr = hh - dr
                dc = pap_c - pre_c
                kc = hw - dc

                if 0 <= kr < self._kernel_h and 0 <= kc < self._kernel_w:
                    if post_idx in coords[pre_idx]:
                        continue
                    coords[pre_idx].append(post_idx)

                    # Store weights, delays and pre/post ids
                    w = self._krn_weights[kr, kc]
                    d = self._krn_delays[kr, kc]

                    count += 1

                    all_pre_ids.append(pre_idx)
                    all_post_ids.append(post_idx)
                    all_delays.append(d)
                    all_weights.append(w)

        # Now the loop is complete, return relevant data
        return (count, numpy.array(all_post_ids, dtype=uint32),
                numpy.array(all_pre_ids, dtype=uint32),
                numpy.array(all_delays), numpy.array(all_weights))

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        # Use the kernel delays if user has supplied them
        if self._krn_delays is not None:
            return numpy.max(self._krn_delays)

        # I think this is overestimated, but not by much
        n_conns = (
            self._pre_w * self._pre_h * self._kernel_w * self._kernel_h)

        # if not then use the values that came in
        return self._get_delay_maximum(
            synapse_info.delays, n_conns, synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        # Use the kernel delays if user has supplied them
        if self._krn_delays is not None:
            return numpy.min(self._krn_delays)

        # I think this is overestimated, but not by much
        n_conns = (
            self._pre_w * self._pre_h * self._kernel_w * self._kernel_h)

        # if not then use the values that came in
        return self._get_delay_minimum(
            synapse_info.delays, n_conns, synapse_info)

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(self, delays: Delay_Types,
                           synapse_info: SynapseInformation) -> float:
        if self._krn_delays is not None:
            return float(numpy.var(self._krn_delays))
        return super().get_delay_variance(delays, synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        return numpy.clip(self._kernel_h * self._kernel_w, 0, n_post_atoms)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        return numpy.clip(self._kernel_h * self._kernel_w, 0, 255)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        # Use the kernel weights if user has supplied them
        if self._krn_weights is not None:
            return numpy.max(self._krn_weights)

        # I think this is overestimated, but not by much
        n_conns = self._pre_w * self._pre_h * self._kernel_w * self._kernel_h
        return self._get_weight_maximum(
            synapse_info.weights, n_conns, synapse_info)

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(self, weights: Weight_Types,
                        synapse_info: SynapseInformation) -> float:
        # Use the kernel weights if user has supplied them
        if self._krn_weights is not None:
            return float(numpy.mean(self._krn_weights))
        return super().get_weight_mean(weights, synapse_info)

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(self, weights: Weight_Types,
                            synapse_info: SynapseInformation) -> float:
        # Use the kernel weights if user has supplied them
        if self._krn_weights is not None:
            return float(numpy.var(self._krn_weights))
        return super().get_weight_variance(weights, synapse_info)

    def __repr__(self):
        return \
            f"KernelConnector(shape_kernel[{self._kernel_w},{self._kernel_h}])"

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        (n_connections, all_post, all_pre_in_range, all_pre_in_range_delays,
         all_pre_in_range_weights) = self.__compute_statistics(
            synapse_info.weights, synapse_info.delays, post_vertex_slice,
            synapse_info.n_pre_neurons)

        syn_dtypes = AbstractConnector.NUMPY_SYNAPSES_DTYPE

        if n_connections <= 0:
            return numpy.zeros(0, dtype=syn_dtypes)

        # 0 for excitatory, 1 for inhibitory
        syn_type = numpy.array(all_pre_in_range_weights < 0)
        block = numpy.zeros(n_connections, dtype=syn_dtypes)
        block["source"] = all_pre_in_range
        block["target"] = all_post
        block["weight"] = all_pre_in_range_weights
        block["delay"] = all_pre_in_range_delays
        block["synapse_type"] = syn_type.astype('uint8')
        return block

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self) -> int:
        return ConnectorIDs.KERNEL_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(
            self, synapse_info: SynapseInformation) -> NDArray[uint32]:
        data = numpy.array([
            shape2word(self._common_w, self._common_h),
            shape2word(self._pre_w, self._pre_h),
            shape2word(self._post_w, self._post_h),
            shape2word(self._pre_start_w, self._pre_start_h),
            shape2word(self._post_start_w, self._post_start_h),
            shape2word(self._pre_step_w, self._pre_step_h),
            shape2word(self._post_step_w, self._post_step_h),
            shape2word(self._kernel_w, self._kernel_h),
            shape2word(int(self._krn_weights is not None),
                       int(self._krn_delays is not None))], dtype=uint32)
        extra_data = []
        if self._krn_weights is not None:
            extra_data.append(DataType.S1615.encode_as_numpy_int_array(
                self._krn_weights.flatten()))
        if self._krn_delays is not None:
            extra_data.append(DataType.S1615.encode_as_numpy_int_array(
                self._krn_delays.flatten()))

        if extra_data:
            return numpy.concatenate((data, *extra_data))
        return data

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self) -> int:
        return N_KERNEL_PARAMS * BYTES_PER_WORD

    @overrides(AbstractGenerateConnectorOnMachine.get_connected_vertices)
    def get_connected_vertices(
            self, s_info: SynapseInformation, source_vertex: ApplicationVertex,
            target_vertex: ApplicationVertex) -> Sequence[
                Tuple[MachineVertex, Sequence[AbstractVertex]]]:
        src_splitter = source_vertex.splitter
        return [
            (t_vert,
             [s_vert for s_vert in src_splitter.get_out_going_vertices(
                 SPIKE_PARTITION_ID) if self.__connects(s_vert, t_vert)])
            for t_vert in target_vertex.splitter.get_in_coming_vertices(
                SPIKE_PARTITION_ID)]

    def __connects(self, src_machine_vertex: MachineVertex,
                   dest_machine_vertex: MachineVertex) -> bool:
        # If the pre- and post-slices are not 2-dimensional slices, we have
        # to let them pass
        pre_slice = src_machine_vertex.vertex_slice
        post_slice = dest_machine_vertex.vertex_slice
        if (pre_slice.shape is None or len(pre_slice.shape) != 2 or
                post_slice.shape is None or len(post_slice.shape) != 2):
            return True

        pre_slice_x = pre_slice.get_slice(0)
        pre_slice_y = pre_slice.get_slice(1)
        post_slice_x = post_slice.get_slice(0)
        post_slice_y = post_slice.get_slice(1)

        min_pre_x = post_slice_x.start - self._hlf_k_w
        max_pre_x = (post_slice_x.stop + self._hlf_k_w) - 1
        min_pre_y = post_slice_y.start - self._hlf_k_h
        max_pre_y = (post_slice_y.stop + self._hlf_k_h) - 1

        # No part of the pre square overlaps the post-square, don't connect
        if (pre_slice_x.stop <= min_pre_x or
                pre_slice_x.start > max_pre_x or
                pre_slice_y.stop <= min_pre_y or
                pre_slice_y.start > max_pre_y):
            return False

        # Otherwise, they do
        return True

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation):
        pre = application_edge.pre_vertex
        post = application_edge.post_vertex
        if len(pre.atoms_shape) != 1 or len(post.atoms_shape) != 1:
            raise ConfigurationException(
                "The Kernel Connector is designed to work with 1D vertices")
