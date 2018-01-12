#pragma once

// Standard includes
#include <cstdint>

// Rig CPP common includes
#include "rig_cpp_common/bit_field.h"
#include "rig_cpp_common/log.h"
#include "rig_cpp_common/spinnaker.h"
#include "rig_cpp_common/utils.h"

//-----------------------------------------------------------------------------
// Common::SpikeRecording
//-----------------------------------------------------------------------------
namespace Common
{
class SpikeRecording
{
public:
  SpikeRecording() : m_NumWords(0), m_CurrentBit(0), m_IndicesToRecord(NULL), m_RecordBuffer(NULL), m_RecordSDRAM(NULL) {}

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numNeurons)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "SpikeRecording::ReadSDRAMData");

    // Read number of words per sample from first word
    m_NumWords = *region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\tNum words per sample:%u", m_NumWords);

    // Calculate number of words that are required to build a bitfield for ALL neurons
    unsigned int numWords = BitField::GetWordSize(numNeurons);
    LOG_PRINT(LOG_LEVEL_INFO, "\tNum words per population:%u", numWords);

    // Copy indices to record
    if(!Utils::AllocateCopyStructArray(numWords, region, m_IndicesToRecord))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate indices to record array");
      return false;
    }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    BitField::PrintBits(IO_BUF, m_IndicesToRecord, numWords);
    io_printf(IO_BUF, "\n");
#endif

    // Cache pointer of subsequent data
    m_RecordSDRAM = region;
    LOG_PRINT(LOG_LEVEL_INFO, "\tRecording starting at %08x", m_RecordSDRAM);

    // If we need to record anything
    if(m_NumWords > 0)
    {
      // Allocate local record buffer
      m_RecordBuffer = (uint32_t*)spin1_malloc(m_NumWords * sizeof(uint32_t));
      if(m_RecordBuffer == NULL)
      {
        LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate local record buffer");
        return false;
      }
    }

    // Reset
    Reset();

    return true;
  }

  void RecordSpike(unsigned int neuron, bool spiked)
  {
    // If we should record this neuron's spikingness
    if(BitField::TestBit(m_IndicesToRecord, neuron))
    {
      // If current bit is beyond the end of the bitfield, spike buffer has
      // probably not been transferred and hence in reset so give and error
      if(m_CurrentBit >= (m_NumWords * 32))
      {
        LOG_PRINT(LOG_LEVEL_ERROR, "Recording spike past end of record buffer");
        return;
      }

      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tRecording neuron:%u, spikes:%u",
                neuron, spiked ? 1 : 0);

      // If it's spiked, set current bitm_SDRAMBuffers
      if(spiked)
      {
        BitField::SetBit(m_RecordBuffer, m_CurrentBit);
      }

      // Increment current bit
      m_CurrentBit++;
    }
  }

  void Reset()
  {
    // Reset current bit
    m_CurrentBit = 0;

    // Zero recording buffer
    BitField::Clear(m_RecordBuffer, m_NumWords);
  }

  void TransferBuffer(uint tag)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\tTransferring record buffer to SDRAM:%08x",
      m_RecordSDRAM);
#if LOG_LEVEL <= LOG_LEVEL_TRACE
    BitField::PrintBits(IO_BUF, m_RecordBuffer, m_NumWords);
    io_printf(IO_BUF, "\n");
#endif

    // Use DMA to transfer record buffer to SDRAM
    if(m_NumWords > 0)
    {
      spin1_dma_transfer(tag, m_RecordSDRAM,
                         m_RecordBuffer, DMA_WRITE,
                         m_NumWords * sizeof(uint32_t));

      // Advance SDRAM pointer
      m_RecordSDRAM += m_NumWords;
    }
  }

  bool IsReset() const
  {
    return (m_CurrentBit == 0);
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  // How many words to write to SDRAM every time step
  unsigned int m_NumWords;

  // Which bit within m_RecordBuffer should we set next
  unsigned int m_CurrentBit;

  // Bit field specifying which neurons to record
  uint32_t *m_IndicesToRecord;

  // Buffer into which one timestep worth of spiking data is written
  uint32_t *m_RecordBuffer;

  // Pointer in SDRAM to write next buffer to
  uint32_t *m_RecordSDRAM;
};
}