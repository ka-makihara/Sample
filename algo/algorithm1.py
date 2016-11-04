#-*- coding: UTF-8 -*-
u"""造形ｱﾙｺﾞﾘｽﾞﾑ1
				 	layerSubNo : offset 0.032
	((印刷・印刷・乾燥) ×16) + 乾燥
	((印刷・印刷・乾燥) ×16) + 乾燥
	((印刷・印刷・乾燥) × 8) + 乾燥
"""

import os
import sys
import xml.etree.ElementTree as ET

import jobUtil

__version__ = "1.0.0"

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

#層毎の imageOrizinZ のｵﾌｾｯﾄ(層毎に加算)
layer_offset_Z = 0.032

def curing_print(layerNo, subNo, materialName, imageFile, originZ, idx):
	u"""乾燥用のprintCommandを生成する
		速度: 50mm/sec
		回数: 8回
	"""

	elm_list = []

	#ｲﾒｰｼﾞﾌｧｲﾙ名をﾌｧｲﾙ名と拡張子に分割
	img_name,ext = os.path.splitext( os.path.basename(imageFile) )	

	pos = image_table[idx][0]
	idx = image_table[idx][1]

	#ﾃﾞﾌｫﾙﾄﾊﾟﾗﾒｰﾀ
	params = {'layerNo':layerNo, 'layerSubNo':subNo,'materialName':materialName,'rollerMode':0, 'layerType':0}
	params.update({'offsetX':0, 'offsetY':0, 'offsetZ':0})

	#分割されたｲﾒｰｼﾞﾌｧｲﾙ名
	img_file = 'image/' + img_name + '_M0101_B' + '{0:02d}{1:02d}'.format(idx[0],idx[1]) + ext

	#ﾊﾟﾗﾒｰﾀ設定
	params.update({'printImage':img_file})
	params.update({'imageOriginX':pos[0], 'imageOriginY':pos[1], 'imageOriginZ':pos[2] + originZ})
	params.update({'printMode':0,'printSpeed':500})
	params.update({'curingMode':3,'curingSpeed':50,'curingCount':8})

	elm_list.append( jobUtil.print_command(params) )

	return elm_list

def layer_print(layerNo, subNo, materialName, imageFile, originZ, start, end):
	u"""(印刷・印刷・乾燥) × 16
		layerNo     :
		subNo       : layerSubNo 開始番号
		materialName:
		imageFile   :
		originZ     :
		start       : ｲﾒｰｼﾞﾃｰﾌﾞﾙの使用開始位置
		end         : ｲﾒｰｼﾞﾃｰﾌﾞﾙの使用終了位置

		return : XML 文字列ﾘｽﾄ
			例) ['<AAA>123</AAA>','<BBB>0123</BBB>']
	"""

	elm_list = []

	#ｲﾒｰｼﾞﾌｧｲﾙ名をﾌｧｲﾙ名と拡張子に分割
	img_name,ext = os.path.splitext( os.path.basename(imageFile) )	

	for (i,layer) in enumerate(image_table[start:end]):
		pos = layer[0]
		idx = layer[1]

		#ﾃﾞﾌｫﾙﾄﾊﾟﾗﾒｰﾀ
		params = {'layerNo':layerNo, 'materialName':materialName,'rollerMode':0, 'layerType':0}

		#分割されたｲﾒｰｼﾞﾌｧｲﾙ名
		img_file = 'image/' + img_name + '_M0101_B' + '{0:02d}{1:02d}'.format(idx[0],idx[1]) + ext

		#ﾊﾟﾗﾒｰﾀ設定
		params.update({'printImage':img_file})
		params.update({'layerSubNo':subNo + i + 1})
		params.update({'imageOriginX':pos[0], 'imageOriginY':pos[1], 'imageOriginZ':pos[2] + originZ})
		params.update({'offsetX':0, 'offsetY':0, 'offsetZ':0})
		params.update({'printMode':1,'printSpeed':500})
		params.update({'curingMode':0,'curingSpeed':0,'curingCount':0})

		#印刷
		elm_list.append( jobUtil.print_command(params) )

		#乾燥
		if i % 2 == 1:
			params.update({'offsetZ':80.0})
			params.update({'printMode':0, 'curingMode':1, 'curingSpeed':500, 'curingCount':1})
			elm_list.append( jobUtil.print_command(params) )

	return elm_list

def func1(layerNo=1, materialName="", imageFile="", originZ=0.000, blockX=4 ,blockY=4):
	u"""((印刷・印刷・乾燥) ×16) ×2.5回 + 乾燥
		layerNo     : ﾚｲﾔｰ番号
		materialName: ﾏﾃﾘｱﾙ名
		imageFile   : ｲﾒｰｼﾞﾌｧｲﾙ名
		originZ     : Z基本位置

		return : XML <printCommand> 文字列ﾘｽﾄ
		例) ['<printCommand><layerNo>1</layerNo>','<layerSubNo>3</layerSubNo>','</printCommand>']
	"""
	#print 'materialName={0}:{1}'.format(type(materialName),materialName.encode('ShiftJIS'))
	#print 'imageFile={0}:{1}'.format(type(imageFile),imageFile.encode('ShiftJIS'))
	#print 'originZ={0}:{1}'.format(type(originZ),originZ)
	#print 'blockX={0}:{1} blockY={2}'.format(type(blockX),blockX,blockY)

	elm_list = []
	#指定ﾌﾞﾛｯｸ数で画像分割
	imgFiles = jobUtil.split_image(blockX,blockY,imageFile)

	subNo = 0
	elm_list.extend( layer_print(layerNo,subNo,materialName,imageFile,originZ + 0.000,0,len(image_table)) )

	subNo += len(image_table)
	elm_list.extend( layer_print(layerNo,subNo,materialName,imageFile,originZ + layer_offset_Z,0,len(image_table)) )

	subNo += len(image_table)
	elm_list.extend( layer_print(layerNo,subNo,materialName,imageFile,originZ + layer_offset_Z * 2,0,len(image_table)/2) )

	elm_list.extend( curing_print(layerNo,40,materialName,imageFile,originZ + layer_offset_Z * 2,7) )

	return elm_list
#
#
#
if __name__ == '__main__':
	func1(1,materialName=u"日本語",imageFile="bbb.png")
