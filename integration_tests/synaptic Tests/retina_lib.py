import numpy
numpy.set_printoptions(precision=4, suppress=True)

import math
import pylab
from scipy import ndimage

#FUNCION THAT CREATES A BANK OF GABOR FILTERS AT DIFFERENT SCALES AND ORIENTATIONS
#M AND N ESPECIFY THE NUMBER OF SCALES AND ORIENTATIONS. LONGE REPRESENTS THE SIZE OF THE FILTER: LONGE X LONGE)

H = 0
DEG45 = 1 
V = 2
DEG135 = 3



def Gabor_creation(M,N,longe):
    longe=float(longe)
    #longe=5.0
    Ui=0.05
    Uh=0.4
    a=pow((Uh / Ui),(1/(M-1)))
    gab={}
    K=N
    W=Uh
    size1=floor(longe/2)
    size2=ceil(longe/2-1)
    t=0;
    for m in range(M):
        for n in range(N):
            sigu=((a-1)*Uh)/((a+1)*sqrt(2*log(2)))
            este=tan(pi/(2*K))*(Uh-2*log(2)*((pow(sigu,2))/Uh))
            este2=pow((2*log(2)- (((pow((2*log(2)),2))*(pow(sigu,2)))/(pow(Uh,2)))),(-1.0/2.0))
            temp=(2*log(2)- (((pow((2*log(2)),2))*(pow(sigu,2)))/(pow(Uh,2))))
            sigv=tan(pi/(2*K))*(Uh-2*log(2)*((pow(sigu,2))/Uh))*pow(temp,(-1.0/2.0))
            sigmax=1.0/(2*pi*sigu)
            sigmay=1.0/(2*pi*sigv)
            theta=(n*pi)/N
            v=0
            w=0
            gab1=[]
            for x in range(-int(size1),int(size2)+1):   
                v=v+1
                w=0
                row=[]
                for y in range(-int(size1),int(size2)+1):
                    w=w+1
                    xb=pow(a,(-m)) * (x*cos(theta) + y*sin(theta))
                    yb=pow(a,(-m)) * ((-x)*sin(theta) + y*cos(theta))
                    phi1=(-1.0/2.0) * ((xb*xb)/(sigmax*sigmax) + (yb*yb)/(sigmay*sigmay))            
                    phi=(1.0/(2*pi*sigmax*sigmay))*((exp(phi1))*(exp(2j*pi*W*xb)))
                    row.append(phi*pow(a,(-m)))
                    
                gab1.append(row)
            gab[t]=gab1            
            t=t+1
               
    return gab



#WE CONSIDER ONLY ABSOLUTE VALUES OF THE FILTER
def GaborConnectorList(scales,orientations,sizeg1):
    gabor=Gabor_creation(scales,orientations,sizeg1)
    gabor2=gabor

    for m in range(scales*orientations):
        for n in range(int(sizeg1)):
            for l in range (int(sizeg1)):
#                print m, n, l
                gabor2[m][n][l]=abs(gabor[m][n][l])
    return gabor2





def Filter1DConnector(size_in1,size_in2, size_out1,size_out2,weights, size_k1,size_k2,jump,delays, gain=1):
    mylist = Filter2DConnector_jose(size_in1,size_in2, size_out1,size_out2,weights, size_k1,size_k2,jump,delays, gain=1)
    out = []
    for i in mylist:
        out.append(([i[0][0]*size_in1+i[0][1]], [i[1][0]*size_out1+i[1][1]], i[2], i[3]))
        
    return out
    
#def Filter2DConnector(size_in1,size_in2, size_out1,size_out2, weights, size_k1,size_k2,jump,delays, gain=1):

#    #CREATES A SET OF CONNECTIONS BETWEEN INPUT AND OUTPUT NEURONS WITH A CERTAIN SET OF WEIGHTS. JUMP STABLISHES HOW MANY POSITIONS ARE DISCARDED AT EACH TIME
#    from numpy import ones
#    out = []
#    # If passed a single weight value creates a matrix
#    if type(weights) == int or type(weights)==float:          
#        w = weights
#        weights = []
#        for i in range(size_k1):
#            weights.append(ones(size_k2)*w)

