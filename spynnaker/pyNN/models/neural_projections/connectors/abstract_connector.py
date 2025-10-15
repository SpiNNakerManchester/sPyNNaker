# Copyright (c) 2014 The University of Manchester
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
from __future__ import annotations
import logging
import math
import re
from typing import Dict, Optional, Sequence, Tuple, Union, TYPE_CHECKING
from typing_extensions import Never

import numpy
from numpy import float64, uint32, uint16, uint8
from numpy.typing import NDArray

from pyNN.random import NumpyRNG, RandomDistribution
from pyNN.space import Space

from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.safe_eval import SafeEval
from spinn_utilities.abstract_base import AbstractBase, abstractmethod

from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import Slice
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex

from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.types import (
    Delays, is_scalar, WeightsDelays, Weights)
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.exceptions import SpynnakerException

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.populations import Population, PopulationView

# global objects
logger = FormatAdapter(logging.getLogger(__name__))
_expr_context = SafeEval(
    math, numpy, numpy.arccos, numpy.arcsin, numpy.arctan, numpy.arctan2,
    numpy.ceil, numpy.cos, numpy.cosh, numpy.exp, numpy.fabs, numpy.floor,
    numpy.fmod, numpy.hypot, numpy.ldexp, numpy.log, numpy.log10, numpy.modf,
    numpy.power, numpy.sin, numpy.sinh, numpy.sqrt, numpy.tan, numpy.tanh,
    numpy.maximum, numpy.minimum, e=numpy.e, pi=numpy.pi)


