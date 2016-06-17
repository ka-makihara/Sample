# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        moveLib
# Purpose:     軸移動・干渉回避動作ﾗｲﾌﾞﾗﾘ
#
# Author:      makihara
#
# Created:     27/04/2015
# Copyright:   (c) makihara 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import math
import copy

ROBOT_AREA	= 0
CRUSH_AREA = 1
ESC_PICK_AREA1 = 2
ESC_PICK_AREA2 = 3
ESC_PLACE_AREA1 = 4
ESC_PLACE_AREA2 = 5
CARRY_AREA = 6
PLACE_AREA = 7
PICK_AREA = 8
OUT_OF_AREA = 255

#移動座標クラス
class MovePos:
	def __init__( self, xx=0, yy=0, zz=0, qq=0, ll=0 ):
		self.x = xx
		self.y = yy
		self.z = zz
		self.q = qq
		self.l = ll
	#座標設定
	def set( self, xx, yy, zz, qq, ll ):
		self.x = xx
		self.y = yy
		self.z = zz
		self.q = qq
		self.l = ll
	#画像処理補正
	def correction( self, retList ):
		self.x = self.x + retList[0]
		self.y = self.y + retList[1]
		self.q = (self.q + retList[2])

#直線が交差するか
def line_line(A1x,A1y,A2x,A2y, B1x,B1y,B2x,B2y):
	bX = B2x - B1x
	bY = B2y - B1y
	sx1 = A1x - B1x
	sy1 = A1y - B1y
	sx2 = A2x - B1x
	sy2 = A2y - B1y

	bs1 = bX * sy1 - bY * sx1
	bs2 = bX * sy2 - bY * sx2
	rr = bs1 * bs2
	if rr > 0:
		return False

	bX = A2x - A1x
	bY = A2y - A1y
	sx1 = B1x - A1x
	sy1 = B1y - A1y
	sx2 = B2x - A1x
	sy2 = B2y - A1y

	bs1 = bX * sy1 - bY * sx1
	bs2 = bX * sy2 - bY * sx2
	rr = bs1 * bs2
	if rr > 0:
		return False

	return True



# 矩形座標
class RectArea:
	def __init__(self, x1,y1,x2,y2,emg):
		self.left = min(x1,x2)
		self.top = min(y1,y2)
		self.right = max(x1,x2)
		self.bottom = max(y1,y2)
		self.emg = emg

	def IsIn(self,xx,yy):
		fx = xx / 10000.0
		fy = yy / 10000.0
		if self.left <= fx <= self.right:
			if self.top <= fy <= self.bottom:
				return True

		return False

	#
	# 矩形と線分の交差判定
	#
	def HitTest(self, x1,y1, x2,y2):
		fx1 = x1 / 10000.0
		fy1 = y1 / 10000.0
		fx2 = x2 / 10000.0
		fy2 = y2 / 10000.0
		if line_line(self.left,self.top,self.right,self.top,fx1,fy1,fx2,fy2) == True:
			return True
		if line_line(self.right,self.top,self.right,self.bottom,fx1,fy1,fx2,fy2) == True:
			return True
		if line_line(self.right,self.bottom,self.left,self.bottom,fx1,fy1,fx2,fy2) == True:
			return True
		if line_line(self.left,self.bottom,self.left,self.top,fx1,fy1,fx2,fy2) == True:
			return True


