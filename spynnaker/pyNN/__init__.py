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

"""
The :py:mod:`spynnaker.pyNN` package contains the front end specifications
and implementation for the PyNN High-level API
(https://neuralensemble.org/trac/PyNN).

This package contains the profile of that code for PyNN 0.9.
"""

# common imports
import logging
import numpy as __numpy
from pyNN import common as pynn_common
from pyNN.common import control as _pynn_control
from pyNN.recording import get_io
from pyNN.random import NumpyRNG
from pyNN.space import (
    Space, Line, Grid2D, Grid3D, Cuboid, Sphere, RandomStructure)
from pyNN.space import distance as _pynn_distance

from spinn_utilities.exceptions import SimulatorNotSetupException
from spinn_utilities.log import FormatAdapter
from spinn_utilities.helpful_functions import is_singleton
from spinn_front_end_common.utilities.exceptions import (
    ConfigurationException)

from spynnaker.pyNN.random_distribution import RandomDistribution
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel

# connections
# noinspection PyUnresolvedReferences
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

# big stuff
from spynnaker.pyNN.spinnaker import SpiNNaker

from spynnaker._version import __version__  # NOQA
from spynnaker._version import __version_name__  # NOQA
from spynnaker._version import __version_month__  # NOQA
from spynnaker._version import __version_year__  # NOQA


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
    'reset', 'set_number_of_neurons_per_core',
    'Projection',
    'get_current_time', 'create', 'connect', 'get_time_step', 'get_min_delay',
    'get_max_delay', 'initialize', 'list_standard_models', 'name',
    'record', 'record_v', 'record_gsyn', "get_machine"]

# Dynamically-extracted operations from PyNN
__pynn = {}
# Cache of the simulator created by setup
__simulator = None


# Patch the bugs in the PyNN documentation... Ugh!
def distance(src_cell, tgt_cell, mask=None, scale_factor=1.0, offset=0.0,
             periodic_boundaries=None):
    """
    Return the Euclidean distance between two cells.

    :param src_cell: Measure from this cell
    :param tgt_cell: To this cell
    :param ~numpy.ndarray mask:
        allows only certain dimensions to be considered, e.g.:

        * to ignore the z-dimension, use ``mask=array([0,1])``
        * to ignore y, ``mask=array([0,2])``
        * to just consider z-distance, ``mask=array([2])``
    :param float scale_factor:
        allows for different units in the pre- and post-position
        (the post-synaptic position is multiplied by this quantity).
    :param float offset:
    :param periodic_boundaries:
    """
    return _pynn_distance(
        src_cell, tgt_cell, mask, scale_factor, offset, periodic_boundaries)


