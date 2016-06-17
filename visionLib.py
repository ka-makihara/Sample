#-*- coding: UTF-8 -*-

#
# Vision ﾗｲﾌﾞﾗﾘ
#
version = 1.00

import debugLib as debug
import math
import missionLib as img

class CvPoint:
	def __init__(self, x, y):
		self._x = x
		self._y = y


class CvRect:
	def __init__(self, x1, y1, x2, y2):
		self._x1 = x1
		self._y1 = y1
		self._x2 = x2
		self._y2 = y2

#画像処理結果クラス
class VisionRet:
	def __init__( self, xx=0, yy=0, qq=0 ):
		self.x = xx
		self.y = yy
		self.q = qq
		
#
# ｶﾒﾗ初期化
#
def init_camera():
	return Vm.camera_init()

#
# 画像取り込み
#    No : 番号(0～)[ｶﾒﾗ,shape,mark]
#  type : ｶﾒﾗﾀｲﾌﾟ(0:? 1:ﾊﾟｰﾂ 2:ﾏｰｸ)
#  mode : 取り込みﾓｰﾄﾞ(-1:連続 0:連続停止 1:1画面)
#   spd : ｼｬｯﾀｰｽﾋﾟｰﾄﾞ (%)
#
def grab(no, type, mode = 1, spd = 100):
	'''画像取り込み(no,type,mode,speed)
	 no  : ﾏｰｸ(1～) or ｼｪｲﾌﾟ番号(1～)
	 type: ｶﾒﾗﾀｲﾌﾟ(1=ﾊﾟｰﾂ 2=ﾏｰｸ)
	 mode: 取り込みﾓｰﾄﾞ(-1=連続 0:連続停止 1:1画面)
	speed: ｼｬｯﾀｰｽﾋﾟｰﾄﾞ(%) (100%->100)'''
	if type == 0:
		ret = Vision.GrabCamera(mode)
		Vm.UpdateProperty("GrabStatus")
		return ret
	elif type == 1 or type == 2:
		if type == 1:
			if img.load_shape(100,no) < 0:
				return -3
		else:
			if img.load_mark(101,no) < 0:
				return -3

		if img.ready_imaging(103,type,no,spd) < 0:
			return -4

		if img.take_image(104,1000) < 0:
			return -5
	else:
		return -2

	return 0

#
# 画像処理ﾊﾟﾗﾒｰﾀの設定
#  type 0: ｻｰﾁｴﾘｱ [CvRect(x1,y1,x2,y2)]
#
def set_params(type, data):
	'''ｻｰﾁｴﾘｱ設定
	未対応です'''
	if type == 0:
		if isinstance(data,CvRect) == False:
			return -2

		Vision.SetSearchArea(data._x1,data._y1,data._x2,data._y2)
	elif type == 1:
		pass
	else:
		return -2

	return 0

def draw_center():
	'''中心線描画'''
	Vision.DrawCenter()
	return 0
#
# OpenCv・画像処理
#   tmpNo : 使用するﾃﾝﾌﾟﾚｰﾄ番号(0～)
#
def cv_execute(tmpNo):
	'''OpenCv・画像処理(tmpNo)
	tmpNo: ﾃﾝﾌﾟﾚｰﾄ番号(0～)
	return: OK=0 ERR<0'''
	#ﾊﾟﾀｰﾝﾏｯﾁﾝｸﾞ
	# pos_list = [X,Y,Q,*,R(相関率*100)]
	ret = Vision.Execute(tmpNo)
	if ret < 0:
		print "cv_execute error:{0}".format(ret)
		return -2

	#結果描画用
	pos_list = [0,0,0,0,0]
	ret  = Vision.GetVisionPos(pos_list)

	#ﾋﾟｸｾﾙ座標を実座標へ(画面中心(320,320)を(0,0)とした座標系)
	cx = (pos_list[0] - 320) * setting.PixelRatioX
	cy = (320 - pos_list[1]) * setting.PixelRatioY

	#print "X={0} Y={1} maching={2:3.2f}".format(cx,cy,pos_list[4]/100.0)
	Vision.DrawCenterRect(pos_list[0],pos_list[1],tmpNo);

	return 0

