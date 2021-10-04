from distutils.core import setup
import py2exe

setup(windows=[{'script': "gui.py", "dest_base": "PADKP-2.3.1"}])
