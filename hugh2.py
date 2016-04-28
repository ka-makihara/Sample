#-*- coding: UTF-8 -*-

import sys
import cv2
import numpy as np
import math

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

def get_img_data(img, yy, xx):
	return [img.item(yy,xx,0),img.item(yy,xx,1),img.item(yy,xx,2)]

def set_img_data(img, yy, xx, col):
	img.itemset((yy,xx,0),col)
	img.itemset((yy,xx,1),col)
	img.itemset((yy,xx,2),col)

def search_horizontal(img, yy, xx):
	u"""[水平方向に画像を走査]
		   img : 画像ﾃﾞｰﾀ
		   yy : ﾋﾟｸｾﾙ座標 Y
		   xx : ﾋﾟｸｾﾙ座標 X
		return: 線分の長さ(ﾋﾟｸｾﾙ)
	"""
	height,width = img.shape[:2]

	ww = 0
	for n in range(xx,width):
		data = [img.item(yy,n,0),img.item(yy,n,1),img.item(yy,n,2)]
		if all([x < 200 for x in data]):
			if ww < 3:
				return 0
			return ww
		ww += 1

	return ww

def search_vertical(img, yy,xx):
	u"""[水直方向に画像を走査]
		   img : 画像ﾃﾞｰﾀ
		   yy : ﾋﾟｸｾﾙ座標 Y
		   xx : ﾋﾟｸｾﾙ座標 X
		return: 線分の長さ(ﾋﾟｸｾﾙ)
	"""
	height,width = img.shape[:2]

	ww = 0
	for n in range(yy,height):
		data = [img.item(n,xx,0),img.item(n,xx,1),img.item(n,xx,2)]
		if all([x < 200 for x in data]):
			if ww < 3:
				return 0
			return ww
		ww += 1

	return ww	

def direction(img, yy,xx):
	u"""[斜めを含めて画像を走査していく]
		   img : 画像ﾃﾞｰﾀ
		    yy : ﾋﾟｸｾﾙ座標 Y
		    xx : ﾋﾟｸｾﾙ座標 X
		return : ﾗｲﾝが途切れた座標(y,x)
	"""
	height,width = img.shape[:2]

	if yy == 0:
		dw = get_img_data(img,yy+1,xx)
		if all([x > 200 for x in dw]):
			set_img_data(img,yy+1,xx,0)
			return direction(img,yy+1,xx)

		dwL = get_img_data(img,yy+1,xx-1)
		if all([x > 200 for x in dwL]):
			set_img_data(img,yy+1,xx-1,0)
			return direction(img,yy+1,xx-1)

		if xx + 1 < width:
			right = get_img_data(img,yy,xx+1)
			if all([x > 200 for x in right]):
				set_img_data(img,yy,xx+1,0)
				return direction(img,yy,xx+1)

			dwR = get_img_data(img,yy+1,xx+1)
			if all([x > 200 for x in dwR]):
				set_img_data(img,yy+1,xx+1,0)
				return direction(img,yy+1,xx+1)

		return (yy,xx)

	elif yy + 1 < height:
		dw = get_img_data(img,yy+1,xx)
		if all([x > 200 for x in dw]):
			set_img_data(img,yy+1,xx,0)
			return direction(img,yy+1,xx)

		dwL = get_img_data(img,yy+1,xx-1)
		if all([x > 200 for x in dwL]):
			set_img_data(img,yy+1,xx-1,0)
			return direction(img,yy+1,xx-1)

		if xx + 1 < width:
			right = get_img_data(img,yy,xx+1)
			if all([x > 200 for x in right]):
				set_img_data(img,yy,xx+1,0)
				return direction(img,yy,xx+1)

			dwR = get_img_data(img,yy+1,xx+1)
			if all([x > 200 for x in dwR]):
				set_img_data(img,yy+1,xx+1,0)
				return direction(img,yy+1,xx+1)

		return (yy,xx)
	else:
		if xx + 1 < width:
			right = get_img_data(img,yy,xx+1)
			if all([x > 200 for x in right]):
				set_img_data(img,yy,xx+1,0)
				return direction(img,yy,xx+1)

			dwR = get_img_data(img,yy+1,xx+1)
			if all([x > 200 for x in dwR]):
				set_img_data(img,yy+1,xx+1,0)
				return direction(img,yy+1,xx+1)

		return( (yy,xx) )