#
# 画像処理の結果を取得する
#
#  angle : カメラ取り付け角度(°*10000)
#
#  posList:結果
#           posList[0]:X X座標(mm * 10000)
#           posList[1]:Y Y座標(mm * 10000)
#           posList[2]:Q  角度(°* 10000)
#           posList[3]:* 未使用
#           posList[4]:R 相関率(1.0を最大)
#
def cv_get_position(angle, posList):
	'''OpenCV・画像処理結果取得(angle,posList)
	  angle: 展開角度(補正量を角度変換します)(x10000°)
	posList: [] 戻り値格納用ﾘｽﾄ
	 return: OK=0 ERR<0'''
	pos_list = [0,0,0,0,0]
	ret  = Vision.GetVisionPos(pos_list)
	if ret < 0:
		return -2

	#ﾋﾟｸｾﾙ座標を実座標へ(画面中心(320,320)を(0,0)とした座標系)
	cx = (pos_list[0] - 320) * setting.PixelRatioX
	cy = (320 - pos_list[1]) * setting.PixelRatioY

	#角度補正
	rad = math.radians(angle/10000.0)
	vcx = int((cx * math.cos(rad) + cy * math.sin(rad)) * 10000.0)
	vcy = int((-(cx * math.sin(rad)) + cy * math.cos(rad)) * 10000.0)

#	print "vcx={0} vcy={1} cx={2} cy={3}".format(vcx,vcy,cx,cy)

	#答えのﾘｽﾄを設定
	posList.append(vcx)
	posList.append(vcy)
	posList.append(0)
	posList.append(0)
	posList.append( pos_list[4] )

	return 0

#
# OpenCv・ﾏｰｸ画像処理
#  tplName: ﾃﾝﾌﾟﾚｰﾄ画像ﾌｧｲﾙ名(拡張子含む)
#    angle: 変換角度
#
def cv_executeName(tplName, angle=0.0):
	'''OpenCV・画像処理(tplName,angle)
	tplName:ﾊﾟﾀｰﾝﾏｯﾁﾝｸﾞ用ﾌｧｲﾙ名
	angle  :展開角度
	return : ﾀﾌﾟﾙ(Ret, XX,YY,QQ)'''
	posList = []
	idx = Vm.GetCvTplIdx(tplName)
	if idx < 0:
		print "Undefined templete:{0}".format(tplName)
		return (-2,0,0,0)

	if cv_execute(idx) < 0:
		return (-3,0,0,0)

	if cv_get_position(angle,posList) < 0:
		return (-3,0,0,0)

	# (ret,CX,CY,CQ)
	return(0,posList[0],posList[1],posList[2])

#
# imaging・ﾏｰｸ画像処理
#   partNo : ﾏｰｸ番号
#     load : True -> ﾃﾞｰﾀﾛｰﾄﾞ
#    ready : True -> ready_imagingの実行
#     take : True -> ｲﾒｰｼﾞ取り込みの実行
#
#  return : (ret, X, Y, Q)
#
def img_execute_mark(markNo, load=False, ready=False, take=False):
	'''Imaging・ﾏｰｸ画像処理(markNo,load=False,ready=False,take=False)
	markNo:ﾏｰｸ番号
	load  : True => load_mark を実行する
	ready : True => ready_imaging を実行する
	take  : True => take_image を実行する
	return: ﾀﾌﾟﾙ(Ret,X,Y,Q)'''
	#ﾃﾞｰﾀﾛｰﾄﾞ
	if load == True:
		if img.load_mark(10,markNo) < 0:
			return (-1,0,0,0)

	#準備
	if ready == True:
		if img.ready_imaging(11, 2, markNo, 100) < 0:
			return (-2,0,0,0)

	#取り込み
	if take == True:
		if img.take_image(12, 1000) < 0:
			return (-3,0,0,0)

	#(ret,arg2,arg3,arg4) = img.mark_imaging(3, markNo, 0,10000)
	return img.mark_imaging(13, markNo, 0,10000)

