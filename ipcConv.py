#-*- coding:utf-8 -*-

import os
import sys

import re
import collections
import math
from xml.etree import ElementTree as ET

# 追加でｲﾝｽﾄｰﾙが必要なﾓｼﾞｭｰﾙ
#  pip install <ﾓｼﾞｭｰﾙ名> でｲﾝｽﾄｰﾙが必要
#   PIL  : pillow   ->> pip install pillow
#   numpy: numpy
from PIL import Image, ImageDraw
import numpy as np

###########################################################


# xml の namespace 部を '' で置換するための正規表現ﾃﾞｰﾀ
#  XML に xmlns="http://webstds.ipc.org/2581" のﾈｰﾑｽﾍﾟｰｽが設定されているために
#  全てのﾀｸﾞに {http://webstds.ipc.org/2581}/<Tag名>  のようにﾈｰﾑｽﾍﾟｰｽが追加されている
#  処理しづらいので、{} 部分を置換するための定義
re_pat = re.compile('\{.*?\}')

# 層ﾃﾞｨｸｼｮﾅﾘ={'層名':Layer}
layers={}

# {'ﾚｲﾔｰｸﾞﾙｰﾌﾟ名':[ﾚｲﾔｰ,ﾚｲﾔｰ, ...]}
layer_group = collections.OrderedDict()		#※順番を規定したいので順番保持型のﾃﾞｨｸｼｮﾅﾘを使用
phy_net_group = {}	#{'PhyNet名':[NetPoint,NetPoint, ...]}

# 図形定義(EntryStandard)={'id':IPC_Shape}
entryStandard = {}

# {'Component名':IPCObject_Component}
# <Component refDes=""> refDesをComponent名
components = {}

# <Package> {'ﾊﾟｯｹｰｼﾞ名':IPCObject_Package}
# Component のPackageRef で参照される
packages = {}

#色定義 {'ﾚｲﾔｰ名':IPCObject_Color, ...}
colors = {}

# XML ElementTree root
root = None

dotSize = 0.0423	#1ﾄﾞｯﾄのｻｲｽﾞ(mm)
layerThick = 0.067	#1層の厚み(mm)

##########################################################################################

def rot(deg):
	u'''
		座標を角度変換するための行列ﾃﾞｰﾀ作成
		deg: 角度
	'''
	r = np.radians(deg)
	obj = np.matrix( ((np.cos(r),-np.sin(r)),(np.sin(r),np.cos(r))) )
	return obj


class IPCObject(object):
	def __init__(self, name,attrib=None):
		self.attrib_ = attrib
		self.name_ = name
		if attrib != None:
			if attrib.has_key('name') == True:
				self.name_ = attrib['name']
	@property
	def name(self):
		return self.name_
	@property
	def attribute(self):
		return self.attrib_

## IPC Shape
class IPC_RectRound(IPCObject):
	def __init__(self, attrib):
		super(IPC_RectRound,self).__init__(attrib['id'],attrib)

	def polygon(self, centerPos):
		w = float(self.attribute['width']) / 2.0
		h = float(self.attribute['height']) / 2.0
		x = float(centerPos[0])
		y = float(centerPos[1])

		x1 = int( (x-w)/dotSize )
		x2 = int( (x+w)/dotSize )
		y1 = int( (y-h)/dotSize )
		y2 = int( (y+h)/dotSize )

		return ('RectRound',[(x1,y1),(x2,y1),(x2,y2),(x1,y2)])

class IPC_Circle(IPCObject):
	def __init__(self, attrib):
		super(IPC_Circle,self).__init__(attrib['id'],attrib)

	def polygon(self, centerPos):
		r = int( float( self.attribute['diameter'] ) / dotSize)
		x = int(float(centerPos[0])/dotSize)
		y = int(float(centerPos[1])/dotSize)
		return ('Circle',[(x,y),(r,r)])

### 色定義
class IPC_Color(IPCObject):
	def __init__(self,attrib):
		super(IPC_Color,self).__init__('Color')
		self.red_ = int(attrib['r'])
		self.green_ = int(attrib['g'])
		self.blue_ = int(attrib['b'])

	@property
	def rgb(self):
		return (self.red_,self.green_,self.blue_)


