import logging
import numpy
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utilities import globals_variables
from .abstract_connector import AbstractConnector
from spynnaker.pyNN.exceptions import InvalidParameterType

logger = logging.getLogger(__name__)

# Indices of the source and target in the connection list array
_SOURCE = 0
_TARGET = 1
_FIRST_PARAM = 2


class FromListConnector(AbstractConnector):
    """ Make connections according to a list.
    """
    __slots__ = [
        "_conn_list",
        "_column_names",
        "_sources",
        "_targets",
        "_weights",
        "_delays",
        "_extra_parameters",
        "_extra_parameter_names"]

    def __init__(self, conn_list, safe=True, verbose=False, column_names=None):
        """
        :param: conn_list:
            a list of tuples, one tuple for each connection. Each\
            tuple should contain at least::

                (pre_idx, post_idx)

            where pre_idx is the index (i.e. order in the Population,\
            not the ID) of the presynaptic neuron, and post_idx is\
            the index of the postsynaptic neuron.

            Additional items per synapse are acceptable but all synapses\
            should have the same number of items.
        """
        super(FromListConnector, self).__init__(safe, verbose)

        # Need to set column names first, as setter uses this
        self._column_names = column_names

        # Call the conn_list setter, as this sets the internal values
        self.conn_list = conn_list

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, delays):
        if self._delays is None:
            return numpy.max(delays)
        else:
            return numpy.max(self._delays)

    @overrides(AbstractConnector.get_delay_variance)
    def get_delay_variance(self, delays):
        if self._delays is None:
            return numpy.var(delays)
        else:
            return numpy.var(self._delays)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, delays, post_vertex_slice, min_delay=None, max_delay=None):

        mask = None
        if min_delay is None or max_delay is None or self._delays is None:
            mask = ((self._targets >= post_vertex_slice.lo_atom) &
                    (self._targets <= post_vertex_slice.hi_atom))
        elif self._delays is not None:
            mask = ((self._targets >= post_vertex_slice.lo_atom) &
                    (self._targets <= post_vertex_slice.hi_atom) &
                    (self._delays >= min_delay) &
                    (self._delays <= max_delay))
        if mask is None:
            sources = self._sources
        else:
            sources = self._sources[mask]
        if sources.size == 0:
            return 0
        max_targets = numpy.max(numpy.bincount(
            sources.astype('int64', copy=False)))

        # If no delays just return max targets as this is for all delays
        # If there are delays in the list, this was also handled above
        if min_delay is None or max_delay is None or self._delays is not None:
            return max_targets

        # If here, there must be no delays in the list, so use the passed in
        # ones
        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            delays, self._n_pre_neurons * self._n_post_neurons,
            max_targets, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self):
        if not len(self._targets):
            return 0
        # pylint: disable=too-many-arguments
        return numpy.max(numpy.bincount(
            self._targets.astype('int64', copy=False)))

    @overrides(AbstractConnector.get_weight_mean)
    def get_weight_mean(self, weights):
        if self._weights is None:
            return numpy.mean(weights)
        else:
            return numpy.mean(numpy.abs(self._weights))

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, weights):
        # pylint: disable=too-many-arguments
        if self._weights is None:
            return numpy.amax(weights)
        else:
            return numpy.amax(numpy.abs(self._weights))

    @overrides(AbstractConnector.get_weight_variance)
    def get_weight_variance(self, weights):
        # pylint: disable=too-many-arguments
        if self._weights is None:
            return numpy.var(weights)
        else:
            return numpy.var(numpy.abs(self._weights))

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, weights, delays, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type):
        # pylint: disable=too-many-arguments
        mask = ((self._sources >= pre_vertex_slice.lo_atom) &
                (self._sources <= pre_vertex_slice.hi_atom) &
                (self._targets >= post_vertex_slice.lo_atom) &
                (self._targets <= post_vertex_slice.hi_atom))
        sources = self._sources[mask]
        block = numpy.zeros(sources.size, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = sources
        block["target"] = self._targets[mask]
        # check that conn_list has weights, if not then use the value passed in
        connection_slices = None
        if self._weights is None:
            if sources.size:
                # create connection slices for this pre+post based on the mask
                connection_slices = [
                    slice(n, n+1) for n in range(mask.size) if mask[n]]
                block["weight"] = self._generate_weights(
                    weights, sources.size, connection_slices)
            else:
                block["weight"] = 0
        else:
            block["weight"] = self._weights[mask]
        # check that conn_list has delays, if not then use the value passed in
        if self._delays is None:
            if sources.size:
                # create connection slices for this pre+post based on the mask
                if connection_slices is None:
                    connection_slices = [
                        slice(n, n+1) for n in range(mask.size) if mask[n]]
                block["delay"] = self._generate_delays(
                    delays, sources.size, connection_slices)
            else:
                block["delay"] = 0
        else:
            block["delay"] = self._clip_delays(self._delays[mask])
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "FromListConnector(n_connections={})".format(
            len(self._sources))

    @property
    def conn_list(self):
        return self._conn_list

    @conn_list.setter
    def conn_list(self, conn_list):
        if conn_list is None or not len(conn_list):
            self._conn_list = numpy.zeros((0, 2), dtype="uint32")
        else:
            self._conn_list = numpy.array(conn_list)

        # If the shape of the conn_list is 2D, numpy has been able to create
        # a 2D array which means every entry has the same number of values.
        # If this was not possible, raise an exception!
        if len(self._conn_list.shape) != 2:
            raise InvalidParameterType(
                "Each tuple in the connection list for the"
                " FromListConnector must have the same number of elements")

        # This tells us how many columns are in the list
        n_columns = self._conn_list.shape[1]
        if n_columns < 2:
            raise InvalidParameterType(
                "Each tuple in the connection list for the"
                " FromListConnector must have at least 2 elements")
        if (self._column_names is not None and
                n_columns != len(self._column_names) + _FIRST_PARAM):
            raise InvalidParameterType(
                "The number of column names must match the number of"
                " additional elements in each tuple in the connection list,"
                " not including the pre_idx or post_idx")

        # Get the column names if not specified
        column_names = self._column_names
        if self._column_names is None:
            if n_columns == 4:
                column_names = ('weight', 'delay')
            elif n_columns == 2:
                column_names = ()
            else:
                raise TypeError(
                    "Need to set 'column_names' for n_columns={}".format(
                        n_columns))

        # Set the source and targets
        self._sources = self._conn_list[:, _SOURCE]
        self._targets = self._conn_list[:, _TARGET]

        # Find any weights
        self._weights = None
        try:
            weight_column = column_names.index('weight') + _FIRST_PARAM
            self._weights = self._conn_list[:, weight_column]
        except ValueError:
            pass

        # Find any delays
        self._delays = None
        try:
            delay_column = column_names.index('delay') + _FIRST_PARAM
            machine_time_step = globals_variables.get_simulator(
                ).machine_time_step
            self._delays = numpy.rint(
                numpy.array(self._conn_list[:, delay_column]) * (
                    1000.0 / machine_time_step)) * (machine_time_step / 1000.0)
        except ValueError:
            pass

        # Find extra columns
        extra_columns = list()
        for i, name in enumerate(column_names):
            if name not in ('weight', 'delay'):
                extra_columns.append(i + _FIRST_PARAM)

        # Check any additional parameters have single values over the whole
        # set of connections (as other things aren't currently supported
        for i in extra_columns:
            # numpy.ptp gives the difference between the maximum and
            # minimum values of an array, so if 0, all values are equal
            if numpy.ptp(self._conn_list[:, i]):
                raise ValueError(
                    "All values in column {} ({}) of a FromListConnector must"
                    " have the same value".format(
                        i, column_names[i - _FIRST_PARAM]))

        # Store the extra data
        self._extra_parameters = None
        self._extra_parameter_names = None
        if extra_columns:
            self._extra_parameters = self._conn_list[:, extra_columns]
            self._extra_parameter_names = [
                column_names[i - _FIRST_PARAM] for i in extra_columns]

    @property
    def column_names(self):
        return self._column_names

    @column_names.setter
    def column_names(self, column_names):
        self._column_names = column_names

    def get_extra_parameters(self):
        """ Getter for the extra parameters.

        :return: The extra parameters
        """
        return self._extra_parameters

    def get_extra_parameter_names(self):
        """ Getter for the names of the extra parameters
        """
        return self._extra_parameter_names
