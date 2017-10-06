#-*- coding:utf-8 -*-

import os
import sys

import re
from lxml import etree
from xml.etree import ElementTree as ET


class IPCObject(object):
	def __init__(self, name,attrib=None):
		self.attrib_ = attrib
		if attrib != None:
			if attrib.has_key('name') == True:
				self.name_ = attrib['name']
			else:
				self.name_ = name


## IPC Shape
class IPC_RectRound(IPCObject):
	def __init__(self, attrib):
		super(IPC_RectRound,self).__init__(attrib['id'],attrib)

class IPC_Circle(IPCObject):
	def __init__(self, attrib):
		super(IPC_Circle,self).__init__(attrib['id'],attrib)

### 色定義
class IPC_Color(IPCObject):
	def __init__(self,attrib):
		super(IPC_Color,self).__init__('Color')
		self.red_ = int(attrib['r'])
		self.green_ = int(attrib['g'])
		self.blue_ = int(attrib['b'])

###
### 層内ｵﾌﾞｼﾞｪｸﾄ
###
##### ｷｬﾋﾞﾃｨ
class IPCObject_Cavity(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_Cavity,self).__init__('Cavity',attrib)


### ﾎｰﾙ
class IPCObject_Hole(IPCObject):
	def __init__(self, net, attrib):
		super(IPCObject_Hole,self).__init__('Hole',attrib)
		self.net_ = net

class IPCObject_Pad(IPCObject):
	def __init__(self, net, attrib):
		super(IPCObject_Pad,self).__init__('Pad',attrib)
		self.net_ = net

class IPCObject_Package(IPCObject):
	def __init__(self, polygon, attrib):
		super(IPCObject_Package,self).__init__('Package',attrib)
		self.polugon_ = polygon
		self.pad_list_ = []	

	def set_land_pattern(self, pad_list):
		self.pad_list_ = pad_list

	def set_pin(self, attr_pin):
		self.attr_pin_ = attr_pin

class IPCObject_Component(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_Component,self).__init__(attrib['refDes'],attrib)
		self.rotation_ = 0.0
		self.location_ = (0.0,0.0)

	def set_rotation(self, r):
		self.rotation_ = r

	def set_location(self, pos):
		self.location_ = pos

class IPCObject_Logicalnet(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_Logicalnet,self).__init__('LogicalNet',attrib)
		self.pin_ref_ = []

	def add_pin_ref(self, pinRef):
		'''
			pinRef(tuple): ('ｺﾝﾎﾟｰﾈﾝﾄ名',pin番号)
		'''
		self.pin_ref_.append(pinRef)

class IPCObject_PhyNetPoint(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_PhyNetPoint,self).__init__('PhyNetPoint',attrib)
		self.net_point_ = []	# [{PhyNetPoint Attrib},{}, ...]

	def add_net_point(self, net_point):
		self.net_point_.append(net_point)

class IPCObject_Via(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_Via,self).__init__('Via',attrib)
		self.location_ = (0,0)

class IPCObject_Circuit(IPCObject):
	def __init__(self, attrib):
		super(IPCObject_Circuit,self).__init__(attrib['net'],attrib)

### 層
class Layer(IPCObject):
	def __init__(self,name):
		super(Layer,self).__init__(name)
		self.items_ = []	#層内ｵﾌﾞｼﾞｪｸﾄ
		self.thickness = 0.0


# xml の namespace 部を '' で置換するための正規表現ﾃﾞｰﾀ
re_pat = re.compile('\{.*?\}')

# 層ﾃﾞｨｸｼｮﾅﾘ={'層名':Layer}
layers={}
layer_group = []	#[(ｸﾞﾙｰﾌﾟ名,[ﾚｲﾔｰ,ﾚｲﾔｰ,...]), ...]
phy_net_group = {}	#{'PhyNet名':[NetPoint,NetPoint, ...]}

# 図形定義(EntryStandard)={'id':IPC_Shape}
entryStandard = {}

# {'Component名':IPCObject_Component}
# <Component refDes=""> refDesをComponent名
components = {}

#色定義
colors = {}

def layer_range(startLayer, endLayer):
	'''
		layer_group で 中に startLayer を含むｸﾞﾙｰﾌﾟ から
		layer_group で 中に endLayer   を含むｸﾞﾙｰﾌﾟ
		をﾘｽﾄとして取得
	'''
	st = 0
	ed = 0
	for n,(groupName,layers) in enumerate(layer_group):
		for layer in layers:
			if layer.name_ == startLayer:
				st = n
			if layer.name_ == endLayer:
				ed = n
	return layer_group[st:ed+1]

