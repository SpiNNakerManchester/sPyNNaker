import spynnaker.pyNN as sim

sim.setup(timestep=1.0, min_delay=1.0, max_delay=1.0)

simtime = 1000

pg_pop1 = sim.Population(2, sim.SpikeSourcePoisson,
                         {'rate': 10.0, 'start':0,
                          'duration':simtime}, label="pg_pop1")
pg_pop2 = sim.Population(2, sim.SpikeSourcePoisson,
                         {'rate': 10.0, 'start':0,
                          'duration':simtime}, label="pg_pop2")

pg_pop1.record()
pg_pop2.record()

sim.run(simtime)

spikes1 = pg_pop1.getSpikes(compatible_output=True)
spikes2 = pg_pop2.getSpikes(compatible_output=True)

print spikes1
print spikes2

sim.end()
