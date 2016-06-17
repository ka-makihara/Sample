#-*- coding: UTF-8 -*-

#
# Rowthon ｻｰﾎﾞ ﾗｲﾌﾞﾗﾘ
#
#import clr
import time

# C# のﾃﾞｨｸｼｮﾅﾘを使用するためのﾗｲﾌﾞﾗﾘ
#clr.AddReference('System.Collections')
#from System.Collections import Generic as DotNetCollectionsG

import traceLib
import moveLib

#
import Rowthon

version = 1.00
CURRENT_POS	= 0	#現在値
ERROR_INFO  = 1 #ｴﾗｰ情報
POWER_INFO  = 2 #電源情報

PARAM_MAX_SPD	= 2
PARAM_JOG_SPD	= 4


AXIS_X = 0
AXIS_Y = 1
AXIS_Z = 2
AXIS_A = 3
AXIS_B = 4
AXIS_R = AXIS_A
AXIS_Q = AXIS_B
AXIS_XYZ = 5
AXIS_QR = 6


def move_string(pos):
	cmd_msg = ""

	if pos.has_key('X') == True:
		cmd_msg = cmd_msg + '"X"' + ':{0},'.format(pos['X'])

	if pos.has_key('Y') == True:
		cmd_msg = cmd_msg + '"Y"' + ':{0},'.format(pos['Y'])

	if pos.has_key('Z') == True:
		cmd_msg = cmd_msg + '"Z"' + ':{0},'.format(pos['Z'])

	if pos.has_key('A') == True:
		cmd_msg = cmd_msg + '"A"' + ':{0},'.format(pos['A'])

	if pos.has_key('B') == True:
		cmd_msg = cmd_msg + '"B"' + ':{0},'.format(pos['B'])

	return cmd_msg

#
# 初期化
#
def init(motionName):
	'''ｻｰﾎﾞ初期化
	params:('制御名')
		TECHNO or LINSEY
	return: ID'''
	ret = Rowthon.send_recv_msg('servo.init({0});'.format(motionName))
	return ret._retCode

#'
# 軸の移動(回避動作付き)
#  <dict> {"X":xxxx, "Y":yyyy, ...}
#   lerp : 空間補正 有(=1) 無(=0) ﾃﾞﾌｫﾙﾄに従う(=-1)
#
def move(dict, lerp=-1):
	''' ｻｰﾎﾞ移動:回避動作付き
	param :(dict,lerp)
	    dict  :({"AxisName":<pos>,"AxisName":<pos>,...})
        rerp  :空間補正 有(=1) 無(=0) ﾃﾞﾌｫﾙﾄに従う(=-1)
	return:wait Id'''
	#msg = 'servo.move({' + move_string(dict) + '},' + 'lerp={0});'.format(lerp)

	ret = Rowthon.send_recv_msg( 'servo.move({' + move_string(dict) + '},' + 'lerp={0});'.format(lerp))
	return ret._retCode

#
# 軸の移動(回避動作無し)
#  <dict> {"X":xxxx, "Y":yyyy, ...}
#
def move_unsafe(dict):
	''' ｻｰﾎﾞ移動:回避動作無し
	param :({"AxisName":<pos>,"AxisName":<pos>,...})
	return:wait Id'''
	ret = Rowthon.send_recv_msg( 'servo.move_unsafe({' + move_string(dict) + '});')
	return ret._retCode
#
# ﾊﾟﾗﾒｰﾀ設定
#
def set_param(axisNo, code, data):
	'''ﾊﾟﾗﾒｰﾀ設定
	params: (axisNo,code,data)
	    axisNo:0～
	    code  :MoveSpeed=2 JogSpeed=4
	return: OK=0 ERR<0'''
	ret = Rowthon.send_recv_msg('servo.set_param({0},{1},{2});'.format(axisNo-1,code,data))
	return ret._retCode
	
#
# ﾊﾟﾗﾒｰﾀ取得
#
def get_param(axisNo, code):
	'''ﾊﾟﾗﾒｰﾀ取得
	params:(axisNo,code)
		axisNo:0～
		code:MoveSpeed=2 JogSpeed=4
	return: value or ERR<0'''
	ret = Rowthon.send_recv_msg('servo.get_param({0},{1});'.format(axisNo-1,code))
	return ret._retCode

#
# 状態取得
#
def get_status(axisNo, code):
	'''ｻｰﾎﾞ状態取得
	params:(axisNo,code)
	  axisNo:0～
	  code  :
	return:value'''
	ret = Rowthon.send_recv_msg('_result=servo.get_status({0},{1})\n_result;'.format(axisNo-1,code))
	return ret._retCode

#
# 軸動作中止
#
def stop_move(eventId):
	'''移動中止
	params:(Id)
	  Id:move()の戻り値
	return: OK=0 ERR<0'''
	ret = Rowthon.send_recv_msg('servo.stop_move({0});'.format(eventId))
	return ret._retCode

#
# JOG 動作
#
def jog(axisNo, direction, spd):
	'''JOG動作(axisNo,direction,speed)
	 axisNo   :0～
	 direction:-1=-方向,0=停止,1=+方向
	 speed    :速度
	 return: OK=0 ERR<0'''
	ret = Rowthon.send_recv_msg('servo.jog({0},{1},{2});'.format(axisNo-1,direction,spd) )
	return ret._retCode

#
# ｻｰﾎﾞ電源
#
def power(onOff):
	'''ｻｰﾎﾞ電源のON/onOff
	params:(ON=1, OFF=0)
	return: OK=0 ERR<0'''
	ret = Rowthon.send_recv_msg('servo.power({0});'.format(onOff))
	return ret._retCode

#
#  return: [X,Y,Z,A,B]
def get_pos_list():
	xPos = Rowthon.send_recv_msg('_result=servo.get_status(0,0)\n_result;')
	yPos = Rowthon.send_recv_msg('_result=servo.get_status(1,0)\n_result;')
	zPos = Rowthon.send_recv_msg('_result=servo.get_status(2,0)\n_result;')
	aPos = Rowthon.send_recv_msg('_result=servo.get_status(3,0)\n_result;')
	bPos = Rowthon.send_recv_msg('_result=servo.get_status(4,0)\n_result;')

	return [xPos._retCode,yPos._retCode,zPos._retCode,aPos._retCode,bPos._retCode]
