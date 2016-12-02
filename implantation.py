#-*- coding: UTF-8 -*-
u"""埋め込みｱﾙｺﾞﾘｽﾞﾑ

"""

import os
import sys
import math
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np
from itertools import groupby
from collections import defaultdict
import cv2

import jobUtil
import imageUtil
import mcmUtil
import laserUtil
import vectUtil

__version__ = "1.0.0"

#### ｻｲｽﾞ計算用ﾊﾟﾗﾒｰﾀ ######
mount_margin    = (0.3,0.3)				#実装精度ﾏｰｼﾞﾝ
cavity_ratio    = 0.56					#ｷｬﾋﾞﾃｨ傾斜による流れ込み比率
embedded_margin = (0.0, 0.0)			#埋め込みﾏｰｼﾞﾝ
dot_R           = 0.116					#着弾径
dot_pitch       = (0.042333, 0.042333)	#印刷ﾄﾞｯﾄﾋﾟｯﾁ
resin_ratio     = 0.93					#樹脂の硬化収縮率
resin_dot_qty   = 52.5					#構造材1ﾄﾞｯﾄあたりの塗布量
resin_path      = 40					#構造材1層当たりの印刷ﾊﾟｽ数
resin_img_block = 16					#構造材ｲﾒｰｼﾞﾌｧｲﾙ分割数(4x4=16)
print_ratio     = 0.98					#埋め込み印刷ｴﾘｱの拡大比率

#  (originX,originY,originZ),(imageIndex)
#           layer[0]           layer[1]
#    [0][0]  [0][1]  [0][2]
image_table = [
[(0.0000000,0.0000000,0.0000),(1,4)],
[(0.0846667,0.0846667,0.0000),(3,2)],
[(0.0846667,0.0000000,0.0000),(3,4)],
[(0.0000000,0.0846667,0.0000),(1,2)],
[(0.0423330,0.0423330,0.0000),(2,3)],
[(0.1270000,0.1270000,0.0000),(4,1)],
[(0.1270000,0.0423330,0.0000),(4,3)],
[(0.0423330,0.1270000,0.0000),(2,1)],
[(0.1270000,0.0000000,0.0000),(4,4)],
[(0.0423330,0.0846667,0.0000),(2,2)],
[(0.0423330,0.0000000,0.0000),(2,4)],
[(0.1270000,0.0846667,0.0000),(4,2)],
[(0.0000000,0.0423330,0.0000),(1,3)],
[(0.0846667,0.1270000,0.0000),(3,1)],
[(0.0846667,0.0423330,0.0000),(3,3)],
[(0.0000000,0.1270000,0.0000),(1,1)]
]

#画像位置ずれ補正用(本来は不要なはずだが・・・)
img_pix_offsetY = 10
img_pix_offsetX = -3
'''
#PILデータで画像を読み込む
im = Image.open('t.jpg')

#OpenCVデータに変換
ocv_im = np.asarray(im)

#OpenCVで保存
cv2.imwrite("t_ocv.jpg",ocv_im)

#PILデータへ変換
pil_im = Image.fromarray(ocv_im)
#PILで保存
pil_im.save("t_pil.jpg")
'''

##############################
#
# 内部で使用している関数
#
def mm_to_pix( (x,y) ):
	u''' mm 位置をﾋﾟｸｾﾙ位置へ変換する
		(x,y): mm 位置
	'''
	return ( int(x/dot_pitch[0]), int(y/dot_pitch[1]) )	

def pix_to_mm( (x,y) ):
	u''' ﾋﾟｸｾﾙ位置をmm位置へ変換する
		(x,y): ﾋﾟｸｾﾙ 位置
	'''
	return ( x*dot_pitch[0], y*dot_pitch[1] )	

def parts_capacity(partsData):
	u'''ﾊﾟｰﾂ体積
	'''
	if partsData.capacity == 0.0:
		return partsData.x_size * partsData.y_size * partsData.height

	return partsData.capacity

def get_parts_capa(mnt_list):
	u'''
	'''
	capa = 0.0
	for md in mnt_list:
		capa += parts_capacity(md.parts)

	return capa

def resin_thickness():
	u''' 構造材1層あたりの厚み
		<計算式>
	 樹脂の硬化収縮率
	 × 構造材1ﾄﾞｯﾄ当たりの塗布量
	 ÷ 1000000
	 ÷ (印刷ﾄﾞｯﾄﾋﾟｯﾁ_X × 印刷ﾄﾞｯﾄﾋﾟｯﾁ_Y)
	 × 構造材1層当たりの印刷ﾊﾟｽ数
	 ÷ 構造材ｲﾒｰｼﾞﾌｧｲﾙ分割数
	'''
	ret = resin_ratio * resin_dot_qty / 1000000.0 /(dot_pitch[0] * dot_pitch[1]) * resin_path / resin_img_block

	return ret

def struct_layer_qty(partsData):
	u'''ｷｬﾋﾞﾃｨの構造材積層数
		<計算式>
		(部品高さ÷構造材1層当たりの厚み)+1
	'''
	return int(partsData.height / resin_thickness()) + 1

def cavity_margin(partsData):
	u'''ｷｬﾋﾞﾃｨﾏｰｼﾞﾝ(x,y)
		<計算式>
		ｷｬﾋﾞﾃｨ傾斜による流れ込み比率 × ｷｬﾋﾞﾃｨの構造材積層数 × 構造材1層あたりの厚み
	'''
	d = cavity_ratio * struct_layer_qty(partsData) * resin_thickness()

	return( (d,d) )

def cavity_size(partsData):
	u'''ｷｬﾋﾞﾃｨｴﾘｱの大きさ(x,y)
		partsData[0]:ﾊﾟｰﾂXｻｲｽﾞ
		partsData[1]:ﾊﾟｰﾂYｻｲｽﾞ
		partsData[2]:ﾊﾟｰﾂ高さ

		<計算式>
		  部品ｻｲｽﾞ
		+ 2 × 実装精度ﾏｰｼﾞﾝ
		+ 2 × ｷｬﾋﾞﾃｨﾏｰｼﾞﾝ
		+ 2 × 埋め込みﾏｰｼﾞﾝ
		+ 着弾径
		+ 印刷ﾄﾞｯﾄﾋﾟｯﾁ÷2
	'''
	xs = partsData.x_size + (2 * mount_margin[0]) + (2 * cavity_margin(partsData)[0]) + (2 * embedded_margin[0]) + dot_R + (dot_pitch[0] / 2)
	ys = partsData.y_size + (2 * mount_margin[1]) + (2 * cavity_margin(partsData)[1]) + (2 * embedded_margin[1]) + dot_R + (dot_pitch[1] / 2)

	return (xs,ys)

def cavity_dot(partsData):
	u'''ｷｬﾋﾞﾃｨｴﾘｱの大きさﾄﾞｯﾄ数(x,y)
		<計算式>
		(ｷｬﾋﾞﾃｨｴﾘｱの大きさ÷印刷ﾄﾞｯﾄﾋﾟｯﾁ)+1
	'''
	sz = cavity_size(partsData)

	xd = int(sz[0] / dot_pitch[0]) + 1
	yd = int(sz[1] / dot_pitch[1]) + 1

	return (xd,yd)

def cavity_capacity(partsData):
	u'''ｷｬﾋﾞﾃｨ容積
		<計算式>
		 (ｷｬﾋﾞﾃｨｴﾘｱﾄﾞｯﾄ数_X × ｷｬﾋﾞﾃｨｴﾘｱﾄﾞｯﾄ数_Y)
		×構造材1層当たりのﾊﾟｽ数
		÷構造材ｲﾒｰｼﾞﾌｧｲﾙ分割数
		×ｷｬﾋﾞﾃｨの構造材積層数
		×構造材1ﾄﾞｯﾄあたりの塗布量
		-部品体積×1000000.0
	'''
	dot = cavity_dot(partsData)
	capa = parts_capacity(partsData)

	ret = (dot[0] * dot[1]) * resin_path / resin_img_block * struct_layer_qty(partsData) * resin_dot_qty - (capa * 1000000.0)

	return ret

def dot_r():
	u'''構造材1ﾄﾞｯﾄ飛翔径
		<計算式>
		(構造材1ﾄﾞｯﾄあたりの塗布量 × 3 × 6 ÷ π)^(1 ÷ 3) × 10 ÷ 1000.0
	'''
	ret = math.pow((resin_dot_qty * 3.0 * 6.0 / math.pi),(1.0 / 3.0)) * 10.0 / 1000.0

	return ret

def outer_embedded_size(partsData):
	u'''埋め込みエリア側側の大きさ(x,y)
		<計算式>
		  ｷｬﾋﾞﾃｨｴﾘｱの大きさ
		+ 埋め込み印刷ｴﾘｱの拡大比率
		× ｷｬﾋﾞﾃｨの構造材積層数
		× 構造材1層あたりの厚み
	'''
	sz = cavity_size(partsData)
	xs = sz[0] + print_ratio * struct_layer_qty(partsData) * resin_thickness()
	ys = sz[1] + print_ratio * struct_layer_qty(partsData) * resin_thickness()

	return (xs,ys)

def outer_embedded_dot(partsData):
	u'''埋め込みエリア外側の大きさﾄﾞｯﾄ数(x,y)
		<計算式>
		埋め込みエリア外側の大きさ / 印刷ﾄﾞｯﾄﾋﾟｯﾁ
	'''
	sz = outer_embedded_size(partsData)

	return ( int(sz[0]/dot_pitch[0]), int(sz[1]/dot_pitch[1]) )

