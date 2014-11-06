##from pyNN.utility import get_script_args
#
##from pyNN.spiNNaker2_nest import *
##from pyNN.random import NumpyRNG, RandomDistribution
from pylab import *
#from NeuroTools.signals import *
from numpy import ones
#simulator_name = get_script_args(1)[0]  
#exec("from pyNN.%s import *" % simulator_name)

#FUNCION THAT CREATES A BANK OF GABOR FILTERS AT DIFFERENT SCALES AND ORIENTATIONS
#M AND N ESPECIFY THE NUMBER OF SCALES AND ORIENTATIONS. LONGE REPRESENTS THE SIZE OF THE FILTER: LONGE X LONGE)


def Gabor_creation(M,N,longe):
  #longe=5.0
  Ui=0.05
  Uh=0.4
  gab={}
  K=N
  W=Uh
  size1=floor(float(longe)/2.0)  # ADR fixed possible int-float conversion bug 17 June 2014
  size2=ceil(float(longe)/2.0-1) # ADR fixed possible int-float conversion bug 17 June 2014
  t=0;
  if M > 1:
     a=pow((Uh / Ui),(1.0/(float(M)-1))) # ADR fixed possible int-float conversion bug 17 June 2014
     # ADR optimised function by moving fixed computations outside the loops 22 July 2014
     sigu=((a-1)*Uh)/((a+1)*sqrt(2*log(2)))
     # ADR fixed 1-orientation (radially symmetric) bug (tan(pi/2) should be undefined) 21 July 2014
     este=sigu if K == 1 else tan(pi/(2*K))*(Uh-2*log(2)*((pow(sigu,2))/Uh))
     este2=pow((2*log(2)-(((pow((2*log(2)),2))*(pow(sigu,2)))/(pow(Uh,2)))),(-1.0/2.0))
     # ADR simplified calculation of sigv eliminating intermediate temp variable 21 July 2014
     sigv=sigu if K == 1 else tan(pi/(2*K))*sqrt((pow(Uh,2)-2*log(2)*pow(sigu,2))/(2*log(2)))
     sigmax=1.0/(2*pi*sigu)
     sigmay=1.0/(2*pi*sigv)
     for m in range(M):
        for n in range(N):
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
  else:
     # ADR fixed 1-scale case. Uses the maximum filter width as set by Ui (0.05): 9.048. Technically
     # the "normal" formula gives an "infinite" (undefined divide-by-zero) width for the y direction.
     # However, the limiting case for y width under any other choice of scale is 9.048 so it seems
     # sensible to use it. 22 July 2014
     sigu=Uh/sqrt(2*log(2))
     este=sigu if K == 1 else tan(pi/(2*K))*Ui
     este2=pow((2*log(2)- (((pow((2*log(2)),2))*(pow(sigu,2)))/(pow(Uh,2)))),(-1.0/2.0))
     sigv=sigu if K == 1 else tan(pi/(2*K))*Ui/sqrt(2*log(2))
     sigmax=1.0/(2*pi*sigu)
     sigmay=1.0/(2*pi*sigv)
     for n in range(N):
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
                 xb=x*cos(theta) + y*sin(theta)
                 yb=(-x)*sin(theta) + y*cos(theta)
                 phi1=(-1.0/2.0) * ((xb*xb)/(sigmax*sigmax) + (yb*yb)/(sigmay*sigmay))            
                 phi=(1.0/(2*pi*sigmax*sigmay))*((exp(phi1))*(exp(2j*pi*W*xb)))
	         row.append(phi)

             gab1.append(row)
         gab[t]=gab1
	 t=t+1
               
  return gab

