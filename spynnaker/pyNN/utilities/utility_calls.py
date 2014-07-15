__author__ = 'stokesa6'
import os


'''
helper method that chekcs if a directory exists
'''


def check_directory_exists(filename):
    components = os.path.abspath(filename).split(os.sep)
    directory = os.path.abspath(os.path.join(os.sep,
                                             *components[1:len(components)-1]))
    #check if directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)


def is_conductance(population):
    raise NotImplementedError


def check_weight(weight, synapse_type, is_conductance_type):
    raise NotImplementedError


def check_delay(delay):
    raise NotImplementedError