def create_shape(elem):
	''' 形状定義(EntryStandard)
	'''
	ch = elem.getchildren()
	tn = re.sub(re_pat,'',ch[0].tag)
	if tn == 'RectRound':
		return IPC_RectRound(elem.attrib)
	elif tn == 'Circle':
		return IPC_Circle(elem.attrib)
	else:
		print 'UnSupport:{0}'.format(tn)
		return None


def xml_entry_standard(elem):
	for n,ee in enumerate(elem):
		if type(ee).__name__ == 'Element':
			tagName = re.sub(re_pat,'',ee.tag)
			if tagName == 'EntryStandard':
				entryStandard[ee.attrib['id']] = create_shape(ee)


def xml_entry_color(elem):
	for n,ee in enumerate(elem):
		if type(ee).__name__ == 'Element':
			tagName = re.sub(re_pat,'',ee.tag)
			if tagName == 'EntryColor':
				cl = ee.getchildren()
				for col in cl:
					# 層に色ｵﾌﾞｼﾞｪｸﾄを追加
					layers[ee.attrib['id']].items_.append( IPC_Color(col.attrib) )


def xml_content(elem):
	'''
		<Content>処理
	'''
	for n, ee in enumerate(elem):
		if type(ee).__name__ == 'Element':
			print '{0}:{1}={2}'.format(n,re.sub(re_pat,'',ee.tag),ee.attrib)
			tagName = re.sub(re_pat,'',ee.tag)

			if tagName == 'FunctionMode':
				pass
			elif tagName == 'StepRef':
				pass
			elif tagName == 'LayerRef':
				layers[ee.attrib['name']] = Layer(ee.attrib['name'])
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
	'''
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
	'''
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

#def create_cavity(layerName, elem):
#	'''
#	'''
#	for ee in elem:
#		tagName = re.sub(re_pat,'',ee.tag)
#		if tagName == 'Span':
#			layers[layerName].items_.append( IPCObject_Cavity(ee.attrib))
#
#def create_hole(layerName, elem):
#	'''
#	'''
#	for ee in elem:
#		tagName = re.sub(re_pat,'',ee.tag)
#		if tagName == 'Span':
#			layers[layerName].items_.append( IPCObject_Hole(ee.attrib))


def xml_stuckup(elem, thick):
	'''
		層構造定義
	'''
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'StackupGroup':
			ch = ee.getchildren()
			#ｸﾞﾙｰﾌﾟ
			layer_group.append( (ee.attrib['name'],[layers[ cc.attrib['layerOrGroupRef'] ] for cc in ch]) )
			#層厚み
			for cc in ch:
				layers[ cc.attrib['layerOrGroupRef']].thickness = float(cc.attrib['thickness'])

def create_pad_stuck(elem, net=None):
	'''
		elem: [<LayerPad> or <LayerHole>, ...]
	'''
	attr = {}
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'LayerPad':
			attr.update( {k:el.attrib[k] for el in ee.getchildren() for k in el.attrib} )
			if attr.has_key('diameter') == True:
				layers[ ee.attrib['layerRef'] ].items_.append( IPCObject_Hole(net,attr) )
			else:
				layers[ ee.attrib['layerRef'] ].items_.append( IPCObject_Pad(net,attr) )
			attr = {}

		elif tagName == 'LayerHole':
			attr = ee.attrib
			# <Span> の attrib を取り出して、<LayerHole> の attrib と繋げる
			attr.update( {k:el.attrib[k] for el in ee.getchildren() for k in el.attrib} )


def pos_polygon(elem):
	'''
		elemの属性値、'x','y'を(x,y)のﾘｽﾄとする
	'''
	#[(x,y),(x,y), ...]
	#return [(float(el.attrib['x']),float(el.attrib['y'])) for el in elem.getchildren()]
	return [(float(el.attrib['x']),float(el.attrib['y'])) for el in elem.getchildren() if el.attrib.has_key('x') and el.attrib.has_key('y')]

def step_profile(elem):
	'''
		基板外形
		list[elem]: elem[0]= <Polygon>
		children(): <PolyStepSegment>
	'''

	## pos=[(x,y),(x,y), ...]
	pos = pos_polygon(elem[0])

def package_land_pattern(elem):
	'''
	'''
	attrs = []
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Pad':
			attrs.append({k:el.attrib[k] for el in ee.getchildren() for k in el.attrib})

	#'pin'番号の小さい順に並べる
	return sorted(attrs,key=lambda x:int(x['pin']))