#
# imaging・ﾊﾟｰﾂ画像処理
#   partNo : ﾊﾟｰﾂ番号
#    angle : 処理角度
#      ofx : Xｵﾌｾｯﾄ
#      ofy : Yｵﾌｾｯﾄ
#     load : True -> ﾃﾞｰﾀﾛｰﾄﾞ
#    ready : True -> ready_imagingの実行
#     take : True -> ｲﾒｰｼﾞ取り込みの実行
#
#  return : (ret, X, Y, Q)
#
def img_execute_part(partNo, angle=0, ofx=0, ofy=0, load=False, ready=False, take=False):
	'''Imaging・ﾊﾟｰﾂ画像処理(partNo,angle=0,ofx=0,ofy=0,load=False,ready=False,take=False)
	partNo:ﾊﾟｰﾂ番号
	angle : 角度変換
	ofx   : X方向ｵﾌｾｯﾄ値
	ofy   : Y方向ｵﾌｾｯﾄ値
	load  : True => load_mark を実行する
	ready : True => ready_imaging を実行する
	take  : True => take_image を実行する
	return: ﾀﾌﾟﾙ(Ret,X,Y,Q)'''
	#ﾃﾞｰﾀﾛｰﾄﾞ
	if load == True:
		if img.load_shape(20,partNo) < 0:
			return (-1,0,0,0)

	#準備
	if ready == True:
		if img.ready_imaging(21, 1, partNo, 100) < 0:
			return (-2,0,0,0)

	#取り込み
	if take == True:
		if img.take_image(22, 1000) < 0:
			return (-3,0,0,0)

	return img.parts_imaging(23, partNo, angle,ofx,ofy,0,10000)

#
# OpenCv・ﾏｰｸ画像処理
#
def cv_mark_proc(tplNo):
	'''OpenCv・ﾏｰｸ画像処理(tplNo)
	tplNo :ﾃﾝﾌﾟﾚｰﾄ番号
	return:無し(表示のみ)'''
	posList = []
	ret = cv_execute(tplNo)
	if ret < 0:
		print 'visionProcError'
	else:
		get_position(0,posList)
		print "X={0} Y={1} R={2}".format(posList[0],posList[1],posList[4])

#
# imaging・ﾏｰｸ画像処理
#
def img_mark_proc(tplNo):
	'''Imaging・ﾏｰｸ画像処理(markNo)
	markNo: ﾏｰｸ番号
	return: 無し(表示のみ)
	  load_mark, ready_imaging, take_imageを実行して画像処理の実行'''
	(ret,x,y,q) = img_execute_mark(tplNo,load=True,ready=True,take=True)
	if ret < 0:
		print 'imaging Mark error:{0}'.format(ret)
	else:
		print "X:{0} Y:{1} Q:{2}".format(x,y,q)

#
# imaging・ﾊﾟｰﾂ画像処理
#
def img_part_proc(tplNo):
	'''Imaging・ﾊﾟｰﾂ画像処理(partNo)
	partNo: ﾊﾟｰﾂ番号
	return: 無し(表示のみ)
	  load_shape, ready_imaging, take_imageを実行して画像処理の実行'''
	(ret,x,y,q) = img_execute_part(tplNo,angle=0, ofx=0, ofy=0, load=True,ready=True,take=True)
	if ret < 0:
		print 'imaging Part error:{0}'.format(ret)
	else:
		print "X:{0} Y:{1} Q:{2}".format(x,y,q)

#
# OpenCv・ﾏｰｸ画像処理
#   tplName: ﾃﾝﾌﾟﾚｰﾄ画像ﾌｧｲﾙ名
#
def cv_mark_procName(tplName):
	'''OpenCv・ﾏｰｸ画像処理(tplName)
	tplName:ﾃﾝﾌﾟﾚｰﾄ画像ﾌｧｲﾙ名
	return :無し(表示のみ)'''
	posList = []
	ret = cv_executeName(tplName)
	if ret < 0:
		print 'visionProcError'
	else:
		get_position(0,posList)
		print "X={0} Y={1} R={2}".format(posList[0],posList[1],posList[4])

