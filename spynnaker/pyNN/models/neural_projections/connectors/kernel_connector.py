import numpy
from pyNN.random import RandomDistribution
from .abstract_connector import AbstractConnector
from pacman.model.decorators.overrides import overrides
from data_specification.enums.data_type import DataType
from .abstract_generate_connector_on_machine \
    import AbstractGenerateConnectorOnMachine, ConnectorIDs, PARAM_TYPE_KERNEL

HEIGHT, WIDTH = 0, 1
N_KERNEL_PARAMS = 8


class ConvolutionKernel(numpy.ndarray):
    pass


def shape2word(sw, sh):
    return (((numpy.uint32(sw) & 0xFFFF) << 16) |
            (numpy.uint32(sh) & 0xFFFF))


class KernelConnector(AbstractGenerateConnectorOnMachine):
    """
    Where the pre- and postsynaptic populations are thought-of as a 2D array.\
    Connect every post(row, col) neuron to many pre(row, col, kernel) through\
    the same set of weights and delays.
    """

    def __init__(
            self, shape_pre, shape_post, shape_kernel,
            shape_common=None, pre_sample_steps=None, pre_start_coords=None,
            post_sample_steps=None, post_start_coords=None,
            safe=True, space=None, verbose=False):
        """
        :param shape_common:\
            2D shape of common coordinate system (for both pre and post, \
            usually the input image sizes)
        :param shape_pre:\
            2D shape of the pre population (rows/height, cols/width, usually \
            the input image shape)
        :param shape_post:\
            2D shape of the post population (rows/height, cols/width)
        :param shape_kernel:\
            2D shape of the kernel (rows/height, cols/width)
        :param pre/post_sample_steps:\
            Sampling steps/jumps for post pop <=> (startX, endX, _stepX_)
            None or 2-item array
        :param pre/post_start_coords:\
            Starting row/col for sampling <=> (_startX_, endX, stepX)
            None or 2-item array
        """
        super(KernelConnector, self).__init__(self, safe=safe, verbose=verbose)

        self._kernel_w = shape_kernel[WIDTH]
        self._kernel_h = shape_kernel[HEIGHT]
        self._hlf_k_w = shape_kernel[WIDTH] // 2
        self._hlf_k_h = shape_kernel[HEIGHT] // 2

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

        self._krn_weights = self.get_kernel_vals(self._weights)
        self._krn_delays = self.get_kernel_vals(self._delays)

        self._shape_common = \
            shape_pre if shape_common is None else shape_common
        self._shape_pre = shape_pre
        self._shape_post = shape_post

        self._pre_in_range = {}
        self._all_post = {}
        self._all_pre_in_range = {}
        self._all_pre_in_range_delays = {}
        self._all_pre_in_range_weights = {}
        self._post_as_pre = {}
        self._num_conns = {}

    def pre_in_range(self, pre_vertex_slice, post_vertex_slice):
        if (str(pre_vertex_slice) not in self._pre_in_range and
                str(post_vertex_slice) not in
                self._pre_in_range[str(pre_vertex_slice)]):
            self.compute_statistics(pre_vertex_slice, post_vertex_slice)
        return self._pre_in_range[pre_vertex_slice][post_vertex_slice]

    def to_post_coords(self, post_vertex_slice):
        post = numpy.arange(
            post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1)

        return post // self._shape_post[WIDTH], post % self._shape_post[WIDTH]

    def map_to_pre_coords(self, (post_r, post_c)):
        return (self._post_start_h + post_r * self._post_step_h,
                self._post_start_w + post_c * self._post_step_w)

    def post_as_pre(self, post_vertex_slice):
        if str(post_vertex_slice) not in self._post_as_pre:
            self._post_as_pre[str(post_vertex_slice)] = self.map_to_pre_coords(
                self.to_post_coords(post_vertex_slice))
        return self._post_as_pre[str(post_vertex_slice)]

    def pre_as_post(self, coords):
        r = ((coords[HEIGHT] - self._pre_start_h - 1) // self._pre_step_h) + 1
        c = ((coords[WIDTH] - self._pre_start_w - 1) // self._pre_step_w) + 1
        return (r, c)

    def get_kernel_vals(self, vals):
        krn_size = self._kernel_h * self._kernel_w
        krn_shape = (self._kernel_h, self._kernel_w)
        if isinstance(self._delays, RandomDistribution):
            return numpy.array(self._delays.next(krn_size)).reshape(krn_shape)
        elif numpy.isscalar(self._delays):
            return self._delays*numpy.ones(krn_shape)
        elif ((isinstance(vals, numpy.ndarray) or
                isinstance(vals, ConvolutionKernel)) and
                vals.shape[HEIGHT] == self._kernel_h and
                vals.shape[WIDTH] == self._kernel_w):
            return vals.view(ConvolutionKernel)
        raise Exception("Error generating KernelConnector values")

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

    def compute_statistics(self, pre_vertex_slice, post_vertex_slice):
        print("In kernel connector, compute_statistics")
        prevs = str(pre_vertex_slice)
        postvs = str(post_vertex_slice)
        self.init_pre_entries(prevs)

        post_as_pre_r, post_as_pre_c = self.post_as_pre(post_vertex_slice)
        coords = {}
        hh, hw = self._hlf_k_h, self._hlf_k_w
        unique_pre_ids = []
        all_pre_ids = []
        all_post_ids = []
        all_delays = []
        all_weights = []
        count = 0
        post_lo = post_vertex_slice.lo_atom

        for pre_idx in range(
                pre_vertex_slice.lo_atom, pre_vertex_slice.hi_atom + 1):
            pre_r = pre_idx // self._shape_pre[WIDTH]
            pre_c = pre_idx % self._shape_pre[WIDTH]
            coords[pre_idx] = []
            for post_idx in range(
                    post_vertex_slice.lo_atom, post_vertex_slice.hi_atom + 1):

                # convert to common coord system
                r = post_as_pre_r[post_idx - post_lo]
                c = post_as_pre_c[post_idx - post_lo]
                if r < 0 or r >= self._shape_common[HEIGHT] or \
                   c < 0 or c >= self._shape_common[WIDTH]:
                    continue

                r, c = self.pre_as_post((r, c))

                fr_r = max(0, r - hh)
                to_r = min(r + hh + 1, self._shape_pre[HEIGHT])
                fr_c = max(0, c - hw)
                to_c = min(c + hw + 1, self._shape_pre[WIDTH])

                if fr_r <= pre_r and pre_r < to_r and \
                   fr_c <= pre_c and pre_c < to_c:

                    if post_idx in coords[pre_idx]:
                        continue

                    coords[pre_idx].append(post_idx)

                    dr = r - pre_r
                    kr = hh - dr
                    dc = c - pre_c
                    kc = hw - dc

                    w = self._krn_weights[kr, kc]
                    d = self._krn_delays[kr, kc]

                    count += 1

                    all_pre_ids.append(pre_idx)
                    all_post_ids.append(post_idx)
                    all_delays.append(d)
                    all_weights.append(w)

        self._pre_in_range[prevs][postvs] = numpy.array(unique_pre_ids)
        self._num_conns[prevs][postvs] = count
        # print("\n\n%s -> %s = %d conns\n"%(prevs, postvs, count))
        self._all_post[prevs][postvs] = numpy.array(
            all_post_ids, dtype='uint32')
        self._all_pre_in_range[prevs][postvs] = numpy.array(
            all_pre_ids, dtype='uint32')
        self._all_pre_in_range_delays[prevs][postvs] = numpy.array(
            all_delays)
        self._all_pre_in_range_weights[prevs][postvs] = numpy.array(
            all_weights)

        return self._pre_in_range[prevs][postvs]

    def min_max_coords(self, pre_r, pre_c):
        hh, hw = self._hlf_k_h, self._hlf_k_w
        return (numpy.array([pre_r[0] - hh, pre_c[0] - hw]),
                numpy.array([pre_r[-1] + hh, pre_c[-1] + hw]))

    def to_pre_indices(self, pre_r, pre_c):
        return pre_r * self._shape_pre[WIDTH] + pre_c

    def gen_key(self, pre_vertex_slice, post_vertex_slice):
        return '%s->%s' % (pre_vertex_slice, post_vertex_slice)

    def get_num_conns(self, pre_vertex_slice, post_vertex_slice):
        if (str(pre_vertex_slice) not in self._num_conns or
                str(post_vertex_slice) not in
                self._num_conns[str(pre_vertex_slice)]):
            self.compute_statistics(pre_vertex_slice, post_vertex_slice)

        return self._num_conns[str(pre_vertex_slice)][str(post_vertex_slice)]

    def get_all_delays(self, pre_vertex_slice, post_vertex_slice):
        if (str(pre_vertex_slice) not in self._all_pre_in_range_delays or
                str(post_vertex_slice) not in
                self._all_pre_in_range_delays[str(pre_vertex_slice)]):
            self.compute_statistics(pre_vertex_slice, post_vertex_slice)

        return self._all_pre_in_range_delays[
            str(pre_vertex_slice)][str(post_vertex_slice)]

    def get_delay_maximum(self):
        # way over-estimated
        n_conns = (
            self._n_pre_neurons * self._n_post_neurons * self._kernel_w *
            self._kernel_h)
        return self._get_delay_maximum(self._delays, n_conns)

    def get_delay_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        slices = (slice(0, self._kernel_h), slice(0, self._kernel_w))
        return self._get_delay_variance(self._delays, slices)

    def get_n_connections_from_pre_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            min_delay=None, max_delay=None):
        # max outgoing from pre connections with min_delay <= delay <=
        # max_delay

        if isinstance(self._weights, ConvolutionKernel):
            if self._weights.size > pre_vertex_slice.n_atoms:
                return pre_vertex_slice.n_atoms
            elif self._weights.size > 255:
                return 255
            else:
                return (self._weights[self._weights != 0]).size

        return numpy.clip(self._kernel_h*self._kernel_w, 0, 255)

    def get_n_connections_to_post_vertex_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        if isinstance(self._weights, ConvolutionKernel):
            if self._weights.size > pre_vertex_slice.n_atoms:
                return pre_vertex_slice.n_atoms
            elif self._weights.size > 255:
                return 255
            else:
                return (self._weights[self._weights != 0]).size

        return numpy.clip(self._kernel_h * self._kernel_w, 0, 255)

    def get_weight_mean(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        if isinstance(self._weights, ConvolutionKernel):
            return numpy.mean(numpy.abs(self._weights[self._weights != 0]))

        slices = (slice(0, self._kernel_h), slice(0, self._kernel_w))
        return self._get_weight_mean(self._weights, slices)

    def get_weight_maximum(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        if isinstance(self._weights, ConvolutionKernel):
            return numpy.max(numpy.abs(self._weights[self._weights != 0]))

        slices = (slice(0, self._kernel_h), slice(0, self._kernel_w))
        n_conns = (
            self._n_pre_neurons * self._n_post_neurons * self._kernel_w *
            self._kernel_h)
        return self._get_weight_maximum(self._weights, n_conns, slices)

    def get_weight_variance(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice):

        if isinstance(self._weights, ConvolutionKernel):
            return numpy.var(numpy.abs(self._weights[self._weights != 0]))

        slices = (slice(0, self._kernel_h), slice(0, self._kernel_w))
        return self._get_weight_variance(self._weights, slices)

    def __repr__(self):
        return "KernelConnector"

    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        n_connections = self.get_num_conns(pre_vertex_slice, post_vertex_slice)

        syn_dtypes = AbstractConnector.NUMPY_SYNAPSES_DTYPE

        if n_connections <= 0:
            return numpy.zeros(0, dtype=syn_dtypes)

        prevs = str(pre_vertex_slice)
        postvs = str(post_vertex_slice)

        # 0 for exc, 1 for inh
        syn_type = numpy.array(
            self._all_pre_in_range_weights[prevs][postvs] < 0)
        block = numpy.zeros(n_connections, dtype=syn_dtypes)
        block["source"] = self._all_pre_in_range[prevs][postvs]
        block["target"] = self._all_post[prevs][postvs]
        block["weight"] = self._all_pre_in_range_weights[prevs][postvs]
        block["delay"] = self._all_pre_in_range_delays[prevs][postvs]
        block["synapse_type"] = syn_type.astype('uint8')
        return block

    @property
    def generate_on_machine(self):
        super_generate = super(KernelConnector, self).generate_on_machine

        # This connector can also cope with listed weights and delays
        return super_generate or (isinstance(self._delays, numpy.ndarray) and
                                  isinstance(self._weights, numpy.ndarray))

    @property
    def _kernel_properties(self):
        return [
            shape2word(self._shape_common[WIDTH], self._shape_common[HEIGHT]),
            shape2word(self._shape_pre[WIDTH], self._shape_pre[HEIGHT]),
            shape2word(self._shape_post[WIDTH], self._shape_post[HEIGHT]),
            shape2word(self._pre_start_w, self._pre_start_h),
            shape2word(self._post_start_w, self._post_start_h),
            shape2word(self._pre_step_w, self._pre_step_h),
            shape2word(self._post_step_w, self._post_step_h),
            shape2word(self._kernel_w, self._kernel_h)]

    @property
    def gen_delays_id(self):
        if isinstance(self._delays, numpy.ndarray):
            return PARAM_TYPE_KERNEL
        return super(KernelConnector, self).gen_delays_id

    @property
    def gen_delay_params_size_in_bytes(self):
        if isinstance(self._delays, numpy.ndarray):
            return (N_KERNEL_PARAMS + 1 + self._delays.size) * 4
        return super(KernelConnector, self).gen_delay_params_size_in_bytes()

    def gen_delay_params(self, pre_vertex_slice, post_vertex_slice):
        if isinstance(self._delays, numpy.ndarray):
            properties = self._kernel_properties
            properties.append(post_vertex_slice.lo_atom)
            data = numpy.array(properties, dtype="uint32")
            values = numpy.round(
                self._delays * float(DataType.S1615.scale)).astype("uint32")
            return numpy.concatenate(data, values)
        return super(KernelConnector, self).gen_delay_params(
            self, pre_vertex_slice, post_vertex_slice)

    @property
    def gen_weights_id(self):
        if isinstance(self._weights, numpy.ndarray):
            return PARAM_TYPE_KERNEL
        return super(KernelConnector, self).gen_weights_id

    @property
    def gen_weight_params_size_in_bytes(self):
        if isinstance(self._weights, numpy.ndarray):
            return (N_KERNEL_PARAMS + 1 + self._weights.size) * 4
        return super(KernelConnector, self).gen_weight_params_size_in_bytes()

    def gen_weights_params(self, pre_vertex_slice, post_vertex_slice):
        if isinstance(self._weights, numpy.ndarray):
            properties = self._kernel_properties
            properties.append(post_vertex_slice.lo_atom)
            data = numpy.array(properties, dtype="uint32")
            values = numpy.round(
                self._weights * float(DataType.S1615.scale)).astype("uint32")
            return numpy.concatenate(data, values)
        return super(KernelConnector, self).gen_weights_params(
            self, pre_vertex_slice, post_vertex_slice)

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
        return numpy.array(self._kernel_properties, dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return N_KERNEL_PARAMS * 4

    def get_max_num_connections(self, pre_slice, post_slice):
        return post_slice.n_atoms * self._kernel_w * self._kernel_h