def Gaussian_creation(M,N,longe):
  #longe=5.0
  Ui=0.05
  Uh=0.4
  gauss={}
  K=N
  W=Uh
  size1=floor(float(longe)/2.0)  # ADR fixed possible int-float conversion bug 17 June 2014
  size2=ceil(float(longe)/2.0-1) # ADR fixed possible int-float conversion bug 17 June 2014
  t=0;
  if M > 1: 
     a=pow((Uh / Ui),(1.0/(float(M)-1))) # ADR fixed possible int-float conversion bug 17 June 2014
     sigu=((a-1)*Uh)/((a+1)*sqrt(2*log(2)))
     sigv=sigu if K == 1 else tan(pi/(2*K))*sqrt((pow(Uh,2)-2*log(2)*pow(sigu,2))/(2*log(2)))
     sigmax=1.0/(2*pi*sigu)
     sigmay=1.0/(2*pi*sigv)
     for m in range(M):
        for n in range(N):
            theta=(n*pi)/N
            v=0
            w=0
	    gauss1=[]
            for x in range(-int(size1),int(size2)+1):   
                v=v+1
                w=0
	        row=[]
                for y in range(-int(size1),int(size2)+1):
                    w=w+1
                    xb=pow(a,(-m)) * (x*cos(theta) + y*sin(theta))
                    yb=pow(a,(-m)) * ((-x)*sin(theta) + y*cos(theta))
                    phi1=(-1.0/2.0) * ((xb*xb)/(sigmax*sigmax) + (yb*yb)/(sigmay*sigmay))            
                    phi=(1.0/(2*pi*sigmax*sigmay))*((exp(phi1)))
		    row.append(phi*pow(a,(-m)))

                gauss1.append(row)
            gauss[t]=gauss1
	    t=t+1
  else: 
     sigu=Uh/sqrt(2*log(2))
     sigv=sigu if K == 1 else tan(pi/(2*K))*Ui/sqrt(2*log(2))
     sigmax=1.0/(2*pi*sigu)
     sigmay=1.0/(2*pi*sigv)
     for n in range(N):
         theta=(n*pi)/N
         v=0
         w=0
	 gauss1=[]
         for x in range(-int(size1),int(size2)+1):   
             v=v+1
             w=0
	     row=[]
             for y in range(-int(size1),int(size2)+1):
                 w=w+1
                 xb=x*cos(theta) + y*sin(theta)
                 yb=(-x)*sin(theta) + y*cos(theta)
                 phi1=(-1.0/2.0) * ((xb*xb)/(sigmax*sigmax) + (yb*yb)/(sigmay*sigmay))            
                 phi=(1.0/(2*pi*sigmax*sigmay))*((exp(phi1)))
	         row.append(phi)

             gauss1.append(row)
         gauss[t]=gauss1
	 t=t+1
               
  return gauss


#ADR added tunable gabor and gaussian filters with user-settable gains and eccentricities. 18 June 2014

def Gabor_creation_tunable(M,N,longe,gain=0.4,eccentricity=1.0):
  #longe=5.0
  Ui=0.05
  Uh=gain
  gab={}
  K=N
  W=Uh
  size1=floor(float(longe)/2.0)
  size2=ceil(float(longe)/2.0-1)
  t=0;
  if M > 1:
     a=pow((Uh / Ui),(1.0/(float(M)-1)))
     sigu=((a-1)*Uh)/((a+1)*sqrt(2*log(2)))
     if sigu < Ui/sqrt(2*log(2)):
        raise OverflowError("Gain for Gabor filter %f too small" % sigu)
     este=sigu if K == 1 else tan(pi/(2*K))*(Uh-2*log(2)*((pow(sigu,2))/Uh))
     este2=pow((2*log(2)- (((pow((2*log(2)),2))*(pow(sigu,2)))/(pow(Uh,2)))),(-1.0/2.0))
     sigv=sigu if K == 1 else tan(pi/(2*K))*sqrt((pow(Uh,2)-2*log(2)*pow(sigu,2))/(2*log(2)))
     sigmax=1.0/(2*pi*sigu)
     sigmay=eccentricity/(2*pi*sigv)
     for m in range(M):
        for n in range(N):
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
  else:
     for n in range(N):
         sigu=Uh/sqrt(2*log(2))
	 este=sigu if K == 1 else tan(pi/(2*K))*Ui
	 este2=pow((2*log(2)-(((pow((2*log(2)),2))*(pow(sigu,2)))/(pow(Uh,2)))),(-1.0/2.0))
         sigv=sigu if K == 1 else tan(pi/(2*K))*Ui/sqrt(2*log(2))
         sigmax=1.0/(2*pi*sigu)
         sigmay=eccentricity/(2*pi*sigv)
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
                 xb=x*cos(theta) + y*sin(theta)
                 yb=(-x)*sin(theta) + y*cos(theta)
                 phi1=(-1.0/2.0) * ((xb*xb)/(sigmax*sigmax) + (yb*yb)/(sigmay*sigmay))            
                 phi=(1.0/(2*pi*sigmax*sigmay))*((exp(phi1))*(exp(2j*pi*W*xb)))
	         row.append(phi)

             gab1.append(row)
         gab[t]=gab1
	 t=t+1
               
  return gab

