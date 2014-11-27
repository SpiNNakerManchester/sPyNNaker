import math
import itertools

class scale_factor(object):

      def __init__(self, dimensions=0, dim_sizes=None, base_dim_size=16, subsample_factor_i_1=1.6, subsample_factor_1_2=1.0, subsample_factor_2_4=2.0, subsample_factor_4_L=1.0, subsample_factor_4_P=1.0, base_filter_size=5.0, sweep_filter=False, filter_scale=(1,1,1), xy_kernel_quant_cutoff=(0,0), base_v2_subfield_size=2, sweep_subfield=False, subfield_scale=(1,1,1), active_P=False):

          self.base_filter_size = base_filter_size
          self.subsample_factor = (subsample_factor_i_1, subsample_factor_1_2, subsample_factor_2_4, subsample_factor_4_L, subsample_factor_4_P)
          if dim_sizes == None:
             dim_sizes = [base_dim_size]*dimensions
          if sweep_filter:
             if type(filter_scale) == int:
                self.filter_scale_factors = range(filter_scale)
             else: 
                self.filter_scale_factors = range(*filter_scale)
          else:
             self.filter_scale_factors = [1]
          if sweep_subfield:
             if type(subfield_scale) == int:
                self.subfield_scale_factors = range(subfield_scale)
             else:
                self.subfield_scale_factors = range(*subfield_scale)
          else:
             self.subfield_scale_factors = [1]
          self.input_size = []
          self.v1_pop_size = []
          self.v2_pop_size = []
          self.v4_pop_size = []
          self.lip_pop_size = []
          self.pfc_pop_size = []
          for dimension in range(dimensions):
              self.input_size.append(dim_sizes[dimension]) # compute the size of the input population
              self.v1_pop_size.append(int(math.ceil(float(self.input_size[dimension])/float(self.subsample_factor[0]))))  # compute the population size for v1
              self.v2_pop_size.append(int(math.ceil(float(self.v1_pop_size[dimension])/float(self.subsample_factor[1]))))  # compute the population size for v2
              self.v4_pop_size.append(int(math.ceil(float(self.v2_pop_size[dimension])/float(self.subsample_factor[2])))) # compute the population sizes for v4
              self.lip_pop_size.append(int(math.ceil(float(self.v4_pop_size[dimension])/float(self.subsample_factor[3])))) # compute the population size for LIP
              self.pfc_pop_size.append(int(math.ceil(float(self.v4_pop_size[dimension])/float(self.subsample_factor[4]))))

          # scale filter sizes by matching against subsample reduction: more aggressively 
          # reduced subsamples need a correspondingly wider filter
          # filter_scale_size = {reference_filter_size/relative_resolution_scale} * {downscale_factor} * {reference_filter_size} / {standard_downscale_factor*standard_filter_size}
          self.filter_size_scales = [(self.base_filter_size**2/size_scale)*self.subsample_factor[0]/(1.6*5.0) for size_scale in self.filter_scale_factors]
          self.x_k_scales = [max(xy_kernel_quant_cutoff[0], int(math.floor(scale))) for scale in self.filter_size_scales]
          self.y_k_scales = [max(xy_kernel_quant_cutoff[1], int(math.floor(scale))) for scale in self.filter_size_scales]
          self.v2_sub_scales = [int(math.ceil(self.subsample_factor[2]))*subscale*base_v2_subfield_size/2 for subscale in self.subfield_scale_factors]
          # ADR modified 23 June 2014 now returns floats for modified Filter2DConnector.
          self.jumps = [[filter_size-((self.v1_pop_size[dimension]*filter_size-self.input_size[dimension]-filter_size)/(self.v1_pop_size[dimension]-1)) for dimension in range(dimensions)] for filter_size in self.filter_size_scales]
          if active_P:
             self.pfc_filter_scale = [math.ceil(float(self.v2_pop_size[dimension])/float(self.pfc_pop_size[dimension])) for dimension in range(dimensions)]
             self.pfc_filter_gain = 1/(2*math.pi*self.pfc_filter_scale[0])
             self.pfc_eccentricities = [p_scale/self.pfc_filter_scale[0] for p_scale in self.pfc_filter_scale[1:]]
             self.pfc_jumps = [self.pfc_filter_scale[dimension]-((self.pfc_pop_size[dimension]*self.pfc_filter_scale[dimension]-self.v1_pop_size[dimension]-self.pfc_filter_scale[dimension])/(self.pfc_pop_size[dimension]-1)) for dimension in range(dimensions)] 
        

      def __iter__(self):

          return scaling_instance(init_obj=self)

      def __getitem__(self, key):
          
          if type(key) == int:
             if key > 0:
                return ((self.filter_size_scales[key], self.x_k_scales[key], self.y_k_scales[key], self.jumps[key]), self.v2_sub_scales[0])  
             elif key < 0: 
                return ((self.filter_size_scales[0], self.x_k_scales[0], self.y_k_scales[0], self.jumps[0]), self.v2_sub_scales[-key])  
             else: 
                return ((self.filter_size_scales[0], self.x_k_scales[0], self.y_k_scales[0], self.jumps[0]), self.v2_sub_scales[0])
          elif type(key) == slice:
             if key.stop > 0:
                return [((self.filter_size_scales[subkey], self.x_k_scales[subkey], self.y_k_scales[subkey], self.jumps[subkey]), self.v2_sub_scales[0]) for subkey in range(key.start, key.stop, key.step)]   
             elif key.stop < 0: 
                return [((self.filter_size_scales[0], self.x_k_scales[0], self.y_k_scales[0], self.jumps[0]), self.v2_sub_scales[subkey]) for subkey in range(key.start, -key.stop, key.step)]
             else:                 
                return [((self.filter_size_scales[0], self.x_k_scales[0], self.y_k_scales[0], self.jumps[0]), self.v2_sub_scales[0])]
          elif type(key) == tuple:
             if (type(key[0]) == int or type(key[0]) == slice) and (type(key[1]) == int or type(key[1]) == slice):
                return ((self.filter_size_scales[key[0]], self.x_k_scales[key[0]], self.y_k_scales[key[0]], self.jumps[key[0]]), self.v2_sub_scales[key[1]])
             else:
                raise KeyError('Bad index type for one of the subindixes %s for scaling - must be int or slice' % (key,))
          else: 
             raise KeyError('Bad index type %s for scaling item - must be an int, tuple, or slice' % (key,)) 
                  
      def setindex(self, f_idx=None, s_idx=None):

          if f_idx == None: f_idx = 0
          if s_idx == None: s_idx = 0
          self.index = (f_idx, s_idx)
          next_scale = self.__getitem__(key=self.index) 
          self.filter_scale = next_scale[0][0]
          self.x_kernel = next_scale[0][1]
          self.y_kernel = next_scale[0][2]
          self.jump = next_scale[0][3]
          self.v2_subfield = next_scale[1]


      def scale_weights(self, presynaptic, postsynaptic, ref_weight=0, index=None):
          mult_accum = lambda a, x: a*x
          if presynaptic == 'input':
             if postsynaptic != 'v1':
                raise ValueError('Only postsynaptic target for input layer is v1. Asked for %s' % postsynaptic)
             else:
                return 1.6/self.subsample_factor[0]*ref_weight
          elif presynaptic == 'v1':
             if postsynaptic != 'v2':
                raise ValueError('Only postsynaptic target for v1 layer is v2. Asked for %s' % postsynaptic)
             else:
                v1Size = reduce(mult_accum, self.v1_pop_size)
                v2Size = reduce(mult_accum, self.v2_pop_size)
                return v2Size/v1Size*ref_weight
          elif presynaptic == 'v2':
             if postsynaptic == 'v2':
                if index == None:
                   return [2/subscale*ref_weight for subscale in self.v2_sub_scales]
                elif type(index) == int:
                   return 2/self.v2_sub_scales[index]*ref_weight
                elif type(index) == slice:
                   return [2/self.v2_sub_scales[subindex]*ref_weight for subindex in range(index.start, index.stop, index.step)]
                else:
                   raise IndexError('Bad index type for v2-v2 connection subscale %s: should be an int or slice' % (index,))
             if postsynaptic == 'v4':
                v2Size = reduce(mult_accum, self.v2_pop_size)
                v4Size = reduce(mult_accum, self.v4_pop_size)
                return v4Size/v2Size*ref_weight
             else:
                raise ValueError('Valid postsynaptic targets for v2 are v2 and v4. Given %s' % postsynaptic)
          elif presynaptic == 'v4':
             if postsynaptic != 'LIP':
                raise ValueError('Only postsynaptic target for v4 layer is LIP. Asked for %s' % postsynaptic)
             else:       
                v4Size = reduce(mult_accum, self.v4_pop_size)
                lipSize = reduce(mult_accum, self.lip_pop_size)
                return lipSize/v4Size*ref_weight
          elif presynaptic == 'LIP':
             if postsynaptic != 'LIP':
                raise ValueError('Only postsynaptic target for LIP layer is LIP. Asked for %s' % postsynaptic)
             else:       
                lipSize = reduce(mult_accum, self.lip_pop_size)
                return 1/lipSize*ref_weight
          elif presynaptic == 'PFC':
             if postsynaptic != 'v4':
                raise ValueError('Only postsynaptic target for PFC layer is v4. Asked for %s' % postsynaptic)
             else:
                v4Size = reduce(mult_accum, self.v4_pop_size)
                pfcSize = reduce(mult_accum, self.pfc_pop_size)
                return v4Size/pfcSize*ref_weight