#円座標
class CircleArea:
	def __init__(self, xx, yy, rLen, emg):
		self.centerX = xx
		self.centerY = yy
		self.rLen = rLen
		self.emg = emg

	def IsIn(self,xx,yy):
		fx = xx / 10000.0
		fy = yy / 10000.0
		ll = (self.centerX - fx) ** 2 + (self.centerY - fy) ** 2
		if (self.rLen ** 2) >= ll:
			return( True )

		return False

	def Distance(self, x, y):
		ll = math.sqrt(math.pow(x-self.centerX,2) + math.pow(y-self.centerY,2))
		return ll

	#
	# 円と線分{(x1,y1)-(x2,y2)}の交差判定
	#
	# 線分の始点から終点へのﾍﾞｸﾄﾙを V、 線分の始点から球の中心へのﾍﾞｸﾄﾙを C とします。 
	# V・C<0 の時、球の中心が線分の始点よりも線分から遠くにあるので、
	# C の長さが球の半径よりも小さければ交差と判定します。 
	# V・C≧0 の時、V・C と V2 の長さを比べます (V 方向での C の長さと V の比較)。 
	# V・C の方が大きければ、円の中心が線分の終点よりも線分から遠くにあるので、 
	# 線分の終点と円の中心の距離の 2 乗を求めて、 円の半径の 2 乗よりも小さければ交差と判定します。 
	# V2 の方が大きければ、円の中心から線分に降ろした足が線分上に 存在するはずです。
	# C2-(V・c/V2)*V・c でその長さの 2 乗が分かり、 円の半径の 2 乗よりも小さければ交差と判定します。
	#
	def HitTest(self, x1,y1, x2,y2):
		fx1 = x1 / 10000.0
		fy1 = y1 / 10000.0
		fx2 = x2 / 10000.0
		fy2 = y2 / 10000.0

		#始点から終点へのﾍﾞｸﾄﾙ:V
		vx = fx2 - fx1
		vy = fy2 - fy1

		#始点から円中心へのﾍﾞｸﾄﾙ:C
		cx = self.centerX - fx1
		cy = self.centerY - fy1

		#二つのﾍﾞｸﾄﾙの内積
		n1 = vx * cx + vy * cy
		n2 = vx * vx + vy * vy

		if n2 == 0:
			#始点と終点が同じなら座標が円内かどうか
			return self.IsIn(x1,y1)

		if n1 < 0:
			ll = self.Distance(fx1,fy1)
			if ll < self.rLen:
				#C(始点から中心へのﾍﾞｸﾄﾙ)が円の半径より小さいなら交差
				return True
			return False

		if n1 > n2:
			#終点と円の中心の距離の二乗
			ll = math.pow( self.Distance(fx2,fy2),2)
			if ll < math.pow(self.rLen,2):
				#円の半径の二乗よりも小さいなら交差
				return True
			else:
				return False
		else:
			n3 = cx * cx + cy * cy
			nn = n3 - (n1/n2) * n1 
			r2 = math.pow(self.rLen,2)
			if nn < r2:
				return True
			else:
				return False


def sv_mm(pos):
	return (pos * 10000)

#################################################################
#
#ｴﾘｱﾘｽﾄ
#  (X1,Y1)-(X2,Y2),移動不可ﾌﾗｸﾞ::[左上-右下]
#
#areaInfo = [CircleArea(0.00,0.00,250.00,1),				#ﾛﾎﾞｯﾄｴﾘｱ
#			RectArea( -270.00, 305.00, 270.00, 330.00,1),	#干渉ｴﾘｱ
#			RectArea(    0.00,   0.00, 270.00, 270.00,0),	#要退避吸着ｴﾘｱ1
#        	RectArea(    0.00,-270.00, 270.00,   0.00,0),	#要退避吸着ｴﾘｱ2
#            RectArea( -270.00,   0.00,   5.00, 270.00,0),	#要退避装着ｴﾘｱ1
#            RectArea( -270.00,-270.00,   0.00,   0.00,1),	#要退避装着ｴﾘｱ2
#            RectArea( -270.00, 270.00, 270.00, 305.00,0),	#搬送ｴﾘｱ
#            RectArea( -540.00,   5.00,-270.00, 330.00,0),	#装着ｴﾘｱ
#            RectArea(  270.00,-270.00, 640.00, 330.00,0)]	#吸着ｴﾘｱ

areaInfo = [CircleArea(0.00,0.00,250.00,1),				#ﾛﾎﾞｯﾄｴﾘｱ
			CircleArea(0.00,0.00,250.00,1),					#干渉ｴﾘｱ
			RectArea(    0.00,    0.00, 270.00, -270.00,0),	#要退避吸着ｴﾘｱ1
        	RectArea(    0.00,  270.00, 270.00,    0.00,0),	#要退避吸着ｴﾘｱ2
            RectArea( -270.00,    0.00,   5.00, -270.00,0),	#要退避装着ｴﾘｱ1
            RectArea( -270.00,  270.00,   0.00, -270.00,1),	#要退避装着ｴﾘｱ2
            RectArea(  150.00, -270.00, 270.00, -305.00,0),	#搬送ｴﾘｱ
            RectArea( -135.00, -270.00, 150.00, -550.00,0),	#装着ｴﾘｱ
            RectArea(  270.00,  270.00, 640.00, -330.00,0)]	#吸着ｴﾘｱ