def inner_embedded_size(partsData):
	u'''埋め込みエリア内側の大きさ(x,y)
		<計算式>
		  部品ｻｲｽﾞ
		+ 2 × 実装精度ﾏｰｼﾞﾝ
		+ 構造材1ﾄﾞｯﾄ飛翔径
		+ 印刷ﾄﾞｯﾄﾋﾟｯﾁ ÷ 2
	'''
	xs = partsData.x_size + 2 * mount_margin[0] + dot_r() + dot_pitch[0] / 2.0
	ys = partsData.y_size + 2 * mount_margin[1] + dot_r() + dot_pitch[1] / 2.0

	return (xs,ys)

def inner_embedded_dot(partsData):
	u'''埋め込みエリア内側の大きさﾄﾞｯﾄ数(x,y)
		<計算式>
		埋め込みエリア内側の大きさ / 印刷ﾄﾞｯﾄﾋﾟｯﾁ
	'''
	sz = inner_embedded_size(partsData)

	return ( int(sz[0]/dot_pitch[0])+1, int(sz[1]/dot_pitch[1])+1 )

def embedded_slope_capacity(partsData):
	u'''埋め込み傾斜部の体積
		<計算式>
		  1 ÷ 3 × (ｷｬﾋﾞﾃｨ外形と部品とのｻｲｽﾞ差[XX,YY,ZZ]) 
		+ 1 ÷ 2 × (ｷｬﾋﾞﾃｨ外形と部品とのｻｲｽﾞ差[XX,YY]) × ｷｬﾋﾞﾃｨ外形と部品とのｻｲｽﾞ差(ZZ)
		+ 部品ｻｲｽﾞX × 部品ｻｲｽﾞY × ｷｬﾋﾞﾃｨ外形と部品とのｻｲｽﾞ差(ZZ)
	'''
	od = outer_embedded_dot(partsData)

	#ｷｬﾋﾞﾃｨ外形と部品とのｻｲｽﾞ差
	xx = od[0] * dot_pitch[0] - partsData.x_size
	yy = od[1] * dot_pitch[1] - partsData.y_size
	zz = struct_layer_qty(partsData) * resin_thickness() - partsData.height

	ret = 1.0 / 3.0 * (xx * yy * zz) \
		+ 1.0 / 2.0 * (xx * partsData.x_size + yy * partsData.y_size) * zz \
		+ partsData.x_size * partsData.y_size * zz

	return ret 

def create_multi_parts(mount_list):
	u'''複数のﾊﾟｰﾂを一つのﾊﾟｰﾂとして仮想ﾊﾟｰﾂを生成する
		・条件
			実装方向は水平・垂直のみ
	'''
	#実装方向から実装角度を算出
	mlx = sorted(mount_list, key=lambda x: x.xPos)
	mly = sorted(mount_list, key=lambda x: x.yPos)

	xLen = mlx[-1].xPos - mlx[0].xPos
	yLen = mly[-1].yPos - mly[0].yPos

	dir_R = math.atan2(yLen,xLen)
	margin_x = (len(mount_list) - 1) * (mount_margin[0] * math.cos(dir_R)) * 2
	margin_y = (len(mount_list) - 1) * (mount_margin[1] * math.sin(dir_R)) * 2

	mount_list.sort(key=lambda x: (x.xPos, x.yPos))

	xLenSum = 0
	yLenSum = 0
	parts_capacity = 0.0
	for md in mount_list:
		r = math.radians(md.angle)

		ww = md.parts.x_size /2
		hh = md.parts.y_size /2

		#部品の座標
		#   B-------D
		#   |       |
		#   |   E   |
		#   |       |
		#   A-------C
		# 実装位置(xPos,yPos)と部品ｻｲｽﾞから部品座標を設定
		A = (md.xPos-ww,md.yPos-hh)
		B = (md.xPos-ww,md.yPos+hh)
		C = (md.xPos+ww,md.yPos-hh)
		D = (md.xPos+ww,md.yPos+hh)
		E = (md.xPos,md.yPos)
		R = sorted([A,B,C,D], key=lambda x: (x[0],x[1]))

		#指定角度で回転
		AA = ((A[0]-E[0]) * math.cos(r) - (A[1]-E[1]) * math.sin(r) + E[0], (A[0]-E[0]) * math.sin(r) + (A[1]-E[1]) * math.cos(r) + E[1])
		BB = ((B[0]-E[0]) * math.cos(r) - (B[1]-E[1]) * math.sin(r) + E[0], (B[0]-E[0]) * math.sin(r) + (B[1]-E[1]) * math.cos(r) + E[1])
		CC = ((C[0]-E[0]) * math.cos(r) - (C[1]-E[1]) * math.sin(r) + E[0], (C[0]-E[0]) * math.sin(r) + (C[1]-E[1]) * math.cos(r) + E[1])
		DD = ((D[0]-E[0]) * math.cos(r) - (D[1]-E[1]) * math.sin(r) + E[0], (D[0]-E[0]) * math.sin(r) + (D[1]-E[1]) * math.cos(r) + E[1])

		#回転した各座標(AA,BB,CC,DD)が上図Aと同じ位置関係になるようにｿｰﾄする
		RR = sorted([AA,BB,CC,DD], key=lambda x: (x[0],x[1]))

		xl = RR[2][0] - RR[0][0]
		yl = RR[1][1] - RR[0][1]

		if xLenSum == 0 and yLenSum == 0:
			#xLenSum = xl + mount_margin[0] * math.cos(dir_R)
			#yLenSum = yl + mount_margin[1] * math.sin(dir_R)
			xLenSum = xl
			yLenSum = yl
		else:
			#xLenSum += (xl * math.cos(dir_R) + mount_margin[0] * math.cos(dir_R))
			#yLenSum += (yl * math.sin(dir_R) + mount_margin[1] * math.sin(dir_R))
			xLenSum += (xl * math.cos(dir_R))
			yLenSum += (yl * math.sin(dir_R))

		#ﾊﾟｰﾂ体積は各ﾊﾟｰﾂ体積の合計
		parts_capacity += (md.parts.x_size * md.parts.y_size * md.parts.height)

	xLenSum += margin_x
	yLenSum += margin_y

	return jobUtil.PartsData("temp",xLenSum,yLenSum,mount_list[0].parts.height,capa=parts_capacity)

def embedded_print_qty(partsData):
	u'''埋め込み印刷層数
		<計算式>
		  (ｷｬﾋﾞﾃｨｴﾘｱの大きさﾄﾞｯﾄ数(x,y) × ｷｬﾋﾞﾃｨ構造材積層数
		- 構造材ｲﾒｰｼﾞﾌｧｲﾙ分割数 × (部品体積 + 埋め込み傾斜部の体積) × 1000000.0
		÷ (構造材1ﾄﾞｯﾄあたりの塗布量 × 構造材1層当たりの印刷ﾊﾟｽ数))
		÷ (樹脂の硬化収縮率 × (埋め込みエリア外側の大きさﾄﾞｯﾄ数 - 埋め込みエリア内側の大きさﾄﾞｯﾄ数))
	'''
	cav_dot = cavity_dot(partsData)
	out_dot = outer_embedded_dot(partsData)
	inner_dot = inner_embedded_dot(partsData)

	ret = (cav_dot[0] * cav_dot[1] * struct_layer_qty(partsData) \
		- resin_img_block * (parts_capacity(partsData) + embedded_slope_capacity(partsData)) * 1000000.0 \
		/ (resin_dot_qty * resin_path)) \
		/ (resin_ratio * ( out_dot[0] * out_dot[1] - inner_dot[0] * inner_dot[1]))
 
 	#print 'parts:{0} Qty={1}'.format(partsData.name, ret)
	return int(ret)

def embedded_print_path(partsData):
	u'''埋め込み残りの印刷ﾊﾟｽ数
		<計算式>
		 ((ｷｬﾋﾞﾃｨｴﾘｱのﾄﾞｯﾄ数[dx,dy] × ｷｬﾋﾞﾃｨの構造材積層数
		- 構造材ｲﾒｰｼﾞﾌｧｲﾙ分割数
		÷ (構造材1ﾄﾞｯﾄあたりの塗布量 × 構造材1層当たりの印刷ﾊﾟｽ数) × (部品体積 + 埋め込み傾斜部の体積) × 1000000.0)
		÷ (樹脂の硬化収縮率 × (埋め込みエリア外側の大きさ - 埋め込みエリア内側の大きさ)) - 埋め込み印刷層数)
		× 構造材1層当たりの印刷ﾊﾟｽ数
	'''
	cav_dot = cavity_dot(partsData)
	outer = outer_embedded_dot(partsData)
	inner = inner_embedded_dot(partsData)

	ret = ((cav_dot[0] * cav_dot[1] * struct_layer_qty(partsData) \
		- resin_img_block \
		/ (resin_dot_qty * resin_path) * (parts_capacity(partsData) + embedded_slope_capacity(partsData)) * 1000000.0) \
		/ (resin_ratio * (outer[0] * outer[1] - inner[0] * inner[1])) - embedded_print_qty(partsData)) \
		* resin_path

	return int(ret)

def exist_parts(job_parts, mount_parts):
	u'''JOBの中に埋め込むﾊﾟｰﾂの定義があるか確認する
		  job_parts: JOBに記述されたﾊﾟｰﾂﾘｽﾄ
		mount_parts: mountData に記述されたﾊﾟｰﾂﾘｽﾄ
	'''
	for mp in mount_parts:
		#nameが同じものを抽出する
		nn = filter((lambda x: x.name == mp.name),job_parts)

		if len(nn) == 0:
			#抽出したものが無い -> 含まれない
			return False

	return True

