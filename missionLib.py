#-*- coding: UTF-8 -*-

import time
import ctypes
import ctypes.wintypes as winTypes

import missionCode
import winApi

import System
from System.Diagnostics import Process,ProcessStartInfo

import ctrlLib as ctrl

hWnd = winApi.FindWindow('0016_IMAGING')
#hWnd = winApi.FindWindow('無題 - メモ帳')
#hWnd = winApi.FindWindow('PyMsgTest')
hOwnWnd = winApi.FindWindow('Rowthon')

#print hWnd
IMAGING_TASK_NAME = '0016_IMAGING'

#
# Windowsﾒｯｾｰｼﾞ(WM_COPYDATA)を使用して任意ｻｲｽﾞのﾃﾞｰﾀを送信する
#   ※WM_COPYDATA では、Windowsが内部で共有ﾒﾓﾘ(?)的な事を行ってくれるので
#     ﾛｰｶﾙ変数のﾒﾓﾘを渡してもよい
#
#
def send_copy_msg(windowName, missionData, dwData):
	copyData = winApi.COPYDATASTRUCT()
	copyData.dwData = dwData
	copyData.cbData = ctypes.sizeof(missionData)
	copyData.lpData = ctypes.cast(ctypes.pointer(missionData),ctypes.c_void_p)
	
	hWnd = winApi.FindWindow(windowName)

	if hWnd != None:
		winApi.SendMessage(hWnd,winApi.WM_COPYDATA,hOwnWnd,ctypes.cast(ctypes.pointer(copyData),winTypes.c_void_p).value)
	else:
		print "{0}Window Not Found".format(windowName)
		return -1

	return 0

#
# ﾐｯｼｮﾝの実行結果の受け取り
#   最後のﾐｯｼｮﾝの結果がｱﾌﾟﾘ側に保持されているので、ﾀﾌﾟﾙで取得して
#   ｸﾗｽに代入してﾘﾀｰﾝする
#
def get_mission_ret():
	data = missionCode.SendMissionArg()
	(tr_id,no,ret,sp,arg1,arg2,arg3,arg4,arg5,arg6) = Vision.GetMissionRet()

	data.transaction_id = tr_id
	data.CommandNo = no
	data.result = ret
	data.spare = sp
	data.arg1 = arg1
	data.arg2 = arg2
	data.arg3 = arg3
	data.arg4 = arg4
	data.arg5 = arg5
	data.arg6 = arg6

	print "ID:{0} No:{1} R:{2} 1:{3} 2:{4} 3:{5} 4:{6} 5:{7}".format(data.transaction_id,data.CommandNo,data.result,data.arg1,data.arg2,data.arg3,data.arg4,data.arg6)

	return data

#
# ﾐｯｼｮﾝ送信
#
def send_mission(tr_id, cmd, arg1=0, arg2=0, arg3=0, arg4=0, arg5=0, arg6=0, timeout=1000):
	data = missionCode.SendMissionArg()
	data.CommandNo = cmd
	data.transaction_id =tr_id 
	data.arg1 = arg1
	data.arg2 = arg2
	data.arg3 = arg3
	data.arg4 = arg4
	data.arg5 = arg5
	data.arg6 = arg6

	id = Vm.GetMsgEventID()
	if send_copy_msg(IMAGING_TASK_NAME,data, missionCode.DATA_TYPE_MISSION) >= 0:
		ret = ctrl.wait([id],timeout)

		if ret == id:
			#ﾘﾀｰﾝﾃﾞｰﾀの受け取り
			ret_data = get_mission_ret()
			if ret_data.transaction_id == tr_id:
				return ret_data

		data.result = 2
		data.arg1 = ret
	else:
		data.result = 2
		data.arg1 = -3 

	return data

#
#
#
def send_ctrl(tr_id, cmd, dwCode, arg1=0,arg2=0,arg3=0,arg4=0,arg5=0,arg6=0):
	data = missionCode.SendMissionArg()
	data.CommandNo = cmd
	data.transaction_id =tr_id 
	data.arg1 = arg1
	data.arg2 = arg2
	data.arg3 = arg3
	data.arg4 = arg4
	data.arg5 = arg5
	data.arg6 = arg6

	send_copy_msg(IMAGING_TASK_NAME,data, dwCode)

	#ﾘﾀｰﾝﾃﾞｰﾀの受け取り
	ret_data = get_mission_ret()

	return ret_data


