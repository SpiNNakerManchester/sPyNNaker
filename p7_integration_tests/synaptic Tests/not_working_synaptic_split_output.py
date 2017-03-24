import spynnaker.pyNN as p
import retina_lib

if __name__ == '__main__':
    input_size = 128             # Size of each population
    subsample_size = 32
    runtime = 60
    # Simulation Setup
    p.setup(timestep=1.0, min_delay = 1.0, max_delay = 11.0)            # Will add some extra parameters for the spinnPredef.ini in here

    p.set_number_of_neurons_per_core('IF_curr_exp', 128)      # this will set one population per core

    cell_params = { 'tau_m' : 64, 'i_offset'  : 0,
        'v_rest'    : -75,  'v_reset'    : -95, 'v_thresh'   : -40,
        'tau_syn_E' : 15,   'tau_syn_I'  : 15,  'tau_refrac' : 2}



    #external stuff population requiremenets
    connected_chip_coords = {'x': 0, 'y': 0}
    virtual_chip_coords = {'x': 0, 'y': 5}
    link = 4


    print "Creating input population: %d x %d" % (input_size, input_size)

    input_pol_1_up = p.Population(128*128,
                                   p.ExternalRetinaDevice,
                                   {'virtual_chip_coords': virtual_chip_coords,
                                    'connected_chip_coords':connected_chip_coords,
                                    'connected_chip_edge':link,
                                    'unique_id': 'R',
                                    "polarity": p.ExternalRetinaDevice.UP_POLARITY},
                                   label='input_pol_1up')

    input_pol_1_down = p.Population(128*128,
                                   p.ExternalRetinaDevice,
                                   {'virtual_chip_coords': virtual_chip_coords,
                                    'connected_chip_coords':connected_chip_coords,
                                    'connected_chip_edge':link,
                                    'unique_id': 'R',
                                    "polarity": p.ExternalRetinaDevice.DOWN_POLARITY},
                                   label='input_pol_1down')

    subsampled = p.Population(subsample_size*subsample_size,         # size
                              p.IF_curr_exp,   # Neuron Type
                              cell_params,   # Neuron Parameters
                              label="Input") # Label
    subsampled.initialize('v', -75)

    subsampled.set_mapping_constraint({'x':0,'y':1})
    #subsampled.record()     # sends spikes to the visualiser (use parameters = 32)

    list_input = retina_lib.subSamplerConnector2D(128,subsample_size,.2,1)
    #print "input list is :"
    #print list_input

    p1_up = p.Projection(input_pol_1_up,
                      subsampled,
                      p.FromListConnector(list_input),
                      label='subsampling projection')

    p2_down = p.Projection(input_pol_1_down,
                      subsampled,
                      p.FromListConnector(list_input),
                      label='subsampling projection')

    p.run(runtime)              # Simulation time
    p.end()