def create_glue_img(src_imgFile, tgt_imgFile):
	u''' 画像ﾌｧｲﾙを白黒反転させたﾌｧｲﾙを生成する
		src_imgFile: 元画像ﾌｧｲﾙ名
		tgt_imgFile: 生成するﾌｧｲﾙ名
	'''
	#ｲﾒｰｼﾞﾌｧｲﾙ
	img = Image.open(src_imgFile)
	pix1 = img.load()

	#上部100ﾗｲﾝ分を白で塗りつぶす(捨て打ちエリアの除外)
	fill_data = [[255 for i in range(3)] for j in range(img.size[0])]	#画像横ｻｲｽﾞ
	for yy in range(100):
		pix[0,yy] = fill_data

	#openCvﾃﾞｰﾀへ変換
	ocv_im = np.asarray(img)

	#白黒反転用のﾙｯｸｱｯﾌﾟﾃｰﾌﾞﾙ
	lookup_tbl = np.ones((256,1),dtype='uint8')
	for i in range(256):
		lookup_tbl[i][0] = 255 - i

	#ｷｬﾋﾞﾃｨ画像(白抜き画像)に対して、接着用画像は白黒逆転させる
	#LUT を使用して白黒反転
	img_tmp = cv2.LUT(ocv_im,lookup_tbl)

	#PILﾃﾞｰﾀへ変換
	pil_img = Image.fromarray(img_tmp)

	#画像保存
	pil_img.save( tgt_imgFile )

def show_cv_image(srcImg):
	cv2.imshow("data",srcImg)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

def create_parts_emb_image(partsData, angle=0.0 ):
	u'''ﾊﾟｰﾂの埋め込みｲﾒｰｼﾞﾃﾞｰﾀを生成(Pillowﾃﾞｰﾀ)
		partsData: ﾊﾟｰﾂﾃﾞｰﾀ

		回転を考慮するために実際のｷｬﾝﾊﾞｽはｷｬﾋﾞﾃｨｻｲｽﾞの二倍にする
		ｷｬﾋﾞﾃｨは白、ｷｬﾋﾞﾃｨの内側は128(合成のため)とする
	'''
	#埋め込みｴﾘｱ外側の大きさﾄﾞｯﾄ数
	outer_img_size = outer_embedded_dot(partsData)

	#埋め込みｴﾘｱ内側の大きさのﾄﾞｯﾄ数
	inner_img_size = inner_embedded_dot(partsData)

	canvas_size = (outer_img_size[0]*2,outer_img_size[1]*2)
	canvas = Image.new('L',canvas_size,0)
	#ｸﾞﾚｰｽｹｰﾙの画像ﾃﾞｰﾀを生成する(外側:白、内側:黒)
	outer_img = Image.new('L',outer_img_size,255)
	inner_img = Image.new('L',inner_img_size,128)

	#貼り付け位置
	ofx = (outer_img_size[0] - inner_img_size[0]) / 2
	ofy = (outer_img_size[1] - inner_img_size[1]) / 2

	#合成(外側 + 内側)
	outer_img.paste(inner_img,(ofx,ofy))

	#canvasの中心に配置
	posx = int( (canvas_size[0]-outer_img_size[0]) / 2)
	posy = int( (canvas_size[1]-outer_img_size[1]) / 2)
	canvas.paste(outer_img,(posx,posy))

	#指定角度で回転
	tmp = canvas.rotate(angle)

	return tmp

def create_parts_cavity_image(partsData, angle=0.0 ):
	u'''ﾊﾟｰﾂのｷｬﾋﾞﾃｨｲﾒｰｼﾞﾃﾞｰﾀを生成(Pillowﾃﾞｰﾀ)
		partsData: ﾊﾟｰﾂﾃﾞｰﾀ

		回転を考慮するために実際のｷｬﾝﾊﾞｽはｷｬﾋﾞﾃｨｻｲｽﾞの二倍にする
		ｷｬﾋﾞﾃｨは白、ｷｬﾋﾞﾃｨの内側は128(合成のため)とする
	'''
	#ｷｬﾋﾞﾃｨｴﾘｱのﾄﾞｯﾄ数
	outer_img_size = cavity_dot(partsData)

	#埋め込みｴﾘｱ内側の大きさのﾄﾞｯﾄ数
	inner_img_size = inner_embedded_dot(partsData)

	canvas_size = (outer_img_size[0]*2,outer_img_size[1]*2)
	canvas = Image.new('L',canvas_size,0)
	#ｸﾞﾚｰｽｹｰﾙの画像ﾃﾞｰﾀを生成する(外側:白、内側:黒)
	outer_img = Image.new('L',outer_img_size,255)
	inner_img = Image.new('L',inner_img_size,128)

	#貼り付け位置
	ofx = (outer_img_size[0] - inner_img_size[0]) / 2
	ofy = (outer_img_size[1] - inner_img_size[1]) / 2

	#合成(外側 + 内側)
	outer_img.paste(inner_img,(ofx,ofy))

	#canvasの中心に配置
	posx = int( (canvas_size[0]-outer_img_size[0]) / 2)
	posy = int( (canvas_size[1]-outer_img_size[1]) / 2)
	canvas.paste(outer_img,(posx,posy))

	#指定角度で回転
	tmp = canvas.rotate(angle)

	return tmp

def paste_image(canvas_inf, canvas, src_img, offset):
	u'''ｷｬﾝﾊﾞｽにｷｬﾋﾞﾃｨｲﾒｰｼﾞを張り付ける
		ただし、128に設定された内側ﾃﾞｰﾀは黒(0)に変換する
	'''
	canvas_pix = canvas.load()
	src_pix = src_img.load()
	src_size = src_img.size

	for yy in range(src_size[1]):
		for xx in range(src_size[0]):
			base = canvas_pix[xx+offset[0],yy+offset[1]]
			info = canvas_inf[yy+offset[1]][xx+offset[0]]
			src = src_pix[xx,yy]
			if info == 0:
				#画素は未配置
				if src == 0:
					#回転のためのﾀﾞﾐｰ領域なら
					pass
				else:
					if src == 128:
						#ｷｬﾋﾞﾃｨ内側(ﾊﾟｰﾂ領域)
						canvas_pix[xx+offset[0],yy+offset[1]] = 0 
					else:
						#ｷｬﾋﾞﾃｨ外郭(白)
						canvas_pix[xx+offset[0],yy+offset[1]] = src

					canvas_inf[yy+offset[1]][xx+offset[0]] += 1
			else:
				if base == 255:
					#既に画素が存在する
					if src == 0:
						#ﾀﾞﾐｰ領域は無視
						pass
					elif src == 128:
						#内側ﾃﾞｰﾀ
						canvas_pix[xx+offset[0],yy+offset[1]] = 0 
					else:
						#画素(255)あり
						canvas_inf[yy+offset[1]][xx+offset[0]] += 1

def paste_image2(canvas_inf, canvas, src_img, offset, contours):
	u'''ｷｬﾝﾊﾞｽにｷｬﾋﾞﾃｨｲﾒｰｼﾞを張り付ける
		ただし、128に設定された内側ﾃﾞｰﾀは黒(0)に変換する
	'''
	canvas_pix = canvas.load()
	src_pix = src_img.load()
	src_size = src_img.size

	for yy in range(src_size[1]):
		for xx in range(src_size[0]):
			base = canvas_pix[xx+offset[0],yy+offset[1]]
			info = canvas_inf[yy+offset[1]][xx+offset[0]]
			src = src_pix[xx,yy]
			if info == 0:
				#画素は未配置
				if src == 0:
					#回転のためのﾀﾞﾐｰ領域なら
					pass
				else:
					if src == 128:
						#ｷｬﾋﾞﾃｨ内側(ﾊﾟｰﾂ領域)
						canvas_pix[xx+offset[0],yy+offset[1]] = 0 
					else:
						#ｷｬﾋﾞﾃｨ外郭(白)
						canvas_pix[xx+offset[0],yy+offset[1]] = src

					canvas_inf[yy+offset[1]][xx+offset[0]] += 1
			else:
				if base == 255:
					#既に画素が存在する
					if src == 0:
						#ﾀﾞﾐｰ領域は無視
						pass
					elif src == 128:
						#内側ﾃﾞｰﾀ
						canvas_pix[xx+offset[0],yy+offset[1]] = 0 
					else:
						#画素(255)あり
						yp = yy+offset[1]
						xp = xx+offset[0]

						emb = 0
						for con in contours:
							fc = int(cv2.pointPolygonTest(con,(xp,yp),0))
							if fc == 1:
								emb = 1
								break

						if emb == 0:
							canvas_inf[yy+offset[1]][xx+offset[0]] += 1

def get_mount_area(canvas, (x,y)):
	pix = canvas.load()

	#左上
	yy = y
	while( pix[x,yy] <= 128 ):
		yy = yy -1

	yy += 1
	xx = x
	while( pix[xx,yy] <= 128 ):
		xx = xx -1
	xx += 1

	x1 = xx
	y1 = yy

	while( pix[xx,yy] == 128 ):
		xx += 1
	xx -= 1

	while( pix[xx,yy] == 128 ):
		yy += 1
	yy -= 1

	x2 = xx
	y2 = yy

	return  imageUtil.RectObj(x1-1,y1-1,x2,y2)

def get_cavity_area(canvas, (x,y)):
	pix = canvas.load()

	#左上
	yy = y
	while( pix[x,yy] > 0 ):
		yy = yy -1

	yy += 1
	xx = x
	while( pix[xx,yy] > 0 ):
		xx = xx -1
	xx += 1

	x1 = xx
	y1 = yy

	while( pix[xx,yy] == 255 ):
		xx += 1
	xx -= 1

	while( pix[xx,yy] == 255 ):
		yy += 1
	yy -= 1

	x2 = xx
	y2 = yy

	#return (x1,y1,x2,y2)
	return  imageUtil.RectObj(x1-1,y1-1,x2,y2)

def search_cavity_dict(index, cavity_dict, outer_rect, inner_rect):
	for key, val in cavity_dict.items():
		if val[0] == outer_rect and val[1] == inner_rect:
			return key

	return 'cavity_' + str(index)