def step_package(elem, attrib):
	'''
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
			pass

def step_component(elem, attrib):
	'''
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
	'''
	'''
	#net = [elem[x:x + 2] for x in xrange(0, len(elem), 2)]

	netObj = IPCObject_Logicalnet(attrib)

	for ee in elem:
		netObj.add_pin_ref( (ee.attrib['componentRef'],int(ee.attrib['pin'])) )


def step_phynet_group(elem, attrib):
	'''
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


def layer_feature_set(elem, attrib, layerName):
	'''
		elem:[<Features>, ...]
		attrib:{}
	'''
	for ee in elem:
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Pad':
			attr = {k:el.attrib[k] for el in ee.getchildren() for k in el.attrib}
			if attrib.has_key('componentRef'):
				component = components[attrib['componentRef']]
				if attr.has_key('rotation'):
					component.set_rotation( float(attr['rotation']) )

				component.set_location( (float(attr['x']),float(attr['y'])) )
			else:
				attr.update(attrib)
				#ﾚｲﾔｰにﾋﾞｱを追加[※Pad(IPCObject_Pad)と同じ座標にﾋﾞｱを定義している]
				layers[layerName].items_.append( IPCObject_Via(attr) )

		elif tagName == 'Features':
			ch = ee.getchildren()
			if 'Line' in ch[0].tag:
				attr = ch[0].attrib
				attr.update( {k:el.attrib[k] for el in ch[0].getchildren() for k in el.attrib})
				pos = ( (float(attr['startX']),float(attr['startY'])), (float(attr['endX']),float(attr['endY'])) )
				layers[layerName].items_.append( IPCObject_Circuit(attrib) )
				pass
			elif 'Polyline' in ch[0].tag:
				attr = {k:el.attrib[k] for el in ch[0].getchildren() for k in el.attrib}
				pos = pos_polygon(ch[0])
				layers[layerName].items_.append( IPCObject_Circuit(attrib) )
				pass
			elif 'Contour' in ch[0].tag:
				pos = pos_polygon( ch[0].getchildren()[0] )
				pass
			else:
				pass
		elif tagName == 'Hole':
			attr = attrib
			attr.update( ee.attrib )
			layers[layerName].items_.append( IPCObject_Hole(attr['net'],attr) )
			pass
		elif tagName == 'SlotCavity':
			attr = attrib
			attr.update( ee.attrib )
			ch = ee.getchildren()
			pos = pos_polygon(ch[0].getchildren()[0])
			layers[layerName].items_.append( IPCObject_Cavity(attr) )
			pass


def step_layer_feature(elem, attrib):
	'''
		elem:[<Set>,<Set>,...]
		attrib: {'layerRef':'ﾚｲﾔｰ名'}
	'''
	print attrib['layerRef']
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
					print pos
				else:
					ch2 = ch[0].getchildren()
					if 'Line' in ch2[0].tag:
						attr = ch2[0].attrib
						pos = ( (float(attr['startX']),float(attr['startY'])), (float(attr['endX']),float(attr['endY'])) )
					elif 'Polyline' in ch2[0].tag:
						pos = pos_polygon( ch2[0] )	
					elif 'Contour' in ch2[0].tag:
						pos = pos_polygon( ch2[0].getchildren()[0] )
					else:
						print 'Error'
						pass

					print pos


def xml_step(elem):
	'''
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
	'''
	'''
	for n,ee in enumerate(elem):
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'Layer':
			'''
			if ee.attrib['layerFunction'] == 'ROUT':
				create_cavity(ee.attrib['name'],ee.getchildren())

			elif ee.attrib['layerFunction'] == 'DRILL':
				create_hole(ee.attrib['name'],ee.getchildren())
			'''
			pass
		elif tagName == 'Stackup':
			xml_stuckup(ee.getchildren(),ee.attrib['overallThickness'])
		elif tagName == 'Step':
			xml_step( ee.getchildren() )




def xml_ecad(elem):
	'''
	'''
	for n,ee in enumerate(elem):
		tagName = re.sub(re_pat,'',ee.tag)
		if tagName == 'CadHeader':
			pass
		elif tagName == 'CadData':
			xml_cad_data( ee.getchildren() )


#############################################3

tree = ET.parse('f:\\mockup2016_3.xml')

root = tree.getroot()
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


'''
root = etree.parse('f:\\mockup2016_3.xml')

for tag in root.iter():
	print tag.tag
	xml_child(tag.getchildren())
	#print tag.tag
'''
print 'End'
