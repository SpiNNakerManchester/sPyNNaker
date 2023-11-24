# Copyright (c) 2021 The University of Manchester
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
from typing import (
    Iterator, List, Optional, Set, Tuple, Type, Union, TYPE_CHECKING)
from spinn_utilities.log import FormatAdapter
from spinn_front_end_common.data import FecDataView
from spynnaker import _version
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
if TYPE_CHECKING:
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.populations import Population

logger = FormatAdapter(logging.getLogger(__name__))
# pylint: disable=protected-access


class _SpynnakerDataModel(object):
    """
    Singleton data model.

    This class should not be accessed directly please use the DataView and
    DataWriter classes.
    Accessing or editing the data held here directly is *not supported!*

    There are other DataModel classes which sit next to this one and hold
    additional data. The DataView and DataWriter classes will combine these
    as needed.

    What data is held where and how can change without notice.
    """

    __singleton: Optional['_SpynnakerDataModel'] = None

    __slots__ = (
        # Data values cached
        "_id_counter",
        "_min_delay",
        "_neurons_per_core_set",
        "_populations",
        "_projections",
        "_segment_counter")

    def __new__(cls) -> '_SpynnakerDataModel':
        if cls.__singleton is not None:
            return cls.__singleton
        # pylint: disable=protected-access
        obj = object.__new__(cls)
        cls.__singleton = obj
        obj._clear()
        return obj

    def _clear(self) -> None:
        """
        Clears out all data.
        """
        self._id_counter = 0
        self._min_delay: Optional[float] = None
        # Using a dict to verify if later could be stored here only
        self._neurons_per_core_set: Set[Type[AbstractPyNNModel]] = set()
        self._populations: List[Population] = []
        self._projections: List[Projection] = []
        self._segment_counter = 0

    def _hard_reset(self) -> None:
        """
        Puts all data back into the state expected at graph changed and
        `sim.reset`.
        """
        self._soft_reset()

    def _soft_reset(self) -> None:
        """
        Puts all data back into the state expected at `sim.reset` but not
        graph changed.
        """
        # segment_counter is increased by the writer


class SpynnakerDataView(FecDataView):
    """
    Adds the extra Methods to the View for PyNN level.

    See :py:class:`~spinn_utilities.data.UtilsDataView` for a more detailed
    description.

    Use this class wherever possible as it inherits all methods from all View
    classes.
    """
    # pylint: disable=attribute-defined-outside-init

    __spy_data = _SpynnakerDataModel()

    __slots__ = ()

    @classmethod
    def get_min_delay(cls) -> float:
        """
        The minimum supported delay if available, in milliseconds.

        Typically `simulation_time_step_per_ms` but may be a positive multiple
        of it.

        :rtype: float
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the min_delay is currently unavailable
        """
        if cls.__spy_data._min_delay is not None:
            return cls.__spy_data._min_delay
        return cls.get_simulation_time_step_ms()

    @classmethod
    def has_min_delay(cls) -> bool:
        """
        Report if there is a minimum supported delay available.

        :rtype: bool
        """
        if cls.__spy_data._min_delay is not None:
            return True
        return cls.has_time_step()

    @classmethod
    def iterate_projections(cls) -> Iterator[Projection]:
        """
        An iteration of the projections previously added.

        The iteration will be empty if no projections added.

        :rtype: iterable(Projection)
        """
        return iter(cls.__spy_data._projections)

    @classmethod
    def get_n_projections(cls) -> int:
        """
        The number of projections previously added.

        rtype: int
        """
        return len(cls.__spy_data._projections)

    @classmethod
    def add_projection(cls, projection: Projection):
        """
        Called by each projection to add itself to the list.

        Usage other than from `Projection.__init__` is not supported and likely
        to raise an exception

        :param ~spynnaker.pyNN.models.projection.Projection projection:
            Projection to add
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If projections should not be added in the current state
        """
        # UGLY but needed to avoid circular import
        from spynnaker.pyNN.models.projection import Projection as Proj
        cls.check_user_can_act()
        if projection in cls.__spy_data._projections:
            raise NotImplementedError(
                "This method should only be called from the Projection init")
        if not isinstance(projection, Proj):
            raise TypeError("The projection must be a Projection")
        cls.__spy_data._projections.append(projection)

    @classmethod
    def iterate_populations(cls) -> Iterator[Population]:
        """
        An iteration of the populations previously added.

        The iteration will be empty if no populations added.

        :rtype: iterable(~spynnaker.pyNN.models.populations.Population)
        """
        return iter(cls.__spy_data._populations)

    @classmethod
    def get_n_populations(cls) -> int:
        """
        The number of populations previously added.

        :rtype: int
        """
        return len(cls.__spy_data._populations)

    @classmethod
    def add_population(cls, population: Population):
        """
        Called by each population to add itself to the list.

        Usage other than from `Population.__init__` is not supported and likely
        to raise an exception

        Increments the all population ID counter by the size of the population.

        :param ~spynnaker.pyNN.models.populations.Population population:
            Population to add
        :return: The first and last global IDs for this Population
        :rtype: tuple(int, int)
        :raises ~spinn_utilites.exceptions.SimulatorRunningException:
            If `sim.run` is currently running
        :raises ~spinn_utilites.exceptions.SimulatorNotSetupException:
            If called before `sim.setup`
        :raises ~spinn_utilites.exceptions.SimulatorShutdownException:
            If called after `sim.end`
        """
        # UGLY but needed to avoid circular import
        from spynnaker.pyNN.models.populations.population import (
            Population as Pop)
        cls.check_user_can_act()
        if not isinstance(population, Pop):
            raise TypeError("The population must be a Population")
        if population in cls.__spy_data._populations:
            raise NotImplementedError(
                "This method should only be called from the Population init")
        first_id = cls.__spy_data._id_counter
        cls.__spy_data._id_counter += population.size
        cls.__spy_data._populations.append(population)
        return first_id, cls.__spy_data._id_counter-1

    @classmethod
    def set_number_of_neurons_per_dimension_per_core(
            cls, neuron_type: Type[AbstractPyNNModel],
            max_permitted: Union[Tuple[int, ...], None]):
        """
        Sets a ceiling on the number of neurons of a given type that can be
        placed on a single core for each dimension.

        :param type neuron_type: neuron type
        :param max_permitted: the number to set to in each dimension
        :type max_permitted: tuple or None
        """
        cls.check_valid_simulator()
        if not issubclass(neuron_type, AbstractPyNNModel):
            raise TypeError(f"{neuron_type} is not an AbstractPyNNModel")

        neuron_type.set_model_max_atoms_per_dimension_per_core(max_permitted)
        cls.__spy_data._neurons_per_core_set.add(neuron_type)

    @classmethod
    def get_segment_counter(cls) -> int:
        """
        The number of the current recording segment being generated.

        :return: the segment counter
        :rtype: int
        """
        return cls.__spy_data._segment_counter

    @classmethod
    def get_sim_name(cls) -> str:
        """
        Gets the name to be returned by `pyNN.spiNNaker.name`.

        :rtype: str
        """
        return _version._NAME   # pylint: disable=protected-access
