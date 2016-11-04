#-*- coding: UTF-8 -*-

u"""画像ﾌｧｲﾙから焼成用ﾍﾞｸﾄﾙﾃﾞｰﾀを生成する
	画像に対して、焼成幅以上を「膜」画像として分離する
	元画像から「膜」画像を引いたものを「線分」画像とする。
	線分画像に対しては、細線化処理を行い1ﾄﾞｯﾄのﾗｲﾝとする。
"""

import sys
import os
import numpy as np
import math
from PIL import Image

import imageUtil
import mcmUtil
import thinning
import cv2

__version__ = "1.0.0"

dottLen = 0.0423333

def dup_area(areaGroup, pitchX, areaList, img_tmp = None):
	u"""[検索対象領域からｴﾘｱの重なるものをｸﾞﾙｰﾌﾟ化する]

		areaGroup : 領域が重なっているｵﾌﾞｼﾞｪｸﾄのﾘｽﾄ
                    ﾘｽﾄ最後のX座標が最終端となっている
		   pitchX : ﾍﾞｸﾄﾙ生成ﾋﾟｯﾁ
		 areaList : 検索対象領域

		return    : 領域ﾘｽﾄ  [rect1,rect2, ...]
					※areaGroup, areaList はこの関数で変更されます
	"""
	if len(areaList) == 0:
		#ﾘｽﾄの最後なら
		return areaGroup

	nextArea = areaList[0]

	#ﾋﾟｯﾁ単位でのX終端(-1 ==>ﾘｽﾄの最後)
	xEnd = areaGroup[-1].pitchEnd(pitchX)

	if xEnd > nextArea.left():
		#次のｴﾘｱの左端より対象ｴﾘｱの右端(ﾋﾟｯﾁ換算)の方が大きい==焼成領域が重なる
		#対象領域を次の領域に設定し、その次の領域との重なりをﾁｪｯｸ
		nextArea = areaList.pop(0)

		if xEnd < nextArea.right():
			areaGroup.append(nextArea)
			return dup_area(areaGroup,pitchX,areaList, img_tmp)
		else:
			#見つけた領域より自身の領域の方が広いので
			# ﾘｽﾄの最終のX座標を最終端とするために一つ前に挿入する
			areaGroup.insert(areaGroup.index(areaGroup[-1]),nextArea)
			return dup_area(areaGroup,pitchX,areaList, img_tmp)

	#重なりが無い
	return areaGroup

def get_area_group(area_list, pixelLen, burnRange, img_tmp = None):
	u"""[膜座標のﾘｽﾄに対して、X方向の重なりを調べてｸﾞﾙｰﾌﾟ化する]
		area_list : 膜座標のﾘｽﾄ
		 pixelLen : 1ﾋﾟｸｾﾙの長さ(mm)
		burnRange : 焼成幅(mm)

		   return : [ [rect1,rect2],[rect3,rect4], ... ]
	"""
	vecArea = []

	if len(area_list) == 0:
		return vecArea

	#x1 の座標が小さい(左から)でｿｰﾄ(昇順)する
	area_list.sort(key=lambda x: x.x1)

	while True:
		base = area_list.pop(0)
		group = [base]
		dup = dup_area(group,int(burnRange * pixelLen),area_list, img_tmp)

		vecArea.append(group)

		if len(area_list) == 0:
			break

 	return vecArea

