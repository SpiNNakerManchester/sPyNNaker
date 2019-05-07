import numpy
from pyNN.random import RandomDistribution
from .abstract_connector import AbstractConnector
from spynnaker.pyNN.exceptions import SpynnakerException
from pacman.model.decorators.overrides import overrides
from data_specification.enums.data_type import DataType
from .abstract_generate_connector_on_machine \
    import AbstractGenerateConnectorOnMachine, ConnectorIDs, PARAM_TYPE_KERNEL

HEIGHT, WIDTH = 0, 1
N_KERNEL_PARAMS = 8


# TODO: Is this being used anywhere now?
class ConvolutionKernel(numpy.ndarray):
    pass


def shape2word(sw, sh):
    return (((numpy.uint32(sw) & 0xFFFF) << 16) |
            (numpy.uint32(sh) & 0xFFFF))


class KernelConnector(AbstractConnector):
# class KernelConnector(AbstractGenerateConnectorOnMachine):
    """
    Where the pre- and post-synaptic populations are thought-of as a 2D array.\
    Connect every post(row, col) neuron to many pre(row, col, kernel) through\
    a (kernel) set of weights and/or delays.

    TODO: should these include allow_self_connections and with_replacement?
    """

    def __init__(
            self, shape_pre, shape_post, shape_kernel, weight_kernel,
            delay_kernel, shape_common, pre_sample_steps, pre_start_coords,
            post_sample_steps, post_start_coords, safe, space, verbose):
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
        :param pre/post_sample_steps (optional):\
            Sampling steps/jumps for post pop <=> (startX, endX, _stepX_)
            None or 2-item array
        :param pre/post_start_coords (optional):\
            Starting row/col for sampling <=> (_startX_, endX, stepX)
            None or 2-item array
        """
        super(KernelConnector, self).__init__(safe=safe, verbose=verbose)

        # Get the kernel size
        self._kernel_w = shape_kernel[WIDTH]
        self._kernel_h = shape_kernel[HEIGHT]

        print('pre-post neurons ', self._n_pre_neurons, self._n_post_neurons)

        # if the width or height is even then thrown an exception
        if (self._kernel_w % 2 == 0) or (self._kernel_h % 2 == 0):
            raise SpynnakerException(
                "Weight kernel specified with even size in one or"
                "both dimensions; kernels should only have odd dimensions")

        # The half-value used here indicates the half-way array position
        self._hlf_k_w = shape_kernel[WIDTH] // 2
        self._hlf_k_h = shape_kernel[HEIGHT] // 2

        # Cache values for the pre and post sizes
        self._pre_w = shape_pre[WIDTH]
        self._pre_h = shape_pre[HEIGHT]
        self._post_w = shape_post[WIDTH]
        self._post_h = shape_post[HEIGHT]

        # Get the starting coords and step sizes (or defaults if not given)
        if pre_start_coords is None:
            self._pre_start_w = 0
            self._pre_start_h = 0
        else:
            self._pre_start_w = pre_start_coords[WIDTH]
            self._pre_start_h = pre_start_coords[HEIGHT]

        if post_start_coords is None:
            self._post_start_w = 0
            self._post_start_h = 0
        else:
            self._post_start_w = post_start_coords[WIDTH]
            self._post_start_h = post_start_coords[HEIGHT]

        if pre_sample_steps is None:
            self._pre_step_w = 1
            self._pre_step_h = 1
        else:
            self._pre_step_w = pre_sample_steps[WIDTH]
            self._pre_step_h = pre_sample_steps[HEIGHT]

        if post_sample_steps is None:
            self._post_step_w = 1
            self._post_step_h = 1
        else:
            self._post_step_w = post_sample_steps[WIDTH]
            self._post_step_h = post_sample_steps[HEIGHT]

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
        self._pre_in_range = {}
        self._all_post = {}
        self._all_pre_in_range = {}
        self._all_pre_in_range_delays = {}
        self._all_pre_in_range_weights = {}
        self._post_as_pre = {}
        self._num_conns = {}

    # this function isn't called anywhere?
#     def pre_in_range(self, pre_vertex_slice, post_vertex_slice):
#         if (str(pre_vertex_slice) not in self._pre_in_range and
#                 str(post_vertex_slice) not in
#                 self._pre_in_range[str(pre_vertex_slice)]):
#             self.compute_statistics(pre_vertex_slice, post_vertex_slice)
#         return self._pre_in_range[pre_vertex_slice][post_vertex_slice]

    def to_post_coords(self, post_vertex_slice):
        post = numpy.arange(
            post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)

        return post // self._post_w, post % self._post_w

    def map_to_pre_coords(self, post_r, post_c):
        return (self._post_start_h + post_r * self._post_step_h,
                self._post_start_w + post_c * self._post_step_w)

    def post_as_pre(self, post_vertex_slice):
        if str(post_vertex_slice) not in self._post_as_pre:
            post_r, post_c = self.to_post_coords(post_vertex_slice)
            self._post_as_pre[str(post_vertex_slice)] = self.map_to_pre_coords(
                post_r, post_c)
        return self._post_as_pre[str(post_vertex_slice)]

    def pre_as_post(self, coords):
        r = ((coords[HEIGHT] - self._pre_start_h - 1) // self._pre_step_h) + 1
        c = ((coords[WIDTH] - self._pre_start_w - 1) // self._pre_step_w) + 1
        return (r, c)

    def get_kernel_vals(self, vals):
        # TODO: can this be covered using _generate_values etc.
        #       in the AbstractConnector?
        if vals is None:
            return None
        krn_size = self._kernel_h * self._kernel_w
        krn_shape = (self._kernel_h, self._kernel_w)
        print('vals: ', vals)
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
        raise SpynnakerException("Error generating KernelConnector values")

    def init_pre_entries(self, pre_vertex_slice_str):
        if pre_vertex_slice_str not in self._num_conns:
            self._num_conns[pre_vertex_slice_str] = {}

        if pre_vertex_slice_str not in self._pre_in_range:
            self._pre_in_range[pre_vertex_slice_str] = {}

        if pre_vertex_slice_str not in self._all_post:
            self._all_post[pre_vertex_slice_str] = {}

        if pre_vertex_slice_str not in self._all_pre_in_range:
            self._all_pre_in_range[pre_vertex_slice_str] = {}

        if pre_vertex_slice_str not in self._all_pre_in_range_delays:
            self._all_pre_in_range_delays[pre_vertex_slice_str] = {}

        if pre_vertex_slice_str not in self._all_pre_in_range_weights:
            self._all_pre_in_range_weights[pre_vertex_slice_str] = {}

    def compute_statistics(
            self, weights, delays, pre_vertex_slice, post_vertex_slice):
        print("In kernel connector, compute_statistics")

        # If compute_statistics is called more than once, there's
        # no need to get these weights and delays again
        if self._krn_weights is None:
            self._krn_weights = self.get_kernel_vals(weights)
        if self._krn_delays is None:
            self._krn_delays = self.get_kernel_vals(delays)

        print('weights: ', self._krn_weights)

        pre_vs = str(pre_vertex_slice)
        post_vs = str(post_vertex_slice)
        self.init_pre_entries(pre_vs)

        post_as_pre_r, post_as_pre_c = self.post_as_pre(post_vertex_slice)
        coords = {}
        hh, hw = self._hlf_k_h, self._hlf_k_w
        print('hh, hw', hh, hw)
#         print('post_as: ', post_as_pre_r, post_as_pre_c)
        unique_pre_ids = []
        all_pre_ids = []
        all_post_ids = []
        all_delays = []
        all_weights = []
        count = 0
        post_lo = post_vertex_slice.lo_atom

        for pre_idx in range(
                pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1):
            pre_r = pre_idx // self._pre_w
            pre_c = pre_idx % self._pre_w
#             print('pre_idx, pre_r, pre_c: ', pre_idx, pre_r, pre_c)
            coords[pre_idx] = []
            for post_idx in range(
                    post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1):

                # convert to common coord system
                r = post_as_pre_r[post_idx - post_lo]
                c = post_as_pre_c[post_idx - post_lo]
                if r < 0 or r >= self._common_h or \
                   c < 0 or c >= self._common_w:
                    continue

                r, c = self.pre_as_post((r, c))

                fr_r = max(0, r - hh)
                to_r = min(r + hh + 1, self._pre_h)
                fr_c = max(0, c - hw)
                to_c = min(c + hw + 1, self._pre_w)

                if fr_r <= pre_r and pre_r < to_r and \
                   fr_c <= pre_c and pre_c < to_c:

                    if post_idx in coords[pre_idx]:
                        continue

                    coords[pre_idx].append(post_idx)

#                     dr = abs(r - pre_r)  # absolute?
                    dr = r - pre_r
                    kr = hh - dr
#                     dc = abs(c - pre_c)  # absolute?
                    dc = c - pre_c
                    kc = hw - dc

#                     print('dr, dc: ', dr, dc, self._krn_weights)

                    w = self._krn_weights[kr, kc]
                    d = self._krn_delays[kr, kc]

#                     print('w, d: ', w, d)

                    count += 1

                    all_pre_ids.append(pre_idx)
                    all_post_ids.append(post_idx)
                    all_delays.append(d)
                    all_weights.append(w)

        self._pre_in_range[pre_vs][post_vs] = numpy.array(unique_pre_ids)
        self._num_conns[pre_vs][post_vs] = count
        # print("\n\n%s -> %s = %d conns\n"%(pre_vs, post_vs, count))
        self._all_post[pre_vs][post_vs] = numpy.array(
            all_post_ids, dtype='uint32')
        self._all_pre_in_range[pre_vs][post_vs] = numpy.array(
            all_pre_ids, dtype='uint32')
        self._all_pre_in_range_delays[pre_vs][post_vs] = numpy.array(
            all_delays)
        self._all_pre_in_range_weights[pre_vs][post_vs] = numpy.array(
            all_weights)

        return self._pre_in_range[pre_vs][post_vs]

    def min_max_coords(self, pre_r, pre_c):
        hh, hw = self._hlf_k_h, self._hlf_k_w
        return (numpy.array([pre_r[0] - hh, pre_c[0] - hw]),
                numpy.array([pre_r[-1] + hh, pre_c[-1] + hw]))

    def to_pre_indices(self, pre_r, pre_c):
        return pre_r * self._pre_w + pre_c

    def gen_key(self, pre_vertex_slice, post_vertex_slice):
        return '%s->%s' % (pre_vertex_slice, post_vertex_slice)

    def get_num_conns(
            self, weights, delays, pre_vertex_slice, post_vertex_slice):
        if (str(pre_vertex_slice) not in self._num_conns or
                str(post_vertex_slice) not in
                self._num_conns[str(pre_vertex_slice)]):
            self.compute_statistics(weights, delays,
                                    pre_vertex_slice, post_vertex_slice)

        return self._num_conns[str(pre_vertex_slice)][str(post_vertex_slice)]

    def get_all_delays(self, pre_vertex_slice, post_vertex_slice):
        if (str(pre_vertex_slice) not in self._all_pre_in_range_delays or
                str(post_vertex_slice) not in
                self._all_pre_in_range_delays[str(pre_vertex_slice)]):
            self.compute_statistics(weights, delays,
                                    pre_vertex_slice, post_vertex_slice)

        return self._all_pre_in_range_delays[
            str(pre_vertex_slice)][str(post_vertex_slice)]

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        print('get_delay_maximum', self._n_pre_neurons, self._n_post_neurons)
        # I think this is overestimated, but not by much
        n_conns = (
            self._pre_w * self._pre_h * self._kernel_w * self._kernel_h)
        # use the kernel delays if user has supplied them
        if self._krn_delays is not None:
            return self._get_delay_maximum(self._krn_delays, n_conns)

        # if not then use the values that came in
        return self._get_delay_maximum(delays, n_conns)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):
        print('get_n_connections_from_pre_vertex_maximum')
        # If the user hasn't supplied delays, do it this way
#         if self._krn_delays is None:
#             return self._get_n_connections_from_pre_vertex_with_delay_maximum(
#                 delays, self._n_pre_neurons * self._n_post_neurons,
#                 self._kernel_h * self._kernel_w * self._pre_w * self._pre_h,
#                 min_delay, max_delay)

        # I am not quite sure really what's going on here; it
        # appears to basically be doing the same as the clip function anyway
#         if isinstance(delays, ConvolutionKernel):
#             if self._weights.size > pre_vertex_slice.n_atoms:
#                 return pre_vertex_slice.n_atoms
#             elif self._weights.size > 255:
#                 return 255
#             else:
#                 return (self._weights[self._weights != 0]).size

        # This is clearly a cop-out, but it works at the moment:
        # I haven't been able to make this break for "standard usage"
        return numpy.clip(
            self._kernel_h * self._kernel_w * self._pre_h * self._pre_w,
            0, 255)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        print('get_n_connections_to_post_vertex_maximum')

#         if isinstance(self._krn_weights, ConvolutionKernel):
#             if self._krn_weights.size > pre_vertex_slice.n_atoms:
#                 return pre_vertex_slice.n_atoms
#             elif self._krn_weights.size > 255:
#                 return 255
#             else:
#                 return (self._weights[self._weights != 0]).size

        # Again as above this is something of a cop-out and we can
        # probably do better
        return numpy.clip(
            self._kernel_h * self._kernel_w * self._post_h * self._post_w,
            0, 255)

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        print('get_weight_maximum')
        # Get relevant slices
        slices = (slice(0, self._kernel_h), slice(0, self._kernel_w))
        # it would be better to use the pre to post sizes here...
        n_conns = (
            self._pre_w * self._pre_h * self._kernel_w * self._kernel_h)
        return self._get_weight_maximum(weights, n_conns)

    def __repr__(self):
        return "KernelConnector"

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        print('create_synaptic_block')
        n_connections = self.get_num_conns(weights, delays,
                                           pre_vertex_slice, post_vertex_slice)

        syn_dtypes = AbstractConnector.NUMPY_SYNAPSES_DTYPE

        if n_connections <= 0:
            return numpy.zeros(0, dtype=syn_dtypes)

        pre_vs = str(pre_vertex_slice)
        post_vs = str(post_vertex_slice)

        # 0 for exc, 1 for inh
        syn_type = numpy.array(
            self._all_pre_in_range_weights[pre_vs][post_vs] < 0)
        block = numpy.zeros(n_connections, dtype=syn_dtypes)
        block["source"] = self._all_pre_in_range[pre_vs][post_vs]
        block["target"] = self._all_post[pre_vs][post_vs]
        block["weight"] = self._all_pre_in_range_weights[pre_vs][post_vs]
        block["delay"] = self._all_pre_in_range_delays[pre_vs][post_vs]
        block["synapse_type"] = syn_type.astype('uint8')
        return block

#    Double-check this, but I think this property exists in
#    AbstractGenerateConnectorOnMachine already
    @property
    def generate_on_machine(self):
        super_generate = super(KernelConnector, self).generate_on_machine

        # This connector can also cope with listed weights and delays
        return super_generate or (isinstance(self._delays, numpy.ndarray) and
                                  isinstance(self._weights, numpy.ndarray))

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

#    I think everything commented out below is covered in
#    AbstractGenerateConnectorOnMachine
    @overrides(AbstractGenerateConnectorOnMachine.gen_delays_id)
    def gen_delays_id(self, delays):
        if self._krn_delays is not None:
            return PARAM_TYPE_KERNEL
        return super(KernelConnector, self).gen_delays_id(delays)

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_delay_params_size_in_bytes)
    def gen_delay_params_size_in_bytes(self, delays):
        if self._krn_delays is not None:
            return (N_KERNEL_PARAMS + 1 + self._krn_delays.size) * 4
        return super(KernelConnector, self).gen_delay_params_size_in_bytes(
            delays)

    @overrides(AbstractGenerateConnectorOnMachine.gen_delay_params)
    def gen_delay_params(self, delays, pre_vertex_slice, post_vertex_slice):
        if self._krn_delays is not None:
            properties = self._kernel_properties
            properties.append(post_vertex_slice.lo_atom)
            data = numpy.array(properties, dtype="uint32")
            values = numpy.round(self._krn_delays * float(
                DataType.S1615.scale)).astype("uint32")
            print('delays data, values ', data, values.flatten())
            print('kernel_h, kernel_w', self._kernel_h, self._kernel_w)
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
            return (N_KERNEL_PARAMS + 1 + self._krn_weights.size) * 4
        return super(KernelConnector, self).gen_weight_params_size_in_bytes(
            weights)

    @overrides(AbstractGenerateConnectorOnMachine.gen_weights_params)
    def gen_weights_params(self, weights, pre_vertex_slice, post_vertex_slice):
        if self._krn_weights is not None:
            properties = self._kernel_properties
            properties.append(post_vertex_slice.lo_atom)
            data = numpy.array(properties, dtype="uint32")
            values = numpy.round(self._krn_weights * float(
                DataType.S1615.scale)).astype("uint32")
            print('weights data, values ', data, values.flatten())
            print('kernel_h, kernel_w', self._kernel_h, self._kernel_w)
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
            synapse_type):
        # Not just the kernel_properties any more;
        # add the kernel weights and delays as well?
        # does it need the lo_atom value??
        return numpy.array(self._kernel_properties, dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return N_KERNEL_PARAMS * 4

    def get_max_num_connections(self, pre_slice, post_slice):
        return post_slice.n_atoms * self._kernel_w * self._kernel_h
