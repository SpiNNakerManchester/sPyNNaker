#!/usr/bin/env python
import pylab
import struct
from optparse import OptionParser

# Loads a neuron parameter recording
def load_neuron_parameter_recording(parameterFilename, numNeurons, timeStepMs):
  with open(parameterFilename, mode = 'rb') as parameterFile:
    # Read file contents
    parameterFileContents = parameterFile.read()
    
    # Standard fixed-point 'accum' type scaling
    scale = float(0x7FFF)
    
    # Read header word and thus calculate data length
    numVectorBytes = numNeurons * 4
    numberOfBytesWritten = struct.unpack_from("<I", parameterFileContents)[0]
    numberOfTimeStepsWritten = numberOfBytesWritten / numVectorBytes
    print("Neuron parameter file contains %u bytes of spike data = %u simulation ticks" % (numberOfBytesWritten, numberOfTimeStepsWritten))
    
    parameterTimes = range(0, numberOfTimeStepsWritten * timeStepMs, timeStepMs)
    parameterValues = [[] for neuronID in range(numNeurons)]

    # Loop through neurons
    for neuronID in range(numNeurons):
      # Loop through ticks
      for tick in range(0, numberOfTimeStepsWritten):
        # Calculate offset to this neuron's parameter value this tick
        neuronParameterOffset = 4 + (tick * numVectorBytes) + (neuronID * 4)
        
        # Unpack and scale parameter word
        neuronParameterValue = float(struct.unpack_from("<i", parameterFileContents, neuronParameterOffset)[0]) / scale
        parameterValues[neuronID].append(neuronParameterValue)
    
    return parameterTimes, parameterValues

# Entry point
if __name__ == "__main__":
  # Parse command line
  parser = OptionParser()
  parser.add_option("-f", "--file", dest = "filename", action = "store", type = "string", help = "file containing data written to memory by SpiNNaker")
  parser.add_option("-t", "--timestep", dest = "timestep", action = "store", type = "int", default = 1, help = "simulation timestep in ms")
  parser.add_option("-n", "--num-neurons", dest = "numNeurons", action = "store", type = "int", help = "number of neurons")
  parser.add_option("-i", "--neuron-id", dest = "neuronID", action = "store", type = "int", help = "id of neuron's parameter to display")
  (options, args) = parser.parse_args()
  
  if options.filename == None:
    parser.error("No filename specified")
  elif options.numNeurons == None:
    parser.error("No number of neurons specified")
  else:
    parameters_t, parameters_value = load_neuron_parameter_recording(options.filename, options.numNeurons, options.timestep)

    # Make some graphs
    pylab.figure()
    
    # If no neuron IDs specified
    if options.neuronID == None:
      for neuronParameterValues in parameters_value:
        pylab.plot(parameters_t, neuronParameterValues, '.')
    # Otherwise, just plot one neuron's id
    else:
      pylab.plot(parameters_t, parameters_value[options.neuronID], '.')
      
    pylab.title('Parameter')
    pylab.show()

