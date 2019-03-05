#-*- coding: UTF-8 -*-

import sys
import os
#import xml.etree.ElementTree as ET #xmlツリー構造を読み込む　asで別名に変更
import lxml.etree as ET

import traceback
import matplotlib.pyplot as plt
import subprocess

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

def job_check(jobPath, debug=True):
	u'''
		jobPath: JOBﾌｫﾙﾀﾞ名
	'''
	ret = 123
	try:
		#ｴﾝｺｰﾃﾞｨﾝｸﾞを統一する
		#  ※setdefaultencoding() は sitecustomizeﾓｼﾞｭｰﾙからのみ使用するように定義
		#    されているため、site.py から呼び出された後でこの関数はsysから削除される
		#    よって、reload() で再ﾛｰﾄﾞしないと関数が実行できない
		reload(sys)
		sys.setdefaultencoding('cp932')
		if jobPath == None:
			#引数にJOBﾌｫﾙﾀﾞが指定されていない
			if debug == True:
				user32.MessageBoxW(0,u"引数にJOBﾌｫﾙﾀﾞを指定してください",u"引数ｴﾗｰ",(MB_OK | MB_ICONSTOP))
				print 'usage: jobCheck <JOB Folder>'

		else:
			#plt はglobalであるため(Builder下では)、違うJOBを読み込んだ場合にｸﾞﾗﾌが重なる場合があるので消去する
			plt.clf()

			#ｶﾚﾝﾄﾌｫﾙﾀﾞ(作業ﾌｫﾙﾀﾞ)をJOBのﾌｫﾙﾀﾞへ
			os.chdir(jobPath)

			#JOB.xml の読み込み
			tree = ET.parse(jobPath + '\\JOB.xml')
			root = tree.getroot()

			#printCommand　または　planarizeCommand に含まれる imageOriginZ　または　posZ の値を取り出してﾘｽﾄ化
			#z_list =[float(cmd.findtext('.//imageOriginZ')) for cmd in root.findall('.//printCommand')]
			#z_list =[float(cmd.findtext('.//posZ')) for cmd in root.findall('.//planarizeCommand')]
			z_list =[(float(cmd.findtext('.//posZ')) or float(cmd.findtext('.//imageOriginZ')))  for cmd in (root.findall('.//planarizeCommand') or root.findall('.//printCommand'))]

			# (比較のために)昇順に並べる
			z2 = sorted(z_list)

			if z_list != z2:
				#(昇順に並べる前と後で)変化点がある
				if debug == True:
					user32.MessageBoxW(0,u"imageOriginZ 比較エラー",u"JOBチェック",(MB_OK | MB_ICONSTOP))

				ret = -1
			else:
				if debug == True:
					user32.MessageBoxW(0,u"JOBチェック完了",u"JOBチェック",(MB_OK | MB_ICONINFORMATION))

			#list.txtを保存する
			f = open('list.txt','w')
			for x in z_list:
				f.write(str(x) + "\n")
			f.close()

			plt.grid(True)
			plt.plot(z_list)
			plt.savefig("graph.png")
			#ｸﾞﾗﾌ表示する
			if debug == True:
				# Builder 側からmatplotlib の show() を呼ぶと、ｸﾞﾗﾌｳｲﾝﾄﾞｳをｸﾛｰｽﾞするとBuilderのﾀﾞｲｱﾛｸﾞが戻ってこない(場合が多い)
				# builder 側から呼ばずにｺﾝｿｰﾙで呼ぶ場合にのみ使用したほうが良い
				plt.show()

			# 上記 matplotlib のshow()では不具合が発生する(原因不明)ので
			# PhotoViewer を呼び出してｸﾞﾗﾌを表示する
			png_file = jobPath + '\\graph.png'
			cmd = 'C:\\Windows\\system32\\rundll32.exe "C:\\Program Files\\Windows Photo Viewer\\PhotoViewer.dll",ImageView_Fullscreen ' + png_file
			subprocess.call(cmd)

	except:
		ret = -2
		errmsg = traceback.format_exc( sys.exc_info()[2] )
		if debug == True:
			user32.MessageBoxW(0,u"Error\n" + errmsg,u"JOBチェック",(MB_OK | MB_ICONSTOP))

	return ret

if __name__ == '__main__':

	job_check(sys.argv[1])
