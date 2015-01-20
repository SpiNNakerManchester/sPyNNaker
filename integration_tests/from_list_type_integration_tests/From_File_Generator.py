
import numpy
# import math
from pyNN.spiNNaker import *            # Imports the pyNN.spiNNaker module

pop_size = 32

rng_weights=NumpyRNG(seed=369121518)
rng_connections=NumpyRNG(seed=453276549)

min_weight = 0.1
max_weight = 30.0
weight_scale_ex_in = 0.25
weight_dependence_e = RandomDistribution(distribution='uniform', parameters=[min_weight, max_weight], rng=rng_weights)
weight_dependence_i = RandomDistribution(distribution='uniform', parameters=[-(max_weight*weight_scale_ex_in), -min_weight], rng=rng_weights)
connection_dependence_I_p2 = RandomDistribution(distribution='uniform', parameters=[0, 1], rng=rng_connections).next(pop_size*pop_size)
connection_dependence_p1_p2 = RandomDistribution(distribution='uniform', parameters=[0, 1], rng=rng_connections).next(pop_size*pop_size)

for form_I_p2 in range(4):
    I_p2_file = open('List_I_p2_form_%d.txt' % (form_I_p2+1,), 'w')
    list_I_p2 = [(i, j, weight_dependence_i.next(), 4.0) for i in range(pop_size) for j in range(pop_size) if connection_dependence_I_p2[pop_size*i+j] > 0.5]
    if form_I_p2 == 0:
       I_p2_file.write("%s" % list_I_p2)
    elif form_I_p2 == 1:
       I_p2_file.writelines(["%s\n" % (conn,) for conn in list_I_p2])
    elif form_I_p2 == 2:
       I_p2_file.writelines(["%s %s %.17f %.17f\n" % (conn[0], conn[1], conn[2], conn[3]) for conn in list_I_p2])
    elif form_I_p2 == 3:
       I_p2_file.writelines(["%s, %s, %.17f, %.17f\n" % (conn[0], conn[1], conn[2], conn[3]) for conn in list_I_p2])
    I_p2_file.close()
for form_p1_p2 in range(4):
    p1_p2_file = open('List_p1_p2_form_%d.txt' % (form_p1_p2+1,), 'w')
    list_p1_p2 = [(i, j, weight_dependence_e.next(), 4.0) for i in range(pop_size) for j in range(pop_size) if connection_dependence_p1_p2[pop_size*i+j] > 0.5]
    if form_p1_p2 == 0:
       p1_p2_file.write("%s" % list_p1_p2)
    elif form_p1_p2 == 1:
       p1_p2_file.writelines(["%s\n" % (conn,) for conn in list_p1_p2])
    elif form_p1_p2 == 2:
       p1_p2_file.writelines(["%s %s %.17f %.17f\n" % (conn[0], conn[1], conn[2], conn[3]) for conn in list_p1_p2])
    elif form_p1_p2 == 3:
       p1_p2_file.writelines(["%s, %s, %.17f, %.17f\n" % (conn[0], conn[1], conn[2], conn[3]) for conn in list_p1_p2])
    p1_p2_file.close()