#
#移動不可ｴﾘｱ
#  現在値-目的地を結ぶ直線はこのｴﾘｱを通過することはできない
#emgArea = [CircleArea(0.00,0.00,250.00,1),					#ﾛﾎﾞｯﾄｴﾘｱ
#			RectArea( -270.00, 305.00, 270.00, 330.00,1),	#干渉ｴﾘｱ
#            RectArea( -270.00,-270.00,   0.00,   5.00,1)]	#要退避装着ｴﾘｱ2

emgArea = [CircleArea(0.00,0.00,250.00,1),					#ﾛﾎﾞｯﾄｴﾘｱ
            RectArea( -270.00, 270.00,   0.00, -270.00,1)]	#要退避装着ｴﾘｱ2

#
# 軸ﾘﾐｯﾄ
#
axisLimit = {"Z":[-900000,1000000],"A":[1300000,1500000],"B":[-1800000,1800000]}

###################################################################
#
# ｴﾘｱ番号の取得
#
def GetAreaNo(xx, yy):
	index = 0
	for pos in areaInfo:
		if pos.IsIn(xx,yy) == True:
			return index

		index = index + 1

	return OUT_OF_AREA 

def is_ok_area(xx,yy):
	areaNo = GetAreaNo(xx,yy)
	if areaNo == OUT_OF_AREA:
		return False

	if areaInfo[areaNo].emg == 1:
		return False

	return True

##################################################################
#
# 線分([x1,y1]-[x2,y2])が移動不可ｴﾘｱと交差するか(True)
#
def HitArea(x1,y1,x2,y2):
	for pos in emgArea: 
		if pos.HitTest(x1,y1,x2,y2) == True:
			return	True 

	return False

##################################################################
#
# ｴﾘｱ番号名(ﾃﾞﾊﾞｯｸﾞ用)
#
def areaName(no):
	if no == ROBOT_AREA:
		return u"ﾛﾎﾞｯﾄｴﾘｱ"
	elif no == CRUSH_AREA:
		return u"干渉ｴﾘｱ"
	elif no == ESC_PICK_AREA1:
		return u"要退避吸着ｴﾘｱ1"
	elif no == ESC_PICK_AREA2:
		return u"要退避吸着ｴﾘｱ2"
	elif no == ESC_PLACE_AREA1:
		return u"要退避装着ｴﾘｱ1"
	elif no == ESC_PLACE_AREA2:
		return u"要退避装着ｴﾘｱ2"
	elif no == CARRY_AREA:
		return u"搬送ｴﾘｱ"
	elif no == PLACE_AREA:
		return u"装着ｴﾘｱ"
	elif no == PICK_AREA:
		return u"吸着ｴﾘｱ"
	else:
		return u"undefined"

######################################################################

#移動リストに追加
def append_moveList(appendDict, speed, moveList):
	if len(appendDict) != 0:
		if speed != 0:
			appendDict['F'] = speed
		moveList.append(appendDict.copy())

######################################################################

# 装着退避位置移動
def move_esc_place(speed, moveList):
	if speed == 0:
		moveList.append({"X":-2700000,"Y":2700000})
	else:
		moveList.append({"X":-2700000,"Y":2700000,"F":speed})

# 装着搬送位置移動
def move_place_carry(speed, moveList):
	if speed == 0:
#		moveList.append({"X":-2700000,"Y":2880000})
		moveList.append({"X":1500000,"Y":-2880000})
	else:
#		moveList.append({"X":-2700000,"Y":2880000,"F":speed})
		moveList.append({"X":1500000,"Y":-2880000,"F":speed})

# 吸着搬送位置移動
def move_pick_carry(speed, moveList):
	if speed == 0:
		moveList.append({"X":2700000,"Y":-2880000})
	else:
		moveList.append({"X":2700000,"Y":-2880000,"F":speed})

# 吸着退避位置移動
def move_esc_pick(speed, moveList):
	if speed == 0:
		moveList.append({"X":2700000,"Y":2700000})
	else:
		moveList.append({"X":2700000,"Y":2700000,"F":speed})

######################################################################

def G_1(tgtArea, speed, moveList):
	move_esc_place(speed, moveList)		#装着退避位置へ移動
	if tgtArea == ESC_PLACE_AREA2:
		return 0						#目標位置へ移動
	else:
		return -5

def F_1(tgtArea, speed, moveList):
	if tgtArea == PLACE_AREA:
		return 0						#目標位置へ移動
	else:
		return( G_1(tgtArea,speed,moveList) )

def E_1(tgtArea, speed, moveList):
	move_place_carry(speed,moveList)	#装着搬送位置へ移動
	if tgtArea == ESC_PLACE_AREA1:
		return 0						#目標位置へ移動
	else:
		return( F_1(tgtArea,speed,moveList) )

