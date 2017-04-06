'''
LOG BASAB 16TH OF JANUARY 2017:
THE STN SPIKE RATE OUTPUT WTIH VARYING CURRENT BIAS IS BEING TESTED WHILE THERE IS ALSO A 3 HZ POISSON INPUT PRESENT
TO THE POPULATION. THE OUTPUT IS STORED IN AN ARRAY AND AS A .CSV FILE AS ABOVE, BUT NOW WITH NOISE INPUT.
THE GRAPHS ARE PLOTTED IN IPYTHON, THE CODE IS STORED IN ~/. AS PLOTTINGGRAPHS.IPYNB.

LOG BASAB 11TH AND 12TH OF JANUARY: GENERATED SPIKE RATE WITH VARYING CURRENT BIAS - IN LOOP. SAVED AS .CSV
IN DATAFILES FOLDER.

'''

# !/usr/bin/python

import numpy as np
import matplotlib.pylab as plt
import pylab
from pylab import *
import spynnaker.pyNN as p
from pyNN.random import NumpyRNG, RandomDistribution

import time

start_time = time.time()

TotalDuration = 5000  ### TOTAL RUN TIME
TimeInt = 0.1  ### SIMULATION TIME STEP
TotalDataPoints = int(TotalDuration * (1 / TimeInt))

stn_a = 0.005
stn_b = 0.265
stn_c = -65.0
stn_d = 2.0
stn_v_init = -60.0
stn_u_init = stn_b * stn_v_init

tau_ampa = 6  ###excitatory synapse time constant
tau_gabaa = 4  ### inhibitory synapse time constant
E_ampa = 0.0
E_gabaa = -80.0

scale_fact = 100  ###SCALING UP THE NUMBER OF NEURONS
numCellsPerCol = 3 * scale_fact

'''CHANGING THE CURRENT BIAS IN THE DEFINED DICTIONARY OF IZHIKEVICH NEURON AND OBSERVING MODEL RESPONSE'''
# current_bias = -0.2
# current_bias_arr = np.asarray(range(0, 31)) ## NOT MEANT TO FIRE FOR NEGATIVE DC BIAS
current_bias_arr = [0, 10, 0, -10, 0]

stnspikecountArr = np.zeros((len(current_bias_arr)))

''' SET UP SPINNAKER AND BEGIN SIMULATION'''
p.setup(timestep=0.1, min_delay=1.0, max_delay=14.0)

current_bias = 0

'''SUB-THALAMIC NUCLEUS OF THE BASAL GANGLIA'''

stn_cell_params = {'a': stn_a, 'b': stn_b, 'c': stn_c, 'd': stn_d,
                   'v_init': stn_v_init, 'u_init': stn_u_init,
                   'tau_syn_E': tau_ampa, 'tau_syn_I': tau_gabaa,
                   'i_offset': current_bias,
                   'e_rev_E': E_ampa, 'e_rev_I': E_gabaa,
                   }

stn_pop1 = p.Population(numCellsPerCol, p.IZK_cond_exp, stn_cell_params,
                        label='stn_pop1')

'''RECORD THE POPULATION RESPONSE'''

stn_pop1.record()
stn_pop1.record_v()

'''RUN FOR TOTAL DURATION'''
p.run(1000)

stn_pop1.set('i_offset', 10)

p.run(1000)

'''RUN COMPLETE; NOW GO GET SPIKES AND MEMBRANE VOLTAGES'''
stn_spike_raster1 = np.asarray(stn_pop1.getSpikes())

# stn_membrane_volt1 =  stn_pop1.get_v()

stnspikecount1 = stn_pop1.meanSpikeCount() / (TotalDuration / 1000)

# stn_pop1.print_v(foldername+'/stnmempot.dat')

'''STRUCTURE DATA FOR OBTAINING THE AVERAGE VOLTAGE OVER THE POPULATION'''

# signalstn = np.reshape(stn_membrane_volt1[: ,2], [numCellsPerCol, TotalDataPoints], order='C')
# print('reshaped the signal as 2D matrix')
# avgsignalstn = mean(signalstn, axis=0) ## mean along the rows

# print ('obtained mean of the signal')
# print('current bias for this loop is %d') %current_bias



print stnspikecount1
# print ('now k is %d') % k
# stnspikecountArr[k] = stnspikecount1
# p.end()
#
# print ('ok out of the loop now')
# stnspikecountArr = np.asarray(stnspikecountArr)
# print stnspikecountArr
# np.savetxt('./datafiles/stnspikecountArr.csv', stnspikecountArr)

f1 = plt.figure
n_plots_1 = 3
plot = 1
numcols = 1
plt.subplot(n_plots_1, numcols, plot)
plot += 1
if len(stn_spike_raster1) > 0:
    plt.scatter(stn_spike_raster1[:, 1], stn_spike_raster1[:, 0],
                color='violet', s=1)
plt.xlabel('Time/ms')
plt.ylabel('number of neurons')
plt.title('Spike raster for STN')
plt.xlim(-100, TotalDuration)
#
# plt.subplot(n_plots_1, numcols, plot)
# plot += 1
# plt.plot(avgsignalstn[0:TotalDataPoints:10], color='violet')
# plt.xlabel('Time/ms')
# plt.ylabel('membrane potential/mV')
# plt.title('STN MEMBRANE VOLTAGE')
# plt.xlim(-100, TotalDuration)
#
# plt.subplot(n_plots_1, numcols, plot)
# plot += 1
# plt.plot(avgsignalstn, color='purple')
# plt.xlabel('Time/ms')
# plt.ylabel('membrane potential/mV')
# plt.title('STN MEMBRANE VOLTAGE')
# plt.xlim(-1000, TotalDataPoints)
#
#
# plt.show(f1)
