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

enum param_generator_hash {
    // For now, hash is just an index agreed between Python and here
    CONSTANT_PARAM,
    UNIFORM_PARAM,
    NORMAL_PARAM,
    NORMAL_CLIPPED_PARAM,
    NORMAL_CLIPPED_BOUNDARY_PARAM,
    EXPONENTIAL_PARAM,
    /**
     *! \brief The number of known generators
     */
    N_PARAM_GENERATORS
};

struct param_generator_info;

/**
 *! \brief The data for a parameter generator
 */
struct param_generator {
    struct param_generator_info *type_ptr;
    void *data;
};

/**
 *! \brief Initialise the generator
 *! \param[in/out] region Region to read parameters from.  Should be updated
 *!                       to position just after parameters after calling.
 *! \return A data item to be passed in to other functions later on
 */
typedef void* (param_generator_initialize_t)(address_t *region);

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
typedef void (param_generator_generate_t)(
    void *data, uint32_t n_synapses, uint32_t pre_neuron_index,
    uint16_t *indices, accum *values);

/**
 *! \brief Free any data for the generator
 *! \param[in] data The data to free
 */
typedef void (param_generator_free_t)(void *data);

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
     */
    param_generator_initialize_t *initialize_fun;
    /**
     *! \brief Generate values with a parameter generator
     */
    param_generator_generate_t *generate_fun;
    /**
     *! \brief Free any data for the generator
     */
    param_generator_free_t *free_fun;
};

/**
 *! \brief An Array of known generators
 */
struct param_generator_info param_generators[] = {
    {CONSTANT_PARAM,    // Constant value
            param_generator_constant_initialize,
            param_generator_constant_generate,
            param_generator_constant_free},
    {UNIFORM_PARAM,     // Uniform random values
            param_generator_uniform_initialize,
            param_generator_uniform_generate,
            param_generator_uniform_free},
    {NORMAL_PARAM,      // Normally distributed random values
            param_generator_normal_initialize,
            param_generator_normal_generate,
            param_generator_normal_free},
    {NORMAL_CLIPPED_PARAM,
            // Normally distributed random values redrawn when outside boundary
            param_generator_normal_clipped_initialize,
            param_generator_normal_clipped_generate,
            param_generator_normal_clipped_free},
    {NORMAL_CLIPPED_BOUNDARY_PARAM,
            // Normally distributed random values clipped to boundary
            param_generator_normal_clipped_boundary_initialize,
            param_generator_normal_clipped_boundary_generate,
            param_generator_normal_clipped_boundary_free},
    {EXPONENTIAL_PARAM, // Exponentially distributed random values
            param_generator_exponential_initialize,
            param_generator_exponential_generate,
            param_generator_exponential_free}
};

param_generator_t param_generator_init(uint32_t hash, address_t *in_region) {

    // Look through the known generators
    for (uint32_t i = 0; i < N_PARAM_GENERATORS; i++) {

        // If the hash requested matches the hash of the generator, use it
        if (hash == param_generators[i].hash) {

            // Prepare a space for the data
            param_generator_t generator =
                    spin1_malloc(sizeof(param_generator_t));
            if (generator == NULL) {
                log_error("Could not create generator");
                return NULL;
            }

            // Store which type it is
            generator->type_ptr = &param_generators[i];

            // Initialise the generator and store the data
            generator->data = generator->type_ptr->initialize_fun(in_region);
            return generator;
        }
    }
    log_error("Param generator with hash %u not found", hash);
    return NULL;
}

void param_generator_generate(
        param_generator_t generator, uint32_t n_indices,
        uint32_t pre_neuron_index, uint16_t *indices, accum *values) {
    generator->type_ptr->generate_fun(
        generator->data, n_indices, pre_neuron_index, indices, values);
}

void param_generator_free(param_generator_t generator) {
    generator->type_ptr->free_fun(generator->data);
    sark_free(generator);
}
