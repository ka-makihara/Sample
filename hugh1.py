#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      makihara
#
# Created:     22/03/2016
# Copyright:   (c) makihara 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import cv2
#from matplotlib import cm
from skimage.transform import (hough_line,hough_line_peaks,probabilistic_hough_line)

#from skimage.feature import canny
#from skimage import data

import numpy as np
#import matplotlib.pyplot as plt


image = cv2.imread("f:\\19-c1.png")
gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray,150,200,apertureSize = 3)

#edges = canny(image,2,1,25)
lines = probabilistic_hough_line(edges,threshold=10,line_length=5,line_gap=3)

for line in lines:
	p0,p1 = line
	cv2.line(image,(p0[0],p0[1]),(p1[0],p1[1]),(0,255,0),2)

cv2.imshow('houghlines',image)
cv2.waitKey(0)
cv2.destroyAllWindows()