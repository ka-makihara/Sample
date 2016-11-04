#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      makihara
#
# Created:     04/11/2016
# Copyright:   (c) makihara 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import imageUtil
from PIL import Image

def main():
	os.chdir('f:\\source\\jobConverter')
	img = Image.open("1-f.png")

	xs = img.size[0]
	ys = img.size[1]
	tmp = Image.new('L',img.size,(255,255,255))

	data = img.load()
	fill_data = [[255 for i in range(3)] for j in range(img.size[0])]
	for yy in range(100):
		data[0,yy] = fill_data

	pix = tmp.load()
	for yy in range(img.size[1]):
		for xx in range(img.size[0]):
			col = data[xx,yy]
			if col == 255:
				pix[xx,yy] = 0
			else:
				pix[xx,yy] = 255

	tmp.save('dummy.png')

if __name__ == '__main__':
	main()
