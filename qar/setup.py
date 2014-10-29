import sys
from cx_Freeze import setup, Executable


# Dependencies are automatically detected, but it might need fine tuning.
includefiles = ['save.png', 
		        'save_raw.png', 
		        'setting.png', 
		        'boeing_747.jpg' , 
		        'open_CF.png', 
		        'open_folder.png', 
                'bur_92.png',
		        'microsoft.vc90.crt.manifest',
		        'msvcm90.dll',
		        'msvcp90.dll',
		        'msvcr90.dll']
#includes = ['atexit']
#excludes = ['Tkinter']
#packages = ['os']

build_exe_options = {"packages": ["os"], "excludes": [""], 'include_files':includefiles}

# GUI applications require a different base on Windows (the default is for a
# console application).

if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "QAR Reader",
        version = "0.1",
        description = "QAR reader application",
        options = {"build_exe": build_exe_options},
        executables = [Executable("qar_reader.py" )])
#base = "Win32GUI"

#setup(name="Reader",scripts=["qar_reader.py",
                  #"boeing.py",
                  #"pickFlight_v5.py",
                  #"qarReader_prod_v2.py",
                  #"compact_flash.py",
                  #"splitter.py",
                  #"processing.py",
                  #"airbus.py",
                  #"SAAB340.py"],)
                  
                  


# GUI applications require a different base on Windows (the default is for a
# console application).
'''
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "my-app",
        version = "0.9.0",
        description = "Copyright 2013",
        options = {"build_exe": build_exe_options},
        executables = [Executable("my_module.py", base=base)])'''



