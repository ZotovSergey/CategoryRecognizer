from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('main.py', base=base, target_name = 'CategoryRecognizer.exe', icon='NTech_logo.ico')
]

include_files = [
                 'config',
                 'NTech_logo.png'
                 ]

build_options = {
                 'include_msvcr': True,
                 'include_files': include_files
                }

setup(name='CategoryRecognizer',
      version = '0.1',
      description = 'Программа, распознающая бренд/категорию по краткому неструктурированному описанию, используя словарь идентификаторов',
      options = {'build_exe': build_options},
      executables = executables)