def group_vec(group, burnRange, yLen, pixelLen):
	u"""[膜ｸﾞﾙｰﾌﾟの領域に対して垂直ﾍﾞｸﾄﾙﾃﾞｰﾀを生成する]
			対象領域の下に重なる領域が無い場合は終端とする

	        group : 膜座標のｸﾞﾙｰﾌﾟ( [rect1,rect2,rect3, ...])
		 burnRange: 焼成幅(mm)
		     yLen : 垂直ﾍﾞｸﾄﾙの長さ(画像Yｻｲｽﾞ)(ﾋﾟｸｾﾙ)
		 pixelLen : 1ﾋﾟｸｾﾙの長さ(mm)

		  return : [(x1,y1,x2,y2),(x1,y1,x2,y2),...]
	 """
	vec_list = []

	x_list = sorted(group, key=lambda x: x.x1)

	#y座標(top)の降順でｿｰﾄ
	y_list = sorted(group, key=lambda y: y.y2, reverse=True)

	xStart = x_list[0].left(pixelLen)
	xEnd = group[-1].right(pixelLen)
	vecCnt = int((xEnd - xStart) / burnRange) + 1
	br = burnRange / 2

	#ﾍﾞｸﾄﾙの本数分
	for n in range(vecCnt):
		#画像に対しての垂直ﾍﾞｸﾄﾙ(焼成幅の始点)
		sx1 = xStart + n * burnRange
		sx2 = sx1
		sy2 = 0.0
		sy1 = yLen * pixelLen

		#画像に対しての垂直ﾍﾞｸﾄﾙ(焼成幅の終点)
		ex1 = xStart + n * burnRange + burnRange
		ex2 = ex1
		ey2 = 0.0
		ey1 = yLen * pixelLen	

		#ｸﾞﾙｰﾌﾟ内にﾋｯﾄするものがあるならﾋｯﾄした領域の下端
		#焼成幅でﾋｯﾄするか
		ty = yLen * pixelLen 
		for rect in y_list:
			px1,py1,px2,py2 = imageUtil.to_pixel(sx1,sy1,sx2,sy2,pixelLen)
			qx1,qy1,qx2,qy2 = imageUtil.to_pixel(ex1,ey1,ex2,ey2,pixelLen)

			if rect.HitTest(px1,py1,px2,py2) == True or rect.HitTest(qx1,qy1,qx2,qy2) == True:
				if ty > rect.top(pixelLen):
					ty = rect.top(pixelLen)

		#ﾋｯﾄしたものがあれば
		if ty != 0:
			sy2 = ty

		vec_list.append((sx1+br,(yLen * pixelLen) - sy1,sx2+br,(yLen * pixelLen) - sy2))

	return vec_list

def group_vec2(group, burnRange, yLen, pixelLen):
	u"""[膜ｸﾞﾙｰﾌﾟの領域に対して垂直ﾍﾞｸﾄﾙﾃﾞｰﾀを生成する]
    		ｸﾞﾙｰﾌﾟを包含する四角形の全ｴﾘｱを対象とする

		   group : 膜座標のｸﾞﾙｰﾌﾟ( [rect1,rect2,rect3, ...])
		burnRange: 焼成幅(mm)
		    yLen : 垂直ﾍﾞｸﾄﾙの長さ(画像Yｻｲｽﾞ)(ﾋﾟｸｾﾙ)
		pixelLen : 1ﾋﾟｸｾﾙの長さ(mm)

		  return : [(x1,y1,x2,y2),(x1,y1,x2,y2),...]
  	"""
	vec_list = []

	#x座標(left)の昇順でｿｰﾄ
	x_list = sorted(group, key=lambda x: x.x1)
	#y座標(bottom)の降順でｿｰﾄ
	y_list = sorted(group, key=lambda y: y.y2, reverse=True)

	xStart = x_list[0].left(pixelLen)
	xEnd = x_list[-1].right(pixelLen)
	vecCnt = int((xEnd - xStart) / burnRange) + 1
	yStart = yLen * pixelLen
	yEnd = y_list[-1].top(pixelLen)

	#ﾍﾞｸﾄﾙの本数分
	for n in range(vecCnt):
		#画像に対しての垂直ﾍﾞｸﾄﾙ
		x1 = xStart + n * burnRange
		x2 = x1
		y1 = yEnd
		y2 = yStart
		vec_list.append((x1,y1-yEnd,x2,y2-yEnd))

	return vec_list

