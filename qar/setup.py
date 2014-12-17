#-*-coding: utf-8-*-
import sys
from cx_Freeze import setup, Executable

ACCESS = {1: ["admin", "admin", ['b747.bmp',
                                 'a320.bmp',
                                 'an148.bmp',
                                 'an32.bmp',
                                 'an26.bmp',
                                 'an72.bmp',
                                 'an74.bmp',
                                 's340.bmp',
                                 'b737.bmp',
                                 'open_CF.png']],
          10: ["yanair", "YanAir", ['a320.bmp', 
                                    's340.bmp',
                                    'open_CF.png']],
          11: ["gap_ukraine", u'ГАП "Украина" Ан148 БУР-92 А-05', []],
          12: ["VCH", u'В/Ч №2269', ['an26.bmp', 
                                     'an72.bmp',
                                     'an74.bmp']]}


USER = 1

USER_LIST = [each for each in ACCESS[USER][2]]

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

setup(name=u"QAR Reader %s" % ACCESS[USER][1],
      version="0.2",
      description="QAR reader application",
      options={"build_exe": build_exe_options},
      executables=[Executable("qar_reader.py")])
#base = "Win32GUI"


# GUI applications require a different base on Windows (the default is for a
# console application).


