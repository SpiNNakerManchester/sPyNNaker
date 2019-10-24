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

# common imports
import numpy as __numpy
from six import iteritems

# pynn imports
from spynnaker.pyNN import (
    _pynn_control, get_io, NumpyRNG, _PynnRandomDistribution, Space, Line,
    Grid2D, Grid3D, Cuboid, Sphere, RandomStructure, _pynn_distance,
    pynn_common)

# fec imports
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.failed_state import FAILED_STATE_MSG

from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel

# connections
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.all_to_all_connector import \
    AllToAllConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.array_connector import ArrayConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.csa_connector import CSAConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.\
    distance_dependent_probability_connector \
    import DistanceDependentProbabilityConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.fixed_number_post_connector import \
    FixedNumberPostConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.fixed_number_pre_connector import \
    FixedNumberPreConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.fixed_probability_connector import \
    FixedProbabilityConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.from_file_connector import \
    FromFileConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.from_list_connector import \
    FromListConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.index_based_probability_connector import\
    IndexBasedProbabilityConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.multapse_connector import \
    MultapseConnector as FixedTotalNumberConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.one_to_one_connector import \
    OneToOneConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.small_world_connector import \
    SmallWorldConnector
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.connectors.kernel_connector import \
    KernelConnector

# synapse structures
from spynnaker.pyNN.models.synapse_dynamics.synapse_dynamics_static import \
    SynapseDynamicsStatic as StaticSynapse

# plastic stuff
from spynnaker.pyNN.models.synapse_dynamics.synapse_dynamics_stdp import \
    SynapseDynamicsSTDP as STDPMechanism
from spynnaker.pyNN.models.synapse_dynamics.\
    synapse_dynamics_structural_static import \
    SynapseDynamicsStructuralStatic as StructuralMechanismStatic
from spynnaker.pyNN.models.synapse_dynamics.synapse_dynamics_structural_stdp \
    import SynapseDynamicsStructuralSTDP as StructuralMechanismSTDP
from spynnaker.pyNN.models.synapse_dynamics.weight_dependence\
    .weight_dependence_additive import WeightDependenceAdditive as \
    AdditiveWeightDependence
from spynnaker.pyNN.models.synapse_dynamics.weight_dependence\
    .weight_dependence_multiplicative import \
    WeightDependenceMultiplicative as MultiplicativeWeightDependence
from spynnaker.pyNN.models.synapse_dynamics.timing_dependence\
    .timing_dependence_spike_pair import TimingDependenceSpikePair as \
    SpikePairRule
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .partner_selection import LastNeuronSelection
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .partner_selection import RandomSelection
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .formation import DistanceDependentFormation
from spynnaker.pyNN.models.neuron.structural_plasticity.synaptogenesis\
    .elimination import RandomByWeightElimination

# neuron stuff
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.if_cond_exp_base import \
    IFCondExpBase as IF_cond_exp
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.if_curr_exp_base import \
    IFCurrExpBase as IF_curr_exp
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.if_curr_alpha import \
    IFCurrAlpha as IF_curr_alpha
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.neuron.builds.izk_curr_exp_base import \
    IzkCurrExpBase as Izhikevich
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.spike_source.spike_source_array \
    import SpikeSourceArray
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.spike_source.spike_source_poisson \
    import SpikeSourcePoisson

# pops
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.populations.assembly import Assembly
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.populations.population import Population
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.populations.population_view import PopulationView

# projection
# noinspection PyUnresolvedReferences
from spynnaker.pyNN.models.projection import Projection as SpiNNakerProjection

from spynnaker.pyNN import external_devices
from spynnaker.pyNN import extra_models
from spynnaker.pyNN.utilities.version_util import pynn8_syntax

# big stuff
from spynnaker.pyNN.spinnaker import SpiNNaker
from spinn_utilities.log import FormatAdapter

from ._version import __version__  # NOQA
from ._version import __version_name__  # NOQA
from ._version import __version_month__  # NOQA
from ._version import __version_year__  # NOQA


import logging

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
    'FixedTotalNumberConnector', 'OneToOneConnector', 'SmallWorldConnector',
    'KernelConnector',
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
    'IF_cond_exp', 'IF_curr_exp', "IF_curr_alpha",
    'Izhikevich', 'SpikeSourceArray', 'SpikeSourcePoisson',
    # pops
    'Assembly', 'Population', 'PopulationView',
    # projection
    'SpiNNakerProjection',
    # External devices and extra models
    'external_devices', 'extra_models',
    # Stuff that we define
    'end', 'setup', 'run', 'run_until', 'run_for', 'num_processes', 'rank',
    'reset', 'set_number_of_neurons_per_core', 'get_projections_data',
    'Projection',
    'get_current_time', 'create', 'connect', 'get_time_step', 'get_min_delay',
    'get_max_delay', 'initialize', 'list_standard_models', 'name',
    'num_processes', 'record', 'record_v', 'record_gsyn',
    '__version__', '__version_name__', '__version_month__',
    '__version_year__'
    ]

