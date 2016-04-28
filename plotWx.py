import matplotlib
matplotlib.interactive( True )
matplotlib.use( 'WXAgg' )

import wx
class myWxPlot(wx.Panel):
	def __init__( self, parent):
		from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
		from matplotlib.figure import Figure
		
		self.parent = parent
		wx.Panel.__init__( self, parent)

		#matplotlib figure
		self.figure = Figure( None )
		self.figure.set_facecolor( (0.7,0.7,1.) )
		self.subplot = self.figure.add_subplot( 111 )
		#canvas
		self.canvas = FigureCanvasWxAgg( self, -1, self.figure )
		self.canvas.SetBackgroundColour( wx.Colour( 100,255,255 ) )

		self._SetSize()
		self.draw2()

	def _SetSize( self ):
		size = tuple( self.parent.GetClientSize() )
		self.SetSize( size )
		self.canvas.SetSize( size )
		self.figure.set_size_inches( float( size[0] )/self.figure.get_dpi(),
									 float( size[1] )/self.figure.get_dpi() )

	def draw(self):
		from mpl_toolkits.mplot3d import Axes3D
		import numpy as np
		
		x = np.arange(-3, 3, 0.25)
		y = np.arange(-3, 3, 0.25)
		X, Y = np.meshgrid(x, y)
		Z = np.sin(X)+ np.cos(Y)
		
		ax = Axes3D(self.figure)
		ax.plot_wireframe(X,Y,Z)

	def draw2(self):
		import numpy as np

		theta = np.arange(0,200, 0.1)
		x = 2*np.cos(theta/7)
		y = 3*np.sin(theta/3)

		self.subplot.plot(x,y, '-r')

		self.subplot.set_title("Sample", fontsize = 12)
		self.subplot.set_xlabel("x")
		self.subplot.set_ylabel("y")
		self.subplot.set_xlim([-4, 4])
		self.subplot.set_ylim([-4, 4])


app = wx.App()
frame = wx.Frame( None, size=(500,500) )
panel = myWxPlot( frame )
frame.Show()
app.MainLoop()
