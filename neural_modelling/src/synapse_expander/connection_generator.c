/**
 *! \file
 * \brief The implementation of the functions in connection_generator.h
 */

#include "connection_generator.h"
#include <spin1_api.h>
#include <debug.h>

#include "connection_generators/connection_generator_one_to_one.h"
#include "connection_generators/connection_generator_all_to_all.h"
#include "connection_generators/connection_generator_fixed_prob.h"
#include "connection_generators/connection_generator_fixed_total.h"
#include "connection_generators/connection_generator_kernel.h"

// For now, hash is just an index agreed between Python and here
enum connection_generator_hash {
    ONE_TO_ONE_GENERATOR,
    ALL_TO_ALL_GENERATOR,
    FIXED_PROBABILITY_GENERATOR,
    FIXED_TOTAL_NUMBER_GENERATOR,
    KERNEL_GENERATOR,
    N_CONNECTION_GENERATORS
};

struct connection_generator_info;

/**
 *! \brief The data for a connection generator
 */
struct connection_generator {
    const struct connection_generator_info *type_ptr;
    void *data;
};

/**
 *! \brief Initialise the generator
 *! \param[in/out] region Region to read parameters from.  Should be updated
 *!                       to position just after parameters after calling.
 *! \return A data item to be passed in to other functions later on
 */
typedef void* (connection_generator_initialize_t)(address_t *region);

/**
 *! \brief Generate connections
 *! \param[in] data The data for the connection generator, returned by the
 *!                 initialise function
 *! \param[in] pre_slice_start The start of the slice of the pre-population
 *!                            being generated
 *! \param[in] pre_slice_count The number of neurons in the slice of the
 *!                            pre-population being generated
 *! \param[in] pre_neuron_index The index of the neuron in the
 *!                             pre-population being generated
 *! \param[in] post_slice_start The start of the slice of the
 *!                             post-population being generated
 *! \param[in] post_slice_count The number of neurons in the slice of the
 *!                             post-population being generated
 *! \param[in] max_row_length The maximum number of connections to generate
 *! \param[in/out] indices An array into which the core-relative
 *!                        post-indices should be placed.  This will be
 *!                        initialised to be max_row_length in size
 *! \return The number of connections generated
 */
typedef uint32_t (connection_generator_generate_t)(
        void *data, uint32_t pre_slice_start, uint32_t pre_slice_count,
        uint32_t pre_neuron_index, uint32_t post_slice_start,
        uint32_t post_slice_count, uint32_t max_row_length, uint16_t *indices);

/**
 *! \brief Free any data for the generator
 *! \param[in] data The data to free
 */
typedef void (connection_generator_free_t)(void *data);

/**
 *! \brief A "class" for connection generators
 */
struct connection_generator_info {
    /**
     *! \brief The hash of the generator
     */
    uint32_t hash;
    /**
     *! \brief Initialise the generator
     */
    connection_generator_initialize_t *initialize_fun;
    /**
     *! \brief Generate connections
     */
    connection_generator_generate_t *generate_fun;
    /**
     *! \brief Free any data for the generator
     */
    connection_generator_free_t *free_fun;
};

/**
 *! \brief An Array of known generators
 */
const struct connection_generator_info connection_generators[] = {
    {ONE_TO_ONE_GENERATOR,          // One To One Connector
            connection_generator_one_to_one_initialise,
            connection_generator_one_to_one_generate,
            connection_generator_one_to_one_free},
    {ALL_TO_ALL_GENERATOR,          // All To All Connector
            connection_generator_all_to_all_initialise,
            connection_generator_all_to_all_generate,
            connection_generator_all_to_all_free},
    {FIXED_PROBABILITY_GENERATOR,   // Fixed-Probability Connector
            connection_generator_fixed_prob_initialise,
            connection_generator_fixed_prob_generate,
            connection_generator_fixed_prob_free},
    {FIXED_TOTAL_NUMBER_GENERATOR,  // Fixed Total Number (Multapse) Connector
            connection_generator_fixed_total_initialise,
            connection_generator_fixed_total_generate,
            connection_generator_fixed_total_free},
    {KERNEL_GENERATOR,              // Kernel Connector (tried to cheat, failed)
            connection_generator_kernel_initialise,
            connection_generator_kernel_generate,
            connection_generator_kernel_free}
};

static inline connection_generator_t connection_generator_new(
        const struct connection_generator_info *gen_type, address_t *in_region) {
    // Prepare a space for the data
    struct connection_generator *generator =
            spin1_malloc(sizeof(struct connection_generator));
    if (generator == NULL) {
        log_error("Could not create generator");
        return NULL;
    }

    // Store which type it is
    generator->type_ptr = gen_type;

    // Initialise the generator and store the data
    generator->data = gen_type->initialize_fun(in_region);
    return generator;
}

/**
 *! \brief Create and initialise the connection generator
 *! \param[in] hash The code indicating the type of connection generator to use
 *! \param[in/out] in_region The address to read the parameters from.  Should be
 *!                          updated to the position just after the parameters
 *!                          after calling.
 *! \return The connection generator instance data reference
 */
connection_generator_t connection_generator_init(
        uint32_t hash, address_t *in_region) {
    // Look through the known generators
    for (uint32_t i = 0; i < N_CONNECTION_GENERATORS; i++) {
        const struct connection_generator_info *gen_type =
                &connection_generators[i];

        // If the hash requested matches the hash of the generator, use it
        if (hash == gen_type->hash) {
            return connection_generator_new(gen_type, in_region);
        }
    }
    log_error("Connection generator with hash %u not found", hash);
    return NULL;
}

uint32_t connection_generator_generate(
        connection_generator_t generator, uint32_t pre_slice_start,
        uint32_t pre_slice_count, uint32_t pre_neuron_index,
        uint32_t post_slice_start, uint32_t post_slice_count,
        uint32_t max_row_length, uint16_t *indices) {
    return generator->type_ptr->generate_fun(
            generator->data, pre_slice_start, pre_slice_count,
            pre_neuron_index, post_slice_start, post_slice_count,
            max_row_length, indices);
}

void connection_generator_free(connection_generator_t generator) {
    generator->type_ptr->free_fun(generator->data);
    sark_free(generator);
}