def get_vect_list(imageData,  burnRange=0.60, isDraw=False):
	u"""[画像ﾌｧｲﾙから焼成ﾍﾞｸﾄﾙを生成する]
		imageData : 画像ﾃﾞｰﾀ
		burnRange : 焼成幅(mm)
	"""
	#膜画像の座標を取得(収縮・膨張により線分除去)
	cnt = int(burnRange / dottLen / 5) + 1	#収縮・膨張回数
	rectList, img_tmp = imageUtil.get_film_pos(imageData,cnt, isDraw=isDraw)

	img_height, img_width = imageData.shape[:2]
	img_src = img_tmp.copy()
	#
	# 「膜」ﾍﾞｸﾄﾙの生成
	#
	#膜をX座標の重なりでｸﾞﾙｰﾌﾟ化する
	group = get_area_group(rectList,dottLen,burnRange,img_tmp)

	film_vect = []
	#ｸﾞﾙｰﾌﾟ内の各領域に対して垂直ﾍﾞｸﾄﾙ・ﾘｽﾄを生成
	for idx,vec in enumerate(group):
 		vec_list = group_vec2(vec,burnRange,img_height,dottLen)

 		if isDraw == True:
			for rect in vec:
				rect.draw(img_tmp,imageUtil.get_col(idx))

 		for ln in vec_list:
 			film_vect.append( (ln[0],ln[1],ln[2],ln[3]) )
			if isDraw == True:
				px1,py1,px2,py2 = imageUtil.to_pixel(ln[0],ln[1],ln[2],ln[3],dottLen)
				imageUtil.drawLine(img_tmp,(px1,img_height-py1),(px2,img_height-py2),imageUtil.COL_RED,1)

	if isDraw == True:
		imageUtil.image_show('film_view',img_tmp, waitKey=True)

	#
	# 「線」ﾍﾞｸﾄﾙの生成
	#
	if isDraw == True:
		imageUtil.image_show('film_view',img_src, waitKey=True)
		imageUtil.image_show('film_view',imageData, waitKey=True)

	gray = cv2.cvtColor(imageData,cv2.COLOR_BGR2GRAY)	#原画
	tmp_mask = cv2.cvtColor(img_src,cv2.COLOR_BGR2GRAY)

	img_tmp = cv2.bitwise_not(gray,gray,mask=tmp_mask)
	if isDraw == True:
		imageUtil.image_show('film_view',img_tmp, waitKey=True)

	#細線化
	img_tmp = cv2.cvtColor(img_tmp,cv2.COLOR_GRAY2BGR)
	img_tmp = thinning.thinning_Hi(img_tmp)
	if isDraw == True:
		imageUtil.image_show('film_view',img_tmp, waitKey=True)
		#imageUtil.image_save('thin.png',img_tmp)

	#線分ﾍﾞｸﾄﾙの走査
	line_vect = imageUtil.line_search(img_tmp,dottLen)
	if isDraw == True:
		for ln in line_vect:
			px1,py1,px2,py2 = imageUtil.to_pixel(ln[0],ln[1],ln[2],ln[3],dottLen)
			imageUtil.drawLine(img_tmp,(px1,img_height-py1),(px2,img_height-py2),imageUtil.COL_RED,1)
		imageUtil.image_show('film_view',img_tmp, waitKey=True)

	if isDraw == True:
		imageUtil.destroyAllWindows()

	return film_vect,line_vect 

