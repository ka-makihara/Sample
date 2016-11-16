#-*- coding: UTF-8 -*-
u"""JOBへの出力用ﾕｰﾃｨﾘﾃｨﾗｲﾌﾞﾗﾘ
"""

import os
import sys
import subprocess
import glob
import types
import xml.etree.ElementTree as ET
import _winreg

import traceback
import mcmUtil		#初期化は jobConv.py で行われている
import re			#正規表現ﾗｲﾌﾞﾗﾘ

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

mount_cmd_items = ['layerNo','partName','x','y','z','angle','direction','placeOffsetX','placeOffsetY','placeOffsetZ']

def split_image(bx, by, imgFile):
	u"""[指定されたﾌﾞﾛｯｸ数でｲﾒｰｼﾞﾌｧｲﾙを分割する]
		   bx : X方向ﾌﾞﾛｯｸ数
		   by : Y方向ﾌﾞﾛｯｸ数
		return: 生成されたｲﾒｰｼﾞﾌｧｲﾙﾘｽﾄ(ﾌｧｲﾙ名のみ)
	"""

	#分割ｱﾌﾟﾘのｲﾝｽﾄｰﾙ先をﾚｼﾞｽﾄﾘから取得
	try:
		reg =_winreg.OpenKey(_winreg.HKEY_CURRENT_USER,u"Software\\NSW\\イメージ分割アプリケーション".encode('ShiftJis'))
		path =_winreg.EnumValue(reg,0)[1].encode('ShiftJis')
	except:
		path = mcmUtil.get_exe_path() + '\\'

	#分割ｱﾌﾟﾘのﾌﾙﾊﾟｽ
	exe_file = path + 'bitmapBunkatsu.exe'

	imageFile = imgFile.encode('ShiftJIS')
	exe_para = ' /mask=1,1 /output=image /image=' + imgFile.encode('ShiftJIS')
	exe_para = exe_para + ' /block={0},{1}'.format(bx,by)

	cmd = exe_file + exe_para

	#実行ﾌｧｲﾙとﾊﾟﾗﾒｰﾀをﾘｽﾄ化
	exe_cmd = [exe_file]+exe_para.strip().split(" ")

	try:
		#分割ｱﾌﾟﾘの起動と終了待ち
		#ret = subprocess.check_call( cmd.strip().split(" ") )
		ret = subprocess.check_call( exe_cmd )
	except:
		print traceback.format_exc(sys.exc_info()[2])
		return []

	#ｲﾒｰｼﾞ分割で生成したﾌｧｲﾙ群の一覧を取得
	name,ext = os.path.splitext( os.path.basename(imageFile) )
	out_path = os.getcwd() + '\\image\\'	#出力先はｶﾚﾝﾄ\image
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

def mount_command(dict):
	return create_cmd('mountCommand',mount_cmd_items,dict).encode('UTF-8')


class PartsData:
	def __init__(self,name, xs=0.0, ys=0.0, hh=0.0, capa=0.0):
		self.name = name
		self.x_size = xs 
		self.y_size = ys
		self.height = hh
		self.layerQty = 0
		self.pathQty = 0
		self.capacity = capa #体積(ｻｲｽﾞによる計算値ではなく直接設定用)

	def size(self):
		return (self.x_size,self.y_size)

	def left_up(self,center_pos):
		u''' 指定されたﾊﾟｰﾂ中心(mm)から左上の位置を得る
		'''
		return ( center_pos[0]-self.x_size/2.0, center_pos[1]+self.y_size/2.0 )

	def set_print_count(self, layerQty, pathQty):
		u'''印刷層数とﾊﾟｽ数を設定する
		'''
		self.layerQty = layerQty
		self.pathQty = pathQty

	def get_print_count(self):
		return (self.layerQty, self.pathQty)

class MountData:
	def __init__(self,name,xx,yy,rr,zz):
		self.name = name
		self.xPos = xx
		self.yPos = yy
		self.angle = rr
		self.zPos = zz
		self.layerQty = 0
		self.pathQty = 0
		self.parts = PartsData(name)

	def position(self, ofx=0.0, ofy=0.0):
		return (self.xPos-ofx,self.yPos-ofy)

	def set_print_count(self, layerQty, pathQty):
		self.layerQty = layerQty
		self.pathQty = pathQty

	def get_print_count(self):
		return (self.layerQty, self.pathQty)

	def get_total_path(self, layerPath):
		return self.layerQty * layerPath + self.pathQty

