"""
The :py:mod:`spynnaker.pynn` package contains the frontend specifications
and implementation for the PyNN High-level API
(http://neuralensemble.org/trac/PyNN)
"""

import inspect
from ._version import __version__, __version_month__, __version_year__

#utility functions
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.utilities.parameters_surrogate\
    import PyNNParametersSurrogate

#pynn centric classes
from spynnaker.pyNN.spinnaker import Spinnaker
from spynnaker.pyNN import exceptions
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam

# neural models
from spynnaker.pyNN.models.neural_models.if_cond_exp \
    import IFConductanceExponentialPopulation as IF_cond_exp
from spynnaker.pyNN.models.neural_models.if_curr_dual_exp \
    import IFCurrentDualExponentialPopulation as IF_curr_dual_exp
from spynnaker.pyNN.models.neural_models.if_curr_exp \
    import IFCurrentExponentialPopulation as IF_curr_exp
from spynnaker.pyNN.models.neural_models.izk_curr_exp \
    import IzhikevichCurrentExponentialPopulation as IZK_curr_exp

#neural projections
from spynnaker.pyNN.models.neural_projections.delay_afferent_partitionable_edge \
    import DelayAfferentPartitionableEdge
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

#spike sources
from spynnaker.pyNN.models.spike_source.spike_source_array \
    import SpikeSourceArray
from spynnaker.pyNN.models.spike_source.spike_source_poisson\
    import SpikeSourcePoisson

#connections
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
from spynnaker.pyNN.models.neural_projections.connectors.from_file_connector \
    import FromFileConnector
from spynnaker.pyNN.models.neural_projections.connectors.small_world_connector \
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

#constraints
from pacman.model.constraints.placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint

#note importing star is a bad thing to do.
from pyNN.random import *
from pyNN.space import *

#traditional logger
logger = logging.getLogger(__name__)

#global controller / spinnaker object that does everything
_spinnaker = None

# List of binary search paths
_binary_search_paths = []

def register_binary_search_path(search_path):
    """Registers an additional binary search path for
    for SpiNNaker executables. Should be called before
    setup by sPyNNaker plugin modules

    :param string search_path:
    absolute search path for binaries
    """
    _binary_search_paths.append(search_path)

def end(stop_on_board=True):
    """
    Do any necessary cleaning up before exiting.

    Unregisters the controller
    """
    global _spinnaker
    _spinnaker.stop(_spinnaker.app_id, stop_on_board)
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
          **extra_params):
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
    """
    global _spinnaker
    global _binary_search_paths

    logger.info(
        "sPyNNaker (c) {} APT Group, University of Manchester".format(
            __version_year__))
    logger.info(
        "Release version {} - {} {}".format(
            __version__, __version_month__, __version_year__))

    if len(extra_params.keys()) > 1:
        logger.warn("Extra params has been applied which we do not consider")
    _spinnaker = Spinnaker(host_name=machine, timestep=timestep,
                           min_delay=min_delay, max_delay=max_delay,
                           binary_search_paths=_binary_search_paths)
    # Return None, simply because the PyNN API says something must be returned
    return None


def set_number_of_neurons_per_core(neuron_type, max_permitted):
    """
    Sets a ceiling on the number of neurons of a given type that can be placed
    on a single core.
    This information is stored in the model itself  and is referenced
    during the partition stage of the mapper.
    Note that each neuron type has a default value for this parameter that will
    be used if no override is given.
    """
    if not inspect.isclass(neuron_type):
        if neuron_type in globals():
            neuron_type = globals()[neuron_type]
        else:
            neuron_type = None
        if neuron_type is None:
            raise Exception("Unknown AbstractConstrainedVertex Type {}"
                            .format(neuron_type))

    if hasattr(neuron_type, "set_model_max_atoms_per_core"):
        neuron_type.set_model_max_atoms_per_core(max_permitted)
    else:
        raise Exception("{} is not a AbstractConstrainedVertex type"
                        .format(neuron_type))


# noinspection PyPep8Naming
def Population(size, cellclass, cellparams, structure=None, label=None):
    global _spinnaker
    return _spinnaker.create_population(size, cellclass, cellparams,
                                        structure, label)


# noinspection PyPep8Naming
def Projection(presynaptic_population, postsynaptic_population,
               connector, source=None, target='excitatory',
               synapse_dynamics=None, label=None, rng=None):
    global _spinnaker
    return _spinnaker.create_projection(
        presynaptic_population, postsynaptic_population, connector, source,
        target, synapse_dynamics, label, rng)


def get_current_time():
    global _spinnaker
    return _spinnaker.get_current_time()