def create_rect_image(outer_rect, inner_rect):
	u'''矩形ｲﾒｰｼﾞの生成
		outer_rect: 外側のｲﾒｰｼﾞ矩形
		inner_rect: 内側のｲﾒｰｼﾞ矩形
	'''
	outer_size = (int(outer_rect.width()),int(outer_rect.height()) )
	inner_size = (int(inner_rect.width()),int(inner_rect.height()) )

	outer_img = Image.new('L',outer_size,0)
	inner_img = Image.new('L',inner_size,255)

	#canvasの中心に配置
	posx = int( (outer_size[0]-inner_size[0]) / 2)
	posy = int( (outer_size[1]-inner_size[1]) / 2)
	outer_img.paste(inner_img,(posx,posy))

	return outer_img

def create_embedded_image(fileName, cavity_grp, imageSize=(1536,3344)):
	u'''埋め込みﾋﾞｯﾄﾏｯﾌﾟの生成
		  fileName: 画像ﾌｧｲﾙ名
		cavity_grp: {(層数,ﾊﾟｽ数):[outer_rect, inner_rect,実装ﾃﾞｰﾀ,実装ﾃﾞｰﾀ,...], }
	'''
	files = []

	keyList = sorted(cavity_grp.keys(),reverse=True)
	canvas = Image.new('L',imageSize,255)

	for key in keyList:
		cavities = cavity_grp[key]
		for cavity in cavities:
			outer_rect = cavity[0]
			inner_rect = cavity[1]

			cavity_img = create_rect_image(outer_rect,inner_rect)
			canvas.paste(cavity_img,(outer_rect.x1,outer_rect.y1))

		#ﾌｧｲﾙ名
		imageName = mcmUtil.get_job_path() + '\\image\\' + fileName + "-e_" + str( len(files) ) + ".png"
		canvas.save(imageName)
		files += [imageName]

	return files

def create_embedded_image2(fileName, embedded_list, imageSize=(1536,3344)):
	u'''埋め込みﾋﾞｯﾄﾏｯﾌﾟの生成
		     fileName: 画像ﾌｧｲﾙ名
		embedded_list: {(層数,ﾊﾟｽ数):[ [[outerIdx,innerIdx,innerIdx,...],[実装ﾘｽﾄ],層数,ﾊﾟｽ数], ...
	'''
	#白黒反転用のﾙｯｸｱｯﾌﾟﾃｰﾌﾞﾙ
	lookup_tbl = np.ones((256,1),dtype='uint8')
	for i in range(256):
		lookup_tbl[i][0] = 255 - i

	files = []

	keyList = sorted(embedded_list.keys(),reverse=True)
	canvas = Image.new('L',imageSize,0)

	#ﾃﾞｰﾀ合成用情報(ｷｬﾋﾞﾃｨを配置した場所は1を立てる)
	canvas_info = np.array([[0]*canvas.size[0] for i in range(canvas.size[1])])

	for key in keyList:
		embList = embedded_list[key]
		for emb in embList:
			for md in emb[1]:
				emb_img = create_parts_emb_image( md.parts,md.angle)

				#canvas 上でのｷｬﾋﾞﾃｨｲﾒｰｼﾞのﾋﾟｸｾﾙ位置
				partsCenter = mm_to_pix(md.position())

				#貼り付け位置
				pos = (partsCenter[0]-emb_img.size[0]/2+img_pix_offsetX, canvas.size[1]-(partsCenter[1]+emb_img.size[1]/2)+img_pix_offsetY)

				#canvas にｷｬﾋﾞﾃｨｲﾒｰｼﾞを合成
				paste_image(canvas_info, canvas, emb_img,pos)

		#ﾌｧｲﾙ名
		imageName = mcmUtil.get_job_path() + '\\image\\' + fileName + "-e_" + str( len(files) ) + ".png"

		#LUT を使用して白黒反転
		ocv_img = np.asarray(canvas)
		im = cv2.LUT(ocv_img,lookup_tbl)

		#ﾌｧｲﾙ書き出し
		cv2.imwrite(imageName,im)

		files += [imageName]

	return files

def create_glue_image(image_list, imageFileName='glueImage.png', size=(1536,3344)):
	u''' 接着用画像の生成
		ｷｬﾋﾞﾃｨの情報から接着用画像を生成します

		image_list: [外側矩形,内側矩形,層数,ﾊﾟｽ数], ...
	'''
	canvas = Image.new('L',size,255)
	for idx,obj_list in enumerate(image_list):
		rect = obj_list[1]	#内側矩形
		size = (int(rect.width()),int(rect.height()))
		img = Image.new('L',size,0)
		canvas.paste(img,(rect.x1,rect.y1))

	canvas.save(imageFileName)

def create_glue_image2(cavity_list, contours, imageFileName='glueImage.png', size=(1536,3344)):
	u''' 接着用画像の生成
		ｷｬﾋﾞﾃｨの情報から接着用画像を生成します
		cavity_list: [[outerIdx,innerIdx,innerIdx,...],[実装ﾘｽﾄ],層数,ﾊﾟｽ数],[[],,], ...
		   contours: 輪郭情報
	'''
	canvas = Image.new('L',size,255)
	ocv_img = np.asarray(canvas)

	for idx,obj_list in enumerate(cavity_list):
		for obj in obj_list[0][1:]:	#内側の輪郭情報ﾘｽﾄ
			con = contours[obj]
			cv2.fillConvexPoly(ocv_img,con,(0,0,0))	#輪郭の内側を塗りつぶす(四隅が欠けるが問題無い)

	cv2.imwrite(imageFileName,ocv_img)

def create_glue_image3(cavity_list, contours, imageFileName='glueImage.png', size=(1536,3344)):
	u''' 接着用画像の生成
		ｷｬﾋﾞﾃｨの情報から接着用画像を生成します
		cavity_list: [[outerIdx,innerIdx,innerIdx,...],[実装ﾘｽﾄ],層数,ﾊﾟｽ数],[[],,], ...
		   contours: 輪郭情報
	'''
	canvas = Image.new('L',size,255)
	ocv_img = np.asarray(canvas)

	for idx,obj_list in enumerate(cavity_list):
		for obj in obj_list[1:]:	#内側の輪郭情報ﾘｽﾄ
			con = contours[obj]
			cv2.fillConvexPoly(ocv_img,con,(0,0,0))	#輪郭の内側を塗りつぶす(四隅が欠けるが問題無い)

	cv2.imwrite(imageFileName,ocv_img)

def create_embedded_canvas(mount_list,job_parts, imgSize, contours):
	u'''実装ﾃﾞｰﾀを元に埋め込みｲﾒｰｼﾞを生成してcanvasに張り付ける
		mount_list: 実装ﾘｽﾄ
		 job_parts: JOBに定義されたﾊﾟｰﾂ一覧
		   imgSize: 画像ｻｲｽﾞ(xsize,ysize)
		  contours: ｷｬﾋﾞﾃｨの輪郭情報
	'''
	#ｸﾞﾚｰｽｹｰﾙの画像ﾃﾞｰﾀを生成する
	canvas = Image.new('L',imgSize,0)

	#ﾃﾞｰﾀ合成用情報(ｷｬﾋﾞﾃｨを配置した場所は1を立てる)
	canvas_info = np.array([[0]*canvas.size[0] for i in range(canvas.size[1])])

	for md in mount_list:
		parts = filter((lambda x: x.name == md.name),job_parts)
		cavity_img = create_parts_emb_image( parts[0],md.angle)

		#canvas 上でのｷｬﾋﾞﾃｨｲﾒｰｼﾞのﾋﾟｸｾﾙ位置
		partsCenter = mm_to_pix(md.position())

		#貼り付け位置
		pos = (partsCenter[0]-cavity_img.size[0]/2+img_pix_offsetX, canvas.size[1]-(partsCenter[1]+cavity_img.size[1]/2)+img_pix_offsetY)
		#
		#本来はこちらの位置のばすだが、ズレるので
		#pos = (partsCenter[0]-cavity_img.size[0]/2, canvas.size[1]-(partsCenter[1]+cavity_img.size[1]/2))

		#canvas にｷｬﾋﾞﾃｨｲﾒｰｼﾞを合成
		paste_image2(canvas_info, canvas, cavity_img,pos, contours)

	canvas.save("emb_canvas.png")

	#img = np.select([canvas_info>1],[255])
	#pil_im = Image.fromarray(np.uint8(img))
	#pil_im.save("pil.png")

	return canvas

def create_cavity_canvas(mount_list,job_parts, imgSize):
	u'''実装ﾃﾞｰﾀを元にｷｬﾋﾞﾃｨｲﾒｰｼﾞを生成してcanvasに張り付ける
		mount_list: 実装ﾘｽﾄ
		 job_parts: JOBに定義されたﾊﾟｰﾂ一覧
		   imgSize: 画像ｻｲｽﾞ(xsize,ysize)
	'''
	#ｸﾞﾚｰｽｹｰﾙの画像ﾃﾞｰﾀを生成する
	canvas = Image.new('L',imgSize,0)

	#ﾃﾞｰﾀ合成用情報(ｷｬﾋﾞﾃｨを配置した場所は1を立てる)
	canvas_info = np.array([[0]*canvas.size[0] for i in range(canvas.size[1])])

	for md in mount_list:
		parts = filter((lambda x: x.name == md.name),job_parts)
		cavity_img = create_parts_cavity_image( parts[0],md.angle)

		#canvas 上でのｷｬﾋﾞﾃｨｲﾒｰｼﾞのﾋﾟｸｾﾙ位置
		partsCenter = mm_to_pix(md.position())

		#貼り付け位置
		pos = (partsCenter[0]-cavity_img.size[0]/2+img_pix_offsetX, canvas.size[1]-(partsCenter[1]+cavity_img.size[1]/2)+img_pix_offsetY)
		#
		#本来はこちらの位置のばすだが、ズレるので
		#pos = (partsCenter[0]-cavity_img.size[0]/2, canvas.size[1]-(partsCenter[1]+cavity_img.size[1]/2))

		#canvas にｷｬﾋﾞﾃｨｲﾒｰｼﾞを合成
		paste_image(canvas_info, canvas, cavity_img,pos)	

	canvas.save("cvty_canvas.png")

	return canvas

