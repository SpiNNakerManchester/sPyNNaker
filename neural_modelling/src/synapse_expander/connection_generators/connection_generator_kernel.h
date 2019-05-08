/**
 *! \file
 *! \brief Kernel connection generator implementation
 */

#include <stdbool.h>

/**
 *! \brief The parameters to be passed around for this connector
 */
struct kernel {
	// put in the relevant kernel connector parameters here
    uint16_t m_commonWidth;
    uint16_t m_commonHeight;

    uint16_t m_preWidth;
    uint16_t m_preHeight;
    uint16_t m_postWidth;
    uint16_t m_postHeight;

    uint16_t m_startPreWidth;
    uint16_t m_startPreHeight;
    uint16_t m_startPostWidth;
    uint16_t m_startPostHeight;

    uint16_t m_stepPreWidth;
    uint16_t m_stepPreHeight;
    uint16_t m_stepPostWidth;
    uint16_t m_stepPostHeight;

    uint16_t m_kernelWidth;
    uint16_t m_kernelHeight;

    // any further parameters required would go here
    // uint32_t allow_self_connections;
};

void *connection_generator_kernel_initialise(address_t *region) {

    // Allocate the data structure for parameters
    struct kernel *params = (struct kernel *)
        spin1_malloc(sizeof(struct kernel));

    // Copy the parameters into the data structure
    address_t params_sdram = *region;
    spin1_memcpy(params, params_sdram, sizeof(struct kernel));
    params_sdram = &(params_sdram[sizeof(struct kernel) >> 2]);
    log_debug("Kernel connector, m_kernelWidth, m_kernelHeight = %u %u",
    		params->m_kernelWidth, params->m_kernelHeight);

    *region = params_sdram;
    return params;
}

void connection_generator_kernel_free(void *data) {
    sark_free(data);
}

// Note: the following three functions are used here and in param_generator_kernel.h
uint16_t uidiv2(uint16_t dividend, uint16_t divider, uint16_t *reminder) {
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

void post_in_pre_world2(uint16_t in_row, uint16_t in_col,
        uint16_t start_row, uint16_t start_col,
        uint16_t step_row, uint16_t step_col,
        uint16_t *out_row, uint16_t *out_col) {
    *out_row = start_row + in_row * step_row;
    *out_col = start_col + in_col * step_col;
}

void pre_in_post_world2(uint16_t in_row, uint16_t in_col, uint16_t start_row,
        uint16_t start_col, uint16_t step_row, uint16_t step_col,
        int16_t *out_row, int16_t *out_col) {
    int16_t d = (int16_t) (in_row - start_row - 1);
    uint16_t r;
    if (d == 0) {
        *out_row = 1;
    } else if (d < 0) {
        d = (int16_t) uidiv2((uint16_t) (-d), step_row, &r);
        *out_row = (-d + 1);
    } else {
        d = (int16_t) uidiv2((uint16_t) (d), step_row, &r);
        *out_row = (d + 1);
    }

    d = (int16_t) (in_col - start_col - 1);
    if (d == 0) {
        *out_col = 1;
    } else if (d < 0) {
        d = (int16_t) uidiv2((uint16_t) (-d), step_col, &r);
        *out_col = (-d + 1);
    } else {
        d = (int16_t) uidiv2((uint16_t) (d), step_col, &r);
        *out_col = (d + 1);
    }
}

uint32_t connection_generator_kernel_generate(
        void *data,  uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(pre_slice_start);
    use(pre_slice_count);

    log_debug("Generating for %u", pre_neuron_index);

    // If no space, generate nothing
    if (max_row_length < 1) {
    	return 0;
    }

    struct kernel *params = (struct kernel *) data;

    // start n_conns at zero
    uint32_t n_conns = 0;

    uint16_t pre_c = 0;
    uint16_t pre_r = uidiv2(pre_neuron_index, params->m_preWidth, &pre_c);

    uint16_t hlf_kw = params->m_kernelWidth >> 1;
    uint16_t hlf_kh = params->m_kernelHeight >> 1;
    int16_t k_r, k_c;
    for (uint16_t i = 0; i < post_slice_count; i++) {
        uint16_t post_r, post_c; //post raw
        uint16_t pac_r, pac_c; // post as common
        int16_t pap_r, pap_c; // post as pre
        post_r = uidiv2(post_slice_start + i,
            params->m_postWidth, &post_c);

        //move post coords into common coordinate system
        post_in_pre_world2(post_r, post_c, params->m_startPostHeight,
            params->m_startPostWidth, params->m_stepPostHeight,
            params->m_stepPostWidth, &pac_r, &pac_c);

        //move common to pre coords
        pre_in_post_world2(
            pac_r, pac_c, params->m_startPreHeight, params->m_startPreHeight,
            params->m_stepPreHeight, params->m_stepPreWidth, &pap_r, &pap_c);

        int16_t r_diff = (int16_t) pap_r - (int16_t) pre_r;
        int16_t c_diff = (int16_t) pap_c - (int16_t) pre_c;

        k_r = hlf_kh - r_diff;
        k_c = hlf_kw - c_diff;

        if (0 <= k_r && k_r < params->m_kernelHeight && 0 <= k_c
                && k_c < params->m_kernelWidth) {
            indices[n_conns++] = i;
        }
    }

    return n_conns;
}
