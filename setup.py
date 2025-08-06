from distutils.core import setup
from setuptools import find_packages
import py2exe

setup( packages=find_packages(
        where='',
        include=['gui'],  # alternatively: `exclude=['additional*']`
    ), windows=[{'script': "gui.py", "dest_base": "PADKP-2.8.0"}])
