#-*- coding: UTF-8 -*-
u"""MCMで使用するﾚｰｻﾞｰ出力値に関するﾗｲﾌﾞﾗﾘ
"""

import math

__version__ = "1.0.0"

spotR = 1000.356073			# ｽﾎﾟｯﾄ径
vwAngle = 5.467714286		# ﾚｰｻﾞｰ v-w 傾き
vwIntercept = -4.91614286	# ﾚｰｻﾞｰ v-w 切片

beamDiameter = 11000		# 仕様・発振器・ﾋﾞｰﾑ直径
focusLen = 331.4			# 仕様・ﾚﾝｽﾞ・焦点距離

beamRadius = 500.2			# ﾋﾞｰﾑ性状・焼成位置・ﾋﾞｰﾑ半径
burnDiameter = 1000.4 		# ﾋﾞｰﾑ性状・焼成位置・ﾋﾞｰﾑ直径

def laserPow(powDensity):
	u"""[ﾊﾟﾜｰ密度よりﾚｰｻﾞｰ電圧を取得する]
		powDensity : ﾊﾟﾜｰ密度
		    return : ﾚｰｻﾞｰ電圧 JOB:: <burnCommand><power>
	"""
	v = (powDensity * ((spotR/2/1000)**2 * math.pi) - vwIntercept) / vwAngle

	#
	return float('{0:.4f}'.format(v))
	#return v

def get_spot_beamR(waveLength):
	u"""[ﾋﾞｰﾑ性状・焦点位置・ﾋﾞｰﾑ径取得]
		waveLength : 波長
	"""
	return 2 * waveLength * focusLen / beamDiameter / math.pi

def get_offsetLZ(waveLength=1062):
	u"""[ﾃﾞﾌｫｰｶｽ高さを得る]
		waveLength : 波長(ﾃﾞﾌｫﾙﾄ=1062)

		return : <burnCommand><offsetLZ>
	"""
	br = get_spot_beamR(waveLength)
	ofst = math.pi * br ** 2/waveLength*math.sqrt((burnDiameter/2/br)**2-1)
	return float('{0:.4f}'.format(ofst))
	#return ofst