###
### 層内ｵﾌﾞｼﾞｪｸﾄ
###
##### ｷｬﾋﾞﾃｨ
class IPCObject_Cavity(IPCObject):
	def __init__(self, pos, attrib):
		super(IPCObject_Cavity,self).__init__('Cavity',attrib)
		self.pos_ = pos
		if attrib.has_key('x') == False:
			# x,y の属性が無いので始点をx,yとする
			self.attrib_['x'] = str(pos[0][0])
			self.attrib_['y'] = str(pos[0][1])

	def polygon(self):
		return ('Polygon',map(lambda arg: (int(arg[0]/dotSize),int(arg[1]/dotSize)), self.pos_))


### ﾎｰﾙ
class IPCObject_Hole(IPCObject):
	def __init__(self, net, attrib):
		super(IPCObject_Hole,self).__init__('Hole',attrib)
		self.net_ = net

	def polygon(self):
		shape_obj = entryStandard[self.attribute['id']]
		return shape_obj.polygon( (self.attribute['x'],self.attribute['y']) )

### ﾊﾟｯﾄﾞ
class IPCObject_Pad(IPCObject):
	def __init__(self, net, attrib):
		super(IPCObject_Pad,self).__init__('Pad',attrib)
		self.net_ = net

	def polygon(self):
		shape_obj = entryStandard[self.attribute['id']]
		return shape_obj.polygon( (self.attribute['x'],self.attribute['y']) )


class IPCObject_Package(IPCObject):
	def __init__(self, polygon, attrib):
		super(IPCObject_Package,self).__init__('Package',attrib)
		self.polygon_ = polygon
		self.pad_list_ = []	

	def polygon(self, rotate='0.0'):
		if rotate == '0.0':
			return ('Polygon',self.polygon_)
		else:
			rr = rot(float(rotate))
			#poly=[]
			#for pos in self.polygon_:
			#	p = rr.dot(pos)
			#	poly.append( (round(p[0,0],3),round(p[0,1],3)) )
			#return poly
			return ('Polygon',map(lambda arg:(round(rr.dot(arg)[0,0],3),round(rr.dot(arg)[0,1],3)),self.polygon_))

	def set_land_pattern(self, pad_list):
		self.pad_list_ = pad_list

	def set_pin(self, attr_pin):
		self.attr_pin_ = attr_pin

class IPCObject_Component(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_Component,self).__init__(attrib['refDes'],attrib)
		self.rotation_ = 0.0
		self.location_ = (0.0,0.0)
		self.pad_list_ = []

	def set_rotation(self, r):
		self.rotation_ = r
		self.attrib_['rotation'] = str(r)

	def set_location(self, pos):
		self.location_ = pos
		self.attrib_['x'] = str(pos[0])
		self.attrib_['y'] = str(pos[1])

	def add_pad(self, obj):
		self.pad_list_.append(obj)
	
	def set_polygon(self, pos):
		self.pos_ = pos

	def polygon(self):
		if packages.has_key(self.attribute['packageRef']) == True:
			package = packages[ self.attribute['packageRef'] ]

			pol = package.polygon(str(self.rotation_))
			pos = map(lambda arg:( int((self.location_[0]+arg[0])/dotSize), int((self.location_[1]+arg[1])/dotSize)),pol[1])
			return ('Polygon',pos)
		else:
			return ('None',[(0,0),(0,0),(0,0),(0,0)])


class IPCObject_Logicalnet(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_Logicalnet,self).__init__('LogicalNet',attrib)
		self.pin_ref_ = []

	def add_pin_ref(self, pinRef):
		'''
			pinRef(tuple): ('ｺﾝﾎﾟｰﾈﾝﾄ名',pin番号)
		'''
		self.pin_ref_.append(pinRef)

	def polygon(self):
		return ('None',[(0,0)])


class IPCObject_PhyNetPoint(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_PhyNetPoint,self).__init__('PhyNetPoint',attrib)
		self.net_point_ = []	# [{PhyNetPoint Attrib},{}, ...]

	def add_net_point(self, net_point):
		self.net_point_.append(net_point)

	def polygon(self):
		return ('None',[(0,0)])

