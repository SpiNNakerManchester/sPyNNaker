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
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD


class AbstractConnectorSupportsViewsOnMachine(object):
    """ Connector that generates on machine and supports using PopulationViews
    """

    N_VIEWS_PARAMS = 4

    __slots__ = ()

    def get_view_lo_hi(self, indexes):
        """ Get the low and high index values of the PopulationView

        :param list(int) indexes: the indexes array of a PopulationView
        :return: The low and high index values of the PopulationView
        :rtype: uint, uint
        """
        view_lo = indexes[0]
        view_hi = indexes[-1]
        return view_lo, view_hi

    def _basic_connector_params(self, synapse_info):
        """
        :param SynapseInformation synapse_info:
        :rtype: list(int)
        """
        params = []

        pre_view_lo = 0
        pre_view_hi = synapse_info.n_pre_neurons - 1
        if synapse_info.prepop_is_view:
            pre_view_lo, pre_view_hi = self.get_view_lo_hi(
                # pylint: disable=protected-access
                synapse_info.pre_population._indexes)
        params.extend([pre_view_lo, pre_view_hi])

        post_view_lo = 0
        post_view_hi = synapse_info.n_post_neurons - 1
        if synapse_info.postpop_is_view:
            post_view_lo, post_view_hi = self.get_view_lo_hi(
                # pylint: disable=protected-access
                synapse_info.post_population._indexes)
        params.extend([post_view_lo, post_view_hi])

        return params

    @property
    def _view_params_bytes(self):
        return self.N_VIEWS_PARAMS * BYTES_PER_WORD
