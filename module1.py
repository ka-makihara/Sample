#-*- coding: UTF-8 -*-

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
import cv2
import numpy as np

# 膨張・収縮用ﾏｽｸﾃﾞｰﾀ
neg8 = np.array([[1,1,1],
				 [1,1,1],
				 [1,1,1]],np.uint8)

def main():
	os.chdir('f:\\source\\jobConverter')
	img = Image.open("12-f.png")

	xs = img.size[0]
	ys = img.size[1]
	tmp = Image.new('L',img.size,(255,255,255))

	#画像の上部100ﾋﾟｸｾﾙを塗りつぶす
	data = img.load()
	fill_data = [[255 for i in range(3)] for j in range(img.size[0])]
	for yy in range(100):
		data[0,yy] = fill_data

	#openCvﾃﾞｰﾀへ変換
	ocv_im = np.asarray(img)

	#白黒反転用のﾙｯｸｱｯﾌﾟﾃｰﾌﾞﾙ
	lookup_tbl = np.ones((256,1),dtype='uint8')
	for i in range(256):
		lookup_tbl[i][0] = 255 - i

	#収縮
	'''
	img_tmp = cv2.erode(ocv_im,neg8,iterations=1)
	cv2.imshow("data1",img_tmp)
	cv2.waitKey(0)

	cv2.destroyAllWindows()
	'''

	#openCvで保存
	#cv2.imwrite("sample_ocv.png",ocv_im)
	#cv2.imwrite("sample_ocv.png",img_tmp)

	#LUT を使用して白黒反転
	img_tmp = cv2.LUT(ocv_im,lookup_tbl)

	#PILﾃﾞｰﾀへ変換
	#pil_im = Image.fromarray(ocv_im)
	pil_im = Image.fromarray(img_tmp)

	#PIL保存
	pil_im.save("sample_pil.png")


if __name__ == '__main__':
	main()