def D_1(tgtArea, speed, moveList):
	if tgtArea == CARRY_AREA:
		return 0						#目標位置へ移動
	else:
		return( E_1(tgtArea,speed,moveList) )

def C_1(tgtArea, speed, moveList):
	move_pick_carry(speed,moveList)		#吸着搬送位置へ移動
	if tgtArea == ESC_PICK_AREA1:
		return 0						#目標位置へ移動
	else:
		return( D_1(tgtArea,speed,moveList) )

def B_1(tgtArea, speed, moveList):
	if tgtArea == PICK_AREA:
		return 0						#目標位置へ移動
	else:
		return( C_1(tgtArea,speed,moveList) )

def A_1(tgtArea, speed, moveList):
	move_esc_pick(speed,moveList)		#吸着退避位置へ移動
	if tgtArea == ESC_PICK_AREA2:
		return 0						#目標位置へ移動
	else:
		return( B_1(tgtArea,speed,moveList) )

#################################################################

def A_2(tgtArea, speed, moveList):
	move_esc_pick(speed,moveList)		#吸着退避位置へ移動
	if tgtArea == ESC_PICK_AREA2:
		return 0						#目標位置へ移動
	else:
		return -6

def B_2(tgtArea, speed, moveList):
	if tgtArea == PICK_AREA:
		return 0						#目標位置へ移動
	else:
		return( A_2(tgtArea,speed,moveList) )

def C_2(tgtArea, speed, moveList):
	move_pick_carry(speed,moveList)		#吸着搬送位置へ移動
	if tgtArea == ESC_PICK_AREA1:
		return 0						#目標位置へ移動
	else:
		return( B_2(tgtArea,speed,moveList) )

def D_2(tgtArea, speed, moveList):
	if tgtArea == CARRY_AREA:
		return 0						#目標位置へ移動
	else:
		return( C_2(tgtArea,speed,moveList) )

def E_2(tgtArea, speed, moveList):
	move_place_carry(speed,moveList)	#装着搬送位置へ移動
	if tgtArea == ESC_PLACE_AREA1:
		return 0						#目標位置へ移動
	else:
		return( D_2(tgtArea,speed,moveList) )

def F_2(tgtArea, speed, moveList):
	if tgtArea == PLACE_AREA:
		return 0						#目標位置へ移動
	else:
		return( E_2(tgtArea,speed,moveList) )

def G_2(tgtArea, speed, moveList):
	move_esc_place(speed,moveList)		#装着退避位置へ移動
	if tgtArea == ESC_PLACE_AREA2:
		return 0						#目標位置へ移動
	else:
		return( F_2(tgtArea,speed,moveList) )

##################################################################

def root_select(curX, curY, tgtX, tgtY, rootCode):
	curAreaNo = GetAreaNo(curX,curY)
	tgtAreaNo = GetAreaNo(tgtX,tgtY)

	if tgtAreaNo == ESC_PICK_AREA2:
		return rootCode[0]
	if tgtAreaNo == ESC_PICK_AREA2:
		return rootCode[1]
	elif tgtAreaNo == PICK_AREA:
		return rootCode[2] 
	elif tgtAreaNo == ESC_PICK_AREA1:
		return rootCode[3]
	elif tgtAreaNo == CARRY_AREA:
		return rootCode[4]
	elif tgtAreaNo == ESC_PLACE_AREA1:
		return rootCode[5] 
	elif tgtAreaNo == PLACE_AREA:
		return rootCode[6]
	elif tgtAreaNo == ESC_PLACE_AREA2:
		return rootCode[7]
	else:
		return -3

def root(curX,curY,tgtX, tgtY, speed, moveList):
	curAreaNo = GetAreaNo(curX,curY)
	tgtAreaNo = GetAreaNo(tgtX,tgtY)

