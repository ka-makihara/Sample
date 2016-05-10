# -*- coding: utf-8 -*-

"""
"""
from __future__ import unicode_literals, print_function

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager
from scipy.ndimage.interpolation import shift
import serial

import argparse


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

def pause_plot(portName):
	#ser = serial.Serial('COM5',115200)
	ser = serial.Serial(portName,115200)

	fig, ax = plt.subplots(1, 1)
	x = np.arange(0.0, 60.0, 1.0)
	y = np.zeros( len(x) )

	plt.title(u'LM61 温度グラフ',fontdict={"fontproperties":font_prop})
	plt.xlabel('Time')
	plt.ylabel(u'温度',fontdict={"fontproperties":font_prop})
	plt.grid()
	ax.set_ylim((0.0, 50.0))

	for i,d in enumerate(y):
		y[i] = None

	# 初期化的に一度plotしなければならない
	# そのときplotしたオブジェクトを受け取る受け取る必要がある．
	# listが返ってくるので，注意
	lines, = ax.plot(x, y,label=u'温度')
	ax.legend(prop=font_prop)

	# ここから無限にplotする
	xp = 0
	idx = -1 
	while True:
		# plotデータの更新
		x += 1.0

		if idx >= len(y) -1:
			idx = len(y) - 1
			y = shift(y,-1,cval=0.0)
		else:	
			idx = idx + 1

		tt = temp(ser) / 100.0
		y[idx] = tt

		# 描画データを更新するときにplot関数を使うと
		# lineオブジェクトが都度増えてしまうので，注意．
		#
		# 一番楽なのは上記で受け取ったlinesに対して
		# set_data()メソッドで描画データを更新する方法．
		lines.set_data(x, y)

		ax.legend([str(tt)],prop=font_prop)

		# set_data()を使うと軸とかは自動設定されないっぽいので，
		# 今回の例だとあっという間にsinカーブが描画範囲からいなくなる．
		# そのためx軸の範囲は適宜修正してやる必要がある．
		ax.set_xlim((x.min(), x.max()))

		# 一番のポイント
		# - plt.show() ブロッキングされてリアルタイムに描写できない
		# - plt.ion() + plt.draw() グラフウインドウが固まってプログラムが止まるから使えない
		# ----> plt.pause(interval) これを使う!!! 引数はsleep時間
		plt.pause(0.1)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-p','--port',required=True, help='COM port Name')

	args = parser.parse_args()

	pause_plot( args.port )
	#pause_plot()
