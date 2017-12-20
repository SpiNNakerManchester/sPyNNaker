from spinn_front_end_common.utilities import globals_variables
from pacman.model.graphs.common.slice import Slice
import numpy
import pytest
import functools
from spynnaker.pyNN.utilities.spynnaker_failed_state \
    import SpynnakerFailedState
from spynnaker.pyNN.models.neural_projections.connectors \
    import FixedNumberPreConnector, FixedNumberPostConnector, \
    FixedProbabilityConnector


class MockPopulation(object):

    def __init__(self, size, label):
        self._size = size
        self._label = label

    @property
    def size(self):
        return self._size

    @property
    def label(self):
        return self.label

    def __repr__(self):
        return "Population {}".format(self._label)


class MockRNG(object):

    def next(self, n):
        return numpy.random.uniform(size=n)


class MockSimulator(object):

    def is_a_pynn_random(self, values):
        return isinstance(values, MockRNG)

    def get_pynn_NumpyRNG(self):
        return MockRNG()


@pytest.fixture(scope="module", params=[10, 100])
def n_pre(request):
    return request.param


@pytest.fixture(scope="module", params=[10, 100])
def n_post(request):
    return request.param


@pytest.fixture(scope="module", params=[10])
def n_in_slice(request):
    return request.param


@pytest.fixture(
    scope="module",
    params=[
        functools.partial(FixedNumberPreConnector, 1),
        functools.partial(FixedNumberPostConnector, 1),
        functools.partial(FixedNumberPreConnector, 2),
        functools.partial(FixedNumberPostConnector, 2),
        functools.partial(FixedNumberPreConnector, 5, with_replacement=True),
        functools.partial(FixedNumberPostConnector, 5, with_replacement=True),
        functools.partial(FixedNumberPreConnector, 20, with_replacement=True),
        functools.partial(FixedNumberPostConnector, 20, with_replacement=True),
        functools.partial(FixedProbabilityConnector, 0.1),
        functools.partial(FixedProbabilityConnector, 0.5)],
    ids=[
        "FixedNumberPreConnector1-",
        "FixedNumberPostConnector1-",
        "FixedNumberPreConnector2-",
        "FixedNumberPreConnector2-",
        "FixedNumberPreConnector5Replace-",
        "FixedNumberPreConnector5Replace-",
        "FixedNumberPreConnector20Replace-",
        "FixedNumberPreConnector20Replace-",
        "FixedProbabilityConnector0.1-",
        "FixedProbabilityConnector0.5-"]
    )
def create_connector(request):
    return request.param


@pytest.fixture(scope="module", params=[5])
def weight(request):
    return request.param


@pytest.fixture(scope="module", params=[5])
def delay(request):
    return request.param


def test_connectors(
        n_pre, n_post, n_in_slice, create_connector, weight, delay):

    simulator = MockSimulator()
    globals_variables.set_failed_state(SpynnakerFailedState())
    globals_variables.set_simulator(simulator)

    max_target = 0
    max_source = 0
    for seed in range(1000):
        numpy.random.seed(seed)
        connector = create_connector()
        connector.set_projection_information(
            pre_population=MockPopulation(n_pre, "Pre"),
            post_population=MockPopulation(n_post, "Post"),
            rng=None, machine_time_step=1000)
        connector.set_weights_and_delays(weight, delay)

        pre_slices = [
            Slice(i, i + n_in_slice - 1) for i in range(0, n_pre, n_in_slice)]
        post_slices = [
            Slice(i, i + n_in_slice - 1) for i in range(0, n_post, n_in_slice)]
        pre_slice_index = 0
        post_slice_index = 0
        pre_vertex_slice = pre_slices[pre_slice_index]
        post_vertex_slice = post_slices[post_slice_index]
        synapse_type = 0
        pre_slice = pre_slices[pre_slice_index]
        post_slice = post_slices[post_slice_index]
        pre_range = numpy.arange(pre_slice.lo_atom, pre_slice.hi_atom + 2)
        post_range = numpy.arange(post_slice.lo_atom, post_slice.hi_atom + 2)

        max_delay = connector.get_delay_maximum()
        max_weight = connector.get_weight_maximum(
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice)
        max_row_length = connector.get_n_connections_from_pre_vertex_maximum(
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice)
        max_col_length = connector.get_n_connections_to_post_vertex_maximum(
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice)
        synaptic_block = connector.create_synaptic_block(
            pre_slices, pre_slice_index, post_slices, post_slice_index,
            pre_vertex_slice, post_vertex_slice, synapse_type)
        source_histogram = numpy.histogram(
            synaptic_block["source"], pre_range)[0]
        target_histogram = numpy.histogram(
            synaptic_block["target"], post_range)[0]
        matrix_max_weight = (
            max(synaptic_block["weight"]) if len(synaptic_block) > 0 else 0)
        matrix_max_delay = (
            max(synaptic_block["delay"]) if len(synaptic_block) > 0 else 0)

        max_source = max((max(source_histogram), max_source))
        max_target = max((max(target_histogram), max_target))

        try:
            assert max(source_histogram) <= max_row_length
            assert max(target_histogram) <= max_col_length
            assert matrix_max_weight <= max_weight
            assert matrix_max_delay <= max_delay
        except Exception:
            print connector.__class__.__name__
            print max_row_length, max(source_histogram), source_histogram
            print max_col_length, max(target_histogram), target_histogram
            print max_weight, matrix_max_weight, synaptic_block["weight"]
            print max_delay, matrix_max_delay, synaptic_block["delay"]
            raise
    print (connector.__class__.__name__, max_row_length, max_source,
           max_col_length, max_target)
