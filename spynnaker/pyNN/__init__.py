# encoding: utf-8
"""
The :py:mod:`spynnaker.pynn` package contains the frontend specifications
and implementation for the PyNN High-level API
(http://neuralensemble.org/trac/PyNN)
"""

import inspect
from collections import defaultdict
from ._version import __version__, __version_month__, __version_year__

# utility functions
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.utilities.parameters_surrogate\
    import PyNNParametersSurrogate

# pynn centric classes
from spynnaker.pyNN.spinnaker import Spinnaker
from spynnaker.pyNN.spinnaker import executable_finder
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.utilities.database.socket_address import SocketAddress

# neural models
from spynnaker.pyNN.models.neural_models.if_cond_exp \
    import IFConductanceExponentialPopulation as IF_cond_exp
from spynnaker.pyNN.models.neural_models.if_curr_dual_exp \
    import IFCurrentDualExponentialPopulation as IF_curr_dual_exp
from spynnaker.pyNN.models.neural_models.if_curr_exp \
    import IFCurrentExponentialPopulation as IF_curr_exp
from spynnaker.pyNN.models.neural_models.izk_curr_exp \
    import IzhikevichCurrentExponentialPopulation as IZK_curr_exp

# neural projections
from spynnaker.pyNN.models.neural_projections\
    .delay_afferent_partitionable_edge import DelayAfferentPartitionableEdge
from spynnaker.pyNN.models.utility_models.delay_extension_vertex \
    import DelayExtensionVertex
from spynnaker.pyNN.models.neural_projections.delay_partitionable_edge \
    import DelayPartitionableEdge
from spynnaker.pyNN.models.neural_projections.delay_partitioned_edge \
    import DelayPartitionedEdge
from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge
from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge

# spike sources
from spynnaker.pyNN.models.spike_source.spike_source_poisson\
    import SpikeSourcePoisson
from spynnaker.pyNN.models.spike_source.spike_source_array \
    import SpikeSourceArray
from spynnaker.pyNN.models.spike_source.spike_source_from_file \
    import SpikeSourceFromFile

# connections
from spynnaker.pyNN.models.neural_projections.connectors.all_to_all_connector\
    import AllToAllConnector
from spynnaker.pyNN.models.neural_projections.connectors.\
    fixed_number_pre_connector import FixedNumberPreConnector
from spynnaker.pyNN.models.neural_projections.connectors.\
    fixed_probability_connector import FixedProbabilityConnector
from spynnaker.pyNN.models.neural_projections.connectors.from_list_connector \
    import FromListConnector
from spynnaker.pyNN.models.neural_projections.connectors.from_file_connector \
    import FromFileConnector
from spynnaker.pyNN.models.neural_projections.connectors.multapse_connector \
    import MultapseConnector
from spynnaker.pyNN.models.neural_projections.connectors.one_to_one_connector \
    import OneToOneConnector
from spynnaker.pyNN.models.neural_projections.connectors.\
    distance_dependent_probability_connector import \
    DistanceDependentProbabilityConnector
from spynnaker.pyNN.models.neural_projections.connectors.\
    fixed_number_post_connector import FixedNumberPostConnector
from spynnaker.pyNN.models.neural_projections.connectors.small_world_connector\
    import SmallWorldConnector

# Mechanisms for synapse dynamics
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.\
    synapse_dynamics import SynapseDynamics
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.stdp_mechanism \
    import STDPMechanism

# STDP weight dependences
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.dependences.\
    additive_weight_dependence import AdditiveWeightDependence
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.dependences.\
    multiplicative_weight_dependence import MultiplicativeWeightDependence

# STDP timing dependences
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.dependences.\
    pfister_spike_triplet_time_dependence import \
    PfisterSpikeTripletTimeDependence as PfisterSpikeTripletRule
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.dependences.\
    spike_pair_time_dependency import SpikePairTimeDependency as SpikePairRule

# constraints
from pacman.model.constraints.placer_constraints.\
    placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint import PartitionerMaximumSizeConstraint
