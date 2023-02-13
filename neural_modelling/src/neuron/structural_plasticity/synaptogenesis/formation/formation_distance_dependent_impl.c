/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