class IPCObject_Via(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_Via,self).__init__('Via',attrib)
		self.location_ = (0,0)

	def polygon(self):
		shape_obj = entryStandard[self.attribute['id']]
		return shape_obj.polygon( (self.attribute['x'],self.attribute['y']) )


class IPCObject_Line(IPCObject):
	def __init__(self, pos, attrib=None):
		super(IPCObject_Line,self).__init__('Line',attrib)
		self.pos_ = pos

	def polygon(self):
		pos = map(lambda arg:( int((arg[0])/dotSize), int((arg[1])/dotSize)),self.pos_)
		return ('Line',pos)


class IPCObject_Polygon(IPCObject):
	def __init__(self, pos, attrib=None):
		super(IPCObject_Polygon,self).__init__('Polygon',attrib)
		self.pos_ = pos

	def polygon(self):
		pos = map(lambda arg:( int((arg[0])/dotSize), int((arg[1])/dotSize)),self.pos_)
		return ('Polygon',pos)


class IPCObject_Polyline(IPCObject):
	def __init__(self,pos, attrib=None):
		super(IPCObject_Polyline,self).__init__('Polyline',attrib)
		self.pos_ = pos

	def polygon(self):
		pos = map(lambda arg:( int((arg[0])/dotSize), int((arg[1])/dotSize)),self.pos_)
		return ('Polyline',pos)

### 層
class Layer(IPCObject):
	def __init__(self, attrib):
		super(Layer,self).__init__(attrib['name'], attrib)
		self.items_ = []	#層内ｵﾌﾞｼﾞｪｸﾄ
		#self.params_ = []
		self.thickness_ = 0.0

	@property
	def items(self):
		return self.items_

	@property
	def thikness(self):
		return self.thickness_

	@property
	def function(self):
		return self.attrib_['layerFunction']


class Layer_Cavity(Layer):
	def __init__(self, attrib):
		super(Layer_Cavity,self).__init__(attrib)


class Layer_Hole(Layer):
	def __init__(self, attrib):
		super(Layer_Hole,self).__init__(attrib)


###############################################################################

def create_shape(elem):
	u'''
		形状定義(EntryStandard)
	'''
	ch = elem.getchildren()
	tn = re.sub(re_pat,'',ch[0].tag)

	attr = elem.attrib
	attr.update(ch[0].attrib)

	if tn == 'RectRound':
		return IPC_RectRound(attr)
	elif tn == 'Circle':
		return IPC_Circle(attr)
	else:
		print 'UnSupport:{0}'.format(tn)
		return None


def xml_entry_standard(elem):
	u'''
		<EntryStandard> ﾀｸﾞ処理
	'''
	for n,ee in enumerate(elem):
		if type(ee).__name__ == 'Element':
			tagName = re.sub(re_pat,'',ee.tag)
			if tagName == 'EntryStandard':
				entryStandard[ee.attrib['id']] = create_shape(ee)


def xml_entry_color(elem):
	u'''
		<EntryColor>ﾀｸﾞ処理
	'''
	for n,ee in enumerate(elem):
		if type(ee).__name__ == 'Element':
			tagName = re.sub(re_pat,'',ee.tag)
			if tagName == 'EntryColor':
				cl = ee.getchildren()
				for col in cl:
					# 色ｵﾌﾞｼﾞｪｸﾄを追加
					colors[ee.attrib['id']] = IPC_Color(col.attrib)
					#layers[ee.attrib['id']].params_.append( IPC_Color(col.attrib) )


def xml_content(elem):
	u'''
		<Content>処理
	'''
	for n, ee in enumerate(elem):
		if type(ee).__name__ == 'Element':
			#print '{0}:{1}={2}'.format(n,re.sub(re_pat,'',ee.tag),ee.attrib)
			tagName = re.sub(re_pat,'',ee.tag)

			if tagName == 'FunctionMode':
				pass
			elif tagName == 'StepRef':
				pass
			elif tagName == 'LayerRef':
				#layers[ee.attrib['name']] = Layer(ee.attrib['name'])
				pass
			elif tagName == 'BomRef':
				pass
			elif tagName == 'DictionaryStandard':
				xml_entry_standard( ee.getchildren() )
			elif tagName == 'DictionaryUser':
				pass
			elif tagName == 'DictionaryColor':
				xml_entry_color( ee.getchildren() )
			else:
				print 'Unsupport tag:{0}'.format(tagName)

