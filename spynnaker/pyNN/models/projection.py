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

import functools
import logging
import numpy
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.log import FormatAdapter
from pyNN import common as pynn_common
from pyNN.recording.files import StandardTextFile
from pyNN.space import Space as PyNNSpace
from spinn_utilities.logger_utils import warn_once
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from spynnaker.pyNN.models.neural_projections import (
    SynapseInformation, ProjectionApplicationEdge)
from spynnaker.pyNN.models.neural_projections.connectors import (
    FromListConnector)
from spynnaker.pyNN.models.neuron import ConnectionHolder
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic)
from spynnaker._version import __version__
from spynnaker.pyNN.models.populations import Population, PopulationView
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVertex

logger = FormatAdapter(logging.getLogger(__name__))


def _we_dont_do_this_now(*args):  # pylint: disable=unused-argument
    # pragma: no cover
    raise NotImplementedError("sPyNNaker does not currently do this")


class Projection(object):
    """
    A container for all the connections of a given type (same synapse type and
    plasticity mechanisms) between two populations, together with methods to
    set parameters of those connections, including of plasticity mechanisms.
    """
    # "format" param name defined by PyNN/
    # pylint: disable=redefined-builtin
    __slots__ = (
        "__projection_edge",
        "__synapse_information",
        "__virtual_connection_list",
        "__label")

    def __init__(
            self, pre_synaptic_population, post_synaptic_population,
            connector, synapse_type=None, source=None,
            receptor_type=None, space=None, label=None):
        """
        :param ~spynnaker.pyNN.models.populations.PopulationBase \
                pre_synaptic_population:
        :param ~spynnaker.pyNN.models.populations.PopulationBase \
                post_synaptic_population:
        :param AbstractConnector connector:
        :param AbstractSynapseDynamics synapse_type:
        :param None source: Unsupported; must be `None`
        :param str receptor_type:
        :param ~pyNN.space.Space space:
        :param str label:
        """
        # pylint: disable=too-many-arguments
        if source is not None:
            raise NotImplementedError(
                f"sPyNNaker {__version__} does not yet support "
                "multi-compartmental cells.")

        self.__projection_edge = None
        self.__label = label

        pre_is_view = self.__check_population(pre_synaptic_population)
        post_is_view = self.__check_population(post_synaptic_population)

        # set default label
        if label is None:
            # set the projection's label to a default (maybe non-unique!)
            self.__label = (
                f"from pre {pre_synaptic_population.label} "
                f"to post {post_synaptic_population.label} "
                f"with connector {connector}")
            # give an auto generated label for the underlying edge
            label = "projection edge {}".format(
                SpynnakerDataView.get_next_none_labelled_edge_number())

        # Handle default synapse type
        if synapse_type is None:
            synapse_dynamics = SynapseDynamicsStatic()
        else:
            synapse_dynamics = synapse_type

        # set the space function as required
        if space is None:
            space = PyNNSpace()
        connector.set_space(space)

        pre_vertex = pre_synaptic_population._vertex
        post_vertex = post_synaptic_population._vertex

        if not isinstance(post_vertex, AbstractAcceptsIncomingSynapses):
            raise ConfigurationException(
                "postsynaptic population is not designed to receive"
                " synaptic projections")

        # sort out synapse type
        synapse_id = post_vertex.get_synapse_id_by_target(receptor_type)
        synapse_id_from_dynamics = False
        if synapse_id is None:
            synapse_id = synapse_dynamics.get_synapse_id_by_target(
                receptor_type)
            synapse_id_from_dynamics = True
        if synapse_id is None:
            raise ConfigurationException(
                f"Synapse target {receptor_type} not found "
                f"in {post_synaptic_population.label}")

        # as a from-list connector can have plastic parameters, grab those (
        # if any) and add them to the synapse dynamics object
        if isinstance(connector, FromListConnector):
            connector._apply_parameters_to_synapse_type(synapse_dynamics)

        # set the plasticity dynamics for the post pop (allows plastic stuff
        #  when needed)
        post_vertex.set_synapse_dynamics(synapse_dynamics)

        # Set and store synapse information for future processing
        self.__synapse_information = SynapseInformation(
            connector, pre_synaptic_population, post_synaptic_population,
            pre_is_view, post_is_view, synapse_dynamics,
            synapse_id, receptor_type, synapse_id_from_dynamics,
            synapse_dynamics.weight, synapse_dynamics.delay)

        # Set projection information in connector
        connector.set_projection_information(self.__synapse_information)

        # Find out if there is an existing edge between the populations
        edge_to_merge = self._find_existing_edge(pre_vertex, post_vertex)
        if edge_to_merge is not None:
            # If there is an existing edge, add the connector
            edge_to_merge.add_synapse_information(self.__synapse_information)
            self.__projection_edge = edge_to_merge
        else:
            # If there isn't an existing edge, create a new one and add it
            self.__projection_edge = ProjectionApplicationEdge(
                pre_vertex, post_vertex, self.__synapse_information,
                label=label)
            SpynnakerDataView.add_edge(
                self.__projection_edge, SPIKE_PARTITION_ID)

        # Ensure the connector is happy
        connector.validate_connection(
            self.__projection_edge, self.__synapse_information)

        # add projection to the SpiNNaker control system
        SpynnakerDataView.add_projection(self)

        # If there is a virtual board, we need to hold the data in case the
        # user asks for it
        self.__virtual_connection_list = None
        if get_config_bool("Machine", "virtual_board"):
            self.__virtual_connection_list = list()
            self.__synapse_information.add_pre_run_connection_holder(
                ConnectionHolder(
                    None, False, pre_vertex.n_atoms, post_vertex.n_atoms,
                    self.__virtual_connection_list))

        # If the target is a population, add to the list of incoming
        # projections
        if isinstance(post_vertex, AbstractPopulationVertex):
            post_vertex.add_incoming_projection(self)

        # If the source is a poisson, add to the list of outgoing projections
        if isinstance(pre_vertex, SpikeSourcePoissonVertex):
            pre_vertex.add_outgoing_projection(self)

    @staticmethod
    def __check_population(param):
        """
        :param ~spynnaker.pyNN.models.populations.PopulationBase param:
        :return: Whether the parameter is a view
        :rtype: bool
        """
        if isinstance(param, Population):
            # Projections definitely work from Populations
            return False
        if not isinstance(param, PopulationView):
            raise ConfigurationException(
                f"Unexpected parameter type {type(param)}. "
                "Expected Population")
        # Check whether the array is contiguous or not
        if not param._is_contiguous():  # pylint: disable=protected-access
            raise NotImplementedError(
                "Projections over views only work on contiguous arrays, "
                "e.g. view = pop[n:m], not view = pop[n,m]")
        # Projection is compatible with PopulationView
        return True

    def get(self, attribute_names, format,  # @ReservedAssignment
            gather=True, with_address=True, multiple_synapses='last'):
        """
        Get a parameter/attribute of the projection.

        .. note::
            SpiNNaker always gathers.

        :param attribute_names: list of attributes to gather
        :type attribute_names: str or iterable(str)
        :param str format: ``"list"`` or ``"array"``
        :param bool gather: gather over all nodes
        :param bool with_address:
            True if the source and target are to be included
        :param str multiple_synapses:
            What to do with the data if format="array" and if the multiple
            source-target pairs with the same values exist.  Currently only
            "last" is supported
        :return: values selected
        """
        # pylint: disable=too-many-arguments
        if not gather:
            logger.warning("sPyNNaker always gathers from every core.")
        if multiple_synapses != 'last':
            raise ConfigurationException(
                "sPyNNaker only recognises multiple_synapses == last")

        return self.__get_data(
            attribute_names, format, with_address, notify=None)

    def save(
            self, attribute_names, file, format='list',  # @ReservedAssignment
            gather=True, with_address=True):
        """
        Print synaptic attributes (weights, delays, etc.) to file. In the
        array format, zeros are printed for non-existent connections.
        Values will be expressed in the standard PyNN units (i.e.,
        millivolts, nanoamps, milliseconds, microsiemens, nanofarads,
        event per second).

        .. note::
            SpiNNaker always gathers.

        :param attribute_names:
        :type attribute_names: str or list(str)
        :param file: filename or open handle (which will be closed)
        :type file: str or pyNN.recording.files.BaseFile
        :param str format:
        :param bool gather: Ignored
        :param bool with_address:
        """
        # pylint: disable=too-many-arguments
        if not gather:
            warn_once(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        if isinstance(attribute_names, str):
            attribute_names = [attribute_names]
        if attribute_names in (['all'], ['connections']):
            attribute_names = \
                self._projection_edge.post_vertex.synapse_dynamics.\
                get_parameter_names()
        metadata = {"columns": attribute_names}
        if with_address:
            metadata["columns"] = ["i", "j"] + list(metadata["columns"])
        self.__get_data(
            attribute_names, format, with_address,
            notify=functools.partial(self.__save_callback, file, metadata))

    def __get_data(
            self, attribute_names, format,  # @ReservedAssignment
            with_address, notify):
        """
        Internal data getter to add notify option.

        :param attribute_names: list of attributes to gather
        :type attribute_names: str or iterable(str)
        :param str format: ``"list"`` or ``"array"``
        :param bool with_address:
        :param callable(ConnectionHolder,None) notify:
        :return: values selected
        """
        # fix issue with 1 versus many
        if isinstance(attribute_names, str):
            attribute_names = [attribute_names]

        data_items = list()
        if format != "list":
            with_address = False
        if with_address:
            data_items.append("source")
            data_items.append("target")
            if "source" in attribute_names:
                logger.warning(
                    "Ignoring request to get source as with_address=True. ")
                attribute_names.remove("source")
            if "target" in attribute_names:
                logger.warning(
                    "Ignoring request to get target as with_address=True. ")
                attribute_names.remove("target")

        # Split out attributes in to standard versus synapse dynamics data
        fixed_values = list()
        for attribute in attribute_names:
            data_items.append(attribute)
            if attribute not in {"source", "target", "weight", "delay"}:
                value = self._synapse_information.synapse_dynamics.get_value(
                    attribute)
                fixed_values.append((attribute, value))

        # Return the connection data
        return self._get_synaptic_data(
            format == "list", data_items, fixed_values, notify=notify)

    @staticmethod
    def __save_callback(save_file, metadata, data):
        """
        :param save_file:
        :type save_file: str or pyNN.recording.files.BaseFile
        :param dict(str,object) metadata:
        :param data:
        :type data: ConnectionHolder or numpy.ndarray
        """
        # Convert structured array to normal numpy array
        if hasattr(data, "dtype") and hasattr(data.dtype, "names"):
            dtype = [(name, "<f8") for name in data.dtype.names]
            data = data.astype(dtype)
        data = numpy.nan_to_num(data)
        if isinstance(save_file, str):
            data_file = StandardTextFile(save_file, mode='wb')
        else:
            data_file = save_file
        try:
            data_file.write(data, metadata)
        finally:
            data_file.close()

    @property
    def pre(self):
        """
        The pre-population or population view.

        :rtype: ~spynnaker.pyNN.models.populations.PopulationBase
        """
        return self._synapse_information.pre_population

    @property
    def post(self):
        """
        The post-population or population view.

        :rtype: ~spynnaker.pyNN.models.populations.PopulationBase
        """
        return self._synapse_information.post_population

    @property
    def label(self):
        """
        :rtype: str
        """
        return self.__label

    def __repr__(self):
        return f"projection {self.__label}"

    # -----------------------------------------------------------------

    @property
    def _synapse_information(self) -> SynapseInformation:
        """
        :rtype: SynapseInformation
        """
        return self.__synapse_information

    @property
    def _projection_edge(self) -> ProjectionApplicationEdge:
        """
        :rtype: ProjectionApplicationEdge
        """
        return self.__projection_edge

    def _find_existing_edge(self, pre_synaptic_vertex, post_synaptic_vertex):
        """
        Searches though the graph's edges to locate any
        edge which has the same post- and pre- vertex

        :param pre_synaptic_vertex: the source vertex of the multapse
        :type pre_synaptic_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param post_synaptic_vertex: The destination vertex of the multapse
        :type post_synaptic_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :return: `None` or the edge going to these vertices.
        :rtype: ~.ApplicationEdge
        """
        # Find edges ending at the postsynaptic vertex
        partitions = (
            SpynnakerDataView.get_outgoing_edge_partitions_starting_at_vertex(
                pre_synaptic_vertex))

        # Partitions and Partition.edges will be OrderedSet but may be empty
        for partition in partitions:
            for edge in partition.edges:
                if edge.post_vertex == post_synaptic_vertex:
                    return edge

        return None

    def _get_synaptic_data(
            self, as_list, data_to_get, fixed_values=None, notify=None):
        """
        :param bool as_list:
        :param list(int) data_to_get:
        :param list(tuple(str,int)) fixed_values:
        :param callable(ConnectionHolder,None) notify:
        :rtype: ConnectionHolder
        """
        post_vertex = self.__projection_edge.post_vertex
        pre_vertex = self.__projection_edge.pre_vertex

        # If in virtual board mode, the connection data should be set
        if self.__virtual_connection_list is not None:
            connection_holder = ConnectionHolder(
                data_to_get, as_list, pre_vertex.n_atoms, post_vertex.n_atoms,
                self.__virtual_connection_list, fixed_values=fixed_values,
                notify=notify)
            connection_holder.finish()
            return connection_holder

        # if not virtual board, make connection holder to be filled in at
        # possible later date
        connection_holder = ConnectionHolder(
            data_to_get, as_list, pre_vertex.n_atoms, post_vertex.n_atoms,
            fixed_values=fixed_values, notify=notify)

        # If we haven't run, add the holder to get connections, and return it
        # and set up a callback for after run to fill in this connection holder
        if not SpynnakerDataView.is_ran_ever():
            self.__synapse_information.add_pre_run_connection_holder(
                connection_holder)
            return connection_holder

        # Otherwise, get the connections now, as we have ran and therefore can
        # get them
        connections = post_vertex.get_connections_from_machine(
            self.__projection_edge, self.__synapse_information)
        if connections is not None:
            connection_holder.add_connections(connections)
            connection_holder.finish()
        return connection_holder

    def _clear_cache(self):
        post_vertex = self.__projection_edge.post_vertex
        if isinstance(post_vertex, AbstractAcceptsIncomingSynapses):
            post_vertex.clear_connection_cache()

    # -----------------------------------------------------------------

    def set(self, **attributes):  # @UnusedVariable
        # pylint: disable=unused-argument
        """
        .. warning::
            Not implemented.
        """
        _we_dont_do_this_now()

    def getWeights(self, format='list',  # @ReservedAssignment
                   gather=True):
        """
        .. deprecated:: 5.0
            Use ``get('weight')`` instead.
        """
        logger.warning("getWeights is deprecated.  Use get('weight') instead")
        return self.get('weight', format, gather, with_address=False)

    def getDelays(self, format='list',  # @ReservedAssignment
                  gather=True):
        """
        .. deprecated:: 5.0
            Use ``get('delay')`` instead.
        """
        logger.warning("getDelays is deprecated.  Use get('delay') instead")
        return self.get('delay', format, gather, with_address=False)

    def getSynapseDynamics(self, parameter_name,
                           format='list',  # @ReservedAssignment
                           gather=True):
        """
        .. deprecated:: 5.0
            Use ``get(parameter_name)`` instead.
        """
        logger.warning(
            "getSynapseDynamics is deprecated. Use get(parameter_name)"
            " instead")
        return self.get(parameter_name, format, gather, with_address=False)

    def saveConnections(self, file,  # @ReservedAssignment
                        gather=True, compatible_output=True):
        """
        .. deprecated:: 5.0
            Use ``save('all')`` instead.
        """
        if not compatible_output:
            logger.warning("SpiNNaker only supports compatible_output=True.")
        logger.warning(
            "saveConnections is deprecated. Use save('all') instead")
        self.save('all', file, format='list', gather=gather)

    def printWeights(self, file, format='list',  # @ReservedAssignment
                     gather=True):
        """
        .. deprecated:: 5.0
            Use ``save('weight')`` instead.
        """
        logger.warning(
            "printWeights is deprecated. Use save('weight') instead")
        self.save('weight', file, format, gather)

    def printDelays(self, file, format='list',  # @ReservedAssignment
                    gather=True):
        """
        .. deprecated:: 5.0
            Use ``save('delay')`` instead.

        Print synaptic weights to file. In the array format, zeros are
        printed for non-existent connections.
        """
        logger.warning("printDelays is deprecated. Use save('delay') instead")
        self.save('delay', file, format, gather)

    def weightHistogram(self, min=None, max=None,  # @ReservedAssignment
                        nbins=10):
        """
        .. deprecated:: 5.0
            Use ``numpy.histogram`` on the weights instead.

        Return a histogram of synaptic weights.
        If ``min`` and ``max`` are not given, the minimum and maximum weights
        are calculated automatically.
        """
        logger.warning(
            "weightHistogram is deprecated. Use numpy.histogram function"
            " instead")
        pynn_common.Projection.weightHistogram(
            self, min=min, max=max, nbins=nbins)

    def size(self, gather=True):  # @UnusedVariable
        # pylint: disable=unused-argument
        """
        Return the total number of connections.

        .. note::
            SpiNNaker always gathers.
        .. warning::
            Not implemented.

        :param bool gather:
            If False, only get the number of connections locally.
        """
        # TODO
        _we_dont_do_this_now()
