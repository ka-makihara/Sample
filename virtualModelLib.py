#-*- coding: UTF-8 -*-

#
# ｽｸﾘﾌﾟﾄﾃﾞﾊﾞｯｸﾞ用のﾀﾞﾐｰﾗｲﾌﾞﾗﾘ
#

import sys
import time

import Rowthon

def PyTrace(funcName,msg):
	print '{0}:{1}'.format(funcName,msg)

def StopMove(eventId):
	pass
	return 0

def ServoJog(axisNo,direction,spd):
	pass
	return

def IoOut(port,bit,onoff):
	pass
	return 0

def GetStatus():
	return 0

def GetCtrlMode():
	return 0

def SetCtrlMode(mode):
	return 0

def ClearError():
	return 0

def EventStatus(eventId):
	return 0

def CancelWait(eventId):
	return 0

def GetProgramResult(resultName):
	return 0

def StopProgram(eventId):
	return 0

def GetMsgEventID():
	return 0