def bom_item(elem):
	u'''
		<BomItem> ﾀｸﾞ処理
	'''
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'RefDes':
			pass
		elif tagName == 'Characteristics':
			pass
		else:
			print 'Unsupport tag:{0}'.format(tagName)


def xml_bom(elem):
	u'''
		<Bom> 処理
	'''
	for n,ee in enumerate(elem):
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'BomHeader':
			pass
		elif tagName == 'BomItem':
			bom_item( ee.getchildren() )
		else:
			print 'UnSupport tag:{0}'.format(tagName)


def xml_stuckup(elem, thick):
	u'''
		<Stuckup> ﾀｸﾞ処理
		層構造定義
	'''
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'StackupGroup':
			ch = ee.getchildren()
			#ｸﾞﾙｰﾌﾟ
			#layer_group.append( (ee.attrib['name'],[layers[ cc.attrib['layerOrGroupRef'] ] for cc in ch]) )
			layer_group[ee.attrib['name']] = [layers[ cc.attrib['layerOrGroupRef'] ] for cc in ch] 
			#層厚み
			for cc in ch:
				layers[ cc.attrib['layerOrGroupRef']].thickness = float(cc.attrib['thickness'])


def get_layer_list(fromLayerName, toLayerName):
	u'''
		ﾚｲﾔｰｸﾞﾙｰﾌﾟで fromLayerName～toLayerName までのﾚｲﾔｰをﾘｽﾄで取得
	'''
	layer_list = []

	lst = 0
	for groupName,layers in layer_group.iteritems():
		for layer in layers:
			if layer.name == fromLayerName:
				layer_list.append(layer)
				lst = 1

			elif layer.name == toLayerName:
				layer_list.append(layer)
				lst = 0

			else:
				if lst == 1:
					layer_list.append(layer)

		if toLayerName == fromLayerName:
			return layer_list

	return layer_list


def create_pad_stuck(elem, net=None):
	u'''
		elem: [<LayerPad> or <LayerHole>, ...]
	'''
	attr = {}
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'LayerPad':
			attr.update( {k:el.attrib[k] for el in ee.getchildren() for k in el.attrib} )
			if attr.has_key('diameter') == True:
				obj = IPCObject_Hole(net,attr)
				lst = get_layer_list(attr['fromLayer'],attr['toLayer'])

				#該当する全てのﾚｲﾔｰに追加する
				for layer in lst:
					layer.items_.append(obj)
			else:
				layers[ ee.attrib['layerRef'] ].items_.append( IPCObject_Pad(net,attr) )
			attr = {}

		elif tagName == 'LayerHole':
			attr = ee.attrib
			# <Span> の attrib を取り出して、<LayerHole> の attrib と繋げる
			attr.update( {k:el.attrib[k] for el in ee.getchildren() for k in el.attrib} )


def pos_polygon(elem):
	u'''
		elemの属性値、'x','y'を(x,y)のﾘｽﾄとする
	'''
	#[(x,y),(x,y), ...]
	#return [(float(el.attrib['x']),float(el.attrib['y'])) for el in elem.getchildren()]
	return [(float(el.attrib['x']),float(el.attrib['y'])) for el in elem.getchildren() if el.attrib.has_key('x') and el.attrib.has_key('y')]

def step_profile(elem):
	u'''
		<Profile> ﾀｸﾞ処理
		基板外形
		list[elem]: elem[0]= <Polygon>
		children(): <PolyStepSegment>
	'''
	## pos=[(x,y),(x,y), ...]
	pos = pos_polygon(elem[0])

def package_land_pattern(elem):
	u'''
		<Package>-<LandPattern> ﾀｸﾞ処理
	'''
	attrs = []
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Pad':
			attrs.append({k:el.attrib[k] for el in ee.getchildren() for k in el.attrib})

	#'pin'番号の小さい順に並べる
	return sorted(attrs,key=lambda x:int(x['pin']))


