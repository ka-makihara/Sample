#-*- coding: UTF-8 -*-
u"""JOBへの出力用ﾕｰﾃｨﾘﾃｨﾗｲﾌﾞﾗﾘ
"""

import os
import sys
import subprocess
import glob
import types
import xml.etree.ElementTree as ET

import traceback

__version__ = "1.0.0"

print_cmd_items = [	'layerNo',     'layerSubNo',  'layerType',
					'materialName','printMode',   'printImage',
					'imageOriginX','imageOriginY','imageOriginZ',
					'offsetX',     'offsetY',     'offsetZ',    'printSpeed',
					'rollerMode',  'curingMode',  'curingSpeed','curingCount',
					'dryingMode', 'dryingSpeed','dryingCount','dryingTime','dryingOffsetY'
				]

move_cmd_items = ['positionNo','offsetX','offsetY','offsetZ','headRetruction','capping']
delay_cmd_items= ['time']
burn_cmd_items = ['scanList','materialName','imageOriginX','imageOriginY','imageOriginZ',
					'offsetX','offsetY','offsetZ','offsetLZ','markSpeed','power']

maintenance_cmd_items = ['target','purgeTime','wipingMode','flushCount','cappingMode']

#
# bx,by で指定されたﾌﾞﾛｯｸ数でｲﾒｰｼﾞﾌｧｲﾙを分割する
#  return: 生成されたｲﾒｰｼﾞﾌｧｲﾙﾘｽﾄ(ﾌｧｲﾙ名のみ)
#
#
def split_image(bx, by, imgFile):
	imageFile = imgFile.encode('ShiftJIS')
	exe_file = 'F:\\source\\SplitImage\\Release\\bitmapBunkatsu.exe'
	exe_para = ' /mask=1,1 /output=image /image=' + imgFile.encode('ShiftJIS')
	exe_para = exe_para + ' /block={0},{1}'.format(bx,by)

	cmd = exe_file + exe_para
	try:
		#分割ｱﾌﾟﾘの起動と終了待ち
		ret = subprocess.check_call( cmd.strip().split(" ") )
	except:
		print traceback.format_exc(sys.exc_info()[2])
		return []

	#ｲﾒｰｼﾞ分割で生成したﾌｧｲﾙ群の一覧を取得
	name,ext = os.path.splitext( os.path.basename(imageFile) )
	out_path = os.getcwd() + '\\image\\'	#出力先はｶﾚﾝﾄ\image
	#files = glob.glob(out_path + name + '*.png')
	files = [os.path.basename(r) for r in glob.glob(out_path + name + '*.png')]

	return files

#
#
#
def create_cmd(cmdName, cmd_items, dict):
	ret = '<' + cmdName + '>'

	for item in cmd_items:
		if dict.has_key(item) == True:
			if isinstance(dict[item],types.UnicodeType) == True:
				cmd = '<' + item + '>' + dict[item] + '</' + item + '>'
			else:
				cmd = '<' + item + '>' + str(dict[item]) + '</' + item + '>'
		else:
			cmd = '<' + item + '>' + '0' + '</' + item + '>'

		ret = ret + cmd

	return ret + '</' + cmdName + '>'
#
#
#
def print_command(dict):
	return create_cmd('printCommand',print_cmd_items,dict).encode('UTF-8')

def print_command_xml(dict):
	return ET.fromstring(print_command(dict)) 

def move_command(dict):
	return create_cmd('moveCommand',move_cmd_items,dict).encode('UTF-8')

def delay_command(dict):
	return create_cmd('delayCommand',delay_cmd_items,dict).encode('UTF-8')

def burn_command(dict):
	return create_cmd('burnCommand',burn_cmd_items,dict).encode('UTF-8')

def maintenance_command(dict):
	return create_cmd('maintenanceCommand',maintenance_cmd_items,dict).encode('UTF-8')
