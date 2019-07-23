# Copyright (c) 2019-2020 The University of Manchester
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

#ifndef _DIRECT_SYNAPSES_H_
#define _DIRECT_SYNAPSES_H_

//! \brief setup for the direct synapses
//! \param[in] direct_matrix_address: the sdram base address for the direct
//                                    matrix
//! \param[out]: direct_synapses_address: the dtcm address for the direct matrix
//! \return: bool, that states true if successful, false otherwise.
bool direct_synapses_initialise(
    address_t direct_matrix_address, address_t *direct_synapses_address);

//! \brief returns the synapse for a given direct synaptic row.
// \param[in] row_address: the row address to read.
//! \return the synaptic row.
synaptic_row_t direct_synapses_get_direct_synapse(address_t row_address);

#endif /* _DIRECT_SYNAPSES_H_ */
