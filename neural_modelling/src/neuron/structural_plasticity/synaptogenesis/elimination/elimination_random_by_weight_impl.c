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
//! \brief Support code for elimination_random_by_weight_impl.h
#include "elimination_random_by_weight_impl.h"

elimination_params_t *synaptogenesis_elimination_init(uint8_t **data) {
    elimination_params_t *elim_params =
            spin1_malloc(sizeof(elimination_params_t));
    if (elim_params == NULL) {
        log_error("Out of memory when allocating parameters");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(elim_params, *data, sizeof(elimination_params_t));
    log_debug("Elimination random by weight prob_dep=%u prob_pot=%u thresh=%u",
            elim_params->prob_elim_depression,
            elim_params->prob_elim_potentiation,
            elim_params->threshold);
    *data += sizeof(elimination_params_t);
    return elim_params;
}
