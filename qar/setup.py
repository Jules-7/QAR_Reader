#-*-coding: utf-8-*-
import sys
from cx_Freeze import setup, Executable
from source_data import ACCESS, USER

USER_LIST = [each for each in ACCESS[USER][3]]

# Dependencies are automatically detected, but it might need fine tuning.
COMMON = ['save.png', 
          'microsoft.vc90.crt.manifest',
          'msvcm90.dll',
          'msvcp90.dll',
          'msvcr90.dll']

includefiles = COMMON + USER_LIST

build_exe_options = {"packages": ["os"], 
                     "excludes": [""], 
                     "include_files": includefiles}

# GUI applications require a different base on Windows (the default is for a
# console application).

if sys.platform == "win32":
    base = "Win32GUI"

if ACCESS[USER][0] == 'admin':
    setup(name=u"QAR Reader %s" % ACCESS[USER][1],
          version="0.16",
          description="QAR reader application",
          options={"build_exe": build_exe_options},
          executables=[Executable("qar_reader.py")])
else:
    setup(name=u"QAR Reader %s" % ACCESS[USER][1],
          version="0.1",
          description="QAR reader application",
          options={"build_exe": build_exe_options},
          executables=[Executable("qar_reader.py", base="Win32GUI")])