#    i0=0
#    j0=0
#    iker=0
#    jker=0
#    out=[]
#    k=0
#    for xout in range(size_out1):
#        for yout in range(size_out2):
#            for i in range(i0,i0+size_k1):
#                   for j in range(j0,j0+size_k2):
#                       out.append((i + (j*size_in2), xout + yout*size_out2, weights[iker][jker]*gain, delays))  # working 16
#                       jker=jker+1
#                   jker=0
#                   iker=iker+1
#            k=k+1
#            iker=0
#            jker=0
#            j0=j0+jump
#        j0=0
#        i0=i0+jump
#    return out

###############################################################################


def Filter2DConnector(size_in, size_out, size_gabor, jump, weights, delays, gain=1, precision=0):
    """
    Creates a connection list of tuples (pre, post, weight, delay) convolving the weights kernel on the original map
    """
    
#    numpy.set_printoptions(threshold=nan)

    pre_matrix = numpy.arange(size_in*size_in).reshape(size_in,size_in)
    post_matrix = numpy.arange(size_out*size_out).reshape(size_out,size_out)
    
    print weights, size_gabor
    kernel_matrix = numpy.asarray(weights).reshape(size_gabor*size_gabor)        
    
    
    
    # these pivots represent the center of the receptive field (pre) of the post neuron
    pre_x = 0 
    pre_y = 0
    post_x = 0 
    post_y = 0    
    
    conn_list = list()
    
    while (post_x < size_out):
        post_y = 0
        pre_y = 0
        while (post_y < size_out):
#            print "Evaluating post neuron (%d,%d), receives connections from" % (post_x, post_y)  
            x = 0
            y = 0
            
            for x in range(-size_gabor/2+1, size_gabor/2+1):
                for y in range(-size_gabor/2+1, size_gabor/2+1):
                    if  (pre_x+x >= 0) \
                        and (pre_y+y >= 0) \
                        and (pre_x+x < size_in) \
                        and (pre_y+y < size_in):
#                            print "connection from", pre_x+x, pre_y+y, "(%d)"% translate_2D_to_1D(pre_x+x, pre_y+y, size_in) ,"exist and it's weight", kernel_matrix[(x+size_gabor/2)*size_gabor+(y+size_gabor/2)]                            
                            weight = kernel_matrix[(x+size_gabor/2)*size_gabor+(y+size_gabor/2)]*gain
                            if (precision > 0 and abs(weight)>1/2.0**precision) or precision==0:                            
                                conn_list.append((translate_2D_to_1D(pre_x+x, pre_y+y, size_in),
                                                 translate_2D_to_1D(post_x, post_y, size_out),
                                                 weight,
                                                 delays))
                    
                    y += 1
                x += 1
                                                            
                        
            pre_y += jump            
            post_y += 1
            
        pre_x += jump
        post_x += 1        
    
    return conn_list
    
            
    

def normalizeFilter(f):
    absmax = max(max(f))
    out = []
    for i in (f):
        out_x = []
        for j in i:
            out_x.append(int(floor(j*255/absmax)))
        out.append(out_x)
    return out

def getImageFromFilter(f):
    f = normalizeFilter(f)
    from PIL import Image
    img = Image.new('L',(size(f[0]),size(f[0])), 0)
    for i in range(size(f[0])):
        for j in range(size(f[0])):
            img.putpixel((j,i), f[i][j])
    return img


def subSamplerConnector2D(size_in, size_out, weights, delays):
    """
    This function is called later on to build the subsampler connections. Read this when is called, now jump to the start of the simulation
    Returns a list that can then be used with the FromList Connector
    The output is a connectivity matrix which will subsample the input population
    
    size_in = size of the input population (2D = size_in x size_in)    
    size_out = size of the sampled population
    weights = averaging weight value (each connection will have this value) must be float
    delays = averaging delay value (each connection will have this value)
    """
    import math
    out = []
    step = size_in/size_out
    for i in range(size_in):
         for j in range(size_in):
            i_out = i/step
            j_out = j/step
            out.append((i*size_in + j, i_out*size_out + j_out, weights, delays))
    return out

def translate_2D_to_1D(x, y, row_size):
    return(x*row_size + y)
    
def translate_1D_to_2D(neuron_id, row_size, col_size):
    x = neuron_id % row_size
    y = neuron_id / col_size
    return((x,y))