def step_package(elem, attrib):
	u'''
		<Package> ﾀｸﾞ処理
		list[elem]: elem[0]= <Outline> elem[1]= <LandPattern>
	'''
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Outline':
			ch = ee.getchildren()
			pol = pos_polygon(ch[0])	#ch[0]=<Polygon>
			#ch[1].attrib				#ch[1]=<LineDesc>
			package = IPCObject_Package(pol,attrib)
			pass
		elif tagName == 'LandPattern':
			package.set_land_pattern( package_land_pattern( ee.getchildren() ))
			pass
		elif tagName == 'Pin':
			attr = ee.attrib
			ch = ee.getchildren()
			if 'Contour' in ch[0].tag:
				pol = pos_polygon( ch[0].getchildren()[0] )
				attr.update({'Contour':pol})
			else:
				attr.update({k:el.attrib[k] for el in ch for k in el.attrib})

			package.set_pin(attr)

	packages[attrib['name']] = package

def step_component(elem, attrib):
	u'''
		<Component> ﾀｸﾞ処理
	'''
	component = IPCObject_Component(attrib)
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Xform':
			component.set_rotation( float(ee.attrib['rotation']) )
		elif tagName == 'Location':
			component.set_location( (float(ee.attrib['x']),float(ee.attrib['y'])) )

	#部品登録(名前、位置(Location))
	components[attrib['refDes']] = component

	#部品を層に登録
	layers[attrib['layerRef']].items_.append(component)

def step_logical_net(elem, attrib):
	u'''
		<LogicalNet> ﾀｸﾞ処理
	'''
	netObj = IPCObject_Logicalnet(attrib)

	for ee in elem:
		netObj.add_pin_ref( (ee.attrib['componentRef'],int(ee.attrib['pin'])) )


def step_phynet_group(elem, attrib):
	u'''
	
		elem: [<PhyNet>,<PhyNet>, ...]
	'''
	for ee in elem:
		net_point = ee.getchildren()	#[<PhyNetPoint>,<PhyNetPoint>, ...]

		net_point_list = []
		for np in net_point:
			attr = np.attrib

			ch = np.getchildren()		#Circle
			tagName = re.sub(re_pat,'',ch[0].tag)
			if tagName == 'Circle':
				attr.update(ch[0].attrib)

			obj = IPCObject_PhyNetPoint(attr)
			net_point_list.append(obj)

			layers[np.attrib['layerRef']].items_.append(obj)

		phy_net_group[ ee.attrib['name'] ] = net_point_list;


def set_layer_object(layer, obj):
	u'''
		ﾚｲﾔｰの属性が ROUT(Cavity) または DRILL(Hole) である場合に
		fromLayer～toLayer の各ﾚｲﾔｰにｵﾌﾞｼﾞｪｸﾄを設定する
	'''
	layer_list = []

	if layer.function == 'ROUT':
		if layer.attribute.has_key('fromLayer') == True:
			layer_list = get_layer_list(layer.attribute['fromLayer'], layer.attribute['toLayer'])

	elif layer.function == 'DRILL':
		if layer.attribute.has_key('fromLayer') == True:
			layer_list = get_layer_list(layer.attribute['fromLayer'], layer.attribute['toLayer'])

	#該当するﾚｲﾔｰにｵﾌﾞｼﾞｪｸﾄを設定
	ln = [l.name for l in layer_list]
	print '{0} APPEND {1}::{2}'.format(ln, type(obj).__name__, obj.name)

	for ll in layer_list:
		ll.items_.append(obj)	


