import numpy
import math
import itertools
import re
import copy

debug = False

def attention_metric(fixation_point = (0,0), preferred_objs=None, aversive_objs=None, neutral_objs=None):
    if preferred_objs == None: preferred_objs = []
    if aversive_objs == None: aversive_objs = []
    if neutral_objs == None: neutral_objs = []
    preferred_dists = [math.sqrt((obj[0][0]-fixation_point[0])**2+(obj[0][1]-fixation_point[1])**2) + math.sqrt((obj[1][0]-fixation_point[0])**2+(obj[1][1]-fixation_point[1])**2) for obj in preferred_objs]
    aversive_dists = [math.sqrt((obj[0][0]-fixation_point[0])**2+(obj[0][1]-fixation_point[1])**2) + math.sqrt((obj[1][0]-fixation_point[0])**2+(obj[1][1]-fixation_point[1])**2) for obj in aversive_objs]
    neutral_dists = [math.sqrt((obj[0][0]-fixation_point[0])**2+(obj[0][1]-fixation_point[1])**2) + math.sqrt((obj[1][0]-fixation_point[0])**2+(obj[1][1]-fixation_point[1])**2) for obj in preferred_objs]

    """
    Sum up the combined contributions from each of the distances from fixation point to targets.
    There are the following contributions:

    preferred-preferred: radial clustering of distances to preferred targets, between different
    fixation points. Small radii and tight clusterings are desirable. Thus the distances should
    be similar and the overall radius small. 
    Small distances, small radii => large contribution to metric

    preferred-aversive: radial anti-clustering of distance to preferred and distance to aversive
    targets, between fixation points. A given fixation ideally is far away from aversive targets
    and near to preferred targets. Thus the distances should be very different and the overall
    radius small.
    Large distances, small radii => large contribution to metric

    preferred-neutral: radial non-anti-clustering of distance to preferred and distance to neutral
    targets, between fixation points. Fixations should be near to preferred targets without any 
    particular relation to neutral targets. Thus the distances should be different and biassed towards
    the preferred target, and the overall radius small.
    Large non-negative distances, small radii => large contribution to metric

    aversive-aversive: radial clustering of distances to aversive targets, between fixation points.
    Large radii and tight clusterings are desirable (tight because they cluster near the preferred
    objects). Thus the distances should be similar and the overall radius large
    Small distances, large radii => large contribution to metric

    aversive-neutral: radial anti-clustering of distance to aversive and distance to neutral 
    targets, between fixation points. Fixations should be far away from aversive targets without 
    any particular relation to neutral targets. Thus the distances should be very different and 
    the overall radius large
    Large distances, large radii => large contribution to metric 
    
    """
    metric = 0
    #metric += reduce(lambda x, y: x+reduce(lambda a, b: a+(abs(preferred_dists[y]-b)/(preferred_dists[y]+b)), preferred_dists[y+1:], 0), range(len(preferred_dists)), 0) # preferred-preferred
    metric += reduce(lambda x, y: x+reduce(lambda a, b: a+(1/(abs(preferred_dists[y]-b)*(preferred_dists[y]+b))), preferred_dists[y+1:], 0), range(len(preferred_dists)), 0) # preferred-preferred
    metric += reduce(lambda x, y: x+reduce(lambda a, b: a+((aversive_dists[y]-b)/(aversive_dists[y]+b)), preferred_dists, 0), range(len(aversive_dists)), 0)             # preferred-aversive
    metric += reduce(lambda x, y: x+reduce(lambda a, b: a+(max(neutral_dists[y]-b, 0)/(neutral_dists[y]+b)), preferred_dists, 0), range(len(neutral_dists)), 0)          # preferred-neutral
    metric += reduce(lambda x, y: x+reduce(lambda a, b: a-(1/(abs(aversive_dists[y]-b)*(aversive_dists[y]+b))), aversive_dists[y+1:], 0), range(len(aversive_dists)), 0)     # aversive-aversive
    metric += reduce(lambda x, y: x+reduce(lambda a, b: a-(1/((aversive_dists[y]-b)*(aversive_dists[y]+b))), neutral_dists, 0), range(len(aversive_dists)), 0)               # aversive-neutral
    #metric += reduce(lambda x, y: x+reduce(lambda a, b: a-(abs(aversive_dists[y]-b)/(aversive_dists[y]+b)), aversive_dists[y+1:], 0), range(len(aversive_dists)), 0)     # aversive-aversive
    #metric += reduce(lambda x, y: x+reduce(lambda a, b: a+((aversive_dists[y]-b)/(aversive_dists[y]+b)), neutral_dists, 0), range(len(aversive_dists)), 0)               # aversive-neutral
    return metric

