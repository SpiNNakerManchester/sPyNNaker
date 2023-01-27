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

import csv
import os
import numpy
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from spynnaker.pyNN.utilities.neo_csv import NeoCsv


class TestCSV(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_v = os.path.join(my_dir, "v.csv")
        v_expected = []
        with open(my_v) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                row = list(map(lambda x: float(x), row))
                v_expected.append(row)
        cls.v_expected = numpy.array(v_expected)
        my_spikes = os.path.join(my_dir, "spikes.csv")
        spikes_expected = []
        with open(my_spikes) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                row = list(map(lambda x: float(x), row))
                spikes_expected.append((row[0], row[1]))
        cls.spikes_expected = numpy.array(spikes_expected)

    def test_write(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        my_csv = os.path.join(my_dir, "test.csv")
        with NeoBufferDatabase(my_buffer) as db:
            db.write_csv(my_csv, "pop_1", variables="all")
            pop = db.get_population("pop_1")
            neo = pop.get_data("all")
            neo = NeoCsv().read_csv(my_csv)

    def test_view(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        my_csv = os.path.join(my_dir, "test.csv")
        with NeoBufferDatabase(my_buffer) as db:
            #  packets-per-timestep data can not be extracted using a view
            db.write_csv(my_csv, "pop_1", variables=["spikes", "v"],
                         view_indexes=[2, 4, 7, 8])

    def test_spikes(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "all_data.sqlite3")
        my_csv = os.path.join(my_dir, "test.csv")
        with NeoBufferDatabase(my_buffer) as db:
            db.write_csv(my_csv, "pop_1", variables="spikes")

    def test_rewiring(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        my_buffer = os.path.join(my_dir, "rewiring_data.sqlite3")
        my_csv = os.path.join(my_dir, "test.csv")
        with NeoBufferDatabase(my_buffer) as db:
            db.write_csv(my_csv, "pop_1", variables="all")
