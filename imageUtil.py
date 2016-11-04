#-*- coding: UTF-8 -*-
u"""openCVを使用した画像解析用ﾗｲﾌﾞﾗﾘ
	画像の収縮、拡張、細線化
"""

import sys
import cv2
import types
import numpy as np
import math
from PIL import Image

__version__ = "1.0.0"

# 膨張・収縮用ﾏｽｸﾃﾞｰﾀ
neg8 = np.array([[1,1,1],
				 [1,1,1],
				 [1,1,1]],np.uint8)

COL_GREEN = (255,  0,  0)
COL_BLUE  = (  0,255,  0)
COL_RED   = (  0,  0,255)
COL_SYAN  = (255,255,  0)
COL_YELLOW= (  0,255,255)

colors = [(255,  0,  0),
		  (  0,255,  0),
		  (  0,  0,255),
		  (255,255,  0),
		  (255,  0,255),
		  (  0,255,255)]

def get_col(idx):
	return colors[ idx%len(colors) ]

#
# 画像ﾌｧｲﾙの生成
#
def createPngFile(fileName, size=(640,640), color=(255,255,255)):
	try:
		#ｸﾞﾚｰｽｹｰﾙの画像ﾃﾞｰﾀを生成する
		img = Image.new('L',size,color)

		#ﾃﾞｰﾀをﾌｧｲﾙへ
		img.save(fileName)
	except:
		return False

	return True

def image_show(windowName, img, waitKey=True):
	cv2.imshow(windowName,img)

	if waitKey == True:
		cv2.waitKey(0)

def drawLine(img,start,end,col,thin=1):
	cv2.line(img,start,end,col,thin)

def destroyAllWindows():
	cv2.destroyAllWindows()

def image_save(file, img):
	cv2.imwrite(file,img)
#
# mm座標をﾋﾟｸｾﾙ座標に変換
#
def to_pixel(x1,y1,x2,y2,pixelLength):
	px1 = int(x1 / pixelLength)
	py1 = int(y1 / pixelLength)
	px2 = int(x2 / pixelLength)
	py2 = int(y2 / pixelLength)
	return px1,py1, px2,py2

def to_mm(x1,y1,x2,y2,pixelLength):
	vx1 = x1 * pixelLength
	vy1 = y1 * pixelLength
	vx2 = x2 * pixelLength
	vy2 = y2 * pixelLength
	return vx1, vy1, vx2, vy2

#直線が交差するか
def line_line(A1x,A1y,A2x,A2y, B1x,B1y,B2x,B2y):
	bX = B2x - B1x
	bY = B2y - B1y
	sx1 = A1x - B1x
	sy1 = A1y - B1y
	sx2 = A2x - B1x
	sy2 = A2y - B1y

	bs1 = bX * sy1 - bY * sx1
	bs2 = bX * sy2 - bY * sx2
	rr = bs1 * bs2
	if rr > 0:
		return False

	bX = A2x - A1x
	bY = A2y - A1y
	sx1 = B1x - A1x
	sy1 = B1y - A1y
	sx2 = B2x - A1x
	sy2 = B2y - A1y

	bs1 = bX * sy1 - bY * sx1
	bs2 = bX * sy2 - bY * sx2
	rr = bs1 * bs2
	if rr > 0:
		return False

	return True

