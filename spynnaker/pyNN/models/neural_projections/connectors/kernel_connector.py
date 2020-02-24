# Copyright (c) 2017-2019 The University of Manchester
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
from pyNN.random import RandomDistribution
from .abstract_connector import AbstractConnector
from spynnaker.pyNN.exceptions import SpynnakerException
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from .abstract_generate_connector_on_machine \
    import AbstractGenerateConnectorOnMachine, ConnectorIDs, PARAM_TYPE_KERNEL

HEIGHT, WIDTH = 0, 1
N_KERNEL_PARAMS = 8


class ConvolutionKernel(numpy.ndarray):
    pass


def shape2word(sw, sh):
    return (((numpy.uint32(sh) & 0xFFFF) << 16) |
            (numpy.uint32(sw) & 0xFFFF))


class KernelConnector(AbstractGenerateConnectorOnMachine):
    """
    Where the pre- and post-synaptic populations are considered as a 2D array.
    Connect every post(row, col) neuron to many pre(row, col, kernel) through
    a (kernel) set of weights and/or delays.

    TODO: should these include allow_self_connections and with_replacement?
    """

    def __init__(
            self, shape_pre, shape_post, shape_kernel, weight_kernel,
            delay_kernel, shape_common, pre_sample_steps_in_post,
            pre_start_coords_in_post, post_sample_steps_in_pre,
            post_start_coords_in_pre, safe, verbose,
            callback=None):
        """
        :param shape_pre:\
            2D shape of the pre population (rows/height, cols/width, usually \
            the input image shape)
        :param shape_post:\
            2D shape of the post population (rows/height, cols/width)
        :param shape_kernel:\
            2D shape of the kernel (rows/height, cols/width)
        :param weight_kernel (optional):\
            2D matrix of size shape_kernel describing the weights
        :param delay_kernel (optional):\
            2D matrix of size shape_kernel describing the delays
        :param shape_common (optional):\
            2D shape of common coordinate system (for both pre and post, \
            usually the input image sizes)
        :param pre/post_sample_steps_in_post/pre (optional):\
            Sampling steps/jumps for pre/post pop <=> (startX, endX, _stepX_)
            None or 2-item array
        :param pre/post_start_coords_in_post/pre (optional):\
            Starting row/col for pre/post sampling <=> (_startX_, endX, stepX)
            None or 2-item array
        """
        super(KernelConnector, self).__init__(
            safe=safe, callback=callback, verbose=verbose)

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

        # Get the starting coords and step sizes (or defaults if not given)
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
        self._krn_weights = self.get_kernel_vals(weight_kernel)
        self._krn_delays = self.get_kernel_vals(delay_kernel)

        self._shape_common = \
            shape_pre if shape_common is None else shape_common
        self._common_w = self._shape_common[WIDTH]
        self._common_h = self._shape_common[HEIGHT]
        self._shape_pre = shape_pre
        self._shape_post = shape_post

        # Create storage for later
        self._post_as_pre = {}

    # Get a list of possible post-slice coordinates
    def to_post_coords(self, post_vertex_slice):
        post = numpy.arange(
            post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)

        return numpy.divmod(post, self._post_w)

    # Get a map from post to pre coords
    def map_to_pre_coords(self, post_r, post_c):
        return (self._post_start_h + post_r * self._post_step_h,
                self._post_start_w + post_c * self._post_step_w)

    # Write post coords as pre coords
    def post_as_pre(self, post_vertex_slice):
        if str(post_vertex_slice) not in self._post_as_pre:
            post_r, post_c = self.to_post_coords(post_vertex_slice)
            self._post_as_pre[str(post_vertex_slice)] = self.map_to_pre_coords(
                post_r, post_c)
        return self._post_as_pre[str(post_vertex_slice)]

    # Write pre coords as post coords
    def pre_as_post(self, coords):
        r = ((coords[HEIGHT] - self._pre_start_h - 1) // self._pre_step_h) + 1
        c = ((coords[WIDTH] - self._pre_start_w - 1) // self._pre_step_w) + 1
        return (r, c)

    # Convert kernel values given into the correct format
    def get_kernel_vals(self, vals):
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

    # Compute the relevant information required for the connections
    def compute_statistics(
            self, weights, delays, pre_vertex_slice, post_vertex_slice):
        # If compute_statistics is called more than once, there's
        # no need to get the user-supplied weights and delays again
        if self._krn_weights is None:
            self._krn_weights = self.get_kernel_vals(weights)
        if self._krn_delays is None:
            self._krn_delays = self.get_kernel_vals(delays)

        post_as_pre_r, post_as_pre_c = self.post_as_pre(post_vertex_slice)
        coords = {}
        hh, hw = self._hlf_k_h, self._hlf_k_w
        all_pre_ids = []
        all_post_ids = []
        all_delays = []
        all_weights = []
        count = 0
        post_lo = post_vertex_slice.lo_atom

        # Loop over pre-vertices
        for pre_idx in range(
                pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1):
            pre_r, pre_c = divmod(pre_idx, self._pre_w)
            coords[pre_idx] = []
            # Loop over post-vertices
            for post_idx in range(
                    post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1):

                # convert to common coord system
                r = post_as_pre_r[post_idx - post_lo]
                c = post_as_pre_c[post_idx - post_lo]
                if not (0 <= r < self._common_h and 0 <= c < self._common_w):
                    continue

                r, c = self.pre_as_post((r, c))

                # Obtain coordinates to test against kernel sizes
                dr = r - pre_r
                kr = hh - dr
                dc = c - pre_c
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
        return (count, numpy.array(all_post_ids, dtype='uint32'),
                numpy.array(all_pre_ids, dtype='uint32'),
                numpy.array(all_delays), numpy.array(all_weights))

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        # I think this is overestimated, but not by much
        n_conns = (
            self._pre_w * self._pre_h * self._kernel_w * self._kernel_h)
        # Use the kernel delays if user has supplied them
        if self._krn_delays is not None:
            return self._get_delay_maximum(self._krn_delays, n_conns)

        # if not then use the values that came in
        return self._get_delay_maximum(synapse_info.delays, n_conns)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        # This is clearly a cop-out, but it works at the moment:
        # I haven't been able to make this break for "standard usage"
        return numpy.clip(
            self._kernel_h * self._kernel_w * post_vertex_slice.n_atoms,
            0, 255)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        # Again as above this is something of a cop-out and we can
        # probably do better
        return numpy.clip(
            self._kernel_h * self._kernel_w * synapse_info.n_pre_neurons,
            0, 255)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        # I think this is overestimated, but not by much
        n_conns = (
            self._pre_w * self._pre_h * self._kernel_w * self._kernel_h)
        # Use the kernel delays if user has supplied them
        if self._krn_weights is not None:
            return self._get_weight_maximum(self._krn_weights, n_conns)

        return self._get_weight_maximum(synapse_info.weights, n_conns)

    def __repr__(self):
        return "KernelConnector(shape_kernel[{},{}])".format(
            self._kernel_w, self._kernel_h)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        (n_connections, all_post, all_pre_in_range, all_pre_in_range_delays,
         all_pre_in_range_weights) = self.compute_statistics(
            synapse_info.weights, synapse_info.delays, pre_vertex_slice,
            post_vertex_slice)

        syn_dtypes = AbstractConnector.NUMPY_SYNAPSES_DTYPE

        if n_connections <= 0:
            return numpy.zeros(0, dtype=syn_dtypes)

        # 0 for exc, 1 for inh
        syn_type = numpy.array(all_pre_in_range_weights < 0)
        block = numpy.zeros(n_connections, dtype=syn_dtypes)
        block["source"] = all_pre_in_range
        block["target"] = all_post
        block["weight"] = all_pre_in_range_weights
        block["delay"] = all_pre_in_range_delays
        block["synapse_type"] = syn_type.astype('uint8')
        return block

    @property
    def _kernel_properties(self):
        return [
            shape2word(self._common_w, self._common_h),
            shape2word(self._pre_w, self._pre_h),
            shape2word(self._post_w, self._post_h),
            shape2word(self._pre_start_w, self._pre_start_h),
            shape2word(self._post_start_w, self._post_start_h),
            shape2word(self._pre_step_w, self._pre_step_h),
            shape2word(self._post_step_w, self._post_step_h),
            shape2word(self._kernel_w, self._kernel_h)]

    @overrides(AbstractGenerateConnectorOnMachine.gen_delays_id)
    def gen_delays_id(self, delays):
        if self._krn_delays is not None:
            return PARAM_TYPE_KERNEL
        return super(KernelConnector, self).gen_delays_id(delays)

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_delay_params_size_in_bytes)
    def gen_delay_params_size_in_bytes(self, delays):
        if self._krn_delays is not None:
            return (N_KERNEL_PARAMS + 1 + self._krn_delays.size) * \
                BYTES_PER_WORD
        return super(KernelConnector, self).gen_delay_params_size_in_bytes(
            delays)

    @overrides(AbstractGenerateConnectorOnMachine.gen_delay_params)
    def gen_delay_params(self, delays, pre_vertex_slice, post_vertex_slice):
        if self._krn_delays is not None:
            properties = self._kernel_properties
            properties.append(post_vertex_slice.lo_atom)
            data = numpy.array(properties, dtype="uint32")
            values = DataType.S1615.encode_as_numpy_int_array(self._krn_delays)
            return numpy.concatenate((data, values.flatten()))
        return super(KernelConnector, self).gen_delay_params(
            delays, pre_vertex_slice, post_vertex_slice)

    @overrides(AbstractGenerateConnectorOnMachine.gen_weights_id)
    def gen_weights_id(self, weights):
        if self._krn_weights is not None:
            return PARAM_TYPE_KERNEL
        return super(KernelConnector, self).gen_weights_id(weights)

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_weight_params_size_in_bytes)
    def gen_weight_params_size_in_bytes(self, weights):
        if self._krn_weights is not None:
            return (N_KERNEL_PARAMS + 1 + self._krn_weights.size) * \
                BYTES_PER_WORD
        return super(KernelConnector, self).gen_weight_params_size_in_bytes(
            weights)

    @overrides(AbstractGenerateConnectorOnMachine.gen_weights_params)
    def gen_weights_params(self, weights, pre_vertex_slice, post_vertex_slice):
        if self._krn_weights is not None:
            properties = self._kernel_properties
            properties.append(post_vertex_slice.lo_atom)
            data = numpy.array(properties, dtype="uint32")
            values = DataType.S1615.encode_as_numpy_int_array(
                self._krn_weights)
            return numpy.concatenate((data, values.flatten()))
        return super(KernelConnector, self).gen_weights_params(
            weights, pre_vertex_slice, post_vertex_slice)

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.KERNEL_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params)
    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        return numpy.array(self._kernel_properties, dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return N_KERNEL_PARAMS * BYTES_PER_WORD
