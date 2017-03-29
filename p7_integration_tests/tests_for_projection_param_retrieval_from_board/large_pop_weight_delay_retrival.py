import spynnaker.pyNN as p

if __name__ == '__main__':
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
    nNeurons = 900  # number of neurons in each population

    cell_params_lif = {'cm': 0.25,  # nF
                       'i_offset': 0.0,
                       'tau_m': 20.0,
                       'tau_refrac': 2.0,
                       'tau_syn_E': 5.0,
                       'tau_syn_I': 5.0,
                       'v_reset': -70.0,
                       'v_rest': -65.0,
                       'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 2.0
    delay = 1

    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))

    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_2'))

    projections.append(p.Projection(populations[0], populations[1],
                                    p.AllToAllConnector(weights=weight_to_spike,
                                                        delays=delay)))

    print "before"
    delays = projections[0].getDelays()
    weights = projections[0].getWeights()
    print delays
    print weights

    p.run(100)

    print "after"
    delays = projections[0].getDelays()
    weights = projections[0].getWeights()

    print delays
    print weights


    p.end(stop_on_board=True)