def setup(timestep=_pynn_control.DEFAULT_TIMESTEP,
          min_delay=_pynn_control.DEFAULT_MIN_DELAY,
          max_delay=None,
          database_socket_addresses=None, time_scale_factor=None,
          n_chips_required=None, n_boards_required=None, **extra_params):
    """
    The main method needed to be called to make the PyNN 0.8 setup.
    Needs to be called before any other function

    :param timestep:
        the time step of the simulations in microseconds;
        if `None`, the configuration value is used
    :type timestep: float or None
    :param min_delay: the minimum delay of the simulation
    :type min_delay: float or str
    :param max_delay: Ignored and logs a warning if provided
    :type max_delay: float or str or None
    :param database_socket_addresses: the sockets used by external devices
        for the database notification protocol
    :type database_socket_addresses:
        iterable(~spinn_utilities.socket_address.SocketAddress)
    :param time_scale_factor: multiplicative factor to the machine time step
        (does not affect the neuron models accuracy)
    :type time_scale_factor: int or None
    :param n_chips_required:
        Deprecated! Use n_boards_required instead.
        Must be `None` if n_boards_required specified.
    :type n_chips_required: int or None
    :param n_boards_required:
        if you need to be allocated a machine (for spalloc) before building
        your graph, then fill this in with a general idea of the number of
        boards you need so that the spalloc system can allocate you a machine
        big enough for your needs.
    :type n_boards_required: int or None
    :param extra_params: other keyword arguments used to configure PyNN
    :return: MPI rank (always 0 on SpiNNaker)
    :rtype: int
    :raises \
        ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
        if both ``n_chips_required`` and ``n_boards_required`` are used.
    """
    # pylint: disable=global-statement
    global __simulator
    # Check for "auto" values
    if timestep == "auto":
        timestep = SPYNNAKER_AUTO_TIMESTEP
    if min_delay == "auto":
        min_delay = timestep
    if max_delay:
        logger.warning(
            "max_delay is not supported by sPyNNaker so will be ignored")

    # pylint: disable=too-many-arguments
    # setup PyNN common stuff
    pynn_common.setup(timestep, min_delay, **extra_params)

    # create stuff simulator
    if SpynnakerDataView.is_setup():
        logger.warning("Calling setup a second time causes the previous "
                       "simulator to be stopped and cleared.")
        # if already exists, kill and rebuild
        try:
            __simulator.clear()
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error forcing previous simulation to clear")

    # create the main object for all stuff related software
    __simulator = SpiNNaker(
        time_scale_factor=time_scale_factor, timestep=timestep,
        min_delay=min_delay,
        n_chips_required=n_chips_required,
        n_boards_required=n_boards_required)
    # pylint: disable=protected-access
    external_devices._set_simulator(__simulator)

    # warn about kwargs arguments
    if extra_params:
        logger.warning("Extra params {} have been applied to the setup "
                       "command which we do not consider", extra_params)

    # get overloaded functions from PyNN in relation of our simulator object
    _create_overloaded_functions(__simulator)
    SpynnakerDataView.add_database_socket_addresses(database_socket_addresses)
    return rank()


def name():
    """
    Returns the name of the simulator.

    :rtype: str
    """
    return SpynnakerDataView.get_sim_name()


def Projection(
        presynaptic_population, postsynaptic_population,
        connector, synapse_type=None, source=None, receptor_type="excitatory",
        space=None, label=None):
    """
    Used to support PEP 8 spelling correctly.

    :param presynaptic_population: the source pop
    :type presynaptic_population:
        ~spynnaker.pyNN.models.populations.Population
    :param postsynaptic_population: the destination population
    :type postsynaptic_population:
        ~spynnaker.pyNN.models.populations.Population
    :param AbstractConnector connector: the connector type
    :param AbstractStaticSynapseDynamics synapse_type: the synapse type
    :param None source: Unsupported; must be ``None``
    :param str receptor_type: the receptor type
    :param space: the space object
    :type space: ~pyNN.space.Space or None
    :param label: the label
    :type label: str or None
    :return: a projection object for SpiNNaker
    :rtype: ~spynnaker.pyNN.models.projection.Projection
    """
    # pylint: disable=too-many-arguments
    return SpiNNakerProjection(
        pre_synaptic_population=presynaptic_population,
        post_synaptic_population=postsynaptic_population, connector=connector,
        synapse_type=synapse_type, source=source, receptor_type=receptor_type,
        space=space, label=label)


def _create_overloaded_functions(spinnaker_simulator):
    """
    Creates functions that the main PyNN interface supports
    (given from PyNN)

    :param spinnaker_simulator: the simulator object we use underneath
    """
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
    """
    Cleans up the SpiNNaker machine and software

    :param _: was named `compatible_output`, which we don't care about,
        so is a non-existent parameter
    """
    if SpynnakerDataView.is_shutdown():
        logger.warning("Second call to end ignored")
        return
    try:
        SpynnakerDataView.check_valid_simulator()
    except SimulatorNotSetupException:
        logger.exception("Calling end before setup makes no sense ignoring!")
        return
    for (population, variables, filename) in \
            __simulator.write_on_end:
        io = get_io(filename)
        population.write_data(io, variables)
    __simulator.write_on_end = []
    __simulator.stop()