def slanting_search(img, y1=0, x1=0):
	u"""[斜め方向のﾗｲﾝ検索]
	"""
	height,width = img.shape[:2]

	line_pos = []
	while y1 < height:
		x1 = 0
		while x1 < width:
			data = get_img_data(img,y1,x1)
			if all([x > 200 for x in data]):
				(y2,x2) = direction(img,y1,x1)
				#二点間の距離(ﾋﾟｸｾﾙ)
				dd = int(math.sqrt((x1 - x2) **2 + (y1 - y2) ** 2))
				if dd > 3:
					#print '({0},{1})-({2},{3})'.format(x1,y1,x2,y2)
					#(x2 - x1)*(y - y1) == (y2 - y1)*(x - x1)
					xlen = min(x1,width-x1)
					if xlen > y1:
						nx = (x2-x1)*(0-y1)/(y2 - y1) + x1
						#cv2.line(img,(nx,0),(x2,y2),(0,0,255),1)
						line_pos.append((nx,0,x2,y2))
					else:
						if x1 < (width-x1):
							nx = 0
						else:
							nx = width

						ny = (y2 - y1)*(nx - x1)/(x2-x1) + y1
						#cv2.line(img,(nx,ny),(x2,y2),(0,0,255),1)
						line_pos.append((nx,ny,x2,y2))

				else:
					#線分として認めない
					cv2.line(img,(x1,y1),(x2,y2),get_col(2),1)
			else:
				x1 += 1
		y1 += 1

	return line_pos

def horizontal_search(img, yy=0, xx=0):
	u"""[水平方向にﾗｲﾝを検索]
		見つけた線分の始点Xは 0 とする(画像端)
		線分を抽出した部分は消去します
	"""
	height,width = img.shape[:2]

	#横ﾗｲﾝを検索
	line_pos_h =[]
	line_pos = []
	yy = 0
	while yy < height:
		xx = 0
		while xx < width:
			data = [img.item(yy,xx,0),img.item(yy,xx,1),img.item(yy,xx,1)]
			#if all([x > 200 for x in img[yy,xx]]):
			if all([x > 200 for x in data]):
				ww = search_horizontal(img,yy,xx+1)
				if ww > 0:
					line_pos_h.append( (xx,yy,xx+ww,yy) )

					#見つけたﾗｲﾝは消去(3ﾋﾟｸｾﾙ幅+前後3ﾋﾟｸｾﾙ延長)
					cv2.line(img,(xx-3,yy),(xx+ww+3,yy),(0,0,0),1)
					cv2.line(img,(xx-3,yy-1),(xx+ww+3,yy-1),(0,0,0),1)
					cv2.line(img,(xx-3,yy+1),(xx+ww+3,yy+1),(0,0,0),1)

					xx += ww
				else:
					xx += 1
			else:
				xx += 1
		yy += 1

	while len(line_pos_h):
		y1 = line_pos_h[0][1]
		l1 = filter(lambda x: x[1]==y1,line_pos_h)

		line_pos.append( (0,l1[0][1],l1[-1][2],l1[0][1]) )

		nl = [item for item in line_pos_h if item not in l1]
		line_pos_h = nl
		if len(line_pos_h) == 0:
			break

	return line_pos

def vertical_search(img, yy=0, xx=0):
	u"""[垂直方向にﾗｲﾝを検索]
		見つけた線分の始点Yは 0 とする(画像端)
		線分を抽出した部分は消去します
	"""
	height,width = img.shape[:2]

	#縦ﾗｲﾝを検索
	line_pos_v = []
	line_pos = []
	xx = 0
	while xx < width:
		yy = 0
		while yy < height:
			data = [img.item(yy,xx,0),img.item(yy,xx,1),img.item(yy,xx,1)]
			if all([x > 200 for x in data]):
				ww = search_vertical(img,yy+1,xx)
				if ww > 0:
					line_pos_v.append( (xx,yy,xx,yy+ww) )

					#見つけたﾗｲﾝは消去(3ﾋﾟｸｾﾙ幅+上下3ﾋﾟｸｾﾙ延長)
					cv2.line(img,(xx,yy-3),(xx,yy+ww+3),(0,0,0),1)
					cv2.line(img,(xx+1,yy-3),(xx+1,yy+ww+3),(0,0,0),1)
					cv2.line(img,(xx-1,yy-3),(xx-1,yy+ww+3),(0,0,0),1)

					yy += ww
				else:
					yy += 1
			else:
				yy += 1
		xx += 1

	while len(line_pos_v):
		x1 = line_pos_v[0][0]
		l1 = filter(lambda x: x[0]==x1,line_pos_v)
		#print 'X:{0}={1}'.format(x1,l1)

		line_pos.append( (l1[0][0],0,l1[0][0],l1[-1][3]) )

		nl = [item for item in line_pos_v if item not in l1]
		line_pos_v = nl
		if len(line_pos_v) == 0:
			break	

	return line_pos

