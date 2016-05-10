#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      makihara
#
# Created:     07/09/2015
# Copyright:   (c) makihara 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import threading
import subprocess
import os
import time
import socket
import select
import winApi
from contextlib import closing

host = '127.0.0.1'
port = 10005

class AppThread(threading.Thread):
	def __init__(self,path,exeCmd):
		super(AppThread,self).__init__()
		self.path = path
		self.exeCmd = exeCmd

	def run(self):
		os.chdir(self.path)
		cmd_exe = self.path + "\\" + self.exeCmd 
		print "start {0}".format(self.exeCmd)
		subprocess.call(cmd_exe)

def execute_Rowthon():
	rowthon = AppThread("F:\\source\\Rowthon_Vision\\RowThon\\bin\\Debug","Rowthon.exe")
	rowthon.start()
	return rowthon

def main():
	sv_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	readfds = set([sv_sock])

	try:
		sv_sock.bind((host,port))
		sv_sock.listen(10)

		ctrl = True
		while ctrl:
			rready,wready,xready = select.select(readfds,[],[])
			for sock in rready:
				if sock is sv_sock:
					conn,address = sv_sock.accept()
					readfds.add(conn)
				else:
					msg = sock.recv(4096)
					if len(msg) == 0:
						sock.close();
						readfds.remove(sock)
					else:
						print msg
						cmd = msg.split(" ")
						if cmd[0] == "QUIT":
							ctrl = False
							break
						elif cmd[0] == "start":
							if cmd[1] == "ROWTHON":
								rowthon_thread = execute_Rowthon()
						elif cmd[0] == "stop":
							if cmd[1] == "ROWTHON":
								hWnd = winApi.FindWindow("Rowthon")	
								winApi.SendMessage(hWnd,0x10,0,0)
							elif cmd[1] == "WINDOWS":
								os.system("shutdown -s -f")
						elif cmd[0] == "restart":
							if cmd[1] == "ROWTHON":
								hWnd = winApi.FindWindow("Rowthon")	
								winApi.SendMessage(hWnd,0x10,0,0)
								time.sleep(5)
								rowthon_thread = execute_Rowthon()
							elif cmd[1] == "WINDOWS":
								os.system("shutdown -r -f")

	finally:
		print "sock close all"
		for sock in readfds:
			sock.close()

if __name__ == '__main__':
	main()
	print "appSv fine."