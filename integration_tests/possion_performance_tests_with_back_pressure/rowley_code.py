import spynnaker.pyNN as p

n_inputs = 10000
rate = 2000
seed = 123456

p.setup(0.1)
input = p.Population(
    n_inputs, p.SpikeSourcePoisson, {"rate": rate, "seed": seed},
    label="Input")
output = p.Population(1, p.IF_curr_exp, {}, label="Output")
p.Projection(input, output, p.AllToAllConnector())

p.run(500)
p.end()