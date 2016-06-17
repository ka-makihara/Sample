#-*- coding: UTF-8 -*-
import codecs
import math

def read_text(filename,delimiter):
	try:
		#
		# [(xxx,yyy),(xxx,yyy),(xxx,yyy),...] を生成する
		#
		with codecs.open(filename,'r','shift_jis') as file:
			data = map(lambda x: (float(x.split(delimiter)[0]),float(x.split(delimiter)[1])),file.read().strip().split('\n'))

		#ﾏﾄﾘｯｸｽのﾗｲﾝｻｲｽﾞ(ex. 36 => 6x6 のﾏﾄﾘｯｸｽ) 
		cnt = int(math.sqrt(len(data)))

		#
		# 1ﾗｲﾝ毎のﾘｽﾄに分割 [(x,y),(x,y), ...] -> [ [(x,y),(x,y)],[(x,y),(x,y)] ]
		#
		return( [data[x:x + cnt] for x in xrange(0, len(data), cnt)] )
	except:
		return( [[(0.00,0.00)]*6]*6 )
		#return( [[(0.00,0.00) for xx in range(6)] for yy in range(6)] )

def main():
	data = read_text('f:\\matrixSub.txt2',',')
	print data

if __name__ == '__main__':
	main()