class RectObj(object):
	def __init__(self, x1=0, y1=0, x2=0, y2=0):
		self.x1 = x1
		self.y1 = y1
		self.x2 = x2
		self.y2 = y2

	def get_pos(self):
		return( (self.x1, self.y2, self.x2, self.y2) )

	def width(self):
		return( math.fabs(self.x2-self.x1) )
	def height(self):
		return( math.fabs(self.y2-self.y1) )
	def left(self, pixLen=0.0):
		if pixLen == 0.0:
			return self.x1
		return self.x1 * pixLen
	def top(self, pixLen=0.0):
		if pixLen == 0.0:
			return self.y1
		return self.y1 * pixLen
	def right(self, pixLen=0.0):
		if pixLen == 0.0:
			return self.x2
		return self.x2 * pixLen
	def bottom(self, pixLen=0.0):
		if pixLen == 0.0:
			return self.y2
		return self.y2 * pixLen
	def pitchEnd(self, px = 0):
		if px == 0:
			return self.right()

		n = int(self.width() / px)
		if self.width() - (n * px) > 0:
			n += 1
		return self.left() + n * px

	def get_position(self, pixelLength):
		return self.x1*pixelLength, self.y1*pixelLength, self.x2*pixelLength, self.y2*pixelLength

	def get_rect_position(self, pixelLength):
		x1,y1,x2,y2 = self.get_position(pixelLength)
		return RectObj(x1,y1,x2,y2)

	def get_pixel(self, pixelLength):
		px1 = int(self.x1 / pixelLength)
		py1 = int(self.y1 / pixelLength)
		px2 = int(self.x2 / pixelLength)
		py2 = int(self.y2 / pixelLength)
		return px1, py1, px2, py2

	def get_rect_pixel(self, pixelLength):
		px1, py1, px2, py2 = self.get_pixel(pixelLength)
		return RectObj(px1,py1,px2,py2)

	def __eq__(self, other):
		if self.x1 == other.x1 and self.y1 == other.y1 and self.x2 == other.x2 and self.y2 == other.y2:
			return True
		return False

	#
	# 矩形と線分の交差判定
	#
	def HitTest(self, x1,y1, x2,y2):
		fx1 = float(x1)
		fy1 = float(y1)
		fx2 = float(x2)
		fy2 = float(y2)
		if line_line(self.x1,self.y1,self.x2,self.y1,fx1,fy1,fx2,fy2) == True:
			return True
		if line_line(self.x2,self.y1,self.x2,self.y2,fx1,fy1,fx2,fy2) == True:
			return True
		if line_line(self.x2,self.y2,self.x1,self.y2,fx1,fy1,fx2,fy2) == True:
			return True
		if line_line(self.x1,self.y2,self.x1,self.y1,fx1,fy1,fx2,fy2) == True:
			return True
		return False

	def draw(self, img, color):
		x1 = self.x1
		y1 = self.y1
		x2 = self.x2
		y2 = self.y2
		cv2.line(img,(x1,y1),(x2,y1),color,2)
		cv2.line(img,(x1,y1),(x1,y2),color,2)
		cv2.line(img,(x2,y1),(x2,y2),color,2)
		cv2.line(img,(x1,y2),(x2,y2),color,2)

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

	ww = 1
	for n in range(xx,width):
		data = [img.item(yy,n,0),img.item(yy,n,1),img.item(yy,n,2)]
		if all([x < 200 for x in data]):
			if ww < 2:
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

	ww = 1
	for n in range(yy,height):
		data = [img.item(n,xx,0),img.item(n,xx,1),img.item(n,xx,2)]
		if all([x < 200 for x in data]):
			if ww < 2:
				return 0
			return ww
		ww += 1

	return ww

def search_direction(img, yy,xx):
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
			return search_direction(img,yy+1,xx)

		dwL = get_img_data(img,yy+1,xx-1)
		if all([x > 200 for x in dwL]):
			set_img_data(img,yy+1,xx-1,0)
			return search_direction(img,yy+1,xx-1)

		if xx + 1 < width:
			right = get_img_data(img,yy,xx+1)
			if all([x > 200 for x in right]):
				set_img_data(img,yy,xx+1,0)
				return search_direction(img,yy,xx+1)

			dwR = get_img_data(img,yy+1,xx+1)
			if all([x > 200 for x in dwR]):
				set_img_data(img,yy+1,xx+1,0)
				return search_direction(img,yy+1,xx+1)

		return (yy,xx)

	elif yy + 1 < height:
		dw = get_img_data(img,yy+1,xx)
		if all([x > 200 for x in dw]):
			set_img_data(img,yy+1,xx,0)
			return search_direction(img,yy+1,xx)

		dwL = get_img_data(img,yy+1,xx-1)
		if all([x > 200 for x in dwL]):
			set_img_data(img,yy+1,xx-1,0)
			return search_direction(img,yy+1,xx-1)

		if xx + 1 < width:
			right = get_img_data(img,yy,xx+1)
			if all([x > 200 for x in right]):
				set_img_data(img,yy,xx+1,0)
				return search_direction(img,yy,xx+1)

			dwR = get_img_data(img,yy+1,xx+1)
			if all([x > 200 for x in dwR]):
				set_img_data(img,yy+1,xx+1,0)
				return search_direction(img,yy+1,xx+1)

		return (yy,xx)
	else:
		if xx + 1 < width:
			right = get_img_data(img,yy,xx+1)
			if all([x > 200 for x in right]):
				set_img_data(img,yy,xx+1,0)
				return search_direction(img,yy,xx+1)

			dwR = get_img_data(img,yy+1,xx+1)
			if all([x > 200 for x in dwR]):
				set_img_data(img,yy+1,xx+1,0)
				return search_direction(img,yy+1,xx+1)

		return( (yy,xx) )