def Gaussian_creation_tunable(M,N,longe,gain=0.4,eccentricity=1.0):
  #longe=5.0
  Ui=0.05
  Uh=gain
  gauss={}
  K=N
  W=Uh
  size1=floor(float(longe)/2.0)
  size2=ceil(float(longe)/2.0-1)
  t=0;
  if M > 1: 
     a=pow((Uh / Ui),(1.0/(float(M)-1)))
     sigu=((a-1)*Uh)/((a+1)*sqrt(2*log(2)))
     if sigu < Ui/sqrt(2*log(2)):
        raise OverflowError("Gain for Gabor filter %f too small" % sigu)
     sigv = sigu if K == 1 else tan(pi/(2*K))*sqrt((pow(Uh,2)-2*log(2)*pow(sigu,2))/(2*log(2)))
     sigmax=1.0/(2*pi*sigu)
     sigmay=eccentricity/(2*pi*sigv)
     for m in range(M):
        for n in range(N):
            theta=(n*pi)/N
            v=0
            w=0
	    gauss1=[]
            for x in range(-int(size1),int(size2)+1):   
                v=v+1
                w=0
	        row=[]
                for y in range(-int(size1),int(size2)+1):
                    w=w+1
                    xb=pow(a,(-m)) * (x*cos(theta) + y*sin(theta))
                    yb=pow(a,(-m)) * ((-x)*sin(theta) + y*cos(theta))
                    phi1=(-1.0/2.0) * ((xb*xb)/(sigmax*sigmax) + (yb*yb)/(sigmay*sigmay))            
                    phi=(1.0/(2*pi*sigmax*sigmay))*((exp(phi1)))
		    row.append(phi*pow(a,(-m)))

                gauss1.append(row)
            gauss[t]=gauss1
	    t=t+1
  else: 
     sigu=Uh/sqrt(2*log(2))
     sigv=sigu if K == 1 else tan(pi/(2*K))*Ui/sqrt(2*log(2))
     sigmax=1.0/(2*pi*sigu)
     sigmay=eccentricity/(2*pi*sigv)
     for n in range(N):
         theta=(n*pi)/N
         v=0
         w=0
	 gauss1=[]
         for x in range(-int(size1),int(size2)+1):   
             v=v+1
             w=0
	     row=[]
             for y in range(-int(size1),int(size2)+1):
                 w=w+1
                 xb=x*cos(theta) + y*sin(theta)
                 yb=(-x)*sin(theta) + y*cos(theta)
                 phi1=(-1.0/2.0) * ((xb*xb)/(sigmax*sigmax) + (yb*yb)/(sigmay*sigmay))            
                 phi=(1.0/(2*pi*sigmax*sigmay))*((exp(phi1)))
	         row.append(phi)

             gauss1.append(row)
         gauss[t]=gauss1
	 t=t+1
               
  return gauss

def Filter2DConnector(size_in1,size_in2, size_out1,size_out2,weights, size_k1,size_k2,jump,delays, gain=1):

    #CREATES A SET OF CONNECTIONS BETWEEN INPUT AND OUTPUT NEURONS WITH A CERTAIN SET OF WEIGHTS. JUMP STABLISHES HOW MANY POSITIONS ARE DISCARDED AT EACH TIME
    from numpy import ones
    out = []
    # If passed a single weight value creates a matrix
    if type(weights) == int or type(weights)==float:          
        w = weights
        weights = []
        for i in range(size_k1):
            weights.append(ones(size_k2)*w*gain)

    i0=0
    j0=0
    iker=0
    jker=0
    out=[]
    for xout in range(size_out1):
       for yout in range(size_out2):
	    for i in range(i0,i0+size_k1):
               for j in range(j0,j0+size_k2):
	          out.append(((i, j),(xout,yout), weights[iker][jker]*gain, delays))  
	          jker=jker+1
	       jker=0
	       iker=iker+1
	    iker=0
	    jker=0
	    j0=j0+jump
       j0=0
       i0=i0+jump
    return out




