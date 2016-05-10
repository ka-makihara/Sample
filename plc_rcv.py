#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      makihara
#
# Created:     23/09/2014
# Copyright:   (c) makihara 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys
import socket
import struct
from contextlib import closing

hostIP = '127.0.0.1'
portNo = 10002

head218 = struct.Struct("B B B B H H H H")                  #218ﾍｯﾀﾞ
MWRead = struct.Struct("B B B B H H H H H B B B B H H")     #218Head + 保持ﾚｼﾞｽﾀ読み込みｺﾏﾝﾄﾞ
MWRep = struct.Struct("B B B B H H H H H B B B B H")        #218Head + 保持ﾚｼﾞｽﾀ読み込み応答

def init_socket(host,port):
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.bind( (host,port))
    return sock

def main():
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    with closing(sock):
        sock.bind( (hostIP,portNo))
        sock.listen(10)
        while True:
            conn, address = sock.accept()
            with closing(conn):
                msg = conn.recv(4096)
                print(msg)

    return

if __name__ == '__main__':
    main()
