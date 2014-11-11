"""
Topographic activity graphic module for SpiNNaker spiking output
Alexander Rast
9 June 2014

This module creates plots displaying spikes in a topographic arrangement, so
that the location of the plotted spike corresponds to its actual location in
a presumed topographically-mapped network layer. Mapped_boxplot uses a box to
represent a spike. Boxes nest in time, so that the biggest, outermost box at a
given plot location is the earliest and the smallest, innermost the latest. A
leaky integrator cycles the colour from red to white to indicate level of
activity

--------------------------------------------------------------------------------

Modified 19 July 2014 ADR. Added arrow plot for visualisation of intermediate
layers. The vector fields of arrows represent orientations by direction and 
colour of arrow, the colours cycling in a priority scheme: red, green, blue,
yellow, magenta, cyan, orange etc. Each topographic location maps order of 
spikes in a square grid, the earliest spike occurring in the top left, the 
latest in the bottom right, and successive spikes moving row-wise down the y-axis
first, then column-wise shifting right along the x axis next. 

Added auto-scaling for monitor size and resolution, and options to set plot
size according to maximum amount of screen filled. 

--------------------------------------------------------------------------------

"""

import numpy
import math
import matplotlib.pyplot as plt
import matplotlib.colors as colours
import copy

# colour maps for use in displaying plots. Many could be defined here.
activity_colours = ['#800000','#FF0000','#FF8000','#FFC000','#FFE000','#FFFF00','#FFFF80','#FFFFC0','#FFFFE0','#FFFFF0','#FFFFF8','#FFFFFC','#FFFFFE','#FFFFFF']
direction_colours = ['#400000', '#800000', '#C00000', '#FF0000','#004000', '#008000', '#00C000', '#00FF00', '#000040', '#000080', '#0000C0', '#0000FF', '#404000', '#808000', '#C0C000', '#FFFF00', '#400040', '#800080', '#C000C0', '#FF00FF', '#004040', '#008080', '#00C0C0', '#00FFFF', '#402000', '#804000', '#C06000', '#FF8000', '#400020', '#800040', '#C00060', '#FF0080']
colour_map_activity = colours.ListedColormap(colors=activity_colours, name='activity_intensity')
colour_map_direction = colours.ListedColormap(colors=direction_colours, name='direction_strength')

