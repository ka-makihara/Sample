# -*- coding: utf-8 -*-

"""
"""
from __future__ import unicode_literals, print_function

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager
from scipy.ndimage.interpolation import shift
import serial


font_prop = matplotlib.font_manager.FontProperties(fname="c:\\Windows\\Fonts\\msgothic.ttc")

def temp(ser):
	temp = 0.0
	while True:
		tempLine = ser.readline()	
		idx = tempLine.find('te=') 
		if idx != -1:
			temp = int(tempLine[idx+3:idx+7])
			break

	return temp

def pause_plot():
	ser = serial.Serial('COM5',115200)

	fig, ax = plt.subplots(1, 1)
	x = np.arange(0.0, 60.0, 1.0)
	y = np.zeros( len(x) )
	#y[0] = temp(ser) / 100.0

	plt.title(u'LM61 温度グラフ',fontdict={"fontproperties":font_prop})
	plt.xlabel('Time')
	plt.ylabel(u'温度',fontdict={"fontproperties":font_prop})
	plt.grid()
	ax.set_ylim((0.0, 50.0))

	#print 'temp={0}'.format(y)
	# 初期化的に一度plotしなければならない
	# そのときplotしたオブジェクトを受け取る受け取る必要がある．
	# listが返ってくるので，注意
	lines, = ax.plot(x, y)

	# ここから無限にplotする
	idx = -1 
	while True:
		# plotデータの更新
		x += 1.0

		if idx > len(y):
			idx = len(y) - 1
			y = shift(y,-1,cval=0.0)
		else:	
			idx = idx + 1

		tt = temp(ser) / 100.0
		y[idx] = tt

		#plt.text(100,10,'Temp:{0}'.format(str(tt)))
		#print 'temp={0}'.format(y)
		# 描画データを更新するときにplot関数を使うと
		# lineオブジェクトが都度増えてしまうので，注意．
		#
		# 一番楽なのは上記で受け取ったlinesに対して
		# set_data()メソッドで描画データを更新する方法．
		lines.set_data(x, y)

		# set_data()を使うと軸とかは自動設定されないっぽいので，
		# 今回の例だとあっという間にsinカーブが描画範囲からいなくなる．
		# そのためx軸の範囲は適宜修正してやる必要がある．
		ax.set_xlim((x.min(), x.max()))

		# 一番のポイント
		# - plt.show() ブロッキングされてリアルタイムに描写できない
		# - plt.ion() + plt.draw() グラフウインドウが固まってプログラムが止まるから使えない
		# ----> plt.pause(interval) これを使う!!! 引数はsleep時間
		plt.pause(1.0)

if __name__ == "__main__":
	pause_plot()