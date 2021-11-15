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
//! \brief Support code for formation_distance_dependent_impl.h
#include "formation_distance_dependent_impl.h"

formation_params_t *synaptogenesis_formation_init(uint8_t **data) {
    // Reference the parameters to read the sizes
    formation_params_t *form_params = (formation_params_t *) *data;
    uint32_t data_size = sizeof(formation_params_t) + (sizeof(uint16_t) *
            (form_params->ff_prob_size + form_params->lat_prob_size));

    // Allocate the space for the data and copy it in
    form_params = spin1_malloc(data_size);
    if (form_params == NULL) {
        log_error("Out of memory when allocating parameters");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(form_params, *data, data_size);
    log_debug("Formation distance dependent %u bytes, grid=(%u, %u), %u ff probs, %u lat probs",
            data_size, form_params->grid_x, form_params->grid_y,
            form_params->ff_prob_size, form_params->lat_prob_size);

    *data += data_size;

    return form_params;
}