def slanting_search(img, pixelLen):
	u"""[斜め方向のﾗｲﾝ検索]
	"""
	height,width = img.shape[:2]

	x1 = 0
	y1 = 0
	line_pos = []
	while y1 < height:
		x1 = 0
		while x1 < width:
			data = get_img_data(img,y1,x1)
			if all([x > 200 for x in data]):
				(y2,x2) = search_direction(img,y1,x1)
				#二点間の距離(ﾋﾟｸｾﾙ)
				dd = int(math.sqrt((x1 - x2) **2 + (y1 - y2) ** 2))
				if dd > 3:
					#print '({0},{1})-({2},{3})'.format(x1,y1,x2,y2)
					#(x2 - x1)*(y - y1) == (y2 - y1)*(x - x1)
					xlen = min(x1,width-x1)
					if xlen > y1:
						nx = (x2-x1)*(0-y1)/(y2 - y1) + x1
						#cv2.line(img,(nx,0),(x2,y2),(0,0,255),1)
						#line_pos.append((nx,0,x2,y2))
						#line_pos.append( (to_mm(nx,0,x2,y2,pixelLen)) )
						line_pos.append( (to_mm(nx,height,x2,height-y2,pixelLen)) )
					else:
						if x1 < (width-x1):
							nx = 0
						else:
							nx = width

						ny = (y2 - y1)*(nx - x1)/(x2-x1) + y1
						#cv2.line(img,(nx,ny),(x2,y2),(0,0,255),1)
						#line_pos.append((nx,ny,x2,y2))
						line_pos.append( (to_mm(nx,height-ny,x2,height-y2,pixelLen)) )

				else:
					#線分として認めない
					cv2.line(img,(x1,y1),(x2,y2),get_col(2),1)
			else:
				x1 += 1
		y1 += 1

	return line_pos

def horizontal_search(img, pixelLen):
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
					line_pos_h.append( (xx,height-yy,xx+ww+3,height-yy) )

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

		#line_pos.append( (0,l1[0][1],l1[-1][2],l1[0][1]) )
		line_pos.append( (to_mm(0,l1[0][1],l1[-1][2],l1[0][1],pixelLen)) )

		nl = [item for item in line_pos_h if item not in l1]
		line_pos_h = nl
		if len(line_pos_h) == 0:
			break

	return line_pos

def vertical_search(img, pixelLen):
	u"""[垂直方向にﾗｲﾝを検索]
		見つけた線分の始点Yは 0 とする(画像端)
		線分を抽出した部分は消去します
	"""
	height,width = img.shape[:2]

	#height -= 1
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
					#line_pos_v.append( (xx,height-yy,xx,height-(yy+ww)) )
					line_pos_v.append( (xx,height-(yy+ww),xx,height-(yy-3)) )

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

		#line_pos.append( (l1[0][0],0,l1[0][0],l1[-1][3]) )
		#line_pos.append( (to_mm(l1[0][0],0,l1[0][0],l1[-1][3],pixelLen)) )
		# Y方向の小さい順(画像上端)からﾘｽﾄが生成されているので
		# Yの座標を逆転させると、最初(0)のｱｲﾃﾑが最遠となる
		line_pos.append( (to_mm(l1[0][0],0,l1[0][0],l1[0][3],pixelLen)) )

		nl = [item for item in line_pos_v if item not in l1]
		line_pos_v = nl
		if len(line_pos_v) == 0:
			break	

	return line_pos

def line_search(img, pixelLen, isDraw=False):
	u"""[線分を検索]
		水平、垂直、斜めの順で走査

		  img : 画像ﾃﾞｰﾀ
		return: 線分座標ﾘｽﾄ [(x1,y1,x2,y2),(x1,y1,x2,y2), ...]
	"""
	height,width = img.shape[:2]
	line_pos = []

	img_tmp = img.copy()

	#横ﾗｲﾝを検索
	line_pos_h = horizontal_search(img, pixelLen)
	line_pos.extend( line_pos_h )

	#縦ﾗｲﾝを検索
	line_pos_v = vertical_search(img,pixelLen)
	line_pos.extend( line_pos_v );

	#斜めﾗｲﾝを検索
	line_pos_s = slanting_search(img,pixelLen)
	line_pos.extend( line_pos_s )

	#生成したﾗｲﾝの描画
	if isDraw == True:
		for pos in line_pos_h:
			px1,py1,px2,py2 = to_pixel(pos[0],pos[1],pos[2],pos[3],pixelLen)
			cv2.line(img_tmp,(px1,height-py1),(px2,height-py2),(255,0,0),1)

		for pos in line_pos_v:
			px1,py1,px2,py2 = to_pixel(pos[0],pos[1],pos[2],pos[3],pixelLen)
			cv2.line(img_tmp,(px1,height-py1),(px2,height-py2),(0,255,0),1)

		for pos in line_pos_s:
			px1,py1,px2,py2 = to_pixel(pos[0],pos[1],pos[2],pos[3],pixelLen)
			#cv2.line(img_tmp,(px1,py1),(px2,py2),(0,0,255),1)
			cv2.line(img_tmp,(px1,height-py1),(px2,height-py2),(0,0,255),1)

		cv2.imshow('line_vector',img_tmp)
		cv2.waitKey(0)

	return line_pos

