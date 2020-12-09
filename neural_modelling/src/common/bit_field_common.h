/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

//! \file
//! \brief Functions and structs used by bitfields associated systems.

#ifndef _BIT_FIELD_COMMON_H_
#define _BIT_FIELD_COMMON_H_

//! \brief Format of the builder region in SDRAM
typedef struct builder_region_struct {
    //! What region to find master population table in
    int master_pop_region_id;
    //! What region to find the synaptic matrix in
    int synaptic_matrix_region_id;
    //! What region to find the direct matrix in
    int direct_matrix_region_id;
    //! What region to find bitfield region information in
    int bit_field_region_id;
    //! What region to find bitfield key map information in
    int bit_field_key_map_region_id;
    //! What region to find structural plasticity information in
    int structural_matrix_region_id;
} builder_region_struct;

//! \brief Get this processor's virtual CPU control table in SRAM.
//! \return a pointer to the virtual control table
static inline vcpu_t *vcpu(void) {
    vcpu_t *sark_virtual_processor_info = (vcpu_t *) SV_VCPU;
    uint core = spin1_get_core_id();
    return &sark_virtual_processor_info[core];
}



#endif // _BIT_FIELD_COMMON_H_