def layer_feature_set(elem, attrib, layerName):
	u'''
		<LayerFeature>-<Set> ﾀｸﾞ処理
		elem:[<Features>, ...]
		attrib:{}
	'''
	#print '--------------:', layerName, '--------------------'

	layer = layers[layerName]
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Pad':
			attr = {k:el.attrib[k] for el in ee.getchildren() for k in el.attrib}
			if attrib.has_key('componentRef'):
				component = components[attrib['componentRef']]
				obj = IPCObject_Pad('',attr)

				# ｺﾝﾎﾟｰﾈﾝﾄに加えるかどうかは要検討
				component.add_pad( obj )
				print 'Component:{0} add_Pad {1}:({2},{3})'.format(component.name,obj.name,obj.attribute['x'],obj.attribute['y'])
			else:
				attr.update(attrib)
				obj = IPCObject_Via(attr)
				#ﾚｲﾔｰにﾋﾞｱを追加[※Pad(IPCObject_Pad)と同じ座標にﾋﾞｱを定義している]

			layer.items_.append( obj )
			print 'Layer:{0} add_{1} {2}:({3},{4})'.format(layer.name, type(obj).__name__,obj.name, obj.attribute['x'],obj.attribute['y'])

		elif tagName == 'Features':
			ch = ee.getchildren()
			if 'Line' in ch[0].tag:
				attr = attrib
				attr.update(ch[0].attrib)
				attr.update( {k:el.attrib[k] for el in ch[0].getchildren() for k in el.attrib})
				pos = [ (float(attr['startX']),float(attr['startY'])), (float(attr['endX']),float(attr['endY'])) ]
				#layer.items_.append( IPCObject_Circuit(pos,attr) )
				layer.items_.append( IPCObject_Line(pos,attr) )
			elif 'Polyline' in ch[0].tag:
				attr = attrib
				attr.update({k:el.attrib[k] for el in ch[0].getchildren() for k in el.attrib})
				pos = pos_polygon(ch[0])
				#layer.items_.append( IPCObject_Circuit(pos,attr) )
				layer.items_.append( IPCObject_Polyline(pos,attr) )
			elif 'Contour' in ch[0].tag:
				pos = pos_polygon( ch[0].getchildren()[0] )
				if attrib.has_key('componentRef') == True:
					component = components[attrib['componentRef']]
					component.set_polygon(pos)
			else:
				print '{0} is Undefined'.format(ch[0].tag)

		elif tagName == 'Hole':
			attr = attrib
			attr.update( ee.attrib )
			layer.items_.append( IPCObject_Hole(attr['net'],attr) )
			pass
		elif tagName == 'SlotCavity':
			attr = attrib
			attr.update( ee.attrib )
			ch = ee.getchildren()
			pos = pos_polygon(ch[0].getchildren()[0])

			obj = IPCObject_Cavity(pos, attr)

			set_layer_object(layer,obj)


def step_layer_feature(elem, attrib):
	u'''
		<LayerFeature> ﾀｸﾞ処理
		elem:[<Set>,<Set>,...]
		attrib: {'layerRef':'ﾚｲﾔｰ名'}
	'''
	layer = layers[ attrib['layerRef'] ]

	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Set':
			ch = ee.getchildren()
			if len(ee.attrib) != 0:
				layer_feature_set( ch, ee.attrib, attrib['layerRef'])
			else:
				if 'Pad' in ch[0].tag:
					pass
				elif 'SlotCavity' in ch[0].tag:
					ch2 = ch[0].getchildren()
					pos = pos_polygon( ch2[0].getchildren()[0] )
					obj = IPCObject_Cavity(pos,ch[0].attrib)

					set_layer_object(layer,obj)

				else:
					ch2 = ch[0].getchildren()
					if 'Line' in ch2[0].tag:
						attr = ch2[0].attrib
						pos = ( (float(attr['startX']),float(attr['startY'])), (float(attr['endX']),float(attr['endY'])) )
						layer.items_.append( IPCObject_Line(pos) )
					elif 'Polyline' in ch2[0].tag:
						pos = pos_polygon( ch2[0] )	
						layer.items_.append( IPCObject_Polyline(pos) )
					elif 'Contour' in ch2[0].tag:
						pos = pos_polygon( ch2[0].getchildren()[0] )
						layer.items_.append( IPCObject_Polygon(pos) )
					else:
						print 'Error'

					#print pos


