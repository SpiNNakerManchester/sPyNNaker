#pragma once

//----------------------------------------------------------------------------
// Common::RowOffsetLength
//----------------------------------------------------------------------------
namespace Common
{
template<unsigned int S>
class RowOffsetLength
{
public:
  RowOffsetLength(){}
  RowOffsetLength(uint32_t word) : m_Word(word){}
  RowOffsetLength(unsigned int numSynapses, unsigned int wordOffset)
    : m_Word((uint32_t)(numSynapses - 1) | (uint32_t)(wordOffset << S)){}

  //--------------------------------------------------------------------------
  // Public API
  //--------------------------------------------------------------------------
  uint32_t GetNumSynapses() const
  {
    return (m_Word & RowSynapsesMask) + 1;
  }

  uint32_t GetWordOffset() const
  {
    return (m_Word >> S);
  }

  uint32_t GetWord() const
  {
    return m_Word;
  }

private:
  //--------------------------------------------------------------------------
  // Constants
  //--------------------------------------------------------------------------
  static const uint32_t RowSynapsesMask = (1 << S) - 1;

  //--------------------------------------------------------------------------
  // Members
  //--------------------------------------------------------------------------
  uint32_t m_Word;
};
} // Common