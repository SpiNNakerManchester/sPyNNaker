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
from .spynakker_data_model import SpynnakerDataModel


class SpynnakerDataView(FecDataView):
    """
    A read only view of the data available at Spynnaker level

    The property methods will either return a valid value or
    raise an Exception if the data is currently not available

    While how and where the underpinning DataModel(s) store data can change
    without notice, methods in this class can be considered a supported API
    """

    _spy_data = SpynnakerDataModel()

    __slots__ = []

    @property
    def min_delay(self):
        """ The minimum supported delay, in milliseconds.

        :rtype: int
        :raises SpinnFrontEndException:
            If the min_delay is currently unavailable
        """
        if self._spy_data._SpynnakerDataModel__min_delay is not None:
            return self._spy_data._SpynnakerDataModel__min_delay
        if self._fec_data._FecDataModel__machine_time_step is None:
            raise self.status.exception("min_delay")
        return self._fec_data._FecDataModel__machine_time_step

    def has_min_delay(self):
        if self._spy_data._SpynnakerDataModel__min_delay is not None:
            return True
        return self._fec_data._FecDataModel__machine_time_step is not None

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
            if self._spy_data.__SpynnakerDataModel___min_delay is not None:
                return self._spy_data.__SpynnakerDataModel___min_delay
            # In this case even if None
            return self._fec_data._FecDataModel__machine_time_step

        return super._unchecked_gettiem(self, item)