# Dynamically-extracted operations from PyNN
__pynn = {}


class RandomDistribution(_PynnRandomDistribution):
    """ Class which defines a next(n) method which returns an array of ``n``\
        random numbers from a given distribution.

    :param distribution: the name of a random number distribution.
    :param parameters_pos: \
        parameters of the distribution, provided as a tuple. For the correct\
        ordering, see `random.available_distributions`.
    :param rng: the random number generator to use, if a specific one is\
        desired (e.g., to provide a seed). If present, should be a\
        :py:class:`NumpyRNG`,\
        :py:class:`GSLRNG` or\
        :py:class:`NativeRNG` object.
    :param parameters_named: \
        parameters of the distribution, provided as keyword arguments.

    Parameters may be provided either through ``parameters_pos`` or through\
    ``parameters_named``, but not both. All parameters must be provided, there\
    are no default values. Parameter names are, in general, as used in\
    Wikipedia.

    Examples::

        >>> rd = RandomDistribution('uniform', (-70, -50))
        >>> rd = RandomDistribution('normal', mu=0.5, sigma=0.1)
        >>> rng = NumpyRNG(seed=8658764)
        >>> rd = RandomDistribution('gamma', k=2.0, theta=5.0, rng=rng)

    .. list-table:: Available distributions
        :widths: auto
        :header-rows: 1

        * - Name
          - Parameters
          - Comments
        * - ``binomial``
          - ``n``, ``p``
          -
        * - ``gamma``
          - ``k``, ``theta``
          -
        * - ``exponential``
          - ``beta``
          -
        * - ``lognormal``
          - ``mu``, ``sigma``
          -
        * - ``normal``
          - ``mu``, ``sigma``
          -
        * - ``normal_clipped``
          - ``mu``, ``sigma``, ``low``, ``high``
          - Values outside (``low``, ``high``) are redrawn
        * - ``normal_clipped_to_boundary``
          - ``mu``, ``sigma``, ``low``, ``high``
          - Values below/above ``low``/``high`` are set to ``low``/``high``
        * - ``poisson``
          - ``lambda_``
          - Trailing underscore since ``lambda`` is a Python keyword
        * - ``uniform``
          - ``low``, ``high``
          -
        * - ``uniform_int``
          - ``low``, ``high``
          - Only generates integer values
        * - ``vonmises``
          - ``mu``, ``kappa``
          -
    """

    def __repr__(self):
        return self.__str__()


# Patch the bugs in the PyNN documentation... Ugh!
def distance(src, tgt, mask=None, scale_factor=1.0, offset=0.0,
             periodic_boundaries=None):
    """ Return the Euclidian distance between two cells.

    :param mask: allows only certain dimensions to be considered, e.g.:
        * to ignore the z-dimension, use ``mask=array([0,1])``
        * to ignore y, ``mask=array([0,2])``
        * to just consider z-distance, ``mask=array([2])``
    :param scale_factor: allows for different units in the pre- and post-\
        position (the post-synaptic position is multiplied by this quantity).
    """
    return _pynn_distance(
        src, tgt, mask, scale_factor, offset, periodic_boundaries)


def get_projections_data(projection_data):
    return globals_variables.get_simulator().get_projections_data(
        projection_data)


