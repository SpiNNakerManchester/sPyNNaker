#include "../../spin-neuron-impl.h"
#include "../../../common/compile_time_assert.h"
#include "maths.h"

#include <string.h>

//---------------------------------------
// Functions
//---------------------------------------
address_t copy_int16_lut(address_t start_address, uint32_t num_entries, int16_t *lut)
{
  // Get size of LUTs in words
  const uint32_t num_words = num_entries / 2;
  COMPILE_TIME_ASSERT(num_words * 2 == num_entries, luts_must_be_word_aligned);

  // Copy words to LUT
  memcpy(lut, start_address, sizeof(uint32_t) * num_words);

  // Return address after words
  return start_address + num_words;
}