def get_image_array(imageFile, dummyPrintY=100):
	u"""[ｲﾒｰｼﾞﾌｧｲﾙをｵｰﾌﾟﾝして白黒反転したﾃﾞｰﾀ配列を取得]
		焼成ﾃﾞｰﾀ画像は焼成部が黒(0,0,0)なので
		opencv用に「ｵﾌﾞｼﾞｪｸﾄ」(焼成部)を白とするため、反転させる

		  imageFile: 画像ﾌｧｲﾙ名
		dummyPrintY: 画像上端からの捨て打ち幅(ﾋﾟｸｾﾙ)
	"""
	#白黒反転用のﾙｯｸｱｯﾌﾟﾃｰﾌﾞﾙ
	lookup_tbl = np.ones((256,1),dtype='uint8')
	for i in range(256):
		lookup_tbl[i][0] = 255 - i

	if isinstance(imageFile,types.UnicodeType) == True:
		imageFile = imageFile.encode('ShiftJIS')

	src_im = cv2.imread(imageFile)
	#src_im = imageData
	xLen = len(src_im[0]) #画像の横ｻｲｽﾞ
	fill_data = [[255 for i in range(3)] for j in range(xLen)]
	for yy in range(dummyPrintY):
		src_im[yy] = fill_data


	#LUT を使用して白黒反転
	im = cv2.LUT(src_im,lookup_tbl)

	return im

def get_film_pos(imageData, count, isDraw=False):
	u"""[画像から「膜」の座標をﾘｽﾄとして取得する]
		imageFile: 画像ﾃﾞｰﾀ
		    count: 収縮・膨張回数(線分除去)

		   return: [(x1,y1,x2,y2),(x1,y1,x2,y2), ...], 膜画像ﾃﾞｰﾀ
	"""
	#画像ﾃﾞｰﾀ
	img_tmp = imageData.copy()

	#収縮して拡張して、線を消去
	#収縮
	for nn in range(count):
		img_tmp = cv2.erode(img_tmp,neg8,iterations=1)

	#膨張
	for nn in range(count):
		img_tmp = cv2.dilate(img_tmp,neg8,iterations=1)

	#戻り値用の「膜」を抽出した画像
	ret_img = img_tmp.copy()

	#輪郭抽出
	gray = cv2.cvtColor(img_tmp,cv2.COLOR_BGR2GRAY)
	#cnts = cv2.findContours(gray,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)[0]
	cnts = cv2.findContours(gray,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
	cnts.sort(key=cv2.contourArea,reverse=True)

	posList = []
	for i,c in enumerate(cnts):
		#輪郭を直線近似
		arclen = cv2.arcLength(c,True)
		hull = cv2.convexHull(c)		#座標を整列(時計まわり:右下、左下、左上、右上)
		approx = cv2.approxPolyDP(hull,0.02*arclen,True)

		if len(approx) == 4:
			#近似が4線(四角)
			if isDraw == True:
				cv2.drawContours(img_tmp,[approx],-1,(0,255,0),2)
				x = approx[2][0][0]
				y = approx[2][0][1]
				cv2.putText(img_tmp,str(i),(x,y),cv2.FONT_HERSHEY_PLAIN,1.0,(255,255,0))
			#print approx[0], approx[1], approx[2], approx[3]
			#print '{0}:({1},{2})-({3},{4})'.format(i,approx[2][0][0],approx[2][0][1],approx[3][0][0],approx[3][0][1])

			posList.append( RectObj(approx[2][0][0],approx[2][0][1],approx[0][0][0],approx[0][0][1]) )
		else:
			#外接四角形
			x,y,w,h = cv2.boundingRect(approx)
			posList.append( RectObj(x,y,x+w,y+h) )
			#print '{0}:({1},{2})-({3},{4})'.format(i,x,y,x+w,y+h)
			if isDraw == True:
				cv2.drawContours(img_tmp,[approx],-1,(255,0,0),2)
				cv2.rectangle(img_tmp,(x,y),(x+w, y+h),(255,0,0),2)
				cv2.putText(img_tmp,str(i),(x,y),cv2.FONT_HERSHEY_PLAIN,1.0,(255,255,0))

		if isDraw == True:
			for pos in approx:
				cv2.circle(img_tmp,tuple(pos[0]),4,(0,0,255))

	return posList, ret_img