class AbstractConnector(object, metaclass=AbstractBase):
    """
    Abstract class that all PyNN Connectors extend.
    """

    NUMPY_SYNAPSES_DTYPE = numpy.dtype(
        [("source", uint32), ("target", uint16),
         ("weight", float64), ("delay", float64),
         ("synapse_type", uint8)])

    __slots__ = (
        "__min_delay",
        "__n_clipped_delays",
        "__safe",
        "__space",
        "__verbose",
        "__param_seeds")

    def __init__(self, safe: bool = True, callback: None = None,
                 verbose: bool = False):
        """
        :param safe: if True, check that weights and delays have valid
            values. If False, this check is skipped. (NB: SpiNNaker always
            checks.)
        :param callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        if callback is not None:
            warn_once(logger, "sPyNNaker ignores connector callbacks.")
        self.__safe = safe
        self.__space: Optional[Space] = None
        self.__verbose = verbose

        self.__n_clipped_delays = numpy.int64(0)
        self.__min_delay = 0.0
        self.__param_seeds: Dict[Tuple[int, int], int] = dict()

    def set_space(self, space: Space) -> None:
        """
        Set the space object (allowed after instantiation).

        :param space:
        """
        self.__space = space

    def set_projection_information(
            self, synapse_info: SynapseInformation) -> None:
        """
        Sets a connectors projection info.

        :param synapse_info: the synapse info
        """
        _ = synapse_info
        self.__min_delay = SpynnakerDataView.get_simulation_time_step_ms()

    def _get_delay_minimum(
            self, delays: Delays, n_connections: int,
            synapse_info: SynapseInformation) -> float:
        """
        Get the minimum delay given a float or RandomDistribution.

        :param delays: the delays
        :param n_connections: how many connections
        """
        if isinstance(delays, RandomDistribution):
            low_estimated_delay = utility_calls.get_minimum_probable_value(
                delays, n_connections)
            low = utility_calls.low(delays)
            if low is None:
                return low_estimated_delay

            # The minimum is the maximum of the possible maximums
            return max(low_estimated_delay, low, 1)
        elif isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            return numpy.min(_expr_context.eval(delays, d=d))
        elif is_scalar(delays):
            return delays
        raise self.delay_type_exception(delays)

    def _get_delay_maximum(
            self, delays: Delays, n_connections: int,
            synapse_info: SynapseInformation) -> float:
        """
        Get the maximum delay given a float or RandomDistribution.
        """
        if isinstance(delays, RandomDistribution):
            max_estimated_delay = utility_calls.get_maximum_probable_value(
                delays, n_connections)
            high = utility_calls.high(delays)
            if high is None:
                return max_estimated_delay

            # The maximum is the minimum of the possible maximums
            return min(max_estimated_delay, high)
        elif isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            return numpy.max(_expr_context.eval(delays, d=d))
        elif is_scalar(delays):
            return delays
        raise self.delay_type_exception(delays)

    @abstractmethod
    def get_delay_maximum(
            self, synapse_info: SynapseInformation) -> float:
        """
        :param synapse_info: the synapse info
        :returns: The maximum delay specified by the user in ms,.
        """
        raise NotImplementedError

    @abstractmethod
    def get_delay_minimum(
            self, synapse_info: SynapseInformation) -> Optional[float]:
        """
        :param synapse_info:
        :returns: The minimum delay specified by the user in ms,
           or `None` if unbounded.
        """
        raise NotImplementedError

    def get_delay_variance(self, delays: Delays,
                           synapse_info: SynapseInformation) -> float:
        """
        :param delays:
        :param synapse_info: Info to get distances from (if needed)
        :returns: The variance of the delays.
        """
        if isinstance(delays, RandomDistribution):
            return utility_calls.get_variance(delays)
        elif isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            return numpy.var(_expr_context.eval(delays, d=d))
        elif is_scalar(delays):
            return 0.0
        raise self.delay_type_exception(delays)

    def _get_n_connections_from_pre_vertex_with_delay_maximum(
            self, delays: Delays, n_total_connections: int,
            n_connections: int, min_delay: float, max_delay: float,
            synapse_info: SynapseInformation) -> int:
        """
        :param delays:
        :param n_total_connections:
        :param n_connections:
        :param min_delay:
        :param max_delay:
        :returns: The expected number of delays
           that will fall within min_delay andmax_delay
           given a float, RandomDistribution or list of delays.
        """
        if isinstance(delays, RandomDistribution):
            prob_in_range = utility_calls.get_probability_within_range(
                delays, min_delay, max_delay)
            if prob_in_range > 0:
                v = int(math.ceil(utility_calls.get_probable_maximum_selected(
                    n_total_connections, n_connections, prob_in_range)))
                # If the probability is so low as to result in 0, assume
                # at least 1 if there is some probability that the delay is
                # in range
                return max(v, 1)
            else:
                return 0
        elif isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            delays = _expr_context.eval(delays, d=d)
            n_delayed = sum([len([
                delay for delay in delays
                if min_delay <= delay <= max_delay])])
            if n_delayed == 0:
                return 0
            n_total = len(delays)
            prob_delayed = float(n_delayed) / float(n_total)
            return int(math.ceil(utility_calls.get_probable_maximum_selected(
                n_total_connections, n_connections, prob_delayed)))
        elif is_scalar(delays):
            if min_delay <= delays <= max_delay:
                return int(math.ceil(n_connections))
            return 0
        raise self.delay_type_exception(delays)

    @abstractmethod
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        """
        Get the maximum number of connections from any
        neuron in the pre vertex to the neurons in the post_vertex_slice,
        for connections with a delay between min_delay and max_delay
        (inclusive) if both specified (otherwise all connections).

        Not all concrete connectors support omitting the delay range.

        :param n_post_atoms:
        :param synapse_info:
        :param min_delay:
        :param max_delay:
        :returns: maximum number of connections
        """
        raise NotImplementedError

    @abstractmethod
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        """
        :param synapse_info:
        :returns: The maximum number of connections to any neuron
        in the post vertex from neurons in the pre vertex.
        """
        raise NotImplementedError

    def get_weight_mean(self, weights: Weights,
                        synapse_info: SynapseInformation) -> float:
        """
        :param weights:
        :param synapse_info: Info to get distances from (if needed)
        :returns: The mean of the weights.
        """
        if isinstance(weights, RandomDistribution):
            return abs(utility_calls.get_mean(weights))
        elif isinstance(weights, str):
            d = self._get_distances(weights, synapse_info)
            return numpy.mean(_expr_context.eval(weights, d=d))
        elif is_scalar(weights):
            return abs(weights)
        raise self.weight_type_exception(synapse_info)

    def _get_weight_maximum(
            self, weights: Weights, n_connections: int,
            synapse_info: SynapseInformation) -> float:
        """
        Get the maximum of the weights.
        """
        if isinstance(weights, RandomDistribution):
            mean_weight = utility_calls.get_mean(weights)
            if mean_weight < 0:
                min_weight = utility_calls.get_minimum_probable_value(
                    weights, n_connections)
                low = utility_calls.low(weights)
                if low is None:
                    return abs(min_weight)
                return abs(max(min_weight, low))
            else:
                max_weight = utility_calls.get_maximum_probable_value(
                    weights, n_connections)
                high = utility_calls.high(weights)
                if high is None:
                    return abs(max_weight)
                return abs(min(max_weight, high))
        elif isinstance(weights, str):
            d = self._get_distances(weights, synapse_info)
            return numpy.max(_expr_context.eval(weights, d=d))
        elif is_scalar(weights):
            return abs(weights)
        raise self.weight_type_exception(weights)

    @abstractmethod
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        """
        :param synapse_info:
        :returns: The maximum of the weights for this connection.
        """
        raise NotImplementedError

    def get_weight_variance(self, weights: Weights,
                            synapse_info: SynapseInformation) -> float:
        """
        :param weights:
        :param synapse_info: Info to get distances from (if needed)
        :returns: The variance of the weights.
        """
        if isinstance(weights, RandomDistribution):
            return utility_calls.get_variance(weights)
        elif isinstance(weights, str):
            d = self._get_distances(weights, synapse_info)
            return numpy.var(_expr_context.eval(weights, d=d))
        elif is_scalar(weights):
            return 0.0
        raise self.weight_type_exception(weights)

    def _expand_distances(self, d_expression: str) -> bool:
        """
        Check if a distance expression contains at least one term `d[x]`.
        If yes, then the distances are expanded to distances in the
        separate coordinates rather than the overall distance over all
        coordinates, and we assume the user has specified an expression
        such as `d[0] + d[2]`.

        :param d_expression:
        """
        regexpr = re.compile(r'.*d\[\d*\].*')
        return bool(regexpr.match(d_expression))

    def _get_distances(self, values: str,
                       synapse_info: SynapseInformation) -> NDArray[float64]:
        if self.__space is None:
            raise self._no_space_exception(values, synapse_info)
        expand_distances = self._expand_distances(values)

        return self.__space.distances(
            synapse_info.pre_population.positions,
            synapse_info.post_population.positions,
            expand_distances)

    def _generate_random_values(
            self, values: RandomDistribution, n_connections: int,
            post_vertex_slice: Slice) -> NDArray[float64]:
        """
        :param values:
        :param n_connections:
        :param post_vertex_slice:
        """
        key = (id(post_vertex_slice), id(values))
        seed = self.__param_seeds.get(key, None)
        if seed is None:
            seed = int(values.rng.next() * 0x7FFFFFFF)
            self.__param_seeds[key] = seed
        new_rng = NumpyRNG(seed)
        copy_rd = RandomDistribution(
            values.name, parameters_pos=None, rng=new_rng,
            **values.parameters)
        if n_connections == 1:
            return numpy.array([copy_rd.next(1)], dtype=float64)
        return copy_rd.next(n_connections)

    def _no_space_exception(
            self, values: WeightsDelays,
            synapse_info: SynapseInformation) -> SpynnakerException:
        """
        :param values:
        :param synapse_info:
        :returns: A SpynnakerException about there being no space defined
        """
        return SpynnakerException(
            f"Str Weights or delays {values} are distance-dependent "
            f"but no space object was specified in projection "
            f"{synapse_info.pre_population}-"
            f"{synapse_info.post_population}")

    def weight_type_exception(
            self, weights: Weights) -> SpynnakerException:
        """
        :param weights:
        :returns: An Exception explaining incorrect weight or delay type
        """
        if weights is None:
            return SpynnakerException(
                f"The Synapse used is not is not supported with a "
                f"{(type(self))} as neither provided weights")
        elif isinstance(weights, str):
            return SpynnakerException(
                f"Str Weights {weights} not supported by a {(type(self))}")
        elif isinstance(weights, numpy.ndarray):
            # The problem is that these methods are for a MachineVertex/ core
            # while weight and delay are supplied at the application level
            # The FromList is also the one designed to handle the 2D case
            return SpynnakerException(
                f"For efficiency reason {type(self)} does not supports "
                f"list or arrays for weight."
                f"Please use a FromListConnector instead")
        else:
            return SpynnakerException(f"Unrecognised weight {weights}")

    def delay_type_exception(self, delays: Delays) -> SpynnakerException:
        """
        :param delays:
        :returns: An Exception explaining incorrect delay type
        """
        if isinstance(delays, str):
            return SpynnakerException(
                f"Str delays {delays} not supported by {(type(self))}")
        elif isinstance(delays, numpy.ndarray):
            # The problem is that these methods are for a MachineVertex/ core
            # while weight and delay are supplied at the application level
            # The FromList is also the one designed to handle the 2D case
            return SpynnakerException(
                f"For efficiency reason {type(self)} does not supports "
                f"list or arrays for weight or delay."
                f"Please use a FromListConnector instead")
        else:
            return SpynnakerException(f"Unrecognised delay {delays}")

    def _generate_values(
            self, values: WeightsDelays, sources: numpy.ndarray,
            targets: numpy.ndarray, n_connections: int, post_slice: Slice,
            synapse_info: SynapseInformation,
            weights: bool) -> NDArray[float64]:
        if isinstance(values, RandomDistribution):
            return self._generate_random_values(
                values, n_connections, post_slice)
        elif isinstance(values, str) or callable(values):
            if self.__space is None:
                raise self._no_space_exception(values, synapse_info)

            expand_distances = True
            if isinstance(values, str):
                expand_distances = self._expand_distances(values)

                # At this point we need to now get the values corresponding to
                # the distances between connections in "sources" and "targets"
                eval_values = numpy.zeros(n_connections, dtype=float64)
                for i in range(n_connections):
                    # get the distance for this source and target pair
                    dist = self.__space.distances(
                        synapse_info.pre_population.positions[sources[i]],
                        synapse_info.post_population.positions[targets[i]],
                        expand_distances)
                    # evaluate expression at this distance
                    eval_values[i] = _expr_context.eval(values, d=dist)
                return eval_values

            d = self.__space.distances(
                synapse_info.pre_population.positions[sources[i]],
                synapse_info.post_population.positions[targets[i]],
                expand_distances)

            return values(d)
        elif is_scalar(values):
            return numpy.repeat([values], n_connections).astype(float64)
        if weights:
            raise self.weight_type_exception(values)
        else:
            raise self.delay_type_exception(values)

    def _generate_weights(
            self, sources: numpy.ndarray, targets: numpy.ndarray,
            n_connections: int, post_slice: Slice,
            synapse_info: SynapseInformation) -> numpy.ndarray:
        """
        Generate weight values.
        """
        weights = self._generate_values(
            synapse_info.weights, sources, targets, n_connections, post_slice,
            synapse_info, weights=True)
        if self.__safe:
            if not weights.size:
                warn_once(logger, "No connection in " + str(self))
            elif numpy.amin(weights) < 0 < numpy.amax(weights):
                raise SpynnakerException(
                    "Weights must be either all positive or all negative in "
                    f"projection {synapse_info.pre_population.label}->"
                    f"{synapse_info.post_population.label}")
        return numpy.abs(weights)

    def _clip_delays(self, delays: NDArray[float64]) -> NDArray[float64]:
        """
        Clip delay values, keeping track of how many have been clipped.
        """
        # count values that could be clipped
        self.__n_clipped_delays = numpy.sum(delays < self.__min_delay)

        # clip values
        if delays.size:
            delays[delays < self.__min_delay] = self.__min_delay
        return delays

    def _generate_delays(
            self, sources: numpy.ndarray, targets: numpy.ndarray,
            n_connections: int, post_slice: Slice,
            synapse_info: SynapseInformation) -> numpy.ndarray:
        """
        Generate valid delay values.
        """
        delays = self._generate_values(
            synapse_info.delays, sources, targets, n_connections, post_slice,
            synapse_info, weights=False)

        return self._clip_delays(delays)

    @staticmethod
    def __pop_label(pop: Union[Population, PopulationView]) -> str:
        lbl = pop.label
        if lbl is None:
            raise ValueError("unlabelled population")
        return lbl

    def get_provenance_data(self, synapse_info: SynapseInformation) -> None:
        """
        Adds the synapse information to provenance database.

        :param synapse_info:
        """
        # Convert to native Python integer; provenance system assumption
        ncd = self.__n_clipped_delays.item()
        with ProvenanceWriter() as db:
            db.insert_connector(
                self.__pop_label(synapse_info.pre_population),
                self.__pop_label(synapse_info.post_population),
                self.__class__.__name__, "Times_synaptic_delays_got_clipped",
                ncd)
            if ncd > 0:
                db.insert_report(
                    f"The delays in the connector {self.__class__.__name__} "
                    f"from {synapse_info.pre_population.label} "
                    f"to {synapse_info.post_population.label} "
                    f"was clipped to {self.__min_delay} a total of {ncd} "
                    f"times. This can be avoided by reducing the timestep or "
                    f"increasing the minimum delay to one timestep")

    @property
    def safe(self) -> bool:
        """
        Safe value supplied. Note ignored by sPyNNaker
        """
        return self.__safe

    @safe.setter
    def safe(self, new_value: bool) -> None:
        self.__safe = new_value

    @property
    def space(self) -> Optional[Space]:
        """
        The space object (may be updated after instantiation).
        """
        return self.__space

    @space.setter
    def space(self, new_value: Space) -> None:
        """
        Set the space object (allowed after instantiation).

        :param new_value:
        """
        self.__space = new_value

    @property
    def verbose(self) -> bool:
        """
        verbose value supplied by user
        """
        return self.__verbose

    @verbose.setter
    def verbose(self, new_value: bool) -> None:
        self.__verbose = new_value

    def get_connected_vertices(
            self, s_info: SynapseInformation, source_vertex: ApplicationVertex,
            target_vertex: ApplicationVertex) -> Sequence[
                Tuple[MachineVertex, Sequence[AbstractVertex]]]:
        """
        Get the machine vertices that are connected to each other with
        this connector

        :param s_info: The synapse information of the connection
        :param source_vertex: The source of the spikes
        :param target_vertex: The target of the spikes
        :return: A list of tuples of (target machine vertex, list of sources)
        """
        # By default, just return that the whole target connects to the
        # whole source
        return [(m_vertex, [source_vertex])
                for m_vertex in target_vertex.splitter.get_in_coming_vertices(
                    s_info.partition_id)]

    def connect(self, projection: Projection) -> Never:
        """
        Apply this connector to a projection.

        .. warning::
            Do *not* call this! SpyNNaker does not work that way.

        :param projection:
        :raises SpynnakerException: Always. Method not supported; profiled out.
        """
        raise SpynnakerException("Standard pyNN connect method not supported")

    @staticmethod
    def _roundsize(size: Union[int, float], label: str) -> int:
        """
        Ensures that the ``size`` is an integer. Approximate integers are
        rounded; other values cause exceptions.

        :param size: The value to be rounded
        :param label: The type-name of the connection, for messages
        :raises SpynnakerException: If the size is non-integer and not close
        """
        if isinstance(size, int):
            return size
        # Allow a float which has a near int value
        temp = int(round(size))
        if abs(temp - size) < 0.001:
            logger.warning("Size of {} rounded from {} to {}. "
                           "Please use int values for size",
                           label, size, temp)
            return temp
        raise SpynnakerException(
            f"Size of {label} must be an int, received {size}")

    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> None:
        """
        Checks that the edge supports the connector.  Returns nothing; it
        is assumed that an Exception will be raised if anything is wrong.

        By default this checks only that the views are not used
        on multi-dimensional vertices.

        :param application_edge: The edge of the connection
        :param synapse_info: The synaptic information
        """
        _ = application_edge
        if ((synapse_info.prepop_is_view and
                len(synapse_info.pre_vertex.atoms_shape) > 1) or
                (synapse_info.postpop_is_view and
                 len(synapse_info.post_vertex.atoms_shape) > 1)):
            raise ConfigurationException(
                "Using a projection where the source or target is a "
                "PopulationView on a multi-dimensional Population is not "
                "supported")
