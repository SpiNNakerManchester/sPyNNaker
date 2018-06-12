void *connection_generator_one_to_one_initialise(address_t *region) {
    use(region);
    log_debug("One to One connector");
    return NULL;
}

void connection_generator_one_to_one_free(void *data) {
    use(data);
}

uint32_t connection_generator_one_to_one_generate(
        void *data,  uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices) {
    use(data);
    use(pre_slice_start);
    use(pre_slice_count);

    // If no space, generate nothing
    if (max_row_length < 1) {
        return 0;
    }

    // If out of range, don't generate anything
    if ((pre_neuron_index < post_slice_start) ||
            (pre_neuron_index >= (post_slice_start + post_slice_count))) {
        return 0;
    }

    // Pre-index = (core-relative) post-index
    indices[0] = pre_neuron_index - post_slice_start;
    return 1;
}