class scaling_instance(scale_factor):
  
      def __init__(self, init_obj=None, dimensions=0, dim_sizes=None, base_dim_size=16, subsample_factor_i_1=1.6, subsample_factor_1_2=1.0, subsample_factor2_4=2.0, subsample_factor4_L=1.0, base_filter_size=5.0, sweep_filter=False, filter_scale=(1,1,1), xy_kernel_quant_cutoff=(0,0), base_v2_subfield_size=2, sweep_subfield=False, subfield_scale=(1,1,1)):                    
          if init_obj != None:
             for obj_attr in init_obj.__dict__:
                 self.__dict__[obj_attr] = init_obj.__dict__[obj_attr]

          else:
             scale_factor.__init__(self, dimensions=dimensions, dim_sizes=dim_sizes, base_dim_size=base_dim_size, subsample_factor_i_1=subsample_factor_i_1, subsample_factor_1_2=subsample_factor_1_2, subsample_factor2_4=subsample_factor_2_4, subsample_factor4_L=subsample_factor_4_L, base_filter_size=base_filter_size, sweep_filter=sweep_filter, filter_scale=filter_scale, xy_kernel_quant_cutoff=xy_kernel_quant_cutoff, base_v2_subfield_size=base_v2_subfield_size, sweep_subfield=sweep_subfield, subfield_scale=subfield_scale)
          self.iterator = itertools.product(itertools.izip(self.filter_size_scales, self.x_k_scales, self.y_k_scales, self.jumps), self.v2_sub_scales)

      def __iter__(self):

          return self

      def __next__(self):

          next_scale = next(self.iterator)
          self.filter_scale = next_scale[0][0]
          self.x_kernel = next_scale[0][1]
          self.y_kernel = next_scale[0][2]
          self.jump = next_scale[0][3]
          self.v2_subfield = next_scale[1]
      
      def scale_weights(self, presynaptic, postsynaptic, ref_weight=0):

          if presynaptic == 'v2':
             if postsynaptic == 'v2':
                return 2/self.v2_subfield*ref_weight
             if postsynaptic == 'v4':
                v2Size = reduce(mult_accum, self.v2_pop_size)
                v4Size = reduce(mult_accum, self.v4_pop_size)
                return v4Size/v2Size*ref_weight
             else:
                raise ValueError('Valid postsynaptic targets for v2 are v2 and v4. Given %s' % postsynaptic)
          else:
             return scale_factor.scale_weights(self, presynaptic=presynaptic, postsynaptic=postsynaptic, ref_weight=ref_weight)        