def line_search(img):
	line_pos = []

	img_tmp = img.copy()

	#横ﾗｲﾝを検索
	line_pos_h = horizontal_search(img)
	line_pos.append( line_pos_h )

	#縦ﾗｲﾝを検索
	line_pos_v = vertical_search(img)
	line_pos.append( line_pos_v );

	#斜めﾗｲﾝを検索
	line_pos_s = slanting_search(img)
	line_pos.append( line_pos_s )

	#生成したﾗｲﾝの描画
	for pos in line_pos_h:
		cv2.line(img_tmp,(pos[0],pos[1]),(pos[2],pos[3]),(255,0,0),1)

	for pos in line_pos_v:
		cv2.line(img_tmp,(pos[0],pos[1]),(pos[2],pos[3]),(0,255,0),1)

	for pos in line_pos_s:
		cv2.line(img_tmp,(pos[0],pos[1]),(pos[2],pos[3]),(0,0,255),1)

	cv2.imshow('houghlines',img_tmp)
	cv2.waitKey(0)

	return line_pos


def main(file):

	lookup_tbl = np.ones((256,1),dtype='uint8')
	for i in range(256):
		lookup_tbl[i][0] = 255 - i

	src_im = cv2.imread(file)

	#LUT を使用して白黒反転
	im = cv2.LUT(src_im,lookup_tbl)

	# 2値化でﾌｨﾙﾀを使用したら線分が消えてしまう場合がある
	#thresh, im = cv2.threshold(src_im, 1, 255, cv2.THRESH_BINARY_INV)

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

			for (idx,(x1,y1,x2,y2)) in enumerate(lines[0]):
				cv2.line(img_tmp,(x1,y1),(x2,y2),get_col(idx),2)

			cv2.imshow('houghlines',img_tmp)
		elif k == ord('l'):
			#輪郭抽出
			gray = cv2.cvtColor(img_tmp,cv2.COLOR_BGR2GRAY)
			#contours,hierarchy = cv2.findContours(gray,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

			contours,hierarchy = cv2.findContours(gray,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
			#一番の外周のみ
			#contours,hierarchy = cv2.findContours(gray,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

			contours.sort(key=cv2.contourArea,reverse=True)

			cv2.drawContours(img_tmp,contours,-1,(0,255,0),2)
			cv2.imshow('houghlines',img_tmp)

			for con in contours:
				#print con
				#print '-------------\n'
				'''
				for c1 in con:
					print c1[0][0], c1[0][1] #-> xx yy
					cv2.line(img_tmp,(0,0),(c1[0][0],c1[0][1]),(0,0,255,),1)
					cv2.imshow('houghlines',img_tmp)
					cv2.waitKey(0)
				'''
				'''
				rect = cv2.minAreaRect(con)
				points = cv2.cv.BoxPoints(rect)
				cv2.rectangle(img_tmp, (int(points[1][0]), int(points[1][1])), (int(points[3][0]), int(points[3][1])), (255, 0, 0), 2)
				cv2.imshow('houghlines',img_tmp)
				cv2.waitKey(0)
				'''

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
					cv2.drawContours(img_tmp,[approx],-1,(0,255,0),2)
					print approx[0], approx[1], approx[2], approx[3]
				else:
					cv2.drawContours(img_tmp,[approx],-1,(255,0,0),2)

				for pos in approx:
					cv2.circle(img_tmp,tuple(pos[0]),4,(0,0,255))

			cv2.imshow('houghlines',img_tmp)

		elif k == ord('+'):
			#膨張
			img_tmp = cv2.dilate(img_tmp,neg8,iterations=1)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('-'):
			#収縮
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
			#img_tmp = cv2.bilateralFilter(img_tmp,25,1,1)
			img_tmp = cv2.bilateralFilter(img_tmp,0,32,2)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('v'):
			tmp_mask = cv2.cvtColor(img_tmp,cv2.COLOR_BGR2GRAY)
			gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)	#原画

			img_tmp = cv2.bitwise_not(gray,gray,mask=tmp_mask)
			#img_tmp = cv2.bitwise_not(tmp_mask,tmp_mask,mask=gray)
			cv2.imshow('houghlines',img_tmp)
			img_tmp = cv2.cvtColor(img_tmp,cv2.COLOR_GRAY2BGR)

			# 黒配線の場合
			#img_mask = cv2.bitwise_not(gray,gray,mask=tmp_mask)
			#img_tmp = cv2.bitwise_not(img_mask)	#反転
			#cv2.imshow('houghlines',img_tmp)
			#cv2.imshow('houghlines',img_mask)
			#img_tmp = cv2.cvtColor(img_mask,cv2.COLOR_GRAY2BGR)
		elif k == ord('t'):
			#細線化
			img_tmp = thinning.thinning_Hi(img_tmp)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('c'):
			line_search(img_tmp)
			cv2.imshow('houghlines',img_tmp)
		elif k == ord('s'):
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
