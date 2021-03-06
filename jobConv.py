#-*- coding: UTF-8 -*-
u"""ｱﾙｺﾞﾘｽﾞﾑ化JOB変換ﾂｰﾙ
"""

import sys
import os
import shutil		# for ﾌｫﾙﾀﾞｰｺﾋﾟｰ

import re			#正規表現ﾗｲﾌﾞﾗﾘ
import importlib	#ﾓｼﾞｭｰﾙの動的ﾛｰﾄﾞ
import inspect		#ﾓｼﾞｭｰﾙ内の関数検索
import subprocess

import xml.dom.minidom as dom
import xml.etree.ElementTree as ET

import glob		# for ﾌｧｲﾙ一覧用

import mcmUtil
import traceback

from ctypes import *

__version__ = "1.0.0"

user32 = windll.user32

#ﾒｯｾｰｼﾞﾎﾞｯｸｽ定義
MB_OK = 0
MB_OKCANCEL = 1
MB_ABORTRETRYIGNORE = 2
MB_YESNOCANCEL = 3
MB_YESNO = 4
MB_RETRYCANCEL = 5
MB_ICONSTOP = 16
MB_ICONQUESTION = 32
MB_ICONEXCLAMATION = 48
MB_ICONINFORMATION = 64

#
# 文字列が数値かどうか判定する
#   浮動小数点'.'を含む場合も True とする
#
#  <検索ﾊﾟﾀｰﾝの意味>
#    ^[\d+-]: 先頭が数値または'+','-'
#        '+': 前述のﾊﾟﾀｰﾝの一回以上に一致
#       '\.': '.' に一致
#        '?': 直前の文字の0回または1回に一致
#      '\d*': 複数回の数値に一致
#
def is_digit(str):
	return re.compile("^[\d+-]+\.?\d*\Z").match(str)

def prettify(elem):
    rought_string = ET.tostring(elem,'utf-8')
    reparsed = dom.parseString(rought_string)
    return reparsed.toprettyxml(indent=" ",newl="\r\n")

#
# 文字列のparam を 数値、文字列に分けて戻り値とする
#
def argument(param):
	if is_digit(param):
		if param.isdigit():
			return int(param)
		else:
			return float(param)
	else:
		return param
#
#
# elem:Element
#
def indent(elem, level=0):
	i = "\n" + level*"  "
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i

#
# XML 出力
#
def write_xml(f,elem):
	indent(elem)
	tree = ET.ElementTree(elem)

	tree.write(f,encoding='utf-8',xml_declaration=True)
	
	#Windowsﾒﾓ帳で読めるように改行ｺｰﾄﾞを '\n' --> '\r\n' にする
	fd = open(f)
	all_file = fd.read()
	fd.close()
	all_file.replace('\n','\r\n')

	fd = open(f,"w")
	fd.write(all_file)
	fd.close()

def default_func():
	pass

#
# root で指定されたｴﾚﾒﾝﾄﾂﾘｰの idx 番目に
# 
#
def add_elements(root, idx, xml_list):
	#XML 文字列(ﾘｽﾄ)からElement(ﾘｽﾄ)を生成する
	elm_list = [ET.fromstring(elm) for elm in xml_list]

	for elm in reversed(elm_list):
		root.insert(idx,elm)

#
# 関数引数用の辞書ｵﾌﾞｼﾞｪｸﾄを生成する
#  argList:[('argName','argValue'), ...]
#
def create_arg_dict(argList):
	return {arg[0]:argument(arg[1]) for arg in argList}

#
# cmd_elem : <algorithm> ﾀｸﾞﾃﾞｰﾀ
# params   : [('属性','値'),...]
# seq_elem : <sequenceGroup> ﾀｸﾞﾃﾞｰﾀ
#      idx : <sequenceGropu>ﾀｸﾞ内の<algorithm>ﾀｸﾞのｲﾝﾃﾞｯｸｽ
#
def algorithm_command(jobPath,cmd_elem,params, seq_elem, idx):
	fileName = ""	#ｱﾙｺﾞﾘｽﾞﾑﾌｧｲﾙ名
	funcName = ""	#ｱﾙｺﾞﾘｽﾞﾑ関数名

	for param in params:
		# param ==> ("属性値","値")
		if param[0] == 'file':
			fileName = param[1]
		elif param[0] == 'func':
			funcName = param[1]

	try:
		#指定ﾓｼﾞｭｰﾙのｲﾝﾎﾟｰﾄ
		module = importlib.import_module(fileName)

		#ﾓｼﾞｭｰﾙに含まれる関数の一覧を取得
		#funcList = inspect.getmembers(module,inspect.isfunction)

		#func = getattr(module,funcName,default_func)
		func = getattr(module,funcName)
	except Exception as e:
		#関数が見つからない
		msg = e.message + "\n" + u"ﾓｼﾞｭｰﾙ:" + fileName + u"のﾛｰﾄﾞに失敗しました"
		user32.MessageBoxW(0,msg,"JOB変換",0x40)
		return

	for tag in cmd_elem:
		if tag.tag == 'parameter':
			#parameter ﾀｸﾞの属性値を取得(関数ﾊﾟﾗﾒｰﾀの取得)
			argDict = create_arg_dict( tag.items() )

			print 'convert:{0}-{1}'.format(module.__file__,funcName)
			#関数呼び出し
			elm_str = func(**argDict)
			add_elements(seq_elem,idx,elm_str)


