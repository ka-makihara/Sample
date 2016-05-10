#-*- coding: UTF-8 -*-

#from ctypes import *
#from ctypes.wintypes import *
import time
import ctypes
import ctypes.wintypes as winType

#Windows ﾒｯｾｰｼﾞｺｰﾄﾞ
WM_CLOSE	= 0x10
WM_COPYDATA = 0x4A

#Windows API
_FindWindow = ctypes.WinDLL('user32').FindWindowW
_FindWindow.argtypes = [winType.c_wchar_p,winType.c_wchar_p]
_FindWindow.restype = winType.c_void_p

_GetWindowText = ctypes.WinDLL('user32').GetWindowTextW
_GetWindowText.argtypes = [winType.HWND,winType.c_wchar_p,winType.c_int]
_GetWindowText.restype = winType.c_int

_SendMessage = ctypes.WinDLL('user32').SendMessageW
_SendMessage.argtypes = [winType.HWND,winType.UINT,winType.WPARAM,winType.LPARAM]
_SendMessage.restype = winType.c_int

_FindWindowEx = ctypes.WinDLL('user32').FindWindowExW
_FindWindowEx.argtypes = [winType.HWND,winType.HWND,winType.c_wchar_p,winType.c_wchar_p]
_FindWindowEx.restype = winType.c_void_p

#
# Windows WM_COPYDATA 用の構造体
#    dwData: 任意
#    cdData: ﾃﾞｰﾀｻｲｽﾞ
#    lpData: ﾃﾞｰﾀｱﾄﾞﾚｽ
#
class COPYDATASTRUCT(ctypes.Structure):
    _fields_ = [
        ('dwData' ,winType.LPARAM),
        ('cbData',winType.DWORD),
        ('lpData',winType.c_void_p)
    ]

#
# name で指定されたｳｲﾝﾄﾞｳ名のｳｲﾝﾄﾞｳﾊﾝﾄﾞﾙを取得する
#
def FindWindow(name):
	hWnd = _FindWindow(None,name)
	return hWnd	

#
# hParentWnd を親に持つWindowﾊﾝﾄﾞﾙを取得する
#   例) FindWindowEx(<ﾀﾞｲｱﾛｸﾞHWND>,None,"Button","OK")
#         ﾀﾞｲｱﾛｸﾞ上の OK ﾎﾞﾀﾝのHWNDを取得
#         className などは spy で確認すると良い
#
def FindWindowEx(hParentWnd, hChildWnd, className, winName):
	hWnd = _FindWindowEx(hParentWnd,hChildWnd,className,winName)
	return hWnd	

#
# hWnd で指定されたｳｲﾝﾄﾞｳにﾒｯｾｰｼﾞを送信する
#
def SendMessage(hWnd, code, lPalam, wParam):
	_SendMessage(hWnd,code,lPalam,wParam)


#
# ﾀﾞｲｱﾛｸﾞ上のOKﾎﾞﾀﾝを押した状態を模擬したい
#   ※うまく動作しない・・・
#
#def quit_win(name):
#	hWnd = FindWindow(name)
#	if hWnd == None:
#		print "parent Window:{0} undefined".format(name)
#		return
#
#	h2 = FindWindowEx(hWnd,None,"Button","OK")
#	if h2 == None:
#		print "Button Window Undefined"
#		return
#
#	SendMessage(hWnd,0x7,0,0)	#WM_SETFOCUS
#	time.sleep(0.5)
#	SendMessage(h2,0x7,0,0)		#ﾎﾞﾀﾝにﾌｫｰｶｽ
#	time.sleep(0.5)
#	SendMessage(h2,0,1,1)		#BN_CLICK, IDOK
