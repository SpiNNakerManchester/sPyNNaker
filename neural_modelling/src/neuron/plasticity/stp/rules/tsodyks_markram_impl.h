#ifndef TSODYKS_MARKRAM_IMPL_H
#define TSODYKS_MARKRAM_IMPL_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// sPyNNaker neural modelling includes
#include <debug.h>

// sPyNNaker plasticity common includes
#include "../../common/maths.h"
#include "../../common/stdp_typedefs.h"

//---------------------------------------
// Structures
//---------------------------------------
typedef struct
{
  int32_t asymptotic_prob_release;
  int32_t tau_rec_over_psc_rec;
  int32_t tau_psc_over_psc_rec;
} stp_region_data_t;

typedef struct
{
  int16_t u;
  int16_t x;
  int16_t y;
} stp_trace_t;

typedef int16_t stp_update_state_t;

typedef struct
{
  stp_trace_t trace;
  stp_update_state_t update_state;
} stp_result_t;

//---------------------------------------
// Macros
//---------------------------------------
// Exponential decay lookup parameters
#define TAU_SYN_LUT_SHIFT 0
#define TAU_SYN_LUT_SIZE 256

#define TAU_REC_LUT_SHIFT 3
#define TAU_REC_LUT_SIZE 1136

#define TAU_FAC_LUT_SHIFT 3
#define TAU_FAC_LUT_SIZE 1136

// Helper macros for looking up decays
#define DECAY_TAU_SYN(t) \
    maths_lut_exponential_decay(t, TAU_SYN_LUT_SHIFT, TAU_SYN_LUT_SIZE, tau_syn_lut)
#define DECAY_TAU_REC(t) \
    maths_lut_exponential_decay_rounded(t, TAU_REC_LUT_SHIFT, TAU_REC_LUT_SIZE, tau_rec_lut)
#define DECAY_TAU_FAC(t) \
    maths_lut_exponential_decay_rounded(t, TAU_FAC_LUT_SHIFT, TAU_FAC_LUT_SIZE, tau_fac_lut)

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t tau_syn_lut[TAU_SYN_LUT_SIZE];
extern int16_t tau_rec_lut[TAU_REC_LUT_SIZE];
extern int16_t tau_fac_lut[TAU_FAC_LUT_SIZE];

extern stp_region_data_t stp_region_data;

//---------------------------------------
// STP inline functions
//---------------------------------------
static inline stp_result_t stp_add_pre_spike(uint32_t time,
    uint32_t last_time, stp_trace_t last_trace)
{
  // Get time since last spike
  const uint32_t delta_time = time - last_time;

  // Calculate exponential decay of delta
  // time with all three time constants
  const int32_t p_uu = DECAY_TAU_FAC(delta_time);
  const int32_t p_yy = DECAY_TAU_SYN(delta_time);
  const int32_t p_zz = DECAY_TAU_REC(delta_time);

  // **TODO** this is a mess - re-order and implement in a less state-mutating manner

  const int32_t p_xy = STDP_FIXED_MUL_16X16(p_zz - STDP_FIXED_POINT_ONE, stp_region_data.tau_rec_over_psc_rec)
    - STDP_FIXED_MUL_16X16(p_yy - STDP_FIXED_POINT_ONE, stp_region_data.tau_psc_over_psc_rec);
  const int32_t p_xz = STDP_FIXED_POINT_ONE - p_zz;

  const int32_t z = STDP_FIXED_POINT_ONE - last_trace.x - last_trace.y;

  int32_t new_u = STDP_FIXED_MUL_16X16(last_trace.u, p_uu)
    + STDP_FIXED_MUL_16X16(stp_region_data.asymptotic_prob_release, STDP_FIXED_POINT_ONE - last_trace.u);
  int32_t new_x = last_trace.x + STDP_FIXED_MUL_16X16(p_xy, last_trace.y)
    + STDP_FIXED_MUL_16X16(p_xz, z);
  int32_t new_y = STDP_FIXED_MUL_16X16(last_trace.y, p_yy);

  // delta function u
  new_u += STDP_FIXED_MUL_16X16(stp_region_data.asymptotic_prob_release,
                                STDP_FIXED_POINT_ONE - new_u);

  // postsynaptic current step caused by incoming spike
  const int32_t delta_y_tsp = STDP_FIXED_MUL_16X16(new_u, new_x);

  // delta function x, y
  new_x -= delta_y_tsp;
  new_y += delta_y_tsp;

  // Return new STP update state with new trace and
  // delta_y_tsp value required to apply STP to weights
  return (stp_result_t){
    .trace = (stp_trace_t){ .u = new_u, .x = new_x, .y = new_y },
    .update_state = delta_y_tsp,
  };
}
//---------------------------------------
static inline weight_t stp_apply(uint32_t weight, stp_update_state_t update_state)
{
  // Multiply weight by delta_y_tsp
  // **NOTE** this leaves result in whatever fixed-point format weight is in
  return STDP_FIXED_MUL_16X16(update_state, weight);
}

//---------------------------------------
// STP functions
//---------------------------------------
address_t stp_initialise(address_t address);

#endif  // TSODYKS_MARKRAM_IMPL_H