def ProximityConnector(row_size, col_size, receptive_field, weights, delays, allow_self_connections=True):
    out = []
    for r in range(0, row_size, receptive_field):
        for c in range(0, col_size, receptive_field):
#            print r,c,translate_2D_to_1D(r, c, row_size), "->", get_neighbour_ids(translate_2D_to_1D(r, c, row_size), row_size, col_size, receptive_field)
            connector_list = get_neighbour_ids(translate_2D_to_1D(r, c, row_size), row_size, col_size, receptive_field)
            out_temp = []
            out_temp = [ (i,j,weights,delays) for i in connector_list for j in connector_list ]  # create all possible connections
            
            if allow_self_connections==False:
                out_temp = [ o for o in out_temp if o[0]!=o[1] ]  # will eliminate self connections
            for o in out_temp:
                out.append(o)                            
    return(out)



def get_neighbour_ids(neuron_id, row_size, col_size, receptive_field, allow_self_connections=True):
    """
    this function returns the +receptive fields ids (rows and columns) of neuron id
    """
    out = []
    x_coord, y_coord = translate_1D_to_2D(neuron_id, row_size, col_size)
        
    for r in range(receptive_field):
        for c in range(receptive_field):
            x = x_coord + c
            y = y_coord + r
            if (x < col_size) and (y < row_size):
                dest_id = translate_2D_to_1D(x, y, row_size)
                if not (dest_id == neuron_id and allow_self_connections==False):
                    out.append(dest_id)            
    return out

#print ProximityConnector(10, 10, 2, 1, 1, allow_self_connections=False)

    
    


def subSamplerConnector2D(size_in, size_out, weights, delays):
    """
    size_in = size of the input population (2D = size_in x size_in)    
    size_out = size of the sampled population
    weights = averaging weight value (each connection will have this value) must be float
    delays = averaging delay value (each connection will have this value)
    """
    out = []
    step = size_in/size_out
    for i in range(size_in):
         for j in range(size_in):
            i_out = i/step
            j_out = j/step
            out.append((i*size_in + j, i_out*size_out + j_out, weights, delays))
    return out

#size_gabor = 5
#size_in = 32
#size_out = 32

#weights = numpy.arange(size_gabor*size_gabor).reshape(size_gabor,size_gabor)

#gabors = GaborConnectorList(2, 4, size_gabor)


from math import pi, sqrt, exp

def gauss(n=11,sigma=1):
    """
    from http://stackoverflow.com/questions/11209115/creating-gaussian-filter-of-required-length-in-python
    """
    r = range(-int(n/2),int(n/2)+1)
    return [1 / (sigma * sqrt(2*pi)) * exp(-float(x)**2/(2*sigma**2)) for x in r]

def show_kernel(kernel, blocking=True):
    pylab.imshow(numpy.transpose(kernel), cmap = pylab.cm.Greys_r, interpolation='nearest', origin='upper')
    pylab.show(block=blocking)

out=[]
sigma=.75
l = 7


def AllToOne(size_in, id_out, weight, delay):
    """
    Function used to connect all the cells of the pre population to just 1 cell
    in the post populations
    """
    out = []
    for i in range(size_in):
        out.append((i, id_out, weight, delay))
    return out

def gaussians(size, orientations, sigma=1):
    kernel = []
    # creates gaussian kernel
    for i in range(size):
        kernel.append(gauss(size,sigma))

    kernel=numpy.asarray(kernel)
    angles = range(0,180,180/orientations)
    print angles
    out = []    
    for angle in angles:
        out.append(ndimage.rotate(kernel, angle, reshape=False, mode='nearest'))
        
    return out

    

#c = gaussians(orientations=4,size=5, sigma=.75)

#for cc in c:
#    print cc
#    show_kernel(cc)



#for c in Filter2DConnector(size_in, size_out, size_gabor, 1, numpy.arange(size_gabor*size_gabor).reshape(size_gabor, size_gabor), 1, gain=1):
#for c in Filter2DConnector(size_in, size_out, size_gabor, 1, gabors[0], 1, gain=1):
#    print c



#gaussians = gaussians(orientations=4,size=33, sigma=1)

#show_kernel(numpy.ones((33,33)))

#for g in gaussians:    
#    print g
#    show_kernel(g)


