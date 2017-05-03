# encoding: utf-8
"""
The :py:mod:`spynnaker.pynn` package contains the front-end specifications
and implementation for the PyNN High-level API
(http://neuralensemble.org/trac/PyNN)
"""

import inspect as __inspect

from ._version import __version__, __version_name__, __version_month__,\
    __version_year__


# utility functions
from .utilities import utility_calls

# pynn centric classes
from .spinnaker import Spinnaker as __Spinnaker
from .spinnaker import executable_finder as __exec_finder

# notification protocol classes (stored in front end common)
from spinn_front_end_common.utilities.notification_protocol.\
    socket_address import SocketAddress as __SockAddr

# front end common exceptions
from spinn_front_end_common.utilities import exceptions as \
    front_end_common_exceptions

# neural models
from .models.neuron.builds.if_cond_exp \
    import IFCondExp as IF_cond_exp
from .models.neuron.builds.if_curr_dual_exp \
    import IFCurrDualExp as IF_curr_dual_exp
from .models.neuron.builds.if_curr_exp \
    import IFCurrExp as IF_curr_exp
from .models.neuron.builds.izk_curr_exp \
    import IzkCurrExp as IZK_curr_exp
from .models.neuron.builds.izk_cond_exp \
    import IzkCondExp as IZK_cond_exp

# neural projections
from .models.neural_projections.delay_afferent_application_edge \
    import DelayAfferentApplicationEdge
from .models.utility_models.delay_extension_vertex \
    import DelayExtensionVertex
from .models.neural_projections.projection_application_edge \
    import ProjectionApplicationEdge

# spike sources
from .models.spike_source.spike_source_poisson \
    import SpikeSourcePoisson
from .models.spike_source.spike_source_array \
    import SpikeSourceArray
from .models.spike_source.spike_source_from_file \
    import SpikeSourceFromFile

# connections
from .models.neural_projections.connectors.all_to_all_connector \
    import AllToAllConnector
from .models.neural_projections.connectors.fixed_number_pre_connector \
    import FixedNumberPreConnector
from .models.neural_projections.connectors.fixed_probability_connector \
    import FixedProbabilityConnector
from .models.neural_projections.connectors.from_list_connector \
    import FromListConnector
from .models.neural_projections.connectors.from_file_connector \
    import FromFileConnector
from .models.neural_projections.connectors.multapse_connector \
    import MultapseConnector
from .models.neural_projections.connectors.one_to_one_connector \
    import OneToOneConnector
from .models.neural_projections.connectors.\
    distance_dependent_probability_connector \
    import DistanceDependentProbabilityConnector
from .models.neural_projections.connectors.fixed_number_post_connector \
    import FixedNumberPostConnector

# Mechanisms for synapse dynamics
from .models.neuron.synapse_dynamics.pynn_synapse_dynamics \
    import PyNNSynapseDynamics as SynapseDynamics
from .models.neuron.synapse_dynamics.synapse_dynamics_stdp \
    import SynapseDynamicsSTDP as STDPMechanism

# STDP weight dependences
from .models.neuron.plasticity.stdp.weight_dependence\
    .weight_dependence_additive \
    import WeightDependenceAdditive as AdditiveWeightDependence
from .models.neuron.plasticity.stdp.weight_dependence\
    .weight_dependence_multiplicative\
    import WeightDependenceMultiplicative as MultiplicativeWeightDependence

# STDP timing dependences
from .models.neuron.plasticity.stdp.timing_dependence\
    .timing_dependence_spike_pair \
    import TimingDependenceSpikePair as SpikePairRule
from .models.neuron.plasticity.stdp.timing_dependence\
    .timing_dependence_pfister_spike_triplet\
    import TimingDependencePfisterSpikeTriplet as PfisterSpikeTripletRule

import spynnaker
# constraints

# note importing star is a bad thing to do.
from pyNN.random import NumpyRNG, RandomDistribution
from pyNN.space import \
    distance, Space, Line, Grid2D, Grid3D, Cuboid, Sphere, RandomStructure
import os as __os
import numpy as __numpy

# traditional logger
import logging as __logging
logger = __logging.getLogger(__name__)

# global controller / spinnaker object that does everything
_spinnaker = None

