#-*- coding: UTF-8 -*-

import Rowthon

#
# imageﾀｽｸ(image.exe)に終了ﾒｯｾｰｼﾞを送信する
#
def shutdown_imaging(tr_id=999):
	ret = Rowthon.send_recv_msg( 'img.shutdown_imaging({0});'.format(tr_id))
	return ret._retCode

#
# Imageﾀｽｸ(image.exe)を起動させる
#   path: imaging.exe があるﾊﾟｽ
#
def start_imaging(path):
	ret = Rowthon.send_recv_msg( 'img.start_imaging({0});'.format(path))
	return ret._retCode

#
# 部品画像処理
#   tr_id: ﾄﾗﾝｻﾞｸｼｮﾝID
# partsId: ﾊﾟｰﾂID
#     ang: 画像処理時の処理角度 (30.5°--> 30.5 * 100000) [-180°～180°]
#      cx: ﾊﾟｰﾂ中心位置X        (+5mm -> 5 * 10000)       [-20mm ～ 20mm]
#      cy: ﾊﾟｰﾂ中心位置Y
#    mode: 画像処理ﾓｰﾄﾞ区分     (0:単一部品画像処理)
#
def parts_imaging(tr_id, partsId, ang, cx, cy, mode=0, tim=1000):
	ret = Rowthon.send_recv_msg( 'img.parts_imaging({0},{1},{2},{3},{4},{5},{6});'.format(tr_id,partsId,ang,cx,cy,mode,tim))
	return ret._retCode

#
# ﾏｰｸ画像処理
#    tr_id: ﾄﾗﾝｻﾞｸｼｮﾝID
#   markId: ﾏｰｸID
#      ang: 画像処理時の処理角度 (30.5°--> 30.5 * 100000) [-90°～90°]
#      tim: ﾀｲﾑｱｳﾄ(ms)
#
def mark_imaging(tr_id, markId, ang, tim = 1000):
	ret = Rowthon.send_recv_msg( 'img.mark_imaging({0},{1},{2},{3});'.format(tr_id,markId,ang,tim))
	#return ret._retCode
	return( (ret._data1,ret._data2,ret._data3,ret._data4) )

#
# 画像取り込み指示
#  tr_id: ﾄﾗﾝｻﾞｸｼｮﾝID
#    tim: 撮像ﾀｲﾑｱｳﾄ時間(ms) [1～10000ms]
#
def take_image(tr_id, tim):
	ret = Rowthon.send_recv_msg( 'img.take_image({0},{1});'.format(tr_id,tim))
	return ret._retCode

#
# 画像処理準備処理
#    tr_id: ﾄﾗﾝｻﾞｸｼｮﾝID
# dataType: ﾃﾞｰﾀ区分      (1:ﾊﾟｰﾂﾃﾞｰﾀ 2:ﾏｰｸﾃﾞｰﾀ)
#   dataId: ﾊﾟｰﾂID,ﾏｰｸID
#      spd: ｼｬｯﾀｰｽﾋﾟｰﾄﾞ%  (100% -> 100)  [1 ～ 16100]
#
def ready_imaging(tr_id, dataType, dataId, spd):
	ret = Rowthon.send_recv_msg( 'img.ready_imaging({0},{1},{2},{3});'.format(tr_id,dataType,dataId,spd))
	return ret._retCode

#
# ｼｪｲﾌﾟﾃﾞｰﾀの読み込み
#   tr_id: ﾄﾗﾝｻﾞｸｼｮﾝID
# partsId: ﾊﾟｰﾂID
#
def load_shape(tr_id,partsId):
	ret = Rowthon.send_recv_msg( 'img.load_shape({0},{1});'.format(tr_id,partsId))
	return ret._retCode

#
# ｼｪｲﾌﾟﾃﾞｰﾀの削除処理
#   tr_id: ﾄﾗﾝｻﾞｸｼｮﾝID
# partsId: ﾊﾟｰﾂID
#
def delete_shape(tr_id, partsId):
	ret = Rowthon.send_recv_msg( 'img.delete_shape({0},{1});'.format(tr_id,partsId))
	return ret._retCode

#
# ﾏｰｸﾃﾞｰﾀの読み込み
#  tr_id: ﾄﾗﾝｻﾞｸｼｮﾝID
# markId: ﾏｰｸID
#
def load_mark(tr_id,markId):
	ret = Rowthon.send_recv_msg( 'img.load_mark({0},{1});'.format(tr_id,markId))
	return ret._retCode

#
# ﾏｰｸﾃﾞｰﾀの削除処理
#  tr_id: ﾄﾗﾝｻﾞｸｼｮﾝID
# markId: ﾏｰｸID
#
def delete_mark(tr_id, markId):
	ret = Rowthon.send_recv_msg( 'img.delete_mark({0},{1});'.format(tr_id,markId))
	return ret._retCode

#start_imaging()
#shutdown_imaging()
