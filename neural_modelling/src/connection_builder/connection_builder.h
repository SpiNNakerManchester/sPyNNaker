#pragma once
#include <cstdint>

namespace ConnectionBuilder
{

#define REGION_START_INDEX 2

//-----------------------------------------------------------------------------
// Enumerations
//-----------------------------------------------------------------------------
// Indexes of synapse executable regions
enum Region
{
  RegionSystem,
  RegionKeyLookup,
  RegionSynapticMatrix,
  RegionPlasticity,
  RegionOutputBuffer,
  RegionDelayBuffer,
  RegionBackPropagationInput,
  RegionConnectionBuilder,
  RegionProfiler,
  RegionStatistics,
};

// Indices of application words
enum AppWord
{
  AppWordWeightFixedPoint,
  AppWordNumPostNeurons,
  AppWordFlushMask,
  AppWordMax,
};

//! human readable definitions of each region in SDRAM
// I think these should be in a higher level so c_main/conn_bldr can
// read them (change once, affect many)
    // names=[('SYSTEM', 0),
    //        ('NEURON_PARAMS', 1),
    //        ('SYNAPSE_PARAMS', 2),
    //        ('POPULATION_TABLE', 3),
    //        ('SYNAPTIC_MATRIX', 4),
    //        ('SYNAPSE_DYNAMICS', 5),
    //        ('RECORDING', 6),
    //        ('PROVENANCE_DATA', 7),
    //        ('PROFILING', 8),
    //        ('CONNECTOR_BUILDER', 9)])

typedef enum regions_e{
    SYSTEM_REGION,           //0
    NEURON_PARAMS_REGION,    //1
    SYNAPSE_PARAMS_REGION,   //2
    POPULATION_TABLE_REGION, //3
    SYNAPTIC_MATRIX_REGION,  //4
    SYNAPSE_DYNAMICS_REGION, //5
    RECORDING_REGION,        //6
    PROVENANCE_DATA_REGION,  //7
    PROFILING_REGION,
    CONNECTOR_BUILDER_REGION //9
} regions_e;

} // ConnectionBuilder