#WE CONSIDER ONLY ABSOLUTE VALUES OF THE FILTER
#gabor=Gabor_creation(scales,orientations,sizeg1)
#gabor2=gabor
#for m in range(scales*orientations):
#	for n in range(sizeg1):
#		for l in range (sizeg1):
#			gabor2[m][n][l]=abs(gabor[m][n][l])



def GaborConnectorList(scales,orientations,sizeg1):
    gabor=Gabor_creation(scales,orientations,sizeg1)
    gabor2=gabor
    for m in range(scales*orientations):
        for n in range(int(sizeg1)):
            for l in range (int(sizeg1)):
                gabor2[m][n][l]=abs(gabor[m][n][l])
    return gabor2

def gaussianConnectorList(scales,orientations,sizeg1):
    gauss=Gaussian_creation(scales,orientations,sizeg1)
    gauss2=gauss
    for m in range(scales*orientations):
        for n in range(int(sizeg1)):
            for l in range (int(sizeg1)):
                gauss2[m][n][l]=abs(gauss[m][n][l])
    return gauss2

def MexicanHatConnectorList(scales,orientations,field_size,zeroRadius):
    gaussInner=Gaussian_creation(scales,orientations,field_size/zeroRadius)
    gaussOuter=Gaussian_creation(scales,orientations,field_size)
    MexHat=[gaussInner,gaussOuter]
    for r in MexHat:
        for m in range(scales*orientations):
            for n in range(int(field_size)):
                for l in range (int(field_size)):
                    r[m][n][l]=abs(r[m][n][l])
    return MexHat 

#ADR corresponding tuned connector lists for different types of filters. 18 June 2014

def TunedGaborConnectorList(scales,orientations,sizeg1,gain=0.4,eccentricity=1.0):
    gabor=Gabor_creation_tunable(scales,orientations,sizeg1,gain,eccentricity)
    gabor2=gabor
    for m in range(scales*orientations):
        for n in range(int(sizeg1)):
            for l in range (int(sizeg1)):
                gabor2[m][n][l]=abs(gabor[m][n][l])
    return gabor2

def TunedGaussianConnectorList(scales,orientations,sizeg1,gain=0.4,eccentricity=1.0):
    gauss=Gaussian_creation_tunable(scales,orientations,sizeg1,gain,eccentricity)
    gauss2=gauss
    for m in range(scales*orientations):
        for n in range(int(sizeg1)):
            for l in range (int(sizeg1)):
                gauss2[m][n][l]=abs(gauss[m][n][l])
    return gauss2

def TunedMexicanHatConnectorList(scales,orientations,field_size,zeroRadius,gain=0.4,eccentricity=1.0):
    gaussInner=Gaussian_creation_tunable(scales,orientations,field_size/zeroRadius,gain,eccentricity)
    gaussOuter=Gaussian_creation_tunable(scales,orientations,field_size,gain,eccentricity)
    MexHat=[gaussInner,gaussOuter]
    for r in MexHat:
        for m in range(scales*orientations):
            for n in range(int(field_size)):
                for l in range (int(field_size)):
                    r[m][n][l]=abs(r[m][n][l])
    return MexHat

def Filter1DConnector(size_in1,size_in2, size_out1,size_out2,weights, size_k1,size_k2,jump,delays, gain=1):
    mylist = Filter2DConnector_jose(size_in1,size_in2, size_out1,size_out2,weights, size_k1,size_k2,jump,delays, gain=1)
    out = []
    for i in mylist:
        #out.append(((i[0][0]*size_in1+i[0][1]*size_in2), (i[1][0]*size_out1+i[1][1]*size_out2)))
