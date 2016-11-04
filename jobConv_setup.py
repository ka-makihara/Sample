from distutils.core import setup
import py2exe, sys, os

sys.argv.append('py2exe')

option = {
	'compressed'  : 1,
	'optimize'    : 2,
	'bundle_files': 3,
	'packages'    : ['PIL'],
	'includes'    : ['PIL.Image','PIL.PngImagePlugin','jobUtil','imageUtil','laserUtil','mcmUtil','vectUtil']
}

setup(
	options = {'py2exe':option},
	console = [{'script':'jobConv.py'}],
	zipfile = None
)