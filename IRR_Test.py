# -*- coding: utf8 -*-
import sys
import random
import serial
import time


port = "COM3"
baud = 9600

baud_list = serial.Serial.BAUDRATES
parity_list = serial.Serial.PARITIES

#size_list = serial.Serial.BYTESIZES
size_list = [7,8]

#stopbit_list = serial.Serial.STOPBITS
stopbit_list = [1,2]

com = serial.Serial(port,baud)

#
# ﾃﾞｰﾀ送信
#  0～255 までのﾗﾝﾀﾞﾑﾃﾞｰﾀを送信する
#
def data_send(count, dataLen):
	base = count
	for nn in range(count):
		data = []
		for cnt in range(dataLen):
			data.append(random.randrange(0,255))

		if nn != 0:
			for m in range(len(str(count-nn+1))):
				sys.stdout.write('\b')

		com.write(data)
		time.sleep(0.1)
		#sys.stdout.write(".")
		sys.stdout.write( str(count-nn) )

#
# ﾎﾞｰﾚｰﾄを変更してﾃﾞｰﾀを送信する
#
def baud_test(count, dataLen):
	for baud in baud_list:
		print "set baud={0}".format(baud)
		com.baudrate = baud
		time.sleep(1)
		#20ﾊﾞｲﾄﾃﾞｰﾀを100回送信
		data_send(count,dataLen)

#
# ﾃﾞｰﾀｻｲｽﾞを変更してﾃﾞｰﾀ送信
#
def size_test(count, dataLen):
	for sz in size_list:
		print "set bytesize={0}".format(sz)
		com.bytesize = sz
		time.sleep(1)
		data_send(count,dataLen)

#
# ﾊﾟﾘﾃｨを変更して送信
#
def parity_test(count, dataLen):
	for parity in parity_list:
		print "set parity={0}".format(parity)
		com.parity = parity
		time.sleep(1)
		data_send(count,dataLen)

#
# ﾊﾟﾘﾃｨを変更して送信
#
def stopbit_test(count, dataLen):
	for bit in stopbit_list:
		print "set stopbit={0}".format(bit)
		com.stopbits = bit 
		time.sleep(1)
		data_send(count,dataLen)


#
# 設定可能な全条件も指定してﾃﾞｰﾀ送信
#
def test_all(count, dataLen):
	for baud in baud_list:
		print "set baud={0}".format(baud)
		com.baudrate = baud

		for sz in size_list:
			print "set bytesize={0}".format(sz)
			com.bytesize = sz

			for parity in parity_list:
				print "set parity={0}".format(parity)
				com.parity = parity

				for bit in stopbit_list:
					print "set stopbit={0}".format(bit)
					com.stopbits = bit 
					time.sleep(1)
					#dataLen ﾊﾞｲﾄﾃﾞｰﾀを count 回送信
					data_send(count,dataLen)

				print "\n"

#baud_test(100,20)
#size_test(100,20)
#parity_test(100,20)
#stopbit_test(100,20)

test_all(10000,10)