def create_parts(element):
	name = ""
	sx = 0.0
	sy = 0.0
	sz = 0.0

	for ee in list(element):
		if ee.tag == 'partName':
			name = ee.text
		elif ee.tag == 'sizeX':
			sx = float(ee.text)
		elif ee.tag == 'sizeY':
			sy = float(ee.text)
		elif ee.tag == 'height':
			sz = float(ee.text)

	partsObj = PartsData(name,sx,sy,sz)

	return partsObj


def create_parts_list():
	u'''JOBﾌｧｲﾙよりﾊﾟｰﾂﾘｽﾄを生成する
	   jobFile: JOBﾌｧｲﾙ名
	 '''
	parts_list = []
	elm = mcmUtil.get_job_element("materialGroup")

	for ee in list(elm):
		if ee.tag == 'partsData':
			parts = create_parts(ee)	
			parts_list.append(parts)

	return parts_list


def create_mount_data(posItem, ofx=0.0, ofy=0.0):
	xPos = 0.0
	yPos = 0.0
	rPos = 0.0
	zPos = 0.0
	name = ""

	for item in posItem:
		data = item.split('=')
		if len(data) == 1:
			#ﾊﾟｰﾂ名
			name = data[0]
		else:
			if data[0].upper() == 'X':
				xPos = float(data[1])
			elif data[0].upper() == 'Y':
				yPos = float(data[1])
			elif data[0].upper() == 'R':
				rPos = float(data[1])
			elif data[0].upper() == 'Z':
				zPos = float(data[1])
			else:
				pass

	md = MountData(name,xPos-ofx,yPos-ofy,rPos,zPos)
	return md


def create_mount_list(mountFile, ofx=0.0, ofy=0.0):
	u'''実装ﾃﾞｰﾀﾌｧｲﾙを読み込んでﾘｽﾄ化する
		mountFile: ﾌｧｲﾙ名
		ofx:X方向ｵﾌｾｯﾄ
		ofy:Y方向ｵﾌｾｯﾄ

		[section名]
			<ﾊﾟｰﾂ名>  X=.... Y=... R=...
	'''

	section = r'\[[a-zA-Z0-9-_]+\]'	#[section]
	pattern = r'[a-zA-Z0-9-.=_]+'

	mount_list = {}
	ml = []
	sectionName = ""

	with open(mountFile) as fd:
		for ln in fd:
			ss = ln.strip()
			if ss[0] == '#':
				continue
			if len(ss):
				if re.match(section,ss):
					if len(ml) != 0:
						mount_list[sectionName] = ml

					sectionName = ss[1:-1]	#section名の取り出し([]を省く)
					ml = []
				else:
					items = re.findall(pattern,ss)
					md = create_mount_data(items,ofx,ofy)
					ml.append(md)

		if len(ml) != 0:
			mount_list[sectionName] = ml

	return mount_list


def exist_parts(job_parts, mount_parts):
	for mp in mount_parts:
		nn = filter((lambda x: x.name == mp.name),job_parts)
		if len(nn) == 0:
			return False

	return True

if __name__ == '__main__':
	u"""ﾃｽﾄ実行用ﾒｲﾝ
	"""
	param = sys.argv

	'''
	#引数である画像ﾌｧｲﾙのﾊﾟｽへ移動
	imgPath = os.path.dirname(param[1])
	os.chdir(imgPath)

	#imageﾌｫﾙﾀﾞを作成する
	if os.path.exists( imgPath + '\\image') == False:
		os.mkdir( imgPath + '\\image')

	split_image(2,2,param[1])
	'''
	mcmUtil.init_mcm_util(param[1],param[1])

	partsList = create_parts_list()

	for part in partsList:
		print 'Name:{0}'.format(part.name)

	ml = create_mount_list('f:\\develop\\mountData.txt')
	print len(ml)
	for key,value in ml.items():
		print 'LayerName:{0}'.format(key)
		for d in value:
			print 'N:{0} X={1} Y={2} R={3}'.format(d.name,d.xPos,d.yPos,d.angle)


	exist_parts(partsList,ml['Layer1'])
