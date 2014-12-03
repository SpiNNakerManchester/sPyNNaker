
import numpy
import math
import matplotlib.pyplot as py_plot
import matplotlib.colors as colours
from pyNN.spiNNaker import *            # Imports the pyNN.spiNNaker module

population_colours = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#FF8000', '#FF0080', '#800000', '#008000', '#000080', '#808000', '#800080', '#008080', '#804000', '#800040', '#C00000', '#00C000', '#0000C0', '#C0C000', '#C000C0', '#00C0C0', '#C06000', '#C00060', '#400000', '#004000', '#000040', '#404000', '#400040', '#004040', '#402000', '#400020']
colour_map_pop = colours.ListedColormap(colors=population_colours, name='population_colour_label')
colour_range = colours.BoundaryNorm(boundaries=range(len(population_colours)), ncolors=len(population_colours), clip=True)

rng_weights=NumpyRNG(seed=369121518)
rng_positions=NumpyRNG(seed=248163264)

r_space = 6.25
conn_rate_ex_in = 4
conn_prob_scale = 0.5
conn_char_dist = 2.3
min_weight = 0.1
max_weight = 5.0
weight_scale_ex_in = 0.25
connection_dependence = "%f*math.exp(-(d**2)/(%f**2))"
weight_dependence_n = RandomDistribution(distribution='uniform', parameters=[1.0+min_weight, 1.0+max_weight], rng=rng_weights)
weight_dependence_e = RandomDistribution(distribution='uniform', parameters=[min_weight, max_weight], rng=rng_weights)
weight_dependence_i = RandomDistribution(distribution='uniform', parameters=[-(max_weight*weight_scale_ex_in), -min_weight], rng=rng_weights)
delay_dependence = "int(round((d/%f)*15.0))+1" % (2*r_space,)

pop_size = 1024
runtime = 10000.0
stim_start = 0.0
stim_rate = 10
pops_to_observe = ['mapped_pop_1', 'mapped_pop_2']

# Simulation Setup
setup(timestep=1.0, min_delay = 1.0, max_delay = 11.0, db_name='A46_NSM.sqlite')

# Neural Parameters
tau_m    = 24.0    # (ms)
cm       = 1
v_rest   = -65.0     # (mV)
v_thresh = -45.0     # (mV)
v_reset  = -65.0     # (mV)
t_refrac = 3.0       # (ms) (clamped at v_reset)
tau_syn_exc = 3.0
tau_syn_inh = tau_syn_exc*3

# cell_params will be passed to the constructor of the Population Object

cell_params = {
    'tau_m'      : tau_m,    'cm'         : cm,       'v_init'    : v_reset,
    'v_rest'     : v_rest,   'v_reset'    : v_reset,  'v_thresh'   : v_thresh,
    'tau_syn_E'       : tau_syn_exc,        'tau_syn_I'       : tau_syn_inh, 'tau_refrac'       : t_refrac, 'i_offset' : 0
    }
observed_pop_list = []
inputs = Population(pop_size,                                                      # size
                    SpikeSourcePoisson,                                            # Neuron Type
                    {'duration': runtime, 'start': stim_start, 'rate': stim_rate}, # Neuron Parameters
                    label="inputs")                                                # Label
if 'inputs' in pops_to_observe:
   inputs.record()
   observed_pop_list.append(inputs)

mapped_pop_1 = Population(pop_size,      # size
                          IF_curr_exp,   # Neuron Type
                          cell_params,   # Neuron Parameters
                          structure=RandomStructure(boundary=Sphere(radius=r_space), rng=rng_positions),
                          label="mapped_pop_1")
if 'mapped_pop_1' in pops_to_observe:
   mapped_pop_1.record()
   observed_pop_list.append(mapped_pop_1)

pop_inhibit = Population(pop_size,         # size
                         IF_curr_exp,      # Neuron Type
                         cell_params,      # Neuron Parameters
                         structure=RandomStructure(boundary=Sphere(radius=r_space), rng=rng_positions),
                         label="pop_inhibit")
if 'pop_inhibit' in pops_to_observe:
   pop_inhibit.record()
   observed_pop_list.append(pop_inhibit)

mapped_pop_2 = Population(pop_size,         # size
                          IF_curr_exp,   # Neuron Type
                          cell_params,   # Neuron Parameters
                          structure=RandomStructure(boundary=Sphere(radius=r_space), rng=rng_positions),
                          label="mapped_pop_2")
if 'mapped_pop_2' in pops_to_observe:
   mapped_pop_2.record()
   observed_pop_list.append(mapped_pop_2)

stimulate_pop_1 = Projection(inputs,
                             mapped_pop_1,
                             OneToOneConnector(weights=weight_dependence_n, delays=1.0),
                             target='excitatory')

stimulate_pop_I = Projection(mapped_pop_1,
                             pop_inhibit,
                             OneToOneConnector(weights=weight_dependence_e, delays=1.0),
                             target='excitatory')

inh_pop2 = Projection(pop_inhibit,
                      mapped_pop_2,
                      DistanceDependentProbabilityConnector(d_expression=connection_dependence % (conn_prob_scale/conn_rate_ex_in, conn_char_dist), weights=weight_dependence_i, delays=delay_dependence),
                      target='inhibitory')

pop1_pop2 = Projection(mapped_pop_1,
                       mapped_pop_2,
                       DistanceDependentProbabilityConnector(d_expression=connection_dependence % (conn_prob_scale, conn_char_dist), weights=weight_dependence_e, delays=delay_dependence),
                       target='excitatory')

run(runtime)

id_accumulator=0
for pop in observed_pop_list:
    state_colour = 0
    data = numpy.asarray(pop.getSpikes())
    if len(data) > 0:
       py_plot.scatter(x=data[:,0], y=data[:,1] + id_accumulator, s=8, c=data[:,1], marker='o', cmap=colour_map_pop, norm=colour_range, vmin=0, vmax=32) # s=1
    id_accumulator += pop.size
    id_accumulator += 5
state_plot = py_plot.gcf()
state_plot.set_frameon(True)        # Background on
state_plot.set_facecolor('#808080') # A grey background is easiest to see
py_plot.show()