def record_v(source, filename):
    """
    Deprecated method for getting voltage.
    This is not documented in the public facing API.

    .. deprecated:: 5.0

    :param source: the population / view / assembly to record
    :type source: ~spynnaker.pyNN.models.populations.Population or
        ~spynnaker.pyNN.models.populations.PopulationView
    :param str filename: the neo file to write to
    """
    logger.warning(
        "Using record_v is deprecated.  Use record('v') function instead")
    record(['v'], source, filename)


def record_gsyn(source, filename):
    """
    Deprecated method for getting both types of gsyn.
    This is not documented in the public facing API

    .. deprecated:: 5.0

    :param source: the population / view / assembly to record
    :type source: ~spynnaker.pyNN.models.populations.Population or
        ~spynnaker.pyNN.models.populations.PopulationView
    :param str filename: the neo file to write to
    """
    logger.warning(
        "Using record_gsyn is deprecated.  Use record('gsyn_exc') and/or"
        " record('gsyn_inh') function instead")
    record(['gsyn_exc', 'gsyn_inh'], source, filename)


def list_standard_models():
    """
    Return a list of all the StandardCellType classes available for this
    simulator.

    :rtype: list(str)
    """
    results = list()
    for (key, obj) in globals().items():
        if isinstance(obj, type) and issubclass(obj, AbstractPyNNModel):
            results.append(key)
    return results


def set_number_of_neurons_per_core(neuron_type, max_permitted):
    """
    Sets a ceiling on the number of neurons of a given model that can be
    placed on a single core.
    This can be overridden by the individual Population.

    The new value can be `None`, meaning that the maximum is the same as
    the number of atoms, an int, meaning all Populations of this model
    must have one dimension, or a tuple of n integers, meaning all
    Populations of this model must have n dimensions.
    If not all Populations of this model have the same number of
    dimensions, it is recommended to set this to `None` here and then
    set the maximum on each Population.

    :param type(AbstractPopulationVertex) neuron_type: neuron type
    :param int max_permitted: the number to set to
    """
    if isinstance(neuron_type, str):
        raise ConfigurationException(
            "set_number_of_neurons_per_core call now expects "
            "neuron_type as a class instead of as a str")
    max_neurons = max_permitted
    if is_singleton(max_permitted):
        max_neurons = (max_permitted, )
    for m in max_neurons:
        # Make sure an integer value is passed in here and warn if different
        m_int = int(m)
        if (m_int - m) != 0:
            logger.warning(
                "The number of neurons per core requested {} is not an "
                "integer; the value has been set to {}", m, m_int)

    SpynnakerDataView.set_number_of_neurons_per_dimension_per_core(
        neuron_type, max_neurons)


# These methods will defer to PyNN methods if a simulator exists


def connect(pre, post, weight=0.0, delay=None, receptor_type=None, p=1,
            rng=None):
    """
    Builds a projection.

    :param ~spynnaker.pyNN.models.populations.Population pre: source pop
    :param ~spynnaker.pyNN.models.populations.Population post: destination pop
    :param float weight: weight of the connections
    :param float delay: the delay of the connections
    :param str receptor_type: excitatory / inhibitory
    :param float p: probability
    :param ~pyNN.random.NumpyRNG rng: random number generator
    """
    # pylint: disable=too-many-arguments
    SpynnakerDataView.check_user_can_act()
    __pynn["connect"](pre, post, weight, delay, receptor_type, p, rng)


def create(cellclass, cellparams=None, n=1):
    """
    Builds a population with certain parameters.

    :param cellclass: population class
    :type cellclass: type or AbstractPyNNModel
    :param cellparams: population parameters.
    :param int n: number of neurons
    :rtype: ~spynnaker.pyNN.models.populations.Population
    """
    SpynnakerDataView.check_user_can_act()
    return __pynn["create"](cellclass, cellparams, n)


def NativeRNG(seed_value):
    """
    Fixes the random number generator's seed.

    :param seed_value:
    :type seed_value: int or list(int) or ~numpy.ndarray(int32)
    """
    __numpy.random.seed(seed_value)


def get_current_time():
    """
    Gets the time within the simulation.

    :return: returns the current time
    """
    SpynnakerDataView.check_user_can_act()
    return __pynn["get_current_time"]()


