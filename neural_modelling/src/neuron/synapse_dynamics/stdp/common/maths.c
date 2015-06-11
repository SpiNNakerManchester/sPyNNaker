#include "maths.h"

#include <string.h>

//---------------------------------------
// Functions
//---------------------------------------
address_t maths_copy_int16_lut(address_t start_address, uint32_t num_entries,
                         int16_t *lut) {

    // Pad to number of words
    const uint32_t num_words = (num_entries / 2)
                               + (((num_entries & 1) != 0) ? 1 : 0);

    // Copy entries to LUT
    memcpy(lut, start_address, sizeof(int16_t) * num_entries);

    // Return address after words
    return start_address + num_words;
}