def attn_performance_monitor(data, objects, y_dim, t_window=None, t_w_offset=None, t_start=None, t_stop=None, t_pos=0):
    if t_pos == 1:
       data = numpy.fliplr(data)
    data.sort(axis=0) 
    if t_window == None: t_window = data[-1,0]-data[0,0]
    if t_w_offset == None: t_w_offset = t_window/2
    if t_start == None: t_start = data[0,0]
    if t_stop == None: t_stop = data[-1,0]
    data_ranges = [[datum for datum in data if datum[0] >= t-t_w_offset and datum[0] < t-t_w_offset+t_window] for t in range(int(t_start+t_w_offset), int(t_stop), int(t_window))]
    data_range_times = [set([d_t[0] for d_t in d_range]) for d_range in data_ranges]
    data_groups = itertools.izip(data_ranges, data_range_times)
    if debug:
       performance_measures = []
       debug_file = open('vis_metric_dbg.txt', 'w')
       debug_file.write("objects in visual field: %s\n" % objects)
       for group in range(len(data_ranges)):
           total_metric = 0
           debug_file.write("active spiking times for group %d: %s\n" % (group, data_range_times[group]))
           for spike in data_ranges[group]:
               debug_file.write("t=%d, coordinate=%s\n" % (spike[0], (int(spike[1])/y_dim, int(spike[1])%y_dim)))
           for time in data_range_times[group]:
               instantaneous_metric = [0, []]
               for spike in data_ranges[group]:
                   if spike[0] == time:
                      fixation_point = (int(spike[1])/y_dim, int(spike[1])%y_dim)
                      if fixation_point not in [point[0] for point in instantaneous_metric[1]]:
                         local_metric = attention_metric(fixation_point=fixation_point, preferred_objs=objects['preferred'], aversive_objs=objects['aversive'], neutral_objs=objects['neutral'])
                         instantaneous_metric[0] += local_metric
                         instantaneous_metric[1].append((fixation_point, local_metric))
               debug_file.write("active time %d, metrics %s\n" % (time, instantaneous_metric))
               total_metric += instantaneous_metric[0]
           total_metric /= t_window
           debug_file.write("Total metric for time window %d: %f" % (group, total_metric))
           performance_measures.append(total_metric)
       debug_file.close()
    # complicated data reduction does the following:
    # 1: break up the data into groups belonging to a specific time window
    # 2: break up each group into the separate times where there is at least one fixation point
    # 3: aggregate the attention metrics, for each fixation point within a given time slot
    # 4: aggregate these aggregations, over the whole time window
    # 5: divide by the number of active time slots in the window
    else:
       performance_measures = [reduce(lambda x, y: x+y, [reduce(lambda x, y: x+attention_metric(fixation_point=(int(y[1])/y_dim, int(y[1])%y_dim), preferred_objs=objects['preferred'], aversive_objs=objects['aversive'], neutral_objs=objects['neutral']), frame, 0) for frame in [[fixation_point for fixation_point in d_group[0] if fixation_point[0] == f_time] for f_time in d_group[1]]], 0)/t_window for d_group in data_groups] 
    return performance_measures

def get_annotations(input_file_name):
    annotated_objs={'horizontal': [], 'vertical': [], 'diagonal': [], 'counterdiagonal': [], 'balanced': []}
    with open(input_file_name, 'r') as fsource:
            read_data = fsource.readlines()

    for line in read_data:
        line.strip()
        if not line.startswith('#'): pass
        elif re.match(r'#\s*horizontal.*', line): # read in preferred positions
           annotated_objs['horizontal'].append(eval(line.partition('=')[2]))
        elif re.match(r'#\s*vertical.*', line):
           annotated_objs['vertical'].append(eval(line.partition('=')[2]))
        elif re.match(r'#\s*diagonal.*', line):
           annotated_objs['diagonal'].append(eval(line.partition('=')[2]))
        elif re.match(r'#\s*counterdiagonal.*', line):
           annotated_objs['counterdiagonal'].append(eval(line.partition('=')[2]))
        elif re.match(r'#\s*balanced.*', line):
           annotated_objs['balanced'].append(eval(line.partition('=')[2]))
    return annotated_objs

def scale_annotations(annotations, scale_x=1.0, scale_y=1.0):
    scaled_annotations = {}
    for category in annotations:
        scaled_annotations[category] = [((obj[0][0]*scale_x, obj[0][1]*scale_y), (obj[1][0]*scale_x, obj[1][1]*scale_y)) for obj in annotations[category]]
    return scaled_annotations

def bias_annotations(annotations, preferred=None, aversive=None):
    orientations = ['horizontal', 'diagonal', 'vertical', 'counterdiagonal', 'balanced']
    biassed_objs = {'preferred': [], 'aversive': [], 'neutral': []}
    if preferred != None:
       biassed_objs['preferred'].extend(annotations[orientations[preferred]])
    if aversive != None:
       biassed_objs['aversive'].extend(annotations[orientations[aversive]])
    for index in [i for i in range(len(orientations)) if i != preferred and i != aversive]:
       biassed_objs['neutral'].extend(annotations[orientations[index]])
    return biassed_objs 
