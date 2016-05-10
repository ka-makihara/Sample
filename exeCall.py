#-*- coding: UTF-8 -*-

import os
import sys
import traceback
import subprocess

cmd = u'F:\\source\\SplitImage\\Release\\bitmapBunkatsu.exe /mask=1,1 /block=4,4 /image=F:\\source\\SplitImage\\Debug\\2-f.構造材.png /output=.\\images2'.encode('ShiftJIS')

try:
	ret = subprocess.check_call( cmd.strip().split(" ") )
	print ret
except:
	#print traceback.format_exc(sys.exc_info()[2])
	print 'split error'
