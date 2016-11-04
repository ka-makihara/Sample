#-*- coding: UTF-8 -*-
u"""埋め込みｱﾙｺﾞﾘｽﾞﾑ

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

__dottLingth = 0.0423333	#1ﾄﾞｯﾄの大きさ

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


def embedded(layerNo=1, imageFile, mountFile, sectionName, blockX=4, blockY=4):
	u'''埋め込みｱﾙｺﾞﾘｽﾞﾑ
		    layerNo: ﾚｲﾔｰ番号
		  imageFile: ｷｬﾋﾞﾃｨ画像ﾌｧｲﾙ
		  mountFile:
		sectionName:
		     blockX:
		     blockY:
	'''

	#ｲﾒｰｼﾞﾌｧｲﾙ名をﾌｧｲﾙ名と拡張子に分割
	img_name,ext = os.path.splitext( os.path.basename(imageFile) )

	#JOBﾌｧｲﾙからﾊﾟｰﾂﾘｽﾄを作成
	job_partsList = jobUtil.create_parts_list()

	#実装ﾃﾞｰﾀﾌｧｲﾙより実装ﾘｽﾄを作成(実装ﾘｽﾄはJOBﾌｫﾙﾀﾞ下のpartsにある事)
	mntFile = mcmUtil.get_job_path() + '\\parts\\' + mountFile
	mountList = jobUtil.create_mount_list(mntFile)

	#埋め込むﾊﾟｰﾂ
	parts_list = mountList[sectionName]

	#埋め込むﾊﾟｰﾂがJOBに定義されているか
	if exist_parts(job_partsList,parts_list) == False:
		return

	#ｲﾒｰｼﾞﾌｧｲﾙ
	img = Image.open(imageFile)
	pix1 = img.load()

	#上部100ﾗｲﾝ分を白で塗りつぶす(捨て打ちエリアの除外)
	fill_data = [[255 for i in range(3)] for j in range(img.size[0])]	#画像横ｻｲｽﾞ
	for yy in range(100):
		pix[0,yy] = fill_data


	#ｸﾞﾚｰｽｹｰﾙの画像ﾃﾞｰﾀを生成する
	tmp_img = Image.new('L',img.size,(255,255,255))

	pix2 = tmp_img.load()
	for yy in range( img.size[1] ):
		for xx in range( img.size[0] ):
			if pix1[xx,yy] == 255:
				pix2[xx,yy] = 0
			else:
				pix2[xx,yy] = 255

	d_img = mcmUtil.get_job_path() * '\\image\\d_img.png'
	tmp_img.save( d_img )

	