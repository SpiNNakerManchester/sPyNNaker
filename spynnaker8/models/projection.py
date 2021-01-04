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

import logging
import functools
import numpy
from six import string_types
from pyNN import common as pynn_common, recording
from pyNN.space import Space as PyNNSpace
from spinn_utilities.logger_utils import warn_once
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnectorSupportsViewsOnMachine)
from spynnaker8.models.connectors import FromListConnector
from spynnaker8.models.synapse_dynamics import SynapseDynamicsStatic
# This line has to come in this order as it otherwise causes a circular
# dependency
from spynnaker.pyNN.models.pynn_projection_common import PyNNProjectionCommon
from spynnaker8.models.populations import Population, PopulationView
from spynnaker8._version import __version__

logger = logging.getLogger(__name__)


class Projection(PyNNProjectionCommon):
    """ sPyNNaker 8 projection class
    """
    # pylint: disable=redefined-builtin
    __slots__ = [
        "__simulator",
        "__label"]

    _static_synapse_class = SynapseDynamicsStatic

    def __init__(
            self, pre_synaptic_population, post_synaptic_population,
            connector, synapse_type=None, source=None,
            receptor_type=None, space=None, label=None):
        """
        :param ~spynnaker8.models.populations.PopulationBase \
                pre_synaptic_population:
        :param ~spynnaker8.models.populations.PopulationBase \
                post_synaptic_population:
        :param connector:
        :type connector:
            ~spynnaker.pyNN.models.neural_projections.connectors.AbstractConnector
        :param synapse_type:
        :type synapse_type:
            ~spynnaker.pyNN.models.neuron.synapse_dynamics.AbstractStaticSynapseDynamics
        :param None source: Unsupported; must be None
        :param str receptor_type:
        :param ~pyNN.space.Space space:
        :param str label:
        """
        # pylint: disable=too-many-arguments
        if source is not None:
            raise InvalidParameterType(
                "sPyNNaker8 {} does not yet support multi-compartmental "
                "cells.".format(__version__))

        self._check_population_param(pre_synaptic_population, connector)
        self._check_population_param(post_synaptic_population, connector)

        # set space object if not set
        if space is None:
            space = PyNNSpace()

        # set the simulator object correctly.
        self.__simulator = globals_variables.get_simulator()

        # set label
        self.__label = label
        if label is None:
            # set the projection's label here, but allow the edge label
            # to be set lower down if necessary
            self.__label = "from pre {} to post {} with connector {}".format(
                pre_synaptic_population.label, post_synaptic_population.label,
                connector)

        if synapse_type is None:
            synapse_type = SynapseDynamicsStatic()

        # set the space function as required
        connector.set_space(space)

        # as a from list connector can have plastic parameters, grab those (
        # if any and add them to the synapse dynamics object)
        if isinstance(connector, FromListConnector):
            synapse_plastic_parameters = connector.get_extra_parameters()
            if synapse_plastic_parameters is not None:
                for i, parameter in enumerate(
                        connector.get_extra_parameter_names()):
                    synapse_type.set_value(
                        parameter, synapse_plastic_parameters[:, i])

        # set rng if needed
        rng = None
        if hasattr(connector, "rng"):
            rng = connector.rng

        super(Projection, self).__init__(
            connector=connector, synapse_dynamics_stdp=synapse_type,
            target=receptor_type, spinnaker_control=self.__simulator,
            pre_synaptic_population=pre_synaptic_population,
            post_synaptic_population=post_synaptic_population,
            prepop_is_view=isinstance(pre_synaptic_population,
                                      PopulationView),
            postpop_is_view=isinstance(post_synaptic_population,
                                       PopulationView),
            rng=rng, machine_time_step=self.__simulator.machine_time_step,
            label=label, time_scale_factor=self.__simulator.time_scale_factor)

    def _check_population_param(self, param, connector):
        if isinstance(param, Population):
            return  # Projections definitely work from Populations
        if not isinstance(param, PopulationView):
            raise ConfigurationException(
                "Unexpected parameter type {}. Expected Population".format(
                    type(param)))
        if not isinstance(connector, AbstractConnectorSupportsViewsOnMachine):
            raise NotImplementedError(
                "Projections over views not currently supported with the {}"
                .format(connector))
        # Check whether the array is contiguous or not
        inds = param._indexes
        if inds != tuple(range(inds[0], inds[-1] + 1)):
            raise NotImplementedError(
                "Projections over views only work on contiguous arrays, "
                "e.g. view = pop[n:m], not view = pop[n,m]")
        # Projection is compatible with PopulationView

    def __len__(self):
        raise NotImplementedError

    def set(self, **attributes):
        """ NOT IMPLEMENTED """
        raise NotImplementedError

    def get(self, attribute_names, format,  # @ReservedAssignment
            gather=True, with_address=True, multiple_synapses='last'):
        """ Get a parameter for PyNN 0.8

        :param attribute_names: list of attributes to gather
        :type attribute_names: str or iterable(str)
        :param str format: ``"list"`` or ``"array"``
        :param bool gather: gather over all nodes

            .. note::
                SpiNNaker always gathers.

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

        return self._get_data(
            attribute_names, format, with_address, multiple_synapses)

    def _get_data(
            self, attribute_names, format,  # @ReservedAssignment
            with_address, multiple_synapses='last', notify=None):
        """ Internal data getter to add notify option
        """
        # pylint: disable=too-many-arguments
        if multiple_synapses != 'last':
            raise ConfigurationException(
                "sPyNNaker only recognises multiple_synapses == last")

        # fix issue with 1 versus many
        if isinstance(attribute_names, string_types):
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

    def __iter__(self):
        raise NotImplementedError

    def getWeights(self, format='list',  # @ReservedAssignment
                   gather=True):
        """ DEPRECATED """
        logger.warning("getWeights is deprecated.  Use get('weight') instead")
        return self.get('weight', format, gather, with_address=False)

    def getDelays(self, format='list',  # @ReservedAssignment
                  gather=True):
        """ DEPRECATED """
        logger.warning("getDelays is deprecated.  Use get('delay') instead")
        return self.get('delay', format, gather, with_address=False)

    def getSynapseDynamics(self, parameter_name,
                           format='list',  # @ReservedAssignment
                           gather=True):
        """ DEPRECATED """
        logger.warning(
            "getSynapseDynamics is deprecated. Use get(parameter_name)"
            " instead")
        return self.get(parameter_name, format, gather, with_address=False)

    def saveConnections(self, file,  # @ReservedAssignment
                        gather=True, compatible_output=True):
        """ DEPRECATED """
        if not compatible_output:
            logger.warning("SpiNNaker only supports compatible_output=True.")
        logger.warning(
            "saveConnections is deprecated. Use save('all') instead")
        self.save('all', file, format='list', gather=gather)

    def printWeights(self, file, format='list',  # @ReservedAssignment
                     gather=True):
        """ DEPRECATED """
        logger.warning(
            "printWeights is deprecated. Use save('weight') instead")
        self.save('weight', file, format, gather)

    def printDelays(self, file, format='list',  # @ReservedAssignment
                    gather=True):
        """ DEPRECATED

            Print synaptic weights to file. In the array format, zeros are\
            printed for non-existent connections.
        """
        logger.warning("printDelays is deprecated. Use save('delay') instead")
        self.save('delay', file, format, gather)

    def weightHistogram(self, min=None, max=None,  # @ReservedAssignment
                        nbins=10):
        """ DEPRECATED

            Return a histogram of synaptic weights.\
            If min and max are not given, the minimum and maximum weights are\
            calculated automatically.
        """
        logger.warning(
            "weightHistogram is deprecated. Use numpy.histogram function"
            " instead")
        pynn_common.Projection.weightHistogram(
            self, min=min, max=max, nbins=nbins)

    def __save_callback(self, save_file, metadata, data):
        # Convert structured array to normal numpy array
        if hasattr(data, "dtype") and hasattr(data.dtype, "names"):
            dtype = [(name, "<f8") for name in data.dtype.names]
            data = data.astype(dtype)
        data = numpy.nan_to_num(data)
        if isinstance(save_file, string_types):
            data_file = recording.files.StandardTextFile(save_file, mode='wb')
        else:
            data_file = save_file
        try:
            data_file.write(data, metadata)
        finally:
            data_file.close()

    def save(
            self, attribute_names, file, format='list',  # @ReservedAssignment
            gather=True, with_address=True):
        """ Print synaptic attributes (weights, delays, etc.) to file. In the\
            array format, zeros are printed for non-existent connections.\
            Values will be expressed in the standard PyNN units (i.e., \
            millivolts, nanoamps, milliseconds, microsiemens, nanofarads, \
            event per second).

        :param attribute_names:
        :type attribute_names: str or list(str)
        :param file: filename or open handle (which will be closed)
        :type file: str or pyNN.recording.files.BaseFile
        :param str format:
        :param bool gather: Ignored

            .. note::
                SpiNNaker always gathers.

        :param bool with_address:
        """
        if not gather:
            warn_once(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        if isinstance(attribute_names, string_types):
            attribute_names = [attribute_names]
        # pylint: disable=too-many-arguments
        if attribute_names in (['all'], ['connections']):
            attribute_names = \
                self._projection_edge.post_vertex.synapse_dynamics.\
                get_parameter_names()
        metadata = {"columns": attribute_names}
        if with_address:
            metadata["columns"] = ["i", "j"] + list(metadata["columns"])
        self._get_data(
            attribute_names, format, with_address,
            notify=functools.partial(self.__save_callback, file, metadata))

    @property
    def pre(self):
        """ The pre-population.

        :rtype: PopulationBase
        """
        return self._synapse_information.pre_population

    @property
    def post(self):
        """ The post-population.

        :rtype: PopulationBase
        """
        return self._synapse_information.post_population

    @property
    def label(self):
        """
        :rtype: str
        """
        return self.__label

    def __repr__(self):
        return "projection {}".format(self.__label)
