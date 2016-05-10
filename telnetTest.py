#-*- coding: UTF-8 -*-

import telnetlib
import re

def main(hostIP,user,password):
	tn = telnetlib.Telnet(hostIP)
	tn.read_until("login: ")
	tn.write(user + "\n")
	tn.read_until("Password: ")
	tn.write(password + "\n")

	tn.write("ls -al\n")
	tn.write("exit\n")

	result = tn.read_all()

	#エスケープシーケンスの除去
	r = re.compile(r'\x1b\[.*?m\[?')
	result1 = re.sub(r,'',result)

	#文字コードutf-8をcp932に変換
	result2 = result1.decode('utf-8').encode('cp932')

	print result2

if __name__ == '__main__':
	main('172.17.28.110','makihara','wildgeese')