#
# imageﾀｽｸ(image.exe)に終了ﾒｯｾｰｼﾞを送信する
#
def shutdown_imaging(tr_id=999):
	#send_mission(tr_id,0xFFFF)
	send_ctrl(tr_id,0xFFFF,missionCode.DATA_TYPE_SHUTDOWN)

#
# Imageﾀｽｸ(image.exe)を起動させる
#
def start_imaging():
	psInfo = ProcessStartInfo()
	#psInfo.FileName = "F:\\source\\MCM_Vision\\Imaging\\Imaging\\VPDplus\\Release\\vc80\\Imaging\\Imaging.exe"
	psInfo.FileName = "F:\\develop\\Imaging\\Imaging.exe"
	psInfo.Arguments = "Rowthon 1"
	psInfo.CreateNoWindow = False 
	psInfo.UseShellExecute = False
	psInfo.RedirectStandardOutput = True

	p = Process.Start(psInfo)
	#Process.Start("F:\\source\\MCM_Vision\\Imaging\\Imaging\\VPDplus\\Release\\vc80\\Imaging\\Imaging.exe")

#
# 部品画像処理
#   arg1: ﾊﾟｰﾂID
#   arg2: 画像処理時の処理角度 (30.5°--> 30.5 * 100000) [-180°～180°]
#   arg3: ﾊﾟｰﾂ中心位置X        (+5mm -> 5 * 10000)       [-20mm ～ 20mm]
#   arg4: ﾊﾟｰﾂ中心位置Y
#   arg5: 画像処理ﾓｰﾄﾞ区分     (0:単一部品画像処理)
#   arg6: 未使用
#
def parts_imaging(tr_id, arg1, arg2, arg3, arg4, arg5=0, tim=1000):
	if arg2 < (-180*100000) or arg2 > (180 * 100000):
		return (-2,0,0,0)
	if arg3 < (-20 * 10000) or arg3 > (20 * 10000):
		return (-2,0,0,0)
	if arg4 < (-20 * 10000) or arg4 > (20 * 10000):
		return (-2,0,0,0)
	if arg5 != 0:
		return (-2,0,0,0)

	ret = send_mission(tr_id,missionCode.CODE_IMAGING_PARTIMAGING,arg1,arg2,arg3,arg4,arg5,timeout=tim)

	if ret.result != 1:
		if ret.arg1 == 0x164102:
			print "err[0x{0:X}]: mission argument:{1},{2}".format(ret.arg1,arg1,arg2)
		elif ret.arg1 == 0x164017:
			print "err[0x{0:X}]: data group".format(ret.arg1)
		elif ret.arg1 == 0x16401B:
			print "err[0x{0:X}]: ID={1} err".format(ret.arg1,arg1)
		elif ret.arg1 == 0x164002:
			print "err[0x{0:X}]: etc...".format(ret.arg1)
		elif ret.arg1 == 0x164011:
			print "err[0x{0:X}]: shared memory error".format(ret.arg1)
		else:
			print "err[0x{0:X}]: imageProc error".format(ret.arg1)
		return (ret.result,ret.arg1,0,0)

	return (0,ret.arg2,ret.arg3,ret.arg4)

#
# ﾏｰｸ画像処理
#   arg1: ﾏｰｸID
#   arg2: 画像処理時の処理角度 (30.5°--> 30.5 * 100000) [-90°～90°]
#   arg3: 未使用
#   arg4: 未使用
#   arg5: 未使用
#   arg6: 未使用
#
def mark_imaging(tr_id, arg1, arg2, tim = 1000):
	if arg2 < (-90 * 100000) or arg2 > (90 * 100000):
		return (-2,0,0,0)

	ret = send_mission(tr_id,missionCode.CODE_IMAGING_WORKIMAGING,arg1,arg2, timeout = tim)

	if ret.result != 1:
		if ret.arg1 == 0x164102:
			print "err[0x{0:X}]: mission argument:{1},{2}".format(ret.arg1,arg1,arg2)
		elif ret.arg1 == 0x164017:
			print "err[0x{0:X}]: data group".format(ret.arg1)
		elif ret.arg1 == 0x16401B:
			print "err[0x{0:X}]: ID={1} err".format(ret.arg1,arg1)
		elif ret.arg1 == 0x164002:
			print "err[0x{0:X}]: etc...".format(ret.arg1)
		elif ret.arg1 == 0x164011:
			print "err[0x{0:X}]: shared memory error".format(ret.arg1)
		else:
			print "err[0x{0:X}]: imageProc error".format(ret.arg1)

		return (-3,ret.arg1,0,0)

	return (0,ret.arg2,ret.arg3,ret.arg4)