#
# jobPath: JOBﾌｫﾙﾀﾞﾊﾟｽ
#   elem : <squenceGroup> ﾀｸﾞﾃﾞｰﾀ
#
def proc_sequence(jobPath, elem):
	for idx,seq in enumerate(elem):
		if seq.tag == 'maintenanceCommand':
			pass
		elif seq.tag == 'printCommand':
			pass
		elif seq.tag == 'flushCommand':
			pass
		elif seq.tag == 'moveCommand':
			pass
		elif seq.tag == 'delayCommand':
			pass
		elif seq.tag == 'burnCommand':
			pass
		elif seq.tag == 'algorithm':
			algorithm_command(jobPath,seq,seq.items(),elem,idx)
			elem.remove(seq)
		else:
			pass

#
#
#
def convert_job(jobPath,exePath):
	cwd = os.getcwd()
	#ｶﾚﾝﾄﾌｫﾙﾀﾞ(作業ﾌｫﾙﾀﾞ)をJOBのﾌｫﾙﾀﾞへ
	os.chdir(jobPath)

	#ｱﾙｺﾞﾘｽﾞﾑﾗｲﾌﾞﾗﾘのﾊﾟｽを import の検索ﾊﾟｽに追加
	sys.path.append(jobPath + '\\..\\..\\algo')
	sys.path.append(exePath)
	sys.path.append(exePath + '\\algo')

	mcmUtil.init_mcm_util(jobPath,exePath)

	#JOB.xml の読み込み
	tree = ET.parse(jobPath + '\\JOB.xml')
	root = tree.getroot()

	#root[0].tag == 'allShapeObject'
	#root[1].tag == 'instrumentGroup'
	#root[2].tag == 'materialGroup'
	#root[3].tag == 'sequenceGroup'

	for et in root:
		if et.tag == 'allShapeObject':
			pass
		elif et.tag == 'instrumentGroup':
			pass
		elif et.tag == 'materialGroup':
			pass
		elif et.tag == 'sequenceGroup':
			proc_sequence(jobPath,et)

	out_job = jobPath + '\\JOB.xml'
	write_xml(out_job,root)

#
# 指定されたJOBﾌｫﾙﾀﾞの中身を全て新規ﾌｫﾙﾀﾞへｺﾋﾟｰする
#
def copy_job(jobPath):

	#JOBﾌｫﾙﾀﾞのｺﾋﾟｰを生成する(ﾌｫﾙﾀﾞ名+_xxx, とりあえず100まであれば)
	for nn in range(100):
		if os.path.exists(jobPath + '_conv_'+ str(nn)) == False:
			break

	#ｺﾋﾟｰ先ﾌｫﾙﾀﾞ名
	newPath = jobPath + '_conv_' + str(nn)

	#ﾌｫﾙﾀﾞｺﾋﾟｰ
	shutil.copytree(jobPath,newPath)

	#JOB.xml のみ削除
	#if os.path.exists(newPath + '\\JOB.xml') == True:
	#	os.remove(newPath + '\\JOB.xml')

	return newPath
#
#
#
if __name__ == '__main__':
	args = sys.argv

	#from ctypes import *
	#user32 = windll.user32

	#ｴﾝｺｰﾃﾞｨﾝｸﾞを統一する
	#  ※setdefaultencoding() は sitecustomizeﾓｼﾞｭｰﾙからのみ使用するように定義
	#    されているため、site.py から呼び出された後でこの関数はsysから削除される
	#    よって、reload() で再ﾛｰﾄﾞしないと関数が実行できない
	reload(sys)
	sys.setdefaultencoding('cp932')

	if len(sys.argv) == 1:
		#引数にJOBﾌｫﾙﾀﾞが指定されていない
		user32.MessageBoxW(0,u"引数にJOBﾌｫﾙﾀﾞを指定してください",u"引数ｴﾗｰ",(MB_OK | MB_ICONSTOP))
		print 'usage: jobConv <JOB Folder>'

	else:
		exePath = os.path.dirname(args[0])
		if exePath == "":
			exePath = os.getcwd()

		try:
			newPath = copy_job(args[1])
			convert_job(newPath,exePath)
			user32.MessageBoxW(0,u"JOB変換完了",u"JOB変換",(MB_OK | MB_ICONINFORMATION))
		except:
			errmsg = traceback.format_exc( sys.exc_info()[2] )
			user32.MessageBoxW(0,u"JOB変換エラー\n" + errmsg,u"JOB変換",(MB_OK | MB_ICONSTOP))