#	print u"現在値(%d,%d)=%s --> 目的値(%d,%d)=%s" % (curX,curY, areaName(curAreaNo),tgtX,tgtY, areaName(tgtAreaNo))

	#ｴﾘｱ外への移動は不可
	if tgtAreaNo == OUT_OF_AREA:
		return -1

	#目的位置が干渉ｴﾘｱ内である場合
	if areaInfo[tgtAreaNo].emg == 1:
		return -1

	#
	if curAreaNo == ESC_PICK_AREA2:		#要退避吸着ｴﾘｱ2
		rootNo = root_select(curX,curY,tgtX,tgtY,[2,1,1,1,1,1,1,1])
		if rootNo == 2:
			return( A_2(tgtAreaNo, speed, moveList) )
		elif rootNo == 1:
			return( A_1(tgtAreaNo, speed, moveList) )

	elif curAreaNo == PICK_AREA:		#吸着ｴﾘｱ
		rootNo = root_select(curX,curY,tgtX,tgtY,[2,2,1,1,1,1,1,1])
		if rootNo == 2:
			return( B_2(tgtAreaNo, speed, moveList) )
		elif rootNo == 1:
			return( B_1(tgtAreaNo, speed, moveList) )

	elif curAreaNo == ESC_PICK_AREA1:	#要退避吸着ｴﾘｱ1
		rootNo = root_select(curX,curY,tgtX,tgtY,[2,2,2,1,1,1,1,1])
		if rootNo == 2:
			return( C_2(tgtAreaNo, speed, moveList) )
		elif rootNo == 1:
			return( C_1(tgtAreaNo, speed, moveList) )

	elif curAreaNo == CARRY_AREA:		#搬送ｴﾘｱ
		rootNo = root_select(curX,curY,tgtX,tgtY,[2,2,2,2,1,1,1,1])
		if rootNo == 2:
			return( D_2(tgtAreaNo, speed, moveList) )
		elif rootNo == 1:
			return( D_1(tgtAreaNo, speed, moveList) )

	elif curAreaNo == ESC_PLACE_AREA1:	#要退避装着ｴﾘｱ1
		rootNo = root_select(curX,curY,tgtX,tgtY,[2,2,2,2,2,1,1,1])
		if rootNo == 2:
			return( E_2(tgtAreaNo, speed, moveList) )
		elif rootNo == 1:
			return( E_1(tgtAreaNo, speed, moveList) )

	elif curAreaNo == PLACE_AREA:		#装着ｴﾘｱ
		rootNo = root_select(curX,curY,tgtX,tgtY,[2,2,2,2,2,2,1,1])
		if rootNo == 2:
			return( F_2(tgtAreaNo, speed, moveList) )
		elif rootNo == 1:
			return( F_1(tgtAreaNo, speed, moveList) )

	elif curAreaNo == ESC_PLACE_AREA2:	#要退避装着ｴﾘｱ2
		rootNo = root_select(curX,curY,tgtX,tgtY,[2,2,2,2,2,2,2,1])
		if rootNo == 2:
			return( G_2(tgtAreaNo, speed, moveList) )
	else:
		return -7

##########################################################

def create_root(curX, curY, tgtX, tgtY, speed, moveList):
	ret = root(curX,curY,tgtX,tgtY,speed,moveList)
	if ret == 0:
		#最終目的地
		if speed == 0:
			moveList.append( {"X":tgtX, "Y":tgtY} )
		else:
			moveList.append( {"X":tgtX, "Y":tgtY,"F":speed} )
	else:
		return ret
	return 0


##########################################################
#
# 回転系(A,B)の動作指令の生成
#  dict:{"X":xxxx,...} => 目標位置
#  svPos: [0]=X,[1]=Y,[2]=Z,[3]=A,[4]=B => 現在位置
#  rotate_deg: X,Yの移動によって発生する角度移動量
#   ※X,Yの移動がない場合は呼び出されない
#
def create_rotation(dict, svPos, rotate_deg, speed, moveList):
	#角度補正
	if dict.has_key('B') == True:
		#角度指定がある
		tgtB_deg = int(dict['B'] + rotate_deg * 10000.0)
	else:
		#角度指定がない
		tgtB_deg = int(svPos[5] + rotate_deg * 10000.0)

	#指定角度の丸め込み
	if tgtB_deg > 0:
		tgtB_deg = (tgtB_deg + 1800000) % 3600000 - 1800000
	else:
		sub = -((abs(tgtB_deg) + 1800000) % 3600000)
		tgtB_deg = sub + 1800000

	if dict.has_key('A') == True or dict.has_key('B') == True:
		if dict.has_key('A') == True:
			#R軸の指定がある
			if speed == 0:
				moveList.append({"A":dict['A'],"B":tgtB_deg})
			else:
				moveList.append({"A":dict['A'],"B":tgtB_deg,"F":speed})
		else:
			#L軸のみ
			if speed == 0:
				moveList.append({"B":tgtB_deg})
			else:
				moveList.append({"B":tgtB_deg,"F":speed})
	else:
		#回転系の指示は無い(移動前の回転位置へ)
		if speed == 0:
			moveList.append({"B":tgtB_deg})
		else:
			moveList.append({"B":tgtB_deg,"F":speed})

