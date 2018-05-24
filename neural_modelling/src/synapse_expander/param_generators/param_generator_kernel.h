#include <stdfix.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>

struct param_generator_kernel {
    uint16_t m_commonHeight;
    uint16_t m_commonWidth;

    uint16_t m_preHeight;
    uint16_t m_preWidth;
    uint16_t m_postHeight;
    uint16_t m_postWidth;

    uint16_t m_startPreHeight;
    uint16_t m_startPreWidth;
    uint16_t m_startPostHeight;
    uint16_t m_startPostWidth;

    uint16_t m_stepPreWidth;
    uint16_t m_stepPreHeight;
    uint16_t m_stepPostWidth;
    uint16_t m_stepPostHeight;

    uint16_t m_kernelWidth;
    uint16_t m_kernelHeight;

    uint32_t post_slice_start;
};

struct all_params {
    struct param_generator_kernel params;
    accum *values;
};

void *param_generator_kernel_initialize(address_t *region) {
    struct all_params *params = (struct all_params *) spin1_malloc(
        sizeof(struct all_params));
    spin1_memcpy(&params->params, *region,
        sizeof(struct param_generator_kernel));
    *region += sizeof(struct param_generator_kernel) >> 2;
    params->values = (accum *) *region;
    *region += params->params.m_kernelHeight * params->params.m_kernelWidth;
    return params;
}

void param_generator_kernel_free(void *data) {
    sark_free(data);
}

uint16_t uidiv(uint16_t dividend, uint16_t divider, uint16_t *reminder) {
    if (dividend == 0 || dividend < divider) {
        *reminder = dividend;
        return 0;
    }

    uint16_t d = 0;
    *reminder = dividend;
    while (*reminder >= divider) {
        d += 1;
        *reminder -= divider;
    }
    return d;
}

void post_in_pre_world(uint16_t in_row, uint16_t in_col,
        uint16_t start_row, uint16_t start_col,
        uint16_t step_row, uint16_t step_col,
        uint16_t *out_row, uint16_t *out_col) {
    *out_row = start_row + in_row * step_row;
    *out_col = start_col + in_col * step_col;
}

void pre_in_post_world(uint16_t in_row, uint16_t in_col, uint16_t start_row,
        uint16_t start_col, uint16_t step_row, uint16_t step_col,
        int16_t *out_row, int16_t *out_col) {
    int16_t d = (int16_t) (in_row - start_row - 1);
    uint16_t r;
    if (d == 0) {
        *out_row = 1;
    } else if (d < 0) {
        d = (int16_t) uidiv((uint16_t) (-d), step_row, &r);
        *out_row = (-d + 1);
    } else {
        d = (int16_t) uidiv((uint16_t) (d), step_row, &r);
        *out_row = (d + 1);
    }

    d = (int16_t) (in_col - start_col - 1);
    if (d == 0) {
        *out_col = 1;
    } else if (d < 0) {
        d = (int16_t) uidiv((uint16_t) (-d), step_col, &r);
        *out_col = (-d + 1);
    } else {
        d = (int16_t) uidiv((uint16_t) (d), step_col, &r);
        *out_col = (d + 1);
    }
}

void param_generator_kernel_generate(void *data, uint32_t n_synapses, rng_t rng,
        uint32_t pre_neuron_index, uint16_t *indices, accum *values) {
    use(pre_neuron_index);
    use(indices);
    struct all_params *all_params = (struct all_params *) data;
    struct param_generator_kernel *params = &params->params;
    uint16_t pre_c = 0;
    uint16_t pre_r = uidiv(pre_neuron_index, params->m_preWidth, &pre_c);

    uint16_t hlf_kw = params->m_kernelWidth >> 1;
    uint16_t hlf_kh = params->m_kernelHeight >> 1;
    int16_t k_r, k_c;
    for (uint16_t i = 0; i < n_synapses; i++) {
        uint16_t post_r, post_c; //post raw
        uint16_t pac_r, pac_c; // post as common
        int16_t pap_r, pap_c; // post as pre
        post_r = uidiv(params->post_slice_start + indices[i],
            params->m_postWidth, &post_c);

        //move post coords into common coordinate system
        post_in_pre_world(post_r, post_c, params->m_startPostHeight,
            params->m_startPostWidth, params->m_stepPostHeight,
            params->m_stepPostWidth, &pac_r, &pac_c);

        //move common to pre coords
        pre_in_post_world(
            pac_r, pac_c, params->m_startPreHeight, params->m_startPreHeight,
            params->m_stepPreHeight, params->m_stepPreWidth, &pap_r, &pap_c);

        int16_t r_diff = (int16_t) pap_r - (int16_t) pre_r;
        int16_t c_diff = (int16_t) pap_c - (int16_t) pre_c;

        k_r = hlf_kh - r_diff;
        k_c = hlf_kw - c_diff;

        if (0 <= k_r && k_r < params->m_kernelHeight && 0 <= k_c
                && k_c < params->m_kernelWidth) {
            values[i] = all_params[values[k_r * params->m_kernelWidth + k_c]];
            //      LOG_PRINT(LOG_LEVEL_INFO, "val = %5.6k", output[i]);
        } else {
            log_error("Kernel coordinates off range (%d, %d)", k_r, k_c);
        }
    }
}
