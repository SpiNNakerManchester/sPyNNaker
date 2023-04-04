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

from spynnaker.pyNN.models.populations import PopulationView as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class PopulationView(_BaseClass):
    """
    A view of a subset of neurons within a
    :py:class:`~spynnaker.pyNN.models.populations.Population`.

    In most ways, Populations and PopulationViews have the same behaviour,
    i.e., they can be recorded, connected with Projections, etc.
    It should be noted that any changes to neurons in a PopulationView
    will be reflected in the parent Population and *vice versa.*

    It is possible to have views of views.

    .. note::
        Selector to Id is actually handled by :py:class:`AbstractSized`.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.populations.PopulationView` instead.
    """
    __slots__ = []

    def __init__(self, parent, selector, label=None):
        """
        :param parent: the population or view to make the view from
        :type parent: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
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
        :param str label: A label for the view
        """
        moved_in_v6("spynnaker8.models.populations.PopulationView",
                    "spynnaker.pyNN.models.populations.PopulationView")
        super(PopulationView, self).__init__(parent, selector, label)