rotatePos = [3000000,0,0,0,0]	#基準位置
# 基準位置が0度の場合の指定位置のBの角度を取得
def get_rotate_deg(tgtX, tgtY):
	rad1 = math.atan2(rotatePos[1],rotatePos[0])
	rad2 = math.atan2(tgtY,tgtX)
	rotate_deg = (rad2 - rad1) * 180.0 / math.pi
	return rotate_deg


def limit_check(dict):
	if dict.has_key('Z') == True:
		lm = axisLimit['Z']
		if dict['Z'] < lm[0] or dict['Z'] > lm[1]:
			return False
	if dict.has_key('A') == True:
		lm = axisLimit['A']
		if dict['A'] < lm[0] or dict['A'] > lm[1]:
			return False
	if dict.has_key('B') == True:
		lm = axisLimit['B']
		if dict['B'] < lm[0] or dict['B'] > lm[1]:
			return False
	return True

##########################################################
#
# X,Y,Z用の回避動作ﾙｰﾄ生成
#  dict:{"X":xxxx,...} => 目標位置
#  svPos: [0]=X,[1]=Y,[2]=Z,[3]=A,[4]=B => 現在位置
#
def create_xyz_root(dict, svPos, moveList):
	rotate_deg 	= 0.0
	speed 		= 0
	targetPosDict = {}	#append用dict

	if dict.has_key('F') == True:
		speed = dict['F']

##	安全高さZへ移動
	if dict.has_key('X') == True or dict.has_key('Y') == True:
		#X,Yの移動がある場合はZ軸を安全高さへ移動
		targetPosDict.clear()	#dictを空に
		targetPosDict['Z'] = setting.SaftyPosZ;
		#リストに追加
		append_moveList(targetPosDict,speed,moveList)

##	指定位置XYABへ移動
	targetPos 	= svPos[:2]	#目標位置XY 現在位置で初期化
	if dict.has_key('X') == True:
		targetPos[0] = dict['X']
	if dict.has_key('Y') == True:
		targetPos[1] = dict['Y']

	if setting.SvCtrlName == "TECHNO":
		## XY移動を追加
		ret = create_root(svPos[0],svPos[1],targetPos[0],targetPos[1],speed,moveList)
		if ret != 0:
			return -3

		## XY移動で回転したBを考慮してAB移動をリストに追加
		create_rotation(dict,svPos,rotate_deg,speed,moveList)

	else:
		if dict.has_key('X') == True or dict.has_key('Y') == True:
			#干渉回避移動XYを設定
			ret = root(svPos[0],svPos[1],targetPos[0],targetPos[1],speed,moveList)
			if ret != 0:
				return -3
		
		#XY(AB)移動を設定
		targetPosDict.clear()	#dictを空に
		if dict.has_key('X') == True:
			targetPosDict['X'] = dict['X']
		if dict.has_key('Y') == True:
			targetPosDict['Y'] = dict['Y']
		if setting.ModeMoveLQ == 0:	#XY同時移動の場合はABの設定
			if dict.has_key('A') == True:
				targetPosDict['A'] = dict['A']
			if dict.has_key('B') == True:
				targetPosDict['B'] = dict['B']
		#リストに追加
		append_moveList(targetPosDict,speed,moveList)

		#AB移動を設定
		if setting.ModeMoveLQ != 0:	#個別移動
			#A移動を設定
			targetPosDict.clear()	#dictを空に
			if dict.has_key('A') == True:
				targetPosDict['A'] = dict['A']			
			#リストに追加
			append_moveList(targetPosDict,speed,moveList)

			#Bを設定
			targetPosDict.clear()	#dictを空に
			if dict.has_key('B') == True:
				targetPosDict['B'] = dict['B']			
			#リストに追加
			append_moveList(targetPosDict,speed,moveList)			


##	指定高さZへ移動
	#Zを設定
	targetPosDict.clear()	#dictを空に
	if dict.has_key('Z') == True:
		#Z軸の移動指示がある場合は指定された位置へ
		targetPosDict['Z'] = dict['Z'];
	else:
		#Z軸の移動指示がない場合
		if dict.has_key('X') == True or dict.has_key('Y') == True:
			#X,Yの移動指示があった場合はZが安全高さに移動しているので、元に戻す
			targetPosDict['Z'] = svPos[2];
	#リストに追加
	append_moveList(targetPosDict,speed,moveList)

	return 0

