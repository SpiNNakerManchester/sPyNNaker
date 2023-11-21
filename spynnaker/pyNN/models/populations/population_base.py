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
from pyNN.space import BaseStructure
import neo
from typing import (
    Any, Dict, Optional, Sequence, Tuple, Union, final,
    TYPE_CHECKING)
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once
from pacman.model.graphs.application import ApplicationVertex
from spynnaker.pyNN.models.recorder import Recorder
from .assembly import Assembly
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.abstract_population_vertex import (
        AbstractPopulationVertex)
    from pyNN.neuron.standardmodels.electrodes import NeuronCurrentSource
    from spynnaker.pyNN.models.common.types import Names
    from .population_view import IDMixin

logger = FormatAdapter(logging.getLogger(__name__))


def _we_dont_do_this_now(*args):  # pylint: disable=unused-argument
    # pragma: no cover
    raise NotImplementedError("sPyNNaker does not currently do this")


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

        :rtype: list(int)
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

        :rtype: list(int)
        """
        raise NotImplementedError

    def __add__(self, other: PopulationBase) -> Assembly:
        """
        A Population / PopulationView can be added to another
        Population, PopulationView or Assembly, returning an Assembly.

        .. warning::
            Currently unimplemented.

        :param PopulationBase other:
        :rtype: Assembly
        """
        # TODO: support assemblies
        _we_dont_do_this_now(other)  # pragma: no cover
        raise NotImplementedError

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
        :type variables: str or list(str)
        :param bool gather: For parallel simulators, if this is True, all data
            will be gathered to all nodes and the Neo Block will contain data
            from all nodes. Otherwise, the Neo Block will contain only data
            from the cells simulated on the local node.

            .. note::
                SpiNNaker always gathers.

        :param bool clear:
            If this is True, recorded data will be deleted from the Population.
        :param annotations: annotations to put on the neo block
        :type annotations: None or dict(str, ...)
        :rtype: ~neo.core.Block
        """
        raise NotImplementedError

    @abstractmethod
    def get_spike_counts(self, gather: bool = True) -> Dict[int, int]:
        """
        Returns a dict containing the number of spikes for each neuron.

        The dict keys are neuron IDs, not indices.

        :param bool gather:
            For parallel simulators, if this is True, all data will be gathered
            to all nodes and the Neo Block will contain data from all nodes.
            Otherwise, the Neo Block will contain only data from the cells
            simulated on the local node.

            .. note::
                SpiNNaker always gathers.

        :rtype: dict(int, int)
        """
        raise NotImplementedError

    def inject(self, current_source: NeuronCurrentSource):
        """
        Connect a current source to all cells in the Population.

        :param current_source:
        :type current_source:
            ~pyNN.neuron.standardmodels.electrodes.NeuronCurrentSource
        """
        raise NotImplementedError

    @final
    def is_local(self, id: int) -> bool:  # @ReservedAssignment
        """
        Indicates whether the cell with the given ID exists on the
        local MPI node.

        :rtype: bool
        """
        # pylint: disable=unused-argument, redefined-builtin
        logger.warning("local calls do not really make sense on sPyNNaker so "
                       "is_local always returns True")
        return True

    @property
    @final
    def local_size(self) -> int:
        """
        The number of cells in the population on the local MPI node.

        :rtype: int
        """
        logger.warning("local calls do not really make sense on sPyNNaker so "
                       "is_local always returns size")
        return len(self)

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    def mean_spike_count(self, gather=True):
        """
        Returns the mean number of spikes per neuron.

        :param bool gather:
            For parallel simulators, if this is True, all data will be gathered
            to all nodes and the Neo Block will contain data from all nodes.
            Otherwise, the Neo Block will contain only data from the cells
            simulated on the local node.

            .. note::
                SpiNNaker always gathers.

        :rtype: float
        """
        if not gather:
            warn_once(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        counts = self.get_spike_counts()
        return sum(counts.values()) / len(counts)

    def nearest(self, position):
        """
        Return the neuron closest to the specified position.

        .. warning::
            Currently unimplemented.
        """
        # TODO: support neuron positions and spaces
        _we_dont_do_this_now(position)  # pragma: no cover

    @property
    def position_generator(self):
        """
        .. note::
            NO PyNN description of this method.

        .. warning::
            Currently unimplemented.
        """
        # TODO: support neuron positions and spaces
        _we_dont_do_this_now()  # pragma: no cover

    @property
    def positions(self):
        """
        .. note::
            NO PyNN description of this method.

        .. warning::
            Currently unimplemented.

        :rtype: ~numpy.ndarray(tuple(float, float, float))
        """
        # TODO: support neuron positions and spaces
        _we_dont_do_this_now()  # pragma: no cover

    @abstractmethod
    def write_data(self, io: Union[str, neo.baseio.BaseIO],
                   variables: Names = 'all',
                   gather: bool = True, clear: bool = False,
                   annotations: Optional[Dict[str, Any]] = None):
        """
        Write recorded data to file, using one of the file formats
        supported by Neo.

        :param io:
            a Neo IO instance, or a string for where to put a Neo instance
        :type io: ~neo.io or ~neo.rawio or str
        :param variables:
            either a single variable name or a list of variable names.
            Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :type variables: str or list(str)
        :param bool gather: For parallel simulators, if this is True, all data
            will be gathered to all nodes and the Neo Block will contain data
            from all nodes. Otherwise, the Neo Block will contain only data
            from the cells simulated on the local node. This is pointless on
            sPyNNaker.

            .. note::
                SpiNNaker always gathers.

        :param bool clear:
            clears the storage data if set to true after reading it back
        :param annotations: annotations to put on the Neo block
        :type annotations: None or dict(str, ...)
        """
        # pylint: disable=too-many-arguments
        raise NotImplementedError

    def receptor_types(self):
        """
        .. note::
            NO PyNN description of this method.

        .. warning::
            Currently unimplemented.
        """
        _we_dont_do_this_now()  # pragma: no cover

    @abstractmethod
    def record(self, variables: Names, to_file=None,
               sampling_interval=None):
        """
        Record the specified variable or variables for all cells in the
        Population or view.

        :param variables: either a single variable name or a list of variable
            names. For a given `celltype` class, `celltype.recordable` contains
            a list of variables that can be recorded for that `celltype`.
        :type variables: str or list(str)
        :param to_file: a file to automatically record to (optional).
            `write_data()` will be automatically called when `end()` is called.
        :type to_file: ~neo.io or ~neo.rawio or str
        :param int sampling_interval: a value in milliseconds, and an integer
            multiple of the simulation timestep.
        """
        raise NotImplementedError

    def save_positions(self, file):  # pylint: disable=redefined-builtin
        """
        Save positions to file. The output format is index x y z

        .. warning::
            Currently unimplemented.
        """
        # TODO:
        _we_dont_do_this_now(file)  # pragma: no cover
        raise NotImplementedError

    @property
    def structure(self) -> BaseStructure:
        """
        The spatial structure of the parent Population.

        .. warning::
            Currently unimplemented.

        :rtype: ~pyNN.space.BaseStructure
        """
        # TODO: support neuron positions and spaces
        _we_dont_do_this_now()  # pragma: no cover
        raise NotImplementedError

    @property
    @abstractmethod
    def _vertex(self) -> ApplicationVertex:
        """
        The underlying application vertex.

        :rtype: ~pacman.model.graphs.application.ApplicationVertex
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

        :rtype: ~Recorder
        """
        raise NotImplementedError

    @staticmethod
    def _check_params(gather, annotations=None):
        if not gather:
            logger.warning(
                "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        if annotations is not None:
            warn_once(
                logger, "annotations parameter is not standard PyNN so may "
                        "not be supported by all platforms.")
