import pyNN.spiNNaker as p
from matplotlib import pylab

p.setup(1.0)

# p.set_number_of_neurons_per_core(p.SpikeSourcePoisson, 27)
# p.set_number_of_neurons_per_core(p.IF_curr_exp, 22)

inp = p.Population(100, p.SpikeSourcePoisson, {"rate": 100}, label="input")
pop = p.Population(100, p.IF_curr_exp, {}, label="pop")

p.Projection(inp, pop, p.OneToOneConnector(weights=100.0))

pop.record()
inp.record()

p.run(100)

# inp.set("rate", 10)
# pop.set("cm", 10)
# pop.set("tau_syn_E", 100)
#
# p.run(100)

pop_spikes = pop.getSpikes()
inp_spikes = inp.getSpikes()

pylab.figure()
pylab.plot(pop_spikes[:, 1], pop_spikes[:, 0], "b.")
pylab.show()

# p.reset()
#
# inp.set("rate", 0)
#
# p.run(100)
#
# print pop.getSpikes()

p.end()