def mapped_boxplot(data, x_dim, y_dim, t_max, tau=1, linewidth=1, screen_size=24, screen_aspect=(16,10), screen_v_resolution=1200, max_v_screen_occupancy=0.8):
    """ 
    mapped_boxplot draws the box plots described above. It expects at least a data source, the specified x and y
    dimensions of the topographic field, and the end time. Tau sets the time constant for the activity leaky
    integrator, linewidth the thickness of the box lines (thin lines can look spidery with sparse data, but thick
    lines will blend together with dense data). The other parameters set the plot scaling.
    """ 
    dpi = int(float(screen_v_resolution)/(math.sqrt(float(screen_size**2)/float(screen_aspect[0]**2+screen_aspect[1]**2))*screen_aspect[1])) # compute how many effective dots per inch the screen in use has. Needed for matplotlib scaling

    # first part: massage the data into a convenient sorted form
    sort_ids = numpy.lexsort((data[:,0], data[:,1]))  # sort the data by neuron first, then by time of spike.
    map_data = numpy.array([[int(data[row, 1])/y_dim, int(data[row, 1])%y_dim, data[row, 0]] for row in sort_ids])

    # second part: manually set the plot scalings. matplotlib expects to scale plots according
    # to dots per inch and inches per object. Here we want to scale the plot so that the boxes
    # exactly tile the plot area and neatly nest inside each other for the time resolution. 
    # Transform this into a size/colour representation
    if (2*linewidth*t_max*y_dim) > screen_v_resolution*max_v_screen_occupancy: 
       # adjust for thick linewidths that would occupy more than the entire screen when combined
       linewidth = math.floor(screen_v_resolution*max_v_screen_occupancy)/float(2*t_max*y_dim)
       print "Warning: requested linewidth wider than maximum allowable."
       print "Setting linewidth to maximum possible: %f" % linewidth
    plot_size = [2*linewidth*t_max*x_dim, 2*linewidth*t_max*y_dim]  # total size of the topographic plot
    sizes = [(2*linewidth*(t_max-row[2]+1))**2 for row in map_data] # sizes of the possible boxes
    colour_range=colours.Normalize(vmin=0.0, vmax=14.0, clip=True)  # map the activity range to the possible colours
    integr_idx = 0.0
    t_prev = map_data[0,2]
    neuron = map_data[0,:2]
    attn_colours = []

    # third part: determine the colour of each box. This is done via a leaky integrator to make
    # successively more active neurons successively whiter boxes.
    for row in map_data: # now go through each neuron in the data. row will be an array of times.
        same_neuron = (row[:2] == neuron) # VERY tricky: an array comparison actually returns an array
        if all(same_neuron): # this means the neuron indices matched
           integr_idx = integr_idx-((row[2]-t_prev)/tau) # update the leaky integrator to the current time
           attn_colours.append(integr_idx)               # decide what activity colour it should be
           integr_idx += 1.0                             # each spike raises the activity by 1
           t_prev = row[2]                               # store the spike time 
        else:                # new neuron
           attn_colours.append(0.0) # first colour must be the lowest                     
           integr_idx = 1.0         # and there's only one spike so far in the integrator
           t_prev = row[2]          # store the spike time
           neuron = row[:2]         # use this neuron as the reference to compare when checking for a new neuron

    # fourth part: output the data in text and plot format
    data_out = open("boxplt_dat.txt", "w")
    data_out.write("sorted spikes: %s" % map_data) # output the spikes to a file for any desired off-line analysis
    data_out.close()
    # the line below actually creates the scatter plot   
    box_plot=plt.scatter(x=map_data[:,0], y=map_data[:,1],s=sizes,c=attn_colours,marker='s',cmap=colour_map_activity,norm=colour_range,vmin=0,vmax=14,linewidths=(linewidth,),facecolors='none')

    # fifth part: set all the remaining scalings and plot options manually. matplotlib
    # requires you to acquire a handle to the plot in order to do this, then you can
    # use the various setup options. A similar situation applies to the axes (perhaps 
    # something of a misnomer) which actually describe the active region of the plot and
    # include all the plot contents as well as the actual axes.
    focus_plot = plt.gcf()                        # get a handle to the current plot object
    focus_plot.set_dpi(dpi)                       # adjust the plot resolution
    focus_plot.set_size_inches(plot_size[0]/dpi, plot_size[1]/dpi, forward=True) # and plot size
    focus_plot.set_frameon(False)                 # no need for a background; keep it black
    focus_plot_axes = focus_plot.gca()            # get the plot object's axes instance
    focus_plot_axes.set_axis_off()                # don't display the axis
    focus_plot_axes.set_autoscale_on(False)       # we have manually scaled so don't autoscale 
    focus_plot_axes.set_frame_on(False)           # no inner background either
    focus_plot_axes.set_xlim(left=0, right=x_dim) # set plot limits to topographic area
    focus_plot_axes.set_ylim(bottom=0, top=y_dim) 
    return box_plot

