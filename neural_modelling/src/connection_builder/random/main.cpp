#include <cstdint>

// Common includes
#include "../common/fixed_point_number.h"
#include "../common/log.h"
#include "../common/spinnaker.h"
#include "../common/maths/normal.h"
#include "../common/random/mars_kiss64.h"

// Namespaces
using namespace Common;
using namespace Common::Maths;
using namespace Common::Random;

//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
extern "C" void c_main()
{
  // Create RNG
  MarsKiss64 rng;

  // Read address of tag zero
  S1615 *outputData = (S1615*)sark_tag_ptr(1, 0);

  // Read number of samples from first word
  uint32_t numSamples = *reinterpret_cast<uint32_t*>(outputData++);
  LOG_PRINT(LOG_LEVEL_INFO, "Generating %u random numbers and writing to %08x",
            numSamples, outputData);

  // Write samples to memory
  for(unsigned int i = 0; i < numSamples; i++)
  {
    uint32_t uniform = rng.GetNext();
    *outputData++ = NormalU032(uniform);
  }

}

