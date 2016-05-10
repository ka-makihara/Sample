#-*- coding: UTF-8 -*-

from ctypes import *
from ctypes.wintypes import *

import mmap
import struct

WM_COPYDATA = 0x4A

FindWindow = WinDLL('user32').FindWindowW
FindWindow.argtypes = [c_wchar_p,c_wchar_p]
FindWindow.restype = c_void_p

GetWindowText = WinDLL('user32').GetWindowTextW
GetWindowText.argtypes = [HWND,c_wchar_p,c_int]
GetWindowText.restype = c_int

SendMessage = WinDLL('user32').SendMessageW
SendMessage.argtypes = [HWND,UINT,WPARAM,LPARAM]
SendMessage.restype = c_int

class SendMissionArg(Struct):
	_fields = [
		('transaction_id',WORD),
		('CommandNo',WORD),
		('result',WORD),
		('spare'),WORD),
		('arg1',LONG),
		('arg2',LONG),
		('arg3',LONG),
		('arg4',LONG),
		('arg5',LONG),
		('arg6',LONG),
		]

#ミッションコード
CODE_IMAGING_PARTIMAGING			0x0101	# 画像処理
CODE_IMAGING_WORKIMAGING			0x0102	# ワークマーク処理
CODE_IMAGING_2DIMAGING				0x0103	# 2Dコード処理
CODE_IMAGING_GSKIPIMAGING			0x0104	# グループスキップ処理
CODE_IMAGING_TAKEIMAGE				0x0105	# 撮像処理
CODE_IMAGING_READYIMAGING			0x0106	# 撮像準備処理
CODE_IMAGING_CLEARIMAGING			0x0107	# 画像処理データクリア処理
CODE_IMAGING_SCRIPTIMAGING			0x0108	# スクリプト処理
CODE_IMAGING_CHANGE_WINDOWSIZE		0x010A	# 画面位置・サイズ変更処理
CODE_IMAGING_FOREFRONT_WINDOW		0x010B	# 最前面表示処理
CODE_IMAGING_OPEN_OPERATIONPANEL	0x010C	# 操作パネル画面表示処理
CODE_IMAGING_EXISTENCE_CALIBLATION	0x010D	# キャリブレーション有無取得処理
CODE_IMAGING_CHANGE_WINDOWMODE		0x010E	# 画面表示モード変更処理
CODE_IMAGING_CHANGE_PICTUREMODE		0x010F	# 動画・静止画切替処理
CODE_IMAGING_MATCHIMAGING			0x0110	# ツール存在チェック処理
CODE_IMAGING_CHANGE_CAMERA_ID		0x0111	# キャリブレーションデータ切替処理
CODE_IMAGING_SET_SCREEN_REFRESH		0x0112	# 画面表示更新切替処理
CODE_IMAGING_DOUT					0x0113	# DOUT処理
CODE_IMAGING_ROI_SET				0x0114	# ROIセット処理
CODE_IMAGING_ROI_RESET				0x0115	# ROIリセット処理
CODE_IMAGING_SAVE_PICTURE			0x0116	# 静止画保存処理
CODE_IMAGING_INI_REWRITE			0x0117	# INIファイル書換処理
CODE_IMAGING_SET_IMAGING_PARAMETER	0x0118	# 画像処理パラメータセット処理
CODE_IMAGING_SHOW_CENTERLINE		0x0119	# 中心線表示処理
CODE_IMAGING_SYS_PARTIMAGING		0x0121	# 画像処理
CODE_IMAGING_SYS_WORKIMAGING		0x0122	# ワークマーク処理
CODE_IMAGING_SYS_2DIMAGING			0x0123	# 2Dコード処理
CODE_IMAGING_SYS_TAKEIMAGE			0x0125	# 撮像処理
CODE_IMAGING_SYS_READYIMAGING		0x0126	# 撮像準備処理
CODE_IMAGING_SYS_MATCHIMAGING		0x0130	# ツール存在チェック処理
CODE_IMAGING_CHECK_RCNO				0x0140	# 認識条件番号確認処理
CODE_IMAGING_LOAD_RECIPE			0x0141	# レシピのシェイプ・マークデータ読み込み処理
CODE_IMAGING_DEL_RECIPE				0x0142	# シェイプ・マークデータ削除処理
CODE_IMAGING_NOZZLE_SET				0x0143	# ノズル登録処理
CODE_IMAGING_GET_IMAGE_TAKE_METHOD	0x0145	# 撮像方法取得処理
CODE_IMAGING_GET_IMAGE_POSITION_OFFSET	0x0146	# 撮像位置のオフセット取得処理
CODE_IMAGING_EMARGENCY_STOP			0x0147	# 非常停止処理
CODE_IMAGING_LIGHT_SET				0x0148	# ライト制御処理
CODE_COLLECT_TRACE_INSTRUCT			0x001C	# トレース出力処理



mm = mmap.mmap(-1,1024,tagname="ShMem")

text = create_unicode_buffer(255)

hWnd = FindWindow(None,'0016_IMAGING')

print "hWnd={0}".format(hWnd)

if hWnd != None:
	GetWindowText(hWnd,text,sizeof(text))

	print text.value

	mm.write( struct.pack('I',int(0xAABBCCDD)) )

	SendMessage(hWnd,0x401,123,text)


mm.close()