def mapped_arrowplot(data, x_dim, y_dim, t_max, tau=1, arrowscale=1.0, linewidth=1, screen_size=24, screen_aspect=(16,10), screen_v_resolution=1200, max_v_screen_occupancy=1.0):
    """ 
    mapped_arrowplot draws the vector activity plots described under the first modification. It expects the same
    required arguments as mapped_blox plot. arrowscale sets how many units in the data correspond to how many
    normalised units of arrow length. "units in the data" means each increment of 1.0 in whatever data source
    you are using. So if data is time in ms, then 1 ms would be the unit in the data. Tau sets the time constant
    for the activity leaky integrator, linewidth sets the thickness of arrows in pixels. The other parameters set
    the plot scaling.
    """ 
    dpi = int(float(screen_v_resolution)/(math.sqrt(float(screen_size**2)/float(screen_aspect[0]**2+screen_aspect[1]**2))*screen_aspect[1])) # same dpi computation as for mapped_boxplot

    # first part: massage the data. For the arrow plot it is necessary to determine
    # the number of directions before sorting as before.
    num_dirs = len(data)
    dir_idxs = range(num_dirs) 
    sort_ids = [numpy.lexsort((data[dir_idx][:,0], data[dir_idx][:,1])) if len(data[dir_idx]) > 0 else numpy.array([]) for dir_idx in dir_idxs] 
    map_data = [numpy.array([[int(data[dir_idx][row, 1])/y_dim, int(data[dir_idx][row, 1])%y_dim, data[dir_idx][row, 0]] for row in sort_ids[dir_idx][:]]) for dir_idx in dir_idxs]

    #cell_dim = t_max/arrowscale

    # second part: set up the input arrays for a quiver plot. First, calculate the scales
    t_dim = int(math.ceil(math.sqrt(t_max)))     # arrows per box-width
    cell_dim = float(t_dim)/arrowscale           # units per box-width
    plot_size = [cell_dim*x_dim, cell_dim*y_dim] # total units per plot
    plot_prescale = screen_v_resolution*max_v_screen_occupancy/plot_size[1] # scaling factor for the plot
    plot_prescale = math.floor(plot_prescale) if plot_prescale > 1.0 else plot_prescale
    # Next, compute the positions and angles of the arrows. The reduction flattens a
    # num_dirs-orientation to a one-dimesional vector. Angles come from the direction
    # positions are computed from the topographic position.
    angles_u = reduce(lambda x, y: x+y, [[math.cos((math.pi/num_dirs)*dir_idx)]*len(map_data[dir_idx]) for dir_idx in dir_idxs if len(map_data[dir_idx]) > 0], [])
    angles_v = reduce(lambda x, y: x+y, [[math.sin((math.pi/num_dirs)*dir_idx)]*len(map_data[dir_idx]) for dir_idx in dir_idxs if len(map_data[dir_idx]) > 0], [])
    #positions_x = reduce(lambda x, y: x+y, [[(1-math.cos((math.pi/num_dirs)*dir_idx))*(cell_dim+0.5+col[2])+(col[0]*cell_dim) for col in map_data[dir_idx]] for dir_idx in dir_idxs if len(map_data[dir_idx]) > 0], [])
    #positions_y = reduce(lambda x, y: x+y, [[(1-math.sin((math.pi/num_dirs)*dir_idx))*(cell_dim+0.5+col[2])+(col[1]*cell_dim) for col in map_data[dir_idx]] for dir_idx in dir_idxs if len(map_data[dir_idx]) > 0], [])
    # in the position computation, we are going to locate the arrows relative to their
    # midpoint. As a result, each position should be shifted by half a normalised arrow length;
    # this is the reason for the appearance of the 0.5 in the position computation. col[d]*cell_dim
    # is the global topographic position. int(col[2]){/|%}t_dim compute the x and y offsets within
    # the topographic square allocated for a particular position, for the spike at a particular time.
    # notice how the reduce is simply collecting arrays; x+y is a list-concatenation operator in this
    # context.
    positions_x = reduce(lambda x, y: x+y, [[(0.5+(int(col[2])/t_dim))+(col[0]*cell_dim) for col in map_data[dir_idx]] for dir_idx in dir_idxs if len(map_data[dir_idx]) > 0], [])
    positions_y = reduce(lambda x, y: x+y, [[(0.5+(int(col[2])%t_dim))+(col[1]*cell_dim) for col in map_data[dir_idx]] for dir_idx in dir_idxs if len(map_data[dir_idx]) > 0], [])

    # third part: determine the colours for each arrow
    # BoundaryNorm the colour range, i.e. map colours to quantised values of activity.
    colour_range = colours.BoundaryNorm(boundaries=range(len(direction_colours)), ncolors=len(direction_colours), clip=True)
    integr_idx = numpy.zeros((num_dirs,), float)
    t_prev = [numpy.array(map_data_vals[0,2] if len(map_data_vals) > 0 else []) for map_data_vals in map_data]
    neuron = [numpy.array(map_data_vals[0,:2] if len(map_data_vals) > 0 else []) for map_data_vals in map_data]
    dir_colours = [[] for i in dir_idxs] # set up a colour array for each orientation
    for dir_idx in [idx for idx in dir_idxs if len(map_data[idx]) > 0]:
        for row in map_data[dir_idx]: # map the activity arrays, following the leaky integrator, for a given orientation
            if all((row[:2] == neuron[dir_idx])): # VERY tricky: an array comparison actually returns an array
               integr_idx[dir_idx] = max(integr_idx[dir_idx]-((row[2]-t_prev[dir_idx])/tau), 3)
               dir_colours[dir_idx].append((4*dir_idx)+integr_idx[dir_idx])
               integr_idx[dir_idx] += 1.0
               t_prev[dir_idx] = row[2]
            else:
               dir_colours[dir_idx].append(4*dir_idx)
               integr_idx[dir_idx] = 1.0
               t_prev[dir_idx] = row[2]
               neuron[dir_idx] = row[:2]
    # merge the orientations into a flat vector
    dir_colours = reduce(lambda x, y: x+y, [dir_cmap for dir_cmap in dir_colours if len(dir_cmap) > 0], [])

    #arrow_plot=plt.quiver(positions_x, positions_y, angles_u, angles_v, dir_colours, units='xy', scale=arrowscale, scale_units='xy', width=linewidth*arrowscale/(int(screen_v_resolution*max_v_screen_occupancy)/int(plot_size[1])), pivot='middle', cmap=colour_map_direction, norm=colour_range)

    # fourth part: output the data
    data_out = open("arrowplt_dat.txt", "w")
    data_out.write("sorted spikes: %s" % map_data) # output the spikes to a file for any desired off-line analysis
    data_out.close()
    arrow_plot=plt.quiver(positions_x, positions_y, angles_u, angles_v, dir_colours, units='xy', scale=arrowscale, scale_units='xy', width=linewidth*arrowscale/plot_prescale, pivot='middle', cmap=colour_map_direction, norm=colour_range)

    # fifth part: configure other plot options. A similar process to mapped_boxplot
    dir_plot = plt.gcf()
    dir_plot.set_dpi(dpi)
    #dir_plot.set_size_inches(plot_size[0]*(int(screen_v_resolution*max_v_screen_occupancy)/int(plot_size[0]))/dpi, plot_size[1]*(int(screen_v_resolution*max_v_screen_occupancy)/int(plot_size[1]))/dpi, forward=True)
    # units_per_dim*inches_per_unit*num_multiples_per_screen
    dir_plot.set_size_inches(plot_size[0]*plot_prescale/dpi, plot_size[1]*plot_prescale/dpi, forward=True)
    dir_plot.set_frameon(True)        # Background on: black tends to hide arrows
    dir_plot.set_facecolor('#808080') # for the arrow plot a grey background is easiest to see
    dir_plot_axes = dir_plot.gca()       # similar scaling of axes as mapped_boxplot.
    dir_plot_axes.set_axis_off()
    dir_plot_axes.set_autoscale_on(False)
    dir_plot_axes.set_frame_on(False)
    dir_plot_axes.set_xlim(left=0, right=plot_size[0])
    dir_plot_axes.set_ylim(bottom=0, top=plot_size[1]) 
    return arrow_plot  
