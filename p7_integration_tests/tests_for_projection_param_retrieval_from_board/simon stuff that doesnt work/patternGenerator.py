import numpy
from random import randint

class pattern(object):
    """
    """

    def __init__(self, totalNeurons, firing, cycleTime):
        """
        """
        self.totalNeurons = totalNeurons
        self.firing = firing
        self.cycleTime = cycleTime
        self.events = list()
        if (firing > 0):
            self.firingFrac = (totalNeurons * 1.0)/firing
        
    def generateRandomPattern(self):
        """
        """
        used = numpy.zeros(self.totalNeurons, dtype=numpy.int)
        self.events = list()
        for i in range(self.firing):
            pick = randint(1, self.totalNeurons-1) 
            while (used[pick] == 1):
                pick = randint(0, self.totalNeurons-1) 
            used[pick] = 1
            eventTime = randint(0, self.cycleTime-2)
            self.events.append((pick, eventTime))

    def printPattern(self):
        """
        """
        for el in self.events:
            print el

    def displayPattern(self):
        """
        """
        firingFrac = 1.0 * self.totalNeurons / self.firing
        print "Total neurons: ", self.totalNeurons
        print "Firing: ", self.firing, "(", firingFrac, "%)"
        print "Cycle time: ", self.cycleTime, "ms"
        print self.events

class spikeStream(object):
    """
    """
    def __init__(self):
        """
        """
        self.streams = list()

    def buildStream(self, numSources=None, patterns=None, interPatternGap=None, order=None, noise=None):
        """
        """
        # Create empty streams, one per source neuron:
        for i in range(numSources):
             self.streams.append(list())

        # Go through order parameter, which is a list of the patterns to be appended.
        # For each one, append it.
        timePtr = 0
        for entry in order:
            if entry == -1:
                # Create a gap (20ms):
                timePtr += 20
            else:
                if entry >= len(patterns):
                    print "ERROR: Pattern set requested pattern ", entry, \
                          " and pattern set has only ", len(patterns), " patterns"
                    return -1
                pattern = patterns[entry]
                biggestTimestamp = 0
                for element in pattern.events:
                    index, timestamp = element
                    biggestTimestamp = max(biggestTimestamp, timestamp)
                    self.streams[index].append(timePtr + timestamp)
                timePtr += biggestTimestamp + interPatternGap

