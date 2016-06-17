#-*- coding: UTF-8 -*-

#
# ﾏﾄﾘｯｸｽ測定
#
import missionLib as img
import servoLib as servo
import ctrlLib as ctrl
import ioLib as io
import time
import math
import sys

import Rowthon

mark_no = 11
countX = 6
countY = 6
pitchX = 35.000 * 10000	#ﾏﾄﾘｯｸｽﾃﾞｰﾀのX方向ﾋﾟｯﾁ
pitchY = 35.000 * 10000 #ﾏﾄﾘｯｸｽﾃﾞｰﾀのY方向ﾋﾟｯﾁ

#ﾛﾎﾞｯﾄｶﾒﾗ位置(MCM-Builder 固有値より)
#robotCameraCenterX = -52.5722
#robotCameraCenterY = 1.9112
robotCameraCenterX = -55.9368
robotCameraCenterY = 1.333676

#baseX = 348.822		#冶具左上のﾏｰｸとノズルが一致するX座標
#baseY = -231.273	#冶具左上のﾏｰｸとノズルが一致するY座標
baseX = -64.000		#冶具左上のﾏｰｸとノズルが一致するX座標
baseY = -480.000	#冶具左上のﾏｰｸとノズルが一致するY座標

pitchX = 35.000	#冶具のX方向ﾋﾟｯﾁ
pitchY = 35.000	#冶具のY方向ﾋﾟｯﾁ

#
#   (0,0) ----> Y+
#     |
#     |
#     X+
test_matrix_data = [
[(sys.maxint, sys.maxint),( 0.0000000, 1.00000000),( 0.0000000, 2.00000000),( 0.0000000, 3.00000000),( 0.000, 4.000),(sys.maxint, sys.maxint)],
[( 1.0000000, 0.00000000),( 1.0000000, 1.00000000),(sys.maxint, sys.maxint),( 1.0000000, 3.00000000),( 1.000, 4.000),( 1.0000000, 5.00000000)],
[( 2.0000000, 0.00000000),(sys.maxint, sys.maxint),( 2.0000000, 2.00000000),( 2.0000000, 3.00000000),( 2.000, 4.000),( 2.0000000, 5.00000000)],
[( 3.0000000, 0.00000000),( 3.0000000, 1.00000000),( 3.0000000, 2.00000000),(sys.maxint, sys.maxint),( 3.000, 4.000),( 3.0000000, 5.00000000)],
[( 4.0000000, 0.00000000),(sys.maxint, sys.maxint),( 4.0000000, 2.00000000),( 4.0000000, 3.00000000),( 4.000, 4.000),( 4.0000000, 5.00000000)],
[(sys.maxint, sys.maxint),( 5.0000000, 1.00000000),( 5.0000000, 2.00000000),( 5.0000000, 3.00000000),( 5.000, 4.000),(sys.maxint, sys.maxint)]
]


#
# 画像処理ｴﾗｰ位置の補間
#
def matrix_lerp(matrix_data):
	ret_matrix = []

	yMax = len(matrix_data) -1
	xMax = len(matrix_data[0]) -1
	for yy,lines in enumerate(matrix_data):
		line_data = []
		for xx,pos in enumerate(lines):
			if pos[0] == sys.maxint and pos[1] == sys.maxint:
				#画像処理異常の場合は maxint
				if yy == 0 and xx == 0:
					#左上
					vx = lines[1][0]
					vy = lines[1][1]
				elif yy == 0 and xx == xMax:
					#右上
					vx = lines[xMax-1][0]
					vy = lines[xMax-1][1]
				elif yy == yMax and xx == 0:
					#左下
					vx = matrix_data[yMax-1][0][0]
					vy = matrix_data[yMax-1][0][1]
				elif yy == yMax and xx == xMax:
					#右下
					vx = matrix_data[yMax-1][xMax-1][0]
					vy = matrix_data[yMax-1][xMax-1][1]
				else:
					pass
					xs = xx -1
					xe = xx	+1
					if xs < 0:
						xs = 0
					if xe > xMax:
						xe = xMax

					(x1,y1)=(lines[xs][0],lines[xs][1])
					(x2,y2)=(lines[xe][0],lines[xe][1])
					vx = (x1 + x2)/2
					vy = (y1 + y2)/2
					#その他
			else:
				vx = pos[0]
				vy = pos[1]

			line_data.append( (vx,vy) )
		ret_matrix.append( line_data )

	return( ret_matrix )

#
#
#
def main():
#	Rowthon.init_connection('127.0.0.1')
#	Rowthon.init_connection('192.168.1.4')

#	init_imaging()

	data = matrix_lerp(test_matrix_data)
	print data
#	itp_test()

#	Rowthon.close_connection()

if __name__ == '__main__':
	main()
