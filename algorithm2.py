#-*- coding: UTF-8 -*-
u"""回路造形・焼成ｱﾙｺﾞﾘｽﾞﾑ

"""

import os
import sys
import xml.etree.ElementTree as ET
from PIL import Image

import jobUtil
import imageUtil
import mcmUtil
import laserUtil
import vectUtil

__version__ = "1.0.0"

image_table = [
[(0.0000000,0.0000000,1.5200),(1,2)],
[(0.0423330,0.0423330,1.5200),(2,1)],
[(0.0000000,0.0423330,1.5200),(1,1)],
[(0.0423330,0.0000000,1.5200),(2,2)],
]

def layer_print(num, layerNo, subNo, materialName, imageFile, paramDict={}):
	u"""[配線用 printCommand の生成]
		     layerNo:
		       subNo: layerSubNo 開始番号
		materialName:
		   imageFile:
		     originZ:
		         cnt: ｲﾒｰｼﾞﾃｰﾌﾞﾙの使用数

 		return : XML 文字列ﾘｽﾄ
		例) ['<AAA>123</AAA>','<BBB>0123</BBB>']
    """

	elm_list = []

	#ｲﾒｰｼﾞﾌｧｲﾙ名をﾌｧｲﾙ名と拡張子に分割
	img_name,ext = os.path.splitext( os.path.basename(imageFile) )	

	#for (i,layer) in enumerate(image_table):
	pos = image_table[num][0]
	idx = image_table[num][1]

	#ﾃﾞﾌｫﾙﾄﾊﾟﾗﾒｰﾀ
	params = {'layerNo':layerNo, 'materialName':materialName,'rollerMode':0, 'layerType':0}

	#分割されたｲﾒｰｼﾞﾌｧｲﾙ名
	img_file = 'image/' + img_name + '_M0101_B' + '{0:02d}{1:02d}'.format(idx[0],idx[1]) + ext

	#ﾊﾟﾗﾒｰﾀ設定
	params.update({'printImage':img_file})
	params.update({'layerSubNo':subNo})
	#params.update({'imageOriginX':pos[0], 'imageOriginY':pos[1], 'imageOriginZ':pos[2]})
	params.update({'imageOriginX':pos[0], 'imageOriginY':pos[1], 'imageOriginZ':layerNo*0.08})
	params.update({'offsetX':0, 'offsetY':0, 'offsetZ':0})
	params.update({'printMode':1,'printSpeed':193})
	params.update({'curingMode':0,'curingSpeed':0,'curingCount':0})
	params.update({'dryingMode':4, 'dryingSpeed':20,'dryingCount':3,'dryingOffsetY':0})
	params.update({'dryingTime':mcmUtil.get_dry_time(layerNo)})

	params.update(paramDict)
	#印刷
	elm_list.append( jobUtil.print_command(params) )

	return elm_list

def baking_command(layerNo, layerSubNo, materialName, imageFile, paramDict={}):
	u"""[ﾍﾞｲｷﾝｸﾞ用 printCommand]
		配線ｲﾒｰｼﾞ画像と同ｻｲｽﾞの白(255,255,255)画像を生成して、予備赤外照射用のpngﾌｧｲﾙとする
	"""
	# ﾍﾞｰｷﾝｸﾞ用画像の生成(配線画像と同ｻｲｽﾞの白画像)
	with Image.open(imageFile) as img:
		if imageUtil.createPngFile('baking.png',img.size,255) == False:
			return False

	img_file = 'image/' + os.path.basename(imageFile)

	#ﾊﾟﾗﾒｰﾀ設定
	params = {'printImage':img_file,'dryingTime':mcmUtil.get_baking_time(layerNo)}
	params.update(paramDict)

	return layer_print(0,layerNo,layerSubNo,materialName,imageFile,params)

def burn_command(layerNo, materialName, vectFile, density, paramDict={}):
	u"""[burnCommand 生成]
		layerNo     :
		materialName:
		 vectFile   : ﾍﾞｸﾄﾙﾌｧｲﾙ名
		density     : ﾊﾟﾜｰ密度
	"""
	elm_list = []

	params = {'materialName':materialName,'markSpeed':1}
	params.update({'imageOriginX':0,'imageOriginY':0,'imageOriginZ':layerNo*0.08})
	params.update({'offsetX':0,'offsetY':0,'offsetZ':0})
	params.update({'offsetLZ':laserUtil.get_offsetLZ()})
	params.update({'power':laserUtil.laserPow(density)})
	params.update({'scanList':'vector\\'+vectFile})

	params.update( paramDict )

	elm_list.append( jobUtil.burn_command(params) )

	return elm_list