def setup(timestep=_pynn_control.DEFAULT_TIMESTEP,
          min_delay=_pynn_control.DEFAULT_MIN_DELAY,
          max_delay=_pynn_control.DEFAULT_MAX_DELAY,
          graph_label=None,
          database_socket_addresses=None, extra_algorithm_xml_paths=None,
          extra_mapping_inputs=None, extra_mapping_algorithms=None,
          extra_pre_run_algorithms=None, extra_post_run_algorithms=None,
          extra_load_algorithms=None, time_scale_factor=None,
          n_chips_required=None, n_boards_required=None, **extra_params):
    """ The main method needed to be called to make the PyNN 0.8 setup. Needs\
        to be called before any other function

    :param timestep: the time step of the simulations
    :param min_delay: the min delay of the simulation
    :param max_delay: the max delay of the simulation
    :param graph_label: the label for the graph
    :param database_socket_addresses: the sockets used by external devices\
        for the database notification protocol
    :param extra_algorithm_xml_paths: \
        list of paths to where other XML are located
    :param extra_mapping_inputs: other inputs used by the mapping process
    :param extra_mapping_algorithms: \
        other algorithms to be used by the mapping process
    :param extra_pre_run_algorithms: extra algorithms to use before a run
    :param extra_post_run_algorithms: extra algorithms to use after a run
    :param extra_load_algorithms: \
        extra algorithms to use within the loading phase
    :param time_scale_factor: multiplicative factor to the machine time step\
        (does not affect the neuron models accuracy)
    :param n_chips_required:\
        Deprecated! Use n_boards_required instead.
        Must be None if n_boards_required specified.
    :type n_chips_required: int or None
    :param n_boards_required:\
        if you need to be allocated a machine (for spalloc) before building\
        your graph, then fill this in with a general idea of the number of
        boards you need so that the spalloc system can allocate you a machine\
        big enough for your needs.
    :param extra_params: other stuff
    :return: rank thing
    :raises ConfigurationException if both n_chips_required and
        n_boards_required are used.
    """
    # pylint: disable=too-many-arguments, too-many-function-args
    if pynn8_syntax:
        # setup PyNN common stuff
        pynn_common.setup(timestep, min_delay, max_delay, **extra_params)
    else:
        # setup PyNN common stuff
        pynn_common.setup(timestep, min_delay, **extra_params)

    # create stuff simulator
    if globals_variables.has_simulator():
        # if already exists, kill and rebuild
        globals_variables.get_simulator().clear()

    # add default label if needed
    if graph_label is None:
        graph_label = "PyNN0.8_graph"

    # create the main object for all stuff related software
    SpiNNaker(
        database_socket_addresses=database_socket_addresses,
        extra_algorithm_xml_paths=extra_algorithm_xml_paths,
        extra_mapping_inputs=extra_mapping_inputs,
        extra_mapping_algorithms=extra_mapping_algorithms,
        extra_pre_run_algorithms=extra_pre_run_algorithms,
        extra_post_run_algorithms=extra_post_run_algorithms,
        extra_load_algorithms=extra_load_algorithms,
        time_scale_factor=time_scale_factor, timestep=timestep,
        min_delay=min_delay, max_delay=max_delay, graph_label=graph_label,
        n_chips_required=n_chips_required,
        n_boards_required=n_boards_required)

    # warn about kwargs arguments
    if extra_params:
        logger.warning("Extra params {} have been applied to the setup "
                       "command which we do not consider", extra_params)

    # get overloaded functions from PyNN in relation of our simulator object
    _create_overloaded_functions(globals_variables.get_simulator())

    return rank()


def name():
    """ Returns the name of the simulator

    :rtype:None
    """
    return globals_variables.get_simulator().name


def Projection(
        presynaptic_population, postsynaptic_population,
        connector, synapse_type=None, source=None, receptor_type="excitatory",
        space=None, label=None):
    """ Used to support PEP 8 spelling correctly

    :param presynaptic_population: the source pop
    :param postsynaptic_population: the dest pop
    :param connector: the connector type
    :param synapse_type: the synapse type
    :param source: the source
    :param receptor_type: the recpetor type
    :param space: the space object
    :param label: the label
    :return: a projection object for SpiNNaker
    """
    # pylint: disable=too-many-arguments
    return SpiNNakerProjection(
        pre_synaptic_population=presynaptic_population,
        post_synaptic_population=postsynaptic_population, connector=connector,
        synapse_type=synapse_type, source=source, receptor_type=receptor_type,
        space=space, label=label)


