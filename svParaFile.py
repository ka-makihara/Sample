# -*- coding: utf-8 -*-

import codecs

if __name__ == "__main__":
	fout = codecs.open("data.txt","w","utf-8")

	for ln in range(580):
		data = "[%03d]:0.00000\n" % ln
		fout.write(data)

	fout.close()