def create_vect_file(imageFile, burnRange=0.60, offsetX=0.0, offsetY=0.0, isDraw=False):
	u"""[ｲﾒｰｼﾞﾌｧｲﾙよりﾍﾞｸﾄﾙﾃﾞｰﾀﾌｧｲﾙを生成する]
		imageFile: ﾍﾞｸﾄﾙﾃﾞｰﾀを生成する元画像ﾌｧｲﾙ名
		burnRange: 焼成幅(mm)
		  offsetX: ﾍﾞｸﾄﾙ生成ｵﾌｾｯﾄX
		  offsetY: ﾍﾞｸﾄﾙ生成ｵﾌｾｯﾄY

		return   : 生成したﾍﾞｸﾄﾙﾌｧｲﾙ名
		             膜用、線用の二個、生成してない場合は ""
	"""
	#vector ﾌｫﾙﾀﾞを生成する
	vec_path = mcmUtil.get_job_path() + '\\vector'
	if os.path.exists(vec_path) == False:
		os.makedirs(vec_path)

	#画像ﾃﾞｰﾀ取得
	img_src = imageUtil.get_image_array(imageFile)

	film_vect, line_vect = get_vect_list(img_src,burnRange,isDraw=isDraw)

	if len(film_vect) == 0 and len(line_vect) == 0:
		return False

	#name, ext = os.path.splitext( os.path.basename(img_file) )
	name, ext = os.path.splitext( os.path.basename(imageFile) )

	vec_file_film = ""
	if len(film_vect):
		vec_file = mcmUtil.get_job_path() + '\\vector\\Laser_scan_film_' + name.encode('ShiftJIS') + '.vect'
		with open(vec_file,'w') as f:
			f.write('LISTSTART\n')
			for vv in film_vect:
				f.write('JUMP {0:.3f} {1:.3f}\n'.format(vv[0]+offsetX,vv[1]+offsetY))
				f.write('MARK {0:.3f} {1:.3f}\n'.format(vv[2]+offsetX,vv[3]+offsetY))

			f.write('LISTEND\n')
		vec_file_film = 'Laser_scan_film_' + name + '.vect'

		#ﾋﾟｸｾﾙ座標確認用
		'''
		f1 = mcmUtil.get_job_path() + '\\vector\\Laser_scan_film_' + name.encode('ShiftJIS') + '.txt'
		with open(f1,'w') as f:
			for vv in film_vect:
				px1,py1,px2,py2 = imageUtil.to_pixel(vv[0],vv[1],vv[2],vv[3],dottLen)
				f.write('({0},{1})-({2},{3})\n'.format(px1,py1,px2,py2))
		'''

	# 線分ﾍﾞｸﾄﾙ
	vec_file_line = ""
	if len(line_vect):
		vec_file = mcmUtil.get_job_path() + '\\vector\\Laser_scan_line_' + name.encode('ShiftJIS') + '.vect'
		with open(vec_file,'w') as f:
			f.write('LISTSTART\n')
			for vv in line_vect:
				f.write('JUMP {0:.3f} {1:.3f}\n'.format(vv[0]+offsetX,vv[1]+offsetY))
				f.write('MARK {0:.3f} {1:.3f}\n'.format(vv[2]+offsetX,vv[3]+offsetY))

			f.write('LISTEND\n')
		vec_file_line = 'Laser_scan_line_' + name + '.vect'

		#ﾋﾟｸｾﾙ座標確認用
		'''
		f2 = mcmUtil.get_job_path() + '\\vector\\Laser_scan_line_' + name.encode('ShiftJIS') + '.txt'
		with open(f2,'w') as f:
			for vv in line_vect:
				px1,py1,px2,py2 = imageUtil.to_pixel(vv[0],vv[1],vv[2],vv[3],dottLen)
				f.write('({0},{1})-({2},{3})\n'.format(px1,py1,px2,py2))
		'''

	return vec_file_film, vec_file_line
#
#
#
if __name__ == '__main__':
	param = sys.argv

	if len(param) < 2:
		print 'usage: {0} <imageFile>'.format(param[0])
		exit(0)

	img_path = os.path.dirname( param[1] )

	exePath = os.path.dirname(param[0])
	if exePath == "":
		exePath = os.getcwd()

	os.chdir(img_path)

	mcmUtil.init_mcm_util( img_path,exePath )

	#img_src = imageUtil.get_image_array( param[1] )

	#film_vect, line_vect = get_vect_list(img_src,burnRange=0.60,isDraw=True)
	ofx = float( mcmUtil.get_job_data('instrumentGroup/circuitPrinter/offsetX') )
	ofy = float( mcmUtil.get_job_data('instrumentGroup/circuitPrinter/offsetY') )
	create_vect_file(imageFile=param[1], isDraw=False,offsetX=ofx,offsetY=ofy)

	from ctypes import *
	user32 = windll.user32
	user32.MessageBoxW(0,u"ﾍﾞｸﾄﾙﾌｧｲﾙを生成しました",u"vect",0x40)