def xml_step(elem):
	u'''
		<Step> ﾀｸﾞ処理
	'''
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'PadStack':
			if ee.attrib.has_key('net') == True:
				create_pad_stuck( ee.getchildren(), ee.attrib['net'] )
			else:
				create_pad_stuck( ee.getchildren())
		elif tagName == 'Datum':
			pass
		elif tagName == 'Profile':
			step_profile( ee.getchildren() )
			pass
		elif tagName == 'Package':
			step_package( ee.getchildren(),ee.attrib )
			pass
		elif tagName == 'Component':
			step_component( ee.getchildren(),ee.attrib )
			pass
		elif tagName == 'LogicalNet':
			step_logical_net( ee.getchildren(), ee.attrib )
			pass
		elif tagName == 'PhyNetGroup':
			step_phynet_group( ee.getchildren(), ee.attrib )
			pass
		elif tagName == 'LayerFeature':
			step_layer_feature( ee.getchildren(), ee.attrib )
			pass

def xml_cad_data(elem):
	u'''
		<CadData> ﾀｸﾞ処理
	'''
	for n,ee in enumerate(elem):
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Layer':
			ch = ee.getchildren()
			if len(ch) != 0:
				attrib = ee.attrib
				attrib.update(ch[0].attrib)
				if 'Span' in ch[0].tag:
					if ee.attrib['layerFunction'] == 'DRILL':
						layers[ee.attrib['name']] = Layer_Hole(attrib)
					else:
						layers[ee.attrib['name']] = Layer_Cavity(attrib)
				elif 'SpecRef' in ch[0].tag:
					layers[ee.attrib['name']] = Layer(ee.attrib)

			else:
				layers[ee.attrib['name']] = Layer(ee.attrib)

		elif tagName == 'Stackup':
			xml_stuckup(ee.getchildren(),ee.attrib['overallThickness'])
		elif tagName == 'Step':
			xml_step( ee.getchildren() )

def xml_ecad(elem):
	u'''
		<Ecad> ﾀｸﾞ処理
	'''
	for n,ee in enumerate(elem):
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'CadHeader':
			pass
		elif tagName == 'CadData':
			xml_cad_data( ee.getchildren() )

#############################################
#
# 公開関数
#
def convert():
	u'''
		読み込んだXML を層ﾃﾞｰﾀに展開する
	'''
	global root

	if root == None:
		print u'XML ﾌｧｲﾙが読み込まれていません'
		return

	for tag in root:
		#print tag.tag
		tt = re.split(re_pat,tag.tag)
		if tt[1] == 'Content':
			xml_content(tag.getchildren())
		elif tt[1] == 'LogisticHeader':
			pass
		elif tt[1] == 'HistoryRecord':
			pass
		elif tt[1] == 'Bom':
			xml_bom(tag.getchildren())
		elif tt[1] == 'Ecad':
			xml_ecad( tag.getchildren() )
		elif tt[1] == 'Avl':
			pass
		else:
			print 'Unsupport tag:{0}'.format(tt[1])

def load_xml(fileName):
	u'''
		XML ﾌｧｲﾙを読み込む
	'''
	global root

	try:
		tree = ET.parse(fileName)
		root = tree.getroot()
	except IOError:
		print '{0} not found'.format(fileName)


#############################################
#
# ﾃﾞﾊﾞｯｸﾞ用関数
#
def layer_thick(groupName):
	u'''
		ﾚｲﾔｰｸﾞﾙｰﾌﾟに含まれるﾚｲﾔｰの厚みをﾘｽﾄを取得する
	'''

	if layer_group.has_key(groupName) == False:
		return 0.0

	#厚みのﾘｽﾄを作成
	tks = [layer.thickness for layer in layer_group[groupName]]
	tk = sum(tks)

	return  tk

def layer_items(groupName):
	u'''
		ﾚｲﾔｰｸﾞﾙｰﾌﾟに含まれるﾚｲﾔｰ名と含まれるｵﾌﾞｼﾞｪｸﾄ名を表示する
	'''
	if layer_group.has_key(groupName) == False:
		return []

	for layer in layer_group[groupName]:
		tn = [type(x).__name__ for x in layer.items_]
		print layer.name, tn

def layer_list():
	u'''
		ﾚｲﾔｰ一覧表示
	'''
	for groupName in layer_group:
		print '{0}:{1} mm'.format(groupName,layer_thick(groupName))
		for layer in layer_group[groupName]:
			print '    {0}:T={1}'.format(layer.name,layer.thickness)

