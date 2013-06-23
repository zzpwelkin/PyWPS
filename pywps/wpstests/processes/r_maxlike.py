#!/usr/bin/env python
#-*- encoding: utf-8 -*-
"""
unsupervised classification of an images group by max maximum-likelihood classifier method

Author: zzpwelkin
"""
def execute(inputs, number , min_size, output):
    from grass.script import core as grass
    import os
    
    inputs = inputs.split(',')
    # set the project of the new created location
    self.cmd(['g.proj','-c','georef={0}'.format(inputs[0])] )
    
    # set input data to new dataset
    gr_names = [ os.path.split(x) for x in range(len(inputs)) ]
    index = 0
    for inputdt in input:
        self.cmd( ['r.in.gdal','-e', '-o', 'input={0}'.format(inputdt), 
                   'output={0}'.format(gr_names[index])] )
        index += 1
        
    # create image group and subgroup
    self.cmd(['i.group', 'group=classfy_group', 'subgroup=classfy_subgroup', 'input={0}'.format(','.join(gr_names))])
    
    # cluster the image group
    self.cmd(['i.cluster', 'group=classfy_group', 'subgroup=classfy_subgroup', 'signaturefile=clustered', 
              'classes={0}'.format(number), 'min_size={0}'.format(min_size)])
    
    # maxlik classify
    self.cmd(['i.maxlik', 'class=maxliked', 'group=classfy_group', 'subgroup=classfy_subgroup', 
            'sigfile=clustered'])
    
    # output the result to a temporary file
    self.cmd(['r.out.gdal', 'input=maxliked', 'output={0}'.format(output)])
    
    # TODO: delete the group raster
    return

if __name__ == "__main__":
    import sys
    execute(inputs = sys.argv[1], number = sys.argv[2], min_size = sys.argv[3], output = sys.argv[4])