def link_cavity_parts(canvas, mount_list, job_parts):
	u'''ﾊﾟｰﾂの実装位置からｷｬﾋﾞﾃｨｻｲｽﾞを画像より検索してｷｬﾋﾞﾃｨと実装ﾃﾞｰﾀを関連づける
		    canvas: ｷｬﾋﾞﾃｨ画像が配置された画像
		mount_list: 実装ﾘｽﾄ
		 job_parts: JOBに定義されたﾊﾟｰﾂﾘｽﾄ

		戻り値のﾃﾞｰﾀ形式
		{'cavity_0':[outer_rect, inner_rect, parts,parts,parts,....]}
	'''
	cavity_dict = {}

	for idx,md in enumerate(mount_list):
		parts = filter((lambda x: x.name == md.name),job_parts)
		#canvas 上でのｷｬﾋﾞﾃｨｲﾒｰｼﾞのﾋﾟｸｾﾙ位置
		partsCenter = mm_to_pix(md.position())
		pos = (partsCenter[0], canvas.size[1]-partsCenter[1])

		#画像を検索してｷｬﾋﾞﾃｨの位置を得る
		outer_rect = get_cavity_area(canvas,pos)
		inner_rect = get_mount_area(canvas,pos)

		cavityName = search_cavity_dict(idx,cavity_dict,outer_rect,inner_rect)

		md.parts = parts[0]	#実装ﾃﾞｰﾀとﾊﾟｰﾂﾃﾞｰﾀを関連付け

		if cavity_dict.has_key(cavityName) == True:
			#同じｷｬﾋﾞﾃｨの場合はﾊﾟｰﾂのみ追加する
			cavity_dict[cavityName].append(md)
		else:
			cavity_dict[cavityName] = [outer_rect,inner_rect,md]

	return cavity_dict	

def search_cavity_dict2(index, cavity_dict, chIdx):
	for key, val in cavity_dict.items():
		cvty_list = val[0]
		if chIdx in cvty_list[1:]:
			return key

	return 'cavity_' + str(index)

def search_cavity_dict3(index, cavity_dict, chIdx):
	for key, val in cavity_dict.items():
		cvty_list = val[0]
		if chIdx in cvty_list[0:]:
			return key

	return 'cavity_' + str(index)

def link_cavity_parts2(ocv_img, mount_list,job_parts, cvty_list, contours):
	u'''ﾊﾟｰﾂの実装位置からｷｬﾋﾞﾃｨｻｲｽﾞを画像より検索してｷｬﾋﾞﾃｨと実装ﾃﾞｰﾀを関連づける
		   ocv_img: ｷｬﾋﾞﾃｨ画像が配置された画像(openCv形式)
		mount_list: 実装ﾘｽﾄ
		 job_parts: JOBに定義されたﾊﾟｰﾂﾘｽﾄ
		 cvty_list: ｷｬﾋﾞﾃｨの親子関係ﾘｽﾄ (cavity_group 参照)
		  contours: openCv で取得した輪郭座標ﾃﾞｰﾀ
		戻り値のﾃﾞｰﾀ形式
		{'cavity_0':[[cavity_list], parts,parts,parts,....]}
	'''
	cavity_dict = {}

	index = 0
	for idx,md in enumerate(mount_list):
		parts = filter((lambda x: x.name == md.name),job_parts)
		#canvas 上でのｷｬﾋﾞﾃｨｲﾒｰｼﾞのﾋﾟｸｾﾙ位置
		partsCenter = mm_to_pix(md.position())
		pos = (partsCenter[0], ocv_img.shape[0]-partsCenter[1])
		#x = pos[0] -2 + img_pix_offsetX
		#y = pos[1] -2 + img_pix_offsetY
		#cv2.rectangle(ocv_img,(x,y),(x+2,y+2),(255,255,0),2)

		for cvty in cvty_list:
			for ch in cvty[1:]:
				con = contours[ch]
				fc = int(cv2.pointPolygonTest(con,(pos[0],pos[1]),0))
				if fc == 1:
					cavityName = search_cavity_dict2(index,cavity_dict,ch)

					md.parts = parts[0]	#実装ﾃﾞｰﾀとﾊﾟｰﾂﾃﾞｰﾀを関連付け

					if cavity_dict.has_key(cavityName) == True:
						cavity_dict[cavityName].append(md)
					else:
						cavity_dict[cavityName] = [cvty,md]
						index += 1

	#cv2.imwrite('vv.png',ocv_img)
	return cavity_dict

def link_cavity_parts3(ocv_img, mount_list,job_parts, contours):
	u'''ﾊﾟｰﾂの実装位置からｷｬﾋﾞﾃｨｻｲｽﾞを画像より検索してｷｬﾋﾞﾃｨと実装ﾃﾞｰﾀを関連づける
		   ocv_img: ｷｬﾋﾞﾃｨ画像が配置された画像(openCv形式)
		mount_list: 実装ﾘｽﾄ
		 job_parts: JOBに定義されたﾊﾟｰﾂﾘｽﾄ
		  contours: openCv で取得した輪郭座標ﾃﾞｰﾀ
		戻り値のﾃﾞｰﾀ形式
		{'cavity_0':[[cavity_list], parts,parts,parts,....]}
	'''
	cavity_dict = {}

	index = 0
	for idx,md in enumerate(mount_list):
		parts = filter((lambda x: x.name == md.name),job_parts)
		#canvas 上でのｷｬﾋﾞﾃｨｲﾒｰｼﾞのﾋﾟｸｾﾙ位置
		partsCenter = mm_to_pix(md.position())
		pos = (partsCenter[0], ocv_img.shape[0]-partsCenter[1])
		#x = pos[0] -2 + img_pix_offsetX
		#y = pos[1] -2 + img_pix_offsetY
		#cv2.rectangle(ocv_img,(x,y),(x+2,y+2),(255,255,0),2)

		for num,con in enumerate(contours):
			fc = int(cv2.pointPolygonTest(con,(pos[0],pos[1]),0))
			if fc == 1:
				cavityName = search_cavity_dict3(index,cavity_dict,num)

				md.parts = parts[0]	#実装ﾃﾞｰﾀとﾊﾟｰﾂﾃﾞｰﾀを関連付け

				if cavity_dict.has_key(cavityName) == True:
					cavity_dict[cavityName].append(md)
				else:
					cavity_dict[cavityName] = [[num],md]
					index += 1

	#cv2.imwrite('vv.png',ocv_img)
	return cavity_dict

def calc_cavity_path(cavity_dict):
	u''' 各ｷｬﾋﾞﾃｨに実装するﾊﾟｰﾂから埋め込みの層数とﾊﾟｽ数を計算する
		cavity_dict: ｷｬﾋﾞﾃｨの矩形とｷｬﾋﾞﾃｨに埋め込むﾊﾟｰﾂのﾘｽﾄ
			<ﾃﾞｰﾀ形式>
				{"cavity_name":側側矩形,内側矩形,埋め込み情報,埋め込み情報,.....}

		<ﾘﾀｰﾝﾃﾞｰﾀ:ﾘｽﾄ>
			[外側矩形,内側矩形,層数,ﾊﾟｽ数],[...],[...], ｷｬﾋﾞﾃｨの数だけ
	'''
	cavity_list = []

	#ｷｬﾋﾞﾃｨとｷｬﾋﾞﾃｨに実装するﾊﾟｰﾂから埋め込み層数を計算
	for val in cavity_dict.values():
		mnt_list = val[2:]

		if len(mnt_list) > 1:
			#一つのｷｬﾋﾞﾃｨに複数のﾊﾟｰﾂを実装する場合
			virParts = create_multi_parts(mnt_list)
			printQty = embedded_print_qty(virParts)
			printPath = embedded_print_path(virParts)
		else:
			#一つのｷｬﾋﾞﾃｨに一つのﾊﾟｰﾂ
			printQty = embedded_print_qty(mnt_list[0].parts)
			printPath = embedded_print_path(mnt_list[0].parts)

		###                 [outer,  inner,  層数,   ﾊﾟｽ数]
		cavity_list.append( [val[0],val[1],printQty,printPath] )

	#層数の多い順、ﾊﾟｽ数の多い順にｿｰﾄする
	cavity_list.sort(key=lambda x:(x[2],x[3]),reverse=True )

	return cavity_list

def cavity_capa(canvas, con):
	u''' 画像ﾃﾞｰﾀから目的の外接矩形を切り出して白・黒のﾋﾟｸｾﾙを数える
		canvas: 画像ﾃﾞｰﾀ(Pillow)
		   con: 輪郭ﾃﾞｰﾀ
	'''
	#外接矩形で画像を切り出す
	x,y,w,h = cv2.boundingRect(con)
	cvs = canvas.crop((x,y,x+w,y+h))

	pix = cvs.load()
	#255(白)のﾋﾟｸｾﾙ数と0(黒)(ただし、輪郭内)の数を数える
	wcnt = 0
	bcnt = 0
	for yy in range(h):
		for xx in range(w):
			col = pix[xx,yy]
			if col == 255:
				wcnt += 1
			else:
				#黒である場合は輪郭内かどうか(輪郭内:1 外:-1 上:0)
				ff = int(cv2.pointPolygonTest(con,(x+xx,y+yy),0))
				if ff == 1:
					bcnt += 1

	return wcnt, bcnt

