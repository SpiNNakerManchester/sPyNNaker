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

#include "elimination_random_by_weight_impl.h"

struct elimination_params *synaptogenesis_elimination_init(uint8_t **data) {
    struct elimination_params *elim_params = spin1_malloc(sizeof(struct elimination_params));
    if (elim_params == NULL) {
        log_error("Out of memory when allocating parameters");
        rt_error(RTE_SWERR);
    }
    spin1_memcpy(elim_params, *data, sizeof(struct elimination_params));
    log_info("Elimination random by weight prob_dep=%u prob_pot=%u thresh=%u",
            elim_params->prob_elim_depression, elim_params->prob_elim_potentiation,
            elim_params->threshold);
    *data += sizeof(struct elimination_params);
    return elim_params;
}
