#-*- coding: UTF-8 -*-
u""" vect ﾌｧｲﾙを読み込んで[(x1,y1,x2,y2)]のﾘｽﾄﾃﾞｰﾀを生成する
	chkVect.py で使用中
"""

import re
import sys
import math

#
# vect ﾃﾞｰﾀ
#   vect ﾌｧｲﾙを読み込んで [(x1,y1,x2,y2)] のﾘｽﾄを生成
#   ｲﾃﾚｰﾀｰ、[] を使用することで各ﾗｲﾝにｱｸｾｽします
#    ex.)
#       vect = VectData('aaa.vect')
#       for vv in vect:
#           vv ==> (x1,y1,x2,y2)
#
#       vv = vect[2],  vect[2] = (10.1, 20.1, 30.1, 40.1)
#
class VectData():
	def __init__(self, vecFile):
		self.fileName = vecFile
		self.vecList = laser_vect(vecFile)
		self.index = 0

	def __iter__(self):
		self.index = 0
		return self

	def next(self):
		if self.index == len(self.vecList):
			raise StopIteration()
		val = self.vecList[self.index]
		self.index += 1
		return val

	def __getitem__(self, i):
		if i < 0 or i > len(self.vecList):
			return None
		return self.vecList[i]

	def __setitem__(self, i, val):
		if i < 0 or i > len(self.vecList) + 1:
			return False
		elif i > len(self.vecList):
			self.vecList.append(val)
		else:
			self.vecList[i]	= val
		return True

	def get_list(self, ofx=0.0, ofy=0.0):
		return [(vec[0]-ofx,vec[1]-ofy,vec[2]-ofx,vec[3]-ofy) for vec in self.vecList]

#
#
#  file : vect ﾌｧｲﾙ
#   ofx : ﾍﾞｸﾄﾙﾃﾞｰﾀ・ｽﾃｰｼﾞｵﾌｾｯﾄX
#   ofy : ﾍﾞｸﾄﾙﾃﾞｰﾀ・ｽﾃｰｼﾞｵﾌｾｯﾄY
#
def laser_vect(file, ofx = 0.0, ofy= 0.0):
	f = open(file,'r')
	data = f.read()
	f.close()

	ret = []
	lines = data.split('\n')

	cmd = re.compile('^[A-Z]+')
	val = re.compile('[\d+-]+\.?\d*')
	for ln in lines:
		cmd_str = cmd.findall(ln)
		if len(cmd_str) == 0 or cmd_str[0] == 'LISTSTART' or cmd_str[0] == 'LISTEND' or cmd_str[0] == '':
			pass
		else:
			val_str = val.findall(ln)
			#print '[{0}]::({1},{2})'.format(cmd_str[0],val_str[0],val_str[1])
			if cmd_str[0] == 'JUMP':
				x1 = float(val_str[0]) - ofx
				y1 = float(val_str[1]) - ofy
			elif cmd_str[0] == 'MARK':
				x2 = float(val_str[0]) - ofx
				y2 = float(val_str[1]) - ofy
				ret.append( (x1,y1,x2,y2) )
			else:
				pass

	return ret

#
#
#     vec:float(x1,y1,x2,f2)
# dottLen:float
#
def pos2Pixel(vec, dottLen, ofx=0.0, ofy=0.0):
	px1 = int((vec[0] - ofx) / dottLen)
	py1 = int((vec[1] - ofy) / dottLen)

	xl = (vec[2] - ofx) - (vec[0] - ofx)
	yl = (vec[3] - ofy) - (vec[1] - ofy)

	px2 = int(xl / dottLen)
	py2 = int(yl / dottLen)

	return( (px1,py1,px2,py2))

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print 'usage:{0} <vect File>\n'.format(sys.argv[0])
		exit(0)

	vec = laser_vect( sys.argv[1] )
	print vec