#
# 画像取り込み指示
#   arg1: 撮像ﾀｲﾑｱｳﾄ時間(ms) [1～10000ms]
#   arg2: 未使用
#   arg3: 未使用
#   arg4: 未使用
#   arg5: 未使用
#   arg6: 未使用
#
def take_image(tr_id, arg1):
	if arg1 < 1 or arg1 > 10000:
		return -2

	ret = send_mission(tr_id,missionCode.CODE_IMAGING_TAKEIMAGE,arg1)

	if ret.result != 1:
		if ret.arg1 == 0x164102:
			print "err[0x{0:X}]: mission argument:{1}".format(ret.arg1,arg1)
		elif ret.arg1 == 0x164005:
			print "err[0x{0:X}]: grab".format(ret.arg1)
		return -3

	return 0

#
# 画像処理準備処理
#   arg1: ﾃﾞｰﾀ区分      (1:ﾊﾟｰﾂﾃﾞｰﾀ 2:ﾏｰｸﾃﾞｰﾀ)
#   arg2: ﾊﾟｰﾂID,ﾏｰｸID
#   arg3: ｼｬｯﾀｰｽﾋﾟｰﾄﾞ%  (100% -> 100)  [1 ～ 16100]
#   arg4: 未使用
#   arg5: 未使用
#   arg6: 未使用
#
def ready_imaging(tr_id, arg1, arg2, arg3):
	if arg1 != 1 and arg1 != 2:
		return -2
	if arg3 < 1 or arg3 > 16100:
		return -2	

	ret = send_mission(tr_id,missionCode.CODE_IMAGING_READYIMAGING,arg1,arg2,arg3)

	if ret.result != 1:
		if ret.arg1 == 0x164102:
			print "err[0x{0:X}]: mission argument:{1}".format(ret.arg1,arg1)
		elif ret.arg1 == 0x164017:
			print "err[0x{0:X}]: shutter spd:{1}".format(ret.arg1,arg3)
		elif ret.arg1 == 0x164006:
			print "err[0x{0:X}]: etc..".format(ret.arg1)

		return -3

	return 0

#
# ｼｪｲﾌﾟﾃﾞｰﾀの読み込み
#   arg1: ﾊﾟｰﾂID
#   arg2～6: 未使用
#
def load_shape(tr_id,arg1):
	ret = send_mission(tr_id,missionCode.CODE_IMAGING_LOAD_SHAPE,arg1)

	if ret.result != 1:
		print "err[0x{0:X}]: load error ID:{1}".format(ret.arg1,arg1)
		return -3

	return 0

#
# ｼｪｲﾌﾟﾃﾞｰﾀの削除処理
#   arg1: ﾊﾟｰﾂID
#   arg2～6: 未使用
#
def delete_shape(tr_id, arg1):
	ret = send_mission(tr_id,missionCode.CODE_IMAGING_DEL_SHAPE,arg1)

	if ret.result != 1:
		print "err[0x{0:X}]: delete error ID:{1}".format(ret.arg1,arg1)
		return -3

	return 0

#
# ﾏｰｸﾃﾞｰﾀの読み込み
#   arg1: ﾏｰｸID
#   arg2～6: 未使用
#
def load_mark(tr_id,arg1):
	ret = send_mission(tr_id,missionCode.CODE_IMAGING_LOAD_MARK,arg1)

	if ret.result != 1:
		print "err[0x{0:X}]: load error ID:{1}".format(ret.arg1,arg1)
		return -3

	return 0

#
# ﾏｰｸﾃﾞｰﾀの削除処理
#   arg1: ﾏｰｸID
#   arg2～6: 未使用
#
def delete_mark(tr_id, arg1):
	ret = send_mission(tr_id,missionCode.CODE_IMAGING_DEL_MARK,arg1)

	if ret.result != 1:
		print "err[0x{0:X}]: delete error ID:{1}".format(ret.arg1,arg1)
		return -3

	return 0

#start_imaging()
#shutdown_imaging()
