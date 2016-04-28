#-*- coding: UTF-8 -*-
u"""MCで使用する数値計算用ﾗｲﾌﾞﾗﾘ
"""

import math
import xml.etree.ElementTree as ET

__version__ = "1.0.0"

job_path = ""
job_tree = None
job_root = None
cfg_tree = None
cfg_root = None

def init_mcm_util(jobPath):
	u"""[MCM の設定情報を取得するためのﾕｰﾃｨﾘﾃｨ初期化]
	"""
	global job_tree, job_root, job_path
	job_path = jobPath
	job_tree = ET.parse(jobPath + '\\JOB.xml')
	job_root = job_tree.getroot()
	#root[0].tag == 'allShapeObject'
	#root[1].tag == 'instrumentGroup'
	#root[2].tag == 'materialGroup'
	#root[3].tag == 'sequenceGroup'

def get_job_data(tagName):
	u"""[JOBﾃﾞｰﾀからﾀｸﾞのﾃﾞｰﾀ値を取得する]
		'materialGroup/materialData/maxX' のように / で区切る
		※予め init_mcm_util(jobPath) を実行しておくこと
	"""
	obj = job_root.find(tagName)
	if obj == None:
		return None

	return obj.text

def get_job_path():
	u"""[現在のJOBﾌｧｲﾙのﾊﾟｽを取得する]
	"""
	return job_path


def get_baking_time(layerNo):
	u"""[ﾍﾞｲｷﾝｸﾞ時間(tb:TimeBaking)の取得]
		layerNo : ﾚｲﾔｰ番号
	"""
	tm = -79.01 * math.log(layerNo) + 308.92
	if tm < 0.0:
		return 0
	else:
		return int(tm * 1000)

def get_baking_wait(layerNo):
	u"""[ﾍﾞｲｷﾝｸﾞ待ち時間(tbw:TimeBakingWait)の取得]
		layerNo : ﾚｲﾔｰ番号
	"""
	tm = 11.427 * math.log(layerNo) - 13.323
	if tm < 0.0:
		return 0
	else:
		return int(tm * 1000)

def get_dry_time(layerNo):
	u"""[乾燥時間(td:TimeDry)の取得]
		layerNo : ﾚｲﾔｰ番号
	"""
	tm = 47.637 / layerNo - 0.3791
	if tm < 0.0:
		return 0
	else:
		return int(tm * 1000)

def get_print_wait(layerNo):
	u"""[印刷待ち時間(tpw:TimePrintWait)の取得]
		layerNo : ﾚｲﾔｰ番号
	"""
	tm = 8.9351 * math.log(layerNo) - 12.548
	if tm < 0.0:
		return 0
	else:
		return int(tm * 1000)
