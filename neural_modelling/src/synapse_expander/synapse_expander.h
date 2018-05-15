#pragma once

typedef enum regions_e {
    SYSTEM_REGION,           // 0
    NEURON_PARAMS_REGION,    // 1
    SYNAPSE_PARAMS_REGION,   // 2
    POPULATION_TABLE_REGION, // 3
    SYNAPTIC_MATRIX_REGION,  // 4
    SYNAPSE_DYNAMICS_REGION, // 5
    RECORDING_REGION,        // 6
    PROVENANCE_DATA_REGION,  // 7
    PROFILING_REGION,        // 8
    CONNECTOR_BUILDER_REGION,// 9
    DIRECT_MATRIX,           // 10
} regions_e;
