#-*- coding: UTF-8 -*-

import sys
import cv2
import numpy as np
import math
from PIL import Image

import imageUtil
import laserUtil

dottLen = 0.042333

#
# 検索対象領域からｴﾘｱの重なるものをｸﾞﾙｰﾌﾟ化する
#
# areaGroup : 領域が重なっているｵﾌﾞｼﾞｪｸﾄのﾘｽﾄ
#             ﾘｽﾄ最後のX座標が最終端となっている
#    pitchX : ﾍﾞｸﾄﾙ生成ﾋﾟｯﾁ
#  areaList : 検索対象領域
#
#    return : 領域ﾘｽﾄ  [rect1,rect2, ...]
#             ※areaGroup, areaList はこの関数で変更されます
#
def dup_area(areaGroup, pitchX, areaList, img_tmp = None):
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

#
# 膜座標のﾘｽﾄに対して、X方向の重なりを調べてｸﾞﾙｰﾌﾟ化する
#
# area_list : 膜座標のﾘｽﾄ
#  pixelLen : 1ﾋﾟｸｾﾙの長さ(mm)
# burnRange : 焼成幅(mm)
#
#    return : [ [rect1,rect2],[rect3,rect4], ... ]
#
def get_area_group(area_list, pixelLen, burnRange, img_tmp = None):
	vecArea = []

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

#
#  膜ｸﾞﾙｰﾌﾟの領域に対して垂直ﾍﾞｸﾄﾙﾃﾞｰﾀを生成する
#    対象領域の下に重なる領域が無い場合は終端とする
#
#    group : 膜座標のｸﾞﾙｰﾌﾟ( [rect1,rect2,rect3, ...])
# burnRange: 焼成幅(mm)
#     yLen : 垂直ﾍﾞｸﾄﾙの長さ(画像Yｻｲｽﾞ)(ﾋﾟｸｾﾙ)
# pixelLen : 1ﾋﾟｸｾﾙの長さ(mm)
#
#  return : [(x1,y1,x2,y2),(x1,y1,x2,y2),...]
#
def group_vec(group, burnRange, yLen, pixelLen):
	vec_list = []

	#y座標(top)の昇順でｿｰﾄ
	y_list = sorted(group, key=lambda y: y.y1)

	xStart = group[0].left(pixelLen)
	xEnd = group[-1].right(pixelLen)
	vecCnt = int((xEnd - xStart) / burnRange) + 1
	br = burnRange / 2

	#ﾍﾞｸﾄﾙの本数分
	for n in range(vecCnt):
		#画像に対しての垂直ﾍﾞｸﾄﾙ(焼成幅の始点)
		sx1 = xStart + n * burnRange
		sx2 = sx1
		sy1 = 0.0
		sy2 = yLen * pixelLen

		#画像に対しての垂直ﾍﾞｸﾄﾙ(焼成幅の終点)
		ex1 = xStart + n * burnRange + burnRange
		ex2 = ex1
		ey1 = 0.0
		ey2 = yLen * pixelLen	

		#ｸﾞﾙｰﾌﾟ内にﾋｯﾄするものがあるならﾋｯﾄした領域の下端
		#焼成幅でﾋｯﾄするか
		ty = 0
		for rect in y_list:
			px1,py1,px2,py2 = imageUtil.to_pixel(sx1,sy1,sx2,sy2,pixelLen)
			qx1,qy1,qx2,qy2 = imageUtil.to_pixel(ex1,ey1,ex2,ey2,pixelLen)
			if rect.HitTest(px1,py1,px2,py2) == True or rect.HitTest(qx1,qy1,qx2,qy2) == True:
				if ty < rect.bottom(pixelLen):
					ty = rect.bottom(pixelLen)

		#ﾋｯﾄしたものがあれば
		if ty != 0:
			sy2 = ty

		vec_list.append((sx1+br,sy1,sx2+br,sy2))

	return vec_list

#
#  膜ｸﾞﾙｰﾌﾟの領域に対して垂直ﾍﾞｸﾄﾙﾃﾞｰﾀを生成する
#    ｸﾞﾙｰﾌﾟを包含する四角形の全ｴﾘｱを対象とする
#
#    group : 膜座標のｸﾞﾙｰﾌﾟ( [rect1,rect2,rect3, ...])
# burnRange: 焼成幅(mm)
#     yLen : 垂直ﾍﾞｸﾄﾙの長さ(画像Yｻｲｽﾞ)(ﾋﾟｸｾﾙ)
# pixelLen : 1ﾋﾟｸｾﾙの長さ(mm)
#
#  return : [(x1,y1,x2,y2),(x1,y1,x2,y2),...]
#
def group_vec2(group, burnRange, yLen, pixelLen):
	vec_list = []

	#y座標(top)の昇順でｿｰﾄ
	y_list = sorted(group, key=lambda y: y.y1)

	xStart = group[0].left(pixelLen) + burnRange / 2.0
	xEnd = group[-1].right(pixelLen)
	vecCnt = int((xEnd - xStart) / burnRange) + 1
	yStart = 0.0
	yEnd = y_list[-1].bottom(pixelLen)

	#ﾍﾞｸﾄﾙの本数分
	for n in range(vecCnt):
		#画像に対しての垂直ﾍﾞｸﾄﾙ
		x1 = xStart + n * burnRange
		x2 = x1
		y1 = yStart
		y2 = yEnd
		vec_list.append((x1,y1,x2,y2))

	return vec_list
#
#      layerNo:
# materialName:
#    imageFile:
#    burnRange: 焼成幅
#       blockX:
#       blockY:
#
#
def func1(layerNo=1, materialName="", imageFile="", burnRange=0.60, blockX=2 ,blockY=2):
	#画像ﾌｧｲﾙを開く
	image = Image.open(imageFile)
	img_height = image.height
	image.close()

	#膜画像の座標を取得(収縮・膨張により線分除去)
	cnt = int(burnRange / dottLen / 5) + 1	#収縮・膨張回数
	rectList, img_tmp = imageUtil.get_film_pos(imageFile,cnt, isDraw=True)

	#膜をX座標の重なりでｸﾞﾙｰﾌﾟ化する
	group = get_area_group(rectList,dottLen,burnRange,img_tmp)

	#ｸﾞﾙｰﾌﾟ内の各領域に対して垂直ﾍﾞｸﾄﾙ・ﾘｽﾄを生成
	for idx,vec in enumerate(group):
 		vec_list = group_vec(vec,burnRange,img_height,dottLen)

		for rect in vec:
			rect.draw(img_tmp,imageUtil.get_col(idx))
 		for ln in vec_list:
			px1,py1,px2,py2 = imageUtil.to_pixel(ln[0],ln[1],ln[2],ln[3],dottLen)
			cv2.line(img_tmp,(px1,py1),(px2,py2),imageUtil.get_col(idx),1)
			#cv2.line(img_tmp,(px1,py1),(px2,py2),imageUtil.get_col(idx), int(burnRange/dottLen))

	cv2.imshow('film_view',img_tmp)
 	cv2.waitKey(0)

	cv2.destroyAllWindows()

#
#
#
if __name__ == '__main__':
	param = sys.argv

	if len(param) < 2:
		print 'usage: {0} <file>'.format(param[0])
		exit(0)

	func1(1,materialName="Test",imageFile=param[1])
