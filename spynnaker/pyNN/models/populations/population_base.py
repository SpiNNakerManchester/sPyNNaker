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
from __future__ import annotations
import logging
from typing import (
    Any, Callable, Dict, final, Optional, Sequence, Tuple, TYPE_CHECKING,
    Union)

from pyNN.space import BaseStructure
import neo
from numpy import floating
from numpy.typing import NDArray
from typing_extensions import Never

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once

from pacman.model.graphs.application import ApplicationVertex

from spynnaker.pyNN.models.recorder import Recorder
from spynnaker.pyNN.types import IoDest

if TYPE_CHECKING:
    from pyNN.neuron.standardmodels.electrodes import NeuronCurrentSource
    from spynnaker.pyNN.models.common.types import Names
    from .population_view import IDMixin

logger = FormatAdapter(logging.getLogger(__name__))


class PopulationBase(object, metaclass=AbstractBase):
    r"""
    Shared methods between :py:class:`Population`\ s and
    :py:class:`PopulationView`\ s.

    Mainly pass through and not implemented.
    """
    __slots__ = ()

    @property
    def local_cells(self) -> Sequence[IDMixin]:
        """
        An array containing the cell IDs of those neurons in the
        Population that exist on the local MPI node.
        """
        logger.warning("local calls do not really make sense on sPyNNaker so "
                       "local_cells just returns all_cells")
        return self.all_cells

    @property
    @abstractmethod
    def all_cells(self) -> Sequence[IDMixin]:
        """
        An array containing the cell IDs of all neurons in the
        Population (all MPI nodes).
        """
        raise NotImplementedError

    @final
    def __add__(self, other: PopulationBase) -> Never:  # pylint: disable=W0613
        """
        A Population / PopulationView can be added to another
        Population, PopulationView or Assembly, returning an Assembly.

        .. warning::
            Currently unimplemented.

        :param other:
        """
        raise NotImplementedError("sPyNNaker does not support Assemblies")

    @abstractmethod
    def get_data(
            self, variables: Names = 'all',
            gather: bool = True, clear: bool = False, *,
            annotations: Optional[Dict[str, Any]] = None) -> neo.Block:
        """
        Return a Neo Block containing the data(spikes, state variables)
        recorded from the Population.

        :param variables:
            Either a single variable name or a list of variable names.
            Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :param gather: Ignored. Purely for PyNN compatibility

            .. note::
                SpiNNaker always gathers.

        :param clear:
            If this is True, recorded data will be deleted from the Population.
        :param annotations: annotations to put on the neo block
        :returns: Data in neo format
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the variable or variables have not been previously set to
            record.
        """
        raise NotImplementedError

    @abstractmethod
    def get_spike_counts(self, gather: bool = True) -> Dict[int, int]:
        """
        Returns a dict containing the number of spikes for each neuron.

        The dict keys are neuron IDs, not indices.

        :param gather: Ignored. Purely for PyNN compatibility

            .. note::
                SpiNNaker always gathers.
        :returns: A dict containing the number of spikes for each neuron.
        """
        raise NotImplementedError

    def inject(self, current_source: NeuronCurrentSource) -> None:
        """
        Connect a current source to all cells in the Population.

        :param current_source:
        """
        raise NotImplementedError

    @final
    def is_local(self, id: int) -> bool:  # @ReservedAssignment
        """
        Indicates whether the cell with the given ID exists on the
        local MPI node.

        :returns: True
        """
        # pylint: disable=redefined-builtin
        _ = id
        logger.warning("local calls do not really make sense on sPyNNaker so "
                       "is_local always returns True")
        return True

    @property
    @final
    def local_size(self) -> int:
        """
        The number of cells in the population on the local MPI node.
        """
        logger.warning("local calls do not really make sense on sPyNNaker so "
                       "is_local always returns size")
        return len(self)

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    def mean_spike_count(self, gather: bool = True) -> float:
        """
        :param gather: Ignored. Purely for PyNN compatibility

            .. note::
                SpiNNaker always gathers.
        :returns: The mean number of spikes per neuron.
        """
        if not gather:
            warn_once(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        counts = self.get_spike_counts()
        return sum(counts.values()) / len(counts)

    @final
    def nearest(
            self, position: Any) -> Never:
        """
        Return the neuron closest to the specified position.

        .. warning::
            Currently unimplemented.
        """
        _ = position
        raise NotImplementedError("sPyNNaker does not currently do nearest")

    @property
    @abstractmethod
    def position_generator(self) -> Callable[[int], NDArray[floating]]:
        """
        Returns a function to get the position for single id
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def positions(self) -> NDArray[floating]:
        """
        The position array for structured populations.

        This will be a 3xN array
        """
        raise NotImplementedError

    @abstractmethod
    def write_data(self, io: Union[str, neo.baseio.BaseIO],
                   variables: Names = 'all',
                   gather: bool = True, clear: bool = False,
                   annotations: Optional[Dict[str, Any]] = None) -> None:
        """
        Write recorded data to file, using one of the file formats
        supported by Neo.

        :param io:
            a Neo IO instance, or a string for where to put a Neo instance
        :param variables:
            either a single variable name or a list of variable names.
            Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :param gather: Ignored. Purely for PyNN compatibility

            .. note::
                SpiNNaker always gathers.

        :param clear:
            clears the storage data if set to true after reading it back
        :param annotations: annotations to put on the Neo block
        """
        raise NotImplementedError

    @final
    def receptor_types(self) -> Never:
        """
        .. note::
            NO PyNN description of this method.

        .. warning::
            Currently unimplemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def record(self, variables: Names, to_file: IoDest = None,
               sampling_interval: Optional[int] = None) -> None:
        """
        Record the specified variable or variables for all cells in the
        Population or view.

        :param variables: either a single variable name or a list of variable
            names. For a given `celltype` class, `celltype.recordable` contains
            a list of variables that can be recorded for that `celltype`.
        :param to_file: a file to automatically record to (optional).
            `write_data()` will be automatically called when `end()` is called.
        :param sampling_interval: a value in milliseconds, and an integer
            multiple of the simulation timestep.
        """
        raise NotImplementedError

    @final
    def save_positions(self, file: Any) -> Never:  # pylint: disable=W0622
        """
        Save positions to file. The output format is index x y z

        .. warning::
            Currently unimplemented.
        """
        _ = file
        raise NotImplementedError

    @property
    @abstractmethod
    def structure(self) -> Optional[BaseStructure]:
        """
        The spatial structure of the parent Population.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _vertex(self) -> ApplicationVertex:
        """
        The underlying application vertex.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _view_range(self) -> Tuple[int, int]:
        """
        The range of neuron IDs supported.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _recorder(self) -> Recorder:
        """
        The recorder of the population.
        """
        raise NotImplementedError

    @staticmethod
    def _check_params(gather: bool,
                      annotations: Optional[Dict[str, Any]] = None) -> None:
        if not gather:
            logger.warning(
                "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        if annotations is not None:
            warn_once(
                logger, "annotations parameter is not standard PyNN so may "
                        "not be supported by all platforms.")