# List of binary search paths
_binary_search_paths = []

__all__ = [
    # Ugly, but tests expect it
    'utility_calls',
    # Implementations of the neuroscience models
    'IF_cond_exp', 'IF_curr_dual_exp', 'IF_curr_exp', 'IZK_curr_exp',
    'IZK_cond_exp', 'DelayAfferentApplicationEdge', 'DelayExtensionVertex',
    'ProjectionApplicationEdge', 'SpikeSourcePoisson', 'SpikeSourceArray',
    'SpikeSourceFromFile', 'AllToAllConnector', 'FixedNumberPreConnector',
    'FixedProbabilityConnector', 'FromListConnector', 'FromFileConnector',
    'MultapseConnector', 'OneToOneConnector', 'FixedNumberPostConnector',
    'DistanceDependentProbabilityConnector', 'SynapseDynamics',
    'STDPMechanism', 'AdditiveWeightDependence', 'SpikePairRule',
    'MultiplicativeWeightDependence', 'PfisterSpikeTripletRule',
    # Stuff from pyNN.random
    'NumpyRNG', 'RandomDistribution',
    # Stuff from pyNN.space
    'distance', 'Space', 'Line', 'Grid2D', 'Grid3D', 'Cuboid', 'Sphere',
    'RandomStructure',
    # Stuff that we define
    'register_binary_search_path', 'end', 'setup', 'run', 'get_spynnaker',
    'num_processes', 'rank', 'reset', 'set_number_of_neurons_per_core',
    'register_database_notification_request', 'Population', 'Projection',
    'NativeRNG', 'get_current_time', 'create', 'connect', 'get_time_step',
    'get_min_delay', 'get_max_delay', 'set', 'initialize', 'record',
    'record_v', 'record_gsyn', 'get_machine']


def register_binary_search_path(search_path):
    """ Registers an additional binary search path for executables

    :param search_path: absolute search path for binaries
    """
    __exec_finder.add_path(search_path)


def end():
    """
    Do any necessary cleaning up before exiting.

    Unregisters the controller,
    prints any data recorded using the low-level API
    """
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "end")
    _spinnaker.stop()
    _spinnaker = None


def get_spynnaker():
    """helper method for other plugins to add stuff to the graph

    :return: The current spinnaker API, or None if before setup or after end.
    """
    global _spinnaker
    return _spinnaker


def num_processes():
    """ Return the number of MPI processes
       (not used for SpiNNaker, always returns 1)
    """
    return 1


def rank():
    """ Return the MPI rank of the current node. (not used for SpiNNaker,\
        always returns 0 - as this is the minimum rank suggesting the front\
        node)
    """
    return 0


def reset():
    """ Reset the time to zero, and start the clock.
    """
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "reset")
    _spinnaker.reset()


def run(run_time=None):
    """ Run the simulation for run_time ms.

    :param run_time: simulation length (in ms)
    """
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "run")
    _spinnaker.run(run_time)
    return None


def setup(timestep=0.1, min_delay=None, max_delay=None, machine=None,
          database_socket_addresses=None, n_chips_required=None,
          **extra_params):
    """ Should be called at the very beginning of a script.
        extra_params contains any keyword arguments that are required by a\
        given simulator but not by others.

    :param machine: A SpiNNaker machine used to run the simulation.
    :param timestep: The timestep in milleseconds.\
       Value will be rounded up to whole microseconds.\
       Set to None to use the value from the config file
    :rtype: float or None
    :param min_delay:
    :param max_delay:
    :param machine:
    :param database_socket_addresses:
    :param n_chips_required: The number of chips required for the simulation
    :param extra_params:
    """
    global _spinnaker
    global _binary_search_paths

    logger.info(
        "sPyNNaker (c) {} APT Group, University of Manchester".format(
            __version_year__))
    parent_dir = __os.path.split(__os.path.split(spynnaker.__file__)[0])[0]
    logger.info(
        "Release version {}({}) - {} {}. Installed in folder {}".format(
            __version__, __version_name__, __version_month__, __version_year__,
            parent_dir))

    if len(extra_params) > 0:
        logger.warn("Extra params {} have been applied to the setup "
                    "command which we do not consider".format(extra_params))
    _spinnaker = __Spinnaker(
        host_name=machine, timestep=timestep, min_delay=min_delay,
        max_delay=max_delay,
        database_socket_addresses=database_socket_addresses,
        n_chips_required=n_chips_required)
    # the PyNN API expects the MPI rank to be returned
    return rank()