def burn_with_bake(layerNo, materialName="", imageFile="", imageOriginX=0.0, imageOriginY=0.0, imageOriginZ=0.0, blockX=2, blockY=2):
	u"""[ﾍﾞｲｷﾝｸﾞを含む印刷・焼成ｺﾏﾝﾄﾞの生成]
		     layerNo:
		materialName:
		   imageFile:
		imageOriginZ:
		      blockX: X方向画像分割数
		      blockY: Y方向画像分割数
	"""
	#ﾍﾞｸﾄﾙ生成のｵﾌｾｯﾄ値をJOBﾌｧｲﾙより取得
	ofx = float( mcmUtil.get_job_data('instrumentGroup/circuitPrinter/offsetX') )
	ofy = float( mcmUtil.get_job_data('instrumentGroup/circuitPrinter/offsetY') )

	#ﾍﾞｸﾄﾙﾌｧｲﾙの生成
	film_vec_file, line_vec_file = vectUtil.create_vect_file(imageFile,burnRange=0.60, offsetX=0.0, offsetY=0.0)

	elm_list = []

 	#印刷前乾燥(ﾍﾞｰｷﾝｸﾞ)
 	elm_list.extend( baking_command(layerNo,1,materialName,imageFile) )
 	elm_list.append( jobUtil.move_command({'positionNo':3}) )
	elm_list.append( jobUtil.delay_command({'time':mcmUtil.get_baking_wait(layerNo)}) )

  	#一層目
  	for n in range(3):
  		elm_list.extend( layer_print(n,layerNo, n+1 , materialName, imageFile) )
 		elm_list.append( jobUtil.move_command({'positionNo':3}) )
		elm_list.append( jobUtil.delay_command({'time':mcmUtil.get_print_wait(layerNo)}) )

	#印刷・(印刷+焼成前)乾燥
  	elm_list.extend( layer_print(3,layerNo,6,materialName,imageFile,{'dryingTime':mcmUtil.get_dry_time(layerNo)*2}) )
  	#焼成
  	if len(film_vec_file) != 0:
  		#膜ﾍﾞｸﾄﾙﾃﾞｰﾀがある
  		elm_list.extend( burn_command(layerNo,materialName,film_vec_file,20,{'imageOriginZ':layerNo*0.08}) )

  	if len(line_vec_file) != 0:
  		#線分ﾍﾞｸﾄﾙﾃﾞｰﾀがある
  		elm_list.extend( burn_command(layerNo,materialName,line_vec_file,20,{'imageOriginZ':layerNo*0.08}) )


	#print elm_list

	return elm_list

def burn_only(layerNo, materialName="", imageFile="", imageOriginX=0.0, imageOriginY=0.0, imageOriginZ=0.0, blockX=2, blockY=2):
	u"""[ﾍﾞｲｷﾝｸﾞ無しの印刷・焼成ｺﾏﾝﾄﾞの生成]
		     layerNo:ﾚｲﾔｰ番号
		materialName:
		   imageFile:
		imageOriginZ:
		      blockX: X方向画像分割数
		      blockY: Y方向画像分割数
	"""
	elm_list = []

 	params = {'printSpeed':500,'curingMode':1,'curingSpeed':500,'curingCount':1}

  	#一層目
  	for n in range(3):
  		elm_list.extend( layer_print(n,layerNo, n+1 , materialName, imageFile,params) )

	#印刷・(印刷+焼成前)乾燥
  	elm_list.extend( layer_print(3,layerNo,6,materialName,imageFile,{'dryingTime':mcmUtil.get_dry_time(layerNo)*2}) )
  	#焼成
  	elm_list.extend( burn_command(layerNo,materialName,imageFile,20) )

	return elm_list


if __name__ == '__main__':
	burn1(1,u'回路材1','sample.png')