def _create_overloaded_functions(spinnaker_simulator):
    """ Creates functions that the main PyNN interface supports\
        (given from PyNN)

    :param spinnaker_simulator: the simulator object we use underneath
    :rtype: None
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
    """ Cleans up the SpiNNaker machine and software

    :param _: was named compatible_output, which we don't care about,\
        so is a non-existent parameter
    :rtype: None
    """
    for (population, variables, filename) in \
            globals_variables.get_simulator().write_on_end:
        io = get_io(filename)
        population.write_data(io, variables)
    globals_variables.get_simulator().write_on_end = []
    globals_variables.get_simulator().stop()


def record_v(source, filename):
    """ Deprecated method for getting voltage.\
        This is not documented in the public facing API.

    :param source: the population / view / assembly to record
    :param filename: the neo file to write to
    :rtype: None
    """
    logger.warning(
        "Using record_v is deprecated.  Use record('v') function instead")
    record(['v'], source, filename)


def record_gsyn(source, filename):
    """ Deprecated method for getting both types of gsyn.\
        This is not documented in the public facing API

    :param source: the population / view / assembly to record
    :param filename: the neo file to write to
    :rtype: None
    """
    logger.warning(
        "Using record_gsyn is deprecated.  Use record('gsyn_exc') and/or"
        " record('gsyn_inh') function instead")
    record(['gsyn_exc', 'gsyn_inh'], source, filename)


def list_standard_models():
    """ Return a list of all the StandardCellType classes available for this\
        simulator.
    """
    results = list()
    for (key, obj) in iteritems(globals()):
        if isinstance(obj, type) and issubclass(obj, AbstractPyNNModel):
            results.append(key)
    return results


def set_number_of_neurons_per_core(neuron_type, max_permitted):
    """ Sets a ceiling on the number of neurons of a given type that can be\
        placed on a single core.

    :param neuron_type: neuron type
    :param max_permitted: the number to set to
    :rtype: None
    """
    if isinstance(neuron_type, str):
        msg = "set_number_of_neurons_per_core call now expects " \
              "neuron_typeas a class instead of as a str"
        raise ConfigurationException(msg)
    simulator = globals_variables.get_simulator()
    simulator.set_number_of_neurons_per_core(
        neuron_type, max_permitted)


# These methods will deffer to PyNN methods if a simulator exists


def connect(pre, post, weight=0.0, delay=None, receptor_type=None, p=1,
            rng=None):
    """ Builds a projection

    :param pre: source pop
    :param post: destination pop
    :param weight: weight of the connections
    :param delay: the delay of the connections
    :param receptor_type: excitatory / inhibitatory
    :param p: probability
    :param rng: random number generator
    :rtype: None
    """
    # pylint: disable=too-many-arguments
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    __pynn["connect"](pre, post, weight, delay, receptor_type, p, rng)


def create(cellclass, cellparams=None, n=1):
    """ Builds a population with certain params

    :param cellclass: population class
    :param cellparams: population params.
    :param n: n neurons
    :rtype: None
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["create"](cellclass, cellparams, n)


def NativeRNG(seed_value):
    """ Fixes the random number generator's seed

    :param seed_value:
    :rtype: None
    """
    __numpy.random.seed(seed_value)


def get_current_time():
    """ Gets the time within the simulation

    :return: returns the current time
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["get_current_time"]()


def get_min_delay():
    """ The minimum allowed synaptic delay; delays will be clamped to be at\
        least this.

    :return: returns the min delay of the simulation
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["get_min_delay"]()


def get_max_delay():
    """ The maximum allowed synaptic delay; delays will be clamped to be at\
        most this.

    :return: returns the max delay of the simulation
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["get_max_delay"]()


def get_time_step():
    """ The integration time step

    :return: get the time step of the simulation (in ms)
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return float(__pynn["get_time_step"]()) / 1000.0


def initialize(cells, **initial_values):
    """ Sets cells to be initialised to the given values

    :param cells: the cells to change params on
    :param initial_values: the params and there values to change
    :rtype: None
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    pynn_common.initialize(cells, **initial_values)


def num_processes():
    """ The number of MPI processes.

    .. note::
        Always 1 on SpiNNaker, which doesn't use MPI.

    :return: the number of MPI processes
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["num_processes"]()


def rank():
    """ The MPI rank of the current node.

    .. note::
        Always 0 on SpiNNaker, whcih doesn't use MPI.

    :return: MPI rank
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["rank"]()


def record(variables, source, filename, sampling_interval=None,
           annotations=None):
    """ Sets variables to be recorded.

    :param variables: may be either a single variable name or a list of \
        variable names. For a given celltype class, celltype.recordable \
        contains a list of variables that can be recorded for that celltype.
    :param source: where to record from
    :param filename: file name to write data to
    :param sampling_interval: \
        how often to sample the recording, not  ignored so far
    :param annotations: the annotations to data writers
    :return: neo object
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["record"](variables, source, filename, sampling_interval,
                            annotations)


def reset(annotations=None):
    """ Resets the simulation to t = 0

    :param annotations: the annotations to the data objects
    :rtype: None
    """
    if annotations is None:
        annotations = {}
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    __pynn["reset"](annotations)


def run(simtime, callbacks=None):
    """ The run() function advances the simulation for a given number of \
        milliseconds, e.g.:

    :param simtime: time to run for (in milliseconds)
    :param callbacks: callbacks to run
    :return: the actual simulation time that the simulation stopped at
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["run"](simtime, callbacks=callbacks)


# left here because needs to be done, and no better place to put it
# (ABS don't like it, but will put up with it)
run_for = run


def run_until(tstop):
    """ Run until a (simulation) time period has completed.

    :param tstop: the time to stop at (in milliseconds)
    :return: the actual simulation time that the simulation stopped at
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return __pynn["run_until"](tstop)


def get_machine():
    """ Get the SpiNNaker machine in use.

    :return: the machine object
    """
    if not globals_variables.has_simulator():
        raise ConfigurationException(FAILED_STATE_MSG)
    return globals_variables.get_simulator().machine
