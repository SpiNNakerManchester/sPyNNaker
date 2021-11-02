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

from spinn_utilities.overrides import overrides
from spinn_front_end_common.data import FecDataView


class _SpynnakerDataModel(object):
    """
    Singleton data model

    This class should not be accessed directly please use the DataView and
    DataWriter classes.
    Accessing or editing the data held here directly is NOT SUPPORTED

    There are other DataModel classes which sit next to this one and hold
    additional data. The DataView and DataWriter classes will combine these
    as needed.

    What data is held where and how can change without notice.
    """

    __singleton = None

    __slots__ = [
        # Data values cached
        "_min_delay"
    ]

    def __new__(cls):
        if cls.__singleton:
            return cls.__singleton
        # pylint: disable=protected-access
        obj = object.__new__(cls)
        cls.__singleton = obj
        obj._clear()
        return obj

    def _clear(self):
        """
        Clears out all data
        """
        self._min_delay = None


class SpynnakerDataView(FecDataView):
    """
    A read only view of the data available at Spynnaker level

    The property methods will either return a valid value or
    raise an Exception if the data is currently not available

    While how and where the underpinning DataModel(s) store data can change
    without notice, methods in this class can be considered a supported API
    """

    __spy_data = _SpynnakerDataModel()

    __slots__ = []

    @property
    def min_delay(self):
        """ The minimum supported delay, in milliseconds.

        :rtype: int
        :raises SpinnFrontEndException:
            If the min_delay is currently unavailable
        """
        if self.__spy_data._min_delay is not None:
            return self.__spy_data._min_delay
        if self.has_machine_time_step():
            return self.machine_time_step
        raise self.status.exception("min_delay")

    def has_min_delay(self):
        if self.__spy_data._min_delay is not None:
            return True
        return self.has_machine_time_step()

    @overrides(FecDataView.items)
    def items(self):
        """
        Lists the keys of the data currently available.

        Keys exposed this way are limited to the ones needed for injection

        :return: List of the keys for which there is data
        :rtype: list(str)
        :raise KeyError:  Amethod this call depends on could raise this
            exception, but that indicates a programming mismatch
        """
        results = super.items(self)
        # MinDelay is not required for injection
        # ONLY included (possibly temporary) to show test extended method
        for key in ["MinDelay"]:
            item = self._unchecked_getitem(key)
            if item is not None:
                results.append((key, item))
        return results

    @overrides(FecDataView._unchecked_getitem)
    def _unchecked_getitem(self, item):
        # MinDelay is not required for injection
        # ONLY included (possibly temporary) to show test extended method
        if item == "MinDelay":
            if self.has_min_delay():
                return self.min_delay
            else:
                return None

        return FecDataView._unchecked_getitem(self, item)