from pacman.model.constraints.placer_constraints.\
    placer_radial_placement_from_chip_constraint \
    import PlacerRadialPlacementFromChipConstraint

# note importing star is a bad thing to do.
from pyNN.random import *
from pyNN.space import *

# traditional logger
logger = logging.getLogger(__name__)

# global controller / spinnaker object that does everything
_spinnaker = None

# List of binary search paths
_binary_search_paths = []

# Populations recorded using the "low-level" API - record(), record_v(), etc.
record_list = defaultdict(list)


def register_binary_search_path(search_path):
    """
    :param search_path:
    Registers an additional binary search path for
        for executables

    absolute search path for binaries
    """
    executable_finder.add_path(search_path)


def end(stop_on_board=True):
    """
    :param stop_on_board:
    Do any necessary cleaning up before exiting.

    Unregisters the controller,
    prints any data recorded using the low-level API
    """
    global _spinnaker, record_list
    for population in record_list['spikes']:
        population.printSpikes(population._record_spike_file)
    for population in record_list['v']:
        population.print_v(population._record_v_file)
    for population in record_list['gsyn']:
        population.print_gsyn(population._record_gsyn_file)
    _spinnaker.stop(stop_on_board)
    _spinnaker = None


def get_spynnaker():
    """helper method for other plugins to add stuff to the graph

    :return:
    """
    global _spinnaker
    return _spinnaker


def num_processes():
    """Return the number of MPI processes
       (not used for SpiNNaker, always returns 1)
    """
    return 1


def rank():
    """Return the MPI rank of the current node. (not used for SpiNNaker,
    always returns 0 - as this is the minimum rank suggesting the front node)
    """
    return 0


def reset():
    """Reset the time to zero, and start the clock.
    TO BE IMPLEMENTED
    """
    pass


def run(run_time=None):
    """Run the simulation for run_time ms.

    :param int run_time:
        simulation length (in ms)

    On run the following :py:class:`pacman103.core.control.Controller`
    functions are called:
     - :py:mod:`pacman103.core.control.Controller.map_model`
     - :py:mod:`pacman103.core.control.Controller.specify_output`
     - :py:mod:`pacman103.core.control.Controller.generate_output`
     - :py:mod:`pacman103.core.control.Controller.load_executables`
     - :py:mod:`pacman103.core.control.Controller.run`
    """
    global _spinnaker
    _spinnaker.run(run_time)
    return None


def setup(timestep=0.1, min_delay=None, max_delay=None, machine=None,
          database_socket_addresses=None, **extra_params):
    """
    Should be called at the very beginning of a script.
    extra_params contains any keyword arguments that are required by a given
    simulator but not by others.
    For simulation on SpiNNaker the following parameters are mandatory:

    :param `pacman103.lib.lib_machine` machine:
        A SpiNNaker machine used to run the simulation.


    The setup() call instantiates a
    :py:class:`pacman103.core.control.Controller`
    object which is used as a global variable throughout the whole process.

    It also creates an AppMonitor Object (a vertex with model-type AppMon),
    placing a mapping constraint on it so that it is on chip (0,0).
    This functionality may move elsewhere later.

    NB: timestep, min_delay and max_delay are required by the PyNN API but we
    ignore them because they have no bearing on the on-chip simulation code.
    :param timestep:
    :param min_delay:
    :param max_delay:
    :param machine:
    :param database_socket_addresses:
    :param extra_params:
    :return:
    """
    global _spinnaker
    global _binary_search_paths
    global record_list

    logger.info(
        "sPyNNaker (c) {} APT Group, University of Manchester".format(
            __version_year__))
    logger.info(
        "Release version {} - {} {}".format(
            __version__, __version_month__, __version_year__))

    if len(extra_params) > 1:
        logger.warn("Extra params has been applied which we do not consider")
    _spinnaker = Spinnaker(
        host_name=machine, timestep=timestep, min_delay=min_delay,
        max_delay=max_delay,
        database_socket_addresses=database_socket_addresses)
    record_list = defaultdict(list)
    # the PyNN API expects the MPI rank to be returned
    return rank()