def create_board_image():
	u'''
		BoardShape から矩形のﾎﾞｰﾄﾞｲﾒｰｼﾞﾃﾞｰﾀを生成する ※黒埋め
		return: Image
	'''
	#ﾎﾞｰﾄﾞｻｲｽﾞ
	layer = layers['BoardShape']
	pol = layer.items[0].polygon()

	sh = sorted(set(pol[1]), key=lambda d: (d[0],d[1]))

	L1 = sh[0]		#(x,y)の最小値
	L2 = sh[-1]		#(x,y)の最大値

	#xs = int(math.ceil((L2[0] - L1[0])/dotSize))
	#ys = int(math.ceil((L2[1] - L1[1])/dotSize))
	xs = L2[0] - L1[0]
	ys = L2[1] - L1[1]

	# ﾎﾞｰﾄﾞｻｲｽﾞのｲﾒｰｼﾞを生成
	#return Image.new('L',(xs,ys))
	return Image.new('RGB',(xs,ys), colors['BoardShape'].rgb)


def group_print(groupName, fileName):
	u'''
		ｸﾞﾙｰﾌﾟに含まれるﾚｲﾔｰのﾋﾞｯﾄﾏｯﾌﾟを作成する
	'''

	print '----', groupName, '----'
	layers = layer_group[groupName]

	img = create_board_image()
	drw = ImageDraw.Draw(img)

	for ly in layers:
		print ly.name
		for obj in ly.items_:
			if obj.attribute.has_key('x') == True:
				print '   {0}::{1}=({2},{3})'.format(type(obj).__name__, obj.name,obj.attribute['x'],obj.attribute['y'])
			else:
				print '   {0}::{1}'.format(type(obj).__name__, obj.name)

			polygonData = obj.polygon()
			print polygonData

			col = colors[ly.name].rgb
			if polygonData[0] == 'Polygon' or polygonData[0] == 'RectRound':
				polygon = map(lambda arg:(arg[0],img.size[1]-arg[1]),polygonData[1])
				drw.polygon( polygon ,col)
				#drw.polygon( polygon ,255)
			elif polygonData[0] == 'Circle':
				rr = polygonData[1]	
				x1 = rr[0][0] - (rr[1][0]/2)
				x2 = rr[0][0] + (rr[1][0]/2)
				y1 = img.size[1] - (rr[0][1] - (rr[1][1]/2))
				y2 = img.size[1] - (rr[0][1] + (rr[1][1]/2))
				drw.ellipse([x1,y1,x2,y2],fill=(0,0,0))
			elif polygonData[0] == 'Polyline':
				lw = int( round(float(obj.attribute['lineWidth'])/dotSize) )
				pos = map(lambda arg:(arg[0],img.size[1]-arg[1]),polygonData[1])
				pp = [pos[0],pos[1]]
				for p2 in pos[2:]:
					drw.line(pp,col,width=lw)
					pp[0] = pp[1]
					pp[1] = p2
				drw.line(pp,col,width=lw)

			elif polygonData[0] == 'Line':
				lw = int( round(float(obj.attribute['lineWidth'])/dotSize) )
				pos = map(lambda arg:(arg[0],img.size[1]-arg[1]),polygonData[1])
				drw.line(pos,col,width=lw)

			elif polygonData[0] == 'None':
				pass

	#ﾌｧｲﾙ保存
	img.save(fileName)

def test():
	load_xml('f:\\mockup2016_A.xml')
	convert()

	#layer_list()

	#group_print('Conductor-7Group', 'f:\\g7.png')
	group_print('Conductor-6Group', 'f:\\g6.png')
	group_print('Conductor-5Group', 'f:\\g5.png')
	group_print('Conductor-4Group', 'f:\\g4.png')
	group_print('Conductor-3Group', 'f:\\g3.png')
	group_print('Conductor-2Group', 'f:\\g2.png')
	group_print('Conductor-1Group', 'f:\\g1.png')

	#ﾋﾟｸｾﾙ指定で書き込み
	#pix = img.load()
	#pix[0,0] = 255

##########################################################

if __name__ == '__main__':
	test()

