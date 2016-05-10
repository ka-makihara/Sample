#-*- coding: UTF-8 -*-

import sys
import cv2
import numpy as np

import thinning

colors = [(255,  0,  0),
		  (  0,255,  0),
		  (  0,  0,255),
		  (255,255,  0),
		  (255,  0,255),
		  (  0,255,255)]

def get_col(idx):
	return colors[ idx%len(colors) ]

def transform_by4(img, points):
	'''4点を指定してﾄﾘﾐﾝｸﾞする'''
	points = sorted(points, key=lambda x:x[1])
	top = sorted(points[:2],key=lambda x:x[0])
	bottom = sorted(points[2:],key=lambda x:x[0])
	points = np.array(top+bottom,dtype='float32')

	width = max(np.sqrt(((points[0][0]-points[2][0])**2)*2), np.sqrt(((points[1][0]-points[3][0])**2)*2))
	height = max(np.sqrt(((points[0][1]-points[2][1])**2)*2), np.sqrt(((points[1][1]-points[3][1])**2)*2))

	dst = np.array([
			np.array([0, 0]),
			np.array([width-1, 0]),
			np.array([width-1, height-1]),
			np.array([0, height-1]),
			], np.float32)

	trans = cv2.getPerspectiveTransform(points, dst)  # 変換前の座標と変換後の座標の対応を渡すと、透視変換行列を作ってくれる。
	return cv2.warpPerspective(img, trans, (int(width), int(height)))  # 透視変換行列を使って切り抜く。

def main(file):
	print " Hough Lines demo "
	print " Press h to draw lines using cv2.HoughLines()"
	print " Press p to draw lines using cv2.HoughLinesP()"
	print " All the parameter values selected at random, Change it the way you like"

	white = cv2.imread('F:\\white.png')
	im = cv2.imread(file)
	gray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
	edges = cv2.Canny(gray,150,200,apertureSize = 3)

	cv2.imshow('houghlines',im)

	neg4 = np.array([[0,1,0],
					 [1,1,1],
					 [0,1,0]],np.uint8)
	neg8 = np.array([[1,1,1],
					 [1,1,1],
					 [1,1,1]],np.uint8)

	img_tmp = im.copy()

	while(True):
		img = im.copy()
		k = cv2.waitKey(0)

		if k == ord('h'):   # Press 'h' to enable cv2.HoughLines()
			#ハフ変換
			lines = cv2.HoughLines(edges,1,np.pi/180,50)
			for rho,theta in lines[0]:
				a = np.cos(theta)
				b = np.sin(theta)
				x0 = a*rho
				y0 = b*rho
				x1 = int(x0 + 1000*(-b))   # Here i have used int() instead of rounding the decimal value, so 3.8 --> 3
				y1 = int(y0 + 1000*(a))    # But if you want to round the number, then use np.around() function, then 3.8 --> 4.0
				x2 = int(x0 - 1000*(-b))   # But we need integers, so use int() function after that, ie int(np.around(x))
				y2 = int(y0 - 1000*(a))
				cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)
			cv2.imshow('houghlines',img)
		elif k == ord('b'):
			#二値化画像
			cv2.imshow('houghlines',im)
			img_tmp = img.copy()
		elif k == ord('p'):
			# 線分抽出
			gray = cv2.cvtColor(img_tmp,cv2.COLOR_BGR2GRAY)
			edges = cv2.Canny(gray,150,200,apertureSize = 3)
			lines = cv2.HoughLinesP(edges,1,np.pi/180,10, minLineLength = 10, maxLineGap = 5)
			#for x1,y1,x2,y2 in lines[0]:
			for (idx,(x1,y1,x2,y2)) in enumerate(lines[0]):
				#cv2.line(img_tmp,(x1,y1),(x2,y2),(0,255,0),2)
				cv2.line(img_tmp,(x1,y1),(x2,y2),get_col(idx),2)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('l'):
			#輪郭抽出
			gray = cv2.cvtColor(img_tmp,cv2.COLOR_BGR2GRAY)
			contours,hierarchy = cv2.findContours(gray,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
			cv2.drawContours(img_tmp,contours,-1,(0,255,0),2)
			cv2.imshow('houghlines',img_tmp)

		elif k == ord('L'):
			#輪郭抽出
			gray = cv2.cvtColor(img_tmp,cv2.COLOR_BGR2GRAY)
			cnts = cv2.findContours(gray,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)[0]
			cnts.sort(key=cv2.contourArea,reverse=True)

			for i,c in enumerate(cnts):
				#輪郭を直線近似
				arclen = cv2.arcLength(c,True)
				hull = cv2.convexHull(c)		#座標を整列(時計まわり:右下、左下、左上、右上)
				approx = cv2.approxPolyDP(hull,0.02*arclen,True)
				#approx = cv2.approxPolyDP(c,0.02*arclen,True)

#				level = 1 - float(i) / len(cnts)
				if len(approx) == 4:
					#近似が4線(四角)
					pass
					cv2.drawContours(img_tmp,[approx],-1,(0,255,0),2)
					print approx[0], approx[1], approx[2], approx[3]
				else:
					cv2.drawContours(img_tmp,[approx],-1,(255,0,0),2)

				for pos in approx:
					cv2.circle(img_tmp,tuple(pos[0]),4,(0,0,255))

			cv2.imshow('houghlines',img_tmp)

		elif k == ord('-'):
			#収縮
			img_tmp = cv2.dilate(img_tmp,neg8,iterations=1)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('+'):
			#膨張
			img_tmp = cv2.erode(img_tmp,neg8,iterations=1)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('m'):
			#img_dst = cv2.morphologyEx(img,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(5,5)))
			#img_dst = cv2.morphologyEx(img,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
			img_tmp = cv2.morphologyEx(img_tmp,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5)))
			img_tmp = cv2.morphologyEx(img_tmp,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5)))
			#img_dst = cv2.morphologyEx(img,cv2.MORPH_CLOSE,neg8)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('n'):
			img_tmp = cv2.bilateralFilter(img_tmp,25,1,1)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('v'):
			tmp_mask = cv2.cvtColor(img_tmp,cv2.COLOR_BGR2GRAY)
			gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)	#原画
			img_mask = cv2.bitwise_not(gray,gray,mask=tmp_mask)

			img_tmp = cv2.bitwise_not(img_mask)	#反転
			cv2.imshow('houghlines',img_tmp)
			img_tmp = cv2.cvtColor(img_tmp,cv2.COLOR_GRAY2BGR)
		elif k == ord('t'):
			#細線化
			img_tmp = thinning.thinning_Hi(img_tmp)
			#img2 = thinning.thinning_Hi(img_tmp)
			cv2.imshow('houghlines',img_tmp)
			cv2.imwrite('tmp_image.png',img_tmp)
		elif k == ord('s'):
			#thresh, tmp = cv2.threshold(img_tmp, 0.5, 255.0, cv2.THRESH_BINARY)
			cv2.imwrite('tmp_image.png',img_tmp)
		elif k == 27:    # Press 'ESC' to exit
			 break
	cv2.destroyAllWindows()

if __name__ == '__main__':
	param = sys.argv

	if len(param) == 0:
		print 'usage: hugh2 <file>'
		exit(0)

	main(param[1])
