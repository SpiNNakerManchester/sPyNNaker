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

from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.quick_test.test_onchip_compressor.many_bitfields \
    import do_bitfield_run


class TestPairBitFieldCompressorWithSettings(BaseTestCase):

    def test_do_run(self):
        self.runsafe(do_bitfield_run)