#        print i[0][0], i[0][1], "->", i[1][0], i[1][1]
#        print (i[0][0]*size_in1+i[0][1]), (i[1][0]*size_out1+i[1][1])
        #out.append(((i[0][0]*size_in1+i[0][1],), (i[1][0]*size_out1+i[1][1],), i[2], i[3]))
        out.append(([i[0][0]*size_in1+i[0][1]], [i[1][0]*size_out1+i[1][1]], i[2], i[3]))
        
    return out
    
def Filter2DConnector_jose(size_in1,size_in2, size_out1,size_out2, weights, size_k1,size_k2,jump,delays, gain=1):

    #CREATES A SET OF CONNECTIONS BETWEEN INPUT AND OUTPUT NEURONS WITH A CERTAIN SET OF WEIGHTS. JUMP STABLISHES HOW MANY POSITIONS ARE DISCARDED AT EACH TIME
    from numpy import ones
    out = []
    # If passed a single weight value creates a matrix
    if type(weights) == int or type(weights)==float:          
        w = weights
        weights = []
        for i in range(size_k1):
            weights.append(ones(size_k2)*w)

    in_size = size_in1*size_in2
    i0=-size_k1/2
    j0=-size_k2/2
    iker=0
    jker=0
    out=[]
    k=0
    # ADR fixed incrementing for multiple scales: a non-integer subsample needs to check,
    # each increment, whether adding the jump field also increments by one more because the
    # accumulation of successive jumps has yielded a value greater than half a pixel. 
    jumpi=(int(0.5+(ii+1)*jump)-int(0.5+ii*jump) for ii in range(size_out1)) 
    for xout in range(size_out1):
        jumpj=(int(0.5+(jj+1)*jump)-int(0.5+jj*jump) for jj in range(size_out2))
        for yout in range(size_out2):
            for i in range(i0,i0+size_k1):
                   for j in range(j0,j0+size_k2):
                       # ADR fixed indexing 17 June 2014 - row-column iteration means yout and j should be
                       # incremented by their corresponding *row* lengths (size_out1, size_in1) not their 
                       # *column* lengths. Would not be noticed in a square connection matrix.
                       # ADR fixed index bounds 23 June 2014 - only adds an element if the index is in the
                       # input field: needed because filter tiles need to overlap the edges in order to avoid
                       # edge effects.
                       #pre_idx = i + (j*size_in1)
                       if i >= 0 and i < size_in1 and j >= 0 and j < size_in2:
                          out.append((i + (j*size_in1), xout + yout*size_out1, weights[iker][jker]*gain, delays))  # working 16
                       jker=jker+1
                   jker=0
                   iker=iker+1
            k=k+1
            iker=0
            jker=0
            j0=j0+next(jumpj)
        j0=-size_k2/2
        i0=i0+next(jumpi)
    return out

###############################################################################


#print Filter2DConnector_jose(5, 5, 2, 2,1, 3,3,jump=2,delays=1, gain=1)

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


#PARAMETERS GABOR
#scales=2
#orientations=6
#sizeg1=5.0

#size_k1 = 5
#size_k2 = 5  
#jump = 1
#delays = 1.0

#input_size = 16         # Size of each population
#output_size = 10

#            
#gabor_filters = GaborConnectorList(2,6,5.0)
#f = gabor_filters[0]

def overSamplerConnector2D(size_in, size_out, weights, delays):
    """
    This function builds the inverse of a subSamplerConnector: an overSampler which 
    maps from a smaller population onto a larger population of neurons
    Returns a list that can then be used with the FromList Connector
    The output is a connectivity matrix which will oversample the input population
    
    size_in = size of the input population (2D = size_in x size_in)    
    size_out = size of the sampled population
    weights = averaging weight value (each connection will have this value) must be float
    delays = averaging delay value (each connection will have this value)
    """
    import math
    out = []
    step = size_out/size_in
    for i in range(size_in):
         for j in range(size_in):
            out = out + [(i*size_in + j, (i*step+i_out)*size_out + (j*step+j_out), weights, delays) for i_out in range(step) for j_out in range(step)] # Python really is magic                    
    return out

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
            out.append((i*size_in + j, i_out*size_out + j_out, weights, delays)) # Python is magic                    
    return out

def translate_2D_to_1D(x, y, row_size):
    return(x + y*row_size)
    
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

    
    
    
