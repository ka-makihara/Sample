#-*- coding: UTF-8 -*-

import os
import wx

from numpy import arange, sin, pi, array
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from PIL import Image

import vecUtil

font_prop = matplotlib.font_manager.FontProperties(fname="c:\\Windows\\Fonts\\msgothic.ttc")


params = {	'xtick.labelsize':30,
			'ytick.labelsize':30
		}

dottLen = 0.0423333
#offsetX = 81.5334
#offsetY = 72.0508
#offsetX = 90.0
#offsetY = 90.0
offsetX = 0.0
offsetY = 0.0

class MyFileDropTarget(wx.FileDropTarget):
 
	"""ﾄﾞﾗｯｸﾞ&ﾄﾞﾛｯﾌﾟ担当ｸﾗｽ"""
 
	def __init__(self, obj):
		wx.FileDropTarget.__init__(self)
		self.obj = obj  # ファイルのドロップ対象を覚えておく
 
	def OnDropFiles(self, x, y, filenames):
		"""ﾌｧｲﾙをﾄﾞﾛｯﾌﾟした時の処理"""
		self.obj.LoadFile(filenames)  # 親？の関数を呼ぶ

#
#
#
class CanvasPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

		self.vectData = None
		plt.rcParams.update(params)

		self.figure = Figure(figsize=(30,30),dpi=30)
		self.axes = self.figure.add_subplot(111)
		self.axes.set_xlabel('X Pixel',fontsize=40)
		self.axes.set_ylabel('Y Pixel',fontsize=40)

		self.canvas = FigureCanvas(self, -1, self.figure)

		#ﾍﾞｸﾄﾙ座標
		self.tx1 = wx.TextCtrl(self,wx.ID_ANY)
		self.ty1 = wx.TextCtrl(self,wx.ID_ANY)
		self.tx2 = wx.TextCtrl(self,wx.ID_ANY)
		self.ty2 = wx.TextCtrl(self,wx.ID_ANY)
		self.bt1 = wx.Button(self,wx.ID_ANY,u'更新',size=(80,30))
		self.bt2 = wx.Button(self,wx.ID_ANY,u'ﾌｧｲﾙ出力',size=(80,30))
		self.bt2.Disable()
		self.tx1.SetToolTipString(u'ﾍﾞｸﾄﾙ開始X')
		self.ty1.SetToolTipString(u'ﾍﾞｸﾄﾙ開始Y')
		self.tx2.SetToolTipString(u'ﾍﾞｸﾄﾙ終了X')
		self.ty2.SetToolTipString(u'ﾍﾞｸﾄﾙ終了Y')
		self.bt1.SetToolTipString(u'選択ﾍﾞｸﾄﾙの位置更新')

		#ﾎﾞﾀﾝのｲﾍﾞﾝﾄﾊﾝﾄﾞﾗを登録
		self.bt2.Bind(wx.EVT_BUTTON, self.click_output_file)
		self.bt1.Bind(wx.EVT_BUTTON, self.click_update)

		#ﾍﾞｸﾄﾙ座標のﾚｲｱｳﾄ
		self.pos = wx.BoxSizer(wx.HORIZONTAL)
		self.pos.Add(self.tx1, proportion=1,flag=wx.EXPAND | wx.TOP, border=2)
		self.pos.Add(self.ty1, proportion=1,flag=wx.EXPAND | wx.TOP, border=2)
		self.pos.Add(self.tx2, proportion=1,flag=wx.EXPAND | wx.TOP, border=2)
		self.pos.Add(self.ty2, proportion=1,flag=wx.EXPAND | wx.TOP, border=2)
		self.pos.Add(self.bt1, proportion=0)
		self.pos.Add(self.bt2, proportion=0)

		#ｵﾌｾｯﾄ
		self.ox1 = wx.TextCtrl(self,wx.ID_ANY)
		self.oy1 = wx.TextCtrl(self,wx.ID_ANY)
		self.ox2 = wx.TextCtrl(self,wx.ID_ANY)
		self.oy2 = wx.TextCtrl(self,wx.ID_ANY)
		self.bt3 = wx.Button(self,wx.ID_ANY,u'更新',size=(80,30))

		self.ox1.SetToolTipString(u'画像ｵﾌｾｯﾄX')
		self.oy1.SetToolTipString(u'画像ｵﾌｾｯﾄY')
		self.ox1.SetValue('{0:.3f}'.format(offsetX))
		self.oy1.SetValue('{0:.3f}'.format(offsetY))
		self.ox2.Disable()
		self.oy2.Disable()
		self.bt3.Bind(wx.EVT_BUTTON,self.click_update_offset)

		#ｵﾌｾｯﾄのﾚｲｱｳﾄ
		self.ofst = wx.BoxSizer(wx.HORIZONTAL)
		self.ofst.Add(self.ox1, proportion=1,flag=wx.EXPAND | wx.TOP, border=2)
		self.ofst.Add(self.oy1, proportion=1,flag=wx.EXPAND | wx.TOP, border=2)
		self.ofst.Add(self.ox2, proportion=1,flag=wx.EXPAND | wx.TOP, border=2)
		self.ofst.Add(self.oy2, proportion=1,flag=wx.EXPAND | wx.TOP, border=2)
		self.ofst.Add(self.bt3, proportion=0)

		#全体のﾚｲｱｳﾄへ登録する
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)	#ｸﾞﾗﾌｴﾘｱ
		self.sizer.Add(self.ofst,flag=wx.BOTTOM | wx.GROW)			#ｵﾌｾｯﾄ
		self.sizer.Add(self.pos,flag=wx.BOTTOM | wx.GROW)			#ﾍﾞｸﾄﾙ座標
		self.SetSizer(self.sizer)

		self.Fit()

		#ﾄﾞﾗｯｸﾞ&ﾄﾞﾛｯﾌﾟを有効にする
		self.droptarget = MyFileDropTarget(self)
		self.SetDropTarget(self.droptarget)

		self.vec = []		#矢印ｵﾌﾞｼﾞｪｸﾄ・ﾘｽﾄ
		self.curVec = None  #選択中の矢印

		#ｸﾞﾗﾌ上のｲﾍﾞﾝﾄﾊﾝﾄﾞﾗの登録
		self.figure.canvas.mpl_connect('motion_notify_event', self.OnMouseMove)	#ﾏｳｽ移動
		self.figure.canvas.mpl_connect('pick_event', self.OnPick)				#矢印を掴む

	#
	#
	#
	def click_update_offset(self, event):
		global offsetX, offsetY
		if self.vectData == None:
			return

		try:
			ofx = float(self.ox1.GetValue())
			ofy = float(self.oy1.GetValue())
		except:
			wx.MessageBox(u'数値以外が使用されています',u'ｴﾗｰ',wx.OK|wx.ICON_ERROR)
			self.ox1.SetValue('{0:.3f}'.format(offsetX))
			self.oy1.SetValue('{0:.3f}'.format(offsetY))
			return

		offsetX = ofx
		offsetY = ofy
		vecList = self.vectData.get_list(offsetX,offsetY)
		self.remove_vect()
		self.draw_vect(vecList,True)

	#
	# 「更新」ﾎﾞﾀﾝ処理
	#
	def click_update(self, event):
		if self.curVec == None:
			#選択された矢印が無い
			return

		idx = self.vec.index( self.curVec )
		#座標ﾃﾞｰﾀ
		str_tx1 = self.tx1.GetValue()
		str_ty1 = self.ty1.GetValue()
		str_tx2 = self.tx2.GetValue()
		str_ty2 = self.ty2.GetValue()
		try:
			vec = (float(str_tx1),float(str_ty1),float(str_tx2),float(str_ty2))
			self.vectData[idx] = vec
		except:
			wx.MessageBox(u'数値以外が使用されています',u'ｴﾗｰ',wx.OK | wx.ICON_ERROR)
			pos = self.vectData[idx]
			self.tx1.SetValue('{0:.3f}'.format(pos[0]))
			self.ty1.SetValue('{0:.3f}'.format(pos[1]))
			self.tx2.SetValue('{0:.3f}'.format(pos[2]))
			self.ty2.SetValue('{0:.3f}'.format(pos[3]))
			return

		self.vec.remove( self.curVec )	#矢印をﾘｽﾄから削除
		self.curVec.remove()			#矢印ｵﾌﾞｼﾞｪｸﾄを削除

		#矢印の生成
		pos = vecUtil.pos2Pixel(vec,dottLen,offsetX,offsetY)
		v = self.axes.quiver(pos[0],pos[1],pos[2],pos[3],angles='xy',scale_units='xy',scale=1,color='r',picker=2)
		self.vec.append(v)
		self.curVec = v

		self.canvas.draw()

	#
	# ﾍﾞｸﾄﾙﾃﾞｰﾀのﾌｧｲﾙ出力
	#
	def click_output_file(self, event):
		if self.vectData == None:
			wx.MessageBox(u'ﾍﾞｸﾄﾙﾃﾞｰﾀがありません',u'ｴﾗｰ',wx.OK|wx.ICON_ERROR)
			return

		id = wx.MessageBox(u'{0}を生成します'.format(self.vectData.fileName),u'確認',wx.YES_NO|wx.ICON_WARNING)
		if id == wx.NO:
			return
		try:
			with open( self.vectData.fileName,'w') as f:
				f.write('LISTSTART\n')
				for vec in self.vectData:
					f.write('JUMP {0:.4f} {1:.4f}\n'.format(vec[0],vec[1]))
					f.write('MARK {0:.4f} {1:.4f}\n'.format(vec[2],vec[3]))

				f.write('LISTEND')
		except:
			wx.MessageBox(u'{0}の生成に失敗しました'.format(self.vectData.fileName),u'ｴﾗｰ',wx.OK|wx.ICON_ERROR)

	#
	# ﾏｳｽ移動のｲﾍﾞﾝﾄﾊﾝﾄﾞﾗ
	#
	def OnMouseMove(self,event):
		#print 'onpick:{0}=({1},{2})'.format(event.name,event.xdata,event.ydata)
		if event.xdata == None and event.ydata == None:
			return

		self.GetParent().SetStatusText('({0:.3f},{1:.3f})'.format(event.xdata,event.ydata) )
		#self.tx1.SetValue('x={0:.3f} y={1:.3f}'.format(event.xdata,event.ydata) )

	#
	# 矢印を掴んだ時のﾊﾝﾄﾞﾗ
	#
	def OnPick(self,event):
		for idx,vec in enumerate(self.vec):
			if vec == event.artist:
				if self.curVec != None:
					self.curVec.set_color('g')	

				vec.set_color('r')
				self.curVec = vec
				pos = self.vectData[idx]
				self.tx1.SetValue('{0:.3f}'.format(pos[0]))
				self.ty1.SetValue('{0:.3f}'.format(pos[1]))
				self.tx2.SetValue('{0:.3f}'.format(pos[2]))
				self.ty2.SetValue('{0:.3f}'.format(pos[3]))

		self.canvas.draw()

	#
	# 画像描画
	#
	def draw(self):
		#xx = self.im.width / 2
		#yy = self.im.height /2
		#self.axes.imshow(self.im_list,aspect='equal',origin='upper',interpolation='None',extent=(-xx,xx,-yy,yy))

		xx = self.im.width
		yy = self.im.height
		self.axes.imshow(self.im_list,aspect='equal',origin='upper',interpolation='None',extent=(0,xx,0,yy),cmap=cm.gray)

	#
	# 矢印ｵﾌﾞｼﾞｪｸﾄを削除
	#
	def remove_vect(self, reDraw = False):
		#矢印ｵﾌﾞｼﾞｪｸﾄを削除
		for vec in self.vec:
			vec.remove()

		#ｵﾌﾞｼﾞｪｸﾄのﾘｽﾄを削除
		del self.vec[0:len(self.vec)]

		self.bt2.Disable()

		self.curVec = None

		if reDraw == True:
			self.canvas.draw()

	#
	# 矢印を描画
	#
	def draw_vect(self, vecList, reDraw=False):
		for vec in vecList:
			pos = vecUtil.pos2Pixel(vec,dottLen)
			v = self.axes.quiver(pos[0],pos[1],pos[2],pos[3],angles='xy',scale_units='xy',scale=1,color='g',picker=2)
			self.vec.append(v)

		if reDraw == True:
			self.canvas.draw()

	#
	# ﾄﾞﾗｯｸﾞ&ﾄﾞﾛｯﾌﾟ ﾊﾝﾄﾞﾗ
	#
	def LoadFile(self, files):
		for file in files:
			path,ext = os.path.splitext(file)
			if ext == '.vect':
				self.vectData = vecUtil.VectData(file)
				vecList = self.vectData.get_list(offsetX,offsetY)
				self.remove_vect()
				self.draw_vect(vecList,True)
				self.bt2.Enable()
			elif ext == '.png' or ext == '.bmp' or ext == '.jpg':
				self.im=Image.open(file)
				self.im_list=array(self.im)

				self.figure.suptitle(os.path.basename(file),fontsize=40,fontdict={"fontproperties":font_prop,"fontsize":40})
				self.remove_vect()
				self.draw()
				self.canvas.draw()
			else:
				wx.MessageBox(u'ｻﾎﾟｰﾄされていないﾌｧｲﾙ形式です',u'警告',wx.OK | wx.ICON_ERROR)
				pass

#
# ﾒｲﾝ
#
if __name__ == "__main__":
	app = wx.App()
	fr = wx.Frame(None, title=u'焼成ﾍﾞｸﾄﾙ確認',size=(600,800))
	fr.CreateStatusBar()
	panel = CanvasPanel(fr)
	#panel.draw()
	fr.Show()
	app.MainLoop()
