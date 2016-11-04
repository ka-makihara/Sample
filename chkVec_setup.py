from distutils.core import setup
import py2exe, sys, os
import matplotlib

sys.argv.append('py2exe')

option = {
	'compressed'  : 1,
	'optimize'    : 2,
	'bundle_files': 3,
	'includes' : ["matplotlib.backends","matplotlib.backends.backend_tkagg","FileDialog",'scipy.special._ufuncs_cxx','scipy', 'scipy.integrate', 'scipy.special.*','scipy.linalg.*'],
}

setup(
	options = {'py2exe':option},
	console = [{'script':'chkVec.py'}],
	data_files = matplotlib.get_py2exe_datafiles(),
	zipfile = None
)