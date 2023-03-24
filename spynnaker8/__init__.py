# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The :py:mod:`spynnaker.pyNN` package contains the front end specifications
and implementation for the PyNN High-level API
(http://neuralensemble.org/trac/PyNN).

This package contains the profile of that code for PyNN 0.9
"""
# common imports
import traceback
import logging
from pyNN import common as pynn_common
from pyNN.common import control as _pynn_control
from pyNN.random import NumpyRNG
from pyNN.space import (
    Space, Line, Grid2D, Grid3D, Cuboid, Sphere, RandomStructure)
from spinn_utilities.log import FormatAdapter

# connections
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.neural_projections.connectors import (
    AllToAllConnector, ArrayConnector, CSAConnector,
    DistanceDependentProbabilityConnector, FixedNumberPostConnector,
    FixedNumberPreConnector, FixedProbabilityConnector,
    FromFileConnector, FromListConnector, IndexBasedProbabilityConnector,
    KernelConnector, MultapseConnector as FixedTotalNumberConnector,
    OneToOneConnector, SmallWorldConnector, ConvolutionConnector,
    PoolDenseConnector)

# synapse structures
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic as StaticSynapse)

# plastic stuff
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsSTDP as
    STDPMechanism, SynapseDynamicsStructuralStatic as
    StructuralMechanismStatic, SynapseDynamicsStructuralSTDP as
    StructuralMechanismSTDP)
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditive as
    AdditiveWeightDependence, WeightDependenceMultiplicative as
    MultiplicativeWeightDependence)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikePair as
    SpikePairRule)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .partner_selection import (
        LastNeuronSelection, RandomSelection)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .formation import (
        DistanceDependentFormation)
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .elimination import (
        RandomByWeightElimination)

# local-only synapses
from spynnaker.pyNN.models.neuron.local_only import (
    LocalOnlyConvolution as Convolution,
    LocalOnlyPoolDense as PoolDense)

# neuron stuff
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.if_cond_exp_base import (
    IFCondExpBase as IF_cond_exp)
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.if_curr_exp_base import (
    IFCurrExpBase as IF_curr_exp)
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.if_curr_alpha import (
    IFCurrAlpha as IF_curr_alpha)
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.if_curr_delta import (
    IFCurrDelta as IF_curr_delta)
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.izk_curr_exp_base import (
    IzkCurrExpBase as Izhikevich)
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.spike_source.spike_source_array import (
    SpikeSourceArray)
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.spike_source.spike_source_poisson import (
    SpikeSourcePoisson)

# pops
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.populations import (
    Assembly, Population, PopulationView)

# projection
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.projection import Projection as SpiNNakerProjection

# current sources
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.current_sources import (
    DCSource, ACSource, StepCurrentSource, NoisyCurrentSource)

from spynnaker.pyNN import external_devices
from spynnaker.pyNN import extra_models

from spynnaker.pyNN.utilities.utility_calls import moved_in_v7
from spynnaker.pyNN.setup_pynn import setup_pynn
import spynnaker.pyNN as sim

#: The timestep to use of "auto" is specified as a timestep
SPYNNAKER_AUTO_TIMESTEP = 1.0

logger = FormatAdapter(logging.getLogger(__name__))

__all__ = [
    # PyNN imports
    'Cuboid', 'distance', 'Grid2D', 'Grid3D', 'Line', 'NumpyRNG',
    'RandomDistribution', 'RandomStructure', 'Space', 'Sphere',

    # connections
    'AllToAllConnector', 'ArrayConnector', 'CSAConnector',
    'DistanceDependentProbabilityConnector', 'FixedNumberPostConnector',
    'FixedNumberPreConnector', 'FixedProbabilityConnector',
    'FromFileConnector', 'FromListConnector', 'IndexBasedProbabilityConnector',
    'FixedTotalNumberConnector', 'KernelConnector', 'OneToOneConnector',
    'SmallWorldConnector', 'ConvolutionConnector', 'PoolDenseConnector',
    # Local-only
    'Convolution', 'PoolDense',
    # synapse structures
    'StaticSynapse',
    # plastic stuff
    'STDPMechanism', 'AdditiveWeightDependence',
    'MultiplicativeWeightDependence', 'SpikePairRule',
    # Structural plasticity by Petrut Bogdan
    'StructuralMechanismStatic', 'StructuralMechanismSTDP',
    'LastNeuronSelection', 'RandomSelection',
    'DistanceDependentFormation', 'RandomByWeightElimination',
    # neuron stuff
    'IF_cond_exp', 'IF_curr_exp', "IF_curr_alpha", "IF_curr_delta",
    'Izhikevich', 'SpikeSourceArray', 'SpikeSourcePoisson',
    # pops
    'Assembly', 'Population', 'PopulationView',
    # projection
    'SpiNNakerProjection',
    # External devices and extra models
    'external_devices', 'extra_models',
    # CurrentSources
    'DCSource', 'ACSource', 'StepCurrentSource', 'NoisyCurrentSource',
    # Stuff that we define
    'end', 'setup', 'run', 'run_until', 'run_for', 'num_processes', 'rank',
    'reset', 'set_number_of_neurons_per_core', 'Projection',
    'get_current_time', 'create', 'connect', 'get_time_step', 'get_min_delay',
    'initialize', 'list_standard_models', 'name',  'record', 'get_machine']

# Dynamically-extracted operations from PyNN
__pynn = {}


def is_pynn_call():
    tr = traceback.extract_stack()
    for frame_summary in tr:
        if 'pyNN' in frame_summary.filename:
            return True
    return False


def use_spynnaker_pynn():
    moved_in_v7("spynnaker8", "pyNN.spinnaker which points to spynnaker.pyNN")


if is_pynn_call():
    setup_pynn()
    raise SpynnakerException(
        "Pynn needed to be setup. Now done. Please try again")
else:
    use_spynnaker_pynn()


class RandomDistribution(sim.RandomDistribution):
    """ Class which defines a next(n) method which returns an array of ``n``\
        random numbers from a given distribution.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """


def distance(src, tgt, mask=None, scale_factor=1.0, offset=0.0,
             periodic_boundaries=None):
    """ Return the Euclidian distance between two cells.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.distance(
        src, tgt, mask, scale_factor, offset, periodic_boundaries)


def setup(timestep=_pynn_control.DEFAULT_TIMESTEP,
          min_delay=_pynn_control.DEFAULT_MIN_DELAY,
          max_delay=None,
          database_socket_addresses=None, time_scale_factor=None,
          n_chips_required=None, n_boards_required=None, **extra_params):
    # pylint: disable=unused-argument
    """ The main method needed to be called to make the PyNN 0.8 setup. Needs\
        to be called before any other function

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.setup(
        timestep, min_delay, max_delay,
        database_socket_addresses, time_scale_factor, n_chips_required,
        n_boards_required, **extra_params)


def name():
    """ Returns the name of the simulator

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.name()


def Projection(
        presynaptic_population, postsynaptic_population,
        connector, synapse_type=None, source=None, receptor_type="excitatory",
        space=None, label=None):
    """ Used to support PEP 8 spelling correctly

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    # pylint: disable=too-many-arguments
    use_spynnaker_pynn()
    return sim.Projection(
        presynaptic_population, postsynaptic_population, connector,
        synapse_type, source, receptor_type, space, label)


def _create_overloaded_functions(spinnaker_simulator):
    """ Creates functions that the main PyNN interface supports\
        (given from PyNN)

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()

    # overload the failed ones with now valid ones, now that we're in setup
    # phase.
    __pynn["run"], __pynn["run_until"] = pynn_common.build_run(
        spinnaker_simulator)

    __pynn["get_current_time"], __pynn["get_time_step"], \
        __pynn["get_min_delay"], __pynn["get_max_delay"], \
        __pynn["num_processes"], __pynn["rank"] = \
        pynn_common.build_state_queries(spinnaker_simulator)

    __pynn["reset"] = pynn_common.build_reset(spinnaker_simulator)
    __pynn["create"] = pynn_common.build_create(Population)

    __pynn["connect"] = pynn_common.build_connect(
        Projection, FixedProbabilityConnector, StaticSynapse)

    __pynn["record"] = pynn_common.build_record(spinnaker_simulator)


def end(_=True):
    """ Cleans up the SpiNNaker machine and software

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    sim.end()


def list_standard_models():
    """ Return a list of all the StandardCellType classes available for this\
        simulator.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.list_standard_models()


def set_number_of_neurons_per_core(neuron_type, max_permitted):
    """ Sets a ceiling on the number of neurons of a given type that can be\
        placed on a single core.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    sim.set_number_of_neurons_per_core(neuron_type, max_permitted)


# These methods will defer to PyNN methods if a simulator exists


def connect(pre, post, weight=0.0, delay=None, receptor_type=None, p=1,
            rng=None):
    """ Builds a projection

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    sim.connect(pre, post, weight, delay, receptor_type, p, rng)


def create(cellclass, cellparams=None, n=1):
    """ Builds a population with certain params

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.create(cellclass, cellparams, n)


def NativeRNG(seed_value):
    """ Fixes the random number generator's seed

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    sim.NativeRNG(seed_value)


def get_current_time():
    """ Gets the time within the simulation

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.get_current_time()


def get_min_delay():
    """ The minimum allowed synaptic delay; delays will be clamped to be at\
        least this.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.get_min_delay()


def get_time_step():
    """ The integration time step

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.get_time_step()


def initialize(cells, **initial_values):
    """ Sets cells to be initialised to the given values

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    sim.initialize(cells, **initial_values)


def num_processes():
    """ The number of MPI processes.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.num_processes()


def rank():
    """ The MPI rank of the current node.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.rank()


def record(variables, source, filename, sampling_interval=None,
           annotations=None):
    """ Sets variables to be recorded.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    sim.record(variables, source, filename, sampling_interval, annotations)


def reset(annotations=None):
    """ Resets the simulation to t = 0

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    sim.reset(annotations)


def run(simtime, callbacks=None):
    """ The run() function advances the simulation for a given number of \
        milliseconds, e.g.:

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.run(simtime, callbacks)


# left here because needs to be done, and no better place to put it
# (ABS don't like it, but will put up with it)
run_for = run


def run_until(tstop):
    """ Run until a (simulation) time period has completed.

    .. deprecated:: 7.0
        Use
        :py:class:`spynnaker.pyNN` instead.
    """
    use_spynnaker_pynn()
    return sim.run_until(tstop)


def get_machine():
    """ Get the SpiNNaker machine in use.

    """
    use_spynnaker_pynn()
    return sim.get_machine()
