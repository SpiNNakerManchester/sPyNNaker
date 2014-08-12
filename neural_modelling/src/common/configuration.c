/*
 * configuration.c
 *
 *
 *  SUMMARY
 *    Configuration and neural data copying
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *
 *
 *  CREATION DATE
 *    9 August, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 9 August 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "common-impl.h"

// Globals
uint32_t system_word = 0;
uint32_t timer_period = 0;
uint32_t simulation_ticks = 0;

bool system_header_filled (uint32_t* address, uint32_t* version, uint32_t flags)
{
  use(flags);

  if (!check_magic_number (address)) {
    log_info("magic number is %08x", address[0]);
    return (false);
  }

  *version = address[1]; // version number extracted.

  log_info("magic = %08x, version = %d.%d", address[0],
           address[1] >> 16, address[1] & 0xFFFF);
  return (true);
}

bool system_data_filled (address_t address, uint32_t flags,
                         uint32_t *spike_history_recording_region_size, uint32_t *neuron_potentials_recording_region_size, uint32_t *neuron_gsyns_recording_region_size)
{
  use(flags);

  log_info("system_data_filled: starting");

  timer_period = address[1];
  simulation_ticks = address[2];

  // Read recording region sizes
  system_word = address[3];
  *spike_history_recording_region_size = address[4];
  *neuron_potentials_recording_region_size = address[5];
  *neuron_gsyns_recording_region_size = address[6];
  log_info("\ttimer period = %u, simulation ticks = %u", timer_period, simulation_ticks);
  log_info("\tsystem word = %08x, spike history recording region size = %u, neuron potential recording region size = %u, neuron gsyn recording region size = %u", system_word,
           *spike_history_recording_region_size, *neuron_potentials_recording_region_size, *neuron_gsyns_recording_region_size);

  return (true);
}

bool system_data_test_bit(system_data_e bit)
{
  return ((system_word & bit) != 0);
}

bool check_deadbeef (uint32_t* start) { return (start[0] == 0xDEADBEEF); }

bool check_magic_number (uint32_t* start) { return (start[0] == 0xAD130AD6); }

bool vector_copied (uint32_t* target, uint32_t n, uint32_t* data_source, uint32_t flags)
{
  uint32_t i;

  use(flags);
  log_info("v32[%u] = {%08x, ...}", n, data_source[0]);

  for (i = 0; i < n; i++)
    target[i] = data_source[i];

  return (true);
}

bool half_word_vector_copied (uint16_t* target, uint32_t n, uint32_t* data_source, uint32_t flags)
{
  uint32_t i;

  use(flags);
  log_info("v16[%u] = {%04x, ...}", n, data_source[0] & 0xFFFF);

  for (i = 0; i < (n >> 1); i++)
    ((uint32_t*)target)[i] = data_source[i];

  return (true);
}

bool byte_vector_copied (uint8_t* target, uint32_t n, uint32_t* data_source, uint32_t flags)
{
  uint32_t i;

  use(flags);

  log_info("v8 [%u] = {%02x, ...}", n, data_source[0] & 0xFF);

  for (i = 0; i < n; i++)
    target[i] = data_source[i] & 0xFF;

  return (true);
}

bool equal_vector (uint32_t n, uint32_t* x, uint32_t flags)
{
  bool equal = true;
  uint cmp;
  uint i;

  use(flags);
  assert(n > 0);

  cmp = x[0];

  for (i = 1; i < n; i++)
    if (cmp != x[i]) equal = false;

  return (equal);
}

address_t region_start (uint32_t n, address_t address)
{ return (configuration_reader_offset(address, 2+n)); }

address_t configuration_reader_offset(address_t address, uint32_t offset)
{ return (& address[address[offset] >> 2]); }
