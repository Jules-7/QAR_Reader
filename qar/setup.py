import sys
from cx_Freeze import setup, Executable


# Dependencies are automatically detected, but it might need fine tuning.
include_files = ['save.png',
                 'save_raw.png',
                 'boeing_747.jpg',
                 'open_CF.png',
                 'open_folder.png',
                 'bur_92.png',
                 'a320.png',
                 'microsoft.vc90.crt.manifest',
                 'msvcm90.dll',
                 'msvcp90.dll',
                 'msvcr90.dll']

build_exe_options = {"packages": ["os"],
                     "excludes": [""],
                     "include_files": include_files}

# GUI applications require a different base on Windows (the default is for a
# console application).

if sys.platform == "win32":
    base = "Win32GUI"

setup(name="QAR Reader",
      version="0.1",
      description="QAR reader application",
      options={"build_exe": build_exe_options},
      executables=[Executable("qar_reader.py")])
#base = "Win32GUI"

# GUI applications require a different base on Windows (the default is for a
# console application).