def calc_cavity_path2(cavity_dict, contours, canvas, emb_canvas):
	u''' 各ｷｬﾋﾞﾃｨに実装するﾊﾟｰﾂから埋め込みの層数とﾊﾟｽ数を計算する
		cavity_dict: ｷｬﾋﾞﾃｨの矩形とｷｬﾋﾞﾃｨに埋め込むﾊﾟｰﾂのﾘｽﾄ
			<ﾃﾞｰﾀ形式>
				{"cavity_name":[outerIdx,innerIdx,innerIdx],埋め込み情報,埋め込み情報,.....}
		   contours: 輪郭情報
		     canvas: 画像ﾃﾞｰﾀ(Pillow)

		<ﾘﾀｰﾝﾃﾞｰﾀ:ﾘｽﾄ>
			[[outerIdx,innerIdx,innerIdx,...],[実装ﾃﾞｰﾀﾘｽﾄ],層数,ﾊﾟｽ数]],[...],[...], ｷｬﾋﾞﾃｨの数だけ
	'''

	#埋め込みの輪郭抽出
	#openCv 形式のﾃﾞｰﾀへ
	ocv_img = np.asarray(emb_canvas)
	cont,hierarchy = cv2.findContours(ocv_img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

	cavity_list = []

	#ｷｬﾋﾞﾃｨとｷｬﾋﾞﾃｨに実装するﾊﾟｰﾂから埋め込み層数を計算
	for val in cavity_dict.values():
		mnt_list = val[1:]	#埋め込み情報ﾘｽﾄ

		if len(mnt_list) > 1:
			#一つのｷｬﾋﾞﾃｨに複数のﾊﾟｰﾂを実装する場合
			con = contours[ val[0][0] ]

			#ｷｬﾋﾞﾃｨﾋﾞｯﾄﾏｯﾌﾟのﾋﾟｸｾﾙ数
			wpix,bpix = cavity_capa(canvas,con)

			#ﾊﾟｰﾂ体積(mm^3) [同一ｷｬﾋﾞﾃｨに実装するﾊﾟｰﾂの体積の合計]
			Vp = get_parts_capa(mnt_list)

			#ｷｬﾋﾞﾃｨ全体の埋め込み体積(pl)
			q = struct_layer_qty(mnt_list[0].parts)
			V1 = (wpix + bpix) * struct_layer_qty(mnt_list[0].parts) * 2.5 * resin_dot_qty

			#ｷｬﾋﾞﾃｨの深さ = ｷｬﾋﾞﾃｨの構造材積層数 * 構造材1層あたりの厚み
			cvty_height = struct_layer_qty(mnt_list[0].parts) * resin_thickness()

			#       ((ｷｬﾋﾞﾃｨの深さ - ﾊﾟｰﾂ高さ) * 吐出量) / 構造材1層あたりの厚み
			top_ratio = ((cvty_height - mnt_list[0].parts.height) * resin_dot_qty) / resin_thickness()

			#埋め込みﾋﾞｯﾄﾏｯﾌﾟのﾋﾟｸｾﾙ数
			wpix2,bpix2 = cavity_capa(emb_canvas,cont[val[0][0]])

			#埋め込み傾斜部の体積
			V2 = (wpix + bpix + bpix) / 2.0 * 2.5 * top_ratio * resin_ratio

			S1 = V1 - (Vp * 1000000.0)
			#埋め込みｼｮｯﾄ数
			S = (V1 - (Vp * 1000000.0) - V2) / (resin_dot_qty * resin_ratio)

			#ﾊﾟｽ数
			P = int(S / (wpix2 / resin_img_block))

			printQty = int(P /40)
			printPath = P - (printQty * 40)

			# 旧方式、同一ｷｬﾋﾞﾃｨに実装する複数のﾊﾟｰﾂを大きな一つとﾊﾟｰﾂとみなす、ｷｬﾋﾞﾃｨ形状が矩形限定
			#virParts = create_multi_parts(mnt_list)
			#printQty = embedded_print_qty(virParts)
			#printPath = embedded_print_path(virParts)
		else:
			#一つのｷｬﾋﾞﾃｨに一つのﾊﾟｰﾂ
			printQty = embedded_print_qty(mnt_list[0].parts)
			printPath = embedded_print_path(mnt_list[0].parts)

		###    [[outer,inner,inner,...],  実装ﾘｽﾄ, 層数,   ﾊﾟｽ数]
		cavity_list.append( [val[0],mnt_list,printQty,printPath] )

	#層数の多い順、ﾊﾟｽ数の多い順にｿｰﾄする
	cavity_list.sort(key=lambda x:(x[2],x[3]),reverse=True )

	return cavity_list

def create_cmd_list(cavity_grp, cureLayer=4):
	u'''ｷｬﾋﾞﾃｨ情報からｺﾏﾝﾄﾞ生成用りﾘｽﾄを生成する
		cavity_grp : ｷｬﾋﾞﾃｨ辞書
				{(層,ﾊﾟｽ):[[(外側矩形,内側矩形,層数,ﾊﾟｽ数),(外側矩形,内側矩形,層数,ﾊﾟｽ数), ...]],}
		   cureLayer: 何層毎に硬化をいれるか(ﾃﾞﾌｫﾙﾄ=4)

		<戻り値:ﾘｽﾄ>
			[0,0,0,0, ..., 'C',1,1,1,2,2,'C',3,3,3,'C']
			 数値:埋め込みｲﾒｰｼﾞ番号
			  'C':硬化ｺﾏﾝﾄﾞ
	'''
	#cmd_list = []

	# cavity_dict の ｷｰは(層数,ﾊﾟｽ数)
	#   (層数,ﾊﾟｽ数)で降順ｿｰﾄしたﾘｽﾄを得る
	keyList = sorted(cavity_grp.keys(),reverse=True)

	#最大印刷ﾊﾟｽ = (最大層数       *    40      + ﾊﾟｽ数)
	totalPath = (keyList[0][0] * resin_path + keyList[0][1])

	cmd_list = [[nn,0] for nn in range(keyList[0][1])]
	for nn in range(keyList[0][0]):
		cmd_list += [[nn,0] for nn in range(len(image_table))]
		cmd_list += [[nn,0] for nn in range(len(image_table))]
		cmd_list += [[nn,0] for nn in range(len(image_table)/2)]

	curePath = cureLayer * resin_path	#何パス毎に硬化するか
	cureCount = totalPath / curePath	#硬化回数
	firstCure = totalPath % curePath	# 最大ﾊﾟｽ数を硬化毎で割った余りが最初の硬化
	cmd_cure = 0

	if firstCure != 0:
		#余りの硬化がある場合
		cmd_cure = 1

	#全部で必要なprintｺﾏﾝﾄﾞの数
	cmd_count = totalPath + cureCount + cmd_cure

	#ｺﾏﾝﾄﾞﾘｽﾄを生成する
	# 数値=ｲﾒｰｼﾞ番号(0～)
	# 'C' = 硬化ｺﾏﾝﾄﾞ
	cavityCount = len(cavity_grp)

	startIdx = 0
	for nn in range(cavityCount-1):
		qty1,path1 = keyList[nn+0]
		qty2,path2 = keyList[nn+1]

		#総ﾊﾟｽ数の差分
		#        (層数 *    40      + ﾊﾟｽ数)
		curCnt = (qty1 * resin_path + path1)
		nxtCnt = (qty2 * resin_path + path2)
		cnt = curCnt - nxtCnt

		#ﾘｽﾄ生成と追加
		#cmd_list += ([nn] * cnt)	## ex.) ([1] * 3) ===> [1,1,1] の生成
		#ｲﾒｰｼﾞﾌｧｲﾙｲﾝﾃﾞｯｸｽ設定
		for idx in range(startIdx,cnt+startIdx):
			cmd_list[idx][1] = nn

		startIdx += cnt

	#最後のｷｬﾋﾞﾃｨｲﾒｰｼﾞ用
	for nn in range(startIdx,len(cmd_list)):
		cmd_list[nn][1] = cavityCount -1

	if firstCure != 0:
		#最初の硬化ｺﾏﾝﾄﾞを追加
		cmd_list.insert(firstCure,['C',0])

	#層毎の硬化ｺﾏﾝﾄﾞを追加
	for n in range(cureCount):
		cmd_list.insert(firstCure+curePath*(n+1)+(n+1),['C',0])

	return cmd_list	

def group_cavity_path(cavity_list):
	u'''層数とパス数が同じｷｬﾋﾞﾃｨをｸﾞﾙｰﾌﾟ化
		<ﾃﾞｰﾀ形式>
			[外側矩形,内側矩形,層数,ﾊﾟｽ数]
	'''
	#層数とパス数が同じものをｸﾞﾙｰﾌﾟ化した辞書を生成
	# {(層数,ﾊﾟｽ数):[ [cavity_list],[cavity_list] ],}
	dic = {k:list(g) for k, g in groupby(cavity_list, key=lambda x: (x[2],x[3]))}

	retDic = {}
	for kk in sorted(dic.keys(), reverse=True):
		retDic[kk] = dic[kk]

	for key, val in retDic.items():
		print key
		for vv in val:
			print vv

def get_child(idx, hierarchy):
	lst = [idx]
	nn = hierarchy[idx][0]
	if hierarchy[idx][0] != -1:
		return lst + get_child(nn,hierarchy)

	return lst

def cavity_group(hierarchy):
	'''ｷｬﾋﾞﾃｨの親子関係をﾘｽﾄ化する
		return: ｲﾝﾃﾞｯｸｽ・ﾘｽﾄ
			[
				[(最外形)RootNo, ChildNo1, ChildNo2, ChildNo3,...]
				[(最外形)RootNo, ChildNo1, ChildNo2, ChildNo3,...],
			]	
	'''
	grp = []

	hi = hierarchy[0]
	for idx,hh in enumerate(hi):
		Child = hh[2]
		if Child != -1:
			chList = [idx] + get_child(Child,hi)
			grp.append(chList)

	return grp

####################################
#
# ｴﾚﾒﾝﾄ出力用
#
def glue_print_command(layerNo, subNo, materialName, originZ, pathCnt=2):
	u''' 接着剤塗布用ｺﾏﾝﾄﾞ
		layerNo:ﾚｲﾔｰ番号
		subNo: ﾚｲﾔｰｻﾌﾞ番号
		materialName: ﾏﾃﾘｱﾙ名
		originZ: Z基準位置
		pathCnt: 接着印刷の回数(ﾃﾞﾌｫﾙﾄ=2)
	'''
	elm_list = []

	if pathCnt < 1 or pathCnt > len(image_table):
		#印刷回数が0 または ｲﾒｰｼﾞﾃｰﾌﾞﾙ(16個)より多い
		return elm_list

	#ﾃﾞﾌｫﾙﾄﾊﾟﾗﾒｰﾀ
	params = {'layerNo':layerNo, 'materialName':materialName,'rollerMode':0, 'layerType':0}

	for (i,layer) in enumerate(image_table[0:pathCnt]):
		pos = layer[0]
		idx = layer[1]

		#分割されたｲﾒｰｼﾞﾌｧｲﾙ名
		img_file = 'image/glueImage_M0101_B' + '{0:02d}{1:02d}'.format(idx[0],idx[1]) + '.png' 

		#ﾊﾟﾗﾒｰﾀ設定
		params.update({'printImage':img_file})
		params.update({'layerSubNo':subNo + i + 1})
		params.update({'imageOriginX':pos[0], 'imageOriginY':pos[1], 'imageOriginZ':pos[2] + originZ})
		params.update({'offsetX':0, 'offsetY':0, 'offsetZ':0})
		params.update({'printMode':1,'printSpeed':500})
		params.update({'curingMode':0,'curingSpeed':0,'curingCount':0})

		#印刷
		elm_list.append( jobUtil.print_command(params) )

	return elm_list

def parts_mount_command(layerNo, mount_list, ofstX=0.0, ofstY=0.0):
	u'''実装ｺﾏﾝﾄﾞの生成
	'''

	elm_list =[]

	#ﾃﾞﾌｫﾙﾄﾊﾟﾗﾒｰﾀ
	params = {'layerNo':layerNo, 'direction':0 }

	for idx,md in enumerate(mount_list):
		params.update({'partName':md.name,'x':md.xPos+ofstX,'y':md.yPos+ofstY,'z':md.zPos,'angle':md.angle,'direction':0})

		#印刷
		elm_list.append( jobUtil.mount_command(params) )

	return elm_list

def curing_command(layerNo, subNo, materialName, imageFile, originZ, capping=0):
	u'''硬化用印刷(print)ｺﾏﾝﾄﾞ生成
	'''	
	elm_list = []

	#ﾃﾞﾌｫﾙﾄﾊﾟﾗﾒｰﾀ
	params = {'layerNo':layerNo, 'layerSubNo':subNo,'layerType':0,'materialName':materialName,'printMode':0 }

	params.update({'printImage':imageFile})
	params.update({'imageOriginX':0.0, 'imageOriginY':0.0, 'imageOriginZ':originZ})
	params.update({'printSpeed':500,'rollerMode':0,'curingMode':3,'curingSpeed':50,'curingCount':8})

	#印刷
	elm_list.append( jobUtil.print_command(params) )

	#maintenamceCommand
	params = {'target':0, 'purgeTime':800,'wipingMode':1,'flushCount':100,'cappingMode':capping}
	elm_list.append( jobUtil.maintenance_command(params) )

	return elm_list

def maintenance_command():
	elm_list = []

	params = {'target':0, 'purgeTime':800,'wipingMode':1,'flushCount':100,'cappingMode':1}
	elm_list.append( jobUtil.maintenance_command(params) )

	return elm_list

def emb_layer_print(layerNo, subNo, materialName, imageFile, originZ, idx):
	u"""印刷ｺﾏﾝﾄﾞ
		layerNo     : layer番号
		subNo       : layerSubNo 開始番号
		materialName: ﾏﾃﾘｱﾙ名
		imageFile   : ｲﾒｰｼﾞﾌｧｲﾙ
		originZ     : Z基準位置
		idx         : ｲﾒｰｼﾞﾃｰﾌﾞﾙの使用位置

		return : XML 文字列ﾘｽﾄ
			例) ['<AAA>123</AAA>','<BBB>0123</BBB>']
	"""

	elm_list = []

	#ｲﾒｰｼﾞﾌｧｲﾙ名をﾌｧｲﾙ名と拡張子に分割
	img_name,ext = os.path.splitext( os.path.basename(imageFile) )	

	layer = image_table[idx]

	pos = layer[0]
	idx = layer[1]

	#ﾃﾞﾌｫﾙﾄﾊﾟﾗﾒｰﾀ
	params = {'layerNo':layerNo, 'layerSubNo':subNo,'materialName':materialName,'rollerMode':0, 'layerType':0}

	#分割されたｲﾒｰｼﾞﾌｧｲﾙ名
	img_file = 'image/' + img_name + '_M0101_B' + '{0:02d}{1:02d}'.format(idx[0],idx[1]) + ext

	#ﾊﾟﾗﾒｰﾀ設定
	params.update({'printImage':img_file})
	params.update({'imageOriginX':pos[0], 'imageOriginY':pos[1], 'imageOriginZ':pos[2] + originZ})
	params.update({'offsetX':0, 'offsetY':0, 'offsetZ':0})
	params.update({'printMode':1,'printSpeed':500})
	params.update({'curingMode':0,'curingSpeed':0,'curingCount':0})

	#印刷ｺﾏﾝﾄﾞ
	elm_list.append( jobUtil.print_command(params) )

	return elm_list

def create_job_element(layerNo, subNo, imageFile, materialName, originZ, cmd_list, mount_list):
	u'''JOB出力用ﾃﾞｰﾀの生成(XML文字列のﾘｽﾄ)
		cmd_list: [(image_table No,imageFileNo), ...]
	'''
	elm_list = []

	#JOBからｵﾌｾｯﾄ値を読み込む
	ofstX = float(mcmUtil.get_job_data('instrumentGroup/framePrinter/offsetX'))
	ofstY = float(mcmUtil.get_job_data('instrumentGroup/framePrinter/offsetY'))

	#ｲﾒｰｼﾞﾌｧｲﾙ名をﾌｧｲﾙ名と拡張子に分割
	img_name,ext = os.path.splitext( os.path.basename(imageFile) )

	#接着ｺﾏﾝﾄﾞ
	elm_list.extend( glue_print_command(layerNo,0,materialName,originZ) )

	#部品実装ｺﾏﾝﾄﾞ前にはﾒﾝﾃﾅﾝｽｺﾏﾝﾄﾞを実行する
	elm_list.extend( maintenance_command() )

	#実装ｺﾏﾝﾄﾞ(実装ﾃﾞｰﾀにはｵﾌｾｯﾄが加算済みなので)
	elm_list.extend( parts_mount_command(layerNo, mount_list,ofstX,ofstY) )

	#実装後の硬化(硬化用のｲﾒｰｼﾞは接着用のｲﾒｰｼﾞを流用。実際には使用しないのでﾀﾞﾐｰ定義)
	elm_list.extend( curing_command(layerNo, subNo, materialName, "image/glueImage_M0101_B0101.png", originZ) )

	#余り乾燥
	first = (len(cmd_list) - len( filter(lambda arg: arg[0] == 'C',cmd_list))) % 40

	#ｺﾏﾝﾄﾞﾘｽﾄの展開(※最終ｺﾏﾝﾄﾞは「硬化」のはず)
	sub = 1
	imgNo = 0
	layerOffset = 0
	printNo = 0
	for imgIdx,fileNo in cmd_list[0:-1]:
		if isinstance(imgIdx,str) == True:
			#硬化ｺﾏﾝﾄ
			elm_list.extend(['<comment>___________________UV___________________________________________________</comment>'])
			elm_list.extend( curing_command(layerNo, 1, materialName, "image/glueImage_M0101_B0101.png", originZ) )
		else:
			if imgNo != fileNo:
				#ｲﾒｰｼﾞ番号が変わった
				imgNo = fileNo
				elm_list.extend(['<comment>_ImageChange_#######################################################</comment>'])

			imageFile = img_name + "-e_" + str(fileNo) + ".png"
			elm_list.extend( emb_layer_print(layerNo, sub, materialName, imageFile, originZ,imgIdx ) )
			printNo += 1
			sub += 1
			if sub > 40:
				sub = 1
				layerOffset += 1
				elm_list.extend(['<comment>_LAYER_*************************************************************_</comment>'])

		if printNo == first:
			sub = 1

	#最終硬化(最終硬化のみはｷｬｯﾋﾟﾝｸﾞを1にする)
	elm_list.extend( curing_command(layerNo, 1, materialName, "image/glueImage_M0101_B0101.png", originZ,capping=1) )

	return elm_list

####################################
#
# 埋め込みﾗｲﾌﾞﾗﾘ
#
#   ※mcmUtil ﾓｼﾞｭｰﾙは予め初期化(init)が必要だが、通常は jobConv 内で実施ずみ
#
def embedded(layerNo, imageFile, mountFile, layerName, materialName, originZ, cureLayer=4, blockX=4, blockY=4):
	u'''埋め込みｱﾙｺﾞﾘｽﾞﾑ
		     layerNo: ﾚｲﾔｰ番号
		   imageFile: ｷｬﾋﾞﾃｨ画像ﾌｧｲﾙ
		   mountFile: 実装ﾃﾞｰﾀﾌｧｲﾙ
		   layerName: 実装ﾃﾞｰﾀﾌｧｲﾙに定義されたﾚｲﾔｰ名
		materialName: ﾏﾃﾘｱﾙ名
		   cureLayer: 層毎の硬化(=4 の場合4層毎に硬化処理)
		      blockX: X方向分割数
		      blockY: Y方向分割数
	'''
	#JOBからｵﾌｾｯﾄ値を読み込む
	ofstX = float(mcmUtil.get_job_data('instrumentGroup/framePrinter/offsetX'))
	ofstY = float(mcmUtil.get_job_data('instrumentGroup/framePrinter/offsetY'))

	#ｲﾒｰｼﾞﾌｧｲﾙ名をﾌｧｲﾙ名と拡張子に分割
	img_name,ext = os.path.splitext( os.path.basename(imageFile) )

	#ｲﾒｰｼﾞﾌｧｲﾙを開いてｻｲｽﾞを取得
	imf = Image.open( mcmUtil.get_job_path() + '\\' + imageFile )
	imageSize = imf.size
	imf.close()

	#JOBﾌｧｲﾙからﾊﾟｰﾂﾘｽﾄを作成
	job_parts = jobUtil.create_parts_list()

	#実装ﾃﾞｰﾀﾌｧｲﾙより実装ﾘｽﾄを作成(実装ﾘｽﾄはJOBﾌｫﾙﾀﾞ下のpartsにある事)
	mntFile = mcmUtil.get_job_path() + '\\' + mountFile
	mountList = jobUtil.create_mount_list(mntFile,ofstX,ofstY)

	#実装ﾃﾞｰﾀより実装するﾚｲﾔｰの部品ﾘｽﾄを得る
	mount_data = mountList[layerName]

	#ﾊﾟｰﾂに印刷層数とﾊﾟｽ数をｾｯﾄする
	for parts in job_parts:
		layerQty = embedded_print_qty(parts)	#埋め込み印刷層数
		pathQty = embedded_print_path(parts)	#印刷ﾊﾟｽ数
		parts.set_print_count(layerQty,pathQty)

		#実装ﾃﾞｰﾀ側にも印刷層数とﾊﾟｽ数をｾｯﾄしておく	
		md = filter((lambda x: x.name == parts.name),mount_data)
		for mm in md:
			mm.set_print_count(layerQty,pathQty)

	#埋め込むﾊﾟｰﾂがJOBに定義されているか
	if exist_parts(job_parts,mount_data) == False:
		return []

	#印刷層数・ﾊﾟｽ数の多い順にｿｰﾄしてﾘｽﾄにする
	mount_list = sorted(mount_data,key=lambda arg: filter((lambda x:x.name == arg.name),job_parts)[0].get_print_count(),reverse=True)

	#canvas(ｷｬﾋﾞﾃｨｲﾒｰｼﾞと同ｻｲｽﾞ) 上に全ｷｬﾋﾞﾃｨを配置
	cvt_canvas = create_cavity_canvas(mount_list,job_parts, imageSize) 

	#openCv 形式のﾃﾞｰﾀへ
	ocv_img = np.asarray(cvt_canvas)

	#ｷｬﾋﾞﾃｨの輪郭抽出
	#contours,hierarchy = cv2.findContours(ocv_img,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
	contours,hierarchy = cv2.findContours(ocv_img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

	#親子関係を含めた輪郭
	cont2,hi2 = cv2.findContours(ocv_img,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)

	#輪郭を親子で分類(※RETR_CCOMP ﾓｰﾄﾞでない場合は無意味=>親子関係を検知しないので)
	cvty_list = cavity_group(hierarchy)
	cvty_list2 = cavity_group(hi2)

	#埋め込みｲﾒｰｼﾞをcanvasに配置
	emb_canvas = create_embedded_canvas(mount_list,job_parts, imageSize, contours) 

	#ﾊﾟｰﾂの実装位置からｷｬﾋﾞﾃｨｻｲｽﾞを画像より検索してｷｬﾋﾞﾃｨと実装ﾃﾞｰﾀを関連づける
	#cavity_dict = link_cavity_parts(canvas,mount_list,job_parts)
	#cavity_dict = link_cavity_parts2(ocv_img,mount_list,job_parts,cvty_list,contours)
	cavity_dict = link_cavity_parts3(ocv_img,mount_list,job_parts,contours)

	#ｷｬﾋﾞﾃｨとｷｬﾋﾞﾃｨに実装するﾊﾟｰﾂから埋め込み層数を計算
	# ﾘﾀｰﾝ形式: [[outerIdx,innerIdx,innerIdx,...],[実装ﾃﾞｰﾀﾘｽﾄ],層数,ﾊﾟｽ数]]
	cavity_list = calc_cavity_path2(cavity_dict,contours,cvt_canvas, emb_canvas) 

	#層数とパス数が同じものをｸﾞﾙｰﾌﾟ化した辞書を生成
	# {(層数,ﾊﾟｽ数):[ [cavity_list],[cavity_list] ],}
	cavity_grp = {k:list(g) for k, g in groupby(cavity_list, key=lambda x: (x[2],x[3]))}

	#埋め込みｺﾏﾝﾄﾞﾘｽﾄの生成
	cmd_list = create_cmd_list(cavity_grp,cureLayer)

	#接着ﾌｧｲﾙの生成(接着用ｲﾒｰｼﾞ名は glueImage.png)
	glueImageName = mcmUtil.get_job_path() + '\\image\\glueImage.png' 
	#create_glue_image(cavity_list,glueImageName,imageSize)
	#create_glue_image2(cavity_list,contours,glueImageName,imageSize)
	create_glue_image3(cvty_list2,cont2,glueImageName,imageSize)

	#接着画像を分割
	glue_files = jobUtil.split_image(blockX,blockY,glueImageName)

	#埋め込みﾒｰｼﾞﾌｧｲﾙの生成
	#files = create_embedded_image(img_name,cavity_grp,imageSize)
	files = create_embedded_image2(img_name,cavity_grp,imageSize)

	#埋め込みｲﾒｰｼﾞを指定ﾌﾞﾛｯｸ数で画像分割
	imgFiles = []
	for idx,file in enumerate(files):
		imgFiles += jobUtil.split_image(blockX,blockY,file)

	#JOB出力ﾃﾞｰﾀの生成
	elm_list = create_job_element(layerNo, 1, imageFile, materialName, originZ, cmd_list, mount_list)

	return elm_list

def calc_test(obj):

	print 'parts_capacity={0}'.format(parts_capacity(obj))
	print 'resin_thickness={0}'.format(resin_thickness())
	print 'struct_layer_qty={0}'.format(struct_layer_qty(obj))

	#ｷｬﾋﾞﾃｨ・ﾏｰｼﾞﾝ
	d = cavity_margin(obj)
	print 'cavity_margin=({0},{1})'.format(d[0],d[1])

	#ｷｬﾋﾞﾃｨｴﾘｱの大きさ
	d = cavity_size(obj)
	print 'cavity_size=({0},{1})'.format(d[0],d[1])

	#ｷｬﾋﾞﾃｨｴﾘｱ・ﾄﾞｯﾄ数
	d = cavity_dot(obj)
	print 'cavity_dot=({0},{1})'.format(d[0],d[1])

	#ｷｬﾋﾞﾃｨ容積
	d = cavity_capacity(obj)
	print 'cavity_capacity={0}'.format(d)

	#部品堆積
	print 'parts_capacity={0}'.format(parts_capacity(obj))

	#構造材1ﾄﾞｯﾄ飛翔径
	print u'構造材1ﾄﾞｯﾄ飛翔径={0}'.format(dot_r())

	#埋め込みｴﾘｱ外側の大きさ
	d = outer_embedded_size(obj)
	print u'埋め込みｴﾘｱ外側の大きさ=({0},{1})'.format(d[0],d[1])

	#埋め込みｴﾘｱ外側の大きさﾄﾞｯﾄ数
	d = outer_embedded_dot(obj)
	print u'埋め込みｴﾘｱ外側の大きさﾄﾞｯﾄ数=({0},{1})'.format(d[0],d[1])

	#埋め込みｴﾘｱ内側の大きさ
	d = inner_embedded_size(obj)
	print u'埋め込みｴﾘｱ内側の大きさ=({0},{1})'.format(d[0],d[1])

	#埋め込みｴﾘｱ内側の大きさﾄﾞｯﾄ数
	d = inner_embedded_dot(obj)
	print u'埋め込みｴﾘｱ内外側の大きさﾄﾞｯﾄ数=({0},{1})'.format(d[0],d[1])

	#埋め込み傾斜部の体積
	print u'埋め込み傾斜部の体積={0}'.format(embedded_slope_capacity(obj))

	#埋め込み印刷層数
	print u'埋め込み印刷層数={0}'.format(embedded_print_qty(obj))

	#埋め込み残りの印刷ﾊﾟｽ数
	print u'埋め込み残りの印刷ﾊﾟｽ数={0}'.format(embedded_print_path(obj))

if __name__ == '__main__':
	mcmUtil.init_mcm_util('.','.')
	#calc_test( jobUtil.PartsData("org",1.6, 0.8, 0.45) )
	#calc_test( jobUtil.PartsData("MPU-9250",3.0, 3.0, 1.0) )
	#calc_test( jobUtil.PartsData("C25",1.6, 0.8, 0.8) )

	#rect_png_test("d1.png", jobUtil.PartsData("org",1.6, 0.8, 0.45) )
	#rect_png_test("d2.png", jobUtil.PartsData("MPU-9250",3.0, 3.0, 1.0) )
	#rect_png_test("d3.png", jobUtil.PartsData("C25",1.6, 0.8, 0.8) )
	embedded(layerNo=10, imageFile='16-f.png', mountFile='parts/mount.txt', layerName='section01', materialName=u"構造材1パス",originZ=1.28, blockX=4, blockY=4)
