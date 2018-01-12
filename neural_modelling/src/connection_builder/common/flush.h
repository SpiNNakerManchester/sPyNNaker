#pragma once

// Standard includes
#include <climits>
#include <cstdint>

// Rig CPP common includes
#include "rig_cpp_common/log.h"
#include "rig_cpp_common/spinnaker.h"

// Namespaces
using namespace Common;

//-----------------------------------------------------------------------------
// Common::Flush
//-----------------------------------------------------------------------------
namespace Common
{
class Flush
{
public:
  Flush() : m_TimeSinceLastSpike(NULL), m_FlushTime(0)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numNeurons)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Flush::ReadSDRAMData");

    // Read flush time from first word of region
    m_FlushTime = *region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\tFlush time:%u timesteps", m_FlushTime);

     // If a flush time is set
    if(m_FlushTime != UINT32_MAX)
    {
      // Allocate array to hold time since last spike
      m_TimeSinceLastSpike = (uint16_t*)spin1_malloc(sizeof(uint16_t) * numNeurons);
      if(m_TimeSinceLastSpike == NULL)
      {
        LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate time since last spike array");
        return false;
      }

      // Initially zero all counts
      for(unsigned int n = 0; n < numNeurons; n++)
      {
        m_TimeSinceLastSpike[n] = 0;
      }
    }
    return true;
  }

  bool ShouldFlush(unsigned int neuronIndex, bool spiked)
  {
    if(m_TimeSinceLastSpike != NULL)
    {
      // If neuron's spiked, reset time since last spike
      if(spiked)
      {
        m_TimeSinceLastSpike[neuronIndex] = 0;
      }
      // Otherwise
      else
      {
        // Increment time since last spike
        m_TimeSinceLastSpike[neuronIndex]++;

        // If flush time has elapsed, clear timer and return true
        if(m_TimeSinceLastSpike[neuronIndex] > m_FlushTime)
        {
          m_TimeSinceLastSpike[neuronIndex] = 0;
          return true;
        }
      }
    }

    return false;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint16_t *m_TimeSinceLastSpike = NULL;
  uint32_t m_FlushTime;
};
} // Common