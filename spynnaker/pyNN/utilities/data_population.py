# Copyright (c) 2022 The University of Manchester
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
import numpy
from numpy import floating
from numpy.typing import NDArray
from pyNN.descriptions import TemplateEngine
from typing import (
    Any, Dict, Iterable, Optional, overload, Sequence, Union, TYPE_CHECKING)
import neo  # type: ignore[import]
from spinn_utilities.ranged.abstract_sized import AbstractSized, Selector
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.populations import Population
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from spynnaker.pyNN.utilities.utility_calls import get_neo_io
from spynnaker.pyNN.models.common.types import Names
if TYPE_CHECKING:
    from .neo_buffer_database import Annotations

logger = FormatAdapter(logging.getLogger(__file__))
_SELECTIVE_RECORDED_MSG = (
    "Getting data on a whole population when selective recording was "
    "active will result in only the recorded neurons being returned "
    "in numerical order and without repeats.")


class DataPopulation(object):
    __slots__ = (
        "__database_file",
        "__label",
        "_indexes",
        "_size")

    def __init__(self, database_file: str, label: str, indexes=None):
        self.__label = label
        self.__database_file = database_file
        # getting size right away also check the inputs or fails fast
        with NeoBufferDatabase(self.__database_file) as db:
            size = db.get_population_metadata(label)[0]
        self._size = size
        self._indexes = indexes

    @overrides(Population.write_data)
    def write_data(self, io: Union[str, neo.baseio.BaseIO],
                   variables: Names = 'all', gather: bool = True,
                   clear: bool = False, annotations: Annotations = None):
        # pylint: disable=protected-access
        Population._check_params(gather, annotations)
        if clear:
            logger.warning("Ignoring clear as supported in this mode")
        if isinstance(io, str):
            io = get_neo_io(io)
        data = self.get_data(variables)
        # write the neo block to the file
        io.write(bl=data)

    @overrides(Population.describe, adds_typing=True)
    def describe(self, template: str = None,
                 engine: Optional[Union[str, TemplateEngine]] = None
                 ) -> Union[str, Dict[str]]:
        if template is not None:
            logger.warning("Ignoring template as supported in this mode")
        if engine is not None:
            logger.warning("Ignoring engine as supported in this mode")
        with NeoBufferDatabase(self.__database_file) as db:
            _, _, description = db.get_population_metadata(self.label)
            return description

    @overrides(Population.get_data)
    def get_data(
            self, variables: Names = 'all',
            gather: bool = True, clear: bool = False, *,
            annotations: Optional[Dict[str, Any]] = None) -> neo.Block:
        # pylint: disable=protected-access
        Population._check_params(gather, annotations)
        if clear:
            logger.warning("Ignoring clear as supported in this mode")
        with NeoBufferDatabase(self.__database_file) as db:
            return db.get_full_block(
                self.__label, variables, self._indexes, annotations)

    @overrides(Population.spinnaker_get_data)
    def spinnaker_get_data(
            self, variable: str, as_matrix: bool = False,
            view_indexes: Optional[Sequence[int]] = None) -> NDArray[floating]:
        if view_indexes:
            return self[view_indexes].spinnaker_get_data(variable, as_matrix)
        with NeoBufferDatabase(self.__database_file) as db:
            return db.spinnaker_get_data(
                self.__label, variable, as_matrix, self._indexes)

    @overrides(Population.get_spike_counts)
    def get_spike_counts(self, gather: bool = True) -> Dict[int, int]:
        # pylint: disable=protected-access
        Population._check_params(gather)
        with NeoBufferDatabase(self.__database_file) as db:
            return db.get_spike_counts(self.__label, self._indexes)

    @overrides(Population.find_units)
    def find_units(self, variable: str) -> Optional[str]:
        with NeoBufferDatabase(self.__database_file) as db:
            (_, _, units) = db.get_recording_metadata(self.__label, variable)
        return units

    def __len__(self) -> int:
        return self._size

    @property
    def label(self) -> str:
        return self.__label

    @property
    def local_size(self) -> int:
        return self._size

    @property
    def size(self) -> int:
        return self._size

    @overload
    def id_to_index(self, id: int) -> int:  # @ReservedAssignment
        # pylint: disable=redefined-builtin
        ...

    @overload
    def id_to_index(
            self, id: Iterable[int]) -> Sequence[int]:  # @ReservedAssignment
        # pylint: disable=redefined-builtin
        ...

    @overrides(Population.id_to_index)
    def id_to_index(self, id: Union[int, Iterable[int]]
                    ) -> Union[int, Sequence[int]]:  # @ReservedAssignment
        # pylint: disable=redefined-builtin
        # assuming not called often so not caching first id
        with NeoBufferDatabase(self.__database_file) as db:
            _, first_id, _ = db.get_population_metadata(self.__label)
        last_id = self._size + first_id
        if not numpy.iterable(id):
            if not first_id <= id <= last_id:
                raise ValueError(
                    f"id should be in the range [{first_id},{last_id}], "
                    f"actually {id}")
            return int(id - first_id)  # assume IDs are consecutive
        return id - first_id

    @overload
    def index_to_id(self, index: int) -> int:
        ...

    @overload
    def index_to_id(self, index: Iterable[int]) -> Sequence[int]:
        ...

    @overrides(Population.index_to_id)
    def index_to_id(self, index: Union[int, Iterable[int]]
                    ) -> Union[int, Sequence[int]]:
        # assuming not called often so not caching first id
        with NeoBufferDatabase(self.__database_file) as db:
            _, first_id, _ = db.get_population_metadata(self.__label)
        if not numpy.iterable(index):
            if index >= self._size:
                raise ValueError(
                    f"indexes should be in the range [0,{self._size}],"
                    f" actually {index}")
            return int(index + first_id)
        # this assumes IDs are consecutive
        return index + first_id

    def __getitem__(self, index_or_slice: Selector) -> DataPopulation:
        """
        :param selector: a slice or numpy mask array.
            The mask array should either be a boolean array (ideally) of the
            same size as the parent,
            or an integer array containing cell indices,
            i.e. if `p.size == 5` then:

            ::

                PopulationView(p, array([False, False, True, False, True]))
                PopulationView(p, array([2, 4]))
                PopulationView(p, slice(2, 5, 2))

            will all create the same view.
        :type selector: None or slice or int or list(bool) or list(int) or
            ~numpy.ndarray(bool) or ~numpy.ndarray(int)
        :param index_or_slice:
        :return:
        """
        sized = AbstractSized(self._size)
        ids = sized.selector_to_ids(index_or_slice, warn=True)
        if self._indexes:
            indexes = [self._indexes[index] for index in ids]
        else:
            indexes = [range(self._size)[index] for index in ids]
        return DataPopulation(self.__database_file, self.__label, indexes)

    @overrides(Population.mean_spike_count)
    def mean_spike_count(self, gather: bool = True) -> float:
        Population._check_params(gather)  # pylint: disable=protected-access
        counts = self.get_spike_counts()
        return sum(counts.values()) / len(counts)
