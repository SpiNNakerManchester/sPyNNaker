#!/usr/bin/env python
from matplotlib import pyplot as plt
import struct
from optparse import OptionParser

# Thanks Andrew!
def plot_spikes( population, title, timeStepMs ):
  plt.figure()
  plt.xlabel( "Time / ms" )
  plt.ylabel( "Neuron" )
  plt.title( title )
  for i,n in enumerate( population ):
    xs = map( lambda (i,s) : i*timeStepMs, filter( lambda (i,s) : s, enumerate( population[i] ) ) )
    plt.vlines( xs, i, i+.5, color='blue')

# Loads a bit-vector based spike recording output by SpiNNaker
def load_spike_recording(spikeFilename, numVectorWords):
  with open(spikeFilename, mode = 'rb') as spikeFile:
    # Read file contents
    spikeFileContents = spikeFile.read()
    
    # Read header word and thus calculate data length
    numVectorBytes = numVectorWords * 4
    numberOfBytesWritten = struct.unpack_from("<I", spikeFileContents)[0]
    numberOfTimeStepsWritten = numberOfBytesWritten / numVectorBytes
    print("Spike file contains %u bytes of spike data = %u simulation ticks" % (numberOfBytesWritten, numberOfTimeStepsWritten))
    
    population = []

    # Loop through ticks
    for tick in range(0, numberOfTimeStepsWritten):
      # Get offset into file data that the bit vector representing the state at this tick begins at
      vectorOffset = 4 + (tick * numVectorBytes)
      neurons = []
      
      # Loop through the words that make up this vector
      for neuronWordIndex in range(0, numVectorBytes, 4):
        # Unpack the word containing the spikingness of 32 neurons
        spikeVectorWord = struct.unpack_from("<I", spikeFileContents, vectorOffset + neuronWordIndex)
        
        # Loop through each bit in this word
        for neuronBitIndex in range(0, 32):
          # If the bit is set
          neuronBitMask = (1 << neuronBitIndex)
          neurons.append(1 if ((spikeVectorWord[0] & neuronBitMask) != 0) else 0)
      
      # Add volumn for this tick to population
      population.append(neurons)
      
    return population

# Entry point
if __name__ == "__main__":
  # Parse command line
  parser = OptionParser()
  parser.add_option("-f", "--file", dest = "filename", action = "store", type = "string", help = "file containing data written to memory by SpiNNaker")
  parser.add_option("-t", "--timestep", dest = "timestep", action = "store", type = "int", default = 1, help = "simulation timestep in ms")
  parser.add_option("-n", "--num-vector-words", dest = "numVectorWords", action = "store", type = "int", default= 8, help = "number of words that are used to represent a spike vector")
  (options, args) = parser.parse_args()
  
  if options.filename == None:
    parser.error("No filename specified")
  else:
    populations = load_spike_recording(options.filename, options.numVectorWords)

    plot_spikes(populations, "Spikes", options.timestep)
    plt.show()

