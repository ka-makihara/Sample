#-*- coding: UTF-8 -*-

#import missionLib as img
import servoLib as servo
import ctrlLib as ctrl
#import ioLib as io
import time
import math
import threading

import Rowthon

class ServoPos(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	def run(self):
		while True:
			for i in range(5):
				print 'st={0}'.format(servo.get_status(i+1,4))
			time.sleep(0.1)

class ProgStop(threading.Thread):
	def __init__(self,id,tm):
		threading.Thread.__init__(self)
		self.id_ = id
		self.tim_  = tm

	def run(self):
		time.sleep(self.tim_)
		print 'stop:ID={0}'.format(self.id_)
		ctrl.stop_program(self.id_)

#
def main():
	Rowthon.init_connection('127.0.0.1')

	program1 = ''
	program2 = ''
	with open('func.py','r') as fp:
		program1 = fp.read()

	with open('func2.py','r') as fp:
		program2 = fp.read()

#	th = ServoPos()
#	th.setDaemon(True)
#	th.start()

	id1 = ctrl.execute_program(program1)
	stpTh = ProgStop(id1,5)
	stpTh.start()
	rr = ctrl.wait([id1],30000)

	'''
	for nn in range(10):
		print 'Count={0}'.format(nn)
		id1 = ctrl.execute_program(program1)
		rr = ctrl.wait([id1],30000)

		id2 = ctrl.execute_program(program2)
		stpTh = ProgStop(id2,3)
		stpTh.start()
		rr = ctrl.wait([id2],30000)
	'''

	Rowthon.close_connection()

if __name__ == '__main__':
	main()