def set_number_of_neurons_per_core(neuron_type, max_permitted):
    """ Sets a ceiling on the number of neurons of a given type that can be\
        placed on a single core.

    """
    if not __inspect.isclass(neuron_type):
        if neuron_type not in globals():
            raise Exception("Unknown Vertex Type {}".format(neuron_type))
        neuron_type = globals()[neuron_type]

    if not hasattr(neuron_type, "set_model_max_atoms_per_core"):
        raise Exception("{} is not a Vertex type".format(neuron_type))
    neuron_type.set_model_max_atoms_per_core(max_permitted)


def register_database_notification_request(hostname, notify_port, ack_port):
    """ Adds a socket system which is registered with the notification protocol

    """
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "register_database_notification_request")
    _spinnaker._add_socket_address(
        __SockAddr(hostname, notify_port, ack_port))


# noinspection PyPep8Naming
def Population(size, cellclass, cellparams, structure=None, label=None):
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "Population")
    return _spinnaker.create_population(
        size, cellclass, cellparams, structure, label)


# noinspection PyPep8Naming
def Projection(presynaptic_population, postsynaptic_population,
               connector, source=None, target='excitatory',
               synapse_dynamics=None, label=None, rng=None):
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "Projection")
    return _spinnaker.create_projection(
        presynaptic_population, postsynaptic_population, connector, source,
        target, synapse_dynamics, label, rng)


def NativeRNG(seed_value):
    """ Fixes the random number generator's seed

    """
    __numpy.random.seed(seed_value)


def get_current_time():
    """
    returns the machine time step defined in setup
    """
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "get_current_time")
    return _spinnaker.get_current_time()


# =============================================================================
#  Low-level API for creating, connecting and recording from individual neurons
# =============================================================================

def create(cellclass, cellparams=None, n=1):
    """ Create n cells all of the same type.

    If n > 1, return a list of cell ids/references.
    If n==1, return just the single id.
    """
    if cellparams is None:
        cellparams = {}
    return Population(n, cellclass, cellparams)


def connect(source, target, weight=0.0, delay=None, synapse_type="excitatory",
            p=1, rng=None):
    """ Connect a source of spikes to a synaptic target.

    source and target can both be individual cells or lists of cells, in
    which case all possible connections are made with probability p, using
    either the random number generator supplied, or the default rng
    otherwise. Weights should be in nA or µS.
    """
    connector = FixedProbabilityConnector(
        p_connect=p, weights=weight, delays=delay)
    return Projection(source, target, connector, target=synapse_type, rng=rng)


def get_time_step():
    """ The timestep requested
    """
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "get_time_step")
    return _spinnaker.machine_time_step


def get_min_delay():
    """ The minimum allowed synaptic delay.
    """
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "get_min_delay")
    return _spinnaker.min_supported_delay


def get_max_delay():
    """ The maximum allowed synaptic delay.
    """
    global _spinnaker
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "get_max_delay")
    return _spinnaker.max_supported_delay


def set(cells, param, val=None):  # @ReservedAssignment
    """ Set one or more parameters of an individual cell or list of cells.

    param can be a dict, in which case val should not be supplied, or a string
    giving the parameter name, in which case val is the parameter value.
    """
    assert isinstance(cells, Population)
    cells.set(param, val)


def initialize(cells, variable, value):
    cells.initialize(variable, value)


def record(source, filename):
    """ Record spikes to a file. source should be a Population.
    """
    source.record(to_file=filename)


def record_v(source, filename):
    """ Record spikes to a file. source should be a Population.
    """
    source.record_v(to_file=filename)


def record_gsyn(source, filename):
    """ Record spikes to a file. source should be a Population.
    """
    source.record_gsyn(to_file=filename)


def get_machine():
    """ Get the spinnaker machine in use
    """
    if _spinnaker is None:
        raise front_end_common_exceptions.ConfigurationException(
            "You currently have not ran setup, please do so before calling "
            "get_machine")
    return _spinnaker.machine
