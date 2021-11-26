# Copyright (c) 2020-2021 The University of Manchester
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
from pacman.operations.partition_algorithms import SplitterPartitioner
from data_specification import ReferenceContext


class SpynnakerSplitterPartitioner(SplitterPartitioner):
    """ a splitter partitioner that's bespoke for spynnaker vertices.
    """

    __slots__ = []

    def __call__(self, app_graph, plan_n_time_steps):
        """
        :param ApplicationGraph app_graph: app graph
        :param int plan_n_time_steps: the number of time steps to run for
        :rtype: int
        :raise PacmanPartitionException: when it cant partition
        """

        # do partitioning in same way, but in a context of references
        with ReferenceContext():
            chips_used = super().__call__(app_graph, plan_n_time_steps)

        # return the accepted things
        return chips_used