def set_number_of_neurons_per_core(neuron_type, max_permitted):
    """
    Sets a ceiling on the number of neurons of a given type that can be placed
    on a single core.
    This information is stored in the model itself  and is referenced
    during the partition stage of the mapper.
    Note that each neuron type has a default value for this parameter that will
    be used if no override is given.
    :param neuron_type:
    :param max_permitted:
    """
    if not inspect.isclass(neuron_type):
        if neuron_type in globals():
            neuron_type = globals()[neuron_type]
        else:
            neuron_type = None
        if neuron_type is None:
            raise Exception("Unknown Vertex Type {}"
                            .format(neuron_type))

    if hasattr(neuron_type, "set_model_max_atoms_per_core"):
        neuron_type.set_model_max_atoms_per_core(max_permitted)
    else:
        raise Exception("{} is not a Vertex type"
                        .format(neuron_type))


def register_database_notification_request(hostname, notify_port, ack_port):
    """
    Adds a socket system which is registered with the notification protocol

    :param hostname:
    :param notify_port:
    :param ack_report:
    :return:
    """
    _spinnaker._add_socket_address(
        SocketAddress(hostname, notify_port, ack_port))


# noinspection PyPep8Naming
def Population(size, cellclass, cellparams, structure=None, label=None):
    """

    :param size:
    :param cellclass:
    :param cellparams:
    :param structure:
    :param label:
    :return:
    """
    global _spinnaker
    return _spinnaker.create_population(size, cellclass, cellparams,
                                        structure, label)


# noinspection PyPep8Naming
def Projection(presynaptic_population, postsynaptic_population,
               connector, source=None, target='excitatory',
               synapse_dynamics=None, label=None, rng=None):
    """

    :param presynaptic_population:
    :param postsynaptic_population:
    :param connector:
    :param source:
    :param target:
    :param synapse_dynamics:
    :param label:
    :param rng:
    :return:
    """
    global _spinnaker
    return _spinnaker.create_projection(
        presynaptic_population, postsynaptic_population, connector, source,
        target, synapse_dynamics, label, rng)


def NativeRNG(seed_value):
    """
    fixes the rnadom number generators seed
    :param seed_value:
    :return:
    """
    numpy.random.seed(seed_value)


def get_current_time():
    """

    :return:
    """
    global _spinnaker
    return _spinnaker.get_current_time()


# ==============================================================================
#   Low-level API for creating, connecting and recording from individual neurons
# ==============================================================================

def create(cellclass, cellparams=None, n=1):
    """
    Create n cells all of the same type.

    If n > 1, return a list of cell ids/references.
    If n==1, return just the single id.
    """
    return Population(n, cellclass, cellparams)


def connect(source, target, weight=0.0, delay=None, synapse_type=None,
            p=1, rng=None):
    """
    Connect a source of spikes to a synaptic target.

    source and target can both be individual cells or lists of cells, in
    which case all possible connections are made with probability p, using
    either the random number generator supplied, or the default rng
    otherwise. Weights should be in nA or µS.
    """
    connector = FixedProbabilityConnector(p_connect=p, weights=weight, delays=delay)
    return Projection(source, target, connector, target=synapse_type, rng=rng)


def set(cells, param, val=None):
    """
    Set one or more parameters of an individual cell or list of cells.

    param can be a dict, in which case val should not be supplied, or a string
    giving the parameter name, in which case val is the parameter value.
    """
    assert isinstance(cells, Population)
    cells.set(param, val)


def initialize(cells, variable, value):
    cells.initialize(variable, value)


def record(source, filename):
    """
    Record spikes to a file. source should be a Population.
    """
    global record_list
    source.record(to_file=filename)
    # record_list is used by end()
    record_list['spikes'].append(source)


def record_v(source, filename):
    """
    Record spikes to a file. source should be a Population.
    """
    global record_list
    source.record_v(to_file=filename)
    # record_list is used by end()
    record_list['v'].append(source)


def record_gsyn(source, filename):
    """
    Record spikes to a file. source should be a Population.
    """
    global record_list
    source.record_gsyn(to_file=filename)
    # record_list is used by end()
    record_list['gsyn'].append(source)
