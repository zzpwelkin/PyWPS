#!/usr/bin/env python
import time
import numpy
from osgeo import gdal
def execute(input, ow, oh, output):
    dataset = gdal.Open(input)
    
    driver = gdal.GetDriverByName('GTiff')
    
    dest_dataset = driver.Create(output, ow, oh, dataset.RasterCount)
    
    for index in range(dataset.RasterCount):
        band = dataset.GetRasterBand(index+1)
        
        dest_dataset.GetRasterBand(index+1).WriteArray(band.ReadAsArray(0, 0, band.XSize, band.YSize, ow, oh))
    
    dataset = None
    dest_dataset = None
    
if __name__ == "__main__":
    import sys 
    if (len(sys.argv) == 6):
        time.sleep(int(sys.argv[5]))
        
    execute(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])