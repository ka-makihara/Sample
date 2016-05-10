#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      makihara
#
# Created:     19/09/2014
# Copyright:   (c) makihara 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys
import socket
import struct

hostIP = '192.168.1.1'
portNo = 10001

head218 = struct.Struct("B B B B H H H H")                  #218ﾍｯﾀﾞ
MWRead =  struct.Struct("B B B B H H H H H B B B B H H")     #218Head + 保持ﾚｼﾞｽﾀ読み込みｺﾏﾝﾄﾞ
MWRep =   struct.Struct("B B B B H H H H H B B B B H H")        #218Head + 保持ﾚｼﾞｽﾀ読み込み応答


MWReadCmd = {
    "type":0,
    "num":0,
    "srcCh":0,
    "dstCh":0,
    "spare1":0,
    "length":0,
    "spare2":0,
    "spare3":0,
    "comLen":0,
    "MFC":0,
    "SFC":0,
    "CPU":0,
    "spare4":0,
    "RegNo":0,
    "RegCnt":0
}
cmd_value = []

def make_cmd(cmd_dict,cpu,mfc,sfc):
    cmd_dict['type'] = 0x11
    cmd_dict['comLen'] = 8
    cmd_dict['length'] = 8 + 12 + 2
    cmd_dict['MFC'] = mfc
    cmd_dict['SFC'] = sfc
    cmd_dict['CPU'] = (cpu << 4)

def make_value(cmd_dict):
    cmd_value.append( cmd_dict['type'] )
    cmd_value.append( cmd_dict['num'] )
    cmd_value.append( cmd_dict['srcCh'] )
    cmd_value.append( cmd_dict['dstCh'] )
    cmd_value.append( cmd_dict['spare1'] )
    cmd_value.append( cmd_dict['length'] )
    cmd_value.append( cmd_dict['spare2'] )
    cmd_value.append( cmd_dict['spare3'] )
    cmd_value.append( cmd_dict['comLen'] )
    cmd_value.append( cmd_dict['MFC'] )
    cmd_value.append( cmd_dict['SFC'] )
    cmd_value.append( cmd_dict['CPU'] )
    cmd_value.append( cmd_dict['spare4'] )
    cmd_value.append( cmd_dict['RegNo'] )
    cmd_value.append( cmd_dict['RegCnt'] )


def init_socket(host,port):
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect((host,port))
    return sock

def main():
    pass
    sock = init_socket(hostIP,portNo)
    MWReadCmd['type'] = 0x11        #指令ｺﾏﾝﾄﾞ
    MWReadCmd['RegCnt'] = 1         #読み込み数は1
    MWReadCmd['RegNo'] = 100;       #読み込みﾚｼﾞｽﾀは MW00100～
    make_cmd(MWReadCmd,1,0x20,0x09) #CPU:1 MFC:0x20 SFC:9(ﾚｼﾞｽﾀ読み込み)
    make_value(MWReadCmd)

    cmd_pack = MWRead.pack( *cmd_value )

    sl = sock.send( cmd_pack )
    rData = sock.recv(1024)
#    print("len:",len(rData))

    sock.close()
    ans_data = MWRep.unpack(rData)
#    print("cmd_list:", cmd_value)
#    print("cmd_pack:", cmd_pack)
#    print("unpack_v:", ans_data)
#    print("len:",len(ans_data))
    print("data:",ans_data[len(ans_data)-1])

if __name__ == '__main__':
    param = sys.argv
    main()
