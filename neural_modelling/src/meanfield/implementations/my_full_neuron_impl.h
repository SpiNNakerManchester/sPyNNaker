#ifndef _MY_FULL_NEURON_IMPL_
#define _MY_FULL_NEURON_IMPL_

// Demonstrating that a "neuron model" can be defined in a different
// way without the use of components for additional input / input / threshold

#include <neuron/implementations/neuron_impl.h>
#include <spin1_api.h>
#include <debug.h>

#define V_RECORDING_INDEX 0
#define N_RECORDED_VARS 1

#define SPIKE_RECORDING_BITFIELD 0
#define N_BITFIELD_VARS 1

#include <neuron/neuron_recording.h>

//! neuron_impl_t struct
typedef struct neuron_impl_t {
    accum inputs[2];
    accum v;
    accum threshold;
} neuron_impl_t;

//! Array of neuron states
static neuron_impl_t *neuron_array;

__attribute__((unused)) // Marked unused as only used sometimes
static bool neuron_impl_initialise(uint32_t n_neurons) {
    // Allocate DTCM for neuron array
    if (sizeof(neuron_impl_t) != 0) {
        neuron_array = spin1_malloc(n_neurons * sizeof(neuron_impl_t));
        if (neuron_array == NULL) {
            log_error("Unable to allocate neuron array - Out of DTCM");
            return false;
        }
    }

    return true;
}

__attribute__((unused)) // Marked unused as only used sometimes
static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    // Copy parameters to DTCM from SDRAM
    spin1_memcpy(neuron_array, &address[next],
            n_neurons * sizeof(neuron_impl_t));
}

__attribute__((unused)) // Marked unused as only used sometimes
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    // Copy parameters to SDRAM from DTCM
    spin1_memcpy(&address[next], neuron_array,
            n_neurons * sizeof(neuron_impl_t));
}

__attribute__((unused)) // Marked unused as only used sometimes
static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // Get the neuron itself
    neuron_impl_t *neuron = &neuron_array[neuron_index];

    // Do something to store the inputs for the next state update
    neuron->inputs[synapse_type_index] += weights_this_timestep;
}

__attribute__((unused)) // Marked unused as only used sometimes
static bool neuron_impl_do_timestep_update(
        index_t neuron_index, input_t external_bias) {
    // Get the neuron itself
    neuron_impl_t *neuron = &neuron_array[neuron_index];

    // Store the recorded membrane voltage
    neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, neuron->v);

    // Do something to update the state
    neuron->v += external_bias + neuron->inputs[0] - neuron->inputs[1];
    neuron->inputs[0] = 0;
    neuron->inputs[1] = 0;

    // Determine if the neuron has spiked
    if (neuron->v > neuron->threshold) {
        // Reset if spiked
        neuron->v = 0k;
        neuron_recording_record_bit(SPIKE_RECORDING_BITFIELD, neuron_index);
        return true;
    }
    return false;
}

#if LOG_LEVEL >= LOG_DEBUG
void neuron_impl_print_inputs(uint32_t n_neurons) {
    log_debug("-------------------------------------\n");
    for (index_t i = 0; i < n_neurons; i++) {
        neuron_impl_t *neuron = &neuron_array[i];
        log_debug("inputs: %k %k", neuron->inputs[0], neuron->inputs[1]);
    }
    log_debug("-------------------------------------\n");
}

void neuron_impl_print_synapse_parameters(uint32_t n_neurons) {
    // there aren't any accessible in this example
    use(n_neurons);
}

const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
    use(synapse_type);
    return 0;
}
#endif // LOG_LEVEL >= LOG_DEBUG


#endif // _MY_FULL_NEURON_IMPL_
