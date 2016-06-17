#-*- coding: UTF-8 -*-

import socket
import struct

host = '192.168.1.4'
SW_CMD_PORT	= 10010
SW_MSG_PORT	= 10011
SW_WAIT_PORT= 10013

cmd_sock = 0
wait_sock = 0
msg_sock = 0

msg_size = 68

class MessageData(): #4x17=68 bytes
	def __init__(self):
		self._size = 0		# int(4)
		self._code = 0		# int(4)
		self._ioInput = 0	# int(4)
		self._ioOutput = 0	# int(4)
		self._retCode = 0	# int(4)
		self._data1 = 0		# int(4)
		self._data2 = 0		# int(4)
		self._data3 = 0		# int(4)
		self._data4 = 0		# int(4)
		self._data5 = 0		# int(4)
		self._data6 = 0		# int(4)
		self._data7 = 0		# int(4)
		self._data8 = 0		# int(4)
		self._data9 = 0		# int(4)
		self._data10 = 0	# int(4)
		self._data11 = 0	# int(4)
		self._data12 = 0	# int(4)

	def set_data(self, data_list):
		self._size = data_list[0] 
		self._code =  data_list[1]
		self._ioInput =  data_list[2]
		self._ioOutput =  data_list[3]
		self._retCode =  data_list[4]
		self._data1 =  data_list[5]
		self._data2 =  data_list[6]
		self._data3 =  data_list[7]
		self._data4 =  data_list[8]
		self._data5 =  data_list[9]
		self._data6 =  data_list[10]
		self._data7 =  data_list[11]
		self._data8 =  data_list[12]
		self._data9 =  data_list[13]
		self._data10 = data_list[14]
		self._data11 = data_list[15]
		self._data12 = data_list[16]



def init_connection(hostIP):
	global cmd_sock
	global wait_sock
	global msg_sock

	cmd_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	cmd_sock.connect((hostIP,SW_CMD_PORT))

	wait_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	wait_sock.connect((hostIP,SW_WAIT_PORT))

	msg_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	msg_sock.connect((hostIP,SW_MSG_PORT))

def close_connection():
	if cmd_sock != 0:
		cmd_sock.close()

	if wait_sock != 0:
		wait_sock.close()

	if msg_sock != 0:
		msg_sock.close()

def send_recv_msg(cmd_msg):
	cmd_sock.send(cmd_msg)
	msg_data = cmd_sock.recv(msg_size)
	data_list = struct.unpack('17i',msg_data)

	msg = MessageData()
	msg.set_data(data_list)

	return msg

def send_wait_msg(cmd_msg):
	wait_sock.send(cmd_msg)
	msg_data = wait_sock.recv(msg_size)
	data_list = struct.unpack('17i',msg_data)

	msg = MessageData()
	msg.set_data(data_list)

	return msg
