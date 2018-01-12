#pragma once

// Standard includes
#include <cstdint>

// Connection builder includes
#include "generator_factory.h"
#include "kernel_maths.h"

// Forward declarations
namespace Common
{
  namespace Random
  {
    class MarsKiss64;
  }
}

// Namespaces
using namespace Common::Random;

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerator
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
namespace ParamGenerator
{
/*binomial':       ('n', 'p'),
'gamma':          ('k', 'theta'),
'exponential':    ('beta',),
'lognormal':      ('mu', 'sigma'),
'normal':         ('mu', 'sigma'),
'normal_clipped': ('mu', 'sigma', 'low', 'high'),
'normal_clipped_to_boundary':
                  ('mu', 'sigma', 'low', 'high'),
'poisson':        ('lambda_',),
'uniform':        ('low', 'high'),
'uniform_int':    ('low', 'high'),*/
//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
class Base
{
public:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        uint32_t pre_idx, uint32_t post_start, uint16_t (indices)[512],
                        MarsKiss64 &rng, int32_t (&integers)[512]) const = 0;
};


class ConvKernel : public Base{
  public:
    ADD_FACTORY_CREATOR(ConvKernel);

  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        uint32_t pre_idx, uint32_t post_start, uint16_t (indices)[512],
                        MarsKiss64 &rng, int32_t (&output)[512]) const;

  private:
    ConvKernel(uint32_t *&);

    uint16_t m_commonHeight;
    uint16_t m_commonWidth;

    uint16_t m_preHeight;
    uint16_t m_preWidth;
    uint16_t m_postHeight;
    uint16_t m_postWidth;

    uint16_t m_startPreHeight;
    uint16_t m_startPreWidth;
    uint16_t m_startPostHeight;
    uint16_t m_startPostWidth;

    uint16_t  m_stepPreWidth;
    uint16_t  m_stepPreHeight;
    uint16_t  m_stepPostWidth;
    uint16_t  m_stepPostHeight;

    uint16_t  m_kernelWidth;
    uint16_t  m_kernelHeight;

    int32_t *m_values;
};


//-----------------------------------------------------------------------------
// Constant
//-----------------------------------------------------------------------------
class Constant : public Base
{
public:
  ADD_FACTORY_CREATOR(Constant);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        uint32_t pre_idx, uint32_t post_start, uint16_t (indices)[512],
                        MarsKiss64 &rng, int32_t (&output)[512]) const;

private:
  Constant(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Value;
};

//-----------------------------------------------------------------------------
// Uniform
//-----------------------------------------------------------------------------
class Uniform : public Base
{
public:
  ADD_FACTORY_CREATOR(Uniform);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        uint32_t pre_idx, uint32_t post_start, uint16_t (indices)[512],
                        MarsKiss64 &rng, int32_t (&output)[512]) const;

private:
  Uniform(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Low;
  int32_t m_Range;
};

//-----------------------------------------------------------------------------
// Normal
//-----------------------------------------------------------------------------
class Normal : public Base
{
public:
  ADD_FACTORY_CREATOR(Normal);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        uint32_t pre_idx, uint32_t post_start, uint16_t (indices)[512],
                        MarsKiss64 &rng, int32_t (&output)[512]) const;

private:
  Normal(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Mu;
  int32_t m_Sigma;
};

//-----------------------------------------------------------------------------
// Normal clipped
//-----------------------------------------------------------------------------
class NormalClipped : public Base
{
public:
  ADD_FACTORY_CREATOR(NormalClipped);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        uint32_t pre_idx, uint32_t post_start, uint16_t (indices)[512],
                        MarsKiss64 &rng, int32_t (&output)[512]) const;

private:
  NormalClipped(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Mu;
  int32_t m_Sigma;
  int32_t m_Low;
  int32_t m_High;
};

//-----------------------------------------------------------------------------
// Normal clipped to boundary
//-----------------------------------------------------------------------------
class NormalClippedToBoundary : public Base
{
public:
  ADD_FACTORY_CREATOR(NormalClippedToBoundary);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        uint32_t pre_idx, uint32_t post_start, uint16_t (indices)[512],
                        MarsKiss64 &rng, int32_t (&output)[512]) const;

private:
  NormalClippedToBoundary(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Mu;
  int32_t m_Sigma;
  int32_t m_Low;
  int32_t m_High;
};

//-----------------------------------------------------------------------------
// Exponential
//-----------------------------------------------------------------------------
class Exponential : public Base
{
public:
  ADD_FACTORY_CREATOR(Exponential);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        uint32_t pre_idx, uint32_t post_start, uint16_t (indices)[512],
                        MarsKiss64 &rng, int32_t (&output)[512]) const;

private:
  Exponential(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Beta;
};
 
} // ParamGenerator
} // ConnectionBuilder