def get_min_delay():
    """
    The minimum allowed synaptic delay; delays will be clamped to be at
    least this.

    :return: returns the min delay of the simulation
    :rtype: int
    """
    SpynnakerDataView.check_user_can_act()
    return __pynn["get_min_delay"]()


def get_max_delay():
    """
    Part of the PyNN API but does not make sense for sPyNNaker as
    different Projection, Vertex splitter combination could have different
    delays they can support.

    Most likely value is timestep * 144

    :raises NotImplementedError: As there is no system wide max_delay
    """
    raise NotImplementedError(
        "sPyNNaker does not have a system wide max_delay")


def get_time_step():
    """
    The integration time step.

    :return: get the time step of the simulation (in ms)
    :rtype: float
    """
    SpynnakerDataView.check_user_can_act()
    return float(__pynn["get_time_step"]())


def initialize(cells, **initial_values):
    """
    Sets cells to be initialised to the given values.

    :param cells: the cells to change parameters on
    :type cells: ~spynnaker.pyNN.models.populations.Population or
        ~spynnaker.pyNN.models.populations.PopulationView
    :param initial_values: the parameters and their values to change
    """
    SpynnakerDataView.check_user_can_act()
    pynn_common.initialize(cells, **initial_values)


def num_processes():
    """
    The number of MPI processes.

    .. note::
        Always 1 on SpiNNaker, which doesn't use MPI.

    :return: the number of MPI processes
    :rtype: int
    """
    SpynnakerDataView.check_user_can_act()
    return __pynn["num_processes"]()


def rank():
    """
    The MPI rank of the current node.

    .. note::
        Always 0 on SpiNNaker, which doesn't use MPI.

    :return: MPI rank
    :rtype: int
    """
    SpynnakerDataView.check_user_can_act()
    return __pynn["rank"]()


def record(variables, source, filename, sampling_interval=None,
           annotations=None):
    """
    Sets variables to be recorded.

    :param variables: may be either a single variable name or a list of
        variable names. For a given `celltype` class, `celltype.recordable`
        contains a list of variables that can be recorded for that `celltype`.
    :type variables: str or list(str)
    :param source: where to record from
    :type source: ~spynnaker.pyNN.models.populations.Population or
        ~spynnaker.pyNN.models.populations.PopulationView
    :param str filename: file name to write data to
    :param sampling_interval:
        how often to sample the recording, not ignored so far
    :param annotations: the annotations to data writers
    :type annotations: dict(str, ...)
    :return: neo object
    :rtype: ~neo.core.Block
    """
    SpynnakerDataView.check_user_can_act()
    return __pynn["record"](variables, source, filename, sampling_interval,
                            annotations)


def reset(annotations=None):
    """
    Resets the simulation to t = 0.

    :param annotations: the annotations to the data objects
    :type annotations: dict(str, ...)
    """
    if annotations is None:
        annotations = {}
    SpynnakerDataView.check_user_can_act()
    __pynn["reset"](annotations)


def run(simtime, callbacks=None):
    """
    The run() function advances the simulation for a given number of
    milliseconds.

    :param float simtime: time to run for (in milliseconds)
    :param callbacks: callbacks to run
    :return: the actual simulation time that the simulation stopped at
    :rtype: float
    """
    SpynnakerDataView.check_user_can_act()
    return __pynn["run"](simtime, callbacks=callbacks)


# left here because needs to be done, and no better place to put it
# (ABS don't like it, but will put up with it)
run_for = run


def run_until(tstop):
    """
    Run until a (simulation) time period has completed.

    :param float tstop: the time to stop at (in milliseconds)
    :return: the actual simulation time that the simulation stopped at
    :rtype: float
    """
    SpynnakerDataView.check_user_can_act()
    return __pynn["run_until"](tstop)


def get_machine():
    """
    Get the SpiNNaker machine in use.

    :return: the machine object
    :rtype: ~spinn_machine.Machine
    """
    SpynnakerDataView.check_user_can_act()
    return SpynnakerDataView.get_machine()
