/**
 *! \file
 *! \brief The implementation of a parameter generator
 */
#include "param_generator.h"
#include <spin1_api.h>
#include <debug.h>

#include "param_generators/param_generator_constant.h"
#include "param_generators/param_generator_uniform.h"
#include "param_generators/param_generator_normal.h"
#include "param_generators/param_generator_normal_clipped.h"
#include "param_generators/param_generator_normal_clipped_to_boundary.h"
#include "param_generators/param_generator_exponential.h"

/**
 *! \brief The number of known generators
 */
#define N_PARAM_GENERATORS 6

/**
 *! \brief The data for a parameter generator
 */
struct param_generator {
    uint32_t index;
    void *data;
};

/**
 *! \brief A "class" for parameter generators
 */
struct param_generator_info {

    /**
     *! \brief The hash of the generator
     */
    uint32_t hash;

    /**
     *! \brief Initialise the generator
     *! \param[in/out] region Region to read parameters from.  Should be updated
     *!                       to position just after parameters after calling.
     *! \return A data item to be passed in to other functions later on
     */
    void* (*initialize)(address_t *region);

    /**
     *! \brief Generate values with a parameter generator
     *! \param[in] data The data for the parameter generator, returned by the
     *!                 initialise function
     *! \param[in] n_indices The number of values to generate
     *! \param[in] pre_neuron_index The index of the neuron in the pre-population
     *!                             being generated
     *! \param[in] indices The n_indices post-neuron indices for each connection
     *! \param[in/out] values An array into which to place the values - will be
     *!                       n_indices in size
     */
    void (*generate)(
        void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
        uint16_t *indices, accum *values);

    /**
     *! \brief Free any data for the generator
     *! \param[in] data The data to free
     */
    void (*free)(void *data);
};

/**
 *! \brief An Array of known generators
 */
struct param_generator_info param_generators[N_PARAM_GENERATORS];

void register_param_generators() {
    // Register each of the known connection generators
    // For now, hash is just an index agreed between Python and here

    // Constant value
    param_generators[0].hash = 0;
    param_generators[0].initialize = param_generator_constant_initialize;
    param_generators[0].generate = param_generator_constant_generate;
    param_generators[0].free = param_generator_constant_free;

    // Uniform random values
    param_generators[1].hash = 1;
    param_generators[1].initialize = param_generator_uniform_initialize;
    param_generators[1].generate = param_generator_uniform_generate;
    param_generators[1].free = param_generator_uniform_free;

    // Normally distributed random values
    param_generators[2].hash = 2;
    param_generators[2].initialize = param_generator_normal_initialize;
    param_generators[2].generate = param_generator_normal_generate;
    param_generators[2].free = param_generator_normal_free;

    // Normally distributed random values redrawn when outside boundary
    param_generators[3].hash = 3;
    param_generators[3].initialize = param_generator_normal_clipped_initialize;
    param_generators[3].generate = param_generator_normal_clipped_generate;
    param_generators[3].free = param_generator_normal_clipped_free;

    // Normally distributed random values clipped to boundary
    param_generators[4].hash = 4;
    param_generators[4].initialize =
        param_generator_normal_clipped_boundary_initialize;
    param_generators[4].generate =
        param_generator_normal_clipped_boundary_generate;
    param_generators[4].free = param_generator_normal_clipped_boundary_free;

    // Exponentially distributed random values
    param_generators[5].hash = 5;
    param_generators[5].initialize = param_generator_exponential_initialize;
    param_generators[5].generate = param_generator_exponential_generate;
    param_generators[5].free = param_generator_exponential_free;
}

param_generator_t param_generator_init(uint32_t hash, address_t *in_region) {

    // Look through the known generators
    for (uint32_t i = 0; i < N_PARAM_GENERATORS; i++) {

        // If the hash requested matches the hash of the generator, use it
        if (hash == param_generators[i].hash) {

            // Prepare a space for the data
            address_t region = *in_region;
            param_generator_t generator = spin1_malloc(
                sizeof(param_generator_t));
            if (generator == NULL) {
                log_error("Could not create generator");
                return NULL;
            }

            // Store the index
            generator->index = i;

            // Initialise the generator and store the data
            generator->data = param_generators[i].initialize(&region);
            *in_region = region;
            return generator;
        }
    }
    log_error("Param generator with hash %u not found", hash);
    return NULL;
}

void param_generator_generate(
        param_generator_t generator, uint32_t n_indices,
        uint32_t pre_neuron_index, uint16_t *indices, accum *values) {
    param_generators[generator->index].generate(
        generator->data, n_indices, pre_neuron_index, indices, values);
}

void param_generator_free(param_generator_t generator) {
    param_generators[generator->index].free(generator->data);
    sark_free(generator);
}
