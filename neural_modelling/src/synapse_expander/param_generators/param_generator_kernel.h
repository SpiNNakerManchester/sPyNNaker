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

#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <synapse_expander/common_kernel.h>
#include <synapse_expander/common_mem.h>
#include <synapse_expander/generator_types.h>

static initialize_func param_generator_kernel_initialize;
static free_func param_generator_kernel_free;
static generate_param_func param_generator_kernel_generate;

struct param_generator_kernel {
    uint16_t commonWidth;
    uint16_t commonHeight;

    uint16_t preWidth;
    uint16_t preHeight;
    uint16_t postWidth;
    uint16_t postHeight;

    uint16_t startPreWidth;
    uint16_t startPreHeight;
    uint16_t startPostWidth;
    uint16_t startPostHeight;

    uint16_t stepPreWidth;
    uint16_t stepPreHeight;
    uint16_t stepPostWidth;
    uint16_t stepPostHeight;

    uint16_t kernelWidth;
    uint16_t kernelHeight;

    uint32_t post_slice_start;
};

struct all_kernel_params {
    struct param_generator_kernel params;
    accum *values;
};

static void *param_generator_kernel_initialize(address_t *region) {
    struct all_kernel_params *obj = spin1_malloc(sizeof(struct all_kernel_params));
    struct param_generator_kernel *params_sdram = (void *) *region;
    fast_memcpy(&obj->params, params_sdram++, sizeof(*params_sdram));
    *region = (void *) params_sdram;

    obj->values = (accum *) params_sdram;
    *region += obj->params.kernelHeight * obj->params.kernelWidth;

    log_debug("Kernel param generator; kernelWidth, kernelHeight = %u,%u",
    		obj->params.kernelWidth, obj->params.kernelHeight);

    return obj;
}

static void param_generator_kernel_free(void *data) {
    sark_free(data);
}

static void param_generator_kernel_generate(void *data, uint32_t n_synapses,
        uint32_t pre_neuron_index, uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);
    struct all_kernel_params *obj = data;
    struct param_generator_kernel *params = &obj->params;
    uint16_t pre_c = 0;
    uint16_t pre_r = uidiv(pre_neuron_index, params->preWidth, &pre_c);

    uint16_t hlf_kw = params->kernelWidth >> 1;
    uint16_t hlf_kh = params->kernelHeight >> 1;
    int16_t k_r, k_c;
    for (uint16_t i = 0; i < n_synapses; i++) {
        uint16_t post_r, post_c; //post raw
        uint16_t pac_r, pac_c; // post as common
        int16_t pap_r, pap_c; // post as pre
        post_r = uidiv(params->post_slice_start + indices[i],
                params->postWidth, &post_c);

        //move post coords into common coordinate system
        post_in_pre_world(post_r, post_c, params->startPostHeight,
                params->startPostWidth, params->stepPostHeight,
                params->stepPostWidth, &pac_r, &pac_c);

        //move common to pre coords
        pre_in_post_world(
                pac_r, pac_c, params->startPreHeight, params->startPreHeight,
                params->stepPreHeight, params->stepPreWidth, &pap_r, &pap_c);

        int16_t r_diff = (int16_t) pap_r - (int16_t) pre_r;
        int16_t c_diff = (int16_t) pap_c - (int16_t) pre_c;

        k_r = hlf_kh - r_diff;
        k_c = hlf_kw - c_diff;

        if ((0 <= k_r) && (k_r < params->kernelHeight) && (0 <= k_c)
                && (k_c < params->kernelWidth)) {
            values[i] = obj->values[k_r * params->kernelWidth + k_c];
            //      LOG_PRINT(LOG_LEVEL_INFO, "val = %5.6k", output[i]);
        } else {
            log_error("Kernel coordinates off range (%d, %d)", k_r, k_c);
        }
    }
}
