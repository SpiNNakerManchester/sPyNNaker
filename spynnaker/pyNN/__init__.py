"""
The :py:mod:`spynnaker.pynn` package contains the frontend specifications
and implementation for the PyNN High-level API
(http://neuralensemble.org/trac/PyNN)
"""

import logging
import inspect

#utility functions
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.utilities.parameters_surrogate\
    import PyNNParametersSurrogate
from spynnaker.pyNN.utilities.constants import VISUALISER_MODES

#pynn centric classes
from spynnaker.pyNN.spinnaker import Spinnaker
from spynnaker.pyNN import exceptions

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
from spynnaker.pyNN.models.neural_projections.delay_afferent_edge \
    import DelayAfferentEdge
from spynnaker.pyNN.models.neural_projections.delay_extension_vertex\
    import DelayExtensionVertex
from spynnaker.pyNN.models.neural_projections.delay_projection_edge \
    import DelayProjectionEdge
from spynnaker.pyNN.models.neural_projections.delay_projection_subedge \
    import DelayProjectionSubedge
from spynnaker.pyNN.models.neural_projections.projection_edge \
    import ProjectionEdge
from spynnaker.pyNN.models.neural_projections.projection_subedge \
    import ProjectionSubedge

#spike sources
from spynnaker.pyNN.models.spike_source.spike_source_array \
    import SpikeSourceArray
from spynnaker.pyNN.models.spike_source.spike_source_poisson\
    import SpikeSourcePoisson

#connections
from spynnaker.pyNN.models.neural_projections.connectors.all_to_all\
    import AllToAllConnector
from spynnaker.pyNN.models.neural_projections.connectors.\
    fixed_number_pre_connector import FixedNumberPreConnector
from spynnaker.pyNN.models.neural_projections.connectors.fixed_probability \
    import FixedProbabilityConnector
from spynnaker.pyNN.models.neural_projections.connectors.from_list \
    import FromListConnector
from spynnaker.pyNN.models.neural_projections.connectors.from_file \
    import FromFileConnector
from spynnaker.pyNN.models.neural_projections.connectors.multapse \
    import MultapseConnector
from spynnaker.pyNN.models.neural_projections.connectors.one_to_one \
    import OneToOneConnector
from spynnaker.pyNN.models.neural_projections.connectors.\
    distance_dependent_probability import DistanceDependentProbabilityConnector
from spynnaker.pyNN.models.neural_projections.connectors.\
    fixed_number_post_connector import FixedNumberPostConnector
from spynnaker.pyNN.models.neural_projections.connectors.from_file \
    import FromFileConnector
from spynnaker.pyNN.models.neural_projections.connectors.small_world_connector \
    import SmallWorldConnector

#constraints
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.constraints.partitioner_same_size_as_vertex_constraint import\
    PartitionerSameSizeAsVertexConstraint
from pacman.model.constraints.placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_subvertex_same_chip_constraint \
    import PlacerSubvertexSameChipConstraint


#traditional logger
logger = logging.getLogger(__name__)
#global controller / spinnaker object that does everything
_spinnaker = None


def end():
    """
    Do any necessary cleaning up before exiting.

    Unregisters the controller
    """
    global _spinnaker
    _spinnaker.stop()
    _spinnaker = None


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


def setup(timestep=None, min_delay=None, max_delay=None, machine=None,
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

    logger.info("PACMAN103   (c) 2014 APT Group, University of Manchester")
    logger.info("                Release version 2014.4.1 - April 2014")

    if len(extra_params.keys()) > 1:
        logger.warn("Extra params has been applied which we do not consider")
    _spinnaker = Spinnaker(machine, timestep, min_delay, max_delay)
    # Return None, simply because the PyNN API says something must be returned
    return None


def set_number_of_neurons_per_core(neuron_type, max_permitted):
    """
    Sets a ceiling on the number of neurons of a given type that can be placed
    on a single core.
    This information is stored in  dictionary in the dao and is referenced
    during the partition stage of the mapper.
    Note that each neuron type has a default value for this parameter that will
    be used if no override is given.
    """
    if not inspect.isclass(neuron_type):
        neuron_type = globals()[neuron_type]
        if neuron_type is None:
            raise Exception("Unknown Vertex Type {}".format(neuron_type))

    if hasattr(neuron_type, "set_model_max_atoms_per_core"):
        neuron_type.set_model_max_atoms_per_core = max_permitted
    else:
        raise Exception("{} is not a Vertex type".format(neuron_type))


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